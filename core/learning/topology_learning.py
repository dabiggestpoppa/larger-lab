"""
O-4-B6: TopologyLearning
==========================
Understand topology effects on orchestration.

Analyzes how topology changes (node additions, edge changes,
entropy spikes) affect orchestration outcomes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.topology_learning")


@dataclass
class TopologySnapshot:
    """A snapshot of topology state at a point in time."""
    timestamp: str
    node_count: int
    edge_count: int
    entropy_level: float
    health_score: float
    active_observers: int


@dataclass
class TopologyCorrelation:
    """Correlation between topology state and orchestration outcome."""
    timestamp: str
    topology_state: dict[str, Any]
    orchestration_outcome: str
    score: float


class TopologyLearning:
    """
    Learns how topology affects orchestration quality.
    
    Tracks topology snapshots alongside orchestration outcomes
    to identify patterns like: "high entropy + low connectivity
    leads to routing failures".
    """

    def __init__(self):
        self._snapshots: list[TopologySnapshot] = []
        self._correlations: list[TopologyCorrelation] = []

    def record_snapshot(
        self,
        node_count: int,
        edge_count: int,
        entropy_level: float,
        health_score: float,
        active_observers: int,
    ) -> TopologySnapshot:
        """Record a topology snapshot."""
        snapshot = TopologySnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            node_count=node_count,
            edge_count=edge_count,
            entropy_level=entropy_level,
            health_score=health_score,
            active_observers=active_observers,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def record_correlation(
        self,
        topology_state: dict[str, Any],
        orchestration_outcome: str,
        score: float,
    ) -> None:
        """Record a correlation between topology and outcome."""
        corr = TopologyCorrelation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            topology_state=topology_state,
            orchestration_outcome=orchestration_outcome,
            score=score,
        )
        self._correlations.append(corr)

    def get_risk_factors(self) -> list[dict[str, Any]]:
        """Identify topology configurations that correlate with failures."""
        if not self._correlations:
            return []

        failures = [c for c in self._correlations if c.orchestration_outcome == "failure"]
        successes = [c for c in self._correlations if c.orchestration_outcome == "success"]

        if not failures or not successes:
            return []

        # Compare topology states between failures and successes
        risk_factors = []
        for key in ("entropy_level", "node_count", "edge_count", "health_score"):
            fail_vals = [c.topology_state.get(key, 0) for c in failures if key in c.topology_state]
            success_vals = [c.topology_state.get(key, 0) for c in successes if key in c.topology_state]
            if fail_vals and success_vals:
                avg_fail = sum(fail_vals) / len(fail_vals)
                avg_success = sum(success_vals) / len(success_vals)
                diff = avg_fail - avg_success
                if abs(diff) > 0.1:
                    risk_factors.append({
                        "factor": key,
                        "failure_avg": round(avg_fail, 3),
                        "success_avg": round(avg_success, 3),
                        "risk_direction": "high" if diff > 0 else "low",
                    })

        return sorted(risk_factors, key=lambda r: abs(r["failure_avg"] - r["success_avg"]), reverse=True)

    def get_stats(self) -> dict[str, Any]:
        return {
            "snapshots": len(self._snapshots),
            "correlations": len(self._correlations),
            "risk_factors": len(self.get_risk_factors()),
        }
