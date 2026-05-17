"""
V3 Phase 3 — Resonance Router
Replaces static routing with resonance-weighted propagation.

Old routing: observer_id, event_type, priority → shortest path
New routing: resonance compatibility, trajectory alignment, entropy pressure, collar affinity → resonance-weighted propagation

Score = coherence_alignment - entropy_cost + topology_affinity + resonance_density
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from resonance import SignalPacket, ResonanceEngine
from .collar_field import CollarFieldEngine


@dataclass
class Route:
    """A resonance-weighted route for signal propagation."""
    signal_id: str
    target_observer: str
    score: float               # 0.0-1.0
    coherence_alignment: float
    entropy_cost: float
    topology_affinity: float
    resonance_density: float
    timestamp: float = field(default_factory=time.time)

    @property
    def is_viable(self) -> bool:
        return self.score > 0.3

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "target_observer": self.target_observer,
            "score": round(self.score, 4),
            "coherence_alignment": round(self.coherence_alignment, 4),
            "entropy_cost": round(self.entropy_cost, 4),
            "topology_affinity": round(self.topology_affinity, 4),
            "resonance_density": round(self.resonance_density, 4),
            "is_viable": self.is_viable,
        }


class ResonanceRouter:
    """
    Routes signals through the cognitive field based on resonance weighting.
    
    Instead of hardcoded routing rules, signals flow along paths of
    highest resonance. This creates natural load balancing and ensures
    signals reach the observers best equipped to process them.
    """

    def __init__(self, collar_engine: CollarFieldEngine = None):
        self.collar_engine = collar_engine or CollarFieldEngine()
        self._route_history: list[Route] = []
        self._max_history = 5000

    def calculate_route(
        self, signal: SignalPacket, observer_id: str,
        observer_phase: float, observer_coherence: float,
        resonance_engine: ResonanceEngine,
    ) -> Route:
        """
        Calculate resonance-weighted route score for a signal → observer path.
        
        Score = coherence_alignment - entropy_cost + topology_affinity + resonance_density
        """
        # Coherence alignment: how well signal coherence matches observer coherence
        coherence_alignment = 1.0 - abs(signal.coherence - observer_coherence)

        # Entropy cost: how much entropy this routing choice consumes
        entropy_cost = signal.entropy_delta * 0.5

        # Topology affinity: collar field strength between source and target
        topology_affinity = self._get_topology_affinity(signal.source, observer_id)

        # Resonance density: how many resonant signals are already flowing to this observer
        resonance_density = self._get_resonance_density(observer_id, resonance_engine)

        # Final score
        score = max(0.0, coherence_alignment - entropy_cost + topology_affinity + resonance_density)
        score = min(1.0, score)

        route = Route(
            signal_id=signal.signal_id,
            target_observer=observer_id,
            score=score,
            coherence_alignment=coherence_alignment,
            entropy_cost=entropy_cost,
            topology_affinity=topology_affinity,
            resonance_density=resonance_density,
        )

        self._route_history.append(route)
        if len(self._route_history) > self._max_history:
            self._route_history = self._route_history[-self._max_history:]

        return route

    def find_best_route(
        self, signal: SignalPacket,
        observers: dict[str, tuple[float, float]],
        resonance_engine: ResonanceEngine,
    ) -> Optional[Route]:
        """Find the best route for a signal across all observers."""
        best_route = None
        best_score = 0.0

        for obs_id, (phase, coherence) in observers.items():
            route = self.calculate_route(signal, obs_id, phase, coherence, resonance_engine)
            if route.is_viable and route.score > best_score:
                best_score = route.score
                best_route = route

        return best_route

    def _get_topology_affinity(self, source: str, target: str) -> float:
        """Get topology affinity from collar fields."""
        collar = self.collar_engine.collars.get(source)
        if collar and target in collar.resonance_map:
            return collar.resonance_map[target]
        return 0.1  # Default low affinity

    def _get_resonance_density(self, observer_id: str, resonance_engine: ResonanceEngine) -> float:
        """Calculate resonance density for an observer."""
        if observer_id in resonance_engine.field_manager.coherence_engine._observer_coherences:
            return resonance_engine.field_manager.coherence_engine._observer_coherences[observer_id]
        return 0.1

    @property
    def stats(self) -> dict:
        if not self._route_history:
            return {"total_routes": 0, "avg_score": 0.0, "viable_rate": 0.0}
        viable = sum(1 for r in self._route_history if r.is_viable)
        return {
            "total_routes": len(self._route_history),
            "avg_score": round(sum(r.score for r in self._route_history) / len(self._route_history), 4),
            "viable_rate": round(viable / len(self._route_history), 4),
        }
