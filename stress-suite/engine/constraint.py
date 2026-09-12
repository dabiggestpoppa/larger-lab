"""ConstraintField (A-005 §2.1, PM-RM §4) — versioned machine-readable admissible
state space for an objective.

Extends the base with candidate regimes, anomaly pressure, and stabilize/transform
conditions per the Post-Michels revision. It represents, it does not decide.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base import deterministic_hex


@dataclass
class ConstraintField:
    field_id: str
    schema_version: str = "1.0.0"
    objective: str = ""
    current_state: str = ""
    candidate_regimes: List[str] = field(default_factory=list)
    admissible_transitions: List[str] = field(default_factory=list)
    authority_boundaries: List[str] = field(default_factory=list)
    budgets: Dict[str, str] = field(default_factory=dict)
    required_evidence: List[str] = field(default_factory=list)
    prohibitions: List[str] = field(default_factory=list)
    negative_knowledge: List[str] = field(default_factory=list)
    unresolved_anomalies: List[str] = field(default_factory=list)
    uncertainty: str = "LOW"
    known_failure_surfaces: List[str] = field(default_factory=list)
    reversibility: str = "HIGH"
    state_age: str = "FRESH"
    anomaly_pressure: str = "LOW"
    stabilize_conditions: List[str] = field(default_factory=list)
    transform_conditions: List[str] = field(default_factory=list)
    seq: int = 0

    @classmethod
    def make(cls, seq, objective, **kw):
        return cls(
            field_id=deterministic_hex("constraint_field", seq, objective),
            objective=objective,
            seq=seq,
            **kw,
        )

    @property
    def resolution_should_shrink(self) -> bool:
        """A-005: as valid constraints accumulate, the admissible set shrinks."""
        return True