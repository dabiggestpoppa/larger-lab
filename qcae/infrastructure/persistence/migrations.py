"""Schema migration infrastructure (Book V 13.3, P1 spec §16).

- ``PRAGMA user_version`` pins the current schema version;
- every applied migration is appended to ``schema_migration_ledger`` with its
  identity, timestamp, and pre/post digests (transformation provenance);
- the runner refuses to run a migration whose target is not exactly
  ``current + 1`` (no skipping, no backwards, no re-runs);
- migrations record the schema version they produce; a failed migration rolls
  back inside its own transaction and leaves the ledger untouched.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from qcae.core.errors import QcaeValidationError

__all__ = ["Migration", "MigrationLedgerEntry", "MigrationRunner", "MIGRATION_LEDGER_DDL",
           "TEST_V1_TO_V2"]

MIGRATION_LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration_ledger (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    from_version   INTEGER NOT NULL,
    to_version     INTEGER NOT NULL,
    migration_id   TEXT NOT NULL,
    applied_at     TEXT NOT NULL,
    pre_digest     TEXT NOT NULL,
    post_digest    TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Migration:
    """One explicit, forward-only schema transformation."""

    from_version: int
    to_version: int
    migration_id: str
    apply: Callable[[sqlite3.Connection], None]
    description: str = ""


@dataclass(frozen=True)
class MigrationLedgerEntry:
    from_version: int
    to_version: int
    migration_id: str
    applied_at: str
    pre_digest: str
    post_digest: str


def _schema_fingerprint(conn: sqlite3.Connection) -> str:
    """Digest of table/DDL shape for provenance (content, not row data)."""
    import hashlib

    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        " ORDER BY name"
    ).fetchall()
    material = repr(rows).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


class MigrationRunner:
    def __init__(self, conn: sqlite3.Connection, clock: Callable[[], str]) -> None:
        self._conn = conn
        self._clock = clock
        conn.executescript(MIGRATION_LEDGER_DDL)

    def current_version(self) -> int:
        return int(self._conn.execute("PRAGMA user_version").fetchone()[0])

    def ledger(self) -> List[MigrationLedgerEntry]:
        rows = self._conn.execute(
            "SELECT from_version, to_version, migration_id, applied_at, pre_digest,"
            " post_digest FROM schema_migration_ledger ORDER BY seq"
        ).fetchall()
        return [MigrationLedgerEntry(*row) for row in rows]

    def migrate_to(self, target: int, migrations: Dict[int, Migration]) -> int:
        """Apply sequential migrations until ``target``. Returns new version.

        ``migrations`` is keyed by TARGET schema version (the version each
        migration produces), so lookup is always "the migration that takes
        the store to ``current + 1``".
        """
        current = self.current_version()
        if target < current:
            raise QcaeValidationError(
                f"refusing to migrate backwards ({current} -> {target})"
            )
        while current < target:
            migration = migrations.get(current + 1)
            if migration is None:
                raise QcaeValidationError(
                    f"no migration registered to take schema {current} -> {target}"
                )
            if migration.from_version != current or migration.to_version != current + 1:
                raise QcaeValidationError(
                    f"migration {migration.migration_id!r} declares "
                    f"{migration.from_version}->{migration.to_version}, "
                    f"but store is at {current}"
                )
            pre = _schema_fingerprint(self._conn)
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                migration.apply(self._conn)
                self._conn.execute(f"PRAGMA user_version = {migration.to_version}")
                self._conn.execute(
                    "INSERT INTO schema_migration_ledger (from_version, to_version,"
                    " migration_id, applied_at, pre_digest, post_digest)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (migration.from_version, migration.to_version, migration.migration_id,
                     self._clock(), pre, _schema_fingerprint(self._conn)),
                )
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise
            current = self.current_version()
        return current


def _apply_test_v2(conn: sqlite3.Connection) -> None:
    """Test migration v1->v2: add an indexed provenance column to evidence.

    Uses a table rebuild (SQLite's ALTER TABLE ADD COLUMN cannot add a
    NOT-NULL-without-default column), preserving all existing rows and
    recording transformation provenance in the ledger via the runner.
    """
    conn.execute("ALTER TABLE evidence_artifact RENAME TO evidence_artifact_v1")
    conn.execute(
        """
        CREATE TABLE evidence_artifact (
            evidence_id      TEXT PRIMARY KEY,
            subject_id       TEXT NOT NULL,
            object_type      TEXT NOT NULL,
            evidence_class   TEXT NOT NULL,
            artifact_digest  TEXT NOT NULL,
            producer         TEXT NOT NULL,
            created_at       TEXT NOT NULL,
            external_owner_domain TEXT NOT NULL DEFAULT '',
            payload_json     TEXT NOT NULL,
            payload_digest   TEXT NOT NULL,
            provenance_note  TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO evidence_artifact (evidence_id, subject_id, object_type,"
        " evidence_class, artifact_digest, producer, created_at,"
        " external_owner_domain, payload_json, payload_digest, provenance_note)"
        " SELECT evidence_id, subject_id, object_type, evidence_class,"
        " artifact_digest, producer, created_at, external_owner_domain,"
        " payload_json, payload_digest, 'migrated-from-v1' FROM evidence_artifact_v1"
    )
    conn.execute("DROP TABLE evidence_artifact_v1")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_evidence_subject ON evidence_artifact(subject_id)"
    )


TEST_V1_TO_V2 = Migration(
    from_version=1,
    to_version=2,
    migration_id="P1-TEST-0001-evidence-provenance-note",
    apply=_apply_test_v2,
    description="adds provenance_note column to evidence_artifact (mechanism proof)",
)
