"""
V3 Phase 6 — Attractor Engine
Finds stable cognitive states: execution strategies, repair paths,
task hierarchies, symbolic meaning, planning direction.

Cognition through convergence, NOT search.
The system settles into stable attractors instead of searching endlessly.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from reconstruction.attractor_memory import AttractorMemory, Attractor


@dataclass
class CognitiveAttractor:
    """A stable cognitive state that the field converges to."""
    attractor_id: str
    attractor_type: str      # "execution", "repair", "hierarchy", "meaning", "planning"
    stability: float = 0.5
    convergence_count: int = 0
    field_alignment: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_convergence: float = field(default_factory=time.time)

    @property
    def is_stable(self) -> bool:
        return self.stability > 0.6 and self.convergence_count >= 3

    def converge(self) -> None:
        """Record a convergence event."""
        self.convergence_count += 1
        self.last_convergence = time.time()
        self.stability = min(1.0, self.stability + 0.1)


class AttractorEngine:
    """
    Finds and maintains stable cognitive states.
    
    Instead of searching through possibilities, the field:
    1. Identifies convergence points (attractors)
    2. Reinforces successful attractors
    3. Dissolves unstable structures
    4. Uses attractors as cognitive anchors
    
    This is the "thinking" mechanism — cognition through convergence.
    """

    def __init__(self, attractor_memory: AttractorMemory = None):
        self.attractor_memory = attractor_memory or AttractorMemory()
        self.cognitive_attractors: dict[str, CognitiveAttractor] = {}

    def find_attractor(
        self, state_space: list[str], coherence_values: list[float],
        observer_cluster: list[str] = None,
    ) -> Optional[CognitiveAttractor]:
        """
        Find the most stable attractor in a state space.
        
        Looks for clusters of high-coherence states that the field
        naturally converges to.
        """
        if not state_space or not coherence_values:
            return None

        # Find the highest coherence region
        best_idx = max(range(len(coherence_values)), key=lambda i: coherence_values[i])
        best_coherence = coherence_values[best_idx]

        if best_coherence < 0.3:
            return None  # No stable attractor found

        # Check if this converges an existing attractor
        for aid, attr in self.cognitive_attractors.items():
            if attr.attractor_type == "execution" and best_coherence > 0.5:
                attr.converge()
                return attr

        # Create new attractor
        aid = f"cog_attr_{int(time.time())}"
        attractor = CognitiveAttractor(
            attractor_id=aid,
            attractor_type=self._classify_attractor(state_space, coherence_values),
            stability=best_coherence,
            convergence_count=1,
            field_alignment=best_coherence,
        )
        self.cognitive_attractors[aid] = attractor
        return attractor

    def _classify_attractor(self, states: list[str], coherence: list[float]) -> str:
        """Classify the type of attractor based on state patterns."""
        avg_coherence = sum(coherence) / max(len(coherence), 1)
        if avg_coherence > 0.8:
            return "execution"
        elif avg_coherence > 0.5:
            return "planning"
        elif any("repair" in s.lower() for s in states):
            return "repair"
        return "meaning"

    def get_stable_attractors(self) -> list[CognitiveAttractor]:
        """Get all stable attractors, sorted by stability."""
        stable = [a for a in self.cognitive_attractors.values() if a.is_stable]
        return sorted(stable, key=lambda a: a.stability, reverse=True)

    def reinforce(self, attractor_id: str) -> None:
        """Reinforce a successful attractor."""
        attr = self.cognitive_attractors.get(attractor_id)
        if attr:
            attr.converge()

    def dissolve_weak(self) -> int:
        """Remove unstable attractors. Returns count removed."""
        to_remove = [
            aid for aid, attr in self.cognitive_attractors.items()
            if attr.stability < 0.2 and attr.convergence_count < 2
        ]
        for aid in to_remove:
            del self.cognitive_attractors[aid]
        return len(to_remove)

    @property
    def stats(self) -> dict:
        stable = sum(1 for a in self.cognitive_attractors.values() if a.is_stable)
        return {
            "total_attractors": len(self.cognitive_attractors),
            "stable_attractors": stable,
            "avg_stability": round(
                sum(a.stability for a in self.cognitive_attractors.values()) / max(len(self.cognitive_attractors), 1), 4
            ),
            "total_convergences": sum(a.convergence_count for a in self.cognitive_attractors.values()),
        }
