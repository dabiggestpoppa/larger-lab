"""Book 4 direct dependency records and function-scoped runtime classification."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture_relations import ArchitectureRelationType
from .dependency_provenance import Book4Provenance
from .relationships import EdgeType
from .temporal import Timestamp, UnknownBound


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
        if self.relation_basis is EdgeType.DEPENDS_ON:
            if self.runtime_scope is RuntimeScope.HARD_RUNTIME:
                raise ValueError(
                    "DEPENDS_ON alone cannot establish HARD_RUNTIME; use HardRuntimeGate"
                )
        return self


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
    runtime_scope_hint: RuntimeScope = RuntimeScope.UNKNOWN
    escape_hatch_evidenced: bool = False

    @model_validator(mode="after")
    def _identity(self) -> "HardRuntimeEvidence":
        if self.consumer_ref == self.provider_ref:
            raise ValueError("consumer and provider identities must differ")
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
        self.provenance.validate_refs(evidence.book2_claim_refs)
        reasons: list[str] = []
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
        if not evidence.source_snapshot_refs:
            reasons.append("source snapshot evidence is missing")
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
        self._records[record.dependency_id] = record
        return record

    def require(self, dependency_id: str) -> DependencyRecord:
        return self._records[dependency_id]

    def all_records(self) -> tuple[DependencyRecord, ...]:
        return tuple(self._records.values())


__all__ = [
    "DependencyBook",
    "DependencyClass",
    "DependencyRecord",
    "DependencyStrengthDescriptor",
    "DependencyStrengthState",
    "FallbackState",
    "HardRuntimeEvidence",
    "HardRuntimeGate",
    "RuntimeAssessment",
    "RuntimeScope",
]
