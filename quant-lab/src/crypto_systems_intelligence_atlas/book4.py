"""Public Book 4 offline kernel facade; no persistence, acquisition, or Book 5."""

from .book4_boundary import (
    BOOK4_DEPENDENCY_RELATION_ALLOWLIST,
    BOOK4ScopeError,
    BOOK5_ECONOMIC_RELATIONS,
    Book4RelationSupportPolicy,
    assert_book4_technical_scope,
)
from .dependency import (
    DependencyBook,
    DependencyClass,
    DependencyRecord,
    DependencyStrengthDescriptor,
    DependencyStrengthState,
    FallbackState,
    HardRuntimeEvidence,
    HardRuntimeGate,
    RuntimeAssessment,
    RuntimeScope,
)
from .dependency_paths import (
    DependencyPath,
    DependencyPathBook,
    DerivedTransitiveDependency,
    PathRelation,
)
from .dependency_provenance import Book4Provenance, Book4ProvenanceError
from .dependency_relations import (
    Book4RelationProjector,
    FORBIDDEN_BOOK4_ADDITIONS,
    OracleDeliveryHyperedgeFactory,
    RelationProjection,
)
from .failure_domains import (
    FailureDomain,
    FailureDomainAssessment,
    FailureDomainBook,
    FailureDomainClassification,
    FailureDomainType,
)
from .infrastructure_context import InfrastructureContext, InfrastructureContextBook
from .offline_pilots import OFFLINE_PILOTS, OfflinePilotFixture
from .protocol_roles import ProtocolRole, ProtocolRoleBook, RoleAssignment, RoleState
from .redundancy import (
    ActivationMode,
    RedundancyAssessment,
    RedundancyBook,
    RedundancyState,
)
from .substitutability import (
    ChangeClass,
    SubstitutabilityAssessment,
    SubstitutabilityBook,
    SubstitutabilityDirection,
)

__all__ = [
    "ActivationMode",
    "BOOK4_DEPENDENCY_RELATION_ALLOWLIST",
    "BOOK4ScopeError",
    "BOOK5_ECONOMIC_RELATIONS",
    "Book4Provenance",
    "Book4RelationSupportPolicy",
    "Book4ProvenanceError",
    "Book4RelationProjector",
    "ChangeClass",
    "DependencyBook",
    "DependencyClass",
    "DependencyPath",
    "DependencyPathBook",
    "DependencyRecord",
    "DependencyStrengthDescriptor",
    "DependencyStrengthState",
    "DerivedTransitiveDependency",
    "FORBIDDEN_BOOK4_ADDITIONS",
    "FallbackState",
    "FailureDomain",
    "FailureDomainAssessment",
    "FailureDomainBook",
    "FailureDomainClassification",
    "FailureDomainType",
    "HardRuntimeEvidence",
    "HardRuntimeGate",
    "InfrastructureContext",
    "InfrastructureContextBook",
    "OFFLINE_PILOTS",
    "OracleDeliveryHyperedgeFactory",
    "OfflinePilotFixture",
    "PathRelation",
    "ProtocolRole",
    "ProtocolRoleBook",
    "RedundancyAssessment",
    "RedundancyBook",
    "RedundancyState",
    "RelationProjection",
    "RoleAssignment",
    "RoleState",
    "RuntimeAssessment",
    "RuntimeScope",
    "SubstitutabilityAssessment",
    "SubstitutabilityBook",
    "SubstitutabilityDirection",
    "assert_book4_technical_scope",
]
