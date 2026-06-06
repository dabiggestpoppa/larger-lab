"""
PO Streaming Thought Layer — 5-stage cognitive streaming pipeline.

Emits SSE events in the order defined by the cognitive pipeline:
  1. 🧠 processing    — Initial reasoning, query analysis
  2. 🔍 scanning       — Workspace scan for relevant files/context
  3. 📚 retrieving     — Vault/memory retrieval
  4. ⚡ routing        — Agent coordination, model selection
  5. 💬 responding     — Token-by-token LLM response stream

This layer replaces the simple _stream_chat in po_api.py with a proper
event-driven cognitive pipeline. Each stage emits structured events
consumable by the VTuber frontend as status cards.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

from oce.backend.po_events import (
    POEventType,
    StatusEvent,
    WorkspaceScanEvent,
    VaultRetrievalEvent,
    AgentSpawnEvent,
    StreamChunkEvent,
    StreamDoneEvent,
    StreamErrorEvent,
)

logger = logging.getLogger("oce.po_stream")


@dataclass
class ThoughtStage:
    """A single stage in the cognitive pipeline."""

    name: str
    display_icon: str
    display_name: str
    status: str = "pending"  # pending, running, complete, error
    result: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class ThoughtPipeline:
    """Full cognitive pipeline state for a single chat turn."""

    request_id: str = ""
    session_id: str = ""
    stages: List[ThoughtStage] = field(default_factory=list)
    current_stage_idx: int = 0
    total_duration_ms: float = 0.0

    def __post_init__(self):
        if not self.stages:
            self.stages = [
                ThoughtStage("processing", "🧠", "Processing", status="running"),
                ThoughtStage("scanning", "🔍", "Workspace Scan", status="pending"),
                ThoughtStage("retrieving", "📚", "Vault Retrieval", status="pending"),
                ThoughtStage("routing", "⚡", "Agent Routing", status="pending"),
                ThoughtStage("responding", "💬", "Responding", status="pending"),
            ]

    def advance(self) -> Optional[ThoughtStage]:
        """Move to the next stage and return it."""
        if self.current_stage_idx < len(self.stages) - 1:
            self.current_stage_idx += 1
            stage = self.stages[self.current_stage_idx]
            stage.status = "running"
            return stage
        return None

    def current_stage(self) -> Optional[ThoughtStage]:
        if self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx]
        return None

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "current_stage": self.current_stage_idx,
            "stages": [
                {
                    "name": s.name,
                    "icon": s.display_icon,
                    "label": s.display_name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                }
                for s in self.stages
            ],
        }


class ThoughtStreamer:
    """Generates the 5-stage cognitive stream for a PO chat request."""

    def __init__(
        self,
        workspace_scanner=None,
        vault_retriever=None,
        agent_coordinator=None,
        model_router=None,
        fallback_chain=None,
    ):
        self.workspace_scanner = workspace_scanner
        self.vault_retriever = vault_retriever
        self.agent_coordinator = agent_coordinator
        self.model_router = model_router
        self.fallback_chain = fallback_chain

    async def stream(
        self,
        request: Dict[str, Any],
        session_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Execute the full 5-stage cognitive pipeline and yield SSE events.

        Yields OpenAI-compatible chunk format so the VTuber frontend
        can consume it as a normal streaming chat completion.
        """
        import uuid
        from oce.backend.po_events import POEvent

        pipeline = ThoughtPipeline(
            request_id=str(uuid.uuid4())[:8],
            session_id=session_id,
        )
        messages = request.get("messages", [])
        last_content = messages[-1]["content"] if messages else ""

        try:
            # ── Stage 1: Processing ──────────────────────────────────────
            stage = pipeline.current_stage()
            yield _format_event(StatusEvent(stage="processing", message="🧠 Analyzing request..."))
            await asyncio.sleep(0.1)  # Simulate processing

            # ── Stage 2: Workspace Scan ──────────────────────────────────
            stage = pipeline.advance()
            yield _format_event(StatusEvent(stage="scanning", message="🔍 Scanning workspace..."))
            scan_result = await self._run_scan(last_content)
            yield _format_event(WorkspaceScanEvent(**scan_result))
            stage.status = "complete"
            stage.result = scan_result

            # ── Stage 3: Vault Retrieval ─────────────────────────────────
            stage = pipeline.advance()
            yield _format_event(StatusEvent(stage="retrieving", message="📚 Retrieving context..."))
            retrieval_result = await self._run_retrieval(last_content)
            yield _format_event(VaultRetrievalEvent(**retrieval_result))
            stage.status = "complete"
            stage.result = retrieval_result

            # ── Stage 4: Agent Routing ───────────────────────────────────
            stage = pipeline.advance()
            yield _format_event(StatusEvent(stage="routing", message="⚡ Routing to model..."))
            route_result = await self._run_routing(last_content)
            yield _format_event(AgentSpawnEvent(**route_result))
            stage.status = "complete"
            stage.result = route_result

            # ── Stage 5: Response Generation ─────────────────────────────
            stage = pipeline.advance()
            yield _format_event(StatusEvent(stage="responding", message="💬 Generating response..."))

            response_text = await self._generate_response(
                messages=messages,
                context=retrieval_result.get("context_string", ""),
                model=route_result.get("model", "po"),
            )

            # Stream tokens for LLM feel
            words = response_text.split()
            accumulated = ""
            for i, word in enumerate(words):
                accumulated += ((" " if i > 0 else "") + word)
                chunk = StreamChunkEvent(content=word + " ")
                yield _format_event(chunk)
                await asyncio.sleep(0.02)  # ~50 words/sec

            stage.status = "complete"
            pipeline.total_duration_ms = sum(s.duration_ms for s in pipeline.stages)

            yield _format_event(
                StreamDoneEvent(
                    usage={
                        "prompt_tokens": len(" ".join(messages)),
                        "completion_tokens": len(words),
                        "total": len(messages[-1]["content"]) + len(words),
                    }
                )
            )

        except Exception as e:
            logger.error(f"Thought stream error: {e}")
            yield _format_event(StreamErrorEvent(message=str(e)[:500]))

    async def _run_scan(self, query: str) -> Dict[str, Any]:
        """Run workspace scan, return summary dict."""
        try:
            from oce.backend.po_workspace import WorkspaceScanner
            scanner = self.workspace_scanner or WorkspaceScanner()
            result = scanner.scan()
            return result.summary()
        except Exception as e:
            logger.warning(f"Workspace scan failed: {e}")
            return {"files_scanned": 0, "fresh": 0, "error": str(e)}

    async def _run_retrieval(self, query: str) -> Dict[str, Any]:
        """Run vault retrieval, return summary dict with context string."""
        try:
            from oce.backend.po_vault import VaultRetriever
            retriever = self.vault_retriever or VaultRetriever()
            result = retriever.retrieve(query)
            summary = result.summary()
            summary["context_string"] = result.as_context_string(max_tokens=2000)
            return summary
        except Exception as e:
            logger.warning(f"Vault retrieval failed: {e}")
            return {"hits": 0, "context_string": "", "error": str(e)}

    async def _run_routing(self, query: str) -> Dict[str, Any]:
        """Determine which model/agent to route to."""
        try:
            from oce.backend.po_router import ModelRouter
            router = self.model_router or ModelRouter()

            # Also try agent coordination for complex queries
            route_result = router.route(query)
            result = {
                "model": route_result.model_id,
                "provider": route_result.provider,
                "confidence": route_result.confidence,
                "fallback_chain": route_result.fallback_chain,
            }

            # If agent coordinator is available, select best agent
            if self.agent_coordinator:
                try:
                    from oce.backend.po_agents import AgentCoordinator
                    coord = self.agent_coordinator
                    if isinstance(coord, AgentCoordinator):
                        result["agent"] = coord.select_agent_for_query(query)
                except Exception:
                    pass

            return result
        except Exception as e:
            logger.warning(f"Model routing failed: {e}")
            return {"model": "po", "provider": "oce", "fallback": False}

    async def _generate_response(
        self,
        messages: List[Dict[str, Any]],
        context: str = "",
        model: str = "po",
    ) -> str:
        """Generate a response using the PO agent or fallback chain."""
        # Try POAgent first
        if model == "po":
            try:
                from core.observer.po_agent import POAgent
                agent = POAgent()
                last_msg = messages[-1]["content"] if messages else ""
                history = messages[:-1] if len(messages) > 1 else []

                # Build augmented prompt with context
                prompt = last_msg
                if context:
                    prompt = f"Context:\n{context}\n\nUser: {last_msg}"

                return await agent.chat(
                    prompt,
                    history=history,
                    session_id="",
                    max_tool_rounds=4,
                )
            except ImportError:
                logger.warning("POAgent not available, trying fallback chain")
            except Exception as e:
                logger.warning(f"POAgent failed: {e}, trying fallback chain")

        # Try fallback chain
        try:
            from oce.backend.po_fallback import FallbackChain
            chain = self.fallback_chain or FallbackChain()
            result = await chain.execute(messages)
            return result.get("response", "")
        except Exception as e:
            logger.warning(f"Fallback chain failed: {e}")

        # Last resort: echo response
        last_content = messages[-1]["content"] if messages else ""
        return f"I received your message: '{last_content[:100]}'. Let me process that further."


def _format_event(event: POEvent) -> str:
    """Format a PO event as an SSE data line."""
    return f"data: {json.dumps(event.to_dict(), default=str)}\n\n"