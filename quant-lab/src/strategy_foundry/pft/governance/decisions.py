"""Checkpoint decision records.

Every major checkpoint produces a machine-readable DECISION.json. Status
is derived from evidence, never hardcoded: a false required gate makes the
checkpoint FAIL; blockers make it BLOCKED; otherwise PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

DECISION_FIELDS = (
    "checkpoint_id",
    "program_id",
    "branch",
    "base_sha",
    "commit_sha",
    "status",
    "spec_generation",
    "data_generation",
    "engine_generation",
    "data_truth_pass",
    "math_conformance_pass",
    "causality_pass",
    "protected_data_touched",
    "economic_pnl_computed",
    "optimization_performed",
    "confirmation_consumed",
    "holdout_consumed",
    "production_authorized",
    "human_review_required",
    "next_checkpoint_authorized",
    "blockers",
    "warnings",
)

STATUSES = {"PASS", "FAIL", "BLOCKED", "PENDING"}

BOOLEAN_FIELDS = (
    "data_truth_pass",
    "math_conformance_pass",
    "causality_pass",
    "protected_data_touched",
    "economic_pnl_computed",
    "optimization_performed",
    "confirmation_consumed",
    "holdout_consumed",
    "production_authorized",
    "human_review_required",
    "next_checkpoint_authorized",
)


class DecisionSchemaError(RuntimeError):
    pass


@dataclass
class DecisionRecord:
    checkpoint_id: str
    program_id: str
    branch: str
    base_sha: str
    commit_sha: str
    status: str = "PENDING"
    spec_generation: str = ""
    data_generation: str = ""
    engine_generation: str = ""
    data_truth_pass: bool = False
    math_conformance_pass: bool = False
    causality_pass: bool = False
    protected_data_touched: bool = False
    economic_pnl_computed: bool = False
    optimization_performed: bool = False
    confirmation_consumed: bool = False
    holdout_consumed: bool = False
    production_authorized: bool = False
    human_review_required: bool = True
    next_checkpoint_authorized: bool = False
    blockers: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        errors = []
        for f in DECISION_FIELDS:
            if not hasattr(self, f):
                errors.append(f"missing field {f}")
        for f in BOOLEAN_FIELDS:
            if not isinstance(getattr(self, f), bool):
                errors.append(f"field {f} must be boolean")
        if self.status not in STATUSES:
            errors.append(f"invalid status {self.status!r}; allowed: {sorted(STATUSES)}")
        if not isinstance(self.blockers, list) or not isinstance(self.warnings, list):
            errors.append("blockers and warnings must be lists")
        if errors:
            raise DecisionSchemaError("; ".join(errors))

    def derive_status(self) -> str:
        """Status from evidence: FAIL on any false required gate, BLOCKED when
        blockers exist, otherwise PASS."""
        required_gates = (
            self.data_truth_pass,
            self.math_conformance_pass,
            self.causality_pass,
        )
        if self.blockers:
            return "BLOCKED"
        if not all(required_gates):
            return "FAIL"
        return "PASS"

    def to_dict(self) -> dict:
        return {f: getattr(self, f) for f in DECISION_FIELDS}


def validate_decision_dict(data: dict) -> list:
    """Return a list of schema violations (empty means valid)."""
    errors = []
    if not isinstance(data, dict):
        return ["decision must be a JSON object"]
    for f in DECISION_FIELDS:
        if f not in data:
            errors.append(f"missing required field {f!r}")
    for f in BOOLEAN_FIELDS:
        if f in data and not isinstance(data[f], bool):
            errors.append(f"field {f!r} must be boolean")
    if "status" in data and data["status"] not in STATUSES:
        errors.append(f"invalid status {data['status']!r}")
    if "blockers" in data and not isinstance(data["blockers"], list):
        errors.append("'blockers' must be a list")
    if "warnings" in data and not isinstance(data["warnings"], list):
        errors.append("'warnings' must be a list")
    return errors
