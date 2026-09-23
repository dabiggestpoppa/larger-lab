"""CSIA Book 1 — Bloc 1C: Relationship ontology + hyperedge kernel.

Implements the ratified edge dictionary (plan v0.3 §1C.6, standing on plan
v0.1's full template: definition / direction / domain / range / inverse /
temporal class), the invalid-relationship rules IR-1..IR-13, the hyperedge
primitive with participant roles and route_attributes (E-8 / C-3), and the
pairwise-flattening prohibition (IR-9).

Ratified names only. A missing edge discovered during implementation is a
*contract gap*, not an invitation to invent vocabulary (build mandate §7).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identity import ObjectType
from .temporal import (
    ClaimBinding,
    Timestamp,
    TemporalRecord,
    UnknownBound,
)


class SecurityMechanism(str, Enum):
    """SECURED_BY mechanism enum (E-1 / C-1) — mandatory on every security edge."""

    POW = "POW"
    POS = "POS"
    DPOS = "DPOS"
    BFT_FAMILY = "BFT_FAMILY"
    THRESHOLD_BFT = "THRESHOLD_BFT"
    HYBRID = "HYBRID"
    FEDERATED = "FEDERATED"
    OTHER = "OTHER"  # requires defining_string


class RouteMechanism(str, Enum):
    """route_attributes.mechanism family typing (E-8 / C-3)."""

    IBC_CHANNEL = "IBC_CHANNEL"
    CHAIN_KEY = "CHAIN_KEY"
    LOCK_MINT = "LOCK_MINT"
    LIGHT_CLIENT = "LIGHT_CLIENT"
    OTHER = "OTHER"


class ChainScopeKind(str, Enum):
    """RUNS_ON / VALIDATED_BY chain_scope attribute (E-10 / C-4)."""

    CHAIN = "CHAIN"
    SUBNET = "SUBNET"
    SHARD = "SHARD"
    PARTITION = "PARTITION"


class ChainScope(BaseModel):
    """chain_scope value: CHAIN, or a sub-object reference (family-scoped scope
    objects are owned by Book 3B; here they are referenced by object_id)."""

    model_config = ConfigDict(extra="forbid")

    kind: ChainScopeKind
    scope_ref: str | None = None  # required for SUBNET/SHARD/PARTITION

    @model_validator(mode="after")
    def _ref_rules(self) -> "ChainScope":
        if self.kind is ChainScopeKind.CHAIN:
            if self.scope_ref is not None:
                raise ValueError("CHAIN scope carries no scope_ref")
        elif not self.scope_ref:
            raise ValueError(f"{self.kind.value} scope requires scope_ref")
        return self


class RouteAttributes(BaseModel):
    """Generic route_attributes group on route-bearing hyperedges (E-8 / C-3).

    The attribute GROUP is contractual in Book 1; VALUE population is Book
    3B/4B. Attributes are temporal per record (INV-1C-6) — the group lives on
    a TemporalRecord, never as attribute-level time.
    """

    model_config = ConfigDict(extra="forbid")

    route_spec: str = Field(min_length=1)
    state: str | None = None
    version: str | None = None
    mechanism: RouteMechanism
    mechanism_defining_string: str | None = None

    @model_validator(mode="after")
    def _mechanism_rules(self) -> "RouteAttributes":
        if self.mechanism is RouteMechanism.OTHER:
            if not self.mechanism_defining_string:
                raise ValueError("OTHER route mechanism requires defining string")
        elif self.mechanism_defining_string is not None:
            raise ValueError("mechanism_defining_string only valid for OTHER")
        return self


class EdgeType(str, Enum):
    """Edge dictionary — ratified names only (Constitution §10.2 + plan v0.3)."""

    RUNS_ON = "RUNS_ON"
    SETTLES_TO = "SETTLES_TO"
    SECURED_BY = "SECURED_BY"
    VALIDATED_BY = "VALIDATED_BY"
    USES_VM = "USES_VM"
    USES_STANDARD = "USES_STANDARD"
    BRIDGES_TO = "BRIDGES_TO"
    MESSAGES_TO = "MESSAGES_TO"
    ORACLE_FOR = "ORACLE_FOR"
    DATA_FROM = "DATA_FROM"
    ISSUED_ON = "ISSUED_ON"
    NATIVE_TO = "NATIVE_TO"
    COLLATERAL_IN = "COLLATERAL_IN"
    LIQUIDITY_ON = "LIQUIDITY_ON"
    DEPENDS_ON = "DEPENDS_ON"
    INTEGRATES_WITH = "INTEGRATES_WITH"
    BUILT_WITH = "BUILT_WITH"
    FORKED_FROM = "FORKED_FROM"
    GOVERNED_BY = "GOVERNED_BY"
    STAKED_IN = "STAKED_IN"
    RESTAKED_IN = "RESTAKED_IN"
    ROUTED_THROUGH = "ROUTED_THROUGH"
    MIGRATED_FROM = "MIGRATED_FROM"
    MIGRATED_TO = "MIGRATED_TO"
    OWNED_BY = "OWNED_BY"
    OPERATED_BY = "OPERATED_BY"
    COMPETES_WITH = "COMPETES_WITH"
    COMPLEMENTS = "COMPLEMENTS"
    WRAPS = "WRAPS"
    REDEEMS_FOR = "REDEEMS_FOR"
    PRICES = "PRICES"
    SECURES = "SECURES"
    HOSTS = "HOSTS"  # inverse of RUNS_ON (declared in dictionary)
    HOSTS_ISSUANCE = "HOSTS_ISSUANCE"  # inverse of ISSUED_ON
    REALIZES = "REALIZES"  # R-1A-5 Option C [C-16]
    RECEIVED_VIA = "RECEIVED_VIA"  # R-1A-5 Option C [C-16]


class EdgeSpec(BaseModel):
    """One edge-dictionary entry (Constitution §10.1: no entry, no population)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    edge_type: EdgeType
    definition: str = Field(min_length=1)
    domain: frozenset[ObjectType]
    range_: frozenset[ObjectType]
    inverse: EdgeType | None = None
    temporal_class: Literal["STANDING", "EVENT"]
    requires_mechanism: bool = False  # SECURED_BY/SECURES (IR-11)
    acyclic: bool = False  # FORKED_FROM (IR-3); settlement DAG (IR-4)
    symmetric: bool = False  # COMPETES_WITH / COMPLEMENTS

    def compatible(self, subject: ObjectType, obj: ObjectType) -> bool:
        return subject in self.domain and obj in self.range_


_EDGE_SPECS: dict[EdgeType, EdgeSpec] = {}


def _spec(
    edge_type: EdgeType,
    definition: str,
    domain: tuple[ObjectType, ...],
    range_: tuple[ObjectType, ...],
    *,
    inverse: EdgeType | None = None,
    temporal_class: Literal["STANDING", "EVENT"] = "STANDING",
    requires_mechanism: bool = False,
    acyclic: bool = False,
    symmetric: bool = False,
) -> None:
    _EDGE_SPECS[edge_type] = EdgeSpec(
        edge_type=edge_type,
        definition=definition,
        domain=frozenset(domain),
        range_=frozenset(range_),
        inverse=inverse,
        temporal_class=temporal_class,
        requires_mechanism=requires_mechanism,
        acyclic=acyclic,
        symmetric=symmetric,
    )


_ASSET = (ObjectType.TOKEN, ObjectType.STABLECOIN, ObjectType.ASSET)
_CHAIN = (ObjectType.BLOCKCHAIN, ObjectType.LEDGER)
_APP = (ObjectType.PROTOCOL, ObjectType.APPLICATION)
_SYSTEM = (
    ObjectType.PROTOCOL,
    ObjectType.APPLICATION,
    ObjectType.BRIDGE,
    ObjectType.ORACLE_NETWORK,
    ObjectType.INTEROP_PROTOCOL,
    ObjectType.DATA_AVAILABILITY_NETWORK,
    ObjectType.DEX,
    ObjectType.PERP_DEX,
    ObjectType.LENDING_PROTOCOL,
    ObjectType.STAKING_PROTOCOL,
    ObjectType.RESTAKING_PROTOCOL,
    ObjectType.RWA_PROTOCOL,
    ObjectType.PAYMENT_SYSTEM,
    ObjectType.STORAGE_NETWORK,
    ObjectType.COMPUTE_NETWORK,
    ObjectType.DEPIN_NETWORK,
    ObjectType.IDENTITY_SYSTEM,
    ObjectType.PRIVACY_SYSTEM,
    ObjectType.INTENT_SOLVER_NETWORK,
    ObjectType.INSURANCE_SECURITY_PROTOCOL,
)
_ORACLE_SYS = (ObjectType.ORACLE_NETWORK,)

_spec(EdgeType.RUNS_ON, "A executes on the named chain's runtime.",
      _SYSTEM + (ObjectType.VM,), _CHAIN, inverse=EdgeType.HOSTS)
_spec(EdgeType.HOSTS, "Inverse of RUNS_ON.", _CHAIN,
      _SYSTEM + (ObjectType.VM,), inverse=EdgeType.RUNS_ON)
_spec(EdgeType.SETTLES_TO, "Final trust/security root resolves to the settlement chain.",
      _CHAIN, _CHAIN, acyclic=True)
_spec(EdgeType.SECURED_BY, "Security derived from B's validator set/economic security.",
      _CHAIN + _SYSTEM, _CHAIN + (ObjectType.VALIDATOR_SYSTEM,),
      inverse=EdgeType.SECURES, requires_mechanism=True)
_spec(EdgeType.SECURES, "Inverse of SECURED_BY (same mechanism).",
      _CHAIN + (ObjectType.VALIDATOR_SYSTEM,), _CHAIN + _SYSTEM,
      inverse=EdgeType.SECURED_BY, requires_mechanism=True)
_spec(EdgeType.VALIDATED_BY, "Blocks validated by validator system B.",
      _CHAIN, (ObjectType.VALIDATOR_SYSTEM,))
_spec(EdgeType.USES_VM, "Chain A executes VM B.", _CHAIN, (ObjectType.VM,))
_spec(EdgeType.USES_STANDARD, "A conforms to standard B.",
      _SYSTEM + _ASSET, (ObjectType.STANDARD,))
_spec(EdgeType.BRIDGES_TO, "Bridge connects to a chain it serves (one per chain).",
      (ObjectType.BRIDGE,), _CHAIN)
_spec(EdgeType.MESSAGES_TO, "Messaging layer delivers messages between chains.",
      (ObjectType.INTEROP_PROTOCOL,), _CHAIN)
_spec(EdgeType.ORACLE_FOR, "Oracle supplies price/data to consumer.",
      (ObjectType.ORACLE_NETWORK,), _SYSTEM + _CHAIN)
_spec(EdgeType.DATA_FROM, "A sources data feeds from B.",
      _SYSTEM, _SYSTEM + _ORACLE_SYS)
_spec(EdgeType.ISSUED_ON, "Token has a deployment on the named chain.",
      _ASSET, _CHAIN, inverse=EdgeType.HOSTS_ISSUANCE)
_spec(EdgeType.HOSTS_ISSUANCE, "Inverse of ISSUED_ON.", _CHAIN, _ASSET,
      inverse=EdgeType.ISSUED_ON)
_spec(EdgeType.NATIVE_TO, "Asset is native gas/settlement asset of the chain.",
      _ASSET, _CHAIN)
_spec(EdgeType.COLLATERAL_IN, "Asset accepted as collateral by system B.",
      _ASSET, _SYSTEM)
_spec(EdgeType.LIQUIDITY_ON, "Asset has tradable liquidity hosted in system B.",
      _ASSET, _SYSTEM)
_spec(EdgeType.DEPENDS_ON, "A's correct functioning requires B (operational, direct).",
      _SYSTEM, _SYSTEM + _ORACLE_SYS)
_spec(EdgeType.INTEGRATES_WITH, "A uses B's interface but functions degraded without it.",
      _SYSTEM, _SYSTEM)
_spec(EdgeType.BUILT_WITH, "A's client/implementation stack includes B.",
      _SYSTEM, _SYSTEM)
_spec(EdgeType.FORKED_FROM, "A's codebase/ledger state derives from B at a point in time.",
      _CHAIN + (ObjectType.PROTOCOL,), _CHAIN + (ObjectType.PROTOCOL,),
      temporal_class="EVENT", acyclic=True)
_spec(EdgeType.GOVERNED_BY, "A's upgrade/parameter authority is governance B.",
      _CHAIN + _SYSTEM, (ObjectType.GOVERNANCE_SYSTEM, ObjectType.ENTITY))
_spec(EdgeType.STAKED_IN, "Native asset or receipt staked in system B.",
      _ASSET, (ObjectType.STAKING_PROTOCOL, ObjectType.VALIDATOR_SYSTEM))
_spec(EdgeType.RESTAKED_IN, "Staked receipt re-secured into system B.",
      _ASSET, (ObjectType.RESTAKING_PROTOCOL,))
_spec(EdgeType.ROUTED_THROUGH, "Capital route capability exists via C between A and B.",
      _ASSET + _SYSTEM, _SYSTEM + (ObjectType.BRIDGE, ObjectType.INTEROP_PROTOCOL))
_spec(EdgeType.MIGRATED_FROM, "Object A moved its canonical deployment from B.",
      _ASSET + _SYSTEM, _CHAIN + _SYSTEM, temporal_class="EVENT")
_spec(EdgeType.MIGRATED_TO, "Object A moved its canonical deployment to B.",
      _ASSET + _SYSTEM, _CHAIN + _SYSTEM, temporal_class="EVENT")
_spec(EdgeType.OWNED_BY, "Entity-level custody.", _SYSTEM + _CHAIN,
      (ObjectType.ENTITY,))
_spec(EdgeType.OPERATED_BY, "Entity-level operation.", _SYSTEM + _CHAIN,
      (ObjectType.ENTITY,))
_spec(EdgeType.COMPETES_WITH, "A and B serve substitutable demand (E2+ evidence bar).",
      _SYSTEM, _SYSTEM, symmetric=True)
_spec(EdgeType.COMPLEMENTS, "A's use increases B's use (E2+ or INFERRED+methodology).",
      _SYSTEM, _SYSTEM, symmetric=True)
_spec(EdgeType.WRAPS, "B is a 1:1 custodial/synthetic representation of A.",
      _ASSET, _ASSET)
_spec(EdgeType.REDEEMS_FOR, "B redeems 1:1 into A at a defined facility.",
      _ASSET, _ASSET)
_spec(EdgeType.PRICES, "System A provides valuation for asset B.", _SYSTEM, _ASSET)
_spec(EdgeType.REALIZES,
      "Chain-local realization represents the canonical economic asset "
      "(R-1A-5 Option C). realization -> canonical asset.",
      (ObjectType.REALIZATION,), _ASSET)
_spec(EdgeType.RECEIVED_VIA,
      "Realization arrived via the referenced channel/route.",
      (ObjectType.REALIZATION,), _SYSTEM)


def edge_spec(edge_type: EdgeType) -> EdgeSpec:
    return _EDGE_SPECS[edge_type]


class TypedEdge(BaseModel):
    """Typed, bitemporal, evidence-bound edge."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    edge_type: EdgeType
    subject_id: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    mechanism: SecurityMechanism | None = None
    mechanism_defining_string: str | None = None
    chain_scope: ChainScope | None = None
    claim_binding: ClaimBinding
    observed_at: datetime
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None
    source_published_at: datetime | None = None
    ingested_at: datetime | None = None
    superseded_at: datetime | None = None
    supersedes: str | None = None

    @model_validator(mode="after")
    def _security_mechanism_mandatory(self) -> "TypedEdge":
        spec = edge_spec(self.edge_type)
        if spec.requires_mechanism and self.mechanism is None:
            raise ValueError(
                f"{self.edge_type.value} edges require a mechanism attribute "
                "(IR-11 / E-1)"
            )
        if self.mechanism is SecurityMechanism.OTHER:
            if not self.mechanism_defining_string:
                raise ValueError("OTHER security mechanism requires defining string")
        return self

    @model_validator(mode="after")
    def _temporal_rules(self) -> "TypedEdge":
        if self.superseded_at is not None and self.superseded_at < self.observed_at:
            raise ValueError("R3 violated: superseded_at < observed_at")
        return self


# Edge types where a self-edge is explicitly permitted (flagged WRAPS case, IR-5).
_SELF_EDGE_PERMITTED: frozenset[EdgeType] = frozenset({EdgeType.WRAPS})


class GraphValidator:
    """Validates edges against the dictionary + graph-level rules over an
    :class:`IdentityRegistry` (so domain/range checks resolve real classes).

    Acyclic edge families (EdgeSpec.acyclic: FORKED_FROM, SETTLES_TO) are
    fail-closed: an edge whose insertion would create a cycle is rejected
    BEFORE it can become graph state (IR-3/IR-4 enforced at write time).
    """

    def __init__(self, registry) -> None:  # IdentityRegistry — avoids import cycle
        self._registry = registry
        self._edges: dict[str, TypedEdge] = {}

    def add_edge(self, edge: TypedEdge) -> TypedEdge:
        spec = edge_spec(edge.edge_type)
        subj = self._registry.require(edge.subject_id)
        obj = self._registry.require(edge.object_id)
        if not spec.compatible(subj.object_type, obj.object_type):
            raise ValueError(
                f"domain/range violation: {subj.object_type.value} "
                f"-{edge.edge_type.value}-> {obj.object_type.value} not permitted "
                f"(domain={sorted(s.value for s in spec.domain)}, "
                f"range={sorted(r.value for r in spec.range_)}) (IR-1)"
            )
        if edge.subject_id == edge.object_id and edge.edge_type not in _SELF_EDGE_PERMITTED:
            raise ValueError(f"self-edge {edge.edge_type.value} invalid (IR-5)")
        if spec.acyclic and self._creates_cycle(
            edge.edge_type, edge.subject_id, edge.object_id
        ):
            raise ValueError(
                f"inserting {edge.edge_type.value} {edge.subject_id} -> "
                f"{edge.object_id} would create a cycle; acyclic edge families "
                "are fail-closed (IR-3/IR-4)"
            )
        self._edges[edge.edge_id] = edge
        return edge

    def _creates_cycle(self, edge_type: EdgeType, subject: str, obj: str) -> bool:
        """Would adding subject -> obj introduce a cycle in this edge family?
        A cycle exists iff obj can already reach subject via existing edges."""
        adj: dict[str, list[str]] = {}
        for e in self._edges.values():
            if e.edge_type is edge_type:
                adj.setdefault(e.subject_id, []).append(e.object_id)
        # BFS from obj looking for subject
        queue, seen = [obj], {obj}
        while queue:
            node = queue.pop()
            if node == subject:
                return True
            for nxt in adj.get(node, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return False

    def edge(self, edge_id: str) -> TypedEdge:
        return self._edges[edge_id]

    @property
    def edges(self) -> dict[str, TypedEdge]:
        return dict(self._edges)

    def validate_acyclic(self, edge_type: EdgeType) -> bool:
        """Audit method (kept per hardening R1): full-graph DFS check that an
        acyclic-declared family currently forms a DAG. Insertion-time
        enforcement (add_edge) is the primary guarantee."""
        spec = edge_spec(edge_type)
        if not spec.acyclic:
            return True
        adj: dict[str, list[str]] = {}
        for e in self._edges.values():
            if e.edge_type is edge_type:
                adj.setdefault(e.subject_id, []).append(e.object_id)
        state: dict[str, int] = {}

        def visit(node: str) -> bool:
            if state.get(node) == 1:
                return False
            if state.get(node) == 2:
                return True
            state[node] = 1
            for nxt in adj.get(node, ()):  # DFS cycle detection
                if not visit(nxt):
                    return False
            state[node] = 2
            return True

        return all(visit(n) for n in list(adj))


class HyperedgeRole(str, Enum):
    """Initial hyperedge participant roles (plan v0.1 §1C.6 registry)."""

    ISSUER = "ISSUER"
    HOST_CHAIN = "HOST_CHAIN"
    SETTLEMENT_CHAIN = "SETTLEMENT_CHAIN"
    BRIDGE = "BRIDGE"
    CHAIN_A = "CHAIN_A"
    CHAIN_B = "CHAIN_B"
    ASSET = "ASSET"
    PROVIDER_CHAIN = "PROVIDER_CHAIN"
    CONSUMER_CHAIN = "CONSUMER_CHAIN"
    MECHANISM = "MECHANISM"
    ORACLE = "ORACLE"
    DATA_PUBLISHER = "DATA_PUBLISHER"
    CONSUMER = "CONSUMER"
    CHAIN = "CHAIN"
    VENUE = "VENUE"
    COLLATERAL_SITE = "COLLATERAL_SITE"


class HyperedgeClass(str, Enum):
    """Initial hyperedge registry — multi-party facts not losslessly
    decomposable into pairwise edges (Constitution §11.1)."""

    HE_ISSUANCE = "HE-ISSUANCE"
    HE_BRIDGE_ROUTE = "HE-BRIDGE-ROUTE"
    HE_COLLATERAL_LOOP = "HE-COLLATERAL-LOOP"
    HE_SECURITY_SHARE = "HE-SECURITY-SHARE"
    HE_ORACLE_DELIVERY = "HE-ORACLE-DELIVERY"


_HYPEREDGE_REQUIRED_ROLES: dict[HyperedgeClass, frozenset[HyperedgeRole]] = {
    HyperedgeClass.HE_ISSUANCE: frozenset(
        {HyperedgeRole.ISSUER, HyperedgeRole.HOST_CHAIN, HyperedgeRole.ASSET}
    ),
    HyperedgeClass.HE_BRIDGE_ROUTE: frozenset(
        {HyperedgeRole.BRIDGE, HyperedgeRole.CHAIN_A, HyperedgeRole.CHAIN_B}
    ),
    HyperedgeClass.HE_COLLATERAL_LOOP: frozenset(
        {HyperedgeRole.ASSET, HyperedgeRole.VENUE, HyperedgeRole.COLLATERAL_SITE}
    ),
    HyperedgeClass.HE_SECURITY_SHARE: frozenset(
        {
            HyperedgeRole.PROVIDER_CHAIN,
            HyperedgeRole.CONSUMER_CHAIN,
            HyperedgeRole.MECHANISM,
        }
    ),
    HyperedgeClass.HE_ORACLE_DELIVERY: frozenset(
        {HyperedgeRole.ORACLE, HyperedgeRole.CONSUMER, HyperedgeRole.CHAIN}
    ),
}


class Hyperedge(TemporalRecord):
    """Atomic multi-party fact with declared per-participant roles.

    - role coverage mandatory (INV-1C-5);
    - HE-BRIDGE-ROUTE must carry route_attributes at canonical state (IR-12);
    - pairwise projections are derived views only (IR-9) — this class has no
      decomposition-to-edges method by contract.
    """

    model_config = ConfigDict(extra="forbid")

    hyperedge_id: str = Field(min_length=1)
    hyperedge_class: HyperedgeClass
    participants: dict[HyperedgeRole, str]  # role -> object_id
    route_attributes: RouteAttributes | None = None
    claim_binding: ClaimBinding

    @model_validator(mode="after")
    def _role_coverage(self) -> "Hyperedge":
        required = _HYPEREDGE_REQUIRED_ROLES[self.hyperedge_class]
        missing = required - frozenset(self.participants)
        if missing:
            raise ValueError(
                f"hyperedge {self.hyperedge_class.value} missing required roles: "
                f"{sorted(m.value for m in missing)} (INV-1C-5)"
            )
        if (
            self.hyperedge_class is HyperedgeClass.HE_BRIDGE_ROUTE
            and self.route_attributes is None
        ):
            raise ValueError(
                "HE-BRIDGE-ROUTE requires route_attributes at canonical state "
                "(IR-12 / E-8)"
            )
        return self

    def pairwise_projection(self) -> list[tuple[HyperedgeRole, str]]:
        """DERIVED VIEW for consumers (IR-9): participant list explicitly
        labelled as a projection — never stored as edges."""

        return sorted(self.participants.items(), key=lambda kv: kv[0].value)


__all__ = [
    "ChainScope",
    "ChainScopeKind",
    "EdgeSpec",
    "EdgeType",
    "GraphValidator",
    "Hyperedge",
    "HyperedgeClass",
    "HyperedgeRole",
    "RouteAttributes",
    "RouteMechanism",
    "SecurityMechanism",
    "TypedEdge",
    "edge_spec",
]
