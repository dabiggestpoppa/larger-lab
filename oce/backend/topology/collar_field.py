"""
V3 Phase 3 — Active Collar Field Engine
Dynamic coherence membranes that replace static observer relationships.

Each collar tracks: observer affinity, shared memory resonance, synchronization cost,
entropy compatibility, task coupling, glyph compatibility.

Collars are NOT static — they form, strengthen, weaken, and dissolve based on
field dynamics. This is where topology self-organization begins.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CollarField:
    """
    A dynamic coherence membrane between observers.
    
    Collars form when observers frequently interact and share coherence.
    They strengthen with use and weaken with neglect.
    """
    observer_id: str
    resonance_map: dict = field(default_factory=dict)       # observer_id -> resonance_score
    entropy_cost: float = 0.5                                # Cost of syncing through this collar
    glyph_affinity: float = 0.5                              # Compatibility with glyph encoding
    coupling_strength: dict = field(default_factory=dict)   # observer_id -> coupling
    trajectory_alignment: float = 0.5                        # How aligned trajectories are
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    active: bool = True

    @property
    def connection_count(self) -> int:
        return len(self.resonance_map)

    @property
    def avg_resonance(self) -> float:
        if not self.resonance_map:
            return 0.0
        return sum(self.resonance_map.values()) / len(self.resonance_map)

    @property
    def is_strong(self) -> bool:
        return self.avg_resonance > 0.6 and self.connection_count >= 2

    @property
    def is_weakening(self) -> bool:
        return (time.time() - self.last_active) > 3600 or self.avg_resonance < 0.2

    def update_resonance(self, observer_id: str, score: float) -> None:
        self.resonance_map[observer_id] = max(0.0, min(1.0, score))
        self.last_active = time.time()

    def decay(self, factor: float = 0.95) -> None:
        for obs_id in self.resonance_map:
            self.resonance_map[obs_id] *= factor
        self.glyph_affinity *= factor
        self.trajectory_alignment *= factor


class CollarFieldEngine:
    """
    Manages dynamic collar fields across the cognitive field.
    
    Collars form when:
    - Observers frequently synchronize
    - Shared attractors are accessed
    - Task coupling is high
    
    Collars dissolve when:
    - Observers drift apart
    - Entropy cost exceeds benefit
    - No shared activity for extended period
    """

    def __init__(self):
        self.collars: dict[str, CollarField] = {}
        self._observer_collars: dict[str, list[str]] = {}  # observer_id -> [collar_ids]

    def get_or_create_collar(self, observer_id: str) -> CollarField:
        """Get existing collar or create new one for an observer."""
        if observer_id in self.collars:
            return self.collars[observer_id]
        collar = CollarField(observer_id=observer_id)
        self.collars[observer_id] = collar
        self._observer_collars[observer_id] = [observer_id]
        return collar

    def connect(self, observer_a: str, observer_b: str, initial_resonance: float = 0.5) -> None:
        """Create or strengthen a connection between two observers."""
        collar_a = self.get_or_create_collar(observer_a)
        collar_b = self.get_or_create_collar(observer_b)
        collar_a.update_resonance(observer_b, initial_resonance)
        collar_b.update_resonance(observer_a, initial_resonance)

    def disconnect(self, observer_a: str, observer_b: str) -> None:
        """Weaken a connection between two observers."""
        if observer_a in self.collars:
            self.collars[observer_a].update_resonance(observer_b, 0.0)
        if observer_b in self.collars:
            self.collars[observer_b].update_resonance(observer_a, 0.0)

    def get_resonance_matrix(self) -> dict[str, dict[str, float]]:
        """Get the full resonance matrix between all observers."""
        matrix = {}
        for obs_id, collar in self.collars.items():
            matrix[obs_id] = dict(collar.resonance_map)
        return matrix

    def get_strongest_connections(self, observer_id: str, top_n: int = 5) -> list[tuple[str, float]]:
        """Get the strongest connections for an observer."""
        collar = self.collars.get(observer_id)
        if not collar:
            return []
        sorted_conns = sorted(collar.resonance_map.items(), key=lambda x: x[1], reverse=True)
        return sorted_conns[:top_n]

    def get_field_coherence(self) -> float:
        """Calculate overall field coherence from collar strengths."""
        if not self.collars:
            return 1.0
        resonances = [c.avg_resonance for c in self.collars.values()]
        return sum(resonances) / len(resonances)

    def decay_step(self) -> None:
        """Decay all collar fields."""
        for collar in self.collars.values():
            collar.decay()
        # Remove dead collars
        dead = [oid for oid, c in self.collars.items() if c.is_weakening and c.connection_count == 0]
        for oid in dead:
            del self.collars[oid]
            self._observer_collars.pop(oid, None)

    @property
    def stats(self) -> dict:
        active = sum(1 for c in self.collars.values() if c.active)
        strong = sum(1 for c in self.collars.values() if c.is_strong)
        return {
            "total_collars": len(self.collars),
            "active_collars": active,
            "strong_collars": strong,
            "field_coherence": round(self.get_field_coherence(), 4),
        }
