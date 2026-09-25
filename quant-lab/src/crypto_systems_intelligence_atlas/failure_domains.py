"""Book 4 failure domains with mechanism-first, fail-closed classification."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance
from .temporal import Timestamp, UnknownBound


class FailureDomainType(str, Enum):
    PROVIDER = "PROVIDER"
    OPERATOR = "OPERATOR"
    OWNER = "OWNER"
    PROTOCOL = "PROTOCOL"
    CLOUD_BACKEND = "CLOUD_BACKEND"
    SEQUENCER = "SEQUENCER"
    DATA_AVAILABILITY = "DATA_AVAILABILITY"
    VALIDATOR_SET = "VALIDATOR_SET"
    GOVERNANCE = "GOVERNANCE"
    CUSTODY = "CUSTODY"
    RELAYER = "RELAYER"
    INDEXER = "INDEXER"
    UPSTREAM_API = "UPSTREAM_API"
    UNKNOWN = "UNKNOWN"


class FailureDomainClassification(str, Enum):
    SHARED_FAILURE_DOMAIN = "SHARED_FAILURE_DOMAIN"
    PARTIAL_SHARED_DOMAIN = "PARTIAL_SHARED_DOMAIN"
    INDEPENDENT = "INDEPENDENT"
    UNKNOWN = "UNKNOWN"


class FailureDomain(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    domain_id: str = Field(min_length=1)
    domain_type: FailureDomainType
    provider_refs: tuple[str, ...] = ()
    operator_refs: tuple[str, ...] = ()
    owner_refs: tuple[str, ...] = ()
    protocol_refs: tuple[str, ...] = ()
    affected_system_refs: tuple[str, ...] = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    mechanism_evidence_refs: tuple[str, ...] = Field(min_length=1)
    correlation_scope: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _identity_separation(self) -> "FailureDomain":
        groups = (
            self.provider_refs,
            self.operator_refs,
            self.owner_refs,
            self.protocol_refs,
        )
        flattened = [ref for group in groups for ref in group]
        if len(flattened) != len(set(flattened)):
            raise ValueError("provider, operator, owner, and protocol identities must remain distinct")
        return self


class FailureDomainAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_ref: str
    object_ref: str
    classification: FailureDomainClassification
    positive_independence_evidence_refs: tuple[str, ...]
    reason: str


class FailureDomainBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._domains: dict[str, FailureDomain] = {}

    def add(self, domain: FailureDomain) -> FailureDomain:
        if domain.domain_id in self._domains:
            raise ValueError("failure domain IDs are immutable and unique")
        self.provenance.validate_refs(domain.book2_claim_refs)
        self._domains[domain.domain_id] = domain
        return domain

    def require(self, domain_id: str) -> FailureDomain:
        return self._domains[domain_id]

    def classify(
        self,
        left: FailureDomain,
        right: FailureDomain,
        *,
        positive_independence_evidence_refs: tuple[str, ...] = (),
    ) -> FailureDomainAssessment:
        if left.domain_id == right.domain_id:
            return FailureDomainAssessment(
                subject_ref=left.affected_system_refs[0],
                object_ref=right.affected_system_refs[0],
                classification=FailureDomainClassification.SHARED_FAILURE_DOMAIN,
                positive_independence_evidence_refs=(),
                reason="same mechanism-backed failure-domain identity",
            )
        shared_mechanism_evidence = set(left.mechanism_evidence_refs) & set(
            right.mechanism_evidence_refs
        )
        if shared_mechanism_evidence:
            return FailureDomainAssessment(
                subject_ref=left.affected_system_refs[0],
                object_ref=right.affected_system_refs[0],
                classification=FailureDomainClassification.SHARED_FAILURE_DOMAIN,
                positive_independence_evidence_refs=(),
                reason="positive mechanism evidence identifies a shared failure mode",
            )
        if positive_independence_evidence_refs:
            return FailureDomainAssessment(
                subject_ref=left.affected_system_refs[0],
                object_ref=right.affected_system_refs[0],
                classification=FailureDomainClassification.INDEPENDENT,
                positive_independence_evidence_refs=positive_independence_evidence_refs,
                reason="positive independence evidence supplied",
            )
        identity_overlap = bool(
            (set(left.provider_refs) & set(right.provider_refs))
            or (set(left.operator_refs) & set(right.operator_refs))
            or (set(left.owner_refs) & set(right.owner_refs))
            or (set(left.protocol_refs) & set(right.protocol_refs))
        )
        classification = (
            FailureDomainClassification.PARTIAL_SHARED_DOMAIN
            if identity_overlap
            else FailureDomainClassification.UNKNOWN
        )
        reason = (
            "identity overlap is partial correlation evidence, not a complete shared mechanism"
            if identity_overlap
            else "absence of common evidence does not prove independence"
        )
        return FailureDomainAssessment(
            subject_ref=left.affected_system_refs[0],
            object_ref=right.affected_system_refs[0],
            classification=classification,
            positive_independence_evidence_refs=(),
            reason=reason,
        )


__all__ = [
    "FailureDomain",
    "FailureDomainAssessment",
    "FailureDomainBook",
    "FailureDomainClassification",
    "FailureDomainType",
]
