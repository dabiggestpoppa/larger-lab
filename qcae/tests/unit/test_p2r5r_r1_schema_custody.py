"""P2-R5R-R1 — bootstrap atomicity + strict legacy fingerprint (schema law).

Every case is proven against real SQLite files (never a mock):

C01 — no mutation before classification; fresh vs unversioned-existing:
1.  truly empty v0 bootstraps to a complete physical v5;
2.  v0 WITH existing tables is UNVERSIONED_EXISTING and refused;
3.  unknown hybrid refused WITHOUT mutation (version + shape identical).

C02 — true atomic fresh v5 bootstrap with real provenance digests:
4.  failed bootstrap rolls back: no partial schema, version stays 0;
5.  bootstrap pre_digest is a real sha256 (len 64, lowercase hex);
6.  bootstrap post_digest is a real sha256 (len 64, lowercase hex);
7.  post_digest equals the actual schema fingerprint (the ledger ROW is
    data and cannot move the digest).

C03 — strict known-P2 physical fingerprint + hybrid refusal:
8.  true v4 (existing coverage) migrates to v5 — cited, not repeated;
9.  known misversioned v4-physical DB migrates to v5, all rows preserved;
10. known misversioned post-v4-physical DB migrates (existing coverage);
11. §9 counterexample: the three key tables alone are REFUSED;
12. a full shape missing ONE required P2 table is REFUSED;
13. a full shape missing ONE critical index is REFUSED;
14. all historical rows preserved through legacy migration.
"""

from __future__ import annotations

import re

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence import store_factory
from qcae.infrastructure.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    LegacyDatabaseClass,
    MigrationRunner,
    V3_TO_V4,
    _schema_fingerprint,
    classify_legacy_database,
)
from qcae.infrastructure.persistence.store_factory import (
    open_metadata_db,
    open_raw_connection,
)

# Architecture guard (canon 15.2): qcae modules never import sqlite3; the
# connection type is intentionally unannotated here for that reason.

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
        "INSERT INTO repository_record VALUES ('repo-a','r1','{\"repository_id\":\"repo-a\",\"revision\":\"r1\"}','d1')"
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


class TestFreshVsUnversioned:
    def test_01_truly_empty_v0_bootstraps_complete_v5(self, tmp_path) -> None:
        db = tmp_path / "fresh.sqlite3"
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == CURRENT_SCHEMA_VERSION == 5
            assert "runtime_execution" in _tables(conn)
            assert "governance_approval_use" in _tables(conn)
            row = conn.execute(
                "SELECT from_version, to_version, migration_id,"
                " pre_digest, post_digest FROM schema_migration_ledger"
            ).fetchone()
            assert tuple(row[:3]) == (0, 5, "BOOTSTRAP-v5-complete-schema")
            assert _HEX64.fullmatch(row[3]), "pre_digest must be real sha256"
            assert _HEX64.fullmatch(row[4]), "post_digest must be real sha256"
        finally:
            conn.close()

    def test_02_unversioned_existing_db_refused(self, tmp_path) -> None:
        db = tmp_path / "unversioned.sqlite3"
        conn = open_raw_connection(db)
        conn.execute("CREATE TABLE legacy_app_data (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="unversioned"):
            open_metadata_db(db)
        # Refused WITHOUT mutation: version and shape identical.
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == 0
            assert _tables(conn) == {"legacy_app_data"}
        finally:
            conn.close()

    def test_03_unknown_hybrid_refused_without_mutation(self, tmp_path) -> None:
        db = tmp_path / "hybrid.sqlite3"
        conn = open_raw_connection(db)
        # Contradictory shape under every classifier: v2 stamp with
        # runtime tables present (a v2 store must be P1-only).
        conn.execute(
            "CREATE TABLE runtime_job (job_id TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        before_version = _version(conn)
        before_fp = _schema_fingerprint(conn)
        conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == before_version
            assert _schema_fingerprint(conn) == before_fp
        finally:
            conn.close()


class TestAtomicBootstrap:
    def test_04_failed_bootstrap_leaves_no_partial_schema(
        self, tmp_path, monkeypatch
    ) -> None:
        scripts = list(store_factory._fresh_v5_scripts())
        scripts.insert(
            3,
            "CREATE TABLE poison_v5_probe (id TEXT PRIMARY KEY);"
            " THIS IS NOT SQL;",
        )
        monkeypatch.setattr(
            store_factory, "_FRESH_V5_BOOTSTRAP_SCRIPTS", scripts,
            raising=False,
        )
        db = tmp_path / "poisoned.sqlite3"
        with pytest.raises(QcaeValidationError):
            open_metadata_db(db)
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == 0
            assert _tables(conn) == set(), (
                "failed bootstrap must roll back EVERYTHING"
            )
        finally:
            conn.close()

    def test_05_bootstrap_pre_digest_is_real_sha256(self, tmp_path) -> None:
        conn = open_metadata_db(tmp_path / "pre.sqlite3")
        try:
            pre = conn.execute(
                "SELECT pre_digest FROM schema_migration_ledger"
            ).fetchone()[0]
            assert _HEX64.fullmatch(pre), f"sentinel digest: {pre!r}"
            assert pre == _schema_fingerprint(open_raw_connection(":memory:"))
        finally:
            conn.close()

    def test_06_bootstrap_post_digest_is_real_sha256(self, tmp_path) -> None:
        conn = open_metadata_db(tmp_path / "post.sqlite3")
        try:
            post = conn.execute(
                "SELECT post_digest FROM schema_migration_ledger"
            ).fetchone()[0]
            assert _HEX64.fullmatch(post), f"sentinel digest: {post!r}"
        finally:
            conn.close()

    def test_07_post_digest_equals_actual_schema_fingerprint(
        self, tmp_path
    ) -> None:
        conn = open_metadata_db(tmp_path / "exact.sqlite3")
        try:
            post = conn.execute(
                "SELECT post_digest FROM schema_migration_ledger"
            ).fetchone()[0]
            assert post == _schema_fingerprint(conn)
        finally:
            conn.close()


class TestStrictLegacyFingerprint:
    def test_09_known_misversioned_v4_physical_migrates_with_rows(
        self, tmp_path
    ) -> None:
        db = tmp_path / "legacy4.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        _v4_shape_rows(conn)
        # The historical bug: version says 1 while physical P2 state exists.
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.KNOWN_P2_MISVERSIONED
            )
        finally:
            conn.close()
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            assert "runtime_execution" in _tables(conn)
            assert "governance_approval_use" in _tables(conn)
            assert conn.execute(
                "SELECT status FROM runtime_job WHERE job_id='job-r1'"
            ).fetchone()[0] == "SUCCEEDED"
            assert conn.execute(
                "SELECT status FROM runtime_step WHERE step_id='job-r1:s-1'"
            ).fetchone()[0] == "SUCCEEDED"
            assert conn.execute(
                "SELECT event_type FROM runtime_job_event WHERE event_id='ev-r1'"
            ).fetchone()[0] == "JOB_COMPLETED"
            assert conn.execute(
                "SELECT state FROM governance_approval_decision"
                " WHERE decision_id='dec-r1'"
            ).fetchone()[0] == "GRANTED"
        finally:
            conn.close()

    def test_11_three_key_tables_alone_are_refused(self, tmp_path) -> None:
        # §9 counterexample: enough to satisfy the OLD three-column check,
        # but deliberately missing every other mandatory P2 table.
        db = tmp_path / "counterexample.sqlite3"
        conn = open_raw_connection(db)
        conn.execute(
            "CREATE TABLE runtime_job (job_id TEXT PRIMARY KEY,"
            " deterministic_id TEXT NOT NULL, status TEXT NOT NULL,"
            " job_type TEXT NOT NULL, payload_json TEXT NOT NULL,"
            " payload_digest TEXT NOT NULL, priority INTEGER NOT NULL"
            " DEFAULT 0, queued_at TEXT NOT NULL DEFAULT '',"
            " not_before TEXT NOT NULL DEFAULT '')"
        )
        conn.execute(
            "CREATE TABLE runtime_step (step_id TEXT NOT NULL, job_id TEXT"
            " NOT NULL, status TEXT NOT NULL, step_type TEXT NOT NULL,"
            " payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL,"
            " lease_owner TEXT NOT NULL DEFAULT '',"
            " lease_token TEXT NOT NULL DEFAULT '',"
            " lease_expires_at TEXT NOT NULL DEFAULT '',"
            " not_before TEXT NOT NULL DEFAULT '', PRIMARY KEY (step_id))"
        )
        conn.execute(
            "CREATE TABLE governance_approval_decision (decision_id TEXT"
            " PRIMARY KEY, request_ref TEXT NOT NULL, state TEXT NOT NULL,"
            " payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL,"
            " created_at TEXT NOT NULL)"
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.UNKNOWN_HYBRID
            )
        finally:
            conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

    def test_12_full_shape_missing_one_table_refused(self, tmp_path) -> None:
        db = tmp_path / "missing-table.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.execute("DROP TABLE runtime_checkpoint")
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.UNKNOWN_HYBRID
            )
        finally:
            conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

    def test_13_full_shape_missing_critical_index_refused(
        self, tmp_path
    ) -> None:
        db = tmp_path / "missing-index.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.execute("DROP INDEX ix_runtime_event_job")
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        conn = open_raw_connection(db)
        try:
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.UNKNOWN_HYBRID
            )
        finally:
            conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)
