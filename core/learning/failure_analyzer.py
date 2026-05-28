"""
O-4-B5: FailureAnalyzer
========================
Studies why orchestration failed.

Analyzes traces to identify root causes of failures including
routing issues, entropy collapse, topology instability, and
repair saturation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.failure_analyzer")


@dataclass
class FailureReport:
    """Analysis report for a failed orchestration."""
    trace_id: str
    timestamp: str
    failure_type: str
    root_cause: str
    recommendations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FailureAnalyzer:
    """
    Analyzes orchestration failures to identify root causes.
    
    Examines failed traces for patterns: routing errors,
    entropy spikes, topology instability, resource exhaustion.
    """

    FAILURE_TYPES = [
        "routing_error",
        "entropy_collapse",
        "topology_instability",
        "resource_exhaustion",
        "timeout",
        "model_error",
        "boundary_violation",
    ]

    def analyze(self, trace: dict[str, Any]) -> FailureReport:
        """Analyze a failed trace and produce a failure report."""
        trace_id = trace.get("trace_id", "unknown")
        errors = trace.get("errors", [])
        task_type = trace.get("task_type", "unknown")

        failure_type = self._classify_failure(trace, errors)
        root_cause = self._identify_root_cause(trace, errors, failure_type)
        recommendations = self._generate_recommendations(failure_type, root_cause)

        return FailureReport(
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            failure_type=failure_type,
            root_cause=root_cause,
            recommendations=recommendations,
            metadata={"task_type": task_type, "error_count": len(errors)},
        )

    def _classify_failure(self, trace: dict[str, Any], errors: list[str]) -> str:
        """Classify the type of failure."""
        error_text = " ".join(errors).lower()
        if "timeout" in error_text or trace.get("status") == "timeout":
            return "timeout"
        if "routing" in error_text or "route" in error_text:
            return "routing_error"
        if "entropy" in error_text:
            return "entropy_collapse"
        if "topology" in error_text:
            return "topology_instability"
        if "resource" in error_text or "exhaust" in error_text:
            return "resource_exhaustion"
        if "boundary" in error_text or "permission" in error_text:
            return "boundary_violation"
        if "model" in error_text or "api" in error_text:
            return "model_error"
        return "unknown"

    def _identify_root_cause(self, trace: dict[str, Any], errors: list[str], failure_type: str) -> str:
        """Identify the root cause of the failure."""
        causes = {
            "timeout": "Operation exceeded time limit",
            "routing_error": "Task routed to inappropriate observer/model",
            "entropy_collapse": "System entropy exceeded stable threshold",
            "topology_instability": "Topology changes during execution",
            "resource_exhaustion": "Token or turn budget exhausted",
            "boundary_violation": "Agent attempted out-of-scope operation",
            "model_error": "Model API returned error or invalid response",
        }
        return causes.get(failure_type, "Unknown root cause")

    def _generate_recommendations(self, failure_type: str, root_cause: str) -> list[str]:
        """Generate recommendations based on failure analysis."""
        recs = {
            "timeout": ["Increase timeout for complex tasks", "Break task into smaller subtasks"],
            "routing_error": ["Review routing consensus weights", "Add task-specific routing rules"],
            "entropy_collapse": ["Reduce concurrent operations", "Enable entropy dampening"],
            "topology_instability": ["Stale topology snapshot — refresh before routing"],
            "resource_exhaustion": ["Reduce context size", "Optimize token usage"],
            "boundary_violation": ["Tighten execution boundaries", "Review tool scope"],
            "model_error": ["Enable model failover", "Add retry logic"],
        }
        return recs.get(failure_type, ["Review trace for manual analysis"])

    def get_stats(self) -> dict[str, Any]:
        return {"failure_types": self.FAILURE_TYPES}
