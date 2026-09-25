"""CSIA Book 3 — namespaced temporal architecture-family registries.

The registry is deliberately open inside operator-admitted namespaces.  It is
not a universal architecture enum: values are definitions admitted through
canonical Book 2 claims, and every value remains queryable after supersession.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .claims import ClaimState, ClaimStore, can_promote_to_graph
from .temporal import Timestamp, UnknownBound, normalize_utc

RATIFIED_ARCHITECTURE_FAMILIES: Final = (
    "EXECUTION_MODEL",
    "STATE_MODEL",
    "CONSENSUS_MODEL",
    "FINALITY_MODEL",
    "DA_MODEL",
    "SETTLEMENT_MODEL",
    "VALIDATOR_MODEL",
    "PARTICIPANT_MODEL",
    "GOVERNANCE_MODEL",
    "FEE_MODEL",
    "UPGRADE_MODEL",
    "INTEROP_MODEL",
    "DEPLOYMENT_MODEL",
    "SEQUENCING_MODEL",
    "SECURITY_MODEL",
)
"""The fifteen Book 3 registry namespaces ratified by BLOC_3A–3Q."""

_SLUG = re.compile(r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*$")


class RegistryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    HISTORICAL = "HISTORICAL"
    UNKNOWN = "UNKNOWN"


class AdmissionOutcome(str, Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class RegistryNamespace(BaseModel):
    """Operator-admitted namespace and its semantic contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    operator_admission_ref: str | None = None
    ratified: bool = False

    @model_validator(mode="after")
    def _namespace_shape(self) -> "RegistryNamespace":
        if not _SLUG.fullmatch(self.namespace):
            raise ValueError("namespace must be a stable alphanumeric slug")
        if not self.ratified and not self.operator_admission_ref:
            raise ValueError("new namespace requires operator admission")
        return self


class RegistryValue(BaseModel):
    """Immutable architecture-family definition with bitemporal validity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_id: str = Field(min_length=1)
    namespace: str = Field(min_length=1)
    family: str = Field(min_length=1)
    name: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    semantic_key: str = Field(min_length=1)
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    source_claim_refs: tuple[str, ...] = Field(min_length=1)
    status: RegistryStatus = RegistryStatus.ACTIVE
    supersedes: str | None = None
    superseded_by: str | None = None

    @model_validator(mode="after")
    def _value_shape(self) -> "RegistryValue":
        if not _SLUG.fullmatch(self.namespace):
            raise ValueError("invalid namespace")
        if self.family != self.namespace:
            raise ValueError("family must equal its admitted namespace")
        if not self.name.strip() or not self.definition.strip():
            raise ValueError("name and definition are required")
        if not self.semantic_key.strip():
            raise ValueError("semantic_key is required")
        start = _known_start(self.valid_from)
        end = _known_end(self.valid_to)
        if start is not None and end is not None and start > end:
            raise ValueError("valid_from cannot exceed valid_to")
        if self.status is RegistryStatus.SUPERSEDED and not self.superseded_by:
            raise ValueError("superseded value requires superseded_by")
        if self.superseded_by and self.status is not RegistryStatus.SUPERSEDED:
            raise ValueError("superseded_by requires SUPERSEDED status")
        return self


class RegistryAdmission(BaseModel):
    """Deterministic admission request; it never fetches evidence itself."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: RegistryValue
    semantic_collision: bool = False
    vendor_only_label: bool = False
    operator_admission_ref: str | None = None
    decision_reason: str = Field(min_length=1)


class AdmissionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: AdmissionOutcome
    registry_id: str
    reason: str


def mint_registry_id(namespace: str, family: str, name: str) -> str:
    """Mint a stable, namespaced registry identifier."""

    identity = f"{namespace}|{family}|{name.strip().lower()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"csia:architecture:{namespace}:{family.lower()}:{digest}"


class ArchitectureRegistryBook:
    """In-memory append-only registry kernel; no persistence or acquisition."""

    def __init__(self) -> None:
        self._namespaces: dict[str, RegistryNamespace] = {}
        self._values: dict[str, RegistryValue] = {}
        self._semantic_index: dict[tuple[str, str], str] = {}
        self._superseded_by: dict[str, str] = {}
        self._supersession_boundaries: dict[str, Timestamp | UnknownBound] = {}
        for family in RATIFIED_ARCHITECTURE_FAMILIES:
            self.admit_namespace(
                RegistryNamespace(
                    namespace=family,
                    definition=f"Ratified Book 3 {family} definition namespace.",
                    operator_admission_ref="ratified-book3-plan-v0.2",
                    ratified=True,
                )
            )

    def admit_namespace(self, namespace: RegistryNamespace) -> RegistryNamespace:
        existing = self._namespaces.get(namespace.namespace)
        if existing is not None:
            if existing != namespace:
                raise ValueError("namespace admission is immutable")
            return existing
        self._namespaces[namespace.namespace] = namespace
        return namespace

    def namespace(self, namespace: str) -> RegistryNamespace:
        try:
            return self._namespaces[namespace]
        except KeyError as exc:
            raise KeyError(f"namespace {namespace} lacks operator admission") from exc

    def _validate_claims(self, value: RegistryValue, claim_store: ClaimStore) -> None:
        for claim_ref in value.source_claim_refs:
            try:
                claim = claim_store.require(claim_ref)
            except KeyError as exc:
                raise ValueError(f"unknown canonical Book 2 claim {claim_ref}") from exc
            if not can_promote_to_graph(claim, claim_store):
                raise ValueError(
                    f"claim {claim_ref} is not canonical graph-promotable Book 2 evidence"
                )
            if claim.claim_state not in (
                ClaimState.OBSERVED,
                ClaimState.INFERRED,
                ClaimState.CORROBORATED,
            ):
                raise ValueError(f"claim {claim_ref} cannot support a registry value")

    def evaluate(
        self,
        request: RegistryAdmission,
        claim_store: ClaimStore,
    ) -> AdmissionResult:
        value = request.value
        try:
            self.namespace(value.namespace)
        except KeyError as exc:
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                registry_id=value.registry_id,
                reason=str(exc),
            )
        if request.semantic_collision:
            return AdmissionResult(
                outcome=AdmissionOutcome.ESCALATED,
                registry_id=value.registry_id,
                reason="semantic collision requires operator adjudication",
            )
        if request.vendor_only_label:
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                registry_id=value.registry_id,
                reason="vendor-only naming has no architectural authority",
            )
        identity = (value.namespace, value.semantic_key.strip().lower())
        current_id = self._semantic_index.get(identity)
        if current_id is not None and current_id != value.supersedes:
            return AdmissionResult(
                outcome=AdmissionOutcome.ESCALATED,
                registry_id=value.registry_id,
                reason=f"semantic key already belongs to {current_id}",
            )
        if value.supersedes and value.supersedes not in self._values:
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                registry_id=value.registry_id,
                reason="supersedes target is unknown",
            )
        if value.supersedes and not _moves_forward(
            self._values[value.supersedes].valid_from,
            value.valid_from,
        ):
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                registry_id=value.registry_id,
                reason="replacement valid_from must move temporal state forward",
            )
        try:
            self._validate_claims(value, claim_store)
        except ValueError as exc:
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                registry_id=value.registry_id,
                reason=str(exc),
            )
        if current_id is None:
            return AdmissionResult(
                outcome=AdmissionOutcome.ADMITTED,
                registry_id=value.registry_id,
                reason="canonical evidence admitted in ratified namespace",
            )
        return AdmissionResult(
            outcome=AdmissionOutcome.ADMITTED,
            registry_id=value.registry_id,
            reason=f"evidence-admitted supersession of {current_id}",
        )

    def add(
        self,
        request: RegistryAdmission,
        claim_store: ClaimStore,
    ) -> RegistryValue:
        result = self.evaluate(request, claim_store)
        if result.outcome is not AdmissionOutcome.ADMITTED:
            raise ValueError(f"registry admission {result.outcome.value}: {result.reason}")
        value = request.value
        if value.registry_id != mint_registry_id(value.namespace, value.family, value.name):
            raise ValueError("registry_id is not the deterministic namespaced ID")
        if value.registry_id in self._values:
            raise ValueError("registry values are append-only; supersede instead")
        old_id: str | None = None
        if value.supersedes:
            old = self._values[value.supersedes]
            if old.status is not RegistryStatus.ACTIVE:
                raise ValueError("only an active value can be superseded")
            if old.namespace != value.namespace or old.semantic_key.casefold() != value.semantic_key.casefold():
                raise ValueError("supersession must preserve namespace and semantic key")
            if not _moves_forward(old.valid_from, value.valid_from):
                raise ValueError("replacement valid_from must move temporal state forward")
            old_id = old.registry_id
        self._values[value.registry_id] = value
        if old_id is not None:
            self._superseded_by[old_id] = value.registry_id
            self._supersession_boundaries[old_id] = value.valid_from
        self._semantic_index[(value.namespace, value.semantic_key.casefold())] = value.registry_id
        return value

    def admit_unknown(
        self,
        *,
        namespace: str,
        family: str,
        claim_store: ClaimStore,
        claim_ref: str,
        at: datetime,
        definition: str = "Family-native applicability is explicitly unknown.",
    ) -> RegistryValue:
        """Admit the explicit UNKNOWN sentinel without fabricating semantics."""

        normalize_utc(at)
        value = RegistryValue(
            registry_id=mint_registry_id(namespace, family, "unknown"),
            namespace=namespace,
            family=family,
            name="UNKNOWN",
            definition=definition,
            semantic_key="unknown",
            valid_from=at,
            source_claim_refs=(claim_ref,),
            status=RegistryStatus.UNKNOWN,
        )
        if value.registry_id in self._values:
            return self.require(value.registry_id)
        return self.add(
            RegistryAdmission(value=value, decision_reason="explicit unknown"),
            claim_store,
        )

    def require(self, registry_id: str) -> RegistryValue:
        try:
            value = self._values[registry_id]
        except KeyError as exc:
            raise KeyError(f"unknown registry value {registry_id}") from exc
        replacement_id = self._superseded_by.get(registry_id)
        boundary = self._supersession_boundaries.get(registry_id)
        if replacement_id is None or boundary is None:
            return value
        return value.model_copy(
            update={
                "status": RegistryStatus.SUPERSEDED,
                "superseded_by": replacement_id,
                "valid_to": _effective_valid_to(value, boundary),
            }
        )

    def current(self, namespace: str, semantic_key: str) -> RegistryValue | None:
        registry_id = self._semantic_index.get((namespace, semantic_key.casefold()))
        return self._values.get(registry_id) if registry_id else None

    def history(self, namespace: str, semantic_key: str) -> tuple[RegistryValue, ...]:
        values = [
            self.require(registry_id)
            for registry_id, value in self._values.items()
            if value.namespace == namespace
            and value.semantic_key.casefold() == semantic_key.casefold()
        ]
        return tuple(sorted(values, key=_history_sort_key))

    def values(self) -> tuple[RegistryValue, ...]:
        return tuple(self.require(registry_id) for registry_id in self._values)


def _history_sort_key(value: RegistryValue) -> tuple[int, datetime]:
    start = _known_start(value.valid_from)
    if start is None:
        assert isinstance(value.valid_from, UnknownBound)
        start = value.valid_from.earliest_bound or datetime.min.replace(tzinfo=UTC)
    return (1 if isinstance(value.valid_from, UnknownBound) else 0, start)


def _moves_forward(old_start: Timestamp | UnknownBound, new_start: Timestamp | UnknownBound) -> bool:
    old_known = _known_start(old_start)
    new_known = _known_start(new_start)
    return old_known is None or new_known is None or new_known > old_known


def _effective_valid_to(
    value: RegistryValue,
    supersession_boundary: Timestamp | UnknownBound,
) -> Timestamp | UnknownBound:
    if isinstance(supersession_boundary, UnknownBound):
        return supersession_boundary
    if isinstance(value.valid_to, UnknownBound):
        return value.valid_to
    if value.valid_to is None:
        return supersession_boundary
    return min(value.valid_to, supersession_boundary)


def _known_start(value: Timestamp | UnknownBound) -> datetime | None:
    if isinstance(value, UnknownBound):
        return None
    normalize_utc(value)
    return value


def _known_end(value: Timestamp | UnknownBound | None) -> datetime | None:
    if value is None or isinstance(value, UnknownBound):
        return None
    normalize_utc(value)
    return value


__all__ = [
    "RATIFIED_ARCHITECTURE_FAMILIES",
    "AdmissionOutcome",
    "AdmissionResult",
    "ArchitectureRegistryBook",
    "RegistryAdmission",
    "RegistryNamespace",
    "RegistryStatus",
    "RegistryValue",
    "mint_registry_id",
]
