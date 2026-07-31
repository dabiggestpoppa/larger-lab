"""
Phase 11.2-3B.2 — Temporal Edge Capture
========================================
Captures time-dependent topology — the actual field perturbations through time.

Not measuring software calls. Measuring field perturbations.

Every interaction captures:
    timestamp, source, target, event_type, latency,
    entropy_before, entropy_after, repair_triggered, continuity_shift

Outputs:
    temporal_edges.json
    interaction_sequences.json
    repair_chains.json
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
EXPORTS_DIR = REPO_ROOT / "experiments" / "exports" / "temporal"


@dataclass
class TemporalEdge:
    """A single runtime interaction — a field perturbation through time."""
    edge_id: str
    timestamp: str
    source: str
    target: str
    event_type: str
    latency_ms: float = 0.0
    entropy_before: float = 0.0
    entropy_after: float = 0.0
    repair_triggered: bool = False
    continuity_shift: float = 0.0  # -1.0 to 1.0 (negative = degradation)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def entropy_delta(self) -> float:
        return self.entropy_after - self.entropy_before


class TemporalGraph:
    """
    Time-dependent topology graph.
    Captures how the observer field deforms and recovers over time.
    """

    def __init__(self):
        self._edges: list[TemporalEdge] = []
        self._snapshots: list[dict] = []  # periodic topology snapshots
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def record_interaction(self, source: str, target: str, event_type: str,
                           latency_ms: float = 0.0,
                           entropy_before: float = 0.0,
                           entropy_after: float = 0.0,
                           repair_triggered: bool = False,
                           continuity_shift: float = 0.0,
                           metadata: dict | None = None) -> TemporalEdge:
        """Record a single runtime interaction."""
        edge = TemporalEdge(
            edge_id=f"te_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            target=target,
            event_type=event_type,
            latency_ms=latency_ms,
            entropy_before=entropy_before,
            entropy_after=entropy_after,
            repair_triggered=repair_triggered,
            continuity_shift=continuity_shift,
            metadata=metadata or {},
        )
        self._edges.append(edge)
        return edge

    def take_snapshot(self, observer_states: dict[str, dict]) -> dict:
        """Take a point-in-time snapshot of the topology."""
        snapshot = {
            "snapshot_id": f"snap_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_edges": len(self._edges),
            "observer_states": observer_states,
            "recent_edges": [asdict(e) for e in self._edges[-50:]],  # last 50
        }
        self._snapshots.append(snapshot)
        return snapshot

    def get_interaction_sequence(self, source: str | None = None,
                                 target: str | None = None,
                                 event_type: str | None = None,
                                 last_n: int = 100) -> list[TemporalEdge]:
        """Get filtered interaction sequence."""
        results = self._edges
        if source:
            results = [e for e in results if e.source == source]
        if target:
            results = [e for e in results if e.target == target]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        return results[-last_n:]

    def get_repair_chains(self) -> list[list[dict]]:
        """Extract repair trigger → response chains."""
        repair_starts = [e for e in self._edges if e.repair_triggered]
        chains = []
        for start in repair_starts:
            # Find all edges within 30s of repair trigger
            chain = [asdict(start)]
            for e in self._edges:
                if e.edge_id != start.edge_id and e.source == start.source:
                    chain.append(asdict(e))
            chains.append(sorted(chain, key=lambda x: x["timestamp"]))
        return chains

    def get_entropy_timeseries(self) -> list[dict]:
        """Get entropy over time for visualization."""
        return [
            {
                "timestamp": e.timestamp,
                "entropy_before": e.entropy_before,
                "entropy_after": e.entropy_after,
                "delta": e.entropy_delta,
                "source": e.source,
                "target": e.target,
            }
            for e in self._edges
        ]

    def get_continuity_timeseries(self) -> list[dict]:
        """Get continuity shift over time."""
        return [
            {
                "timestamp": e.timestamp,
                "continuity_shift": e.continuity_shift,
                "cumulative": sum(ee.continuity_shift for ee in self._edges[:i+1]),
            }
            for i, e in enumerate(self._edges)
        ]

    def get_node_activity(self) -> dict[str, dict]:
        """Aggregate activity per node."""
        activity: dict[str, dict] = {}
        for e in self._edges:
            for node in (e.source, e.target):
                if node not in activity:
                    activity[node] = {
                        "as_source": 0, "as_target": 0,
                        "total_entropy_delta": 0.0,
                        "repair_triggers": 0,
                        "avg_latency_ms": 0.0,
                    }
                if node == e.source:
                    activity[node]["as_source"] += 1
                if node == e.target:
                    activity[node]["as_target"] += 1
                activity[node]["total_entropy_delta"] += e.entropy_delta
                if e.repair_triggered:
                    activity[node]["repair_triggers"] += 1

        # Compute averages
        for node, data in activity.items():
            total = data["as_source"] + data["as_target"]
            edges_for_node = [e for e in self._edges
                              if e.source == node or e.target == node]
            if edges_for_node:
                data["avg_latency_ms"] = round(
                    sum(e.latency_ms for e in edges_for_node) / len(edges_for_node), 2
                )
            data["total_interactions"] = total

        return activity

    def export(self, path: Path | None = None) -> Path:
        """Export temporal graph data."""
        path = path or EXPORTS_DIR / "temporal_edges.json"

        data = {
            "version": "0.1.0",
            "phase": "11.2-3B.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_edges": len(self._edges),
            "total_snapshots": len(self._snapshots),
            "edges": [asdict(e) for e in self._edges],
            "snapshots": self._snapshots,
            "node_activity": self.get_node_activity(),
            "entropy_timeseries": self.get_entropy_timeseries(),
            "continuity_timeseries": self.get_continuity_timeseries(),
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return path

    def summary(self) -> dict:
        """Quick summary."""
        if not self._edges:
            return {"status": "no_data"}

        return {
            "total_edges": len(self._edges),
            "total_snapshots": len(self._snapshots),
            "unique_sources": len(set(e.source for e in self._edges)),
            "unique_targets": len(set(e.target for e in self._edges)),
            "repair_triggers": sum(1 for e in self._edges if e.repair_triggered),
            "avg_entropy_delta": round(
                sum(e.entropy_delta for e in self._edges) / len(self._edges), 4
            ),
            "avg_continuity_shift": round(
                sum(e.continuity_shift for e in self._edges) / len(self._edges), 4
            ),
        }


# ─── Global Singleton ────────────────────────────────────────────────────

_graph: TemporalGraph | None = None


def get_temporal_graph() -> TemporalGraph:
    """Get or create the global temporal graph."""
    global _graph
    if _graph is None:
        _graph = TemporalGraph()
    return _graph
