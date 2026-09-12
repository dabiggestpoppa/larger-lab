"""SQLite persistence for P0 capability-graph relationships (P1-R1 §8)."""

from __future__ import annotations

import json
import sqlite3
from typing import List

from qcae.core.errors import QcaeValidationError
from qcae.core.relationships.graph import EntityType, Relationship
from qcae.core.ports.relationship_registry import RelationshipPersistencePort

__all__ = ["SqliteRelationshipPersistence", "RELATIONSHIP_DDL"]

RELATIONSHIP_DDL = """
CREATE TABLE IF NOT EXISTS graph_relationship (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    src_type        TEXT NOT NULL,
    src_id          TEXT NOT NULL,
    relation        TEXT NOT NULL,
    dst_type        TEXT NOT NULL,
    dst_id          TEXT NOT NULL,
    src_revision    TEXT NOT NULL DEFAULT '',
    dst_revision    TEXT NOT NULL DEFAULT '',
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    UNIQUE(src_type, src_id, relation, dst_type, dst_id,
           src_revision, dst_revision)
);
CREATE INDEX IF NOT EXISTS ix_rel_src ON graph_relationship(src_type, src_id);
CREATE INDEX IF NOT EXISTS ix_rel_dst ON graph_relationship(dst_type, dst_id);
"""


class SqliteRelationshipPersistence(RelationshipPersistencePort):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, relationship: Relationship) -> None:
        relationship.validate()
        payload = json.dumps(relationship.to_dict(), ensure_ascii=False, sort_keys=True)
        digest = relationship.digest()
        try:
            self._conn.execute(
                "INSERT INTO graph_relationship (src_type, src_id, relation, dst_type,"
                " dst_id, src_revision, dst_revision, payload_json, payload_digest)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (relationship.source.entity_type.value, relationship.source.entity_id,
                 relationship.relation.value, relationship.target.entity_type.value,
                 relationship.target.entity_id, relationship.source_revision,
                 relationship.target_revision, payload, digest),
            )
        except sqlite3.IntegrityError:
            existing = self._conn.execute(
                "SELECT payload_digest FROM graph_relationship WHERE"
                " src_type=? AND src_id=? AND relation=? AND dst_type=? AND dst_id=?"
                " AND src_revision=? AND dst_revision=?",
                (relationship.source.entity_type.value, relationship.source.entity_id,
                 relationship.relation.value, relationship.target.entity_type.value,
                 relationship.target.entity_id, relationship.source_revision,
                 relationship.target_revision),
            ).fetchone()
            if existing and existing[0] == digest:
                return  # idempotent identical edge
            raise QcaeValidationError(
                "relationship key reuse with different content; assert a new "
                "revision-scoped edge instead of rewriting"
            )

    def _rows(self, where: str, params: tuple) -> List[Relationship]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM graph_relationship"
            f" WHERE {where} ORDER BY seq",
            params,
        ).fetchall()
        out = []
        for payload_json, payload_digest in rows:
            rel = Relationship.from_dict(json.loads(payload_json))
            if rel.digest() != payload_digest:
                raise QcaeValidationError(
                    "stored relationship failed integrity check"
                )
            out.append(rel)
        return out

    def edges_from(self, entity_type, entity_id: str) -> List[Relationship]:
        return self._rows("src_type = ? AND src_id = ?", (entity_type.value, entity_id))

    def edges_to(self, entity_type, entity_id: str) -> List[Relationship]:
        return self._rows("dst_type = ? AND dst_id = ?", (entity_type.value, entity_id))

    def edges_implementing(self, entity_type, entity_id: str) -> List[Relationship]:
        return self._rows(
            "relation = 'implements' AND dst_type = ? AND dst_id = ?",
            (entity_type.value, entity_id),
        )

    def edges_located_in(self, entity_type, entity_id: str) -> List[Relationship]:
        return self._rows(
            "relation = 'contained_in' AND dst_type = ? AND dst_id = ?",
            (entity_type.value, entity_id),
        )

    def all_edges(self) -> List[Relationship]:
        return self._rows("1=1", ())
