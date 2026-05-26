"""
O-4-B3: WorkflowDistiller
=========================
Extracts stable patterns from operational traces.

Analyzes completed orchestration workflows to identify:
- Stable task sequences (patterns that repeat)
- Effective routing decisions
- Context distillation templates
- Failure-prone patterns to avoid
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("core.learning.workflow_distiller")


@dataclass
class WorkflowPattern:
    """A stable pattern extracted from workflow traces."""
    pattern_id: str
    name: str
    task_sequence: list[str]
    frequency: int
    success_rate: float
    avg_duration_ms: float
    context_template: dict[str, Any]
    first_seen: str
    last_seen: str


@dataclass
class TraceEntry:
    """Single operational trace entry."""
    trace_id: str
    timestamp: str
    task_domain: str
    complexity: str
    routing_decision: str
    outcome: str  # "success", "failure", "partial"
    duration_ms: float
    context_keys: list[str]
    error_type: str = ""


class WorkflowDistiller:
    """Extracts stable patterns from operational traces."""

    def __init__(self, storage_path: str | None = None):
        self._traces: list[TraceEntry] = []
        self._patterns: dict[str, WorkflowPattern] = {}
        self._storage_path = Path(storage_path) if storage_path else None

    def ingest_trace(self, trace: TraceEntry) -> None:
        """Ingest a new operational trace."""
        self._traces.append(trace)
        if len(self._traces) >= 3:
            self._extract_patterns()

    def ingest_from_events(self, events: list[dict]) -> int:
        """Ingest traces from raw event data. Returns count ingested."""
        count = 0
        for evt in events:
            if evt.get("event_type") in ("orchestration_complete", "orchestration_failure", "task_complete"):
                trace = TraceEntry(
                    trace_id=evt.get("trace_id", evt.get("event_id", "")),
                    timestamp=evt.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    task_domain=evt.get("task_domain", "unknown"),
                    complexity=evt.get("complexity", "low"),
                    routing_decision=evt.get("routing_decision", "default"),
                    outcome="success" if "complete" in evt.get("event_type", "") else "failure",
                    duration_ms=evt.get("duration_ms", 0),
                    context_keys=list(evt.get("context", {}).keys()),
                    error_type=evt.get("error_type", ""),
                )
                self._traces.append(trace)
                count += 1
        if count > 0:
            self._extract_patterns()
        return count

    def _extract_patterns(self) -> None:
        """Extract stable patterns from accumulated traces."""
        if len(self._traces) < 3:
            return

        # Group traces by task domain
        domain_traces: dict[str, list[TraceEntry]] = defaultdict(list)
        for t in self._traces:
            domain_traces[t.task_domain].append(t)

        for domain, traces in domain_traces.items():
            if len(traces) < 2:
                continue

            # Find common routing decisions
            routing_counts: dict[str, int] = defaultdict(int)
            routing_success: dict[str, list[bool]] = defaultdict(list)
            for t in traces:
                routing_counts[t.routing_decision] += 1
                routing_success[t.routing_decision].append(t.outcome == "success")

            for routing, count in routing_counts.items():
                if count >= 2:
                    success_rate = sum(routing_success[routing]) / len(routing_success[routing])
                    pattern_id = f"pattern_{domain}_{routing}"
                    durations = [t.duration_ms for t in traces if t.routing_decision == routing]
                    avg_duration = sum(durations) / len(durations) if durations else 0

                    self._patterns[pattern_id] = WorkflowPattern(
                        pattern_id=pattern_id,
                        name=f"{domain}:{routing}",
                        task_sequence=[domain, routing],
                        frequency=count,
                        success_rate=success_rate,
                        avg_duration_ms=avg_duration,
                        context_template=self._extract_context_template(traces),
                        first_seen=traces[0].timestamp,
                        last_seen=traces[-1].timestamp,
                    )

        logger.info(f"Extracted {len(self._patterns)} patterns from {len(self._traces)} traces")

    def _extract_context_template(self, traces: list[TraceEntry]) -> dict[str, Any]:
        """Extract common context keys from traces."""
        key_counts: dict[str, int] = defaultdict(int)
        for t in traces:
            for k in t.context_keys:
                key_counts[k] += 1
        # Keep keys that appear in >50% of traces
        threshold = len(traces) * 0.5
        return {k: True for k, v in key_counts.items() if v >= threshold}

    def get_patterns(self, min_frequency: int = 2, min_success_rate: float = 0.5) -> list[WorkflowPattern]:
        """Get stable patterns matching criteria."""
        return [
            p for p in self._patterns.values()
            if p.frequency >= min_frequency and p.success_rate >= min_success_rate
        ]

    def get_recommended_routing(self, task_domain: str) -> str | None:
        """Get the best routing decision for a task domain."""
        domain_patterns = [
            p for p in self._patterns.values()
            if p.name.startswith(f"{task_domain}:")
        ]
        if not domain_patterns:
            return None
        # Return the routing with highest success rate * frequency
        best = max(domain_patterns, key=lambda p: p.success_rate * p.frequency)
        return best.task_sequence[1] if len(best.task_sequence) > 1 else None

    def get_stats(self) -> dict[str, Any]:
        """Get distiller statistics."""
        return {
            "total_traces": len(self._traces),
            "total_patterns": len(self._patterns),
            "domains": list(set(t.task_domain for t in self._traces)),
            "avg_success_rate": (
                sum(1 for t in self._traces if t.outcome == "success") / len(self._traces)
                if self._traces else 0
            ),
        }

    def save(self) -> None:
        """Persist patterns to disk."""
        if not self._storage_path:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "patterns": {
                pid: {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "task_sequence": p.task_sequence,
                    "frequency": p.frequency,
                    "success_rate": p.success_rate,
                    "avg_duration_ms": p.avg_duration_ms,
                    "context_template": p.context_template,
                    "first_seen": p.first_seen,
                    "last_seen": p.last_seen,
                }
                for pid, p in self._patterns.items()
            },
            "trace_count": len(self._traces),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(self._patterns)} patterns to {self._storage_path}")

    def load(self) -> bool:
        """Load patterns from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return False
        try:
            data = json.loads(self._storage_path.read_text())
            for pid, pdata in data.get("patterns", {}).items():
                self._patterns[pid] = WorkflowPattern(**pdata)
            logger.info(f"Loaded {len(self._patterns)} patterns from {self._storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return False
