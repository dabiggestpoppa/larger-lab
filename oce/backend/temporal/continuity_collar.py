"""
V3 Phase 5 — Continuity Collar
Temporal continuity membranes between agents.

Maintains: shared project identity, synchronized mission context,
continuity inheritance, long-term collaboration state.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContinuityCollar:
    """
    A temporal continuity membrane between observers/agents.
    
    Collars form when agents collaborate on long-term projects.
    They maintain shared context and ensure continuity inheritance
    when agents join or leave a project.
    """
    collar_id: str
    observer_ids: list[str] = field(default_factory=list)
    shared_attractors: list[str] = field(default_factory=list)
    mission_context: dict = field(default_factory=dict)
    continuity_strength: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_sync: float = field(default_factory=time.time)
    sync_count: int = 0

    @property
    def is_active(self) -> bool:
        return (time.time() - self.last_sync) < 3600  # Active if synced within 1 hour

    @property
    def is_strong(self) -> bool:
        return self.continuity_strength > 0.6 and len(self.observer_ids) >= 2

    def sync(self) -> None:
        """Synchronize the collar — update last sync time."""
        self.last_sync = time.time()
        self.sync_count += 1
        self.continuity_strength = min(1.0, self.continuity_strength + 0.05)

    def add_observer(self, observer_id: str) -> None:
        if observer_id not in self.observer_ids:
            self.observer_ids.append(observer_id)

    def remove_observer(self, observer_id: str) -> None:
        if observer_id in self.observer_ids:
            self.observer_ids.remove(observer_id)
            self.continuity_strength = max(0.0, self.continuity_strength - 0.1)

    def to_dict(self) -> dict:
        return {
            "collar_id": self.collar_id,
            "observers": self.observer_ids,
            "strength": round(self.continuity_strength, 4),
            "is_active": self.is_active,
            "is_strong": self.is_strong,
            "sync_count": self.sync_count,
        }


class ContinuityCollarManager:
    """Manages continuity collars across the cognitive field."""

    def __init__(self):
        self.collars: dict[str, ContinuityCollar] = {}

    def create_collar(self, observer_ids: list[str], mission: str = "") -> ContinuityCollar:
        """Create a new continuity collar."""
        cid = f"collar_{int(time.time())}"
        collar = ContinuityCollar(
            collar_id=cid,
            observer_ids=observer_ids,
            mission_context={"mission": mission},
        )
        self.collars[cid] = collar
        return collar

    def get_collar(self, collar_id: str) -> Optional[ContinuityCollar]:
        return self.collars.get(collar_id)

    def find_collar_for_observer(self, observer_id: str) -> list[ContinuityCollar]:
        """Find all collars involving an observer."""
        return [c for c in self.collars.values() if observer_id in c.observer_ids]

    def sync_collar(self, collar_id: str) -> None:
        """Synchronize a collar."""
        collar = self.collars.get(collar_id)
        if collar:
            collar.sync()

    def get_active_collars(self) -> list[ContinuityCollar]:
        return [c for c in self.collars.values() if c.is_active]

    @property
    def stats(self) -> dict:
        active = sum(1 for c in self.collars.values() if c.is_active)
        strong = sum(1 for c in self.collars.values() if c.is_strong)
        return {
            "total_collars": len(self.collars),
            "active_collars": active,
            "strong_collars": strong,
        }
