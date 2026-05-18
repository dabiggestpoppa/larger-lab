"""
V3 Phase 8 — Constraint Model
Models real operator constraints (time, energy, bandwidth).

The system learns what the operator can and cannot do,
and adapts its behavior accordingly.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OperatorConstraint:
    """A constraint on the operator's capacity."""
    constraint_id: str
    constraint_type: str     # "time", "energy", "bandwidth", "focus", "availability"
    description: str
    severity: float = 0.5    # 0-1, how limiting this constraint is
    is_active: bool = True
    observed_count: int = 0
    first_observed: float = field(default_factory=time.time)
    last_observed: float = field(default_factory=time.time)

    def record_observation(self) -> None:
        self.observed_count += 1
        self.last_observed = time.time()
        self.severity = min(1.0, self.severity + 0.05)


class ConstraintModel:
    """
    Models real operator constraints.
    
    Tracks:
    - Time constraints (when is the operator available?)
    - Energy constraints (when is the operator fatigued?)
    - Bandwidth constraints (how much can the operator handle?)
    - Focus constraints (what is the operator currently focused on?)
    - Availability constraints (is the operator present?)
    
    The system uses these constraints to adapt its behavior:
    - Don't overwhelm during low-bandwidth periods
    - Prioritize during high-energy periods
    - Respect time boundaries
    """

    def __init__(self):
        self.constraints: dict[str, OperatorConstraint] = {}
        self._init_default_constraints()

    def _init_default_constraints(self) -> None:
        """Initialize default constraints."""
        defaults = [
            ("time", "Operator has limited time available", 0.5),
            ("energy", "Operator energy varies throughout the day", 0.5),
            ("bandwidth", "Operator can only process so much at once", 0.6),
            ("focus", "Operator focus is on specific tasks", 0.4),
            ("availability", "Operator is not always present", 0.7),
        ]
        for cid, desc, severity in defaults:
            self.constraints[cid] = OperatorConstraint(
                constraint_id=cid,
                constraint_type=cid,
                description=desc,
                severity=severity,
            )

    def update_constraint(self, constraint_type: str, severity: float, context: str = "") -> None:
        """Update a constraint's severity based on observation."""
        if constraint_type in self.constraints:
            c = self.constraints[constraint_type]
            c.severity = max(0.0, min(1.0, severity))
            c.record_observation()
        else:
            self.constraints[constraint_type] = OperatorConstraint(
                constraint_id=constraint_type,
                constraint_type=constraint_type,
                description=context or constraint_type,
                severity=severity,
            )

    def get_active_constraints(self) -> list[OperatorConstraint]:
        """Get all currently active constraints."""
        return sorted(
            [c for c in self.constraints.values() if c.is_active],
            key=lambda c: c.severity,
            reverse=True,
        )

    def get_capacity_estimate(self) -> float:
        """
        Estimate the operator's current capacity (0-1).
        Higher = more capacity available.
        """
        if not self.constraints:
            return 1.0

        # Capacity is inversely related to constraint severity
        total_severity = sum(c.severity for c in self.constraints.values() if c.is_active)
        avg_severity = total_severity / len([c for c in self.constraints.values() if c.is_active])
        return max(0.0, 1.0 - avg_severity)

    def should_reduce_load(self) -> bool:
        """Should the system reduce its demands on the operator?"""
        return self.get_capacity_estimate() < 0.3

    @property
    def stats(self) -> dict:
        active = sum(1 for c in self.constraints.values() if c.is_active)
        return {
            "total_constraints": len(self.constraints),
            "active_constraints": active,
            "avg_severity": round(
                sum(c.severity for c in self.constraints.values() if c.is_active) / max(active, 1), 4
            ),
            "capacity_estimate": round(self.get_capacity_estimate(), 4),
        }
