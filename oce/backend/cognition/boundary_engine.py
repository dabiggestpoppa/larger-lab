"""
V3 Phase 6 — Boundary Engine
Defines operational limits, entropy tolerances, authority regions, resonance bands.

Prevents infinite recursion through constraint manifolds.
Without boundaries: the field collapses into entropy theater.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Boundary:
    """A boundary condition in the cognitive field."""
    boundary_id: str
    boundary_type: str       # "entropy", "recursion", "authority", "resonance", "compute"
    threshold: float = 0.5
    current_value: float = 0.0
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_triggered: float = 0.0
    trigger_count: int = 0

    @property
    def is_exceeded(self) -> bool:
        return self.current_value > self.threshold

    @property
    def utilization(self) -> float:
        if self.threshold == 0:
            return 0.0
        return self.current_value / self.threshold

    def update(self, value: float) -> bool:
        """Update current value. Returns True if boundary exceeded."""
        self.current_value = value
        if self.is_exceeded:
            self.last_triggered = time.time()
            self.trigger_count += 1
            return True
        return False


class BoundaryEngine:
    """
    Manages boundary conditions for the cognitive field.
    
    Boundaries prevent:
    - Infinite recursion (recursion depth limits)
    - Entropy overflow (entropy budget limits)
    - Authority violations (permission boundaries)
    - Resonance collapse (minimum coherence thresholds)
    - Exhaustion (compute budget limits)
    """

    def __init__(self):
        self.boundaries: dict[str, Boundary] = {}
        self._init_default_boundaries()

    def _init_default_boundaries(self) -> None:
        """Initialize default boundary conditions."""
        defaults = [
            ("entropy_max", "entropy", 0.8),
            ("recursion_max", "recursion", 10.0),
            ("authority_scope", "authority", 1.0),
            ("resonance_min", "resonance", 0.2),
            ("compute_max", "compute", 1.0),
        ]
        for bid, btype, threshold in defaults:
            self.boundaries[bid] = Boundary(
                boundary_id=bid,
                boundary_type=btype,
                threshold=threshold,
            )

    def add_boundary(self, boundary_id: str, boundary_type: str, threshold: float) -> Boundary:
        """Add a new boundary."""
        b = Boundary(boundary_id=boundary_id, boundary_type=boundary_type, threshold=threshold)
        self.boundaries[boundary_id] = b
        return b

    def check(self, boundary_id: str, value: float) -> bool:
        """Check a boundary value. Returns True if exceeded."""
        b = self.boundaries.get(boundary_id)
        if b:
            return b.update(value)
        return False

    def check_all(self, metrics: dict[str, float]) -> list[str]:
        """Check all boundaries against current metrics. Returns list of exceeded boundaries."""
        exceeded = []
        for bid, b in self.boundaries.items():
            if bid in metrics:
                if b.update(metrics[bid]):
                    exceeded.append(bid)
        return exceeded

    def get_pressure(self, boundary_id: str) -> float:
        """Get the pressure on a boundary (0-1, where 1 = at threshold)."""
        b = self.boundaries.get(boundary_id)
        if b:
            return b.utilization
        return 0.0

    def get_critical_boundaries(self) -> list[Boundary]:
        """Get all boundaries that are near or exceeding threshold."""
        return [b for b in self.boundaries.values() if b.utilization > 0.7]

    @property
    def stats(self) -> dict:
        exceeded = sum(1 for b in self.boundaries.values() if b.is_exceeded)
        critical = sum(1 for b in self.boundaries.values() if b.utilization > 0.7)
        return {
            "total_boundaries": len(self.boundaries),
            "exceeded": exceeded,
            "critical": critical,
            "avg_pressure": round(
                sum(b.utilization for b in self.boundaries.values()) / max(len(self.boundaries), 1), 4
            ),
        }
