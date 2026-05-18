"""
V3 Phase 8 — Coherence Reinforcement
Reinforces behaviors that improve long-term coherence.

When the operator or system makes decisions that improve field stability,
those patterns are reinforced. This is the core of coevolution — mutual
stabilization through recursive coherence reinforcement.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CoherenceEvent:
    """An event that affected field coherence."""
    event_id: str
    event_type: str          # "operator_action", "system_action", "environmental"
    description: str
    coherence_before: float = 0.5
    coherence_after: float = 0.5
    timestamp: float = field(default_factory=time.time)
    reinforced: bool = False

    @property
    def improvement(self) -> float:
        return self.coherence_after - self.coherence_before

    @property
    def was_beneficial(self) -> bool:
        return self.improvement > 0.05


class CoherenceReinforcement:
    """
    Reinforces behaviors that improve long-term coherence.
    
    When the operator makes decisions that improve field stability,
    those patterns are reinforced. When the system makes decisions
    that improve coherence, those are reinforced too.
    
    This creates a positive feedback loop: better decisions →
    more reinforcement → more likely to repeat → even better coherence.
    """

    def __init__(self):
        self._events: list[CoherenceEvent] = []
        self._reinforced_patterns: dict[str, int] = {}  # pattern -> reinforcement count

    def record_event(
        self, event_type: str, description: str,
        coherence_before: float, coherence_after: float,
    ) -> CoherenceEvent:
        """Record a coherence-affecting event."""
        event = CoherenceEvent(
            event_id=f"coh_{int(time.time())}",
            event_type=event_type,
            description=description,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
        )
        self._events.append(event)

        # If beneficial, reinforce the pattern
        if event.was_beneficial:
            self._reinforce(event)

        return event

    def _reinforce(self, event: CoherenceEvent) -> None:
        """Reinforce a beneficial pattern."""
        key = f"{event.event_type}:{event.description[:30]}"
        self._reinforced_patterns[key] = self._reinforced_patterns.get(key, 0) + 1
        event.reinforced = True

    def get_reinforced_patterns(self) -> list[tuple[str, int]]:
        """Get all reinforced patterns, sorted by reinforcement count."""
        return sorted(
            self._reinforced_patterns.items(),
            key=lambda x: x[1],
            reverse=True,
        )

    def get_coherence_trend(self, window: int = 20) -> float:
        """Get the coherence trend over recent events."""
        if len(self._events) < 2:
            return 0.0
        recent = self._events[-window:]
        if len(recent) < 2:
            return 0.0
        improvements = [e.improvement for e in recent]
        return sum(improvements) / len(improvements)

    def should_encourage(self, action_type: str) -> bool:
        """Should the system encourage a particular action type?"""
        key = f"{action_type}:"
        matching = {k: v for k, v in self._reinforced_patterns.items() if k.startswith(key)}
        return sum(matching.values()) > 2

    @property
    def stats(self) -> dict:
        beneficial = sum(1 for e in self._events if e.was_beneficial)
        return {
            "total_events": len(self._events),
            "beneficial_events": beneficial,
            "reinforced_patterns": len(self._reinforced_patterns),
            "coherence_trend": round(self.get_coherence_trend(), 4),
        }
