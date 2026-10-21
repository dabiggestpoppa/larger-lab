"""Lineage relationship port (Book IV 9.5).

Provenance/lineage edges between durable records. Canon edge vocabulary for
P1 is the 9.5 set; the P0 Relationship vocabulary (capability graph) remains
separate and untouched.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

__all__ = ["LineageEdgeType", "LineageEdge", "LineageRepository"]


class LineageEdgeType(str, Enum):
    """How one durable record relates to another (Book IV 9.5)."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    SUPERSEDES = "SUPERSEDES"
    REPRODUCES = "REPRODUCES"
    FAILS_TO_REPRODUCE = "FAILS_TO_REPRODUCE"
    DEPENDS_ON = "DEPENDS_ON"
    VALID_UNDER = "VALID_UNDER"


class LineageEdge:
    """One provenance edge between two record identities."""

    __slots__ = ("src_id", "src_kind", "edge_type", "dst_id", "dst_kind", "created_at", "rationale")

    def __init__(
        self,
        src_id: str,
        src_kind: str,
        edge_type: LineageEdgeType,
        dst_id: str,
        dst_kind: str,
        created_at: str,
        rationale: str = "",
    ) -> None:
        self.src_id = src_id
        self.src_kind = src_kind
        self.edge_type = edge_type
        self.dst_id = dst_id
        self.dst_kind = dst_kind
        self.created_at = created_at
        self.rationale = rationale

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LineageEdge):
            return NotImplemented
        return (
            self.src_id == other.src_id
            and self.src_kind == other.src_kind
            and self.edge_type == other.edge_type
            and self.dst_id == other.dst_id
            and self.dst_kind == other.dst_kind
            and self.created_at == other.created_at
            and self.rationale == other.rationale
        )

    def __repr__(self) -> str:
        return (
            f"LineageEdge({self.src_id!r}-[{self.edge_type.value}]->{self.dst_id!r}, "
            f"rationale={self.rationale!r})"
        )


class LineageRepository(ABC):
    """Durable storage for provenance/lineage edges (append-oriented)."""

    @abstractmethod
    def add(self, edge: LineageEdge) -> None:
        """Record an edge. Idempotent for identical edges."""

    @abstractmethod
    def edges_from(self, record_id: str) -> List[LineageEdge]:
        """All edges whose source is ``record_id``."""

    @abstractmethod
    def edges_to(self, record_id: str) -> List[LineageEdge]:
        """All edges whose destination is ``record_id``."""

    @abstractmethod
    def contradictions_of(self, record_id: str) -> List[LineageEdge]:
        """CONTRADICTS edges touching ``record_id`` in either direction."""

    @abstractmethod
    def supersession_chain(self, record_id: str) -> List[LineageEdge]:
        """SUPERSEDES edges touching ``record_id`` in either direction."""

    @abstractmethod
    def all_edges(self) -> List[LineageEdge]:
        """Every stored edge (audit/snapshot use)."""
