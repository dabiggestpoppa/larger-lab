"""Book 4 redundancy assessments independent from Book 2 claim states."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance, Book4ProvenanceError
from .failure_domains import (
    POSITIVE_INDEPENDENCE_QUALIFIER,
    FailureDomainBook,
    IndependenceClaimBinding,
)
from .temporal import Timestamp, UnknownBound


class RedundancyState(str, Enum):
    CORRELATED_REDUNDANCY = "CORRELATED_REDUNDANCY"
    INDEPENDENT_REDUNDANCY = "INDEPENDENT_REDUNDANCY"
    UNKNOWN = "UNKNOWN"


def normalized_provider_pair(left: str, right: str) -> tuple[str, str]:
    """Redundancy independence is set-like: (A, B) and (B, A) are one pair.

    Deterministic normalization so pair coverage does not depend on the
    assessment's ``provider_refs`` tuple ordering.
    """

    return (left, right) if left <= right else (right, left)


def required_provider_pairs(provider_refs: tuple[str, ...]) -> set[tuple[str, str]]:
    """All unordered 2-combinations of the assessed providers.

    Set-level independence requires complete pairwise evidence: N providers
    need N*(N-1)/2 pair bindings.  Transitivity is NOT inferred — A independent
    of B and B independent of C does not imply A independent of C.
    """

    return {
        normalized_provider_pair(left, right)
        for index, left in enumerate(provider_refs)
        for right in provider_refs[index + 1 :]
    }


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
    positive_independence_claim_refs: tuple[str, ...] = ()
    independence_bindings: tuple[IndependenceClaimBinding, ...] = ()
    state: RedundancyState
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _state_evidence(self) -> "RedundancyAssessment":
        if len(set(self.provider_refs)) != len(self.provider_refs):
            raise ValueError("redundancy providers must be distinct")
        if self.state is RedundancyState.INDEPENDENT_REDUNDANCY:
            if not self.positive_independence_claim_refs:
                raise ValueError("INDEPENDENT_REDUNDANCY requires positive evidence")
            if self.shared_upstreams or self.failure_domain_refs:
                raise ValueError("independent redundancy cannot retain correlated dependencies")
        if self.state is RedundancyState.CORRELATED_REDUNDANCY:
            if not (self.shared_upstreams or self.failure_domain_refs):
                raise ValueError("CORRELATED_REDUNDANCY requires a named correlation")
        if self.independence_bindings:
            bound = {binding.claim_ref for binding in self.independence_bindings}
            if bound != set(self.positive_independence_claim_refs):
                raise ValueError(
                    "independence bindings must cover exactly the declared "
                    "positive_independence_claim_refs"
                )
        if self.positive_independence_claim_refs and not self.independence_bindings:
            raise ValueError(
                "redundancy independence claims require explicit provider/function/scope "
                "IndependenceClaimBinding support"
            )
        return self

    def _binding_matches(self, binding: IndependenceClaimBinding) -> bool:
        """A binding must sit entirely inside THIS assessment's provider set.

        No first-pair assumption: any ordered pair of distinct assessed
        providers is representable, and external providers never match.
        """

        return (
            binding.left_system_ref == self.subject_ref
            and binding.right_system_ref == self.subject_ref
            and binding.left_domain_ref in self.provider_refs
            and binding.right_domain_ref in self.provider_refs
            and binding.left_domain_ref != binding.right_domain_ref
            and binding.correlation_scope == self.function
        )


class RedundancyBook:
    """Redundancy cannot duplicate failure-domain state or assert it loosely."""

    def __init__(self, provenance: Book4Provenance, failure_domains: FailureDomainBook) -> None:
        if failure_domains is None:
            raise ValueError("RedundancyBook requires a FailureDomainBook resolver")
        self.provenance = provenance
        self.failure_domains = failure_domains
        self._records: dict[str, RedundancyAssessment] = {}

    def _require_failure_domain(self, domain_id: str) -> None:
        try:
            self.failure_domains.require(domain_id)
        except KeyError as exc:
            raise Book4ProvenanceError(
                f"redundancy references unknown failure domain {domain_id}"
            ) from exc

    def add(self, assessment: RedundancyAssessment) -> RedundancyAssessment:
        if assessment.redundancy_id in self._records:
            raise ValueError("redundancy IDs are immutable and unique")
        self.provenance.validate_refs(assessment.book2_claim_refs)
        for domain_id in assessment.failure_domain_refs:
            self._require_failure_domain(domain_id)
        for claim_ref in assessment.positive_independence_claim_refs:
            self.provenance.resolve_qualifier_claim(
                claim_ref, qualifier=POSITIVE_INDEPENDENCE_QUALIFIER
            )
        self.provenance.require_claim_set_closure(
            assessment.positive_independence_claim_refs,
            assessment.book2_claim_refs,
            nested_role="positive independence",
            record_kind="redundancy assessment",
        )
        # Decision-point re-verification.  Pydantic model_copy skips every
        # model validator, so both coverages are re-derived here from the
        # record's CURRENT state.
        #
        # Typed-binding gate first: raw or untyped bindings (smuggled past the
        # constructor via model_copy) must fail closed, never crash.
        for binding in assessment.independence_bindings:
            if not isinstance(binding, IndependenceClaimBinding):
                raise Book4ProvenanceError(
                    "independence bindings must be typed IndependenceClaimBinding "
                    "records; untyped binding payloads are rejected"
                )
        # CLAIM COVERAGE: binding claim refs must exactly cover the declared
        # positive_independence_claim_refs (unchanged R2 doctrine).
        bound_refs = {
            binding.claim_ref for binding in assessment.independence_bindings
        }
        if assessment.positive_independence_claim_refs and bound_refs != set(
            assessment.positive_independence_claim_refs
        ):
            raise Book4ProvenanceError(
                "independence bindings must cover exactly the declared "
                "positive_independence_claim_refs"
            )
        # PROVIDER-PAIR COVERAGE: every unordered provider pair needs its own
        # pair-scoped binding.  No consecutive-pair shortcut, no transitive
        # inference, no substitution by duplicates.
        required_pairs = required_provider_pairs(assessment.provider_refs)
        bound_pairs: set[tuple[str, str]] = set()
        for binding in assessment.independence_bindings:
            if binding.left_domain_ref == binding.right_domain_ref:
                raise Book4ProvenanceError(
                    f"independence binding {binding.claim_ref} binds a provider to "
                    "itself; redundancy independence requires distinct providers"
                )
            if (
                binding.left_domain_ref not in assessment.provider_refs
                or binding.right_domain_ref not in assessment.provider_refs
            ):
                raise Book4ProvenanceError(
                    f"independence binding {binding.claim_ref} references a provider "
                    "outside the assessed provider set"
                )
            if not assessment._binding_matches(binding):
                raise Book4ProvenanceError(
                    f"independence binding {binding.claim_ref} is not scoped to the "
                    "assessed subject, provider pair, and function"
                )
            normalized = normalized_provider_pair(
                binding.left_domain_ref, binding.right_domain_ref
            )
            if normalized in bound_pairs:
                raise Book4ProvenanceError(
                    f"provider pair {normalized} is covered by more than one "
                    "independence binding; duplicates do not substitute for "
                    "complete pair coverage"
                )
            bound_pairs.add(normalized)
        if bound_refs:
            missing = sorted(required_pairs - bound_pairs)
            if missing:
                raise Book4ProvenanceError(
                    "provider-pair independence evidence is incomplete: missing "
                    f"pair-scoped bindings for {missing}. Set-level independence "
                    f"requires complete unordered pairwise coverage "
                    f"({len(required_pairs)} pairs for {len(assessment.provider_refs)} "
                    "providers); transitive inference is not accepted"
                )
        self._records[assessment.redundancy_id] = assessment
        return assessment

    def all_records(self) -> tuple[RedundancyAssessment, ...]:
        return tuple(self._records.values())


__all__ = [
    "ActivationMode",
    "RedundancyAssessment",
    "RedundancyBook",
    "RedundancyState",
    "normalized_provider_pair",
    "required_provider_pairs",
]
