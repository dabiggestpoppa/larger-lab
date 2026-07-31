# Adaptation Engine

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O-4-B11: AdaptationEngine
===========================
Apply controlled adaptation based on learning.

Uses operational scores and workflow patterns to make
controlled adjustments to observer behavior.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.learning.operational_scoring import OperationalScoring
from core.learning.observer_evolution import ObserverEvolution

logger = logging.getLogger("core.learning.adaptation_engine")


@dataclass
class AdaptationAction:
    """A single adaptation action."""
    timestamp: str
    action_type: str
    target: str
    reason: str
    applied: bool = False
    result: str = ""


class AdaptationEngine:
    """
    Applies controlled adaptation based on learning signals.
    
    Uses operational scoring and observer evolution data to make
    bounded adjustments to routing, model selection, and context
    injection parameters.
    """

    # Thresholds for adaptation triggers
    ADAPTATION_THRESHOLD = 0.3  # Score below this triggers adaptation
    IMPROVEMENT_THRESHOLD = 0.7  # Score above this is considered good
    MAX_ADJUSTMENT_RATE = 0.1   # Maximum change per adaptation cycle

    def __init__(
        self,
        scoring: OperationalScoring | None = None,
        evolution: ObserverEvolution | None = None,
    ):
        self.scoring = scoring or OperationalScoring()
        self.evolution = evolution or ObserverEvolution()
        self._actions: list[AdaptationAction] = []
        self._adjustments: dict[str, float] = {}

    def evaluate_and_adapt(self) -> list[AdaptationAction]:
        """Evaluate current state and apply adaptations if needed."""
        actions: list[AdaptationAction] = []
        breakdown = self.scoring.get_dimension_breakdown()

        for dim, data in breakdown.items():
            score = data["score"]
            if score < self.ADAPTATION_THRESHOLD:
                action = self._adapt_dimension(dim, score)
                if action:
                    actions.append(action)
            elif score > self.IMPROVEMENT_THRESHOLD:
                action = self._reinforce_dimension(dim, score)
                if action:
                    actions.append(action)

        self._actions.extend(actions)
        return actions

    def _adapt_dimension(self, dimension: str, score: float) -> AdaptationAction | None:
        """Create an adaptation action for a low-scoring dimension."""
        adjustment = min(self.MAX_ADJUSTMENT_RATE, (self.ADAPTATION_THRESHOLD - score) * 0.5)
        key = f"{dimension}_weight"
        current = self._adjustments.get(key, 1.0)
        new_value = max(0.1, current - adjustment)
        self._adjustments[key] = new_value

        action = AdaptationAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="reduce_weight",
            target=dimension,
            reason=f"Score {score:.2f} below threshold {self.ADAPTATION_THRESHOLD}",
            applied=True,
            result=f"Adjusted {key}: {current:.3f} -> {new_value:.3f}",
        )
        logger.info(f"Adaptation: {action.result}")
        return action

    def _reinforce_dimension(self, dimension: str, score: float) -> AdaptationAction | None:
        """Reinforce a high-scoring dimension."""
        adjustment = min(self.MAX_ADJUSTMENT_RATE * 0.5, (score - self.IMPROVEMENT_THRESHOLD) * 0.2)
        key = f"{dimension}_weight"
        current = self._adjustments.get(key, 1.0)
        new_value = min(2.0, current + adjustment)
        self._adjustments[key] = new_value

        action = AdaptationAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="increase_weight",
            target=dimension,
            reason=f"Score {score:.2f} above threshold {self.IMPROVEMENT_THRESHOLD}",
            applied=True,
            result=f"Reinforced {key}: {current:.3f} -> {new_value:.3f}",
        )
        return action

    def get_adjustments(self) -> dict[str, float]:
        """Get current adjustment values."""
        return dict(self._adjustments)

    def get_action_history(self, limit: int = 20) -> list[AdaptationAction]:
        """Get recent adaptation actions."""
        return self._actions[-limit:]

    def get_stats(self) -> dict[str, Any]:
        total = len(self._actions)
        applied = sum(1 for a in self._actions if a.applied)
        by_type: dict[str, int] = {}
        for a in self._actions:
            by_type[a.action_type] = by_type.get(a.action_type, 0) + 1
        return {
            "total_actions": total,
            "applied_actions": applied,
            "by_type": by_type,
            "current_adjustments": self._adjustments,
        }

```

LINKS:
[[Ontology Core Summary]]
[[Action]]
[[Citation Workflow]]
[[Patterns]]
[[Revolut]]
[[Server]]
[[Workflow]]
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
