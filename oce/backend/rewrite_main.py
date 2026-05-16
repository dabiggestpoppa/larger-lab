"""Rewrite main.py with comprehensive error handling. Run once."""
import os

target = os.path.join(os.path.dirname(__file__), 'main.py')
f = open(target, 'r')
old_content = f.read()
f.close()

# We'll do targeted replacements rather than full rewrite

# 1. Add new imports after existing imports
old_imports = """from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import json"""

new_imports = """from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import json
import logging
import traceback

logger = logging.getLogger("oce")"""

old_content = old_content.replace(old_imports, new_imports)

# 2. Add global exception handler after CORS middleware
old_cors = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""

new_cors = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}\\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )"""

old_content = old_content.replace(old_cors, new_cors)

# 3. Fix /chat endpoint - add try/except
old_chat = """    adapter = await get_adapter()
    result = await adapter.process_continuity_message(request.message, request.context)
    return {
        "response": result.get("response", "No response"),
        "session_id": request.session_id or "new_session",
        "continuity_preserved": True
    }"""

new_chat = """    try:
        adapter = await get_adapter()
        result = await adapter.process_continuity_message(request.message, request.context)
        return {
            "response": result.get("response", "No response"),
            "session_id": request.session_id or "new_session",
            "continuity_preserved": True
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=503, detail=f"Continuity service unavailable: {str(e)}")"""

old_content = old_content.replace(old_chat, new_chat)

# 4. Fix /observers endpoint
old_observers = """    adapter = await get_adapter()
    status = await adapter.get_observer_status()
    return [ObserverStatus(**s) for s in status]"""

new_observers = """    try:
        adapter = await get_adapter()
        obs_status = await adapter.get_observer_status()
        return [ObserverStatus(**s) for s in obs_status]
    except Exception as e:
        logger.error(f"Observer status error: {e}")
        raise HTTPException(status_code=503, detail=f"Observer service unavailable: {str(e)}")"""

old_content = old_content.replace(old_observers, new_observers)

# 5. Fix /events endpoint
old_events = """    fabric = get_fabric()
    events = fabric.get_history(
        event_type=event_type,
        source=source,
        limit=limit,
        min_priority=min_priority,
    )
    return [_event_to_response(e) for e in events]"""

new_events = """    try:
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
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")"""

old_content = old_content.replace(old_events, new_events)

# 6. Fix /events/types endpoint
old_types = """    fabric = get_fabric()
    return fabric.get_event_types()"""

new_types = """    try:
        fabric = get_fabric()
        return fabric.get_event_types()
    except Exception as e:
        logger.error(f"Event types error: {e}")
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")"""

old_content = old_content.replace(old_types, new_types)

# 7. Fix /events/stats endpoint
old_stats = """    fabric = get_fabric()
    return fabric.get_stats()"""

new_stats = """    try:
        fabric = get_fabric()
        return fabric.get_stats()
    except Exception as e:
        logger.error(f"Event stats error: {e}")
        raise HTTPException(status_code=503, detail=f"Event service unavailable: {str(e)}")"""

old_content = old_content.replace(old_stats, new_stats)

# 8. Fix /attractor endpoint
old_attractor = """    adapter = await get_adapter()
    state = await adapter.get_attractor_state()
    return AttractorState(**state)"""

new_attractor = """    try:
        adapter = await get_adapter()
        state = await adapter.get_attractor_state()
        return AttractorState(**state)
    except Exception as e:
        logger.error(f"Attractor error: {e}")
        raise HTTPException(status_code=503, detail=f"Attractor service unavailable: {str(e)}")"""

old_content = old_content.replace(old_attractor, new_attractor)

# 9. Fix /memory endpoint
old_memory = """    adapter = await get_adapter()
    structural = await adapter.get_structural_memory()
    trajectory = await adapter.get_trajectory_memory()
    return {
        "trajectory_memory": trajectory,
        "structural_memory": structural,
        "repair_memory": []  # TODO: Add repair memory
    }"""

new_memory = """    try:
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
        raise HTTPException(status_code=503, detail=f"Memory service unavailable: {str(e)}")"""

old_content = old_content.replace(old_memory, new_memory)

# 10. Fix /health/srrs endpoint
old_srrs = """    adapter = await get_adapter()
    return await adapter.health_check()"""

new_srrs = """    try:
        adapter = await get_adapter()
        return await adapter.health_check()
    except Exception as e:
        logger.error(f"SRRS health error: {e}")
        return {"status": "unhealthy", "error": str(e)}"""

old_content = old_content.replace(old_srrs, new_srrs)

# 11. Fix _event_to_response to handle timestamp safely
old_evt_resp = """def _event_to_response(event) -> Dict[str, Any]:
    \"\"\"Convert an Event to an API response dict.\"\"\"
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
        "source": event.source,
        "priority": event.priority,
        "payload": event.payload,
    }"""

new_evt_resp = """def _event_to_response(event) -> Dict[str, Any]:
    \"\"\"Convert an Event to an API response dict.\"\"\"
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
    }"""

old_content = old_content.replace(old_evt_resp, new_evt_resp)

# 12. Fix startup event with error handling
old_startup = """@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize Event Fabric on startup.\"\"\"
    fabric = get_fabric()
    await fabric.ingest(
        event_type="system.startup",
        source="oce-continuity-core",
        payload={"version": "1.0.0", "message": "OCE Continuity Core started"},
    )"""

new_startup = """@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize Event Fabric on startup.\"\"\"
    try:
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.startup",
            source="oce-continuity-core",
            payload={"version": "1.0.0", "message": "OCE Continuity Core started"},
        )
        logger.info("OCE Continuity Core started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")"""

old_content = old_content.replace(old_startup, new_startup)

# 13. Fix shutdown event with error handling
old_shutdown = """@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"Emit shutdown event.\"\"\"
    fabric = get_fabric()
    await fabric.ingest(
        event_type="system.shutdown",
        source="oce-continuity-core",
        payload={"message": "OCE Continuity Core shutting down"},
    )"""

new_shutdown = """@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"Emit shutdown event.\"\"\"
    try:
        fabric = get_fabric()
        await fabric.ingest(
            event_type="system.shutdown",
            source="oce-continuity-core",
            payload={"message": "OCE Continuity Core shutting down"},
        )
        logger.info("OCE Continuity Core shutting down")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")"""

old_content = old_content.replace(old_shutdown, new_shutdown)

# 14. Fix WebSocket endpoint with proper error handling and timeout
old_ws = """@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    \"\"\"WebSocket endpoint for real-time event stream from Event Fabric.\"\"\"
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
        manager.disconnect(websocket)"""

new_ws = """@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    \"\"\"WebSocket endpoint for real-time event stream from Event Fabric.\"\"\"
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
            pass"""

old_content = old_content.replace(old_ws, new_ws)

# 15. Fix pipeline endpoints with error handling
old_pipe_status = """    return pipeline_manager.get_status()"""
new_pipe_status = """    try:
        return pipeline_manager.get_status()
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")"""
old_content = old_content.replace(old_pipe_status, new_pipe_status)

old_pipe_contract = """    result = pipeline_manager.generate_contract(
        mutation_type=request.get("mutation_type", "unknown"),
        target=request.get("target", "unknown"),
        historical_accuracy=request.get("historical_accuracy", 0.5),
        coherence_metrics=request.get("coherence_metrics"),
    )
    return result"""
new_pipe_contract = """    try:
        result = pipeline_manager.generate_contract(
            mutation_type=request.get("mutation_type", "unknown"),
            target=request.get("target", "unknown"),
            historical_accuracy=request.get("historical_accuracy", 0.5),
            coherence_metrics=request.get("coherence_metrics"),
        )
        return result
    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")"""
old_content = old_content.replace(old_pipe_contract, new_pipe_contract)

old_pipe_route = """    result = pipeline_manager.route_event(
        event_type=request.get("event_type", "unknown"),
        observer_state=request.get("observer_state", {}),
        entropy_level=request.get("entropy_level", 0.0),
    )
    return result"""
new_pipe_route = """    try:
        result = pipeline_manager.route_event(
            event_type=request.get("event_type", "unknown"),
            observer_state=request.get("observer_state", {}),
            entropy_level=request.get("entropy_level", 0.0),
        )
        return result
    except Exception as e:
        logger.error(f"Event routing error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")"""
old_content = old_content.replace(old_pipe_route, new_pipe_route)

old_pipe_evo = """    result = pipeline_manager.plan_evolution(
        current_metrics=request.get("current_metrics", {}),
        budget=request.get("entropy_budget_remaining", 500.0),
        targets=request.get("coherence_targets", {}),
    )
    return result"""
new_pipe_evo = """    try:
        result = pipeline_manager.plan_evolution(
            current_metrics=request.get("current_metrics", {}),
            budget=request.get("entropy_budget_remaining", 500.0),
            targets=request.get("coherence_targets", {}),
        )
        return result
    except Exception as e:
        logger.error(f"Evolution planning error: {e}")
        raise HTTPException(status_code=503, detail=f"Pipeline service unavailable: {str(e)}")"""
old_content = old_content.replace(old_pipe_evo, new_pipe_evo)

f = open(target, 'w')
f.write(old_content)
f.close()
print('Rewrote main.py with comprehensive error handling')
