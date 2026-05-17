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

from datetime import datetime, timezone
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
from drift_detector import get_drift_detector
from self_healing_engine import get_self_healing_engine


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

    # ─── Execution Analytics ─────────────────────────────────────────────

    @app.get("/execution/analytics")
    async def execution_analytics():
        """Get execution throughput, success rate, and latency per task type."""
        try:
            engine = get_execution_engine()
            history_stats = engine.history.get_stats()

            # Compute per-type analytics
            by_type: Dict[str, Dict[str, Any]] = {}
            for record in engine.history.list_recent(limit=500):
                task_type = record.get("task_type", "unknown")
                if task_type not in by_type:
                    by_type[task_type] = {
                        "total": 0, "completed": 0, "failed": 0,
                        "total_latency_ms": 0, "count_with_latency": 0,
                    }
                by_type[task_type]["total"] += 1
                status = record.get("status", "")
                if status == "completed":
                    by_type[task_type]["completed"] += 1
                elif status == "failed":
                    by_type[task_type]["failed"] += 1
                latency = record.get("latency_ms", 0)
                if latency > 0:
                    by_type[task_type]["total_latency_ms"] += latency
                    by_type[task_type]["count_with_latency"] += 1

            # Compute averages and success rates
            for task_type, data in by_type.items():
                total = data["total"]
                data["success_rate"] = round(data["completed"] / total, 3) if total > 0 else 0
                if data["count_with_latency"] > 0:
                    data["avg_latency_ms"] = round(data["total_latency_ms"] / data["count_with_latency"], 2)
                else:
                    data["avg_latency_ms"] = 0
                del data["total_latency_ms"]
                del data["count_with_latency"]

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": history_stats,
                "by_type": by_type,
                "engine_stats": engine.get_stats(),
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/execution/bottlenecks")
    async def execution_bottlenecks():
        """Identify execution bottlenecks: slow tasks, worker starvation, queue buildup."""
        try:
            engine = get_execution_engine()
            stats = engine.get_stats()
            history_stats = engine.history.get_stats()

            bottlenecks = []

            # Check queue buildup
            queue_size = stats.get("queue_size", 0)
            if queue_size > 20:
                bottlenecks.append({
                    "type": "queue_buildup",
                    "severity": "critical" if queue_size > 50 else "warning",
                    "message": f"Queue has {queue_size} pending tasks",
                    "recommendation": "Increase worker pool size or reduce task submission rate",
                })

            # Check worker utilization
            workers = stats.get("workers", [])
            busy_count = sum(1 for w in workers if w.get("is_busy", False))
            if workers and busy_count == len(workers) and queue_size > 5:
                bottlenecks.append({
                    "type": "worker_saturation",
                    "severity": "warning",
                    "message": f"All {len(workers)} workers are busy with {queue_size} tasks queued",
                    "recommendation": f"Consider increasing workers from {len(workers)} to {len(workers) + 2}",
                })

            # Check failure rate
            total = history_stats.get("total", 0)
            by_status = history_stats.get("by_status", {})
            failed = by_status.get("failed", 0)
            if total > 10 and failed / total > 0.3:
                bottlenecks.append({
                    "type": "high_failure_rate",
                    "severity": "critical",
                    "message": f"Failure rate is {failed/total*100:.1f}% ({failed}/{total})",
                    "recommendation": "Review task handlers and error logs for recurring issues",
                })

            # Check slow task types
            recent = engine.history.list_recent(limit=200)
            type_latencies: Dict[str, List[float]] = {}
            for record in recent:
                lt = record.get("latency_ms", 0)
                if lt > 0:
                    tt = record.get("task_type", "unknown")
                    type_latencies.setdefault(tt, []).append(lt)

            for task_type, latencies in type_latencies.items():
                avg = sum(latencies) / len(latencies)
                if avg > 5000:  # > 5 seconds
                    bottlenecks.append({
                        "type": "slow_task_type",
                        "severity": "warning",
                        "message": f"Task type '{task_type}' averages {avg:.0f}ms latency",
                        "recommendation": f"Review '{task_type}' handler for performance optimization",
                    })

            # DSPy optimizer recommendation
            from dspy_execution_optimizer import get_optimizer
            optimizer = get_optimizer()
            recommended_workers = optimizer.recommend_workers(
                current_workers=engine.max_workers,
                history_stats=history_stats,
            )
            if recommended_workers != engine.max_workers:
                bottlenecks.append({
                    "type": "suboptimal_worker_count",
                    "severity": "info",
                    "message": f"Current workers: {engine.max_workers}, recommended: {recommended_workers}",
                    "recommendation": f"POST /execution/tune to auto-tune worker pool",
                })

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bottleneck_count": len(bottlenecks),
                "bottlenecks": bottlenecks,
                "healthy": len(bottlenecks) == 0,
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/execution/tune")
    async def execution_tune():
        """Auto-tune worker pool size based on current load and history."""
        try:
            engine = get_execution_engine()
            history_stats = engine.history.get_stats()

            from dspy_execution_optimizer import get_optimizer
            optimizer = get_optimizer()
            recommended = optimizer.recommend_workers(
                current_workers=engine.max_workers,
                history_stats=history_stats,
            )

            old_workers = engine.max_workers
            engine.max_workers = recommended

            # If engine is running, restart workers
            was_running = engine._running
            if was_running:
                await engine.stop()
                await engine.start()

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_workers": old_workers,
                "recommended_workers": recommended,
                "tuned": recommended != old_workers,
                "engine_restarted": was_running,
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


# ─── Evolution API (Phase 7) ────────────────────────────────────────────────

@app.get("/evolution/status")
async def evolution_status():
    """Get current evolution state: drift + healing."""
    try:
        drift = get_drift_detector()
        healing = get_self_healing_engine()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drift": {
                "thresholds": drift._thresholds,
            },
            "healing": healing.get_stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/drift")
async def evolution_drift(
    window_hours: int = Query(24, ge=1, le=168),
):
    """Get drift analysis report."""
    try:
        drift = get_drift_detector()
        return drift.get_drift_report(window_hours=window_hours)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/recommendations")
async def evolution_recommendations(
    time_range_hours: int = Query(24, ge=1, le=168),
):
    """Get self-healing recommendations based on failure analysis."""
    try:
        healing = get_self_healing_engine()
        patterns = healing.analyze_failures(time_range_hours)
        recommendations = healing.generate_recommendations(patterns)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": patterns,
            "recommendations": [r.to_dict() for r in recommendations],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/evolution/tune")
async def evolution_tune():
    """
    Trigger auto-tuning: combines drift analysis + DSPy optimizer.
    Analyzes current state and applies optimal configuration.
    """
    try:
        drift = get_drift_detector()
        healing = get_self_healing_engine()

        # Get drift report
        report = drift.get_drift_report()

        # Auto-heal based on drift
        actions = healing.auto_heal(report)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drift_healthy": report.get("healthy", True),
            "drift_level": report.get("overall_level", "none"),
            "actions_taken": [a.to_dict() for a in actions],
            "action_count": len(actions),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/evolution/heal")
async def evolution_heal(request: dict):
    """Execute a specific healing action."""
    try:
        from self_healing_engine import HealingAction, HealingActionType
        healing = get_self_healing_engine()

        action_type_str = request.get("action_type")
        target = request.get("target", "unknown")
        reason = request.get("reason", "Manual trigger via API")
        params = request.get("params", {})

        try:
            action_type = HealingActionType(action_type_str)
        except ValueError:
            raise HTTPException(status_code=400,
                                detail=f"Unknown action type: {action_type_str}")

        action = HealingAction(
            action_type=action_type,
            target=target,
            reason=reason,
            params=params,
        )
        success = healing.apply_healing_action(action)

        return {
            "action": action.to_dict(),
            "success": success,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/evolution/history")
async def evolution_history(
    limit: int = Query(50, ge=1, le=500),
):
    """Get evolution action history (drift reports + healing actions)."""
    try:
        healing = get_self_healing_engine()
        drift = get_drift_detector()
        return {
            "healing_history": healing.get_healing_history(limit),
            "drift_history": drift.get_drift_history(limit),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
