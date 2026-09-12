"""SQLite RepositoryRegistry (P1-R1 §7, §9)."""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.registry import RepositoryRecord, RepositorySourceKind
from qcae.core.ports.repository_registry import RepositoryRegistryPort

__all__ = ["SqliteRepositoryRegistry", "REPOSITORY_REGISTRY_DDL"]

REPOSITORY_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS repository_record (
    repository_id   TEXT NOT NULL,
    source_kind     TEXT NOT NULL,
    canonical_locator TEXT NOT NULL,
    revision        TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    PRIMARY KEY (repository_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_repo_identity
    ON repository_record(source_kind, canonical_locator, revision);
CREATE INDEX IF NOT EXISTS ix_repo_locator ON repository_record(canonical_locator);
CREATE INDEX IF NOT EXISTS ix_repo_kind ON repository_record(source_kind);
"""


class SqliteRepositoryRegistry(RepositoryRegistryPort):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, record: RepositoryRecord) -> str:
        record.validate()
        payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
        digest = record.digest()
        try:
            self._conn.execute(
                "INSERT INTO repository_record (repository_id, source_kind,"
                " canonical_locator, revision, payload_json, payload_digest)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (record.repository_id, record.source_kind.value,
                 record.canonical_locator, record.revision, payload, digest),
            )
        except sqlite3.IntegrityError as exc:
            existing = self._conn.execute(
                "SELECT payload_digest FROM repository_record WHERE repository_id = ?",
                (record.repository_id,),
            ).fetchone()
            if existing and existing[0] == digest:
                return record.repository_id  # idempotent identical re-add
            raise QcaeValidationError(
                f"repository record {record.repository_id!r} conflicts with stored "
                "state (identity/revision key reuse with different content)"
            ) from exc
        return record.repository_id

    def get(self, repository_id: str) -> Optional[RepositoryRecord]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM repository_record"
            " WHERE repository_id = ?",
            (repository_id,),
        ).fetchone()
        if row is None:
            return None
        record = RepositoryRecord.from_dict(json.loads(row[0]))
        if record.digest() != row[1]:
            raise QcaeValidationError(
                f"stored repository record {repository_id!r} failed integrity check"
            )
        return record

    def _rows(self, where: str, params: tuple) -> List[RepositoryRecord]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM repository_record"
            f" WHERE {where} ORDER BY canonical_locator, revision",
            params,
        ).fetchall()
        out = []
        for payload_json, payload_digest in rows:
            record = RepositoryRecord.from_dict(json.loads(payload_json))
            if record.digest() != payload_digest:
                raise QcaeValidationError(
                    "stored repository record failed integrity check"
                )
            out.append(record)
        return out

    def get_by_locator(self, source_kind, canonical_locator: str, revision: str = "") -> Optional[RepositoryRecord]:
        where = "source_kind = ? AND canonical_locator = ?"
        params: list = [source_kind.value, canonical_locator]
        if revision:
            where += " AND revision = ?"
            params.append(revision)
        hits = self._rows(where, tuple(params))
        return hits[0] if hits else None

    def list_by_source_kind(self, source_kind) -> List[RepositoryRecord]:
        return self._rows("source_kind = ?", (source_kind.value,))

    def list_revisions(self, source_kind, canonical_locator: str) -> List[RepositoryRecord]:
        return self._rows(
            "source_kind = ? AND canonical_locator = ?",
            (source_kind.value, canonical_locator),
        )

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM repository_record").fetchone()
        return int(row[0])
