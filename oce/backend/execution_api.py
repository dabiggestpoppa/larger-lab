"""
OCE Execution API (Phase 6 — Execution Substrate)
==================================================

FastAPI endpoints for the Execution Engine.

Provides:
- Task submission, cancellation, status queries
- Task listing and filtering
- Execution history and replay
- Worker stats and engine health
- Policy management
"""

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from execution_engine import (
    ExecutionEngine,
    ExecutionTask,
    ExecutionStatus,
    ExecutionPriority,
    ExecutionPolicy,
    get_execution_engine,
)


# ─── Request/Response Models ─────────────────────────────────────────────────

class SubmitTaskRequest(BaseModel):
    task_type: str  # "skill_call", "tool_invoke", "pipeline_run", "agent_delegate"
    payload: Dict[str, Any] = {}
    priority: int = 1  # 0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL
    max_retries: int = 3
    timeout_sec: int = 30
    source: str = "api"
    tags: List[str] = []
    policy_id: str = "default"


class CreatePolicyRequest(BaseModel):
    policy_id: str
    name: str
    max_concurrent: int = 5
    rate_limit_per_minute: int = 60
    allowed_types: List[str] = ["skill_call", "tool_invoke", "pipeline_run", "agent_delegate"]
    blocked_types: List[str] = []
    max_timeout_sec: int = 300
    require_trace: bool = True
    sandboxed: bool = False
    description: str = ""


class ReplayTaskRequest(BaseModel):
    policy_id: str = "default"


# ─── Registration Function ───────────────────────────────────────────────────

def register_execution_endpoints(app: FastAPI):
    """Register all execution endpoints on the given FastAPI app."""

    @app.on_event("startup")
    async def _start_execution_engine():
        """Start the execution engine on app startup."""
        engine = get_execution_engine()
        await engine.start()

    @app.on_event("shutdown")
    async def _stop_execution_engine():
        """Stop the execution engine on app shutdown."""
        engine = get_execution_engine()
        await engine.stop()

    # ─── Task Submission ────────────────────────────────────────────────

    @app.post("/execution/submit")
    async def submit_task(request: SubmitTaskRequest):
        """Submit a task for execution."""
        try:
            engine = get_execution_engine()
            task = ExecutionTask(
                task_id=__import__("uuid").uuid4().hex,
                task_type=request.task_type,
                payload=request.payload,
                priority=ExecutionPriority(request.priority),
                max_retries=request.max_retries,
                timeout_sec=request.timeout_sec,
                source=request.source,
                tags=request.tags,
            )
            task_id = await engine.submit(task, policy_id=request.policy_id)
            return {"task_id": task_id, "status": "queued"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Execution engine error: {str(e)}")

    @app.post("/execution/{task_id}/cancel")
    async def cancel_task(task_id: str):
        """Cancel a pending or running task."""
        try:
            engine = get_execution_engine()
            success = await engine.cancel(task_id)
            if not success:
                raise HTTPException(status_code=400, detail="Task not found or already completed")
            return {"task_id": task_id, "status": "cancelled"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Task Queries ────────────────────────────────────────────────────

    @app.get("/execution/tasks")
    async def list_tasks(
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = Query(50, ge=1, le=500),
    ):
        """List tasks with optional filters."""
        try:
            engine = get_execution_engine()
            status_enum = ExecutionStatus(status) if status else None
            tasks = engine.list_tasks(status=status_enum, task_type=task_type, limit=limit)
            return [t.to_dict() for t in tasks]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/execution/tasks/{task_id}")
    async def get_task(task_id: str):
        """Get task details by ID."""
        try:
            engine = get_execution_engine()
            task = engine.get_task(task_id)
            if not task:
                # Try history
                record = engine.history.get(task_id)
                if record:
                    return record
                raise HTTPException(status_code=404, detail="Task not found")
            return task.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Execution History ───────────────────────────────────────────────

    @app.get("/execution/history")
    async def get_execution_history(
        limit: int = Query(50, ge=1, le=500),
        status: Optional[str] = None,
    ):
        """Get execution history."""
        try:
            engine = get_execution_engine()
            return engine.history.list_recent(limit=limit, status=status)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/execution/{task_id}/replay")
    async def replay_task(task_id: str, request: ReplayTaskRequest):
        """Replay a previously executed task."""
        try:
            engine = get_execution_engine()
            new_task_id = await engine.replay(task_id, policy_id=request.policy_id)
            return {"original_task_id": task_id, "new_task_id": new_task_id, "status": "queued"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Engine Stats ────────────────────────────────────────────────────

    @app.get("/execution/stats")
    async def get_execution_stats():
        """Get execution engine statistics."""
        try:
            engine = get_execution_engine()
            return engine.get_stats()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/execution/workers")
    async def get_worker_status():
        """Get worker pool status."""
        try:
            engine = get_execution_engine()
            return {
                "workers": [
                    {
                        "worker_id": w.worker_id,
                        "tasks_processed": w.tasks_processed,
                        "tasks_failed": w.tasks_failed,
                        "is_busy": w.is_busy,
                        "current_task_id": w.current_task_id,
                    }
                    for w in engine._workers
                ],
                "active_count": engine._active_count,
                "queue_size": engine._queue.qsize() if engine._queue else 0,
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Policy Management ───────────────────────────────────────────────

    @app.post("/execution/policies")
    async def create_policy(request: CreatePolicyRequest):
        """Create or update an execution policy."""
        try:
            engine = get_execution_engine()
            policy = ExecutionPolicy(
                policy_id=request.policy_id,
                name=request.name,
                max_concurrent=request.max_concurrent,
                rate_limit_per_minute=request.rate_limit_per_minute,
                allowed_types=request.allowed_types,
                blocked_types=request.blocked_types,
                max_timeout_sec=request.max_timeout_sec,
                require_trace=request.require_trace,
                sandboxed=request.sandboxed,
                description=request.description,
            )
            engine.register_policy(policy)
            return {"policy_id": policy.policy_id, "name": policy.name, "status": "registered"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/execution/policies")
    async def list_policies():
        """List all registered execution policies."""
        try:
            engine = get_execution_engine()
            return [
                {
                    "policy_id": p.policy_id,
                    "name": p.name,
                    "max_concurrent": p.max_concurrent,
                    "rate_limit_per_minute": p.rate_limit_per_minute,
                    "allowed_types": p.allowed_types,
                    "blocked_types": p.blocked_types,
                    "sandboxed": p.sandboxed,
                }
                for p in engine._policies.values()
            ]
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))
