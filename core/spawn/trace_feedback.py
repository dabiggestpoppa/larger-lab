"""
O3-B8: TraceFeedback
=====================
Feed traces back to field memory.

Captures execution traces from spawned agents and feeds them back
to the field memory system for learning and analysis.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.trace")


@dataclass
class ExecutionTrace:
    """A single execution trace from a spawned agent."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str = ""
    plan_id: str = ""
    task_type: str = ""
    model: str = ""
    status: str = ""  # complete, failed, timeout
    turns_used: int = 0
    tokens_used: int = 0
    duration_seconds: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    output_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class TraceFeedback:
    """
    Captures and feeds execution traces back to field memory.
    
    Records what happened during agent execution: tool calls,
    errors, results, timing. This data feeds into O-4 Field Learning.
    """

    def __init__(self):
        self._traces: list[ExecutionTrace] = []

    def record_trace(self, trace: ExecutionTrace) -> None:
        """Record an execution trace."""
        self._traces.append(trace)
        logger.info(
            f"Trace recorded: {trace.trace_id} ({trace.task_type}, {trace.status})"
        )

    def create_trace(
        self,
        agent_id: str,
        plan_id: str,
        task_type: str,
        model: str,
        status: str,
        **kwargs: Any,
    ) -> ExecutionTrace:
        """Create and record a new trace."""
        trace = ExecutionTrace(
            agent_id=agent_id,
            plan_id=plan_id,
            task_type=task_type,
            model=model,
            status=status,
            **kwargs,
        )
        self.record_trace(trace)
        return trace

    def get_traces(
        self,
        agent_id: str | None = None,
        task_type: str | None = None,
        status: str | None = None,
        plan_id: str | None = None,
    ) -> list[ExecutionTrace]:
        """Query traces with optional filters."""
        results = self._traces
        if agent_id:
            results = [t for t in results if t.agent_id == agent_id]
        if task_type:
            results = [t for t in results if t.task_type == task_type]
        if status:
            results = [t for t in results if t.status == status]
        if plan_id:
            results = [t for t in results if t.plan_id == plan_id]
        return results

    def get_routing_metrics(self) -> dict[str, Any]:
        """Aggregate routing metrics from all traces."""
        if not self._traces:
            return {"total_traces": 0}

        total = len(self._traces)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_model: dict[str, int] = {}
        total_tokens = 0
        total_turns = 0
        total_duration = 0.0

        for t in self._traces:
            by_type[t.task_type] = by_type.get(t.task_type, 0) + 1
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_model[t.model] = by_model.get(t.model, 0) + 1
            total_tokens += t.tokens_used
            total_turns += t.turns_used
            total_duration += t.duration_seconds

        return {
            "total_traces": total,
            "by_type": by_type,
            "by_status": by_status,
            "by_model": by_model,
            "total_tokens": total_tokens,
            "total_turns": total_turns,
            "avg_tokens": round(total_tokens / total, 1) if total else 0,
            "avg_turns": round(total_turns / total, 1) if total else 0,
            "avg_duration": round(total_duration / total, 1) if total else 0,
            "success_rate": round(
                by_status.get("complete", 0) / total * 100, 1
            ) if total else 0,
        }

    def get_failure_analysis(self) -> list[dict[str, Any]]:
        """Analyze failed traces for patterns."""
        failed = [t for t in self._traces if t.status in ("failed", "timeout")]
        analysis = []
        for t in failed:
            analysis.append({
                "trace_id": t.trace_id,
                "task_type": t.task_type,
                "model": t.model,
                "status": t.status,
                "errors": t.errors[:5],
                "turns_used": t.turns_used,
            })
        return analysis
