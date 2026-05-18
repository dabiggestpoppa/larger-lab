"""
V3 Phase 6 — Self-Model Engine
The system observes itself continuously.

Tracks: failures, drift, inefficiencies, hallucination patterns,
routing instability, compute waste.

This is the meta-cognitive layer — the field's ability to model
its own operation and improve itself.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SelfObservation:
    """An observation about the field's own operation."""
    observation_id: str
    observation_type: str    # "failure", "drift", "inefficiency", "hallucination", "waste"
    description: str
    severity: float = 0.5    # 0-1
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolution: str = ""


class SelfModelEngine:
    """
    The field's self-model — its ability to observe and improve itself.
    
    Continuously monitors:
    - Failures (what went wrong and why)
    - Drift (gradual degradation)
    - Inefficiencies (wasted compute/effort)
    - Hallucination patterns (incorrect outputs)
    - Routing instability (poor routing decisions)
    - Compute waste (unnecessary operations)
    """

    def __init__(self):
        self.observations: list[SelfObservation] = []
        self._failure_patterns: dict[str, int] = {}
        self._drift_history: list[float] = []
        self._waste_log: list[dict] = []

    def observe_failure(self, failure_type: str, description: str, severity: float = 0.5) -> SelfObservation:
        """Record a failure observation."""
        obs = SelfObservation(
            observation_id=f"obs_{int(time.time())}",
            observation_type="failure",
            description=description,
            severity=severity,
            confidence=0.8,
        )
        self.observations.append(obs)
        self._failure_patterns[failure_type] = self._failure_patterns.get(failure_type, 0) + 1
        return obs

    def observe_drift(self, drift_score: float, context: str = "") -> SelfObservation:
        """Record a drift observation."""
        obs = SelfObservation(
            observation_id=f"obs_{int(time.time())}",
            observation_type="drift",
            description=f"Drift detected: {drift_score:.2f} — {context}",
            severity=min(1.0, drift_score),
            confidence=0.7,
        )
        self.observations.append(obs)
        self._drift_history.append(drift_score)
        return obs

    def observe_inefficiency(self, waste_type: str, cost: float, context: str = "") -> SelfObservation:
        """Record an inefficiency observation."""
        obs = SelfObservation(
            observation_id=f"obs_{int(time.time())}",
            observation_type="inefficiency",
            description=f"{waste_type}: cost={cost:.4f} — {context}",
            severity=min(1.0, cost * 10),
            confidence=0.6,
        )
        self.observations.append(obs)
        self._waste_log.append({"type": waste_type, "cost": cost, "time": time.time()})
        return obs

    def resolve_observation(self, observation_id: str, resolution: str) -> bool:
        """Mark an observation as resolved."""
        for obs in self.observations:
            if obs.observation_id == observation_id:
                obs.resolved = True
                obs.resolution = resolution
                return True
        return False

    def get_unresolved(self, observation_type: str = None) -> list[SelfObservation]:
        """Get all unresolved observations."""
        unresolved = [o for o in self.observations if not o.resolved]
        if observation_type:
            unresolved = [o for o in unresolved if o.observation_type == observation_type]
        return sorted(unresolved, key=lambda o: o.severity, reverse=True)

    def get_recurring_failures(self, min_count: int = 2) -> list[tuple[str, int]]:
        """Get failure patterns that recur."""
        return [
            (pattern, count) for pattern, count in self._failure_patterns.items()
            if count >= min_count
        ]

    def get_self_assessment(self) -> dict:
        """Generate a self-assessment of the field's health."""
        unresolved = self.get_unresolved()
        recurring = self.get_recurring_failures()
        avg_drift = sum(self._drift_history[-10:]) / max(len(self._drift_history[-10:]), 1)
        total_waste = sum(w["cost"] for w in self._waste_log[-100:])

        health = 1.0
        health -= len(unresolved) * 0.05
        health -= len(recurring) * 0.1
        health -= avg_drift * 0.2
        health -= min(0.2, total_waste)
        health = max(0.0, min(1.0, health))

        return {
            "health": round(health, 4),
            "unresolved_issues": len(unresolved),
            "recurring_failures": len(recurring),
            "avg_drift": round(avg_drift, 4),
            "recent_waste": round(total_waste, 4),
            "total_observations": len(self.observations),
        }

    @property
    def stats(self) -> dict:
        unresolved = sum(1 for o in self.observations if not o.resolved)
        return {
            "total_observations": len(self.observations),
            "unresolved": unresolved,
            "resolved": len(self.observations) - unresolved,
            "failure_patterns": len(self._failure_patterns),
        }
