"""
V3 Phase 1 — Resonance Engine
Core resonance alignment and scoring mechanism.

The resonance engine is the "thinking" mechanism of the cognitive field.
Not reasoning chains — constraint harmonization through phase-locking.

CCR (Coherent Constraint Resonance): cognition is phase-locking between constraints.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from .signal_packet import SignalPacket, SignalField
from .coherence_metrics import CoherenceEngine, CoherenceSnapshot
from .boundary_mapper import BoundaryMapper
from .field_state import FieldStateManager, FieldState


@dataclass
class ResonanceScore:
    """Result of a resonance scoring operation."""
    observer_id: str
    signal_id: str
    score: float           # 0.0-1.0
    coherence_alignment: float
    phase_proximity: float
    amplitude_factor: float
    entropy_cost: float
    timestamp: float = field(default_factory=time.time)

    @property
    def is_viable(self) -> bool:
        """A resonance is viable if score > 0.3 and entropy_cost < 0.5."""
        return self.score > 0.3 and self.entropy_cost < 0.5

    def to_dict(self) -> dict:
        return {
            "observer_id": self.observer_id,
            "signal_id": self.signal_id,
            "score": round(self.score, 4),
            "coherence_alignment": round(self.coherence_alignment, 4),
            "phase_proximity": round(self.phase_proximity, 4),
            "amplitude_factor": round(self.amplitude_factor, 4),
            "entropy_cost": round(self.entropy_cost, 4),
            "is_viable": self.is_viable,
        }


@dataclass
class Constraint:
    """
    A constraint in the cognitive field.
    Constraints are phase-locked to produce cognition.
    """
    constraint_id: str
    constraint_type: str  # "goal", "system", "resource", "temporal"
    weight: float = 0.5
    phase: float = 0.0
    coherence: float = 0.5
    satisfied: bool = False

    def resonance_with(self, other: Constraint) -> float:
        """Calculate resonance between two constraints."""
        phase_diff = abs(self.phase - other.phase)
        phase_proximity = 1.0 - (phase_diff / (2 * math.pi))
        coherence_alignment = 1.0 - abs(self.coherence - other.coherence)
        return phase_proximity * coherence_alignment * min(self.weight, other.weight)


class ResonanceEngine:
    """
    Core resonance engine for the cognitive field.
    
    Instead of "What should happen next?", the resonance engine asks:
    "What future states maintain coherence with minimal entropy?"
    
    This is the CCR (Coherent Constraint Resonance) mechanism:
    cognition emerges from phase-locking between constraints.
    """

    def __init__(self):
        self.field_manager = FieldStateManager()
        self.boundary_mapper = BoundaryMapper()
        self._constraints: dict[str, Constraint] = {}
        self._resonance_history: list[ResonanceScore] = []
        self._max_history = 5000

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the resonance field."""
        self._constraints[constraint.constraint_id] = constraint

    def remove_constraint(self, constraint_id: str) -> None:
        """Remove a constraint."""
        self._constraints.pop(constraint_id, None)

    def score_resonance(
        self, observer_id: str, observer_phase: float, observer_coherence: float,
        signal: SignalPacket,
    ) -> ResonanceScore:
        """
        Score resonance between an observer and a signal.
        
        Score = coherence_alignment × amplitude × phase_proximity - entropy_cost
        
        This is the BSP routing score: signals route to observers
        based on resonance compatibility, not hardcoded rules.
        """
        coherence_alignment = 1.0 - abs(signal.coherence - observer_coherence)
        phase_diff = abs(signal.phase - observer_phase)
        phase_proximity = 1.0 - (phase_diff / (2 * math.pi))
        amplitude_factor = signal.amplitude
        entropy_cost = signal.entropy_delta

        raw_score = coherence_alignment * amplitude_factor * phase_proximity
        adjusted_score = max(0.0, raw_score - entropy_cost * 0.5)

        score = ResonanceScore(
            observer_id=observer_id,
            signal_id=signal.signal_id,
            score=min(1.0, adjusted_score),
            coherence_alignment=coherence_alignment,
            phase_proximity=phase_proximity,
            amplitude_factor=amplitude_factor,
            entropy_cost=entropy_cost,
        )

        self._resonance_history.append(score)
        if len(self._resonance_history) > self._max_history:
            self._resonance_history = self._resonance_history[-self._max_history:]

        return score

    def find_best_observer(
        self, signal: SignalPacket,
        observers: dict[str, tuple[float, float]],  # observer_id -> (phase, coherence)
    ) -> Optional[str]:
        """
        Find the best observer for a signal based on resonance scoring.
        
        Returns the observer_id with the highest resonance score,
        or None if no viable resonance exists.
        """
        best_id = None
        best_score = 0.0

        for obs_id, (phase, coherence) in observers.items():
            score = self.score_resonance(obs_id, phase, coherence, signal)
            if score.is_viable and score.score > best_score:
                best_score = score.score
                best_id = obs_id

        return best_id

    def harmonize_constraints(self) -> float:
        """
        Calculate constraint harmonization level.
        
        This is the CCR mechanism: how well are constraints phase-locked?
        High harmonization = constraints are aligned = clear action path.
        Low harmonization = constraints conflict = need resolution.
        """
        if len(self._constraints) < 2:
            return 1.0

        constraints = list(self._constraints.values())
        total_resonance = 0.0
        pairs = 0

        for i in range(len(constraints)):
            for j in range(i + 1, len(constraints)):
                total_resonance += constraints[i].resonance_with(constraints[j])
                pairs += 1

        return total_resonance / max(pairs, 1)

    def get_action_path(self) -> list[str]:
        """
        Determine the stable action path from constraint harmonization.
        
        Returns constraint IDs sorted by resonance strength —
        the path of least entropy through the constraint field.
        """
        harmonization = self.harmonize_constraints()
        
        if harmonization > 0.7:
            # High harmonization: all constraints aligned
            return sorted(
                self._constraints.keys(),
                key=lambda cid: self._constraints[cid].weight,
                reverse=True,
            )
        elif harmonization > 0.3:
            # Medium: some conflict, prioritize by weight
            return sorted(
                self._constraints.keys(),
                key=lambda cid: self._constraints[cid].coherence,
                reverse=True,
            )
        else:
            # Low harmonization: conflict — return empty (need repair)
            return []

    def inject_and_score(self, signal: SignalPacket) -> dict:
        """
        Full pipeline: inject signal, update field, measure coherence, map boundaries.
        
        Returns a complete snapshot of the field state after injection.
        """
        # Inject signal
        self.field_manager.inject_signal(signal)
        
        # Detect boundaries
        boundaries = self.boundary_mapper.detect_boundaries(self.field_manager.signal_field)
        
        # Map pressure zones
        zones = self.boundary_mapper.map_pressure_zones()
        
        # Measure coherence
        coherence = self.field_manager.measure_coherence()
        
        return {
            "signal": signal.to_dict(),
            "boundaries_detected": len(boundaries),
            "pressure_zones": len(zones),
            "coherence": coherence.to_dict(),
            "field_state": self.field_manager.current_state.to_dict(),
            "drift_alerts": self.field_manager.get_drift_alerts(),
        }

    def decay_step(self) -> None:
        """Advance field by one decay step."""
        self.field_manager.decay_step()
        self.boundary_mapper.decay()

    def repair(self) -> None:
        """Trigger field repair."""
        self.field_manager.repair()

    @property
    def stats(self) -> dict:
        """Complete resonance engine statistics."""
        return {
            "field": self.field_manager.stats,
            "boundaries": self.boundary_mapper.stats,
            "constraints": len(self._constraints),
            "harmonization": round(self.harmonize_constraints(), 4),
            "resonance_history_size": len(self._resonance_history),
        }

    def __repr__(self) -> str:
        return (
            f"ResonanceEngine(constraints={len(self._constraints)}, "
            f"harmonization={self.harmonize_constraints():.2f}, "
            f"field={self.field_manager.current_state.health:.2f})"
        )
