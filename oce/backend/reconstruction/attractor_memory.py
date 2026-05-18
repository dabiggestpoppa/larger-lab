"""
V3 Phase 2 — Attractor Memory Engine
Stores stable convergence states, NOT every event.

Old memory: store every event → linear growth → bloat.
New memory: store stable convergence states → structural persistence → compression.

An attractor is a state the system naturally converges to.
Storing attractors enables sparse reconstruction and low-bandwidth synchronization.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Attractor:
    """
    A stable convergence state of the cognitive field.
    
    Attractors are NOT events. They are patterns the system
    repeatedly settles into. Storing attractors allows the system
    to reconstruct continuity from sparse data.
    
    Example attractor:
    {
        "state_id": "stable_trading_research",
        "observer_cluster": ["planner", "execution", "memory"],
        "coherence": 0.94,
        "resonance_signature": ["low_entropy", "high_sync", "successful_execution"]
    }
    """
    state_id: str
    observer_cluster: list[str] = field(default_factory=list)
    coherence: float = 0.5
    resonance_signature: list[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    attractor_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: dict = field(default_factory=dict)

    @property
    def stability(self) -> float:
        """
        Stability score based on access recency and frequency.
        More frequently accessed = more stable attractor.
        """
        age = time.time() - self.created_at
        recency = 1.0 / (1.0 + (time.time() - self.last_accessed) / 3600)  # Decay over hours
        frequency = min(1.0, self.access_count / 10.0)  # Normalize to 10 accesses
        return (recency * 0.4 + frequency * 0.3 + self.coherence * 0.3)

    @property
    def is_stable(self) -> bool:
        return self.stability > 0.5

    def access(self) -> None:
        """Record an access to this attractor."""
        self.access_count += 1
        self.last_accessed = time.time()

    def to_dict(self) -> dict:
        return {
            "attractor_id": self.attractor_id,
            "state_id": self.state_id,
            "observer_cluster": self.observer_cluster,
            "coherence": round(self.coherence, 4),
            "resonance_signature": self.resonance_signature,
            "access_count": self.access_count,
            "stability": round(self.stability, 4),
            "is_stable": self.is_stable,
        }


class AttractorMemory:
    """
    Manages attractor storage and retrieval.
    
    Key insight: instead of storing every state transition,
    store only the stable attractors the system converges to.
    Continuity can be reconstructed by finding the nearest attractor.
    """

    def __init__(self, max_attractors: int = 1000):
        self.attractors: dict[str, Attractor] = {}
        self._coherence_index: dict[float, list[str]] = {}  # coherence -> [attractor_ids]
        self._observer_index: dict[str, list[str]] = {}     # observer -> [attractor_ids]
        self.max_attractors = max_attractors

    def store(self, attractor: Attractor) -> str:
        """Store an attractor."""
        # Check if similar attractor already exists
        existing = self._find_similar(attractor)
        if existing:
            # Merge: update coherence and access count
            existing.coherence = max(existing.coherence, attractor.coherence)
            existing.access_count += 1
            existing.last_accessed = time.time()
            # Merge observer clusters
            for obs in attractor.observer_cluster:
                if obs not in existing.observer_cluster:
                    existing.observer_cluster.append(obs)
            existing.resonance_signature = list(set(existing.resonance_signature + attractor.resonance_signature))
            return existing.attractor_id

        self.attractors[attractor.attractor_id] = attractor
        self._index_attractor(attractor)
        
        # Evict unstable attractors if over capacity
        if len(self.attractors) > self.max_attractors:
            self._evict_unstable(keep=self.max_attractors * 8 // 10)
        
        return attractor.attractor_id

    def create_attractor(
        self, state_id: str, observer_cluster: list[str],
        coherence: float, resonance_signature: list[str] = None,
    ) -> Attractor:
        """Create and store a new attractor."""
        attractor = Attractor(
            state_id=state_id,
            observer_cluster=observer_cluster,
            coherence=coherence,
            resonance_signature=resonance_signature or [],
        )
        self.store(attractor)
        return attractor

    def recall(self, attractor_id: str) -> Optional[Attractor]:
        """Retrieve an attractor by ID."""
        attractor = self.attractors.get(attractor_id)
        if attractor:
            attractor.access()
        return attractor

    def find_nearest(self, coherence: float, observers: list[str] = None) -> Optional[Attractor]:
        """
        Find the nearest attractor to a given coherence level and observer set.
        
        Distance = |coherence_diff| + (1 - observer_overlap)
        """
        if not self.attractors:
            return None

        best = None
        best_distance = float('inf')

        for attractor in self.attractors.values():
            coherence_dist = abs(attractor.coherence - coherence)
            if observers:
                overlap = len(set(attractor.observer_cluster) & set(observers))
                observer_dist = 1.0 - (overlap / max(len(observers), 1))
            else:
                observer_dist = 0.5
            distance = coherence_dist + observer_dist
            if distance < best_distance:
                best_distance = distance
                best = attractor

        if best:
            best.access()
        return best

    def find_by_observer(self, observer_id: str) -> list[Attractor]:
        """Find all attractors involving a specific observer."""
        ids = self._observer_index.get(observer_id, [])
        return [self.attractors[aid] for aid in ids if aid in self.attractors]

    def get_stable_attractors(self) -> list[Attractor]:
        """Get all stable attractors, sorted by stability (highest first)."""
        stable = [a for a in self.attractors.values() if a.is_stable]
        return sorted(stable, key=lambda a: a.stability, reverse=True)

    def get_resonance_signature(self, attractor_id: str) -> list[str]:
        """Get the resonance signature of an attractor."""
        attractor = self.attractors.get(attractor_id)
        return attractor.resonance_signature if attractor else []

    def _find_similar(self, attractor: Attractor) -> Optional[Attractor]:
        """Find a similar existing attractor (same state_id or high overlap)."""
        for existing in self.attractors.values():
            if existing.state_id == attractor.state_id:
                return existing
            # Check observer overlap
            if existing.observer_cluster and attractor.observer_cluster:
                overlap = len(set(existing.observer_cluster) & set(attractor.observer_cluster))
                if overlap / max(len(existing.observer_cluster), 1) > 0.7:
                    return existing
        return None

    def _index_attractor(self, attractor: Attractor) -> None:
        """Index an attractor for fast lookup."""
        # Coherence index (bucketed by 0.1)
        coh_key = round(attractor.coherence, 1)
        if coh_key not in self._coherence_index:
            self._coherence_index[coh_key] = []
        self._coherence_index[coh_key].append(attractor.attractor_id)
        # Observer index
        for obs in attractor.observer_cluster:
            if obs not in self._observer_index:
                self._observer_index[obs] = []
            self._observer_index[obs].append(attractor.attractor_id)

    def _evict_unstable(self, keep: int) -> None:
        """Evict least stable attractors to stay under capacity."""
        if len(self.attractors) <= keep:
            return
        sorted_attractors = sorted(self.attractors.values(), key=lambda a: a.stability)
        to_remove = sorted_attractors[:len(self.attractors) - keep]
        for attractor in to_remove:
            del self.attractors[attractor.attractor_id]

    @property
    def stats(self) -> dict:
        """Attractor memory statistics."""
        stable = sum(1 for a in self.attractors.values() if a.is_stable)
        return {
            "total_attractors": len(self.attractors),
            "stable_attractors": stable,
            "unstable_attractors": len(self.attractors) - stable,
            "avg_coherence": round(sum(a.coherence for a in self.attractors.values()) / max(len(self.attractors), 1), 4),
            "avg_stability": round(sum(a.stability for a in self.attractors.values()) / max(len(self.attractors), 1), 4),
            "total_accesses": sum(a.access_count for a in self.attractors.values()),
        }

    def __repr__(self) -> str:
        return f"AttractorMemory(attractors={len(self.attractors)}, stable={sum(1 for a in self.attractors.values() if a.is_stable)})"
