"""Relationship persistence port (P1-R1 §8).

Persists the frozen P0 ``Relationship`` model (canon 1.3.4 vocabulary,
endpoint-role enforcement, revision scoping, verification labels). No new
edge semantics are introduced: repository/candidate/atom links use the
existing canon-approved types.

- candidate implements atom          -> IMPLEMENTS   (candidate -> atom)
- candidate located in repository    -> CONTAINED_IN (candidate's component
  -> repository); for whole-repository claims the candidate itself is the
  source when typed COMPONENT — canon endpoint rules decide per edge
- composite composed of atom         -> COMPOSED_OF  (composite -> atom)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from qcae.core.relationships.graph import Relationship

__all__ = ["RelationshipPersistencePort"]


class RelationshipPersistencePort(ABC):
    """Durable, append-oriented storage for capability-graph edges."""

    @abstractmethod
    def add(self, relationship: Relationship) -> None:
        """Persist one edge. Idempotent for identical edges."""

    @abstractmethod
    def edges_from(self, entity_type, entity_id: str) -> List[Relationship]:
        """Edges whose source is the given entity."""

    @abstractmethod
    def edges_to(self, entity_type, entity_id: str) -> List[Relationship]:
        """Edges whose target is the given entity."""

    @abstractmethod
    def edges_implementing(self, entity_type, entity_id: str) -> List[Relationship]:
        """IMPLEMENTS edges pointing at the given atom/capability."""

    @abstractmethod
    def edges_located_in(self, entity_type, entity_id: str) -> List[Relationship]:
        """CONTAINED_IN edges pointing at the given repository."""

    @abstractmethod
    def all_edges(self) -> List[Relationship]:
        """Every stored edge (snapshot/audit)."""
