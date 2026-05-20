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
from .srrs_adapter import get_adapter, SRRSAdapter
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)