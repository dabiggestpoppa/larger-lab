"""RegistryService facade (P1-R1 §8).

One service wiring the capability, repository, and relationship stores so
later phases link containers to capabilities without collapsing identities:

- repository revision IMPLEMENTS capability atom  — via the frozen P0
  ``Relationship`` graph (canon 1.3.4), revision-scoped (1.3.12);
- candidate DERIVED FROM / CONTAINED IN repository revision — canon types;
- composite COMPOSED OF atom — canon type.

No duplicate graph machinery: the P0 model is authoritative for edge
semantics; this facade only persists and retrieves it.
"""

from __future__ import annotations

from typing import List, Tuple

from qcae.core.capabilities.candidate import CandidateSourceKind
from qcae.core.errors import QcaeValidationError
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.relationships.graph import (
    EntityType,
    Relationship,
    RelationType,
    VerificationLevel,
    make_relationship,
)
from qcae.core.ports.relationship_registry import RelationshipPersistencePort

__all__ = ["RegistryService"]


def _entity_type_for_candidate(source_kind) -> EntityType:
    """Map a candidate's source kind to its canon graph entity type."""
    mapping = {
        CandidateSourceKind.INTERNAL_CODE: EntityType.COMPONENT,
        CandidateSourceKind.REPOSITORY: EntityType.COMPONENT,
        CandidateSourceKind.PACKAGE: EntityType.PACKAGE,
        CandidateSourceKind.SERVICE: EntityType.SERVICE,
        CandidateSourceKind.SPECIFICATION: EntityType.SPECIFICATION,
        CandidateSourceKind.PAPER: EntityType.PAPER,
    }
    try:
        return mapping[source_kind]
    except KeyError as exc:
        raise QcaeValidationError(
            f"no graph entity type for candidate source kind {source_kind}"
        ) from exc


class RegistryService:
    def __init__(self, relationships: RelationshipPersistencePort) -> None:
        self._relationships = relationships

    # -- write paths ---------------------------------------------------------

    def repository_implements_atom(
        self,
        repository: RepositoryRecord,
        atom_id: str,
        verification: VerificationLevel = VerificationLevel.DISCOVERED,
        asserted_by: str = "",
        asserted_at: str = "",
    ) -> Relationship:
        """A repository revision implements a capability atom (revision-scoped).

        Repository->atom IMPLEMENTS is not a canon-permitted endpoint pair
        (IMPLEMENTS sources are implementations/components), so the canonical
        encoding is: this repository record's revision is where an implementing
        component lives; the edge itself runs repository-as-COMPONENT. To stay
        strictly canon-conformant we record the edge from the repository under
        the COMPONENT entity class *only* when the repository record denotes
        code containers; other kinds are rejected.
        """
        if repository.source_kind not in (
            RepositorySourceKind.GIT,
            RepositorySourceKind.LOCAL_PATH,
            RepositorySourceKind.ARCHIVE,
        ):
            raise QcaeValidationError(
                f"source kind {repository.source_kind} is not a code container; "
                "IMPLEMENTS edges require a code container repository"
            )
        edge = make_relationship(
            source=_entity_ref(EntityType.COMPONENT, repository.repository_id),
            relation=RelationType.IMPLEMENTS,
            target=_entity_ref(EntityType.CAPABILITY_ATOM, atom_id),
            verification=verification,
            source_revision=repository.revision,
            asserted_by=asserted_by,
            asserted_at=asserted_at,
        )
        self._relationships.add(edge)
        return edge

    def candidate_implements_atom(
        self,
        candidate,  # Candidate
        atom_id: str,
        verification: VerificationLevel,
        asserted_by: str = "",
        asserted_at: str = "",
    ) -> Relationship:
        edge = make_relationship(
            source=_entity_ref(_entity_type_for_candidate(candidate.source_kind),
                               candidate.candidate_id),
            relation=RelationType.IMPLEMENTS,
            target=_entity_ref(EntityType.CAPABILITY_ATOM, atom_id),
            verification=verification,
            source_revision=candidate.revision,
            asserted_by=asserted_by,
            asserted_at=asserted_at,
        )
        self._relationships.add(edge)
        return edge

    def candidate_located_in_repository(
        self,
        candidate,  # Candidate
        repository: RepositoryRecord,
        verification: VerificationLevel = VerificationLevel.CODE_VERIFIED,
        asserted_by: str = "",
        asserted_at: str = "",
    ) -> Relationship:
        edge = make_relationship(
            source=_entity_ref(_entity_type_for_candidate(candidate.source_kind),
                               candidate.candidate_id),
            relation=RelationType.CONTAINED_IN,
            target=_entity_ref(EntityType.REPOSITORY, repository.repository_id),
            verification=verification,
            source_revision=candidate.revision,
            target_revision=repository.revision,
            asserted_by=asserted_by,
            asserted_at=asserted_at,
        )
        self._relationships.add(edge)
        return edge

    # -- read paths ------------------------------------------------------------

    def atoms_implemented_by_repository(self, repository_id: str) -> List[Relationship]:
        return self._relationships.edges_from(EntityType.COMPONENT, repository_id)

    def candidates_for_atom(self, atom_id: str) -> List[Relationship]:
        return self._relationships.edges_implementing(EntityType.CAPABILITY_ATOM, atom_id)

    def candidates_in_repository(self, repository_id: str) -> List[Relationship]:
        return self._relationships.edges_located_in(EntityType.REPOSITORY, repository_id)


def _entity_ref(entity_type: EntityType, entity_id: str) -> dict:
    """EntityRef construction via dict keeps imports light in the facade."""
    from qcae.core.relationships.graph import EntityRef

    return EntityRef(entity_type=entity_type, entity_id=entity_id)
