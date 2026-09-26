"""Book 4 failure domains with mechanism-first, fail-closed classification."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance, Book4ProvenanceError
from .temporal import Timestamp, UnknownBound

FAILURE_MECHANISM_QUALIFIER = "FAILURE_MECHANISM"
POSITIVE_INDEPENDENCE_QUALIFIER = "POSITIVE_INDEPENDENCE"


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
    mechanism_claim_refs: tuple[str, ...] = Field(min_length=1)
    mechanism_evidence_refs: tuple[str, ...] = ()
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
    positive_independence_claim_refs: tuple[str, ...]
    reason: str


class IndependenceClaimBinding(BaseModel):
    """Which exact failure-domain pair a canonical independence claim supports.

    The canonical Book 2 claim remains the only authority; this binding merely
    establishes which exact left/right comparison that claim supports, so an
    independence claim for one pair can never classify a different pair.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_ref: str = Field(min_length=1)
    left_domain_ref: str = Field(min_length=1)
    right_domain_ref: str = Field(min_length=1)
    left_system_ref: str = Field(min_length=1)
    right_system_ref: str = Field(min_length=1)
    correlation_scope: str = Field(min_length=1)


class FailureDomainBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._domains: dict[str, FailureDomain] = {}

    def add(self, domain: FailureDomain) -> FailureDomain:
        if domain.domain_id in self._domains:
            raise ValueError("failure domain IDs are immutable and unique")
        self.provenance.validate_refs(domain.book2_claim_refs)
        for claim_ref in domain.mechanism_claim_refs:
            self.provenance.resolve_qualifier_claim(
                claim_ref, qualifier=FAILURE_MECHANISM_QUALIFIER
            )
        self.provenance.require_claim_set_closure(
            domain.mechanism_claim_refs,
            domain.book2_claim_refs,
            nested_role="mechanism",
            record_kind="failure domain",
        )
        self._domains[domain.domain_id] = domain
        return domain

    def require(self, domain_id: str) -> FailureDomain:
        return self._domains[domain_id]

    def classify(
        self,
        left: FailureDomain,
        right: FailureDomain,
        *,
        positive_independence_claim_refs: tuple[str, ...] = (),
        independence_bindings: tuple[IndependenceClaimBinding, ...] = (),
    ) -> FailureDomainAssessment:
        subject = left.affected_system_refs[0]
        obj = right.affected_system_refs[0]
        if left.domain_id == right.domain_id:
            return FailureDomainAssessment(
                subject_ref=subject,
                object_ref=obj,
                classification=FailureDomainClassification.SHARED_FAILURE_DOMAIN,
                positive_independence_claim_refs=(),
                reason="same mechanism-backed failure-domain identity",
            )
        shared_mechanism_claims = set(left.mechanism_claim_refs) & set(
            right.mechanism_claim_refs
        )
        if shared_mechanism_claims:
            return FailureDomainAssessment(
                subject_ref=subject,
                object_ref=obj,
                classification=FailureDomainClassification.SHARED_FAILURE_DOMAIN,
                positive_independence_claim_refs=(),
                reason="canonical mechanism support identifies a shared failure mode",
            )
        independence_refs: tuple[str, ...] = ()
        independence_reason = ""
        if positive_independence_claim_refs and not independence_bindings:
            raise Book4ProvenanceError(
                "canonical POSITIVE_INDEPENDENCE claims require explicit pair-scoped "
                "IndependenceClaimBinding support"
            )
        if independence_bindings:
            bound_refs = {binding.claim_ref for binding in independence_bindings}
            if bound_refs != set(positive_independence_claim_refs):
                independence_reason = (
                    "independence bindings must cover exactly the declared "
                    "positive_independence_claim_refs"
                )
            else:
                left_system = left.affected_system_refs[0]
                right_system = right.affected_system_refs[0]
                for binding in independence_bindings:
                    try:
                        claim = self.provenance.resolve_qualifier_claim(
                            binding.claim_ref,
                            qualifier=POSITIVE_INDEPENDENCE_QUALIFIER,
                        )
                    except ValueError as exc:
                        independence_reason = f"independence support rejected: {exc}"
                        break
                    proposition = claim.proposition
                    if (
                        proposition.subject_refs
                        and left_system not in proposition.subject_refs
                    ) or (
                        proposition.object_ref
                        and proposition.object_ref != right_system
                    ):
                        independence_reason = (
                            f"independence claim {binding.claim_ref} does not bind "
                            "the assessed left/right failure domains"
                        )
                        break
                    if (
                        binding.left_domain_ref != left.domain_id
                        or binding.right_domain_ref != right.domain_id
                        or binding.left_system_ref != left_system
                        or binding.right_system_ref != right_system
                        or binding.correlation_scope != left.correlation_scope
                        or binding.correlation_scope != right.correlation_scope
                    ):
                        independence_reason = (
                            "independence claim is not scoped to the assessed "
                            "left/right failure domains"
                        )
                        break
                if not independence_reason:
                    independence_refs = tuple(
                        dict.fromkeys(
                            binding.claim_ref for binding in independence_bindings
                        )
                    )
                    return FailureDomainAssessment(
                        subject_ref=subject,
                        object_ref=obj,
                        classification=FailureDomainClassification.INDEPENDENT,
                        positive_independence_claim_refs=independence_refs,
                        reason="canonical positive independence support bound to the exact assessed pair",
                    )
        identity_overlap = bool(
            (set(left.provider_refs) & set(right.provider_refs))
            or (set(left.operator_refs) & set(right.operator_refs))
            or (set(left.owner_refs) & set(right.owner_refs))
            or (set(left.protocol_refs) & set(right.protocol_refs))
        )
        if independence_reason:
            return FailureDomainAssessment(
                subject_ref=subject,
                object_ref=obj,
                classification=FailureDomainClassification.UNKNOWN,
                positive_independence_claim_refs=(),
                reason=independence_reason,
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
            subject_ref=subject,
            object_ref=obj,
            classification=classification,
            positive_independence_claim_refs=(),
            reason=reason,
        )


__all__ = [
    "FAILURE_MECHANISM_QUALIFIER",
    "FailureDomain",
    "FailureDomainAssessment",
    "FailureDomainBook",
    "FailureDomainClassification",
    "FailureDomainType",
    "IndependenceClaimBinding",
    "POSITIVE_INDEPENDENCE_QUALIFIER",
]
