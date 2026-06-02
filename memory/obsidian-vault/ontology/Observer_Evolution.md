# Observer Evolution

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O-4-B7: ObserverEvolution
==========================
Allow observer specialization through operational history.

Tracks how observers improve over time based on successful/failed
orchestration patterns. Enables gradual specialization (NOT hardcoded
personalities).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.observer_evolution")


@dataclass
class EvolutionRecord:
    """Record of an observer's evolution step."""
    observer_id: str
    timestamp: str
    task_type: str
    success: bool
    confidence_before: float
    confidence_after: float
    specialization_delta: dict[str, float] = field(default_factory=dict)


class ObserverEvolution:
    """
    Manages observer evolution through operational history.
    
    Observers gradually specialize based on their success rates
    across different task domains. This is NOT hardcoded — it emerges
    from actual operational performance.
    """

    def __init__(self, persistence_path: str = ""):
        self._specializations: dict[str, dict[str, float]] = {}
        self._history: list[EvolutionRecord] = []
        self._persistence_path = persistence_path

    def record_outcome(
        self,
        observer_id: str,
        task_type: str,
        success: bool,
        confidence: float,
    ) -> None:
        """Record the outcome of an orchestration decision."""
        if observer_id not in self._specializations:
            self._specializations[observer_id] = {}

        spec = self._specializations[observer_id]
        current = spec.get(task_type, 0.5)

        # Update specialization score
        delta = 0.05 if success else -0.02
        new_score = max(0.0, min(1.0, current + delta))
        spec[task_type] = new_score

        record = EvolutionRecord(
            observer_id=observer_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_type=task_type,
            success=success,
            confidence_before=confidence,
            confidence_after=confidence + (delta * 0.5),
            specialization_delta={task_type: new_score - current},
        )
        self._history.append(record)
        logger.info(
            f"Observer {observer_id} evolution: {task_type} {current:.2f} -> {new_score:.2f}"
        )

    def get_specialization(self, observer_id: str, task_type: str) -> float:
        """Get an observer's specialization score for a task type."""
        return self._specializations.get(observer_id, {}).get(task_type, 0.5)

    def get_best_observer(self, task_type: str) -> str | None:
        """Find the best observer for a given task type."""
        best_id = None
        best_score = -1.0
        for obs_id, spec in self._specializations.items():
            score = spec.get(task_type, 0.5)
            if score > best_score:
                best_score = score
                best_id = obs_id
        return best_id

    def get_observer_profile(self, observer_id: str) -> dict[str, Any]:
        """Get a full specialization profile for an observer."""
        spec = self._specializations.get(observer_id, {})
        history = [r for r in self._history if r.observer_id == observer_id]
        total = len(history)
        successes = sum(1 for r in history if r.success)
        return {
            "observer_id": observer_id,
            "specializations": spec,
            "total_records": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "top_tasks": sorted(spec.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def get_stats(self) -> dict[str, Any]:
        return {
            "observers": len(self._specializations),
            "total_records": len(self._history),
            "avg_success_rate": (
                sum(1 for r in self._history if r.success) / len(self._history)
                if self._history
                else 0.0
            ),
        }

    def save(self) -> None:
        if self._persistence_path:
            data = {
                "specializations": self._specializations,
                "history_count": len(self._history),
            }
            with open(self._persistence_path, "w") as f:
                json.dump(data, f, indent=2)

    def load(self) -> None:
        if self._persistence_path:
            try:
                with open(self._persistence_path, "r") as f:
                    data = json.load(f)
                self._specializations = data.get("specializations", {})
            except FileNotFoundError:
                pass

```

LINKS:
[[Master Plan Observer Core]]
[[Observer Core Workspace State]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Patterns]]
[[Revolut]]
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
