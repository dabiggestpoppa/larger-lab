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
"""

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import json
import logging
import traceback

logger = logging.getLogger("oce")

# Import SRRA-OPH adapter
from srrs_adapter import get_adapter, SRRSAdapter
from event_fabric import get_fabric, EventFabric
from observer_runtime import get_runtime, ObserverRuntime, ObserverConfig, ObserverState
from dspy_pipelines import OCEPipelineManager

app = FastAPI(
    title="OCE Continuity Core",
    description="Operator Continuity Engine API",
    version="1.0.0"
)

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


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "OCE Continuity Core API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "oce-continuity-core"}


@app.post("/chat")
async def continuity_chat(request: ContinuityChatRequest):
    """
    Continuity chat endpoint.
    Preserves goals, trajectories, observer state, operational context.
    """
    try:
        adapter = await get_adapter()
        result = await adapter.process_continuity_message(request.message, request.context)
        return {
            "response": result.get("response", "No response"),
            "session_id": request.session_id or "new_session",
            "continuity_preserved": True
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=503, detail=f"Continuity service unavailable: {str(e)}")


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


@app.on_event("startup")
async def startup_event():
    """Initialize Event Fabric on startup."""
    try:
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.startup",
            source="oce-continuity-core",
            payload={"version": "1.0.0", "message": "OCE Continuity Core started"},
        )
        logger.info("OCE Continuity Core started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Emit shutdown event."""
    try:
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.shutdown",
            source="oce-continuity-core",
            payload={"message": "OCE Continuity Core shutting down"},
        )
        logger.info("OCE Continuity Core shutting down")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)