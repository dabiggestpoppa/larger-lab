"""CSIA Book 1 — package kernel exports.

Book 1 implementation (ratified plan v0.3):
- Bloc 1A canonical identity (``identity``)
- Bloc 1B node ontology (``ontology``)
- Bloc 1C relationships + hyperedges (``relationships``)
- Bloc 1D bitemporal model (``temporal``)

Planning authority: Constitution v0.2 RATIFIED + Book 1 plan v0.3 RATIFIED
(operator authorization 2026-09-23). Implementation authority is kernel-scope
only; no collectors, no persistence engines, no Book 2+ scope.
"""

from .identity import (
    Alias,
    CanonicalObject,
    DeploymentIdentity,
    DeploymentMarkerKind,
    DeploymentStatus,
    IdentityRegistry,
    IdentityResolutionEvent,
    ObjectType,
    RealizationIdentity,
    RealizationRoute,
    RepresentationMechanism,
    RouteHop,
    TickerSymbol,
    mint_deployment_id,
    mint_object_id,
    mint_realization_id,
)
from .ontology import (
    ArchitectureSlot,
    FamilySlotRegistry,
    RoleTag,
    role_tag,
)
from .relationships import (
    ChainScope,
    ChainScopeKind,
    EdgeSpec,
    EdgeType,
    GraphValidator,
    Hyperedge,
    HyperedgeClass,
    HyperedgeRole,
    RouteAttributes,
    RouteMechanism,
    SecurityMechanism,
    TypedEdge,
    edge_spec,
)
from .temporal import (
    OPEN,
    ClaimBinding,
    ObjectLifecycle,
    RealizationStatus,
    RecordLifecycle,
    RecordStore,
    TemporalRecord,
    UnknownBound,
    holds_at,
    normalize_utc,
    utc_now,
)

__version__ = "0.3.0"

__all__ = [
    "OPEN",
    "Alias",
    "ArchitectureSlot",
    "CanonicalObject",
    "ChainScope",
    "ChainScopeKind",
    "ClaimBinding",
    "DeploymentIdentity",
    "DeploymentMarkerKind",
    "DeploymentStatus",
    "EdgeSpec",
    "EdgeType",
    "FamilySlotRegistry",
    "GraphValidator",
    "Hyperedge",
    "HyperedgeClass",
    "HyperedgeRole",
    "IdentityRegistry",
    "IdentityResolutionEvent",
    "ObjectLifecycle",
    "ObjectType",
    "RealizationIdentity",
    "RealizationRoute",
    "RealizationStatus",
    "RecordLifecycle",
    "RecordStore",
    "RepresentationMechanism",
    "RoleTag",
    "RouteAttributes",
    "RouteHop",
    "RouteMechanism",
    "SecurityMechanism",
    "TemporalRecord",
    "TickerSymbol",
    "TypedEdge",
    "UnknownBound",
    "edge_spec",
    "holds_at",
    "mint_deployment_id",
    "mint_object_id",
    "mint_realization_id",
    "normalize_utc",
    "role_tag",
    "utc_now",
]
