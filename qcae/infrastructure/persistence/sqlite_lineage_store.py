"""SQLite adapter for the lineage edge repository (Book IV 9.5)."""

from __future__ import annotations

import sqlite3
from typing import List

from qcae.core.errors import QcaeValidationError
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType, LineageRepository

__all__ = ["SqliteLineageRepository", "LINEAGE_DDL"]

LINEAGE_DDL = """
CREATE TABLE IF NOT EXISTS lineage_edge (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id      TEXT NOT NULL,
    src_kind    TEXT NOT NULL,
    edge_type   TEXT NOT NULL,
    dst_id      TEXT NOT NULL,
    dst_kind    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    rationale   TEXT NOT NULL DEFAULT '',
    UNIQUE(src_id, edge_type, dst_id, dst_kind)
);
CREATE INDEX IF NOT EXISTS ix_lineage_src ON lineage_edge(src_id);
CREATE INDEX IF NOT EXISTS ix_lineage_dst ON lineage_edge(dst_id);
CREATE INDEX IF NOT EXISTS ix_lineage_type ON lineage_edge(edge_type);
"""

_KINDS = ("evidence", "receipt", "decision", "negative_knowledge", "positive_knowledge",
          "candidate", "external_ref")


class SqliteLineageRepository(LineageRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, edge: LineageEdge) -> None:
        if edge.src_kind not in _KINDS or edge.dst_kind not in _KINDS:
            raise QcaeValidationError(
                f"lineage endpoints must be kinds {_KINDS}, got "
                f"{edge.src_kind!r} -> {edge.dst_kind!r}"
            )
        if edge.src_id == edge.dst_id and edge.src_kind == edge.dst_kind:
            raise QcaeValidationError("lineage edge cannot join a record to itself")
        try:
            self._conn.execute(
                "INSERT INTO lineage_edge (src_id, src_kind, edge_type, dst_id, dst_kind,"
                " created_at, rationale) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    edge.src_id,
                    edge.src_kind,
                    edge.edge_type.value,
                    edge.dst_id,
                    edge.dst_kind,
                    edge.created_at,
                    edge.rationale,
                ),
            )
        except sqlite3.IntegrityError as exc:
            existing = self._conn.execute(
                "SELECT 1 FROM lineage_edge WHERE src_id=? AND edge_type=? AND dst_id=?"
                " AND dst_kind=?",
                (edge.src_id, edge.edge_type.value, edge.dst_id, edge.dst_kind),
            ).fetchone()
            if existing:
                return  # idempotent re-add of identical edge
            raise QcaeValidationError(f"lineage edge rejected: {exc}") from exc

    def _select(self, where: str, params: tuple) -> List[LineageEdge]:
        rows = self._conn.execute(
            "SELECT src_id, src_kind, edge_type, dst_id, dst_kind, created_at, rationale"
            f" FROM lineage_edge WHERE {where} ORDER BY seq",
            params,
        ).fetchall()
        return [
            LineageEdge(
                src_id=r[0],
                src_kind=r[1],
                edge_type=LineageEdgeType(r[2]),
                dst_id=r[3],
                dst_kind=r[4],
                created_at=r[5],
                rationale=r[6],
            )
            for r in rows
        ]

    def edges_from(self, record_id: str) -> List[LineageEdge]:
        return self._select("src_id = ?", (record_id,))

    def edges_to(self, record_id: str) -> List[LineageEdge]:
        return self._select("dst_id = ?", (record_id,))

    def contradictions_of(self, record_id: str) -> List[LineageEdge]:
        return self._select(
            "edge_type = ? AND (src_id = ? OR dst_id = ?)",
            (LineageEdgeType.CONTRADICTS.value, record_id, record_id),
        )

    def supersession_chain(self, record_id: str) -> List[LineageEdge]:
        return self._select(
            "edge_type = ? AND (src_id = ? OR dst_id = ?)",
            (LineageEdgeType.SUPERSEDES.value, record_id, record_id),
        )

    def all_edges(self) -> List[LineageEdge]:
        return self._select("1=1", ())
