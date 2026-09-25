"""Book 4 redundancy assessments independent from Book 2 claim states."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance
from .temporal import Timestamp, UnknownBound


class RedundancyState(str, Enum):
    CORRELATED_REDUNDANCY = "CORRELATED_REDUNDANCY"
    INDEPENDENT_REDUNDANCY = "INDEPENDENT_REDUNDANCY"
    UNKNOWN = "UNKNOWN"


class ActivationMode(str, Enum):
    DECLARED = "DECLARED"
    DEPLOYED = "DEPLOYED"
    ACTIVE_FAILOVER = "ACTIVE_FAILOVER"
    MANUAL_FAILOVER = "MANUAL_FAILOVER"


class RedundancyAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    redundancy_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    function: str = Field(min_length=1)
    provider_refs: tuple[str, ...] = Field(min_length=2)
    activation_mode: ActivationMode
    shared_upstreams: tuple[str, ...] = ()
    failure_domain_refs: tuple[str, ...] = ()
    independence_dimensions: tuple[str, ...] = ()
    positive_independence_evidence_refs: tuple[str, ...] = ()
    state: RedundancyState
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _state_evidence(self) -> "RedundancyAssessment":
        if len(set(self.provider_refs)) != len(self.provider_refs):
            raise ValueError("redundancy providers must be distinct")
        if self.state is RedundancyState.INDEPENDENT_REDUNDANCY:
            if not self.positive_independence_evidence_refs:
                raise ValueError("INDEPENDENT_REDUNDANCY requires positive evidence")
            if self.shared_upstreams or self.failure_domain_refs:
                raise ValueError("independent redundancy cannot retain correlated dependencies")
        if self.state is RedundancyState.CORRELATED_REDUNDANCY:
            if not (self.shared_upstreams or self.failure_domain_refs):
                raise ValueError("CORRELATED_REDUNDANCY requires a named correlation")
        return self


class RedundancyBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._records: dict[str, RedundancyAssessment] = {}

    def add(self, assessment: RedundancyAssessment) -> RedundancyAssessment:
        if assessment.redundancy_id in self._records:
            raise ValueError("redundancy IDs are immutable and unique")
        self.provenance.validate_refs(assessment.book2_claim_refs)
        self._records[assessment.redundancy_id] = assessment
        return assessment

    def all_records(self) -> tuple[RedundancyAssessment, ...]:
        return tuple(self._records.values())


__all__ = [
    "ActivationMode",
    "RedundancyAssessment",
    "RedundancyBook",
    "RedundancyState",
]
