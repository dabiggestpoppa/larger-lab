"""CSIA Book 3 — native architecture dossiers and Book 2 provenance gate."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .claims import Claim, ClaimStore, can_promote_to_graph
from .evidence import EvidenceStore
from .temporal import Timestamp, UnknownBound, normalize_utc
from .types import ClaimFamily

ARCHITECTURE_REFERENCE_FIELDS: Final = (
    "execution_model_ref",
    "state_model_ref",
    "consensus_model_ref",
    "finality_model_ref",
    "data_availability_model_ref",
    "settlement_model_ref",
    "validator_or_participant_model_ref",
    "governance_model_ref",
    "fee_model_ref",
    "upgrade_model_ref",
    "interoperability_model_ref",
    "deployment_model_ref",
    "security_model_ref",
    "sequencing_model_ref",
)
"""All architecture value fields; ``None`` means family-native absence."""


class ArchitectureDossier(BaseModel):
    """Envelope for one native architecture truth window."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)
    architecture_family: str = Field(min_length=1)
    network_namespace: str = Field(min_length=1)
    network_identity_anchor_refs: tuple[str, ...] = ()
    genesis_or_origin_anchor_refs: tuple[str, ...] = ()
    native_asset_refs: tuple[str, ...] = ()

    execution_model_ref: str | None = None
    state_model_ref: str | None = None
    consensus_model_ref: str | None = None
    finality_model_ref: str | None = None
    data_availability_model_ref: str | None = None
    settlement_model_ref: str | None = None
    validator_or_participant_model_ref: str | None = None
    governance_model_ref: str | None = None
    fee_model_ref: str | None = None
    upgrade_model_ref: str | None = None
    interoperability_model_ref: str | None = None
    deployment_model_ref: str | None = None
    security_model_ref: str | None = None
    sequencing_model_ref: str | None = None

    source_claim_refs: tuple[str, ...] = ()
    field_claim_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    valid_time: Timestamp | UnknownBound
    observed_time: datetime

    @model_validator(mode="after")
    def _shape(self) -> "ArchitectureDossier":
        normalize_utc(self.observed_time)
        if not isinstance(self.valid_time, UnknownBound):
            normalize_utc(self.valid_time)
        known_fields = {
            name: getattr(self, name)
            for name in ARCHITECTURE_REFERENCE_FIELDS
            if getattr(self, name) is not None
        }
        for field_name, refs in self.field_claim_refs.items():
            if field_name not in known_fields:
                raise ValueError(f"field_claim_refs contains absent field {field_name}")
            if not refs:
                raise ValueError(f"populated field {field_name} requires claim refs")
            if not set(refs).issubset(self.source_claim_refs):
                raise ValueError(f"field {field_name} refs must belong to source_claim_refs")
        missing = set(known_fields) - set(self.field_claim_refs)
        if missing:
            raise ValueError(f"populated architecture fields lack provenance: {sorted(missing)}")
        if not self.source_claim_refs:
            if known_fields:
                raise ValueError("populated architecture requires Book 2 source claims")
        return self


class ArchitectureProvenanceError(ValueError):
    """A dossier or relation failed the canonical Book 2 evidence gate."""


class Book2ArchitectureProvenance:
    """Validate pointers against the accepted Book 2 claim/evidence engines."""

    def __init__(self, claim_store: ClaimStore, evidence_store: EvidenceStore) -> None:
        self.claim_store = claim_store
        self.evidence_store = evidence_store

    def resolve_claim(
        self,
        claim_ref: str,
        *,
        expected_claim: Claim | None = None,
        require_current: bool = True,
        allowed_families: tuple[ClaimFamily, ...] = (ClaimFamily.CHAIN_ARCHITECTURE,),
    ) -> Claim:
        try:
            canonical = self.claim_store.require(claim_ref)
        except KeyError as exc:
            raise ArchitectureProvenanceError(f"unknown claim ID {claim_ref}") from exc
        if expected_claim is not None and canonical != expected_claim:
            raise ArchitectureProvenanceError(f"forged or detached claim object {claim_ref}")
        if require_current and not can_promote_to_graph(canonical, self.claim_store):
            state = canonical.claim_state.value
            raise ArchitectureProvenanceError(
                f"claim {claim_ref} is not canonical current graph-promotable ({state})"
            )
        if canonical.claim_family not in allowed_families:
            raise ArchitectureProvenanceError(
                f"claim {claim_ref} family {canonical.claim_family.value} is not accepted here"
            )
        for evidence_ref in canonical.evidence_refs:
            try:
                self.evidence_store.require(evidence_ref)
            except KeyError as exc:
                raise ArchitectureProvenanceError(
                    f"claim {claim_ref} has detached evidence {evidence_ref}"
                ) from exc
        return canonical

    def validate_dossier(
        self,
        dossier: ArchitectureDossier,
        *,
        supplied_claims: dict[str, Claim] | None = None,
    ) -> ArchitectureDossier:
        supplied_claims = supplied_claims or {}
        allowed_identity_families: tuple[ClaimFamily, ...] = (
            ClaimFamily.IDENTITY_ATTRIBUTES,
            ClaimFamily.HISTORICAL_GENESIS_SPEC,
            ClaimFamily.CHAIN_ARCHITECTURE,
        )
        for claim_ref in dossier.source_claim_refs:
            field_names = tuple(
                name for name, refs in dossier.field_claim_refs.items() if claim_ref in refs
            )
            if dossier.network_namespace in field_names:
                allowed = allowed_identity_families
            elif field_names:
                allowed = (ClaimFamily.CHAIN_ARCHITECTURE,)
            else:
                allowed = allowed_identity_families + (ClaimFamily.CHAIN_ARCHITECTURE,)
            self.resolve_claim(
                claim_ref,
                expected_claim=supplied_claims.get(claim_ref),
                allowed_families=allowed,
            )
        return dossier


class ComponentRole(str, Enum):
    EXECUTION = "EXECUTION"
    SEQUENCING = "SEQUENCING"
    SETTLEMENT = "SETTLEMENT"
    DATA_AVAILABILITY = "DA"
    SECURITY = "SECURITY"
    CONSENSUS = "CONSENSUS"
    BRIDGE_MESSAGING = "BRIDGE_MESSAGING"


class ArchitectureComponent(BaseModel):
    """Typed modular component; component identity is not chain identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    component_id: str = Field(min_length=1)
    role: ComponentRole
    canonical_name: str = Field(min_length=1)
    architecture_ref: str | None = None
    source_claim_refs: tuple[str, ...] = Field(min_length=1)


class ModularArchitecture(BaseModel):
    """A modular system envelope preserving provider distinctions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    system_id: str = Field(min_length=1)
    components: tuple[ArchitectureComponent, ...]

    @model_validator(mode="after")
    def _roles_are_explicit(self) -> "ModularArchitecture":
        roles = [component.role for component in self.components]
        if len(roles) != len(set(roles)):
            raise ValueError("component roles must be unique")
        return self

    def require(self, role: ComponentRole) -> ArchitectureComponent:
        for component in self.components:
            if component.role is role:
                return component
        raise KeyError(f"architecture has no {role.value} component")


__all__ = [
    "ARCHITECTURE_REFERENCE_FIELDS",
    "ArchitectureComponent",
    "ArchitectureDossier",
    "ArchitectureProvenanceError",
    "Book2ArchitectureProvenance",
    "ComponentRole",
    "ModularArchitecture",
]
