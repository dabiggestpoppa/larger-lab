"""
V3 Phase 1 — Field State Management
Manages the propagation of field-state through the cognitive substrate.

The field is not a collection of events — it is a continuous resonant medium.
FieldState tracks the current resonant configuration and how it evolves.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from .signal_packet import SignalPacket, SignalField
from .coherence_metrics import CoherenceEngine, CoherenceSnapshot


@dataclass
class FieldState:
    """
    Represents the current state of the cognitive field.
    
    The field has a resonant configuration — a pattern of signal amplitudes,
    phases, and coherences that determines how observers interact.
    """
    field_id: str = "main"
    timestamp: float = field(default_factory=time.time)
    resonance_level: float = 0.5       # Overall field resonance (0-1)
    stability_index: float = 0.5       # How stable the field is (0-1)
    entropy_budget: float = 1.0        # Remaining entropy budget (0-1)
    active_boundaries: list[str] = field(default_factory=list)
    observer_count: int = 0
    signal_count: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def is_stable(self) -> bool:
        return self.stability_index > 0.5 and self.entropy_budget > 0.2

    @property
    def is_saturated(self) -> bool:
        """Field is saturated when entropy budget is depleted."""
        return self.entropy_budget < 0.1

    @property
    def health(self) -> float:
        """Overall field health = resonance × stability × entropy_budget."""
        return self.resonance_level * self.stability_index * self.entropy_budget

    def to_dict(self) -> dict:
        return {
            "field_id": self.field_id,
            "timestamp": self.timestamp,
            "resonance_level": round(self.resonance_level, 4),
            "stability_index": round(self.stability_index, 4),
            "entropy_budget": round(self.entropy_budget, 4),
            "active_boundaries": self.active_boundaries,
            "observer_count": self.observer_count,
            "signal_count": self.signal_count,
            "is_stable": self.is_stable,
            "is_saturated": self.is_saturated,
            "health": round(self.health, 4),
        }


class FieldStateManager:
    """
    Manages field state evolution over time.
    
    The field state evolves through:
    1. Signal injection → changes resonance
    2. Observer entrainment → changes stability
    3. Entropy accumulation → depletes budget
    4. Decay → natural dissipation
    5. Repair → restores stability
    """

    def __init__(self, entropy_budget_max: float = 1.0, decay_rate: float = 0.01):
        self.signal_field = SignalField()
        self.coherence_engine = CoherenceEngine()
        self.current_state = FieldState(entropy_budget=entropy_budget_max)
        self.entropy_budget_max = entropy_budget_max
        self.decay_rate = decay_rate
        self._state_history: list[FieldState] = []
        self._max_history = 1000

    def inject_signal(self, signal: SignalPacket) -> None:
        """
        Inject a signal into the field and update field state.
        
        Signal injection:
        - Adds signal to the field
        - Consumes entropy budget proportional to signal's entropy_delta
        - May change resonance level based on signal coherence
        """
        self.signal_field.inject(signal)
        
        # Entropy budget consumption
        self.current_state.entropy_budget -= signal.entropy_delta * 0.1
        self.current_state.entropy_budget = max(0.0, self.current_state.entropy_budget)
        
        # Resonance adjustment: coherent signals increase resonance
        if signal.is_resonant:
            self.current_state.resonance_level = min(1.0, self.current_state.resonance_level + 0.05)
        elif signal.is_entropic:
            self.current_state.resonance_level = max(0.0, self.current_state.resonance_level - 0.05)
        
        # Update boundary tracking
        for tag in signal.boundary_tags:
            if tag not in self.current_state.active_boundaries:
                self.current_state.active_boundaries.append(tag)
        
        self.current_state.signal_count = len(self.signal_field)
        self.current_state.timestamp = time.time()

    def entrain_observer(self, observer_id: str, phase: float, coherence: float) -> None:
        """
        Register an observer being entrained by the field.
        Observer entrainment increases field stability.
        """
        self.coherence_engine.update_observer(observer_id, phase, coherence)
        self.current_state.observer_count = self.coherence_engine.observer_count
        # More observers = more stability (up to a point)
        stability_boost = 0.02 * min(self.current_state.observer_count, 10)
        self.current_state.stability_index = min(1.0, self.current_state.stability_index + stability_boost)

    def remove_observer(self, observer_id: str) -> None:
        """Remove an observer from the field."""
        self.coherence_engine.remove_observer(observer_id)
        self.current_state.observer_count = self.coherence_engine.observer_count
        # Observer loss decreases stability
        self.current_state.stability_index = max(0.0, self.current_state.stability_index - 0.05)

    def measure_coherence(self) -> CoherenceSnapshot:
        """Take a coherence measurement of the current field state."""
        snapshot = self.coherence_engine.measure(self.signal_field)
        # Update field state from measurement
        self.current_state.resonance_level = (
            self.current_state.resonance_level * 0.8 + snapshot.resonance_density * 0.2
        )
        self.current_state.stability_index = (
            self.current_state.stability_index * 0.8 + snapshot.attractor_stability * 0.2
        )
        return snapshot

    def decay_step(self) -> None:
        """
        Advance field state by one decay step.
        Signals dissipate, entropy budget slowly recovers.
        """
        self.signal_field.decay(factor=(1.0 - self.decay_rate))
        # Entropy budget slowly recovers
        self.current_state.entropy_budget = min(
            self.entropy_budget_max,
            self.current_state.entropy_budget + self.decay_rate * 0.1
        )
        self.current_state.signal_count = len(self.signal_field)
        self.current_state.timestamp = time.time()

    def repair(self, amount: float = 0.2) -> None:
        """
        Repair the field — restore stability and entropy budget.
        Called by repair observer when instability exceeds threshold.
        """
        self.current_state.stability_index = min(1.0, self.current_state.stability_index + amount)
        self.current_state.entropy_budget = min(
            self.entropy_budget_max,
            self.current_state.entropy_budget + amount * 0.5
        )
        # Clear entropic signals
        entropic = self.signal_field.get_entropic_signals()
        for s in entropic:
            if s in self.signal_field.signals:
                self.signal_field.signals.remove(s)
        self.current_state.signal_count = len(self.signal_field)

    def snapshot(self) -> FieldState:
        """Save current state to history and return it."""
        self._state_history.append(self.current_state)
        if len(self._state_history) > self._max_history:
            self._state_history = self._state_history[-self._max_history:]
        return self.current_state

    def get_pressure_map(self) -> dict[str, float]:
        """Get pressure per boundary tag."""
        return self.signal_field.get_pressure_map()

    def get_drift_alerts(self) -> list[dict]:
        """Get coherence drift alerts."""
        return self.coherence_engine.get_drift_alerts()

    def get_signal_count(self) -> int:
        """Get the current number of signals in the field."""
        return len(self.signal_field)

    @property
    def stats(self) -> dict:
        """Complete field statistics."""
        return {
            "state": self.current_state.to_dict(),
            "signals": self.signal_field.stats,
            "coherence": self.coherence_engine.latest.to_dict() if self.coherence_engine.latest else None,
            "pressure": self.get_pressure_map(),
        }

    def __repr__(self) -> str:
        return (
            f"FieldStateManager(state={self.current_state.health:.2f}, "
            f"signals={len(self.signal_field)}, observers={self.current_state.observer_count})"
        )
