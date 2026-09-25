"""Ordered Book 4 dependency paths; transitive facts are derived only."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture_relations import ArchitectureRelationType
from .dependency_provenance import Book4Provenance
from .relationships import EdgeType
from .temporal import Timestamp, UnknownBound


class PathRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    relation: EdgeType | ArchitectureRelationType

    @model_validator(mode="after")
    def _distinct(self) -> "PathRelation":
        if self.subject_ref == self.object_ref:
            raise ValueError("path relation endpoints must differ")
        return self


class DependencyPath(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    target_ref: str = Field(min_length=1)
    ordered_nodes: tuple[str, ...] = Field(min_length=2)
    ordered_relations: tuple[PathRelation, ...] = Field(min_length=1)
    path_length: int = Field(ge=1)
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)
    source_snapshot_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _continuity(self) -> "DependencyPath":
        if self.ordered_nodes[0] != self.subject_ref:
            raise ValueError("path must begin at subject_ref")
        if self.ordered_nodes[-1] != self.target_ref:
            raise ValueError("path must end at target_ref")
        if len(set(self.ordered_nodes)) != len(self.ordered_nodes):
            raise ValueError("ordered_nodes must not silently collapse a cycle")
        if self.path_length != len(self.ordered_relations):
            raise ValueError("path_length must equal ordered relation count")
        if len(self.ordered_relations) + 1 != len(self.ordered_nodes):
            raise ValueError("A -> B -> C must remain two ordered relations")
        for index, relation in enumerate(self.ordered_relations):
            if relation.subject_ref != self.ordered_nodes[index]:
                raise ValueError("relation does not start at ordered node")
            if relation.object_ref != self.ordered_nodes[index + 1]:
                raise ValueError("relation does not end at next ordered node")
        return self


class DerivedTransitiveDependency(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_ref: str
    target_ref: str
    source_path_id: str
    ordered_path: tuple[str, ...]
    authoritative: bool = False
    derivation: str = "ordered-path"

    @model_validator(mode="after")
    def _non_authoritative(self) -> "DerivedTransitiveDependency":
        if self.authoritative:
            raise ValueError("transitive cache/projection must be non-authoritative")
        return self


class DependencyPathBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._paths: dict[str, DependencyPath] = {}

    def add(self, path: DependencyPath) -> DependencyPath:
        if path.path_id in self._paths:
            raise ValueError("path IDs are immutable and unique")
        self.provenance.validate_refs(path.book2_claim_refs)
        self.provenance.validate_snapshot_lineage(
            path.book2_claim_refs, path.source_snapshot_refs
        )
        self._paths[path.path_id] = path
        return path

    def require(self, path_id: str) -> DependencyPath:
        return self._paths[path_id]

    def derive_transitive(self, path_id: str) -> DerivedTransitiveDependency:
        path = self.require(path_id)
        return DerivedTransitiveDependency(
            subject_ref=path.subject_ref,
            target_ref=path.target_ref,
            source_path_id=path.path_id,
            ordered_path=path.ordered_nodes,
        )


__all__ = [
    "DependencyPath",
    "DependencyPathBook",
    "DerivedTransitiveDependency",
    "PathRelation",
]
