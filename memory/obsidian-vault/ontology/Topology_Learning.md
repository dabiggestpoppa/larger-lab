# Topology Learning

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
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

```

LINKS:
[[03 Srra Topology]]
[[Cg 3 Relational Topology]]
[[Agent Topology]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Configuration]]
[[Effects]]
[[Failures]]
[[Patterns]]
[[Server]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
