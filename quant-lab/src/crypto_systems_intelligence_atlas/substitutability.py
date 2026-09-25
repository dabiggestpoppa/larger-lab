"""Book 4 directional and context-scoped substitutability assessments."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance
from .temporal import Timestamp, UnknownBound


class ChangeClass(str, Enum):
    DROP_IN = "DROP_IN"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    CONTRACT_CHANGE = "CONTRACT_CHANGE"
    PROTOCOL_UPGRADE = "PROTOCOL_UPGRADE"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    ECONOMICALLY_INFEASIBLE = "ECONOMICALLY_INFEASIBLE"
    NO_KNOWN_SUBSTITUTE = "NO_KNOWN_SUBSTITUTE"
    UNKNOWN = "UNKNOWN"


class SubstitutabilityDirection(str, Enum):
    INCUMBENT_TO_CANDIDATE = "INCUMBENT_TO_CANDIDATE"
    CANDIDATE_TO_INCUMBENT = "CANDIDATE_TO_INCUMBENT"


class SubstitutabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=1)
    function: str = Field(min_length=1)
    incumbent_ref: str = Field(min_length=1)
    candidate_ref: str = Field(min_length=1)
    direction: SubstitutabilityDirection
    context: str = Field(min_length=1)
    change_class: ChangeClass
    technical_change: str = Field(min_length=1)
    governance_requirements: tuple[str, ...] = ()
    migration_requirements: tuple[str, ...] = ()
    state_impact: str = Field(min_length=1)
    security_impact: str = Field(min_length=1)
    downtime_risk: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _direction(self) -> "SubstitutabilityAssessment":
        if self.incumbent_ref == self.candidate_ref:
            raise ValueError("incumbent and candidate must differ")
        return self


class SubstitutabilityBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._records: dict[str, SubstitutabilityAssessment] = {}

    def add(self, assessment: SubstitutabilityAssessment) -> SubstitutabilityAssessment:
        if assessment.assessment_id in self._records:
            raise ValueError("substitutability IDs are immutable and unique")
        self.provenance.validate_refs(assessment.book2_claim_refs)
        self._records[assessment.assessment_id] = assessment
        return assessment

    def applies(self, assessment_id: str) -> tuple[str, str]:
        record = self._records[assessment_id]
        return record.incumbent_ref, record.candidate_ref

    def all_records(self) -> tuple[SubstitutabilityAssessment, ...]:
        return tuple(self._records.values())


__all__ = [
    "ChangeClass",
    "SubstitutabilityAssessment",
    "SubstitutabilityBook",
    "SubstitutabilityDirection",
]
