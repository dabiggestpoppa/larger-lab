"""P2-R5R-R2 — durable atomic legacy reconciliation provenance + refusal ordering.

Custody seal tests for Finding A (zero-mutation refusal ordering) and
Finding B (durable atomic reconciliation provenance). Every case is proven
against real SQLite files (never a mock).
"""

from __future__ import annotations

import re
import sys

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    LegacyDatabaseClass,
    MigrationRunner,
    V3_TO_V4,
    V5_ADDITIONS_DDL,
    _schema_fingerprint,
    classify_legacy_database,
)
from qcae.infrastructure.persistence.store_factory import (
    open_metadata_db,
    open_raw_connection,
)

_HEX64 = re.compile(r"[0-9a-f]{64}")


def _tables(conn) -> set:
    return {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
            " AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


def _version(conn) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _journal_mode(conn) -> str:
    return conn.execute("PRAGMA journal_mode").fetchone()[0]


def _sidecars_exist(db_path) -> bool:
    return (
        (db_path.parent / (db_path.name + "-wal")).exists()
        or (db_path.parent / (db_path.name + "-shm")).exists()
    )


def _true_v3(path) -> None:
    """Minimal true v3 database (P1 + repository_revision)."""
    conn = open_raw_connection(path)
    conn.executescript(
        "CREATE TABLE evidence_artifact (evidence_id TEXT PRIMARY KEY,"
        " subject_id TEXT NOT NULL, object_type TEXT NOT NULL,"
        " evidence_class TEXT NOT NULL, artifact_digest TEXT NOT NULL,"
        " producer TEXT NOT NULL, created_at TEXT NOT NULL,"
        " external_owner_domain TEXT NOT NULL DEFAULT '',"
        " payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL);"
        "CREATE TABLE freshness_log (seq INTEGER PRIMARY KEY AUTOINCREMENT,"
        " evidence_id TEXT NOT NULL, from_state TEXT, to_state TEXT NOT NULL,"
        " reason TEXT NOT NULL, changed_at TEXT NOT NULL);"
        "CREATE TABLE repository_record (repository_id TEXT PRIMARY KEY,"
        " revision TEXT NOT NULL, payload_json TEXT NOT NULL,"
        " payload_digest TEXT NOT NULL);"
        "CREATE TABLE repository_revision (repository_revision_id TEXT PRIMARY KEY,"
        " repository_id TEXT NOT NULL, revision TEXT NOT NULL,"
        " payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL,"
        " UNIQUE (repository_id, revision));"
        "CREATE INDEX ix_repo_revision_identity ON repository_revision(repository_id);"
    )
    conn.execute(
        "INSERT INTO repository_record VALUES ('repo-a','r1',?,'d1')",
        ('{"repository_id":"repo-a","revision":"r1"}',),
    )
    conn.execute("PRAGMA user_version = 3")
    conn.commit()
    conn.close()


def _true_v4(path) -> None:
    """True historical v4: v3 carried through the real P2-0004 migration."""
    _true_v3(path)
    conn = open_raw_connection(path)
    runner = MigrationRunner(conn, clock=lambda: "2026-01-01T00:00:00Z")
    runner.migrate_to(4, {4: V3_TO_V4})
    assert _version(conn) == 4
    conn.close()


def _v4_shape_rows(conn) -> None:
    """One historical row per v4 load-bearing table (preservation proof)."""
    conn.execute(
        "INSERT INTO runtime_job (job_id, deterministic_id, status,"
        " job_type, payload_json, payload_digest) VALUES"
        " ('job-r1','det-r1','SUCCEEDED','GENERIC','{}','d1')"
    )
    conn.execute(
        "INSERT INTO runtime_step (step_id, job_id, status, step_type,"
        " payload_json, payload_digest) VALUES"
        " ('job-r1:s-1','job-r1','SUCCEEDED','GENERIC','{}','d1')"
    )
    conn.execute(
        "INSERT INTO runtime_job_event (event_id, event_type, job_id,"
        " occurred_at, event_digest) VALUES"
        " ('ev-r1','JOB_COMPLETED','job-r1','t','d1')"
    )
    conn.execute(
        "INSERT INTO governance_approval_request (request_id, principal,"
        " action, payload_json, payload_digest, created_at) VALUES"
        " ('req-r1','w','a','{}','d1','t')"
    )
    conn.execute(
        "INSERT INTO governance_approval_decision (decision_id, request_ref,"
        " state, payload_json, payload_digest, created_at) VALUES"
        " ('dec-r1','req-r1','GRANTED','{}','d1','t')"
    )


class TestRefusalOrdering:
    """Finding A: all terminal refusals happen before any persistent write."""

    def test_unknown_hybrid_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "hybrid.sqlite3"
        conn = open_raw_connection(db)
        # v2 stamp with runtime tables: contradictory shape.
        conn.executescript(
            "CREATE TABLE runtime_job (job_id TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version
            assert _schema_fingerprint(conn) == before_fp
            # No -wal/-shm sidecars created by the refused open.
            assert not _sidecars_exist(db)
        finally:
            conn.close()

    def test_unversioned_existing_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "unversioned.sqlite3"
        conn = open_raw_connection(db)
        conn.execute("CREATE TABLE legacy_app_data (id TEXT PRIMARY KEY)")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(QcaeValidationError, match="unversioned"):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version
            assert _schema_fingerprint(conn) == before_fp
            assert not _sidecars_exist(db)
        finally:
            conn.close()

    def test_newer_schema_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "newer.sqlite3"
        conn = open_metadata_db(db)  # bootstraps to v5 (sets WAL)
        conn.execute("PRAGMA user_version = 6")
        conn.commit()
        before_mode = _journal_mode(conn)
        before_version = _version(conn)  # == 6
        before_fp = _schema_fingerprint(conn)
        conn.close()

        with pytest.raises(
            QcaeValidationError, match="not openable by this build"
        ):
            open_metadata_db(db)

        conn = open_raw_connection(db)
        try:
            assert _journal_mode(conn) == before_mode
            assert _version(conn) == before_version  # refusal did not change it
            assert _schema_fingerprint(conn) == before_fp
        finally:
            conn.close()


class TestReconciliationProvenance:
    """Finding B: durable atomic reconciliation provenance for misversioned stamps."""

    def _misversioned_true_v4(self, db) -> None:
        """True-v4 physical (13 v4 tables, no post-v4), stamped at 1."""
        _true_v4(db)
        conn = open_raw_connection(db)
        _v4_shape_rows(conn)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()

    def _misversioned_post_v4(self, db) -> None:
        """Post-v4 physical (v4 + both post-v4 tables), stamped at 1."""
        _true_v4(db)
        conn = open_raw_connection(db)
        _v4_shape_rows(conn)
        conn.executescript(V5_ADDITIONS_DDL)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()

    def test_true_v4_reconciliation_provenance(self, tmp_path) -> None:
        """observed=1 -> normalized=2 (true-v4 legacy), then 2->3->4->5, v5, rows preserved."""
        db = tmp_path / "legacy4.sqlite3"
        self._misversioned_true_v4(db)

        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.KNOWN_P2_MISVERSIONED
            )
        finally:
            conn.close()

        conn = open_metadata_db(db)
        try:
            assert _version(conn) == CURRENT_SCHEMA_VERSION == 5
            # Rows preserved through normalization + migration.
            assert conn.execute(
                "SELECT status FROM runtime_job WHERE job_id='job-r1'"
            ).fetchone()[0] == "SUCCEEDED"
            assert conn.execute(
                "SELECT state FROM governance_approval_decision WHERE decision_id='dec-r1'"
            ).fetchone()[0] == "GRANTED"
            # Reconciliation provenance: observed=1, normalized=2 (no post-v4 tables).
            entries = MigrationRunner(conn, clock=lambda: "t").ledger()
            reconcile = [
                e
                for e in entries
                if e.migration_id.startswith("P2-R5R-RECONCILE")
            ]
            assert len(reconcile) == 1
            r = reconcile[0]
            assert r.migration_id == "P2-R5R-RECONCILE-STAMP-v1->v2"
            assert r.from_version == 1
            assert r.to_version == 2
            assert _HEX64.fullmatch(r.pre_digest)
            assert _HEX64.fullmatch(r.post_digest)
            assert r.applied_at.endswith("Z")
            # MigrationRunner continues from the normalized version: 2->3->4->5.
            versions = [(e.from_version, e.to_version) for e in entries]
            assert (2, 3) in versions
            assert (3, 4) in versions
            assert (4, 5) in versions
        finally:
            conn.close()

    def test_post_v4_reconciliation_provenance(self, tmp_path) -> None:
        """observed=1 -> normalized=4 (post-v4 physical), then 4->5, indexes correct."""
        db = tmp_path / "legacy-post4.sqlite3"
        self._misversioned_post_v4(db)

        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.KNOWN_P2_MISVERSIONED
            )
        finally:
            conn.close()

        conn = open_metadata_db(db)
        try:
            assert _version(conn) == CURRENT_SCHEMA_VERSION == 5
            # Post-v4 tables present.
            assert "runtime_execution" in _tables(conn)
            assert "governance_approval_use" in _tables(conn)
            # Single-use unique index present.
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
                " AND name='ux_approval_use_decision'"
            ).fetchone() is not None
            # Reconciliation provenance: observed=1, normalized=4 (both post-v4 tables).
            entries = MigrationRunner(conn, clock=lambda: "t").ledger()
            reconcile = [
                e
                for e in entries
                if e.migration_id.startswith("P2-R5R-RECONCILE")
            ]
            assert len(reconcile) == 1
            r = reconcile[0]
            assert r.migration_id == "P2-R5R-RECONCILE-STAMP-v1->v4"
            assert r.from_version == 1
            assert r.to_version == 4
            assert _HEX64.fullmatch(r.pre_digest)
            assert _HEX64.fullmatch(r.post_digest)
            assert r.applied_at.endswith("Z")
            # MigrationRunner continues from the normalized version: 4->5.
            versions = [(e.from_version, e.to_version) for e in entries]
            assert (4, 5) in versions
            # Rows preserved.
            assert conn.execute(
                "SELECT status FROM runtime_job WHERE job_id='job-r1'"
            ).fetchone()[0] == "SUCCEEDED"
        finally:
            conn.close()

    def test_reconciliation_atomic_rollback_on_injected_failure(
        self, tmp_path, monkeypatch
    ) -> None:
        """Inject failure between provenance write and user_version stamp;
        rollback leaves old version and no reconciliation fact."""
        db = tmp_path / "crash.sqlite3"
        self._misversioned_true_v4(db)

        _sqlite3 = sys.modules["sqlite3"]
        original_connect = _sqlite3.connect
        injected = {"flag": False}

        class CrashingConnection(_sqlite3.Connection):
            def execute(self, sql, *a, **k):
                if (
                    injected["flag"]
                    and isinstance(sql, str)
                    and "PRAGMA user_version =" in sql
                ):
                    raise RuntimeError("injected crash between provenance and stamp")
                return super().execute(sql, *a, **k)

        def crashing_connect(*args, **kwargs):
            kwargs["factory"] = CrashingConnection
            return original_connect(*args, **kwargs)

        monkeypatch.setattr(_sqlite3, "connect", crashing_connect)

        # First attempt: inject failure on the user_version write.
        injected["flag"] = True
        with pytest.raises(RuntimeError, match="injected crash"):
            open_metadata_db(db)

        # Rollback: old version remains, no reconciliation fact.
        # (A pre-existing 3->4 ledger row from _true_v4 remains; only the
        # reconciliation INSERT was rolled back.)
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == 1
            reconcile_count = conn.execute(
                "SELECT COUNT(*) FROM schema_migration_ledger"
                " WHERE migration_id LIKE 'P2-R5R-RECONCILE%'"
            ).fetchone()[0]
            assert reconcile_count == 0
        finally:
            conn.close()

        # Retry without injection: succeeds with exactly one reconciliation fact.
        injected["flag"] = False
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            facts = conn.execute(
                "SELECT COUNT(*) FROM schema_migration_ledger"
                " WHERE migration_id LIKE 'P2-R5R-RECONCILE%'"
            ).fetchone()[0]
            assert facts == 1
        finally:
            conn.close()
