# Operational Scoring

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O-4-B10: OperationalScoring
=============================
Quantify orchestration quality.

Scores orchestration decisions and outcomes to enable
data-driven improvement of the observer field.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.operational_scoring")


@dataclass
class ScoreEntry:
    """A single operational score."""
    timestamp: str
    dimension: str
    score: float  # 0.0 - 1.0
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class OperationalScoring:
    """
    Quantifies orchestration quality across multiple dimensions.
    
    Tracks scores for: routing accuracy, context quality,
    execution efficiency, and outcome success.
    """

    DIMENSIONS = [
        "routing_accuracy",
        "context_quality",
        "execution_efficiency",
        "outcome_success",
        "resource_efficiency",
        "continuity_preservation",
    ]

    def __init__(self):
        self._scores: list[ScoreEntry] = []

    def score(
        self,
        dimension: str,
        score: float,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a score for a dimension."""
        if dimension not in self.DIMENSIONS:
            logger.warning(f"Unknown scoring dimension: {dimension}")
        entry = ScoreEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            dimension=dimension,
            score=max(0.0, min(1.0, score)),
            weight=weight,
            metadata=metadata or {},
        )
        self._scores.append(entry)

    def get_dimension_score(self, dimension: str) -> float:
        """Get the weighted average score for a dimension."""
        entries = [s for s in self._scores if s.dimension == dimension]
        if not entries:
            return 0.5  # Default neutral score
        total_weight = sum(s.weight for s in entries)
        if total_weight == 0:
            return 0.5
        return sum(s.score * s.weight for s in entries) / total_weight

    def get_overall_score(self) -> float:
        """Get the overall weighted score across all dimensions."""
        if not self._scores:
            return 0.5
        total_weight = sum(s.weight for s in self._scores)
        if total_weight == 0:
            return 0.5
        return sum(s.score * s.weight for s in self._scores) / total_weight

    def get_dimension_breakdown(self) -> dict[str, Any]:
        """Get a breakdown of scores by dimension."""
        return {
            dim: {
                "score": round(self.get_dimension_score(dim), 3),
                "entries": len([s for s in self._scores if s.dimension == dim]),
            }
            for dim in self.DIMENSIONS
        }

    def get_trend(self, dimension: str, window: int = 10) -> list[float]:
        """Get recent score trend for a dimension."""
        entries = [s for s in self._scores if s.dimension == dimension][-window:]
        return [s.score for s in entries]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_scores": len(self._scores),
            "overall_score": round(self.get_overall_score(), 3),
            "dimensions": self.get_dimension_breakdown(),
        }

```

LINKS:
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Citation Workflow]]
[[Neutral]]
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
[[Topology Learning]]
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
