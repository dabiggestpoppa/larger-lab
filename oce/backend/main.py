"""
OCE Continuity Core API
========================
FastAPI backend for Operator Continuity Engine.

Provides endpoints for:
- Continuity chat (preserves goals, trajectories, observer state)
- Observer status monitoring
- Event stream access
- Attractor panel data
- Memory view
- Browser control proxy (OC2 sidecar)
"""
import os
import sys
from pathlib import Path

# --- SINGLETON: Kill duplicates, exit if already running ---
_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "scripts"))
from singleton import enforce_singleton
enforce_singleton("oce_backend", kill_others=True)

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timezone
import asyncio
import json
import logging
import traceback
import httpx

logger = logging.getLogger("oce")

# Import SRRA-OPH adapter
from .srrs_adapter import get_adapter, SRRSAdapter
from .rate_limit_tracker import get_rate_limit_tracker, record_api_call
from .event_fabric import get_fabric, get_router, get_persistence, EventFabric, TopologicalRouter, EventPersistence
from .observer_runtime import get_runtime, ObserverRuntime, ObserverConfig, ObserverState
from .structural_memory import StructuralMemory, MemoryEntry, MemoryLayer, MemoryStats
from .dspy_pipelines import OCEPipelineManager
from .phase4_api import register_phase4_endpoints
from .metrics_collector import get_metrics_collector, MetricsCollector
from .tracing_engine import get_tracing_engine, TracingEngine
from .alerting_engine import get_alerting_engine, AlertingEngine, AlertSeverity
from .execution_engine import get_execution_engine, ExecutionEngine, ExecutionTask, ExecutionStatus, ExecutionPriority
from .execution_api import register_execution_endpoints
from .drift_detector import get_drift_detector, DriftDetector
from .self_healing_engine import get_self_healing_engine, SelfHealingEngine
from .governance_api import register_governance_endpoints
from .command_center import router as command_center_router
from .governance_engine import get_governance_engine, GovernanceEngine, ProposalStatus, ProposalType
from .consensus_engine import get_consensus_engine, ConsensusEngine
from .coevolution_protocol import get_coevolution_protocol, CoevolutionProtocol
from .economics_engine import get_economics_engine, EconomicsEngine
from .sync_cost_optimizer import get_sync_cost_optimizer, SyncCostOptimizer
from .adaptive_compression import get_adaptive_compression, AdaptiveCompression
from .resonance_api import register_resonance_endpoints
from .reconstruction_api import register_reconstruction_endpoints
from .topology_api import register_topology_endpoints
from .sovereign_api import register_sovereign_endpoints
from .vault_api import register_vault_endpoints
from .ml_api import register_ml_endpoints
from .po_api import router as po_router
from .po_tools_api import router as po_tools_router
from .po_mcp_client import MCPToolRegistry, BUILTIN_MCP_SERVERS
from .po_idle import POIdleRuntime, get_idle_runtime, set_idle_runtime

app = FastAPI(
    title="OCE Continuity Core",
    description="Operator Continuity Engine API",
    version="1.0.0"
)

# Serve static frontend files (PO monitor dashboard)
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ─── MCP Tool Registry ──────────────────────────────────────────────────────

mcp_registry = MCPToolRegistry()


@app.on_event("startup")
async def startup_mcp():
    """Connect to all MCP servers on startup."""
    mcp_registry.discover_servers()
    await mcp_registry.connect_all()
    logger.info(f"MCP registry: {len(mcp_registry._tools)} tools from {len(mcp_registry._servers)} servers")


@app.on_event("shutdown")
async def shutdown_mcp():
    """Disconnect from all MCP servers on shutdown."""
    await mcp_registry.disconnect_all()


# ─── Models ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ContinuityChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ObserverStatus(BaseModel):
    observer_id: str
    state: str  # active, idle, monitoring
    entropy: float
    task: str


class EventResponse(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    source: str
    priority: int
    payload: Dict[str, Any]


class AttractorState(BaseModel):
    goal: str
    confidence: float
    entropy_pressure: float
    convergence: float


# ─── Structural Memory Models ────────────────────────────────────────────────

class StoreMemoryRequest(BaseModel):
    layer: str  # WORK, LEARNED, KNOWLEDGE
    content: Dict[str, Any]
    tags: List[str] = []
    ttl_seconds: Optional[int] = None
    source: str = "unknown"


class SearchMemoryRequest(BaseModel):
    q: str = ""
    layer: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 20


class CompressRequest(BaseModel):
    layer: str = "WORK"
    max_entries: int = 1000


# Global structural memory instance
_structural_memory: Optional[StructuralMemory] = None


def get_structural_memory() -> StructuralMemory:
    global _structural_memory
    if _structural_memory is None:
        _structural_memory = StructuralMemory()
    return _structural_memory


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "OCE Continuity Core API", "version": "1.0.0"}


@app.get("/po-monitor")
async def po_monitor_page():
    """Serve the PO Monitor HTML dashboard."""
    _monitor_file = Path(__file__).resolve().parent.parent / "frontend" / "po-monitor.html"
    if _monitor_file.exists():
        return HTMLResponse(content=_monitor_file.read_text(), status_code=200)
    raise HTTPException(status_code=404, detail="PO Monitor page not found")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "oce-continuity-core"}


@app.post("/chat")
async def continuity_chat(request: ContinuityChatRequest):
    """
    Continuity chat endpoint.
    Preserves goals, trajectories, observer state, operational context.
    Uses O-1/O-2/O-3 observer pipeline for intelligent responses.
    """
    try:
        adapter = await get_adapter()
        result = await adapter.process_continuity_message(request.message, request.context)
        return {
            "response": result.get("response", "No response"),
            "session_id": result.get("session_id", request.session_id or "new_session"),
            "continuity_preserved": True,
            "observer": result.get("observer", {}),
            "system": result.get("system", {}),
            "confidence": result.get("confidence", 0),
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=503, detail=f"Continuity service unavailable: {str(e)}")


@app.post("/chat/stream")
async def continuity_chat_stream(request: ContinuityChatRequest):
    """
    Streaming chat endpoint — Server-Sent Events (SSE).
    Bypasses the heavy O-1/O-2/O-3 pipeline for direct ChatAgent responses.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            import queue
            progress_queue = queue.Queue()

            def on_progress(event_type: str, data: dict):
                progress_queue.put({"type": event_type, "data": data})

            def run_agent():
                from core.observer.po_agent import POAgent
                agent = POAgent()
                return agent.chat(
                    request.message,
                    sovereign_context="",
                    max_tool_rounds=8,
                    progress_callback=on_progress,
                )

            loop = asyncio.get_event_loop()
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = loop.run_in_executor(executor, run_agent)

            while not future.done():
                while not progress_queue.empty():
                    try:
                        evt = progress_queue.get_nowait()
                        yield f"data: {json.dumps(evt, default=str)}\n\n"
                    except queue.Empty:
                        break
                yield ": keepalive\n\n"
                await asyncio.sleep(0.5)

            while not progress_queue.empty():
                try:
                    evt = progress_queue.get_nowait()
                    yield f"data: {json.dumps(evt, default=str)}\n\n"
                except queue.Empty:
                    break

            response_text = await asyncio.wait_for(future, timeout=300)

            # Log to chat log for conversation history
            try:
                from core.observer.chat_log import get_chat_log
                chat_log = get_chat_log()
                session_id = request.session_id or chat_log.get_current_session()
                chat_log.add_message(
                    role="user",
                    content=request.message,
                    session_id=session_id,
                    observer_metadata={"source": "chat_stream"},
                )
                chat_log.add_message(
                    role="assistant",
                    content=response_text,
                    session_id=session_id,
                    observer_metadata={"source": "chat_stream"},
                )
            except Exception as log_err:
                logger.warning(f"Chat log write failed (non-critical): {log_err}")

            yield f"data: {json.dumps({'type': 'final', 'data': {'response': response_text, 'session_id': request.session_id or '', 'observer': {}, 'system': {}, 'confidence': 1.0}}, default=str)}\n\n"
            executor.shutdown(wait=False)

        except Exception as e:
            logger.error(f"Stream error: {e}")
            # Log error to chat log
            try:
                from core.observer.chat_log import get_chat_log
                chat_log = get_chat_log()
                session_id = request.session_id or chat_log.get_current_session()
                chat_log.add_message(role="user", content=request.message, session_id=session_id)
                chat_log.add_message(role="assistant", content=f"Error: {str(e)[:200]}", session_id=session_id)
            except Exception:
                pass
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)[:500]}})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Chat Log Endpoints ──────────────────────────────────────────────────────

@app.get("/chat/sessions")
async def get_chat_sessions():
    """List all chat sessions with recent messages."""
    try:
        from core.observer.chat_log import get_chat_log
        chat_log = get_chat_log()
        chat_log.reload()  # Force fresh read from disk
        data = chat_log.to_dict()
        sessions = []
        for sid, s in data.get("sessions", {}).items():
            sessions.append({
                "session_id": s["session_id"],
                "start_time": s["start_time"],
                "last_active": s["last_active"],
                "message_count": s["message_count"],
                "user_message_count": s.get("user_message_count", 0),
                "assistant_message_count": s.get("assistant_message_count", 0),
                "recent_messages": s.get("messages", [])[-5:],
            })
        # Sort by last_active descending
        sessions.sort(key=lambda x: x.get("last_active", ""), reverse=True)
        return {
            "sessions": sessions,
            "active_session": data.get("current_session_id"),
        }
    except Exception as e:
        logger.error(f"Chat sessions error: {e}")
        raise HTTPException(status_code=503, detail=f"Chat log unavailable: {str(e)}")


@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get full conversation history for a session."""
    try:
        from core.observer.chat_log import get_chat_log
        chat_log = get_chat_log()
        messages = chat_log.get_session_messages(session_id)
        summary = chat_log.get_session_summary(session_id)
        return {
            "session": summary,
            "messages": messages,
        }
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=503, detail=f"Chat log unavailable: {str(e)}")


@app.get("/chat/recent")
async def get_recent_messages(limit: int = Query(50, ge=1, le=200)):
    """Get recent messages across all sessions."""
    try:
        from core.observer.chat_log import get_chat_log
        chat_log = get_chat_log()
        messages = chat_log.get_recent_messages(limit=limit)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Chat recent error: {e}")
        raise HTTPException(status_code=503, detail=f"Chat log unavailable: {str(e)}")


@app.get("/chat/search")
async def search_chat_history(q: str = Query(..., min_length=1, max_length=200)):
    """Search chat history by content."""
    try:
        from core.observer.chat_log import get_chat_log
        chat_log = get_chat_log()
        results = chat_log.search_messages(query=q)
        return {
            "query": q,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Chat search error: {e}")
        raise HTTPException(status_code=503, detail=f"Chat log unavailable: {str(e)}")


@app.get("/observers", response_model=List[ObserverStatus])
async def get_observer_status():
    """Live observer status panel."""
    try:
        adapter = await get_adapter()
        obs_status = await adapter.get_observer_status()
        return [ObserverStatus(**s) for s in obs_status]
    except Exception as e:
        logger.error(f"Observer status error: {e}")
        raise HTTPException(status_code=503, detail=f"Observer service unavailable: {str(e)}")


@app.get("/events", response_model=List[EventResponse])
async def get_events(
    limit: int = Query(50, ge=1, le=1000),
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    min_priority: Optional[int] = Query(None, ge=0, le=3),
):
    """Query event history from the Event Fabric."""
    try:
        fabric = get_fabric()
        events = fabric.get_history(
            event_type=event_type,
            source=source,
            limit=limit,
            min_priority=min_priority,
        )
        return [_event_to_response(e) for e in events]
    except Exception as e:
        logger.error(f"Events query error: {e}")
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")


class IngestEventRequest(BaseModel):
    """Request model for event ingestion."""
    event_type: str
    source: str
    payload: Dict[str, Any] = {}
    priority: Optional[int] = None


@app.post("/events/ingest")
async def ingest_event(request: IngestEventRequest):
    """
    Ingest a new event into the Event Fabric.
    Called by Operator tools, SRRA-OPH substrate, and external integrations.
    """
    try:
        fabric = get_fabric()
        event = await fabric.ingest(
            event_type=request.event_type,
            source=request.source,
            payload=request.payload,
            priority=request.priority,
        )
        return {"status": "ingested", "event_id": event.event_id}
    except Exception as e:
        logger.error(f"Event ingest error: {e}")
        raise HTTPException(status_code=503, detail=f"Event ingest failed: {str(e)}")


@app.get("/events/types")
async def get_event_types():
    """List all registered event types."""
    try:
        fabric = get_fabric()
        return fabric.get_event_types()
    except Exception as e:
        logger.error(f"Event types error: {e}")
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")


@app.get("/events/stats")
async def get_event_stats():
    """Event throughput statistics."""
    try:
        fabric = get_fabric()
        return fabric.get_stats()
    except Exception as e:
        logger.error(f"Event stats error: {e}")
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")


@app.get("/events/persistence/stats")
async def get_persistence_stats():
    """Event persistence statistics."""
    try:
        persistence = get_persistence()
        return persistence.get_stats()
    except Exception as e:
        logger.error(f"Persistence stats error: {e}")
        raise HTTPException(status_code=503, detail=f"Persistence service unavailable: {str(e)}")


@app.post("/events/persistence/compress")
async def compress_events(request: dict):
    """Compress old events for a given type."""
    try:
        persistence = get_persistence()
        event_type = request.get("event_type")
        keep_last = request.get("keep_last", 100)
        if not event_type:
            raise HTTPException(status_code=400, detail="event_type required")
        deleted = persistence.compress_old_events(event_type, keep_last)
        return {"ok": True, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compression error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topology/stats")
async def get_topology_stats():
    """Observer topology statistics."""
    try:
        router = get_router()
        return router.get_topology_stats()
    except Exception as e:
        logger.error(f"Topology stats error: {e}")
        raise HTTPException(status_code=503, detail=f"Topology service unavailable: {str(e)}")


@app.post("/topology/edge")
async def update_topology_edge(request: dict):
    """Update coupling weight between two observers."""
    try:
        router = get_router()
        observer_a = request.get("observer_a")
        observer_b = request.get("observer_b")
        weight = request.get("weight", 0.5)
        if not observer_a or not observer_b:
            raise HTTPException(status_code=400, detail="observer_a and observer_b required")
        router.update_edge(observer_a, observer_b, weight)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topology update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/attractor", response_model=AttractorState)
async def get_attractor_state():
    """Current operational goals and convergence state."""
    try:
        adapter = await get_adapter()
        state = await adapter.get_attractor_state()
        return AttractorState(**state)
    except Exception as e:
        logger.error(f"Attractor error: {e}")
        raise HTTPException(status_code=503, detail=f"Attractor service unavailable: {str(e)}")


@app.get("/rate-limit/status")
async def get_rate_limit_status():
    """Get current rate-limit status for all API models."""
    try:
        tracker = get_rate_limit_tracker()
        return tracker.get_status()
    except Exception as e:
        logger.error(f"Rate limit status error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/rate-limit/errors")
async def get_rate_limit_errors(limit: int = Query(20, ge=1, le=100)):
    """Get recent rate-limit errors."""
    try:
        tracker = get_rate_limit_tracker()
        return {"errors": tracker.get_recent_errors(limit)}
    except Exception as e:
        logger.error(f"Rate limit errors error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/rate-limit/record")
async def record_rate_limit(request: dict):
    """Record an API call for rate-limit tracking."""
    try:
        record_api_call(
            model=request.get("model", "unknown"),
            status_code=request.get("status_code", 200),
            error_type=request.get("error_type", ""),
            cost=request.get("cost_usd", 0.0),
            tokens=request.get("tokens_used", 0),
        )
        return {"ok": True}
    except Exception as e:
        logger.error(f"Rate limit record error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memory_view():
    """Trajectory memory, structural memory, repair memory."""
    try:
        adapter = await get_adapter()
        structural = await adapter.get_structural_memory()
        trajectory = await adapter.get_trajectory_memory()
        return {
            "trajectory_memory": trajectory,
            "structural_memory": structural,
            "repair_memory": []
        }
    except Exception as e:
        logger.error(f"Memory error: {e}")
        raise HTTPException(status_code=503, detail=f"Memory service unavailable: {str(e)}")


@app.get("/health/srrs")
async def srrs_health():
    """Check SRRA-OPH substrate health."""
    try:
        adapter = await get_adapter()
        return await adapter.health_check()
    except Exception as e:
        logger.error(f"SRRS health error: {e}")
        return {"status": "unhealthy", "error": str(e)}


# ─── Event Fabric Helpers ─────────────────────────────────────────────────────

def _event_to_response(event) -> Dict[str, Any]:
    """Convert an Event to an API response dict."""
    ts = event.timestamp
    if isinstance(ts, str):
        ts_str = ts
    else:
        try:
            ts_str = ts.isoformat()
        except Exception:
            ts_str = str(ts)
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": ts_str,
        "source": event.source,
        "priority": event.priority,
        "payload": event.payload,
    }


def _event_to_dict(event) -> Dict[str, Any]:
    """Convert an Event to a dict for WebSocket transmission."""
    return _event_to_response(event)


# ─── Agent Action API ─────────────────────────────────────────────────────────
# These endpoints let PO (and other agents) execute actions through OCE.

class AgentActionRequest(BaseModel):
    """Request model for agent-executed actions."""
    action: str  # "run_command", "read_file", "write_file", "edit_file", "run_python", "git_op"
    params: Dict[str, Any] = {}
    agent_id: str = "po"
    session_id: Optional[str] = None


class AgentActionResponse(BaseModel):
    """Response from an agent action."""
    ok: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0


@app.post("/agent/execute", response_model=AgentActionResponse)
async def agent_execute_action(request: AgentActionRequest):
    """
    Execute an action on behalf of an agent.
    This is the main integration point for PO and other external agents
    to interact with the workspace through the OCE backend.

    Actions:
    - run_command: Execute a shell command (params: command, timeout?, cwd?)
    - read_file: Read a file (params: path, start_line?, max_lines?)
    - write_file: Write a file (params: path, content)
    - edit_file: Edit a file (params: path, old_text, new_text)
    - run_python: Execute Python code (params: code, timeout?)
    - git_op: Git operation (params: operation, args?)
    """
    import time as _time
    from pathlib import Path as _Path

    start = _time.time()
    repo_root = _Path(__file__).resolve().parents[2]

    try:
        if request.action == "run_command":
            cmd = request.params.get("command", "")
            timeout = request.params.get("timeout", 30)
            cwd = request.params.get("cwd", str(repo_root))
            import subprocess
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=cwd, encoding="utf-8", errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            return AgentActionResponse(ok=True, result=output[:5000], execution_time_ms=(_time.time()-start)*1000)

        elif request.action == "read_file":
            path = request.params.get("path", "")
            fp = repo_root / path
            if not fp.exists():
                return AgentActionResponse(ok=False, error=f"File not found: {path}")
            content = fp.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            start_line = request.params.get("start_line", 1)
            max_lines = request.params.get("max_lines", 200)
            if start_line > 1 or max_lines < len(lines):
                end = min(start_line - 1 + max_lines, len(lines))
                content = f"[Lines {start_line}-{end} of {len(lines)}]\n" + "\n".join(lines[start_line-1:end])
            return AgentActionResponse(ok=True, result=content[:5000], execution_time_ms=(_time.time()-start)*1000)

        elif request.action == "write_file":
            path = request.params.get("path", "")
            content = request.params.get("content", "")
            fp = repo_root / path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            return AgentActionResponse(ok=True, result=f"Wrote {len(content.splitlines())} lines to {path}", execution_time_ms=(_time.time()-start)*1000)

        elif request.action == "edit_file":
            path = request.params.get("path", "")
            old_text = request.params.get("old_text", "")
            new_text = request.params.get("new_text", "")
            fp = repo_root / path
            if not fp.exists():
                return AgentActionResponse(ok=False, error=f"File not found: {path}")
            content = fp.read_text(encoding="utf-8")
            if old_text not in content:
                return AgentActionResponse(ok=False, error=f"Text not found in {path}")
            new_content = content.replace(old_text, new_text, 1)
            fp.write_text(new_content, encoding="utf-8")
            return AgentActionResponse(ok=True, result=f"Edited {path}", execution_time_ms=(_time.time()-start)*1000)

        elif request.action == "run_python":
            code = request.params.get("code", "")
            timeout = request.params.get("timeout", 60)
            import tempfile, os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                tmp_path = f.name
            python_exe = str(repo_root / ".venv" / "Scripts" / "python.exe")
            import subprocess
            result = subprocess.run(
                [python_exe, tmp_path], capture_output=True, text=True,
                timeout=timeout, cwd=str(repo_root), encoding="utf-8", errors="replace",
            )
            os.unlink(tmp_path)
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            return AgentActionResponse(ok=True, result=output[:5000], execution_time_ms=(_time.time()-start)*1000)

        elif request.action == "git_op":
            operation = request.params.get("operation", "")
            args = request.params.get("args", "")
            allowed_ops = ["status", "log", "diff", "add", "commit", "push", "pull", "branch", "checkout", "stash"]
            if operation not in allowed_ops:
                return AgentActionResponse(ok=False, error=f"Unknown git operation: {operation}. Allowed: {', '.join(allowed_ops)}")
            cmd = f"git {operation} {args}"
            import subprocess
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=str(repo_root), encoding="utf-8", errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            return AgentActionResponse(ok=True, result=output[:5000], execution_time_ms=(_time.time()-start)*1000)

        else:
            return AgentActionResponse(ok=False, error=f"Unknown action: {request.action}")

    except subprocess.TimeoutExpired:
        return AgentActionResponse(ok=False, error="Action timed out", execution_time_ms=(_time.time()-start)*1000)
    except Exception as e:
        return AgentActionResponse(ok=False, error=str(e), execution_time_ms=(_time.time()-start)*1000)


@app.get("/agent/workspace/info")
async def agent_workspace_info():
    """Get workspace info for agents — recent files, git status, service ports."""
    import os
    import socket
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parents[2]
    info = {}

    # Git info
    try:
        import subprocess
        branch = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True,
            cwd=str(repo_root), timeout=5
        ).stdout.strip()
        last_commit = subprocess.run(
            ["git", "log", "-1", "--oneline"], capture_output=True, text=True,
            cwd=str(repo_root), timeout=5
        ).stdout.strip()
        info["git"] = {"branch": branch, "last_commit": last_commit}
    except Exception:
        info["git"] = {"error": "git not available"}

    # Service ports
    ports = {
        "oce_backend": 8000, "oce_frontend": 3000,
        "openclaw": 18790, "po_api": 8765,
    }
    port_states = {}
    for name, port in ports.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            port_states[name] = "up"
        except Exception:
            port_states[name] = "down"
        finally:
            s.close()
    info["services"] = port_states

    # Recent progress files
    try:
        progress_dir = repo_root / "progress"
        if progress_dir.exists():
            files = sorted(progress_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            info["recent_progress"] = [f.name for f in files]
    except Exception:
        pass

    return info


@app.on_event("startup")
async def startup_event():
    """Initialize Event Fabric and PO Idle Runtime on startup."""
    try:
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.startup",
            source="oce-continuity-core",
            payload={"version": "1.0.0", "message": "OCE Continuity Core started"},
        )
        # Start PO Idle Runtime (P3.4 — autonomous background tick)
        idle = get_idle_runtime()
        await idle.start()
        logger.info("OCE Continuity Core started successfully (PO Idle Runtime active)")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop PO Idle Runtime and emit shutdown event."""
    try:
        # Stop PO Idle Runtime cleanly
        idle = get_idle_runtime()
        await idle.stop()
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.shutdown",
            source="oce-continuity-core",
            payload={"message": "OCE Continuity Core shutting down"},
        )
        logger.info("OCE Continuity Core shutting down")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# ─── PO Idle Runtime Endpoints (P3.4) ────────────────────────────────────────

@app.get("/api/po/idle/status")
async def po_idle_status():
    """Get PO Idle Runtime status — tick count, uptime, session state, last tick."""
    idle = get_idle_runtime()
    last_report = idle.last_tick_report
    return {
        "running": idle.is_running,
        "tick_count": idle.tick_count,
        "uptime_seconds": round(idle.uptime_seconds, 1),
        "session_state": idle._get_session_state().value if idle.is_running else "stopped",
        "cadence_seconds": idle._compute_cadence() if idle.is_running else 0,
        "last_tick": {
            "ts": last_report.ts,
            "cadence": last_report.cadence,
            "session_state": last_report.session_state.value,
            "vault_sync": {
                "entries_indexed": last_report.vault_sync.entries_indexed,
                "entries_pruned": last_report.vault_sync.entries_pruned,
                "duration_ms": last_report.vault_sync.duration_ms,
            } if last_report and last_report.vault_sync else None,
            "memory_distill": {
                "work_compressed": last_report.memory_distill.work_compressed,
                "learned_created": last_report.memory_distill.learned_created,
                "compression_ratio": last_report.memory_distill.compression_ratio,
            } if last_report and last_report.memory_distill else None,
        } if last_report else None,
    }


@app.post("/api/po/idle/notify")
async def po_idle_notify():
    """Notify PO Idle Runtime that a request was handled (resets active timer)."""
    idle = get_idle_runtime()
    idle.notify_request()
    return {"status": "ok", "message": "Active timer reset"}


# ─── WebSocket for Real-time Updates ──────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()



# Pipeline manager
pipeline_manager = OCEPipelineManager()


@app.get("/pipelines/status")
async def get_pipeline_status():
    """Get status of all DSPy pipelines."""
    try:
        return pipeline_manager.get_status()
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")


@app.post("/pipelines/contract/generate")
async def generate_contract(request: dict):
    """Generate optimized prediction contract parameters."""
    try:
        result = pipeline_manager.generate_contract(
            mutation_type=request.get("mutation_type", "unknown"),
            target=request.get("target", "unknown"),
            historical_accuracy=request.get("historical_accuracy", 0.5),
            coherence_metrics=request.get("coherence_metrics"),
        )
        return result
    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")


@app.post("/pipelines/event/route")
async def route_event(request: dict):
    """Route an event through optimal path."""
    try:
        result = pipeline_manager.route_event(
            event_type=request.get("event_type", "unknown"),
            observer_state=request.get("observer_state", {}),
            entropy_level=request.get("entropy_level", 0.0),
        )
        return result
    except Exception as e:
        logger.error(f"Event routing error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")


@app.post("/pipelines/evolution/plan")
async def plan_evolution(request: dict):
    """Plan adaptive evolution."""
    try:
        result = pipeline_manager.plan_evolution(
            current_metrics=request.get("current_metrics", {}),
            budget=request.get("entropy_budget_remaining", 500.0),
            targets=request.get("coherence_targets", {}),
        )
        return result
    except Exception as e:
        logger.error(f"Evolution planning error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")

# ─── Observer Runtime Endpoints ──────────────────────────────────────────────

@app.post("/observers")
async def create_observer(request: dict):
    """Create a new observer."""
    try:
        runtime = get_runtime()
        config = ObserverConfig(**request)
        observer = await runtime.create_observer(config)
        return {
            "observer_id": observer.observer_id,
            "state": observer.state.value,
            "created_at": observer.created_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Create observer error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/observers")
async def list_observers(
    state: Optional[str] = None,
    observer_type: Optional[str] = None,
):
    """List all observers with optional filters."""
    try:
        runtime = get_runtime()
        state_enum = ObserverState(state) if state else None
        observers = runtime.list_observers(state=state_enum, observer_type=observer_type)
        return [
            {
                "observer_id": o.observer_id,
                "name": o.config.name,
                "type": o.config.observer_type,
                "state": o.state.value,
                "health_score": o.health_score,
                "event_count": o.event_count,
                "created_at": o.created_at.isoformat(),
            }
            for o in observers
        ]
    except Exception as e:
        logger.error(f"List observers error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/observers/{observer_id}")
async def get_observer(observer_id: str):
    """Get observer details."""
    try:
        runtime = get_runtime()
        observer = runtime.get_observer(observer_id)
        if not observer:
            raise HTTPException(status_code=404, detail="Observer not found")
        return {
            "observer_id": observer.observer_id,
            "config": observer.config.model_dump(),
            "state": observer.state.value,
            "health_score": observer.health_score,
            "entropy": observer.entropy,
            "event_count": observer.event_count,
            "error_count": observer.error_count,
            "created_at": observer.created_at.isoformat(),
            "activated_at": observer.activated_at.isoformat() if observer.activated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/observers/{observer_id}/health")
async def get_observer_health(observer_id: str):
    """Get observer health metrics."""
    try:
        runtime = get_runtime()
        health = runtime.get_observer_health(observer_id)
        if not health:
            raise HTTPException(status_code=404, detail="Observer not found")
        return health.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Observer health error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/observers/{observer_id}/activate")
async def activate_observer(observer_id: str):
    """Activate an observer."""
    try:
        runtime = get_runtime()
        observer = await runtime.activate_observer(observer_id)
        if not observer:
            raise HTTPException(status_code=404, detail="Observer not found or destroyed")
        return {"observer_id": observer.observer_id, "state": observer.state.value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/observers/{observer_id}/suspend")
async def suspend_observer(observer_id: str):
    """Suspend an observer."""
    try:
        runtime = get_runtime()
        observer = await runtime.suspend_observer(observer_id)
        if not observer:
            raise HTTPException(status_code=404, detail="Observer not found or destroyed")
        return {"observer_id": observer.observer_id, "state": observer.state.value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suspend observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.delete("/observers/{observer_id}")
async def destroy_observer(observer_id: str):
    """Destroy an observer."""
    try:
        runtime = get_runtime()
        success = await runtime.destroy_observer(observer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Observer not found")
        return {"observer_id": observer_id, "state": "destroyed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Destroy observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/observers/{observer_id}/subscribe")
async def subscribe_observer(observer_id: str, request: dict):
    """Subscribe an observer to event types."""
    try:
        runtime = get_runtime()
        observer = runtime.get_observer(observer_id)
        if not observer:
            raise HTTPException(status_code=404, detail="Observer not found")
        event_types = request.get("event_types", [])
        if event_types:
            fabric = get_fabric()
            fabric.subscribe(
                callback=lambda e, oid=observer_id: runtime._handle_event(oid, e),
                event_types=event_types,
            )
        return {"observer_id": observer_id, "subscribed_to": event_types}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscribe observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/observers/stats")
async def get_observer_stats():
    """Get Observer Runtime statistics."""
    try:
        runtime = get_runtime()
        return runtime.get_stats()
    except Exception as e:
        logger.error(f"Observer stats error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.websocket("/ws/observers")
async def websocket_observers(websocket: WebSocket):
    """WebSocket endpoint for real-time observer updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic observer health updates
            runtime = get_runtime()
            stats = runtime.get_stats()
            await websocket.send_text(json.dumps({
                "type": "observer_stats",
                "data": stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("Observer WebSocket client disconnected")
    except asyncio.CancelledError:
        logger.info("Observer WebSocket connection cancelled")
    except Exception as e:
        logger.error(f"Observer WebSocket error: {e}")
    finally:
        try:
            manager.disconnect(websocket)
        except Exception:
            pass


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event stream from Event Fabric."""
    await manager.connect(websocket)
    fabric = get_fabric()
    queue = fabric.create_stream()
    try:
        async for event in fabric.stream_events(queue):
            if event is None:
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "event",
                    "data": _event_to_dict(event),
                }))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        logger.info("WebSocket connection cancelled")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except Exception:
            pass
    finally:
        try:
            fabric.close_stream(queue)
        except Exception:
            pass
        try:
            manager.disconnect(websocket)
        except Exception:
            pass


# ─── Structural Memory Endpoints ────────────────────────────────────────────

@app.post("/memory/store")
async def memory_store(request: StoreMemoryRequest):
    """Store a memory entry."""
    try:
        sm = get_structural_memory()
        entry = MemoryEntry(
            layer=MemoryLayer(request.layer.upper()),
            content=request.content,
            tags=request.tags,
            ttl_seconds=request.ttl_seconds,
            source=request.source,
        )
        entry_id = sm.store(entry)
        return {"entry_id": entry_id, "status": "stored"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid layer: {request.layer}")
    except Exception as e:
        logger.error(f"Memory store error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/memory/search")
async def memory_search(
    q: str = "",
    layer: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 20,
):
    """Search memories by query, layer, and tags."""
    try:
        sm = get_structural_memory()
        layer_enum = MemoryLayer(layer.upper()) if layer else None
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        entries = sm.search(query=q, layer=layer_enum, tags=tag_list, limit=limit)
        return [
            {
                "entry_id": e.entry_id,
                "layer": e.layer.value,
                "content": e.content,
                "tags": e.tags,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
                "source": e.source,
            }
            for e in entries
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/memory/timeline/{observer_id}")
async def memory_timeline(
    observer_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """Get chronological memory for an observer."""
    try:
        sm = get_structural_memory()
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        entries = sm.get_timeline(observer_id, start_time=start, end_time=end)
        return [
            {
                "entry_id": e.entry_id,
                "layer": e.layer.value,
                "content": e.content,
                "tags": e.tags,
                "created_at": e.created_at.isoformat(),
                "source": e.source,
            }
            for e in entries
        ]
    except Exception as e:
        logger.error(f"Memory timeline error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/memory/compress")
async def memory_compress(request: CompressRequest):
    """Trigger compression on a memory layer."""
    try:
        sm = get_structural_memory()
        removed = sm.compress(MemoryLayer(request.layer.upper()), max_entries=request.max_entries)
        return {"layer": request.layer.upper(), "removed": removed}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Memory compress error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/memory/export")
async def memory_export():
    """Export knowledge layer as wiki markdown."""
    try:
        sm = get_structural_memory()
        md = sm.export_wiki()
        return {"markdown": md}
    except Exception as e:
        logger.error(f"Memory export error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    try:
        sm = get_structural_memory()
        stats = sm.get_stats()
        return stats.model_dump()
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# Register Phase 4 endpoints
register_phase4_endpoints(app)

# Register Phase 6 Execution endpoints
register_execution_endpoints(app)

# Register Phase 8 Governance endpoints
register_governance_endpoints(app)

# Register V3 Phase 1 Resonance endpoints
register_resonance_endpoints(app)

# Register V3 Phase 2 Reconstruction endpoints
register_reconstruction_endpoints(app)

# Register V3 Phase 3 Topology endpoints
register_topology_endpoints(app)

# Register V3 Phase 4 Sovereign endpoints
register_sovereign_endpoints(app)

# Register O-6 Substrate endpoints
from .substrate_api import register_substrate_endpoints
register_substrate_endpoints(app)

# Register O-7 Persistent Field endpoints
from .persistent_field_api import register_persistent_field_endpoints
register_persistent_field_endpoints(app)

# Register O2C Phase 00 + Phase 01 Vault/Cognitive Mesh endpoints
register_vault_endpoints(app)

# Register CEREBUS ML API endpoints
register_ml_endpoints(app)

# Register O2C × MAD LABS Research Mesh endpoints
from .research_api import register_research_endpoints
register_research_endpoints(app)

# Register RCE (Research Cognition Engine) API endpoints
from .rce_api import router as rce_router
app.include_router(rce_router)

# Register PO Monitor (action tracker + learning log)
from .po_monitor import router as po_monitor_router
app.include_router(po_monitor_router)

# Register PO API endpoints (PO × VTuber integration)
app.include_router(po_router)

# Register PO Tools API (all Copilot-equivalent capabilities)
app.include_router(po_tools_router)

# MCP proxy endpoint — forward tool calls to MCP servers
@app.get("/api/po/mcp/tools")
async def list_mcp_tools():
    """List all tools from connected MCP servers."""
    return {"tools": mcp_registry.list_all_tools(), "servers": list(mcp_registry._servers.keys())}


@app.post("/api/po/mcp/call")
async def call_mcp_tool(server: str, tool_name: str, arguments: Dict[str, Any] = {}):
    """Call a tool on a specific MCP server."""
    result = await mcp_registry.call_tool(server, tool_name, arguments)
    return {"server": server, "tool": tool_name, "result": result}


app.include_router(command_center_router)

# ─── Phase 7: Evolution API ──────────────────────────────────────────────────

@app.get("/evolution/status")
async def evolution_status():
    """Get current evolution state (drift + healing)."""
    try:
        drift = get_drift_detector()
        healing = get_self_healing_engine()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drift": {
                "thresholds": drift._thresholds,
                "alert_callbacks_registered": len(drift._alert_callbacks),
            },
            "healing": healing.get_stats(),
        }
    except Exception as e:
        logger.error(f"Evolution status error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/drift")
async def evolution_drift(window_hours: int = Query(24, ge=1, le=168)):
    """Get drift report for the specified time window."""
    try:
        drift = get_drift_detector()
        report = drift.get_drift_report(window_hours=window_hours)
        return report
    except Exception as e:
        logger.error(f"Evolution drift error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/recommendations")
async def evolution_recommendations(time_range_hours: int = Query(24, ge=1, le=168)):
    """Get self-healing recommendations based on failure analysis."""
    try:
        healing = get_self_healing_engine()
        patterns = healing.analyze_failures(time_range_hours=time_range_hours)
        recommendations = healing.generate_recommendations(patterns)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns_found": len(patterns),
            "recommendations": [r.to_dict() for r in recommendations],
        }
    except Exception as e:
        logger.error(f"Evolution recommendations error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/evolution/tune")
async def evolution_tune():
    """Trigger auto-tuning (combines DSPy optimizer + drift data)."""
    try:
        from .dspy_execution_optimizer import get_optimizer
        engine = get_execution_engine()
        drift = get_drift_detector()
        history_stats = engine.history.get_stats()

        optimizer = get_optimizer()
        recommended = optimizer.recommend_workers(
            current_workers=engine.max_workers,
            history_stats=history_stats,
        )

        old_workers = engine.max_workers
        engine.max_workers = recommended

        # Also check drift for additional tuning
        report = drift.get_drift_report(window_hours=6)
        drift_detected = report.get("drift_detected", False)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_workers": old_workers,
            "recommended_workers": recommended,
            "tuned": recommended != old_workers,
            "drift_detected": drift_detected,
            "drift_report": report if drift_detected else None,
        }
    except Exception as e:
        logger.error(f"Evolution tune error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/evolution/heal")
async def evolution_heal():
    """Execute self-healing based on current drift report."""
    try:
        drift = get_drift_detector()
        healing = get_self_healing_engine()

        report = drift.get_drift_report(window_hours=6)
        actions = healing.auto_heal(drift_report=report)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions_taken": len(actions),
            "actions": [a.to_dict() for a in actions],
        }
    except Exception as e:
        logger.error(f"Evolution heal error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/history")
async def evolution_history(limit: int = Query(50, ge=1, le=500)):
    """Get evolution action history (drift reports + healing actions)."""
    try:
        drift = get_drift_detector()
        healing = get_self_healing_engine()

        drift_history = drift.get_drift_history(limit=limit)
        healing_history = healing.get_healing_history(limit=limit)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drift_history": drift_history,
            "healing_history": healing_history,
        }
    except Exception as e:
        logger.error(f"Evolution history error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Observability Models (Phase 5) ──────────────────────────────────────────

class AlertRuleRequest(BaseModel):
    name: str
    metric: str
    threshold: float
    comparison: str = "lt"
    severity: str = "warning"
    cooldown_sec: int = 300
    description: str = ""
    auto_repair: bool = False


# ─── Observability API: Metrics ──────────────────────────────────────────────

@app.get("/metrics")
async def get_metrics():
    """Get current metrics summary."""
    try:
        collector = get_metrics_collector()
        return collector.get_metrics_summary()
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/metrics/history")
async def get_metrics_history(
    metric_name: str = Query(..., description="Dot-path metric name, e.g., events.rate_per_sec"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get historical metrics for a specific metric path."""
    try:
        collector = get_metrics_collector()
        return collector.get_metrics_history(metric_name, limit)
    except Exception as e:
        logger.error(f"Metrics history error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Observability API: Traces ───────────────────────────────────────────────

@app.get("/traces")
async def get_traces(
    active: bool = Query(False, description="Return only active traces"),
    event_type: Optional[str] = None,
    outcome: Optional[str] = None,
    source: Optional[str] = None,
    min_latency_ms: Optional[float] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """List traces. Use active=true for in-flight, or search with filters."""
    try:
        engine = get_tracing_engine()
        if active:
            return engine.get_active_traces()
        return engine.search_traces(
            event_type=event_type,
            outcome=outcome,
            source=source,
            min_latency_ms=min_latency_ms,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Traces error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/traces/{trace_id}")
async def get_trace_detail(trace_id: str):
    """Get full trace detail by ID."""
    try:
        engine = get_tracing_engine()
        trace = engine.get_trace(trace_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="Trace not found")
        return trace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trace detail error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/traces/observer/{observer_id}")
async def get_traces_by_observer(
    observer_id: str,
    limit: int = Query(50, ge=1, le=500),
):
    """Get all traces that passed through a specific observer."""
    try:
        engine = get_tracing_engine()
        return engine.get_traces_by_observer(observer_id, limit)
    except Exception as e:
        logger.error(f"Traces by observer error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Observability API: Alerts ───────────────────────────────────────────────

@app.get("/alerts")
async def get_alerts():
    """Get all active alerts."""
    try:
        engine = get_alerting_engine()
        return engine.get_active_alerts()
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000),
):
    """Get alert history."""
    try:
        engine = get_alerting_engine()
        return engine.get_alert_history(limit)
    except Exception as e:
        logger.error(f"Alert history error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an active alert."""
    try:
        engine = get_alerting_engine()
        if engine.acknowledge_alert(alert_id):
            return {"ok": True, "alert_id": alert_id, "state": "acknowledged"}
        raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledge error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/alerts/rules")
async def add_alert_rule(request: AlertRuleRequest):
    """Add a custom alert rule."""
    try:
        engine = get_alerting_engine()
        rule_id = engine.add_rule(
            name=request.name,
            metric=request.metric,
            threshold=request.threshold,
            comparison=request.comparison,
            severity=request.severity,
            cooldown_sec=request.cooldown_sec,
            description=request.description,
            auto_repair=request.auto_repair,
        )
        return {"ok": True, "rule_id": rule_id}
    except Exception as e:
        logger.error(f"Add alert rule error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Observability API: Dashboard ────────────────────────────────────────────

@app.get("/dashboard")
async def get_dashboard():
    """Full observability dashboard data (metrics + alerts + traces summary)."""
    try:
        collector = get_metrics_collector()
        tracing = get_tracing_engine()
        alerting = get_alerting_engine()
        return {
            "metrics": collector.get_metrics_summary(),
            "alerts": {
                "active": alerting.get_active_alerts(),
                "stats": alerting.get_stats(),
            },
            "traces": {
                "active_count": len(tracing.get_active_traces()),
                "stats": tracing.get_stats(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Observability API: WebSocket Streams ────────────────────────────────────

@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    """Real-time metrics stream. Sends metrics snapshot every 5 seconds."""
    await websocket.accept()
    collector = get_metrics_collector()
    try:
        while True:
            summary = collector.get_metrics_summary()
            await websocket.send_json(summary)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("Metrics WebSocket disconnected")
    except Exception as e:
        logger.error(f"Metrics WS error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """Real-time alert stream. Sends active alerts every 10 seconds."""
    await websocket.accept()
    engine = get_alerting_engine()
    try:
        while True:
            alerts = engine.get_active_alerts()
            stats = engine.get_stats()
            await websocket.send_json({"alerts": alerts, "stats": stats})
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        logger.info("Alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Alerts WS error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


# ─── Phase 9: Entropy Economics Endpoints ────────────────────────────────────

@app.get("/economics/status")
async def economics_status():
    """Get current economics state: budget, yield, entropy debt."""
    try:
        engine = get_economics_engine()
        return {
            "budget": engine.get_budget_status(),
            "yield": engine.get_coherence_yield(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/economics/yield")
async def economics_yield():
    """Get current coherence yield."""
    try:
        return get_economics_engine().get_coherence_yield()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/economics/budget")
async def economics_budget():
    """Get entropy budget status."""
    try:
        return get_economics_engine().get_budget_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/economics/allocate")
async def economics_allocate(request: dict):
    """Allocate entropy budget to a task type."""
    try:
        engine = get_economics_engine()
        return engine.allocate_budget(
            task_type=request.get("task_type", "unknown"),
            amount=request.get("amount", 0.0),
            reason=request.get("reason", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/economics/reallocate")
async def economics_reallocate(request: dict):
    """Reallocate entropy budget between task types."""
    try:
        engine = get_economics_engine()
        return engine.reallocate_budget(
            from_type=request.get("from_type", ""),
            to_type=request.get("to_type", ""),
            amount=request.get("amount", 0.0),
            reason=request.get("reason", ""),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/economics/sync-cost")
async def economics_sync_cost():
    """Get sync cost report."""
    try:
        return get_sync_cost_optimizer().get_sync_cost_report()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/economics/optimize")
async def economics_optimize():
    """Run yield optimization and return suggestions."""
    try:
        engine = get_economics_engine()
        return engine.optimize_yield()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/economics/forecast")
async def economics_forecast(horizon_hours: int = Query(24, ge=1, le=720)):
    """Forecast sustainability."""
    try:
        return get_economics_engine().forecast_sustainability(horizon_hours)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/economics/compress")
async def economics_compress(request: dict):
    """Compress a memory layer."""
    try:
        engine = get_adaptive_compression()
        layer = request.get("layer", "WORK")
        data = request.get("data", {})
        target_ratio = request.get("target_ratio", 0.6)
        return engine.compress_layer(layer, data, target_ratio)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# ─── O-2: Observer Consensus Endpoints ───────────────────────────────────────


@app.get("/consensus/status")
async def get_consensus_status():
    """Get observer consensus statistics."""
    try:
        adapter = await get_adapter()
        return adapter._observer_consensus.get_stats()
    except Exception as e:
        logger.error(f"Consensus status error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/consensus/history")
async def get_consensus_history(limit: int = Query(50, ge=1, le=500)):
    """Get recent consensus decisions."""
    try:
        adapter = await get_adapter()
        return adapter._observer_consensus.get_consensus_history(limit)
    except Exception as e:
        logger.error(f"Consensus history error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/consensus/specializations")
async def get_observer_specializations():
    """Get observer specialization data."""
    try:
        adapter = await get_adapter()
        return adapter._observer_specialization.get_specializations()
    except Exception as e:
        logger.error(f"Specializations error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── O-3: Spawn Engine Endpoints ─────────────────────────────────────────────


@app.get("/spawn/status")
async def get_spawn_status():
    """Get spawn engine status."""
    try:
        adapter = await get_adapter()
        return {
            "registry": adapter._spawn_registry.get_field_snapshot(),
            "active": adapter._agent_spawner.get_active_spawns(),
        }
    except Exception as e:
        logger.error(f"Spawn status error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/spawn/history")
async def get_spawn_history(limit: int = Query(50, ge=1, le=500)):
    """Get spawn history."""
    try:
        adapter = await get_adapter()
        return adapter._spawn_registry.get_history(limit)
    except Exception as e:
        logger.error(f"Spawn history error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/spawn/traces")
async def get_spawn_traces(
    task_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """Get execution traces."""
    try:
        adapter = await get_adapter()
        return adapter._trace_feedback.get_traces(task_type, limit)
    except Exception as e:
        logger.error(f"Traces error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/observer/health")
async def get_observer_health():
    """Get Primary Observer health status."""
    try:
        adapter = await get_adapter()
        return adapter._primary_observer.health
    except Exception as e:
        logger.error(f"Observer health error: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ─── Browser Control Proxy (OC2 Sidecar) ─────────────────────────────────────

OC2_BROWSER_URL = "http://127.0.0.1:18792"
OC2_BROWSER_TOKEN = "oc2-68cdb0729953cce1aecaf09a9dffddac574c9a674f46aa77"


@app.get("/browser")
async def browser_proxy_get(path: str = ""):
    """Proxy GET requests to OC2 browser control sidecar."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{OC2_BROWSER_URL}/{path}" if path else OC2_BROWSER_URL
            resp = await client.get(
                url,
                headers={"Authorization": OC2_BROWSER_TOKEN},
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        logger.error(f"Browser proxy GET error: {e}")
        raise HTTPException(status_code=503, detail=f"Browser control unavailable: {str(e)}")


@app.post("/browser")
async def browser_proxy_post(request: dict):
    """Proxy POST requests to OC2 browser control sidecar."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OC2_BROWSER_URL,
                json=request,
                headers={"Authorization": OC2_BROWSER_TOKEN},
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        logger.error(f"Browser proxy POST error: {e}")
        raise HTTPException(status_code=503, detail=f"Browser control unavailable: {str(e)}")


@app.get("/browser/status")
async def browser_status():
    """Check OC2 browser control sidecar status."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{OC2_BROWSER_URL}/status",
                headers={"Authorization": OC2_BROWSER_TOKEN},
            )
            return {"status": "available", "response": resp.json()}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


# ─── Frontend API Aliases (/api/* → existing endpoints) ──────────────────────
# The Next.js frontend proxies /api/* → /api/* on the backend.
# These aliases map frontend-expected paths to existing OCE endpoints.

@app.get("/api/topology")
async def api_topology():
    """Frontend alias: /api/topology → topology graph with observer nodes."""
    import math
    try:
        adapter = await get_adapter()
        obs_status = await adapter.get_observer_status()
        nodes = []
        count = max(len(obs_status), 1)
        for i, obs in enumerate(obs_status):
            angle = (2 * math.pi * i) / count
            radius = 150
            nodes.append({
                "id": obs.get("observer_id", f"obs-{i}"),
                "label": obs.get("observer_id", f"obs-{i}"),
                "type": "observer",
                "status": obs.get("state", "active"),
                "entropy": obs.get("entropy", 0.0),
                "syncScore": 1.0 - obs.get("entropy", 0.0),
                "repairState": "idle",
                "x": 400 + radius * math.cos(angle),
                "y": 300 + radius * math.sin(angle),
            })
        edges = []
        for i in range(len(nodes) - 1):
            edges.append({
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"],
                "strength": 0.5,
                "type": "routing",
            })
        # If no observers from adapter, provide seed data for UI testing
        if not nodes:
            seed_observers = [
                {"id": "CC", "label": "CC (Claude Code)", "type": "orchestrator", "status": "active", "entropy": 0.05},
                {"id": "OC2", "label": "OC2 (OWL)", "type": "operator", "status": "active", "entropy": 0.08},
                {"id": "AS", "label": "AS (Assistant)", "type": "quality", "status": "active", "entropy": 0.03},
                {"id": "PM", "label": "PM (Polymorph)", "type": "debugger", "status": "active", "entropy": 0.12},
                {"id": "PM2", "label": "PM2 (Polymorph 2)", "type": "experimental", "status": "synced", "entropy": 0.07},
                {"id": "RL", "label": "RL (Researcher)", "type": "research", "status": "active", "entropy": 0.15},
            ]
            count = len(seed_observers)
            for i, obs in enumerate(seed_observers):
                angle = (2 * math.pi * i) / count
                radius = 150
                nodes.append({
                    "id": obs["id"],
                    "label": obs["label"],
                    "type": obs["type"],
                    "status": obs["status"],
                    "entropy": obs["entropy"],
                    "syncScore": 1.0 - obs["entropy"],
                    "repairState": "idle",
                    "x": 400 + radius * math.cos(angle),
                    "y": 300 + radius * math.sin(angle),
                })
            # Create a ring of edges
            for i in range(len(nodes)):
                edges.append({
                    "source": nodes[i]["id"],
                    "target": nodes[(i + 1) % len(nodes)]["id"],
                    "strength": 0.5 + (0.3 * (1 - nodes[i]["entropy"])),
                    "type": "routing",
                })
            # Add cross-edges
            if len(nodes) >= 4:
                edges.append({"source": nodes[0]["id"], "target": nodes[3]["id"], "strength": 0.3, "type": "sync"})
                edges.append({"source": nodes[1]["id"], "target": nodes[4]["id"], "strength": 0.3, "type": "sync"})
        try:
            router = get_router()
            stats = router.get_topology_stats()
        except Exception:
            stats = {"observers": len(nodes), "edges": len(edges), "avg_coupling": 0.5, "density": round(len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1), 2)}
        return {"nodes": nodes, "edges": edges, "stats": stats}
    except Exception as e:
        logger.error(f"API topology error: {e}")
        return {"nodes": [], "edges": [], "stats": {}}


@app.get("/api/health")
async def api_health():
    """Frontend alias: /api/health."""
    return {"status": "healthy", "service": "oce-continuity-core"}


@app.get("/api/chat/sessions")
async def api_chat_sessions():
    """Frontend alias: /api/chat/sessions."""
    try:
        adapter = await get_adapter()
        sessions = await adapter.get_chat_sessions()
        return {"sessions": sessions}
    except Exception:
        return {"sessions": []}


@app.post("/api/chat")
async def api_chat(request: dict):
    """Frontend alias: /api/chat → /chat."""
    try:
        adapter = await get_adapter()
        message = request.get("message", "")
        result = await adapter.process_continuity_message(message, request.get("context"))
        return {
            "response": result.get("response", "No response"),
            "session_id": request.get("session_id", "new_session"),
            "continuity_preserved": True,
            "observer": result.get("observer", {}),
            "system": result.get("system", {}),
            "confidence": result.get("confidence", 0),
        }
    except Exception as e:
        logger.error(f"API chat error: {e}")
        raise HTTPException(status_code=503, detail=f"Chat unavailable: {str(e)}")


@app.post("/api/chat/stream")
async def api_chat_stream(request: dict):
    """Frontend streaming alias: /api/chat/stream with SSE."""
    try:
        adapter = await get_adapter()
        message = request.get("message", "")
        context = request.get("context")

        # Collect progress events thread-safely
        progress_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_progress(event_type: str, data: dict):
            """Thread-safe: called from thread pool, puts into async queue."""
            try:
                evt = {"type": event_type, "data": data}
                loop.call_soon_threadsafe(progress_queue.put_nowait, evt)
            except Exception:
                pass

        async def event_generator():
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

            def run_sync_agent():
                from core.observer.po_agent import POAgent
                agent = POAgent()
                return agent.chat(
                    message,
                    sovereign_context="",
                    max_tool_rounds=8,
                    progress_callback=on_progress,
                )

            future = loop.run_in_executor(executor, run_sync_agent)

            # Stream progress events and keepalive
            while not future.done():
                while not progress_queue.empty():
                    try:
                        evt = progress_queue.get_nowait()
                        yield f"data: {json.dumps(evt, default=str)}\n\n"
                    except asyncio.QueueEmpty:
                        break
                yield ": keepalive\n\n"
                await asyncio.sleep(0.3)

            # Drain remaining events
            await asyncio.sleep(0.2)
            while not progress_queue.empty():
                try:
                    evt = progress_queue.get_nowait()
                    yield f"data: {json.dumps(evt, default=str)}\n\n"
                except asyncio.QueueEmpty:
                    break

            response_text = await asyncio.wait_for(future, timeout=300)

            final_response = {
                "type": "final",
                "data": {
                    "response": response_text,
                    "session_id": request.get("session_id", ""),
                    "observer": {"task_domain": "chat", "complexity": "simple"},
                    "system": {},
                    "confidence": 1.0,
                }
            }
            yield f"data: {json.dumps(final_response, default=str)}\n\n"
            executor.shutdown(wait=False)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"API stream error: {e}")
        raise HTTPException(status_code=503, detail=f"Stream unavailable: {str(e)}")


@app.post("/api/chat/sessions")
async def api_create_chat_session(request: dict):
    """Frontend alias: create new chat session."""
    return {"session_id": f"session-{datetime.now(timezone.utc).timestamp()}", "created": True}


@app.get("/api/entropy/timeseries")
async def api_entropy_timeseries():
    """Frontend alias: /api/entropy/timeseries."""
    try:
        fabric = get_fabric()
        events = fabric.get_history(event_type="entropy", limit=100)
        timeseries = []
        for e in events:
            payload = e.payload if hasattr(e, 'payload') else {}
            timeseries.append({
                "timestamp": e.timestamp if hasattr(e, 'timestamp') else "",
                "entropy_before": payload.get("entropy_before", 0),
                "entropy_after": payload.get("entropy_after", 0),
                "delta": payload.get("delta", 0),
            })
        return {"timeseries": timeseries}
    except Exception:
        return {"timeseries": []}


@app.get("/api/repair/state")
async def api_repair_state():
    """Frontend alias: /api/repair/state."""
    try:
        healing = get_self_healing_engine()
        stats = healing.get_stats()
        return {
            "active": stats.get("active_repairs", []),
            "completed": stats.get("completed_repairs", []),
            "failed": stats.get("failed_repairs", []),
            "saturation": stats.get("saturation", 0.0),
        }
    except Exception:
        return {"active": [], "completed": [], "failed": [], "saturation": 0.0}


@app.get("/api/temporal/timeline")
async def api_temporal_timeline():
    """Frontend alias: /api/temporal/timeline."""
    try:
        fabric = get_fabric()
        events = fabric.get_history(limit=200)
        frames = []
        for i, e in enumerate(events):
            frames.append({
                "frameId": f"frame_{i}",
                "timestamp": e.timestamp if hasattr(e, 'timestamp') else i * 1000,
                "topologySnapshot": {"nodes": [], "edges": []},
                "entropySnapshot": {"local": 0, "cluster": 0, "global": 0},
                "repairSnapshot": {"active": [], "completed": []},
                "events": [{"type": e.event_type if hasattr(e, 'event_type') else "unknown"}],
                "observerStates": {},
            })
        return {"frames": frames}
    except Exception:
        return {"frames": []}


@app.get("/api/sessions")
async def api_sessions():
    """Frontend alias: /api/sessions."""
    try:
        adapter = await get_adapter()
        sessions = await adapter.get_chat_sessions()
        return {"sessions": sessions}
    except Exception:
        return {"sessions": []}


@app.get("/api/observers")
async def api_observers():
    """Frontend alias: /api/observers → /observers."""
    try:
        adapter = await get_adapter()
        obs_status = await adapter.get_observer_status()
        return {"observers": obs_status}
    except Exception:
        return {"observers": []}


@app.get("/api/events")
async def api_events(limit: int = Query(50, ge=1, le=1000)):
    """Frontend alias: /api/events → /events."""
    try:
        fabric = get_fabric()
        events = fabric.get_history(limit=limit)
        return {"events": [
            {
                "event_id": e.event_id if hasattr(e, 'event_id') else str(i),
                "event_type": e.event_type if hasattr(e, 'event_type') else "unknown",
                "timestamp": e.timestamp if hasattr(e, 'timestamp') else "",
                "source": e.source if hasattr(e, 'source') else "system",
                "priority": e.priority if hasattr(e, 'priority') else 0,
                "payload": e.payload if hasattr(e, 'payload') else {},
            }
            for i, e in enumerate(events)
        ]}
    except Exception:
        return {"events": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)