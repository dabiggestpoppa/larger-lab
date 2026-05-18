"""
V3 Phase 7 — Entropy Containment Boundaries
Localize instability, prevent global cascade.

Most entropy resolves at the local level without affecting the
broader field. Containment boundaries prevent local instability
from cascading into global collapse.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContainmentBoundary:
    """A boundary that contains entropy at a particular scale."""
    boundary_id: str
    scale: str           # "local", "regional", "global"
    capacity: float = 1.0    # How much entropy this boundary can contain
    current_load: float = 0.0
    is_contained: bool = True
    created_at: float = field(default_factory=time.time)
    last_breach: float = 0.0

    @property
    def utilization(self) -> float:
        return self.current_load / max(self.capacity, 0.01)

    @property
    def is_breached(self) -> bool:
        return self.utilization > 0.9

    @property
    def is_critical(self) -> bool:
        return self.utilization > 0.7

    def add_entropy(self, amount: float) -> bool:
        """Add entropy to this boundary. Returns True if breached."""
        self.current_load = min(self.capacity * 1.5, self.current_load + amount)
        if self.is_breached:
            self.is_contained = False
            self.last_breach = time.time()
            return True
        return False

    def resolve_entropy(self, amount: float) -> None:
        """Resolve entropy (reduce load)."""
        self.current_load = max(0.0, self.current_load - amount)
        if self.current_load < self.capacity * 0.5:
            self.is_contained = True


class EntropyContainmentSystem:
    """
    Manages entropy containment boundaries across scales.
    
    Key principle: most instability resolves locally without
    affecting the broader field. Containment boundaries prevent
    local entropy from cascading into global collapse.
    
    Escalation path:
    1. Local containment (handles most entropy)
    2. Regional containment (handles overflow from local)
    3. Global containment (last resort for systemic issues)
    """

    def __init__(self):
        self.boundaries: dict[str, ContainmentBoundary] = {}
        self._init_default_boundaries()

    def _init_default_boundaries(self) -> None:
        """Initialize default containment boundaries."""
        self.boundaries["local"] = ContainmentBoundary(
            boundary_id="local_containment", scale="local", capacity=1.0,
        )
        self.boundaries["regional"] = ContainmentBoundary(
            boundary_id="regional_containment", scale="regional", capacity=2.0,
        )
        self.boundaries["global"] = ContainmentBoundary(
            boundary_id="global_containment", scale="global", capacity=5.0,
        )

    def add_entropy(self, scale: str, amount: float) -> bool:
        """Add entropy to a containment boundary. Returns True if breached."""
        boundary = self.boundaries.get(scale)
        if boundary:
            breached = boundary.add_entropy(amount)
            if breached and scale == "local":
                # Escalate to regional
                self.add_entropy("regional", amount * 0.5)
            elif breached and scale == "regional":
                # Escalate to global
                self.add_entropy("global", amount * 0.3)
            return breached
        return False

    def resolve_entropy(self, scale: str, amount: float) -> None:
        """Resolve entropy at a scale."""
        boundary = self.boundaries.get(scale)
        if boundary:
            boundary.resolve_entropy(amount)

    def get_containment_status(self) -> dict:
        """Get the containment status across all scales."""
        return {
            b_id: {
                "scale": b.scale,
                "utilization": round(b.utilization, 4),
                "contained": b.is_contained,
                "breached": b.is_breached,
                "critical": b.is_critical,
            }
            for b_id, b in self.boundaries.items()
        }

    def get_critical_boundaries(self) -> list[ContainmentBoundary]:
        """Get all boundaries that are near or past capacity."""
        return [b for b in self.boundaries.values() if b.is_critical]

    @property
    def stats(self) -> dict:
        critical = sum(1 for b in self.boundaries.values() if b.is_critical)
        breached = sum(1 for b in self.boundaries.values() if b.is_breached)
        return {
            "total_boundaries": len(self.boundaries),
            "critical": critical,
            "breached": breached,
            "avg_utilization": round(
                sum(b.utilization for b in self.boundaries.values()) / max(len(self.boundaries), 1), 4
            ),
        }
