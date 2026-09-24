"""CSIA Book 2 — Blocs 2D/2E: claim objects and CREATE_INFERRED."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .authority import AuthorityPolicy
from .evidence import EvidenceStore
from .identity import IdentityRegistry
from .temporal import (
    ClaimBinding,
    RecordLifecycle,
    Timestamp,
    UnknownBound,
    normalize_utc,
)
from .types import AuthorityTier, ClaimFamily

class Book2ClaimState(str, Enum):
    """Book 2 ratified claim machine, separate from Book 1 temporal kernel."""

    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    CORROBORATED = "CORROBORATED"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"
    STALE = "STALE"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


ClaimState = Book2ClaimState


class Book2ClaimBinding(BaseModel):
    """Book 2 claim projection; Book 1 receives only its compatible pointer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    book1: ClaimBinding
    book2_claim_state: Book2ClaimState

    @classmethod
    def from_claim(cls, claim: "Claim") -> "Book2ClaimBinding":
        source_id = claim.source_refs[0]
        evidence_ref = claim.evidence_refs[0]
        lineage = (*claim.lineage_evidence_refs, claim.methodology_ref) if claim.methodology_ref else claim.lineage_evidence_refs
        return cls(
            book1=ClaimBinding(
                claim_id=claim.claim_id,
                source_id=source_id,
                source_locator=evidence_ref,
                transformation_lineage=lineage,
                claim_state=RecordLifecycle.OBSERVED,
            ),
            book2_claim_state=claim.claim_state,
        )


class MethodologyParameter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    value: str


class Methodology(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    methodology_ref: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: tuple[MethodologyParameter, ...] = ()

    def parameter_tuple(self) -> tuple[MethodologyParameter, ...]:
        return self.parameters


class Proposition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_refs: tuple[str, ...] = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    qualifier: str | None = None

    def text(self) -> str:
        suffix = f" [{self.qualifier}]" if self.qualifier else ""
        return f"{','.join(self.subject_refs)} {self.predicate} {self.object_ref}{suffix}"


class SupersessionLineage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    superseded_claim_id: str = Field(min_length=1)
    replacement_claim_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Claim(BaseModel):
    """Immutable claim version; state changes append a new version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)
    object_refs: tuple[str, ...] = ()
    relationship_refs: tuple[str, ...] = ()
    proposition: Proposition
    claim_family: ClaimFamily
    claim_state: ClaimState
    valid_time_hypothesis: Timestamp | UnknownBound
    observed_time: datetime
    methodology: Methodology
    conflicts: tuple[str, ...] = ()
    supersession_lineage: SupersessionLineage | None = None
    claim_bindings: tuple[ClaimBinding, ...] = ()

    parent_claim_refs: tuple[str, ...] = ()
    parent_claim_states: tuple[ClaimState, ...] = ()
    methodology_ref: str | None = None
    methodology_parameters: tuple[MethodologyParameter, ...] = ()
    lineage_evidence_refs: tuple[str, ...] = ()
    valid_time_derivation: str | None = None

    @model_validator(mode="after")
    def _claim_rules(self) -> "Claim":
        normalize_utc(self.observed_time)
        if self.claim_state is ClaimState.INFERRED:
            if not self.parent_claim_refs:
                raise ValueError("I-1: INFERRED claims require parent claims")
            if len(self.parent_claim_refs) != len(self.parent_claim_states):
                raise ValueError("parent state snapshot must match parent refs")
            if any(
                state not in (ClaimState.OBSERVED, ClaimState.CORROBORATED)
                for state in self.parent_claim_states
            ):
                raise ValueError("I-2: inferred parents must be OBSERVED or CORROBORATED")
            if not self.methodology_ref or self.methodology_ref != self.methodology.methodology_ref:
                raise ValueError("I-3: inferred methodology reference is mandatory")
            if not self.lineage_evidence_refs:
                raise ValueError("I-4: inferred claims require terminating lineage evidence")
            if not self.valid_time_derivation:
                raise ValueError("I-10: inferred valid-time derivation is mandatory")
        elif self.parent_claim_refs or self.parent_claim_states:
            raise ValueError("non-inferred claims cannot carry inference parent fields")
        if self.claim_state is ClaimState.SUPERSEDED and self.supersession_lineage is None:
            raise ValueError("supersession always requires explicit lineage")
        if self.methodology_parameters != self.methodology.parameters:
            raise ValueError("methodology parameter snapshot must match methodology")
        return self


class ClaimStore:
    """Append-only current-plus-history store for claim versions."""

    def __init__(self) -> None:
        self._versions: dict[str, list[Claim]] = {}
        self._transitions: list["TransitionEvent"] = []

    def add(self, claim: Claim) -> Claim:
        if claim.claim_id in self._versions:
            raise ValueError(f"claim {claim.claim_id} already exists")
        self._versions[claim.claim_id] = [claim]
        return claim

    def require(self, claim_id: str) -> Claim:
        try:
            return self._versions[claim_id][-1]
        except KeyError as exc:
            raise KeyError(f"unknown claim {claim_id}") from exc

    def get(self, claim_id: str) -> Claim | None:
        history = self._versions.get(claim_id)
        return history[-1] if history else None

    def history(self, claim_id: str) -> tuple[Claim, ...]:
        try:
            return tuple(self._versions[claim_id])
        except KeyError as exc:
            raise KeyError(f"unknown claim {claim_id}") from exc

    @property
    def claims(self) -> dict[str, Claim]:
        return {claim_id: versions[-1] for claim_id, versions in self._versions.items()}

    def append_transition(self, claim: Claim, event: "TransitionEvent") -> Claim:
        history = self._versions.get(claim.claim_id)
        if history is None:
            raise KeyError(f"unknown claim {claim.claim_id}")
        if history[-1].claim_state is not event.prior_state:
            raise ValueError("transition prior state does not match current claim")
        history.append(claim)
        self._transitions.append(event)
        return claim

    @property
    def transitions(self) -> tuple["TransitionEvent", ...]:
        return tuple(self._transitions)


class TransitionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transition_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    prior_state: ClaimState
    new_state: ClaimState
    triggering_evidence_refs: tuple[str, ...] = Field(min_length=1)
    transitioned_at: datetime
    operator_involvement: str | None = None

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.transitioned_at)


class ClaimService:
    """Validates claim references without minting Book 1 objects."""

    def __init__(
        self,
        evidence_store: EvidenceStore,
        claim_store: ClaimStore | None = None,
        identity_registry: IdentityRegistry | None = None,
        authority_policy: AuthorityPolicy | None = None,
    ) -> None:
        self.evidence_store = evidence_store
        self.source_registry = getattr(evidence_store, "_source_registry", None)
        self.claim_store = claim_store or ClaimStore()
        self.identity_registry = identity_registry
        self.authority_policy = authority_policy

    def _validate_evidence(self, claim: Claim) -> tuple[str, ...]:
        for evidence_ref in claim.evidence_refs:
            self.evidence_store.require(evidence_ref)
        derived_sources = {
            self.evidence_store.require(evidence_ref).source_id
            for evidence_ref in claim.evidence_refs
        }
        if set(claim.source_refs) != derived_sources:
            raise ValueError("source_refs must be derived from evidence_refs")
        if self.identity_registry is not None:
            for object_ref in claim.object_refs:
                self.identity_registry.require(object_ref)
        return tuple(sorted(derived_sources))

    def _add_validated(self, claim: Claim) -> Claim:
        self._validate_evidence(claim)
        if claim.claim_state in (ClaimState.OBSERVED, ClaimState.CORROBORATED):
            self._require_promotion_authority(claim)
        return self.claim_store.add(claim)

    def add(self, claim: Claim) -> Claim:
        raise ValueError("raw claim insertion is closed; use add_declared, add_observed, or CREATE_INFERRED")

    def add_declared(self, claim: Claim) -> Claim:
        if claim.claim_state is not ClaimState.DECLARED:
            raise ValueError("add_declared accepts only DECLARED claims")
        return self._add_validated(claim)

    def add_observed(self, claim: Claim) -> Claim:
        if claim.claim_state is not ClaimState.OBSERVED:
            raise ValueError("add_observed accepts only OBSERVED claims")
        return self._add_validated(claim)

    def _require_promotion_authority(self, claim: Claim) -> None:
        if claim.claim_family is ClaimFamily.NARRATIVE:
            return
        if self.authority_policy is None:
            raise ValueError("structural promotion requires an AuthorityPolicy")
        resolutions = [
            self.authority_policy.resolve(source_id, claim.claim_family, claim.observed_time)
            for source_id in claim.source_refs
        ]
        if not any(item.tier is AuthorityTier.PRIMARY for item in resolutions):
            raise ValueError(
                "structural claim lacks a family-scoped primary source; "
                "narrative/aggregator evidence cannot promote structure"
            )

    def require(self, claim_id: str) -> Claim:
        return self.claim_store.require(claim_id)

    def lineage_evidence(self, claim: Claim) -> tuple[str, ...]:
        """Return all raw evidence reachable through claim parents."""

        visiting: set[str] = set()
        result: set[str] = set()

        def visit(current: Claim) -> None:
            if current.claim_id in visiting:
                raise ValueError("claim lineage cycle detected")
            visiting.add(current.claim_id)
            for evidence_ref in current.evidence_refs:
                self.evidence_store.require(evidence_ref)
                result.add(evidence_ref)
            if current.claim_state is ClaimState.INFERRED:
                for parent_ref in current.parent_claim_refs:
                    visit(self.claim_store.require(parent_ref))
            visiting.remove(current.claim_id)

        visit(claim)
        return tuple(sorted(result))


class InferenceEngine:
    """CREATE_INFERRED: new claim, immutable parents, terminating lineage."""

    def __init__(self, service: ClaimService) -> None:
        self.service = service

    @staticmethod
    def _mint_claim_id(
        parent_ids: tuple[str, ...], methodology: Methodology, proposition: Proposition
    ) -> str:
        payload = "|".join((*parent_ids, methodology.methodology_ref, proposition.text()))
        return "csia:claim:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    def create(
        self,
        *,
        parent_claim_refs: Iterable[str],
        methodology: Methodology,
        proposition: Proposition,
        valid_time_hypothesis: Timestamp | UnknownBound,
        valid_time_derivation: str,
        observed_time: datetime,
        object_refs: tuple[str, ...] = (),
        relationship_refs: tuple[str, ...] = (),
        claim_family: ClaimFamily | None = None,
        claim_id: str | None = None,
    ) -> Claim:
        parent_ids = tuple(parent_claim_refs)
        if not parent_ids:
            raise ValueError("I-1: at least one parent claim is required")
        parents = tuple(self.service.claim_store.require(parent_id) for parent_id in parent_ids)
        if claim_family is None:
            if len({parent.claim_family for parent in parents}) != 1:
                raise ValueError("inference claim family must be explicit and consistent")
            claim_family = parents[0].claim_family
        if not methodology.methodology_ref or not methodology.description:
            raise ValueError("I-3: methodology is mandatory")
        if not valid_time_derivation:
            raise ValueError("I-10: valid-time derivation is mandatory")
        parent_states = tuple(parent.claim_state for parent in parents)
        if any(state not in (ClaimState.OBSERVED, ClaimState.CORROBORATED) for state in parent_states):
            raise ValueError("I-2: every parent must be OBSERVED or CORROBORATED")
        parent_snapshots = tuple(parent.model_dump(mode="json") for parent in parents)
        lineage_refs = tuple(
            sorted({ref for parent in parents for ref in self.service.lineage_evidence(parent)})
        )
        if not lineage_refs:
            raise ValueError("I-4: parent lineage must terminate in RawEvidence")
        source_refs = tuple(
            sorted(
                {
                    self.service.evidence_store.require(ref).source_id
                    for ref in lineage_refs
                }
            )
        )
        new_id = claim_id or self._mint_claim_id(parent_ids, methodology, proposition)
        if self.service.claim_store.get(new_id) is not None:
            raise ValueError("inferred claim_id is already minted")
        inferred = Claim(
            claim_id=new_id,
            evidence_refs=lineage_refs,
            source_refs=source_refs,
            object_refs=object_refs,
            relationship_refs=relationship_refs,
            proposition=proposition,
            claim_family=claim_family,
            claim_state=ClaimState.INFERRED,
            valid_time_hypothesis=valid_time_hypothesis,
            observed_time=observed_time,
            methodology=methodology,
            methodology_ref=methodology.methodology_ref,
            methodology_parameters=methodology.parameters,
            lineage_evidence_refs=lineage_refs,
            valid_time_derivation=valid_time_derivation,
            parent_claim_refs=parent_ids,
            parent_claim_states=parent_states,
        )
        for parent, snapshot in zip(parents, parent_snapshots, strict=True):
            if parent.model_dump(mode="json") != snapshot:
                raise AssertionError("CREATE_INFERRED mutated a parent claim")
        return self.service._add_validated(inferred)


__all__ = [
    "Book2ClaimBinding",
    "Book2ClaimState",
    "Claim",
    "ClaimService",
    "ClaimState",
    "ClaimStore",
    "InferenceEngine",
    "Methodology",
    "MethodologyParameter",
    "Proposition",
    "SupersessionLineage",
    "TransitionEvent",
]
