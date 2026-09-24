"""CSIA Book 3 — native architecture dossiers and Book 2 provenance gate."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture_registry import ArchitectureRegistryBook, RegistryStatus
from .claims import Claim, ClaimStore, can_promote_to_graph
from .evidence import EvidenceStore
from .temporal import Timestamp, UnknownBound, holds_at, normalize_utc
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

ARCHITECTURE_FIELD_NAMESPACES: Final = {
    "execution_model_ref": "EXECUTION_MODEL",
    "state_model_ref": "STATE_MODEL",
    "consensus_model_ref": "CONSENSUS_MODEL",
    "finality_model_ref": "FINALITY_MODEL",
    "data_availability_model_ref": "DA_MODEL",
    "settlement_model_ref": "SETTLEMENT_MODEL",
    "governance_model_ref": "GOVERNANCE_MODEL",
    "fee_model_ref": "FEE_MODEL",
    "upgrade_model_ref": "UPGRADE_MODEL",
    "interoperability_model_ref": "INTEROP_MODEL",
    "deployment_model_ref": "DEPLOYMENT_MODEL",
    "security_model_ref": "SECURITY_MODEL",
    "sequencing_model_ref": "SEQUENCING_MODEL",
}


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

    network_identity_claim_refs: tuple[str, ...] = ()
    genesis_or_origin_claim_refs: tuple[str, ...] = ()
    native_asset_claim_refs: tuple[str, ...] = ()

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
        explicit_groups = (
            (self.network_identity_anchor_refs, self.network_identity_claim_refs, "network identity"),
            (self.genesis_or_origin_anchor_refs, self.genesis_or_origin_claim_refs, "genesis/origin"),
            (self.native_asset_refs, self.native_asset_claim_refs, "native asset"),
        )
        for anchor_refs, claim_refs, label in explicit_groups:
            if anchor_refs and not claim_refs:
                raise ValueError(f"{label} anchors require explicit Book 2 claim refs")
            if claim_refs and not anchor_refs:
                raise ValueError(f"{label} claim refs require corresponding anchors")
            if not set(claim_refs).issubset(self.source_claim_refs):
                raise ValueError(f"{label} claim refs must belong to source_claim_refs")
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

    def __init__(
        self,
        claim_store: ClaimStore,
        evidence_store: EvidenceStore,
        registry: ArchitectureRegistryBook | None = None,
    ) -> None:
        self.claim_store = claim_store
        self.evidence_store = evidence_store
        self.registry = registry

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
        historical: bool = False,
    ) -> ArchitectureDossier:
        supplied_claims = supplied_claims or {}
        identity_families = (
            ClaimFamily.IDENTITY_ATTRIBUTES,
            ClaimFamily.HISTORICAL_GENESIS_SPEC,
            ClaimFamily.CHAIN_ARCHITECTURE,
        )
        genesis_families = (
            ClaimFamily.HISTORICAL_GENESIS_SPEC,
            ClaimFamily.IDENTITY_ATTRIBUTES,
            ClaimFamily.CHAIN_ARCHITECTURE,
        )
        native_asset_families = (
            ClaimFamily.TOKEN_ROLE_MECHANICS,
            ClaimFamily.IDENTITY_ATTRIBUTES,
            ClaimFamily.CHAIN_ARCHITECTURE,
        )
        explicit_groups = (
            (dossier.network_identity_claim_refs, identity_families),
            (dossier.genesis_or_origin_claim_refs, genesis_families),
            (dossier.native_asset_claim_refs, native_asset_families),
        )
        for claim_refs, allowed_families in explicit_groups:
            for claim_ref in claim_refs:
                self.resolve_claim(
                    claim_ref,
                    expected_claim=supplied_claims.get(claim_ref),
                    allowed_families=allowed_families,
                )
        for field_name, claim_refs in dossier.field_claim_refs.items():
            for claim_ref in claim_refs:
                self.resolve_claim(
                    claim_ref,
                    expected_claim=supplied_claims.get(claim_ref),
                    allowed_families=(ClaimFamily.CHAIN_ARCHITECTURE,),
                )
            self._validate_registry_reference(dossier, field_name, historical=historical)
        declared = set(
            ref
            for refs in explicit_groups
            for ref in refs[0]
        ) | {ref for refs in dossier.field_claim_refs.values() for ref in refs}
        if declared != set(dossier.source_claim_refs):
            raise ArchitectureProvenanceError(
                "source_claim_refs must exactly match explicit anchor and field claim bindings"
            )
        return dossier

    def _validate_registry_reference(
        self,
        dossier: ArchitectureDossier,
        field_name: str,
        *,
        historical: bool,
    ) -> None:
        if self.registry is None:
            raise ArchitectureProvenanceError("dossier validation requires an architecture registry")
        registry_ref = getattr(dossier, field_name)
        if registry_ref is None:
            return
        try:
            registry_value = self.registry.require(registry_ref)
        except KeyError as exc:
            raise ArchitectureProvenanceError(f"unknown registry value {registry_ref}") from exc
        expected_namespaces = (
            ("VALIDATOR_MODEL", "PARTICIPANT_MODEL")
            if field_name == "validator_or_participant_model_ref"
            else (ARCHITECTURE_FIELD_NAMESPACES[field_name],)
        )
        if registry_value.namespace not in expected_namespaces:
            raise ArchitectureProvenanceError(
                f"registry namespace {registry_value.namespace} is invalid for {field_name}"
            )
        for claim_ref in registry_value.source_claim_refs:
            self.resolve_claim(
                claim_ref,
                allowed_families=(ClaimFamily.CHAIN_ARCHITECTURE,),
            )
        if not historical and registry_value.status not in (
            RegistryStatus.ACTIVE,
            RegistryStatus.UNKNOWN,
        ):
            raise ArchitectureProvenanceError(
                f"registry value {registry_ref} is superseded, not current truth"
            )
        if historical and registry_value.status is RegistryStatus.SUPERSEDED:
            if isinstance(dossier.valid_time, UnknownBound):
                raise ArchitectureProvenanceError(
                    "historical superseded registry value requires a known dossier valid_time"
                )
            holds = holds_at(
                registry_value.valid_from,
                registry_value.valid_to,
                dossier.valid_time,
            )
            if holds is not True:
                raise ArchitectureProvenanceError(
                    f"registry value {registry_ref} does not hold at dossier valid_time"
                )


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
    "ARCHITECTURE_FIELD_NAMESPACES",
    "ARCHITECTURE_REFERENCE_FIELDS",
    "ArchitectureComponent",
    "ArchitectureDossier",
    "ArchitectureProvenanceError",
    "Book2ArchitectureProvenance",
    "ComponentRole",
    "ModularArchitecture",
]
