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
