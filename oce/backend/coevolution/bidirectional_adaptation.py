"""
V3 Phase 8 — Bidirectional Adaptation
System and operator adapt to each other.

The field learns operator trajectories, the operator learns field resonance.
This is the coevolution core — mutual adaptation through recursive
coherence reinforcement.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdaptationEvent:
    """A bidirectional adaptation event."""
    event_id: str
    direction: str           # "system_to_operator", "operator_to_system", "mutual"
    description: str
    field_adjustment: float = 0.0   # How much the field adapted
    operator_adjustment: float = 0.0  # How much the operator adapted
    coherence_impact: float = 0.0
    timestamp: float = field(default_factory=time.time)


class BidirectionalAdaptation:
    """
    Manages mutual adaptation between the field and the operator.
    
    The field learns:
    - Operator priorities and patterns
    - Optimal timing for interactions
    - Preferred communication styles
    - Effective reinforcement strategies
    
    The operator learns:
    - Field capabilities and limitations
    - How to get better results from the system
    - Field preferences and optimal interaction patterns
    
    This is NOT one-way adaptation. Both sides evolve together.
    """

    def __init__(self):
        self._adaptation_log: list[AdaptationEvent] = []
        self._field_learnings: list[dict] = []
        self._operator_learnings: list[dict] = []

    def record_system_adaptation(
        self, description: str, adjustment: float,
        coherence_impact: float = 0.0,
    ) -> AdaptationEvent:
        """Record the system adapting to the operator."""
        event = AdaptationEvent(
            event_id=f"adapt_{int(time.time())}",
            direction="system_to_operator",
            description=description,
            field_adjustment=adjustment,
            coherence_impact=coherence_impact,
        )
        self._adaptation_log.append(event)
        self._field_learnings.append({
            "description": description,
            "adjustment": adjustment,
            "timestamp": time.time(),
        })
        return event

    def record_operator_adaptation(
        self, description: str, adjustment: float,
        coherence_impact: float = 0.0,
    ) -> AdaptationEvent:
        """Record the operator adapting to the system."""
        event = AdaptationEvent(
            event_id=f"adapt_{int(time.time())}",
            direction="operator_to_system",
            description=description,
            operator_adjustment=adjustment,
            coherence_impact=coherence_impact,
        )
        self._adaptation_log.append(event)
        self._operator_learnings.append({
            "description": description,
            "adjustment": adjustment,
            "timestamp": time.time(),
        })
        return event

    def record_mutual_adaptation(
        self, description: str,
        field_adjustment: float, operator_adjustment: float,
        coherence_impact: float = 0.0,
    ) -> AdaptationEvent:
        """Record mutual adaptation."""
        event = AdaptationEvent(
            event_id=f"adapt_{int(time.time())}",
            direction="mutual",
            description=description,
            field_adjustment=field_adjustment,
            operator_adjustment=operator_adjustment,
            coherence_impact=coherence_impact,
        )
        self._adaptation_log.append(event)
        return event

    def get_adaptation_balance(self) -> dict:
        """Get the balance of adaptations."""
        system_adapt = sum(1 for e in self._adaptation_log if e.direction == "system_to_operator")
        operator_adapt = sum(1 for e in self._adaptation_log if e.direction == "operator_to_system")
        mutual = sum(1 for e in self._adaptation_log if e.direction == "mutual")

        return {
            "system_to_operator": system_adapt,
            "operator_to_system": operator_adapt,
            "mutual": mutual,
            "total": len(self._adaptation_log),
            "is_balanced": abs(system_adapt - operator_adapt) <= 2,
        }

    @property
    def stats(self) -> dict:
        balance = self.get_adaptation_balance()
        avg_impact = (
            sum(e.coherence_impact for e in self._adaptation_log) / len(self._adaptation_log)
            if self._adaptation_log else 0.0
        )
        return {
            **balance,
            "avg_coherence_impact": round(avg_impact, 4),
            "field_learnings": len(self._field_learnings),
            "operator_learnings": len(self._operator_learnings),
        }
