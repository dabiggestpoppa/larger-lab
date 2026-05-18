"""
V3 Phase 2 — Overlap Manifold Engine
Where shared cognition actually emerges.

Observers reconstruct through:
- Overlap zones (shared state regions)
- Resonance intersections (where observer fields intersect)
- Shared attractor projections (multiple observers projecting same attractor)

This is where global continuity emerges from local partial projections.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from .attractor_memory import AttractorMemory, Attractor


@dataclass
class OverlapZone:
    """
    A region where multiple observers share state.
    
    Overlap zones are the mechanism for distributed cognition:
    no observer has full continuity, but overlap between observers
    allows global continuity to emerge.
    """
    zone_id: str
    observer_ids: list[str] = field(default_factory=list)
    shared_attractors: list[str] = field(default_factory=list)
    overlap_strength: float = 0.5     # 0.0-1.0
    continuity_score: float = 0.5     # How much continuity is preserved in this zone
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    @property
    def observer_count(self) -> int:
        return len(self.observer_ids)

    @property
    def is_active(self) -> bool:
        """Zone is active if used within last hour."""
        return (time.time() - self.last_active) < 3600

    @property
    def is_strong(self) -> bool:
        """Strong zone has high overlap and multiple observers."""
        return self.overlap_strength > 0.6 and self.observer_count >= 2

    def add_observer(self, observer_id: str) -> None:
        if observer_id not in self.observer_ids:
            self.observer_ids.append(observer_id)
        self.last_active = time.time()

    def remove_observer(self, observer_id: str) -> None:
        if observer_id in self.observer_ids:
            self.observer_ids.remove(observer_id)
        self.last_active = time.time()

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "observer_count": self.observer_count,
            "overlap_strength": round(self.overlap_strength, 4),
            "continuity_score": round(self.continuity_score, 4),
            "is_active": self.is_active,
            "is_strong": self.is_strong,
        }


class OverlapManifold:
    """
    Manages overlap zones between observers.
    
    Key insight: global cognition doesn't require global state.
    It emerges from the overlap between local projections.
    Each observer stores partial state; overlap zones provide
    the shared context needed for coherent collective behavior.
    """

    def __init__(self):
        self.zones: dict[str, OverlapZone] = {}
        self._observer_zones: dict[str, list[str]] = {}  # observer_id -> [zone_ids]
        self._attractor_zones: dict[str, list[str]] = {}  # attractor_id -> [zone_ids]

    def create_zone(
        self, observer_ids: list[str], shared_attractors: list[str] = None,
    ) -> OverlapZone:
        """Create a new overlap zone."""
        zone_id = f"zone_{len(self.zones)}"
        zone = OverlapZone(
            zone_id=zone_id,
            observer_ids=observer_ids,
            shared_attractors=shared_attractors or [],
        )
        self.zones[zone_id] = zone
        
        # Index by observer
        for obs_id in observer_ids:
            if obs_id not in self._observer_zones:
                self._observer_zones[obs_id] = []
            self._observer_zones[obs_id].append(zone_id)
        
        # Index by attractor
        for att_id in (shared_attractors or []):
            if att_id not in self._attractor_zones:
                self._attractor_zones[att_id] = []
            self._attractor_zones[att_id].append(zone_id)
        
        return zone

    def find_zone(self, observer_ids: list[str]) -> Optional[OverlapZone]:
        """Find an overlap zone containing all specified observers."""
        for zone in self.zones.values():
            if all(obs in zone.observer_ids for obs in observer_ids):
                return zone
        return None

    def get_zones_for_observer(self, observer_id: str) -> list[OverlapZone]:
        """Get all overlap zones involving an observer."""
        zone_ids = self._observer_zones.get(observer_id, [])
        return [self.zones[zid] for zid in zone_ids if zid in self.zones]

    def get_shared_observers(self, observer_a: str, observer_b: str) -> list[str]:
        """Find observers that share zones with both A and B."""
        zones_a = set(self._observer_zones.get(observer_a, []))
        zones_b = set(self._observer_zones.get(observer_b, []))
        shared_zones = zones_a & zones_b
        
        shared = set()
        for zid in shared_zones:
            zone = self.zones.get(zid)
            if zone:
                shared.update(zone.observer_ids)
        
        shared.discard(observer_a)
        shared.discard(observer_b)
        return list(shared)

    def synthesize_shared_state(
        self, observer_ids: list[str], attractor_memory: AttractorMemory,
    ) -> dict:
        """
        Synthesize a shared state from overlapping observer projections.
        
        This is where collective intelligence emerges:
        each observer contributes their partial view,
        and the overlap zone synthesizes a coherent whole.
        """
        zone = self.find_zone(observer_ids)
        if not zone:
            return {"synthesized": False, "reason": "no_overlap_zone"}

        # Gather attractors from all observers in the zone
        all_attractors = []
        for obs_id in observer_ids:
            attractors = attractor_memory.find_by_observer(obs_id)
            all_attractors.extend(attractors)

        if not all_attractors:
            return {"synthesized": False, "reason": "no_attractors"}

        # Find common attractors (shared across multiple observers)
        attractor_counts: dict[str, int] = {}
        for att in all_attractors:
            attractor_counts[att.attractor_id] = attractor_counts.get(att.attractor_id, 0) + 1

        common = [aid for aid, count in attractor_counts.items() if count > 1]
        common_attractors = [attractor_memory.recall(aid) for aid in common if attractor_memory.recall(aid)]

        if common_attractors:
            # Use the most stable common attractor as the shared state anchor
            best = max(common_attractors, key=lambda a: a.stability)
            return {
                "synthesized": True,
                "anchor_attractor": best.attractor_id,
                "state_id": best.state_id,
                "coherence": best.coherence,
                "stability": best.stability,
                "observer_count": len(observer_ids),
                "common_attractor_count": len(common_attractors),
            }

        # No common attractors — use the most stable individual one
        best = max(all_attractors, key=lambda a: a.stability)
        return {
            "synthesized": True,
            "anchor_attractor": best.attractor_id,
            "state_id": best.state_id,
            "coherence": best.coherence * 0.7,  # Reduced confidence
            "stability": best.stability,
            "observer_count": len(observer_ids),
            "common_attractor_count": 0,
            "warning": "no_common_attractors",
        }

    def calculate_overlap_strength(self, observer_a: str, observer_b: str) -> float:
        """Calculate overlap strength between two observers."""
        zones_a = set(self._observer_zones.get(observer_a, []))
        zones_b = set(self._observer_zones.get(observer_b, []))
        
        if not zones_a or not zones_b:
            return 0.0
        
        shared = zones_a & zones_b
        total = zones_a | zones_b
        
        return len(shared) / max(len(total), 1)

    @property
    def stats(self) -> dict:
        """Overlap manifold statistics."""
        active = sum(1 for z in self.zones.values() if z.is_active)
        strong = sum(1 for z in self.zones.values() if z.is_strong)
        return {
            "total_zones": len(self.zones),
            "active_zones": active,
            "strong_zones": strong,
            "tracked_observers": len(self._observer_zones),
            "avg_observers_per_zone": round(
                sum(z.observer_count for z in self.zones.values()) / max(len(self.zones), 1), 2
            ),
        }

    def __repr__(self) -> str:
        return f"OverlapManifold(zones={len(self.zones)}, active={sum(1 for z in self.zones.values() if z.is_active)})"
