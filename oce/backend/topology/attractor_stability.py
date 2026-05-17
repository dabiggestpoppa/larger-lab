"""
V3 Phase 3 — Strange Attractor Stability Layer
The anti-collapse layer. The heart of the theory.

The system should NOT search endlessly. It should settle into stable attractors.
Stable workflows become stronger. Stable observer clusters persist.
Unstable structures dissolve. Coherent patterns self-reinforce.

When instability exceeds threshold:
1. Reduce signal amplitude
2. Compress observer state
3. Freeze non-essential routing
4. Trigger repair observer
5. Rebuild local coherence
6. Reintegrate into field
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from resonance import FieldStateManager, ResonanceEngine
from reconstruction import ContinuityRepairLoop


@dataclass
class StabilityState:
    """Current stability state of the cognitive field."""
    timestamp: float
    is_stable: bool
    instability_level: float     # 0-1, higher = more unstable
    active_attractors: int
    frozen_routes: int
    repair_active: bool
    compression_level: float     # 0-1, how much state is compressed

    def to_dict(self) -> dict:
        return {
            "is_stable": self.is_stable,
            "instability_level": round(self.instability_level, 4),
            "active_attractors": self.active_attractors,
            "frozen_routes": self.frozen_routes,
            "repair_active": self.repair_active,
            "compression_level": round(self.compression_level, 4),
        }


class AttractorStabilityLayer:
    """
    Maintains field stability through attractor convergence.
    
    When the field is stable: reinforce successful patterns
    When the field is unstable: apply stability rules
    """

    def __init__(self, instability_threshold: float = 0.7):
        self.instability_threshold = instability_threshold
        self._frozen_routes: set[str] = set()
        self._compression_level: float = 0.0
        self._repair_active: bool = False
        self._stability_history: list[StabilityState] = []

    def evaluate(
        self, field_manager: FieldStateManager,
        resonance_engine: ResonanceEngine = None,
    ) -> StabilityState:
        """
        Evaluate current field stability and apply rules if needed.
        """
        now = time.time()

        # Calculate instability level
        drift_alerts = field_manager.get_drift_alerts()
        entropy_budget = field_manager.current_state.entropy_budget
        resonance_level = field_manager.current_state.resonance_level

        instability = min(1.0, (
            len(drift_alerts) * 0.15 +
            (1.0 - entropy_budget) * 0.3 +
            (1.0 - resonance_level) * 0.3 +
            (1.0 - field_manager.current_state.stability_index) * 0.25
        ))

        is_stable = instability < self.instability_threshold

        state = StabilityState(
            timestamp=now,
            is_stable=is_stable,
            instability_level=round(instability, 4),
            active_attractors=len(field_manager.coherence_engine._observer_phases),
            frozen_routes=len(self._frozen_routes),
            repair_active=self._repair_active,
            compression_level=round(self._compression_level, 4),
        )

        # Apply stability rules if unstable
        if not is_stable:
            self._apply_stability_rules(field_manager, resonance_engine)

        self._stability_history.append(state)
        return state

    def _apply_stability_rules(
        self, field_manager: FieldStateManager,
        resonance_engine: ResonanceEngine = None,
    ) -> None:
        """
        Apply the 6 stability rules when instability exceeds threshold.
        """
        # 1. Reduce signal amplitude
        for signal in field_manager.signal_field.signals:
            signal.amplitude *= 0.7

        # 2. Compress observer state (reduce history)
        if len(field_manager.coherence_engine.history) > 100:
            field_manager.coherence_engine.history = field_manager.coherence_engine.history[-50:]

        # 3. Freeze non-essential routing
        self._frozen_routes.add("non_essential")

        # 4. Trigger repair observer
        self._repair_active = True
        field_manager.repair(amount=0.3)

        # 5. Rebuild local coherence (decay entropic signals)
        field_manager.signal_field.decay(factor=0.8)

        # 6. Reintegrate (gradually restore) - set compression level high when unstable
        self._compression_level = min(1.0, self._compression_level + 0.3)

    def reinforce(self, observer_cluster: list[str]) -> None:
        """
        Reinforce a stable observer cluster.
        Called when a cluster is repeatedly successful.
        """
        # Strengthen coupling between cluster members
        for i in range(len(observer_cluster)):
            for j in range(i + 1, len(observer_cluster)):
                # This would strengthen collar fields in a full implementation
                pass

    @property
    def stats(self) -> dict:
        if not self._stability_history:
            return {"total_evaluations": 0, "stable_ratio": 1.0}
        stable = sum(1 for s in self._stability_history if s.is_stable)
        return {
            "total_evaluations": len(self._stability_history),
            "stable_ratio": round(stable / len(self._stability_history), 4),
            "avg_instability": round(
                sum(s.instability_level for s in self._stability_history) / len(self._stability_history), 4
            ),
            "currently_frozen": len(self._frozen_routes),
            "repair_active": self._repair_active,
        }
