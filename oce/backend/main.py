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
import asyncio
import json

# Import SRRA-OPH adapter
from srrs_adapter import get_adapter, SRRSAdapter
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


class Event(BaseModel):
    event_type: str
    timestamp: str
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


@app.get("/events", response_model=List[Event])
async def get_events(limit: int = Query(50, ge=1, le=1000)):
    """Live event feed from event fabric."""
    adapter = await get_adapter()
    # TODO: Integrate with Redis Streams/NATS for real events
    # For now, return empty list - events will come via WebSocket
    return []


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
    """WebSocket endpoint for real-time event stream."""
    await manager.connect(websocket)
    adapter = await get_adapter()
    try:
        while True:
            # Send entropy metrics from SRRA-OPH substrate
            metrics = await adapter.get_entropy_metrics()
            await websocket.send_text(json.dumps({
                "type": "entropy_metrics",
                "timestamp": "2026-05-16T16:00:00Z",
                "payload": metrics
            }))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)