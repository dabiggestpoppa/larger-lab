"""
OCE DSPy Execution Optimizer — Phase 6.2
=========================================
Learns optimal execution parameters from execution history.

Pipelines:
- ExecutionOptimizerPipeline: Worker pool sizing from throughput history
- TaskSchedulingPipeline: Priority assignment from task type + system load
- RetryPolicyPipeline: Retry strategy per task type from failure patterns

All pipelines use heuristic fallbacks when DSPy is not installed.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.dspy.execution")

# ─── DSPy availability check ─────────────────────────────────────────────────

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    logger.info("DSPy not installed — using heuristic fallbacks for execution optimization")


# ─── Heuristic Fallbacks ─────────────────────────────────────────────────────

def _heuristic_worker_count(history_stats: Dict[str, Any]) -> int:
    """Determine optimal worker pool size from execution history."""
    total = history_stats.get("total", 0)
    by_status = history_stats.get("by_status", {})
    completed = by_status.get("completed", 0)
    failed = by_status.get("failed", 0)
    avg_latency = history_stats.get("avg_latency_ms", 100)

    if total == 0:
        return 2  # Default

    success_rate = completed / total if total > 0 else 1.0
    failure_rate = failed / total if total > 0 else 0.0

    # High throughput + low latency → more workers
    # High failure rate → fewer workers (reduce contention)
    if avg_latency < 50 and success_rate > 0.9:
        return min(8, max(4, int(total / 10)))
    elif failure_rate > 0.3:
        return max(2, int(total / 20))
    else:
        return min(6, max(2, int(total / 15)))


def _heuristic_priority(task_type: str, system_load: float) -> int:
    """Determine task priority from type and system load."""
    # Critical task types
    critical_types = {"agent_delegate", "repair", "entropy_rebalance"}
    high_types = {"skill_call", "pipeline_run"}
    low_types = {"log", "metrics_collect", "cleanup"}

    if task_type in critical_types:
        return 3  # CRITICAL
    elif task_type in high_types:
        return 2  # HIGH
    elif task_type in low_types:
        return 0  # LOW
    else:
        # Under high system load, deprioritize non-essential tasks
        if system_load > 0.8:
            return 0  # LOW
        elif system_load > 0.5:
            return 1  # NORMAL
        else:
            return 2  # HIGH


def _heuristic_retry_policy(task_type: str, failure_history: List[Dict]) -> Dict[str, Any]:
    """Determine retry strategy from task type and failure history."""
    # Count failures for this task type
    type_failures = [f for f in failure_history if f.get("task_type") == task_type]
    failure_count = len(type_failures)

    if failure_count == 0:
        return {"max_retries": 1, "backoff_sec": 1.0, "retry_on": ["timeout", "transient"]}
    elif failure_count < 3:
        return {"max_retries": 2, "backoff_sec": 2.0, "retry_on": ["timeout", "transient", "handler_error"]}
    else:
        # High failure rate — more retries with exponential backoff
        return {"max_retries": 3, "backoff_sec": 5.0, "retry_on": ["timeout", "transient", "handler_error", "resource_exhausted"]}


# ─── DSPy Signatures (when available) ────────────────────────────────────────

if DSPY_AVAILABLE:
    class WorkerOptimizationSignature(dspy.Signature):
        """Determine optimal worker pool size from execution metrics."""
        total_tasks = dspy.InputField(desc="Total tasks executed")
        completed_tasks = dspy.InputField(desc="Successfully completed tasks")
        failed_tasks = dspy.InputField(desc="Failed tasks")
        avg_latency_ms = dspy.InputField(desc="Average task latency in milliseconds")
        current_workers = dspy.InputField(desc="Current worker pool size")
        optimal_workers = dspy.OutputField(desc="Recommended number of workers (2-16)")

    class TaskSchedulingSignature(dspy.Signature):
        """Determine optimal task priority from context."""
        task_type = dspy.InputField(desc="Type of task being submitted")
        system_load = dspy.InputField(desc="Current system load (0.0-1.0)")
        queue_depth = dspy.InputField(desc="Current number of queued tasks")
        recent_failure_rate = dspy.InputField(desc="Recent failure rate (0.0-1.0)")
        recommended_priority = dspy.OutputField(desc="Recommended priority: LOW, NORMAL, HIGH, CRITICAL")

    class RetryPolicySignature(dspy.Signature):
        """Determine optimal retry strategy from failure patterns."""
        task_type = dspy.InputField(desc="Type of task")
        failure_count = dspy.InputField(desc="Number of recent failures for this type")
        common_errors = dspy.InputField(desc="Most common error messages")
        avg_attempts_before_success = dspy.InputField(desc="Average attempts needed for success")
        max_retries = dspy.OutputField(desc="Recommended max retries (1-5)")
        backoff_sec = dspy.OutputField(desc="Recommended backoff in seconds")
        retry_on = dspy.OutputField(desc="Error types to retry on (comma-separated)")


# ─── Pipeline Classes ────────────────────────────────────────────────────────

class ExecutionOptimizerPipeline:
    """Optimizes worker pool sizing based on execution history."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        if DSPY_AVAILABLE:
            self._optimizer = dspy.ChainOfThought(WorkerOptimizationSignature)
        else:
            self._optimizer = None

    def record_execution(self, task_type: str, status: str, latency_ms: float):
        """Record an execution result for learning."""
        self._history.append({
            "task_type": task_type,
            "status": status,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep last 1000 entries
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

    def recommend_workers(self, current_workers: int, history_stats: Dict[str, Any]) -> int:
        """Recommend optimal worker pool size."""
        if self._optimizer is None:
            return _heuristic_worker_count(history_stats)

        try:
            result = self._optimizer(
                total_tasks=history_stats.get("total", 0),
                completed_tasks=history_stats.get("by_status", {}).get("completed", 0),
                failed_tasks=history_stats.get("by_status", {}).get("failed", 0),
                avg_latency_ms=history_stats.get("avg_latency_ms", 100),
                current_workers=current_workers,
            )
            recommended = int(result.optimal_workers)
            return max(2, min(16, recommended))
        except Exception as e:
            logger.warning(f"DSPy optimizer failed, using heuristic: {e}")
            return _heuristic_worker_count(history_stats)


class TaskSchedulingPipeline:
    """Optimizes task priority assignment based on context."""

    def __init__(self):
        if DSPY_AVAILABLE:
            self._scheduler = dspy.ChainOfThought(TaskSchedulingSignature)
        else:
            self._scheduler = None

    def recommend_priority(self, task_type: str, system_load: float, queue_depth: int, failure_rate: float) -> int:
        """Recommend priority for a task (0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL)."""
        if self._scheduler is None:
            return _heuristic_priority(task_type, system_load)

        try:
            result = self._scheduler(
                task_type=task_type,
                system_load=str(system_load),
                queue_depth=str(queue_depth),
                recent_failure_rate=str(failure_rate),
            )
            priority_map = {"LOW": 0, "NORMAL": 1, "HIGH": 2, "CRITICAL": 3}
            return priority_map.get(result.recommended_priority.upper(), 1)
        except Exception as e:
            logger.warning(f"DSPy scheduler failed, using heuristic: {e}")
            return _heuristic_priority(task_type, system_load)


class RetryPolicyPipeline:
    """Learns optimal retry strategies per task type."""

    def __init__(self):
        if DSPY_AVAILABLE:
            self._retry_advisor = dspy.ChainOfThought(RetryPolicySignature)
        else:
            self._retry_advisor = None

    def recommend_retry_policy(self, task_type: str, failure_history: List[Dict]) -> Dict[str, Any]:
        """Recommend retry policy for a task type."""
        if self._retry_advisor is None:
            return _heuristic_retry_policy(task_type, failure_history)

        try:
            type_failures = [f for f in failure_history if f.get("task_type") == task_type]
            common_errors = ", ".join(set(f.get("error", "unknown") for f in type_failures[:5]))
            avg_attempts = sum(f.get("attempts", 1) for f in type_failures) / max(len(type_failures), 1)

            result = self._retry_advisor(
                task_type=task_type,
                failure_count=str(len(type_failures)),
                common_errors=common_errors or "none",
                avg_attempts_before_success=f"{avg_attempts:.1f}",
            )
            return {
                "max_retries": max(1, min(5, int(result.max_retries))),
                "backoff_sec": max(0.5, float(result.backoff_sec)),
                "retry_on": [s.strip() for s in result.retry_on.split(",") if s.strip()],
            }
        except Exception as e:
            logger.warning(f"DSPy retry advisor failed, using heuristic: {e}")
            return _heuristic_retry_policy(task_type, failure_history)


# ─── Singleton Instance ──────────────────────────────────────────────────────

_optimizer = ExecutionOptimizerPipeline()
_scheduler = TaskSchedulingPipeline()
_retry_advisor = RetryPolicyPipeline()


def get_optimizer() -> ExecutionOptimizerPipeline:
    return _optimizer


def get_scheduler() -> TaskSchedulingPipeline:
    return _scheduler


def get_retry_advisor() -> RetryPolicyPipeline:
    return _retry_advisor
