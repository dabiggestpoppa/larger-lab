"""Relationship + EntityRef — the durable capability-graph edge model.

Canon Book I 1.3:

- Entities and relationships are stored separately (1.3.2).
- Relationships use the controlled vocabulary (1.3.4); no arbitrary prose types.
- Direction matters; ambiguous symmetric edges are avoided (1.3.5).
- Analysis-originated edges carry a VerificationLevel so claimed and verified
  edges stay distinguishable (1.3.6, 1.3.13).
- Edges are revision-scoped: a relationship may be true only for a revision
  range (1.3.12).
- Endpoint roles are enforced against the vocabulary so an impossible edge
  ("paper implements atom" as a source-container claim, etc.) is rejected at
  construction time.

Entities referenced by stable internal ID via EntityRef (1.3.16).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
)
from qcae.core.vocabulary import VerificationLevel


class EntityType(StrEnum):
    """Core entity classes (canon 1.3.3). P0 ships the graph-relevant subset."""

    NEED = "NEED"
    CAPABILITY_CONTRACT = "CAPABILITY_CONTRACT"
    CAPABILITY_ATOM = "CAPABILITY_ATOM"
    COMPOSITE_CAPABILITY = "COMPOSITE_CAPABILITY"
    IMPLEMENTATION_CANDIDATE = "IMPLEMENTATION_CANDIDATE"
    COMPONENT = "COMPONENT"
    REPOSITORY = "REPOSITORY"
    PACKAGE = "PACKAGE"
    SERVICE = "SERVICE"
    SPECIFICATION = "SPECIFICATION"
    PAPER = "PAPER"
    INTERFACE = "INTERFACE"
    DATASET = "DATASET"
    TEST_DEFINITION = "TEST_DEFINITION"
    TEST_RUN = "TEST_RUN"
    BENCHMARK_RUN = "BENCHMARK_RUN"
    EVIDENCE_ARTIFACT = "EVIDENCE_ARTIFACT"
    ACQUISITION_DECISION = "ACQUISITION_DECISION"
    INTEGRATION = "INTEGRATION"
    POLICY_DECISION = "POLICY_DECISION"
    RISK_FINDING = "RISK_FINDING"


class RelationType(StrEnum):
    """Controlled relationship vocabulary (canon 1.3.4)."""

    REQUESTED_BY = "requested_by"
    NORMALIZED_AS = "normalized_as"
    COMPOSED_OF = "composed_of"
    IMPLEMENTS = "implements"
    PARTIALLY_IMPLEMENTS = "partially_implements"
    CONTAINED_IN = "contained_in"
    EXPOSED_THROUGH = "exposed_through"
    DEPENDS_ON = "depends_on"
    OPTIONAL_DEPENDENCY_ON = "optional_dependency_on"
    CONFLICTS_WITH = "conflicts_with"
    SUBSTITUTES_FOR = "substitutes_for"
    EXTENDS = "extends"
    SUPERSEDES = "supersedes"
    WRAPS = "wraps"
    VENDORS = "vendors"
    FORKED_FROM = "forked_from"
    EXTRACTED_FROM = "extracted_from"
    DERIVED_FROM = "derived_from"
    SPECIFIED_BY = "specified_by"
    DESCRIBED_BY = "described_by"
    VALIDATED_BY = "validated_by"
    TESTED_BY = "tested_by"
    BENCHMARKED_BY = "benchmarked_by"
    OBSERVED_IN = "observed_in"
    REQUIRES_DATA = "requires_data"
    PRODUCES_DATA = "produces_data"
    COMPATIBLE_WITH = "compatible_with"
    INCOMPATIBLE_WITH = "incompatible_with"
    INTEGRATED_AS = "integrated_as"
    APPROVED_BY = "approved_by"
    REJECTED_BY = "rejected_by"
    TRIGGERED_REVALIDATION_OF = "triggered_revalidation_of"


@dataclass(frozen=True)
class EntityRef(SerializableRecord):
    """A typed reference to a graph entity by stable internal ID (canon 1.3.16)."""

    SCHEMA_VERSION = 1

    entity_type: EntityType
    entity_id: str

    _COERCIONS = {"entity_type": lambda v: coerce_enum(v, EntityType)}

    def validate(self) -> None:
        if not isinstance(self.entity_type, EntityType):
            raise QcaeValidationError(
                f"entity_type must be an EntityType member, got {self.entity_type!r}"
            )
        require_identifier(self.entity_id, "entity_id")


@dataclass(frozen=True)
class Relationship(SerializableRecord):
    """A typed, directed, revision-scoped edge between two graph entities."""

    SCHEMA_VERSION = 1

    source: EntityRef
    relation: RelationType
    target: EntityRef

    # Verification label: how far this assertion has been independently
    # supported (canon 1.3.13). Never collapsed to a bare boolean.
    verification: VerificationLevel = VerificationLevel.DISCOVERED

    # Revision scoping (canon 1.3.12): the edge may hold only for the given
    # revision(s); empty means not revision-scoped.
    source_revision: str = ""
    target_revision: str = ""

    # Evidence linkage: digests of EvidenceArtifacts supporting this edge.
    evidence_digests: Tuple[str, ...] = ()

    asserted_by: str = ""
    asserted_at: str = ""

    _NESTED_RECORDS = {"source": EntityRef, "target": EntityRef}
    _COERCIONS = {
        "relation": lambda v: coerce_enum(v, RelationType),
        "verification": lambda v: coerce_enum(v, VerificationLevel),
    }

    def validate(self) -> None:
        self.source.validate()
        self.target.validate()
        if not isinstance(self.relation, RelationType):
            raise QcaeValidationError(
                f"relation must be a RelationType member (controlled vocabulary, "
                f"canon 1.3.4), got {self.relation!r}"
            )
        if not isinstance(self.verification, VerificationLevel):
            raise QcaeValidationError(
                f"verification must be a VerificationLevel member, got {self.verification!r}"
            )

        _validate_endpoint_roles(self.relation, self.source.entity_type, self.target.entity_type)

        for digest in self.evidence_digests:
            if not isinstance(digest, str) or len(digest) < 8:
                raise QcaeValidationError(
                    f"evidence_digests entries must be content digests, got {digest!r}"
                )
        if self.asserted_by:
            require_non_empty_str(self.asserted_by, "asserted_by")
        if self.asserted_at and not isinstance(self.asserted_at, str):
            raise QcaeValidationError("asserted_at must be a string timestamp")


def _validate_endpoint_roles(
    relation: RelationType, source_type: EntityType, target_type: EntityType
) -> None:
    """Reject edges whose endpoint entity types contradict the relation's meaning.

    Direction matters (canon 1.3.5); these are the semantically load-bearing
    constraints for the graph's core edges. Deliberately conservative: types
    not listed are unrestricted pending canon refinement.
    """
    src = source_type
    dst = target_type

    if relation == RelationType.IMPLEMENTS:
        # Candidates/components implement atoms or capabilities — not the reverse.
        if src not in (EntityType.IMPLEMENTATION_CANDIDATE, EntityType.COMPONENT):
            raise QcaeValidationError(
                f"{relation} source must be an implementation/component, got {src}"
            )
        if dst not in (
            EntityType.CAPABILITY_ATOM,
            EntityType.COMPOSITE_CAPABILITY,
            EntityType.CAPABILITY_CONTRACT,
        ):
            raise QcaeValidationError(
                f"{relation} target must be an atom/capability, got {dst}"
            )
    elif relation == RelationType.COMPOSED_OF:
        if src not in (
            EntityType.COMPOSITE_CAPABILITY,
            EntityType.CAPABILITY_CONTRACT,
        ):
            raise QcaeValidationError(
                f"{relation} source must be a composite capability/contract, got {src}"
            )
        if dst != EntityType.CAPABILITY_ATOM:
            raise QcaeValidationError(
                f"{relation} target must be a capability atom, got {dst}"
            )
    elif relation == RelationType.CONTAINED_IN:
        if src not in (EntityType.COMPONENT, EntityType.PACKAGE):
            raise QcaeValidationError(
                f"{relation} source must be a component/package, got {src}"
            )
        if dst != EntityType.REPOSITORY:
            raise QcaeValidationError(
                f"{relation} target must be a repository, got {dst}"
            )
    elif relation == RelationType.DEPENDS_ON:
        if dst not in (EntityType.PACKAGE, EntityType.SERVICE):
            raise QcaeValidationError(
                f"{relation} target must be a package or service, got {dst}"
            )
    elif relation == RelationType.NORMALIZED_AS:
        if src != EntityType.NEED:
            raise QcaeValidationError(f"{relation} source must be a NEED, got {src}")
        if dst not in (EntityType.CAPABILITY_CONTRACT,):
            raise QcaeValidationError(
                f"{relation} target must be a capability contract, got {dst}"
            )
    elif relation == RelationType.SUPERSEDES:
        if src != dst:
            raise QcaeValidationError(
                f"{relation} endpoints must be the same entity type, got {src} -> {dst}"
            )


def make_relationship(**kwargs) -> Relationship:
    """Build and validate a relationship in one call."""
    relationship = Relationship(**kwargs)
    relationship.validate()
    return relationship
