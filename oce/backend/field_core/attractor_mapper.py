"""
V3 Phase 9 — Attractor Mapper
Detects stable recurring configurations.
Maps attractor basins and identifies stable field configurations.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AttractorState:
    """A detected attractor in the field."""
    attractor_id: str
    name: str
    basin_size: int = 0  # number of states in the basin
    stability: float = 0.5  # 0-1, how stable this attractor is
    visit_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    @property
    def is_stable(self) -> bool:
        return self.stability > 0.6 and self.visit_count >= 3

    @property
    def age_seconds(self) -> float:
        return time.time() - self.first_seen

    def record_visit(self) -> None:
        self.visit_count += 1
        self.last_seen = time.time()
        # Stability increases with repeated visits
        self.stability = min(1.0, self.stability + 0.05)


class AttractorMapper:
    """
    Detects stable recurring field configurations.
    
    Maps attractor basins — regions of field state space that the system
    naturally gravitates toward. Stable attractors indicate healthy
    recurring patterns; drifting attractors indicate instability.
    """

    def __init__(self):
        self._attractors: dict[str, AttractorState] = {}
        self._state_history: list[dict] = []

    def register_attractor(self, name: str, attractor_id: str = "") -> AttractorState:
        """Register a new attractor."""
        aid = attractor_id or f"attr_{len(self._attractors)}"
        attractor = AttractorState(
            attractor_id=aid, name=name,
        )
        self._attractors[aid] = attractor
        return attractor

    def record_state(self, state: dict) -> Optional[AttractorState]:
        """Record a field state. Returns nearest attractor if found."""
        self._state_history.append(state)

        # Find nearest attractor by state similarity
        best_match = None
        best_score = 0.0

        for attractor in self._attractors.values():
            score = self._compute_similarity(state, attractor)
            if score > best_score and score > 0.5:
                best_score = score
                best_match = attractor

        if best_match:
            best_match.record_visit()
            best_match.basin_size += 1

        return best_match

    def _compute_similarity(self, state: dict, attractor: AttractorState) -> float:
        """Compute similarity between a state and an attractor."""
        # Simple similarity: fraction of matching keys
        if not self._state_history:
            return 0.0
        # Compare against states previously associated with this attractor
        # For now, use visit count as a proxy for basin membership
        return min(1.0, attractor.visit_count / 10.0)

    def get_stable_attractors(self) -> list[AttractorState]:
        """Get all stable attractors."""
        return sorted(
            [a for a in self._attractors.values() if a.is_stable],
            key=lambda a: a.stability,
            reverse=True,
        )

    def get_attractor(self, attractor_id: str) -> Optional[AttractorState]:
        return self._attractors.get(attractor_id)

    def get_drifting_attractors(self, threshold: float = 0.3) -> list[AttractorState]:
        """Get attractors with low stability (drifting)."""
        return [a for a in self._attractors.values() if a.stability < threshold]

    @property
    def stats(self) -> dict:
        stable = sum(1 for a in self._attractors.values() if a.is_stable)
        drifting = sum(1 for a in self._attractors.values() if a.stability < 0.3)
        return {
            "total_attractors": len(self._attractors),
            "stable_attractors": stable,
            "drifting_attractors": drifting,
            "total_states_recorded": len(self._state_history),
        }
