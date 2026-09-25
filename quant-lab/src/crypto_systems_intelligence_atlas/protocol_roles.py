"""Book 4 protocol and infrastructure role assignments."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance
from .temporal import Timestamp, UnknownBound, normalize_utc


class ProtocolRole(str, Enum):
    ORACLE_NETWORK = "ORACLE_NETWORK"
    DATA_PUBLISHER = "DATA_PUBLISHER"
    DATA_SOURCE = "DATA_SOURCE"
    FEED = "FEED"
    PRICE_FEED = "PRICE_FEED"
    ATTESTATION_SERVICE = "ATTESTATION_SERVICE"
    DELIVERY_LAYER = "DELIVERY_LAYER"
    AUTOMATION_SERVICE = "AUTOMATION_SERVICE"
    MESSAGING_SERVICE = "MESSAGING_SERVICE"
    FALLBACK_SOURCE = "FALLBACK_SOURCE"
    MESSAGE_TRANSPORT = "MESSAGE_TRANSPORT"
    ASSET_BRIDGE = "ASSET_BRIDGE"
    CANONICAL_BRIDGE = "CANONICAL_BRIDGE"
    LIGHT_CLIENT_VERIFIER = "LIGHT_CLIENT_VERIFIER"
    VALIDATOR_VERIFIER = "VALIDATOR_VERIFIER"
    GUARDIAN_VERIFIER = "GUARDIAN_VERIFIER"
    ORACLE_ASSISTED_VERIFIER = "ORACLE_ASSISTED_VERIFIER"
    LOCK_MINT = "LOCK_MINT"
    BURN_MINT = "BURN_MINT"
    LIQUIDITY_BRIDGE = "LIQUIDITY_BRIDGE"
    INTENT_BASED_TRANSFER = "INTENT_BASED_TRANSFER"
    CHAIN_NATIVE_INTEROPERABILITY = "CHAIN_NATIVE_INTEROPERABILITY"
    RELAYER_LAYER = "RELAYER_LAYER"
    ENDPOINT = "ENDPOINT"
    CHANNEL = "CHANNEL"
    ROUTE = "ROUTE"
    DA_NETWORK = "DA_NETWORK"
    DA_PROVIDER = "DA_PROVIDER"
    BLOB_DATA_PUBLICATION = "BLOB_DATA_PUBLICATION"
    SAMPLING_AVAILABILITY_MECHANISM = "SAMPLING_AVAILABILITY_MECHANISM"
    RETRIEVAL_SERVICE = "RETRIEVAL_SERVICE"
    SEQUENCER = "SEQUENCER"
    SETTLEMENT_LAYER = "SETTLEMENT_LAYER"
    SECURITY_PROVIDER = "SECURITY_PROVIDER"
    FALLBACK_DA = "FALLBACK_DA"
    RPC_PROVIDER = "RPC_PROVIDER"
    NODE_INFRASTRUCTURE = "NODE_INFRASTRUCTURE"
    INDEXER = "INDEXER"
    DATA_API = "DATA_API"
    SDK = "SDK"
    FRAMEWORK = "FRAMEWORK"
    DEVELOPER_TOOL = "DEVELOPER_TOOL"
    WALLET_INFRASTRUCTURE = "WALLET_INFRASTRUCTURE"
    EXPLORER = "EXPLORER"
    OPERATIONAL_PROVIDER = "OPERATIONAL_PROVIDER"
    HOSTED_SERVICE = "HOSTED_SERVICE"


class RoleState(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    DECLARED_ONLY = "DECLARED_ONLY"
    UNKNOWN = "UNKNOWN"


class RoleAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role_assignment_id: str = Field(min_length=1)
    system_ref: str = Field(min_length=1)
    role_type: ProtocolRole
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    consumes: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    role_state: RoleState
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    source_snapshot_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _temporal(self) -> "RoleAssignment":
        if isinstance(self.valid_from, Timestamp):
            normalize_utc(self.valid_from)
        if isinstance(self.valid_to, Timestamp):
            normalize_utc(self.valid_to)
        return self


class ProtocolRoleBook:
    """Roles are multi-valued, temporal, non-exclusive, and scope-specific."""

    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._assignments: dict[str, RoleAssignment] = {}

    def add(self, assignment: RoleAssignment) -> RoleAssignment:
        if assignment.role_assignment_id in self._assignments:
            raise ValueError("role assignment IDs are immutable and unique")
        self.provenance.validate_refs(assignment.book2_claim_refs)
        self._assignments[assignment.role_assignment_id] = assignment
        return assignment

    def for_system(self, system_ref: str) -> tuple[RoleAssignment, ...]:
        return tuple(
            item for item in self._assignments.values() if item.system_ref == system_ref
        )

    def all_assignments(self) -> tuple[RoleAssignment, ...]:
        return tuple(self._assignments.values())


__all__ = ["ProtocolRole", "ProtocolRoleBook", "RoleAssignment", "RoleState"]
