"""TransformationWindowSpec (A-010 §15). A transformation window must be a
versioned, bounded, admissibility-gated object that may also conclude NO_CHANGE
or remain UNRESOLVED — neither is a failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

from .base import deterministic_hex


@dataclass
class TransformationWindowSpec:
    window_id: str
    schema_version: str = "1.0.0"
    challenged_objects: List[str] = field(default_factory=list)
    scope_ceiling: str = "L3"
    allowed_mutation_surface: List[str] = field(default_factory=list)
    competing_candidate_models: List[str] = field(default_factory=list)
    discriminating_tests: List[str] = field(default_factory=list)
    evidence_budget: str = ""
    compute_time_budget: str = ""
    independence_requirements: List[str] = field(default_factory=list)
    rollback_point: str = ""
    operator_hold_points: List[str] = field(default_factory=list)
    reconsolidation_criteria: List[str] = field(default_factory=list)
    unresolved_outcomes_permitted: bool = True
    evaluation_contract_id: str = ""        # frozen contract governing this window
    status: str = "OPEN"

    @classmethod
    def make(cls, seq, challenged_objects=None, scope_ceiling="L3", evaluation_contract_id=""):
        return cls(
            window_id=deterministic_hex("windowing", seq, scope_ceiling, *challenged_objects),
            challenged_objects=list(challenged_objects or []),
            scope_ceiling=scope_ceiling,
            evaluation_contract_id=evaluation_contract_id,
        )