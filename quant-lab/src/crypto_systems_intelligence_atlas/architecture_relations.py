"""CSIA Book 3 — local typed architecture relations.

These relations do not extend or mutate the frozen Book 1 edge dictionary.
Book 1 relations remain available through the accepted graph kernel; a local
relation is projected only when an explicit faithful mapping is requested.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture import Book2ArchitectureProvenance
from .temporal import Timestamp, UnknownBound, normalize_utc


class ArchitectureRelationType(str, Enum):
    EXECUTES_WITH = "EXECUTES_WITH"
    USES_DA = "USES_DA"
    SEQUENCED_BY = "SEQUENCED_BY"


class ArchitectureRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relation_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    relation_type: ArchitectureRelationType
    object_id: str = Field(min_length=1)
    claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_time: datetime

    @model_validator(mode="after")
    def _shape(self) -> "ArchitectureRelation":
        if self.subject_id == self.object_id:
            raise ValueError("architecture relation subject and object must differ")
        normalize_utc(self.observed_time)
        if not isinstance(self.valid_time, UnknownBound):
            normalize_utc(self.valid_time)
        return self


class ArchitectureRelationBook:
    """Validated in-memory relation collection; no persistence or aliasing."""

    def __init__(self, provenance: Book2ArchitectureProvenance) -> None:
        self.provenance = provenance
        self._relations: dict[str, ArchitectureRelation] = {}

    def add(self, relation: ArchitectureRelation) -> ArchitectureRelation:
        if relation.relation_id in self._relations:
            raise ValueError("architecture relation IDs are immutable and unique")
        for claim_ref in relation.claim_refs:
            self.provenance.resolve_claim(claim_ref)
        self._relations[relation.relation_id] = relation
        return relation

    def require(self, relation_id: str) -> ArchitectureRelation:
        try:
            return self._relations[relation_id]
        except KeyError as exc:
            raise KeyError(f"unknown architecture relation {relation_id}") from exc

    def all_relations(self) -> tuple[ArchitectureRelation, ...]:
        return tuple(self._relations.values())

    def project_to_book1(self, relation_id: str) -> None:
        """Fail closed: no ratified faithful Book 1 edge exists for these three."""

        relation = self.require(relation_id)
        raise ValueError(
            f"{relation.relation_type.value} has no faithful Book 1 projection; "
            "DEPENDS_ON aliasing is forbidden"
        )


__all__ = [
    "ArchitectureRelation",
    "ArchitectureRelationBook",
    "ArchitectureRelationType",
]
