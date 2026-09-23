"""CSIA Book 1 — Bloc 1A: Canonical identity kernel.

Implements the ratified Book 1 plan v0.3 identity doctrine
(`CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.3.md` §1A) on top of
Constitution v0.2 §8 (RATIFIED).

Doctrine highlights enforced here:

- identity is canonical, ticker-independent, minted once (INV-1A-1);
- no two ACTIVE objects share an ``(object_type, slug)`` (INV-1A-2);
- deployments reference chains by object_id, never by name (INV-1A-3);
- objects are never deleted, only lifecycle-transitioned (INV-1A-4);
- deployments = issuance forms (typed marker enum, E-5/C-2);
- realizations = travel forms (R-1A-5 Option C, C-14): a temporally versioned,
  chain-local manifestation of ONE canonical economic asset — never a new
  asset, never an attribute blob, never a protocol deployment
  (INV-1A-9..11, INV-1B-8).
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .temporal import (
    OPEN,
    ObjectLifecycle,
    RealizationStatus,
    Timestamp,
    UnknownBound,
    holds_at,
    normalize_utc,
    utc_now,
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _require_aware(value: datetime, what: str) -> datetime:
    """Reject naive lifecycle timestamps; normalize aware values to UTC.
    Hardening R2: model_copy bypasses field validation, so public lifecycle
    operations enforce timestamp hygiene explicitly (no silent local-time
    assumptions)."""
    try:
        return normalize_utc(value)
    except ValueError as exc:
        raise ValueError(f"{what}: {exc}") from exc


_M = TypeVar("_M", bound=BaseModel)


def _replace_validated(model: _M, updates: dict[str, object]) -> _M:
    """Hardening R2: validated state replacement.

    ``model_copy(update=...)`` bypasses ALL validators, so a lifecycle
    transition could mint states direct construction would reject (e.g.
    IR-6 violations on close). This helper reconstructs through the full
    validated model path instead: ``model_copy`` for the payload, then
    ``model_validate`` so every model_validator runs on the result.
    """
    draft = model.model_copy(update=updates)
    return type(model).model_validate(draft.model_dump())


class ObjectType(str, Enum):
    """Primary node classes — the ratified 42-class registry (Bloc 1B.6, C-15/C-22).

    Constitution §9.2 list + ``REALIZATION`` (adopted via R-1A-5 = Option C).
    Class additions go through the extension mechanism (§9.3), never silently.
    """

    BLOCKCHAIN = "BLOCKCHAIN"
    LEDGER = "LEDGER"
    PROTOCOL = "PROTOCOL"
    TOKEN = "TOKEN"
    STABLECOIN = "STABLECOIN"
    BRIDGE = "BRIDGE"
    ORACLE_NETWORK = "ORACLE_NETWORK"
    INTEROP_PROTOCOL = "INTEROP_PROTOCOL"
    DATA_AVAILABILITY_NETWORK = "DATA_AVAILABILITY_NETWORK"
    DEX = "DEX"
    PERP_DEX = "PERP_DEX"
    LENDING_PROTOCOL = "LENDING_PROTOCOL"
    STAKING_PROTOCOL = "STAKING_PROTOCOL"
    RESTAKING_PROTOCOL = "RESTAKING_PROTOCOL"
    RWA_PROTOCOL = "RWA_PROTOCOL"
    PAYMENT_SYSTEM = "PAYMENT_SYSTEM"
    STORAGE_NETWORK = "STORAGE_NETWORK"
    COMPUTE_NETWORK = "COMPUTE_NETWORK"
    DEPIN_NETWORK = "DEPIN_NETWORK"
    IDENTITY_SYSTEM = "IDENTITY_SYSTEM"
    PRIVACY_SYSTEM = "PRIVACY_SYSTEM"
    WALLET_INFRASTRUCTURE = "WALLET_INFRASTRUCTURE"
    KEY_MANAGEMENT_INFRASTRUCTURE = "KEY_MANAGEMENT_INFRASTRUCTURE"
    RPC_INFRASTRUCTURE = "RPC_INFRASTRUCTURE"
    INDEXING_INFRASTRUCTURE = "INDEXING_INFRASTRUCTURE"
    DEVELOPER_TOOLING = "DEVELOPER_TOOLING"
    SEQUENCER_INFRASTRUCTURE = "SEQUENCER_INFRASTRUCTURE"
    PROVER_ATTESTATION_INFRASTRUCTURE = "PROVER_ATTESTATION_INFRASTRUCTURE"
    INTENT_SOLVER_NETWORK = "INTENT_SOLVER_NETWORK"
    INSURANCE_SECURITY_PROTOCOL = "INSURANCE_SECURITY_PROTOCOL"
    VM = "VM"
    STANDARD = "STANDARD"
    VALIDATOR_SYSTEM = "VALIDATOR_SYSTEM"
    GOVERNANCE_SYSTEM = "GOVERNANCE_SYSTEM"
    ENTITY = "ENTITY"
    ASSET = "ASSET"
    MARKET = "MARKET"
    APPLICATION = "APPLICATION"
    INTEGRATION = "INTEGRATION"
    EVENT = "EVENT"
    NARRATIVE = "NARRATIVE"
    REALIZATION = "REALIZATION"  # 42nd class — R-1A-5 Option C [C-15]

    @classmethod
    def asset_classes(cls) -> tuple["ObjectType", ...]:
        """Classes a canonical economic asset may take (REALIZES range, IR-13)."""
        return (cls.TOKEN, cls.STABLECOIN, cls.ASSET)


class DeploymentMarkerKind(str, Enum):
    """Typed deployment-marker enum (E-5 / C-2). Issuance forms."""

    CONTRACT = "CONTRACT"
    NATIVE = "NATIVE"
    ISSUER_ACCOUNT = "ISSUER_ACCOUNT"
    PROGRAM = "PROGRAM"
    MINT_ACCOUNT = "MINT_ACCOUNT"
    CANISTER = "CANISTER"
    PACKAGE = "PACKAGE"
    OTHER = "OTHER"  # requires (family, defining_string); Book 3B registers families


class RepresentationMechanism(str, Enum):
    """Realization representation mechanism (R-1A-5 Option C schema)."""

    IBC = "IBC"
    CHAIN_KEY = "CHAIN_KEY"
    LOCK_MINT = "LOCK_MINT"
    LIGHT_CLIENT = "LIGHT_CLIENT"
    OTHER = "OTHER"  # requires defining_string


class DeploymentStatus(str, Enum):
    """Deployment status enum (v0.3 final — Option A's CHANNEL_REPRESENTATIVE
    was NOT adopted; channel-bound forms are REALIZATIONs, not deployments)."""

    CANONICAL = "CANONICAL"
    BRIDGED_REPRESENTATIVE = "BRIDGED_REPRESENTATIVE"
    WRAPPED = "WRAPPED"
    DEPRECATED = "DEPRECATED"


class Alias(BaseModel):
    """Historical name window (INV-1A-5: non-overlapping per object unless
    collision-marked)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    # Hardening R2: rebrand history windows inherit the object's valid_from,
    # which may be an explicit UNKNOWN bound (never silently converted to a
    # known instant — R9: no fabricated certainty).
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None  # None = still holds
    name_state: Literal["ACTIVE", "HISTORICAL"]


class TickerSymbol(BaseModel):
    """Ticker as a *contextual attribute* — never an identity key (§8, INV-1A-5)."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    context: str = Field(min_length=1)
    valid_from: Timestamp
    valid_to: Timestamp | None = None
    collision_group: str | None = None


class DeploymentIdentity(BaseModel):
    """Issuance-form identity: how an asset comes to exist on a chain.

    The marker *type* is part of deployment identity (rule 10); marker-type
    correction is an operator-reviewed reclassification, never a silent edit.
    """

    model_config = ConfigDict(extra="forbid")

    deployment_id: str = Field(min_length=1)
    chain: str = Field(min_length=1)  # chain object_id, NEVER a chain name (INV-1A-3)
    marker_kind: DeploymentMarkerKind
    marker_value: str | None = None  # addr / program_id / mint / canister / pkg_id
    marker_family: str | None = None  # required iff marker_kind == OTHER
    marker_defining_string: str | None = None  # required iff marker_kind == OTHER
    standard: str | None = None  # standard object_id
    decimals: int | None = None
    deploy_tx_ref: str | None = None  # evidence pointer
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None  # None/OPEN = still live
    status: DeploymentStatus = DeploymentStatus.CANONICAL

    @model_validator(mode="after")
    def _marker_rules(self) -> "DeploymentIdentity":
        if self.marker_kind is DeploymentMarkerKind.OTHER:
            if not self.marker_family or not self.marker_defining_string:
                raise ValueError(
                    "OTHER markers require marker_family and marker_defining_string "
                    "(INV-1A-8)"
                )
        elif self.marker_kind is not DeploymentMarkerKind.NATIVE:
            if not self.marker_value:
                raise ValueError(
                    f"marker {self.marker_kind.value} requires marker_value (INV-1A-8)"
                )
        elif self.marker_value is not None:
            raise ValueError("NATIVE markers carry no marker_value")
        return self

    @model_validator(mode="after")
    def _temporal_rules(self) -> "DeploymentIdentity":
        start = _bound_start(self.valid_from)
        end = _bound_end(self.valid_to)
        if start is not None and end is not None and start > end:
            raise ValueError("valid_from > valid_to is always invalid (IR-6)")
        return self


class RouteHop(BaseModel):
    """One hop of a multi-hop route (chain, channel, port) — full ordered list."""

    model_config = ConfigDict(extra="forbid")

    chain_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    port: str | None = None


class RealizationRoute(BaseModel):
    """Route identity of a realization (R-1A-5 Option C schema).

    Multi-hop truth lives HERE, at record level — the exact property that
    disqualified attribute-level (Option B) representation under Bloc 1D.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)  # route identity (path id or derivation)
    channel_sequence: list[str] = Field(default_factory=list)  # hop order
    multi_hop_route: list[RouteHop] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sequence_matches(self) -> "RealizationRoute":
        if self.channel_sequence and self.multi_hop_route:
            if len(self.channel_sequence) != len(self.multi_hop_route):
                raise ValueError(
                    "channel_sequence length must match multi_hop_route length"
                )
        return self


class RealizationIdentity(BaseModel):
    """Travel-form identity (R-1A-5 Option C, CONTRACTUAL [C-14]).

    Doctrine (operator-confirmed, normative): a REALIZATION is a temporally
    versioned, chain-local manifestation of the SAME canonical economic asset.
    It is NOT a new economic asset, NOT an attribute blob, NOT a protocol
    deployment.
    """

    model_config = ConfigDict(extra="forbid")

    realization_id: str = Field(min_length=1)
    canonical_asset_id: str = Field(min_length=1)  # the ONE economic asset
    chain_id: str = Field(min_length=1)  # destination chain object_id
    local_asset_identifier: str = Field(min_length=1)  # denom / token id / contract-of-record
    representation_mechanism: RepresentationMechanism
    mechanism_defining_string: str | None = None  # required iff OTHER
    route: RealizationRoute | None = None
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None  # OPEN while ACTIVE
    status: RealizationStatus = RealizationStatus.ACTIVE
    migration_from: str | None = None  # lineage, non-destructive (INV-1A-11)
    migration_to: str | None = None
    claim_bindings: list[str] = Field(default_factory=list)  # provenance per realization

    @model_validator(mode="after")
    def _mechanism_rules(self) -> "RealizationIdentity":
        if self.representation_mechanism is RepresentationMechanism.OTHER:
            if not self.mechanism_defining_string:
                raise ValueError(
                    "OTHER mechanism requires mechanism_defining_string"
                )
        elif self.mechanism_defining_string is not None:
            raise ValueError(
                "mechanism_defining_string is only valid for OTHER mechanism"
            )
        return self

    @model_validator(mode="after")
    def _temporal_rules(self) -> "RealizationIdentity":
        start = _bound_start(self.valid_from)
        end = _bound_end(self.valid_to)
        if start is not None and end is not None and start > end:
            raise ValueError("valid_from > valid_to is always invalid (IR-6)")
        if self.status in (RealizationStatus.CLOSED, RealizationStatus.MIGRATED):
            if self.valid_to is None:
                raise ValueError(
                    f"{self.status.value} realizations must carry valid_to "
                    "(closure is a world-change; INV-1A-10 keeps them queryable, "
                    "never open)"
                )
        if self.status is RealizationStatus.MIGRATED:
            if not (self.migration_from or self.migration_to):
                raise ValueError(
                    "MIGRATED realizations must carry migration lineage pointers "
                    "(INV-1A-11)"
                )
        return self

    def is_live(self, at: datetime) -> bool | None:
        """Liveness at valid-time ``at`` (R6 as-of, R9-aware).

        Liveness is determined by VALID TIME, never by lifecycle status —
        a CLOSED realization with valid_to = T1 was live at every T < T1
        (closure is a world-change recorded at T1, not a retroactive erasure).

        Returns True (live), False (not live), or None (undecidable when an
        UNKNOWN bound covers ``at``) — mirroring :func:`holds_at`.
        """
        return holds_at(self.valid_from, self.valid_to, at)


class IdentityResolutionEvent(BaseModel):
    """Merge/split event (INV-1A-6): irreversible; a reverse requires a new
    event. Every event is operator-approved and evidence-bound."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    kind: Literal["MERGE", "SPLIT"]
    source_object_ids: list[str] = Field(min_length=1)
    target_object_ids: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    occurred_at: datetime


class CanonicalObject(BaseModel):
    """The canonical graph object (plan v0.3 §1A.6 ObjectIdentity).

    Identity is minted once and immutable; everything else is versioned.
    """

    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(min_length=1)
    object_type: ObjectType
    role_tags: tuple[str, ...] = ()
    canonical_name: str = Field(min_length=1)
    aliases: tuple[Alias, ...] = ()
    ticker_symbols: tuple[TickerSymbol, ...] = ()
    chain_namespace: str | None = None  # chain object_id | None
    deployments: tuple[DeploymentIdentity, ...] = ()
    realizations: tuple[RealizationIdentity, ...] = ()
    entity_relationships: tuple[str, ...] = ()
    lifecycle_state: ObjectLifecycle = ObjectLifecycle.ACTIVE
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    claim_bindings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _object_id_scheme(self) -> "CanonicalObject":
        parts = self.object_id.split(":")
        if len(parts) != 3 or parts[0] != "csia":
            raise ValueError(
                f"object_id {self.object_id!r} must be 'csia:<type>:<slug>'"
            )
        if parts[1] != self.object_type.value:
            raise ValueError(
                f"object_id namespace {parts[1]!r} must equal object_type "
                f"{self.object_type.value!r} (INV-1A-1)"
            )
        if not _SLUG_RE.match(parts[2]):
            raise ValueError(f"invalid slug {parts[2]!r}")
        return self

    @model_validator(mode="after")
    def _temporal_rules(self) -> "CanonicalObject":
        start = _bound_start(self.valid_from)
        end = _bound_end(self.valid_to)
        if start is not None and end is not None and start > end:
            raise ValueError("valid_from > valid_to is always invalid (IR-6)")
        return self


def mint_object_id(object_type: ObjectType, slug: str) -> str:
    """Mint an object id ``csia:<type>:<slug>`` (Constitution §8.2)."""
    if not _SLUG_RE.match(slug):
        raise ValueError(f"invalid slug {slug!r}")
    return f"csia:{object_type.value}:{slug}"


def mint_deployment_id(object_id: str, chain_object_id: str, marker: str) -> str:
    """``<object_id>@<chain_object_id>:<marker>`` per plan §1A.6."""
    return f"{object_id}@{chain_object_id}:{marker}"


def mint_realization_id(
    object_id: str, chain_object_id: str, realization_marker: str
) -> str:
    """``<object_id>@<chain_object_id>:<realization_marker>`` per plan §1A.6."""
    return f"{object_id}@{chain_object_id}:{realization_marker}"


class IdentityRegistry:
    """In-memory registry enforcing Bloc 1A invariants at mint/merge time.

    This is the Book 1 *kernel* contract surface — no persistence layer is
    authorized at this stage (beyond what unit tests need, which is nothing:
    the registry itself is the state).
    """

    def __init__(self) -> None:
        self._objects: dict[str, CanonicalObject] = {}
        self._resolution_events: list[IdentityResolutionEvent] = []
        # committed rebrand/closure instants per object (history ambiguity
        # guard, hardening R2 — store-level metadata, not record mutation)
        self._rebrand_instants: dict[str, tuple[datetime, ...]] = {}

    # -- minting ----------------------------------------------------------

    def mint(self, obj: CanonicalObject) -> CanonicalObject:
        if obj.object_id in self._objects:
            raise ValueError(f"object {obj.object_id} already minted (minted once)")
        slug = obj.object_id.split(":")[2]
        for existing in self._objects.values():
            if (
                existing.lifecycle_state is ObjectLifecycle.ACTIVE
                and existing.object_type is obj.object_type
                and existing.object_id.split(":")[2] == slug
            ):
                raise ValueError(
                    f"ACTIVE object {existing.object_id} already uses "
                    f"({obj.object_type.value}, {slug}); route through "
                    "disambiguation + Decision Log (INV-1A-2)"
                )
        self._objects[obj.object_id] = obj
        return obj

    def get(self, object_id: str) -> CanonicalObject | None:
        return self._objects.get(object_id)

    def require(self, object_id: str) -> CanonicalObject:
        obj = self._objects.get(object_id)
        if obj is None:
            raise KeyError(f"unknown object {object_id}")
        return obj

    @property
    def objects(self) -> dict[str, CanonicalObject]:
        return dict(self._objects)

    # -- ticker discipline --------------------------------------------------

    def find_by_ticker(self, symbol: str) -> list[CanonicalObject]:
        """Ticker lookup returns *candidates*, never a unique identity.

        Sharing a ticker must never merge objects (Constitution §8.1).
        """
        hits: list[CanonicalObject] = []
        for obj in self._objects.values():
            for t in obj.ticker_symbols:
                if t.symbol == symbol:
                    hits.append(obj)
                    break
        return hits

    # -- deployment / realization attachment ---------------------------------

    def attach_deployment(self, object_id: str, deployment: DeploymentIdentity) -> None:
        obj = self.require(object_id)
        self._require_chain_object(deployment.chain)
        obj.deployments = obj.deployments + (deployment,)

    def attach_realization(self, object_id: str, realization: RealizationIdentity) -> None:
        """Attach a realization to its canonical asset object.

        Enforces INV-1A-9 (asset-class target; no realization chains) and
        INV-1A-11 (migration lineage: no self-migration, no cycles, coherent
        lineage pointers) at write time — fail-closed, not test-side.
        """
        obj = self.require(object_id)
        if obj.object_type is ObjectType.REALIZATION:
            raise ValueError(
                "a realization may never serve as another realization's canonical "
                "asset (INV-1A-9: no realization chains)"
            )
        if obj.object_type not in ObjectType.asset_classes():
            raise ValueError(
                f"canonical asset must be an asset-class object, got "
                f"{obj.object_type.value}"
            )
        if realization.canonical_asset_id != object_id:
            raise ValueError(
                "realization.canonical_asset_id must reference the attaching object"
            )
        self._require_chain_object(realization.chain_id)
        self._validate_migration_lineage(realization, obj)
        obj.realizations = obj.realizations + (realization,)

    def _validate_migration_lineage(
        self, realization: RealizationIdentity, obj: CanonicalObject
    ) -> None:
        """INV-1A-11 fail-closed enforcement over ALL realizations of this
        canonical asset (existing + the one being attached)."""
        rid = realization.realization_id
        if realization.migration_from == rid:
            raise ValueError(
                f"self-migration invalid: {rid} declares migration_from itself "
                "(INV-1A-11)"
            )
        if realization.migration_to == rid:
            raise ValueError(
                f"self-migration invalid: {rid} declares migration_to itself "
                "(INV-1A-11)"
            )
        # build lineage graph over existing siblings + the candidate
        lineage: dict[str, str | None] = {
            r.realization_id: r.migration_to for r in obj.realizations
        }
        for r in obj.realizations:
            if r.realization_id == rid:
                raise ValueError(
                    f"realization {rid} already attached (minted once)"
                )
        if realization.migration_from is not None:
            lineage[realization.migration_from] = rid
        if realization.migration_to is not None:
            lineage[rid] = realization.migration_to
        elif rid not in lineage:
            lineage[rid] = None
        # incoherence: X declares migration_to=Y but Y declares migration_from=Z
        # (checked over existing siblings AND the incoming realization, incl.
        # lineage the candidate introduces toward already-attached targets)
        known: dict[str, RealizationIdentity] = {
            r.realization_id: r for r in obj.realizations
        }
        if rid not in known and (
            realization.migration_from or realization.migration_to
        ):
            known[rid] = realization
        for x_id, x in known.items():
            if x.migration_to is None:
                continue
            target = known.get(x.migration_to)
            if target is not None and (
                target.migration_from is not None
                and target.migration_from != x_id
            ):
                raise ValueError(
                    f"incoherent lineage: {x_id} -> {x.migration_to}, but the "
                    f"target declares migration_from={target.migration_from} "
                    "(INV-1A-11)"
                )
            # also: target with migration_from but the declared predecessor
            # never points at it
            if target is None and x.migration_to is not None:
                for other_id, other in known.items():
                    if (
                        other.migration_from == x.migration_to
                        and other_id != x_id
                    ):
                        raise ValueError(
                            f"incoherent lineage: {x_id} declares "
                            f"migration_to={x.migration_to}, but "
                            f"{other_id} also declares that id as its own "
                            "migration_from source (INV-1A-11)"
                        )
        # cycle detection over the lineage graph
        for start in list(lineage):
            seen: set[str] = set()
            node: str | None = start
            while node is not None and node in lineage:
                if node in seen:
                    raise ValueError(
                        f"migration lineage cycle detected at {node} starting "
                        f"from {start} (INV-1A-11: lineage must be acyclic)"
                    )
                seen.add(node)
                node = lineage[node]


    def _require_chain_object(self, chain_id: str) -> None:
        chain = self._objects.get(chain_id)
        if chain is None:
            raise KeyError(f"unknown chain object {chain_id} (INV-1A-3)")
        if chain.object_type not in (ObjectType.BLOCKCHAIN, ObjectType.LEDGER):
            raise ValueError(
                f"{chain_id} is {chain.object_type.value}, not a chain object "
                "(deployments/realizations must reference chains by object_id)"
            )

    # -- lifecycle / merge ----------------------------------------------------

    def apply_rebrand(
        self,
        object_id: str,
        new_name: str,
        new_tickers: tuple[TickerSymbol, ...] = (),
        *,
        at: datetime,
    ) -> CanonicalObject:
        """Public rebrand operation (Constitution v0.2 §8.3, plan §1A.7 rule 4).

        The identity is immutable: the SAME object_id keeps its referent. The
        rebrand closes the prior name/ticker windows at ``at`` and adds the
        old canonical_name to ``aliases`` as a HISTORICAL window (§8.3: "a
        rebrand changes canonical_name and adds the old name to aliases").
        History is retained, never destroyed; the object is never replaced.

        Fail-closed (hardening R2): rejects naive timestamps, ``at`` before
        the object's valid_from or an open ticker window's valid_from, same
        name rebrands, and a second rebrand at an instant already used as a
        rebrand/closure instant (ambiguous history).
        """
        at = _require_aware(at, "rebrand instant")
        obj = self.require(object_id)
        start = _bound_start(obj.valid_from)
        if start is not None and at < start:
            raise ValueError(
                f"rebrand instant {at.isoformat()} precedes object valid_from "
                f"{start.isoformat()} (IR-6): would create a window before the "
                "object existed"
            )
        if new_name == obj.canonical_name:
            raise ValueError(
                f"rebrand to the same canonical name {new_name!r} is not a "
                "rebrand: it would mint a zero-length alias window"
            )
        for t in obj.ticker_symbols:
            if t.valid_to is None:
                t_start = _bound_start(t.valid_from)
                if t_start is not None and at < t_start:
                    raise ValueError(
                        f"rebrand instant precedes open ticker window "
                        f"{t.symbol!r} valid_from {t_start.isoformat()} (IR-6)"
                    )
        if any(
            a.name == new_name and _bound_end(a.valid_to) is None
            for a in obj.aliases
        ):
            raise ValueError(
                f"{new_name!r} already exists as an open alias window; "
                "contradictory name history (INV-1A-5)"
            )
        if at in self._rebrand_instants.get(object_id, ()):
            raise ValueError(
                f"a rebrand at {at.isoformat()} is already committed history "
                "for this object: an ambiguous same-instant rebrand is "
                "rejected (fail-closed)"
            )
        for t in new_tickers:
            t_start = _bound_start(t.valid_from)
            if t_start is None or t_start < at:
                raise ValueError(
                    f"new ticker {t.symbol!r} valid_from must be >= the "
                    "rebrand instant (no silent backdating)"
                )
        # close prior windows and retain the old name as alias history (§8.3)
        closed_tickers = tuple(
            t if t.valid_to is not None else _replace_validated(t, {"valid_to": at})
            for t in obj.ticker_symbols
        )
        old_alias = Alias(
            name=obj.canonical_name,
            valid_from=obj.valid_from,
            valid_to=at,
            name_state="HISTORICAL",
        )
        obj.aliases = obj.aliases + (old_alias,)
        obj.canonical_name = new_name
        obj.ticker_symbols = closed_tickers + new_tickers
        instants = self._rebrand_instants.setdefault(object_id, ())
        self._rebrand_instants[object_id] = instants + (at,)
        return obj

    def close_realization(
        self, asset_object_id: str, realization_id: str, at: datetime
    ) -> RealizationIdentity:
        """Public closure operation (INV-1A-10): sets status=CLOSED and
        valid_to=at on the named realization as a world-change. The closed
        realization remains in the graph, queryable forever; all other
        realizations are untouched.

        Fail-closed (hardening R2): model_copy skips validators, so the new
        state is built through ``_replace_validated`` — full model
        revalidation — and additionally rejects naive timestamps, closure
        before valid_from (IR-6), and re-closure of an already-terminal
        (CLOSED/MIGRATED) realization.
        """
        at = _require_aware(at, "closure instant")
        obj = self.require(asset_object_id)
        updated: list[RealizationIdentity] = []
        found = False
        for r in obj.realizations:
            if r.realization_id == realization_id:
                found = True
                if r.status in (RealizationStatus.CLOSED, RealizationStatus.MIGRATED):
                    raise ValueError(
                        f"realization {realization_id} is already "
                        f"{r.status.value}: re-closure would contradict "
                        "committed history (INV-1A-10)"
                    )
                start = _bound_start(r.valid_from)
                if start is not None and at < start:
                    raise ValueError(
                        f"closure instant {at.isoformat()} precedes valid_from "
                        f"{start.isoformat()} (IR-6)"
                    )
                updated.append(
                    _replace_validated(
                        r,
                        {"status": RealizationStatus.CLOSED, "valid_to": at},
                    )
                )
            else:
                updated.append(r)
        if not found:
            raise KeyError(
                f"realization {realization_id} not attached to {asset_object_id}"
            )
        obj.realizations = tuple(updated)
        return next(r for r in obj.realizations if r.realization_id == realization_id)

    def deprecate(self, object_id: str, at: datetime | None = None) -> None:
        """Lifecycle transition — never a deletion (INV-1A-4).

        Fail-closed (hardening R2): rejects naive timestamps, instants before
        the object's valid_from (IR-6), and repeat deprecation (the valid_to
        world-change is already committed history).
        """
        obj = self.require(object_id)
        if at is not None:
            at = _require_aware(at, "deprecation instant")
            if obj.valid_to is not None:
                raise ValueError(
                    f"{object_id} already carries valid_to: re-deprecation "
                    "would contradict committed history (INV-1A-4)"
                )
            start = _bound_start(obj.valid_from)
            if start is not None and at < start:
                raise ValueError(
                    f"deprecation instant {at.isoformat()} precedes valid_from "
                    f"{start.isoformat()} (IR-6)"
                )
            obj.valid_to = at
        obj.lifecycle_state = ObjectLifecycle.DEPRECATED

    def mark_historical(self, object_id: str) -> None:
        obj = self.require(object_id)
        obj.lifecycle_state = ObjectLifecycle.HISTORICAL

    def record_resolution_event(self, event: IdentityResolutionEvent) -> None:
        self._resolution_events.append(event)

    @property
    def resolution_events(self) -> tuple[IdentityResolutionEvent, ...]:
        return tuple(self._resolution_events)


def _bound_start(value: Timestamp | UnknownBound) -> datetime | None:
    if isinstance(value, UnknownBound):
        return value.earliest_bound
    return value


def _bound_end(value: Timestamp | UnknownBound | None) -> datetime | None:
    if value is None or isinstance(value, UnknownBound):
        return None
    return value


__all__ = [
    "OPEN",
    "Alias",
    "CanonicalObject",
    "DeploymentIdentity",
    "DeploymentMarkerKind",
    "DeploymentStatus",
    "IdentityRegistry",
    "IdentityResolutionEvent",
    "ObjectType",
    "RealizationIdentity",
    "RealizationRoute",
    "RepresentationMechanism",
    "RouteHop",
    "TickerSymbol",
    "ObjectLifecycle",
    "mint_deployment_id",
    "mint_object_id",
    "mint_realization_id",
    "utc_now",
]
