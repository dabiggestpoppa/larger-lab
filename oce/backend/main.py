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

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import json

# Import SRRA-OPH adapter
from srrs_adapter import get_adapter, SRRSAdapter
from event_fabric import get_fabric, EventFabric
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
    adapter = await get_adapter()
    result = await adapter.process_continuity_message(request.message, request.context)
    return {
        "response": result.get("response", "No response"),
        "session_id": request.session_id or "new_session",
        "continuity_preserved": True
    }


@app.get("/observers", response_model=List[ObserverStatus])
async def get_observer_status():
    """Live observer status panel."""
    adapter = await get_adapter()
    status = await adapter.get_observer_status()
    return [ObserverStatus(**s) for s in status]


@app.get("/events", response_model=List[EventResponse])
async def get_events(
    limit: int = Query(50, ge=1, le=1000),
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    min_priority: Optional[int] = Query(None, ge=0, le=3),
):
    """Query event history from the Event Fabric."""
    fabric = get_fabric()
    events = fabric.get_history(
        event_type=event_type,
        source=source,
        limit=limit,
        min_priority=min_priority,
    )
    return [_event_to_response(e) for e in events]


@app.get("/events/types")
async def get_event_types():
    """List all registered event types."""
    fabric = get_fabric()
    return fabric.get_event_types()


@app.get("/events/stats")
async def get_event_stats():
    """Event throughput statistics."""
    fabric = get_fabric()
    return fabric.get_stats()


@app.get("/attractor", response_model=AttractorState)
async def get_attractor_state():
    """Current operational goals and convergence state."""
    adapter = await get_adapter()
    state = await adapter.get_attractor_state()
    return AttractorState(**state)


@app.get("/memory")
async def get_memory_view():
    """Trajectory memory, structural memory, repair memory."""
    adapter = await get_adapter()
    structural = await adapter.get_structural_memory()
    trajectory = await adapter.get_trajectory_memory()
    return {
        "trajectory_memory": trajectory,
        "structural_memory": structural,
        "repair_memory": []  # TODO: Add repair memory
    }


@app.get("/health/srrs")
async def srrs_health():
    """Check SRRA-OPH substrate health."""
    adapter = await get_adapter()
    return await adapter.health_check()


# ─── Event Fabric Helpers ─────────────────────────────────────────────────────

def _event_to_response(event) -> Dict[str, Any]:
    """Convert an Event to an API response dict."""
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
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
    fabric = get_fabric()
    await fabric.ingest(
        event_type="system.startup",
        source="oce-continuity-core",
        payload={"version": "1.0.0", "message": "OCE Continuity Core started"},
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Emit shutdown event."""
    fabric = get_fabric()
    await fabric.ingest(
        event_type="system.shutdown",
        source="oce-continuity-core",
        payload={"message": "OCE Continuity Core shutting down"},
    )


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
    return pipeline_manager.get_status()


@app.post("/pipelines/contract/generate")
async def generate_contract(request: dict):
    """Generate optimized prediction contract parameters."""
    result = pipeline_manager.generate_contract(
        mutation_type=request.get("mutation_type", "unknown"),
        target=request.get("target", "unknown"),
        historical_accuracy=request.get("historical_accuracy", 0.5),
        coherence_metrics=request.get("coherence_metrics"),
    )
    return result


@app.post("/pipelines/event/route")
async def route_event(request: dict):
    """Route an event through optimal path."""
    result = pipeline_manager.route_event(
        event_type=request.get("event_type", "unknown"),
        observer_state=request.get("observer_state", {}),
        entropy_level=request.get("entropy_level", 0.0),
    )
    return result


@app.post("/pipelines/evolution/plan")
async def plan_evolution(request: dict):
    """Plan adaptive evolution."""
    result = pipeline_manager.plan_evolution(
        current_metrics=request.get("current_metrics", {}),
        budget=request.get("entropy_budget_remaining", 500.0),
        targets=request.get("coherence_targets", {}),
    )
    return result

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event stream from Event Fabric."""
    await manager.connect(websocket)
    fabric = get_fabric()
    queue = fabric.create_stream()
    try:
        async for event in fabric.stream_events(queue):
            if event is None:
                # Heartbeat
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
        pass
    except Exception:
        pass
    finally:
        fabric.close_stream(queue)
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)