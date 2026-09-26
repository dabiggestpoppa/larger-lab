"""Book 4 direct dependency records and function-scoped runtime classification."""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture_relations import ArchitectureRelationType
from .book4_boundary import (
    BOOK4_DEPENDENCY_RELATION_ALLOWLIST,
    BOOK5_ECONOMIC_RELATIONS,
    Book4RelationSupportPolicy,
)
from .dependency_provenance import Book4Provenance
from .relationships import EdgeType
from .temporal import Timestamp, UnknownBound


class HardRuntimeFact(str, Enum):
    """Fact-specific Book 4 support classes for the D4-6 contract."""

    IDENTITY = "IDENTITY"
    DEPLOYED_CONFIGURATION = "DEPLOYED_CONFIGURATION"
    RUNTIME_NECESSITY = "RUNTIME_NECESSITY"
    FAILURE_CONSEQUENCE = "FAILURE_CONSEQUENCE"
    NO_ACTIVE_EQUIVALENT_FALLBACK = "NO_ACTIVE_EQUIVALENT_FALLBACK"
    VALID_TIME = "VALID_TIME"


REQUIRED_HARD_RUNTIME_FACTS: Final[frozenset[HardRuntimeFact]] = frozenset(HardRuntimeFact)


class DependencyClass(str, Enum):
    DIRECT_RUNTIME = "DIRECT_RUNTIME"
    BUILD_TIME = "BUILD_TIME"
    OPTIONAL_INTEGRATION = "OPTIONAL_INTEGRATION"
    FALLBACK_SERVICE = "FALLBACK_SERVICE"
    UNKNOWN = "UNKNOWN"


class DependencyStrengthState(str, Enum):
    REQUIRED = "REQUIRED"
    PRIMARY = "PRIMARY"
    FALLBACK = "FALLBACK"
    OPTIONAL = "OPTIONAL"
    LEGACY = "LEGACY"
    DEPRECATED = "DEPRECATED"
    UNKNOWN = "UNKNOWN"


class RuntimeScope(str, Enum):
    HARD_RUNTIME = "HARD_RUNTIME"
    SOFT_RUNTIME = "SOFT_RUNTIME"
    BUILD_TIME = "BUILD_TIME"
    CONTROL_PLANE = "CONTROL_PLANE"
    OUT_OF_BAND = "OUT_OF_BAND"
    UNKNOWN = "UNKNOWN"


class FallbackState(str, Enum):
    NONE = "NONE"
    ACTIVE_EQUIVALENT = "ACTIVE_EQUIVALENT"
    DECLARED_UNVERIFIED = "DECLARED_UNVERIFIED"
    INACTIVE = "INACTIVE"


class DependencyStrengthDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: DependencyStrengthState
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class DependencyRecord(BaseModel):
    """A direct dependency only; transitive facts belong to DependencyPath."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dependency_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    relation_basis: EdgeType | ArchitectureRelationType
    dependency_class: DependencyClass
    runtime_scope: RuntimeScope
    strength_descriptor: DependencyStrengthDescriptor
    mechanism: str = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    source_snapshot_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _rules(self) -> "DependencyRecord":
        if self.subject_ref == self.object_ref:
            raise ValueError("direct dependency subject and object must differ")
        if self.relation_basis is EdgeType.BUILT_WITH and self.runtime_scope is RuntimeScope.HARD_RUNTIME:
            raise ValueError("BUILT_WITH cannot establish HARD_RUNTIME")
        if self.relation_basis is EdgeType.INTEGRATES_WITH:
            if self.strength_descriptor.state is DependencyStrengthState.REQUIRED:
                raise ValueError("INTEGRATES_WITH does not establish REQUIRED dependency")
        if self.relation_basis not in BOOK4_DEPENDENCY_RELATION_ALLOWLIST:
            Book4RelationSupportPolicy.require_supported(self.relation_basis)
        if self.relation_basis is EdgeType.DEPENDS_ON:
            if self.runtime_scope is RuntimeScope.HARD_RUNTIME:
                raise ValueError(
                    "DEPENDS_ON alone cannot establish HARD_RUNTIME; use HardRuntimeGate"
                )
        return self


class HardRuntimeFactBinding(BaseModel):
    """Canonical Book 2 claims that support exactly one D4-6 fact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fact: HardRuntimeFact
    claim_refs: tuple[str, ...] = Field(min_length=1)


class HardRuntimeFactContextBinding(HardRuntimeFactBinding):
    """Fact binding sealed to the exact consumer/provider/function/scope.

    The canonical Book 2 claim remains the only authority; this binding
    records which exact assessment context the claim is being interpreted
    for so a claim about one system can never support another.
    """

    consumer_ref: str = Field(min_length=1)
    provider_ref: str = Field(min_length=1)
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)


class HardRuntimeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    consumer_ref: str = Field(min_length=1)
    provider_ref: str = Field(min_length=1)
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    deployed_configuration_evidenced: bool
    runtime_necessity_evidenced: bool
    removal_makes_function_unavailable: bool
    fallback_state: FallbackState
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    source_snapshot_refs: tuple[str, ...] = Field(min_length=1)
    fact_bindings: tuple[HardRuntimeFactBinding, ...] = ()
    runtime_scope_hint: RuntimeScope = RuntimeScope.UNKNOWN
    escape_hatch_evidenced: bool = False

    @model_validator(mode="after")
    def _identity(self) -> "HardRuntimeEvidence":
        if self.consumer_ref == self.provider_ref:
            raise ValueError("consumer and provider identities must differ")
        declared = {binding.fact for binding in self.fact_bindings}
        if len(declared) != len(self.fact_bindings):
            raise ValueError("each HARD_RUNTIME fact may be bound only once")
        if self.fact_bindings and not all(
            isinstance(binding, HardRuntimeFactContextBinding)
            for binding in self.fact_bindings
        ):
            raise ValueError(
                "HARD_RUNTIME fact bindings must be context-bound "
                "(consumer, provider, function, scope)"
            )
        for binding in self.fact_bindings:
            if not isinstance(binding, HardRuntimeFactContextBinding):
                continue
            if (
                binding.consumer_ref != self.consumer_ref
                or binding.provider_ref != self.provider_ref
                or binding.function != self.function
                or binding.scope != self.scope
            ):
                raise ValueError(
                    "HARD_RUNTIME fact binding context must equal the assessed "
                    "consumer, provider, function, and scope"
                )
        return self


class RuntimeAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime_scope: RuntimeScope
    function: str
    scope: str
    reasons: tuple[str, ...]
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)


class HardRuntimeGate:
    """D4-6: all eight conditions are necessary; unknown fallback blocks promotion."""

    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance

    def classify(self, evidence: HardRuntimeEvidence) -> RuntimeAssessment:
        reasons: list[str] = []
        try:
            self.provenance.validate_snapshot_lineage(
                evidence.book2_claim_refs, evidence.source_snapshot_refs
            )
        except ValueError as exc:
            reasons.append(f"snapshot lineage unsupported: {exc}")
        # Decision-point re-verification.  Pydantic model_copy skips every
        # model validator, so constructor-time context checks cannot be
        # trusted here: re-derive them from the current record state.  Raw
        # (unvalidated) binding objects must fail closed, never crash.
        if evidence.fact_bindings and not all(
            isinstance(binding, HardRuntimeFactContextBinding)
            for binding in evidence.fact_bindings
        ):
            reasons.append(
                "HARD_RUNTIME fact bindings must be context-bound "
                "(consumer, provider, function, scope)"
            )
        typed_bindings = tuple(
            binding
            for binding in evidence.fact_bindings
            if isinstance(binding, HardRuntimeFactContextBinding)
        )
        declared_facts = {binding.fact for binding in typed_bindings}
        if len(declared_facts) != len(typed_bindings):
            reasons.append("each HARD_RUNTIME fact may be bound only once")
        for binding in evidence.fact_bindings:
            if not isinstance(binding, HardRuntimeFactContextBinding):
                continue
            if (
                binding.consumer_ref != evidence.consumer_ref
                or binding.provider_ref != evidence.provider_ref
                or binding.function != evidence.function
                or binding.scope != evidence.scope
            ):
                reasons.append(
                    "HARD_RUNTIME fact binding context must equal the assessed "
                    "consumer, provider, function, and scope"
                )
        bound_facts: set[HardRuntimeFact] = set()
        binding_claim_refs: set[str] = set()
        for binding in typed_bindings:
            bound_facts.add(binding.fact)
            for claim_ref in binding.claim_refs:
                binding_claim_refs.add(claim_ref)
                try:
                    claim = self.provenance.resolve_qualifier_claim(
                        claim_ref, qualifier=binding.fact.value
                    )
                except ValueError as exc:
                    reasons.append(f"fact {binding.fact.value} unsupported: {exc}")
                    continue
                proposition = claim.proposition
                if (
                    proposition.subject_refs
                    and binding.consumer_ref not in proposition.subject_refs
                ):
                    reasons.append(
                        f"fact {binding.fact.value} claim {claim_ref} does not "
                        "bind the assessed consumer"
                    )
                if (
                    proposition.object_ref
                    and proposition.object_ref != binding.provider_ref
                ):
                    reasons.append(
                        f"fact {binding.fact.value} claim {claim_ref} does not "
                        "bind the assessed provider"
                    )
        outside = sorted(binding_claim_refs - set(evidence.book2_claim_refs))
        if outside:
            reasons.append(
                "decision-driving fact claims outside the declared book2_claim_refs "
                f"provenance set: {outside}"
            )
        for missing in sorted(REQUIRED_HARD_RUNTIME_FACTS - bound_facts, key=lambda f: f.value):
            reasons.append(f"missing fact-specific support for {missing.value}")
        if evidence.escape_hatch_evidenced:
            reasons.append("escape hatch changes the scoped liveness consequence")
        if evidence.runtime_scope_hint in {
            RuntimeScope.SOFT_RUNTIME,
            RuntimeScope.BUILD_TIME,
            RuntimeScope.CONTROL_PLANE,
            RuntimeScope.OUT_OF_BAND,
        }:
            reasons.append(
                f"explicit non-hard runtime scope is {evidence.runtime_scope_hint.value}"
            )
        if not evidence.deployed_configuration_evidenced:
            reasons.append("missing deployed or operative configuration evidence")
        if not evidence.runtime_necessity_evidenced:
            reasons.append("runtime necessity is not established")
        if not evidence.removal_makes_function_unavailable:
            reasons.append("failure/removal consequence is not established")
        if evidence.fallback_state is FallbackState.ACTIVE_EQUIVALENT:
            reasons.append("active equivalent fallback preserves the function")
        if evidence.fallback_state is FallbackState.DECLARED_UNVERIFIED:
            reasons.append("fallback state is UNKNOWN; promotion is blocked")
        if isinstance(evidence.valid_time, UnknownBound):
            reasons.append("valid time is not established")
        if evidence.fallback_state is FallbackState.NONE and not any(
            binding.fact is HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK
            for binding in typed_bindings
        ):
            reasons.append("absence of an active fallback is asserted without canonical proof")
        scope = (
            evidence.runtime_scope_hint
            if evidence.runtime_scope_hint
            in {
                RuntimeScope.SOFT_RUNTIME,
                RuntimeScope.BUILD_TIME,
                RuntimeScope.CONTROL_PLANE,
                RuntimeScope.OUT_OF_BAND,
            }
            else RuntimeScope.HARD_RUNTIME
            if not reasons
            else RuntimeScope.UNKNOWN
        )
        return RuntimeAssessment(
            runtime_scope=scope,
            function=evidence.function,
            scope=evidence.scope,
            reasons=tuple(reasons) or ("all eight D4-6 conditions established",),
            book2_claim_refs=evidence.book2_claim_refs,
        )


class DependencyBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._records: dict[str, DependencyRecord] = {}

    def add(self, record: DependencyRecord) -> DependencyRecord:
        if record.dependency_id in self._records:
            raise ValueError("dependency IDs are immutable and unique")
        self.provenance.validate_refs(record.book2_claim_refs)
        self.provenance.validate_refs(record.strength_descriptor.book2_claim_refs)
        self.provenance.validate_snapshot_lineage(
            record.book2_claim_refs, record.source_snapshot_refs
        )
        self._records[record.dependency_id] = record
        return record

    def require(self, dependency_id: str) -> DependencyRecord:
        return self._records[dependency_id]

    def all_records(self) -> tuple[DependencyRecord, ...]:
        return tuple(self._records.values())


__all__ = [
    "BOOK4_DEPENDENCY_RELATION_ALLOWLIST",
    "BOOK5_ECONOMIC_RELATIONS",
    "DependencyBook",
    "DependencyClass",
    "DependencyRecord",
    "DependencyStrengthDescriptor",
    "DependencyStrengthState",
    "FallbackState",
    "HardRuntimeEvidence",
    "HardRuntimeFact",
    "HardRuntimeFactBinding",
    "HardRuntimeFactContextBinding",
    "HardRuntimeGate",
    "REQUIRED_HARD_RUNTIME_FACTS",
    "RuntimeAssessment",
    "RuntimeScope",
]
