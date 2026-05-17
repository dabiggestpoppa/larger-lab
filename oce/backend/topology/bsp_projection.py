"""
V3 Phase 3 — BSP Projection Engine
Generates probable stable trajectories and evaluates field alignment pressure.

BSP asks: "What future states maintain coherence with minimal entropy?"
NOT: "What should happen next?"

Outputs field guidance, NOT decisions:
- Pressure vectors
- Resonance gradients
- Coherence probabilities
- Attractor strength
- Topology recommendations
- Field tensions
- Instability warnings
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from resonance import SignalPacket, SignalField, ResonanceEngine, CoherenceEngine
from reconstruction import AttractorMemory, Attractor


@dataclass
class TrajectoryProjection:
    """A projected stable trajectory for the cognitive field."""
    projection_id: str
    state_cluster: str
    trajectory_type: str          # "stable", "divergent", "convergent", "chaotic"
    coherence_score: float        # 0.0-1.0
    entropy_pressure: float       # 0.0-1.0
    repair_risk: float            # 0.0-1.0
    recommended_observers: list[str] = field(default_factory=list)
    pressure_vectors: dict = field(default_factory=dict)
    resonance_gradients: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_stable(self) -> bool:
        return self.coherence_score > 0.6 and self.entropy_pressure < 0.4

    @property
    def needs_repair(self) -> bool:
        return self.repair_risk > 0.6 or self.entropy_pressure > 0.7

    def to_dict(self) -> dict:
        return {
            "projection_id": self.projection_id,
            "state_cluster": self.state_cluster,
            "trajectory_type": self.trajectory_type,
            "coherence_score": round(self.coherence_score, 4),
            "entropy_pressure": round(self.entropy_pressure, 4),
            "repair_risk": round(self.repair_risk, 4),
            "recommended_observers": self.recommended_observers,
            "is_stable": self.is_stable,
            "needs_repair": self.needs_repair,
        }


class BSPProjectionEngine:
    """
    Boundary Signal Projection engine.
    
    Projects current field state into probable future trajectories.
    Evaluates each trajectory for coherence, entropy pressure, and repair risk.
    
    This is NOT a planner. It outputs field guidance that influences
    orchestration decisions.
    """

    def __init__(self):
        self._projection_counter = 0

    def project(
        self, resonance_engine: ResonanceEngine,
        attractor_memory: AttractorMemory,
        observer_states: dict[str, tuple[float, float]] = None,
    ) -> TrajectoryProjection:
        """
        Generate a trajectory projection from current field state.
        
        Args:
            resonance_engine: Current resonance engine state
            attractor_memory: Stored attractors for proximity matching
            observer_states: observer_id -> (phase, coherence)
            
        Returns:
            TrajectoryProjection with field guidance
        """
        self._projection_counter += 1
        observer_states = observer_states or {}

        # Calculate coherence score from resonance engine
        field_coherence = resonance_engine.field_manager.current_state.resonance_level
        observer_coherence = 0.0
        if observer_states:
            coherences = [c for _, c in observer_states.values()]
            observer_coherence = sum(coherences) / len(coherences)
        coherence_score = (field_coherence + observer_coherence) / 2

        # Calculate entropy pressure
        entropy_pressure = resonance_engine.field_manager.current_state.entropy_budget
        entropy_pressure = 1.0 - entropy_pressure  # Invert: low budget = high pressure

        # Calculate repair risk
        drift_alerts = resonance_engine.field_manager.get_drift_alerts()
        repair_risk = min(1.0, len(drift_alerts) * 0.2)

        # Determine trajectory type
        if coherence_score > 0.7 and entropy_pressure < 0.3:
            trajectory_type = "stable"
        elif coherence_score < 0.3:
            trajectory_type = "chaotic"
        elif entropy_pressure > 0.6:
            trajectory_type = "divergent"
        else:
            trajectory_type = "convergent"

        # Find recommended observers (those with highest resonance)
        recommended = []
        if observer_states:
            sorted_observers = sorted(
                observer_states.items(),
                key=lambda x: x[1][1],  # Sort by coherence
                reverse=True,
            )
            recommended = [obs_id for obs_id, _ in sorted_observers[:3]]

        # Calculate pressure vectors per observer
        pressure_vectors = {}
        for obs_id, (phase, coh) in observer_states.items():
            pressure_vectors[obs_id] = {
                "phase": round(phase, 4),
                "coherence": round(coh, 4),
                "pressure": round((1.0 - coh) * entropy_pressure, 4),
            }

        # Calculate resonance gradients
        resonance_gradients = {}
        if len(observer_states) >= 2:
            obs_list = list(observer_states.items())
            for i in range(len(obs_list)):
                for j in range(i + 1, len(obs_list)):
                    id_a, (phase_a, coh_a) = obs_list[i]
                    id_b, (phase_b, coh_b) = obs_list[j]
                    gradient = abs(coh_a - coh_b)
                    resonance_gradients[f"{id_a}-{id_b}"] = round(gradient, 4)

        return TrajectoryProjection(
            projection_id=f"proj_{self._projection_counter}",
            state_cluster=self._identify_cluster(observer_states),
            trajectory_type=trajectory_type,
            coherence_score=coherence_score,
            entropy_pressure=entropy_pressure,
            repair_risk=repair_risk,
            recommended_observers=recommended,
            pressure_vectors=pressure_vectors,
            resonance_gradients=resonance_gradients,
        )

    def _identify_cluster(self, observer_states: dict) -> str:
        """Identify the current state cluster based on observer coherence."""
        if not observer_states:
            return "empty"
        coherences = [c for _, c in observer_states.values()]
        avg = sum(coherences) / len(coherences)
        if avg > 0.8:
            return "highly_coherent"
        elif avg > 0.5:
            return "moderately_coherent"
        elif avg > 0.3:
            return "weakly_coherent"
        return "incoherent"
