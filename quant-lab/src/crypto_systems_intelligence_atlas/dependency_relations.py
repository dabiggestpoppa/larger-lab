"""Faithful projection of Book 4 records onto frozen Book 1/Book 3 relations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .architecture_relations import ArchitectureRelationType
from .claims import Book2ClaimBinding, ClaimStore
from .dependency import DependencyRecord
from .relationships import (
    EdgeType,
    Hyperedge,
    HyperedgeClass,
    HyperedgeRole,
    RouteAttributes,
)
from .temporal import Timestamp, UnknownBound


FORBIDDEN_BOOK4_ADDITIONS = frozenset(
    {
        "VERIFIED_BY",
        "RELAYED_BY",
        "USES_ENDPOINT",
        "USES_RELAYER",
        "TRANSPORTS_FOR",
        "ROUTE_DEPENDS_ON",
    }
)


class RelationProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target_book: str
    relation_type: EdgeType | ArchitectureRelationType
    direct_only: bool = True


class Book4RelationProjector:
    """No new relation names and no transitive DEPENDS_ON projection."""

    def project(self, record: DependencyRecord) -> RelationProjection:
        basis = record.relation_basis
        if isinstance(basis, EdgeType):
            return RelationProjection(target_book="BOOK_1", relation_type=basis)
        return RelationProjection(target_book="BOOK_3", relation_type=basis)

    def ensure_no_forbidden_addition(self, relation_name: str) -> None:
        if relation_name in FORBIDDEN_BOOK4_ADDITIONS:
            raise ValueError(f"Book 4 relation gap requires operator stop: {relation_name}")


class OracleDeliveryHyperedgeFactory:
    """Uses the accepted Book 1 primitive; no Book 4 hypergraph is introduced."""

    def __init__(self, claim_store: ClaimStore) -> None:
        self.claim_store = claim_store

    def build(
        self,
        *,
        hyperedge_id: str,
        oracle_ref: str,
        consumer_ref: str,
        chain_ref: str,
        route_attributes: RouteAttributes,
        claim_ref: str,
        observed_at: datetime,
        valid_from: Timestamp | UnknownBound,
    ) -> Hyperedge:
        claim_store = self.claim_store
        claim = claim_store.require(claim_ref)
        binding = Book2ClaimBinding.for_graph(claim, claim_store).book1
        return Hyperedge(
            hyperedge_id=hyperedge_id,
            hyperedge_class=HyperedgeClass.HE_ORACLE_DELIVERY,
            participants={
                HyperedgeRole.ORACLE: oracle_ref,
                HyperedgeRole.CONSUMER: consumer_ref,
                HyperedgeRole.CHAIN: chain_ref,
            },
            claim_binding=binding,
            observed_at=observed_at,
            valid_from=valid_from,
        )


__all__ = [
    "Book4RelationProjector",
    "FORBIDDEN_BOOK4_ADDITIONS",
    "OracleDeliveryHyperedgeFactory",
    "RelationProjection",
]
