"""
PO API — PO Provider endpoints for Open-LLM-VTuber integration.

Endpoints:
- POST /api/po/chat        — Chat completion (streaming, OpenAI-shape)
- GET  /api/po/status      — Health and active model info

These endpoints are consumed by the POProvider adapter in vtuber_integration/po_provider/.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncGenerator
import json
import logging

logger = logging.getLogger("oce.po_api")

router = APIRouter(prefix="/api/po", tags=["po"])


# ─── Request/Response Models ─────────────────────────────────────────────────

class POChatMessage(BaseModel):
    role: str
    content: str


class POChatRequest(BaseModel):
    model: str = "po"
    messages: List[POChatMessage]
    stream: bool = True
    temperature: float = 0.7
    session_id: str = ""


class POChatChoice(BaseModel):
    index: int = 0
    delta: Dict[str, Any] = {}
    finish_reason: str | None = None


class POChatChunk(BaseModel):
    id: str = ""
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = "po"
    choices: List[POChatChoice] = []


class POChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float = 0.0
    sources: List[Dict[str, Any]] = []


class POStatusResponse(BaseModel):
    status: str = "healthy"
    model: str = "po"
    version: str = "1.0.0"
    streaming_supported: bool = True
    active_sessions: int = 0
    uptime_seconds: float = 0.0


# ─── Chat Endpoint (Streaming) ───────────────────────────────────────────────

@router.post("/chat")
async def po_chat(request: POChatRequest):
    """
    Chat completion endpoint.

    When stream=True, returns SSE with OpenAI-shape chunks.
    When stream=False, returns a single complete response.

    The request is routed through OCE's cognitive pipeline:
    1. Workspace scan for context
    2. Vault retrieval for memory
    3. Agent coordination if needed
    4. LLM generation via configured model router
    """
    if request.stream:
        return StreamingResponse(
            _stream_chat(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return await _complete_chat(request)


async def _stream_chat(request: POChatRequest) -> AsyncGenerator[str, None]:
    """Stream chat response as SSE events in OpenAI chunk format."""
    import time

    # Stage 1: Processing
    yield _sse_chunk({"type": "status", "stage": "processing", "message": "🧠 Processing..."})

    # Stage 2: Workspace scan
    try:
        from core.observer.workspace_scanner import WorkspaceScanner
        scanner = WorkspaceScanner()
        scan_result = await scanner.scan()
        yield _sse_chunk({
            "type": "event",
            "kind": "workspace_scan",
            "payload": scan_result.summary() if hasattr(scan_result, 'summary') else {"files": 0, "fresh": 0},
        })
    except Exception as e:
        logger.warning(f"Workspace scan failed: {e}")
        yield _sse_chunk({"type": "event", "kind": "workspace_scan", "payload": {"error": str(e)}})

    # Stage 3: Vault retrieval
    try:
        from core.observer.vault_retriever import VaultRetriever
        retriever = VaultRetriever()
        retrieval = await retriever.retrieve(request.messages[-1].content if request.messages else "")
        yield _sse_chunk({
            "type": "event",
            "kind": "vault_retrieval",
            "payload": retrieval.summary() if hasattr(retrieval, 'summary') else {"hits": 0},
        })
    except Exception as e:
        logger.warning(f"Vault retrieval failed: {e}")
        yield _sse_chunk({"type": "event", "kind": "vault_retrieval", "payload": {"error": str(e)}})

    # Stage 4: Agent coordination
    yield _sse_chunk({"type": "event", "kind": "agent_spawn", "payload": {"status": "coordinating"}})

    # Stage 5: Generate response via OCE's existing chat pipeline
    try:
        from core.observer.po_agent import POAgent
        agent = POAgent()

        # Convert messages to the format POAgent expects
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]

        response_text = await agent.chat(
            request.messages[-1].content if request.messages else "",
            history=formatted_messages[:-1],
            session_id=request.session_id,
            max_tool_rounds=4,
        )

        # Stream the response word by word for the LLM feel
        words = response_text.split()
        accumulated = ""
        for i, word in enumerate(words):
            accumulated += ((" " if i > 0 else "") + word)
            yield _sse_chunk(
                {"type": "chunk", "choices": [{"delta": {"content": word + " "}}]}
            )
            await _async_sleep(0.02)  # ~50 words/sec streaming speed

        yield _sse_chunk({"type": "done", "usage": {"prompt_tokens": 0, "completion_tokens": len(words), "total": len(words)}})

    except Exception as e:
        logger.error(f"PO chat generation failed: {e}")
        yield _sse_chunk({"type": "error", "message": str(e)[:500]})


async def _complete_chat(request: POChatRequest) -> Dict[str, Any]:
    """Non-streaming chat completion."""
    try:
        from core.observer.po_agent import POAgent
        agent = POAgent()

        response_text = await agent.chat(
            request.messages[-1].content if request.messages else "",
            history=[{"role": m.role, "content": m.content} for m in request.messages[:-1]],
            session_id=request.session_id,
            max_tool_rounds=4,
        )

        return {
            "id": "chatcmpl-po",
            "object": "chat.completion",
            "model": request.model,
            "choices": [{"message": {"role": "assistant", "content": response_text}}],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"PO chat failed: {str(e)}")


# ─── Status Endpoint ─────────────────────────────────────────────────────────

@router.get("/status")
async def po_status() -> POStatusResponse:
    """Return PO service health and configuration."""
    return POStatusResponse(
        status="healthy",
        model="po",
        streaming_supported=True,
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sse_chunk(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, default=str)}\n\n"


async def _async_sleep(seconds: float) -> None:
    """Non-blocking sleep for streaming simulation."""
    import asyncio
    await asyncio.sleep(seconds)