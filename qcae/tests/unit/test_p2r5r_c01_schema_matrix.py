"""P2-R5R-C01 — schema acceptance matrix (canonical substrate reconciliation).

The operator acceptance matrix for schema law. Every case is proven against
real SQLite files (never a mock):

1.  fresh DB is physically complete v5 before it claims v5;
2.  RuntimeIdentity == PRAGMA == CURRENT_SCHEMA_VERSION;
3.  true v3 -> true v4 -> v5;
4.  true historical v4 -> v5 (and ``governance_approval_use`` absent at v4);
5.  known misversioned P2 runtime DB (physical P2 tables, stamp 1) -> v5;
6.  all legacy job/step/event/execution/approval data preserved;
7.  unknown hybrid refused (fail closed);
8.  newer schema refused;
9.  failed migration rolls back;
10. migration ledger pre/post digests truthful;
11. repeated startup is idempotent;
12. build_local_runtime performs no hidden schema completion.
"""

from __future__ import annotations

import hashlib

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    HISTORICAL_V4_DDL_SHA256,
    LegacyDatabaseClass,
    RUNTIME_DDL_MIGRATION,
    V3_TO_V4,
    V4_TO_V5,
    V5_ADDITIONS_DDL,
    V5_ONLY_TABLES,
    Migration,
    MigrationRunner,
    classify_legacy_database,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import APPROVAL_DDL
from qcae.infrastructure.persistence.sqlite_runtime_store import RUNTIME_DDL
from qcae.infrastructure.persistence.store_factory import (
    open_metadata_db,
    open_raw_connection,
)
from qcae.interfaces.cli.app import build_local_runtime

# Architecture guard (canon 15.2): qcae modules never import sqlite3; the
# connection type is intentionally unannotated here for that reason.

#: The complete physical v5 table set the runtime authority owns. (The P1
#: registry adapters create their own tables from their own DDL modules, as
#: they always have; they are not part of the runtime schema authority.)
_V5_REQUIRED_TABLES = {
    "evidence_artifact",
    "freshness_log",
    "runtime_job",
    "runtime_step",
    "runtime_job_event",
    "runtime_checkpoint",
    "runtime_idempotency",
    "runtime_execution",
    "runtime_queue_claim",
    "runtime_budget",
    "governance_policy_request",
    "governance_policy_decision",
    "governance_approval_request",
    "governance_approval_decision",
    "governance_approval_use",
    "governance_escalation",
    "governance_escalation_decision",
}


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
    """Build a minimal true v3 database (P1 + repository_revision)."""
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
    """Build a true (historical) v4 database: P2-0004 DDL only, no post-v4."""
    _true_v3(path)
    conn = open_raw_connection(path)
    runner = MigrationRunner(conn, clock=lambda: "2026-01-01T00:00:00Z")
    runner.migrate_to(4, {4: V3_TO_V4})
    assert _version(conn) == 4
    conn.close()


class TestFreshBootstrap:
    def test_fresh_db_is_physically_complete_v5(self, tmp_path) -> None:
        conn = open_metadata_db(tmp_path / "fresh.sqlite3")
        try:
            assert _version(conn) == CURRENT_SCHEMA_VERSION == 5
            missing = _V5_REQUIRED_TABLES - _tables(conn)
            assert not missing, f"fresh v5 DB missing {sorted(missing)}"
            # The v5-only tables really exist (not just stamped).
            assert V5_ONLY_TABLES <= _tables(conn)
            # The single-use grant index is physically present.
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
                " AND name='ux_approval_use_decision'"
            ).fetchone() is not None
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
                " AND name='ix_approval_use_step'"
            ).fetchone() is not None
        finally:
            conn.close()

    def test_fresh_bootstrap_records_provenance(self, tmp_path) -> None:
        conn = open_metadata_db(tmp_path / "prov.sqlite3")
        try:
            row = conn.execute(
                "SELECT from_version, to_version, migration_id"
                " FROM schema_migration_ledger ORDER BY seq"
            ).fetchall()
            assert len(row) == 1
            assert tuple(row[0]) == (0, 5, "BOOTSTRAP-v5-complete-schema")
        finally:
            conn.close()

    def test_runtime_identity_pruefa_pragma_and_current(self, tmp_path) -> None:
        rt = build_local_runtime(tmp_path / "ident.sqlite3")
        pragma = _version(rt.conn)
        identity = rt.service.identity()
        assert pragma == identity.schema_version == CURRENT_SCHEMA_VERSION

    def test_repeated_startup_is_idempotent(self, tmp_path) -> None:
        db = tmp_path / "idem.sqlite3"
        conn1 = open_metadata_db(db)
        first_tables = _tables(conn1)
        first_ledger = conn1.execute(
            "SELECT COUNT(*) FROM schema_migration_ledger"
        ).fetchone()[0]
        conn1.close()
        conn2 = open_metadata_db(db)
        try:
            assert _version(conn2) == CURRENT_SCHEMA_VERSION
            assert _tables(conn2) == first_tables
            assert conn2.execute(
                "SELECT COUNT(*) FROM schema_migration_ledger"
            ).fetchone()[0] == first_ledger
        finally:
            conn2.close()


class TestHistoricalV4:
    def test_historical_v4_ddl_is_original_p2_0004(self) -> None:
        """Regression: the v4 migration text must match the historical P2 block.

        The original P2 migration (commit 61488273) is the source of truth for
        what ``P2-0004-runtime-governance-tables`` means. It must never again
        absorb post-v4 tables.
        """
        block = 'RUNTIME_DDL_MIGRATION = """' + RUNTIME_DDL_MIGRATION + '"""'
        assert hashlib.sha256(block.encode("utf-8")).hexdigest() == HISTORICAL_V4_DDL_SHA256
        # The original v4 does NOT create the post-v4 structures.
        assert "governance_approval_use" not in RUNTIME_DDL_MIGRATION
        assert "runtime_execution" not in RUNTIME_DDL_MIGRATION

    def test_true_v4_lacks_post_v4_tables_then_migrates(self, tmp_path) -> None:
        db = tmp_path / "v4.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == 4
            assert "governance_approval_use" not in _tables(conn)
            assert "runtime_execution" not in _tables(conn)
            assert classify_legacy_database(conn, 4) == LegacyDatabaseClass.TRUE_V4
        finally:
            conn.close()

        # Open through the production factory: v4 -> v5 via the real chain.
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            assert "governance_approval_use" in _tables(conn)
            assert "runtime_execution" in _tables(conn)
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
                " AND name='ux_approval_use_decision'"
            ).fetchone() is not None
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
                " AND name='ix_approval_use_step'"
            ).fetchone() is not None
            # Old rows preserved by the additive migration.
            assert conn.execute(
                "SELECT repository_id FROM repository_record"
            ).fetchone()[0] == "repo-a"
            # Ledger records the real v4 -> v5 identity.
            entries = MigrationRunner(conn, clock=lambda: "t").ledger()
            assert any(
                (e.from_version, e.to_version) == (4, 5)
                and e.migration_id == "P2-R5-0005-post-v4-execution-and-grant-use"
                for e in entries
            )
        finally:
            conn.close()

    def test_true_v3_migrates_through_v4_to_v5(self, tmp_path) -> None:
        db = tmp_path / "v3.sqlite3"
        _true_v3(db)
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            assert V5_ONLY_TABLES <= _tables(conn)
            entries = MigrationRunner(conn, clock=lambda: "t").ledger()
            identities = [(e.from_version, e.to_version) for e in entries]
            assert (3, 4) in identities and (4, 5) in identities
            assert conn.execute(
                "SELECT repository_id FROM repository_record"
            ).fetchone()[0] == "repo-a"
        finally:
            conn.close()


class TestLegacyMisversioned:
    def _misversioned(self, db) -> None:
        """Historical bug shape: physical P2 tables, PRAGMA user_version == 1."""
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.executescript(RUNTIME_DDL)
        conn.executescript(APPROVAL_DDL)
        conn.execute(
            "INSERT INTO runtime_job (job_id, deterministic_id, status, job_type,"
            " payload_json, payload_digest) VALUES"
            " ('job-legacy-1','det-1','SUCCEEDED','GENERIC','{}','d1')"
        )
        conn.execute(
            "INSERT INTO runtime_step (step_id, job_id, status, step_type,"
            " payload_json, payload_digest) VALUES"
            " ('job-legacy-1:s-1','job-legacy-1','SUCCEEDED','GENERIC','{}','d1')"
        )
        conn.execute(
            "INSERT INTO governance_approval_request (request_id, principal,"
            " action, payload_json, payload_digest, created_at) VALUES"
            " ('req-legacy-1','w','a','{}','d1','2026-01-01T00:00:00Z')"
        )
        # The bug: version says 1 while physical P2 state exists.
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()

    def test_known_misversioned_is_classified_and_migrated(self, tmp_path) -> None:
        db = tmp_path / "legacy.sqlite3"
        self._misversioned(db)
        conn = open_raw_connection(db)
        try:
            assert _version(conn) == 1
            assert classify_legacy_database(conn, 1) == (
                LegacyDatabaseClass.KNOWN_P2_MISVERSIONED
            )
        finally:
            conn.close()

        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            assert V5_ONLY_TABLES <= _tables(conn)
            # All legacy runtime/governance rows preserved.
            assert conn.execute(
                "SELECT status FROM runtime_job WHERE job_id='job-legacy-1'"
            ).fetchone()[0] == "SUCCEEDED"
            assert conn.execute(
                "SELECT status FROM runtime_step WHERE step_id='job-legacy-1:s-1'"
            ).fetchone()[0] == "SUCCEEDED"
            assert conn.execute(
                "SELECT principal FROM governance_approval_request"
                " WHERE request_id='req-legacy-1'"
            ).fetchone()[0] == "w"
        finally:
            conn.close()

    def test_misversioned_p1_metadata_still_migrates(self, tmp_path) -> None:
        db = tmp_path / "legacy-p1.sqlite3"
        conn = open_metadata_db(db)
        conn.execute(
            "INSERT INTO evidence_artifact (evidence_id, subject_id, object_type,"
            " evidence_class, artifact_digest, producer, created_at,"
            " payload_json, payload_digest) VALUES"
            " ('ev-1','subj','CAPABILITY','E2_SOURCE','a','p','t','{}','d')"
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        conn = open_metadata_db(db)
        try:
            assert _version(conn) == 5
            assert conn.execute(
                "SELECT evidence_id FROM evidence_artifact"
            ).fetchone()[0] == "ev-1"
        finally:
            conn.close()


class TestFailClosed:
    def test_unknown_hybrid_refused(self, tmp_path) -> None:
        db = tmp_path / "hybrid.sqlite3"
        conn = open_raw_connection(db)
        # v2 stamp with runtime tables present: contradictory shape.
        conn.executescript(RUNTIME_DDL)
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

    def test_partial_p2_shape_refused(self, tmp_path) -> None:
        db = tmp_path / "partial.sqlite3"
        conn = open_raw_connection(db)
        # Only part of the runtime shape: not a recognized historical DB.
        conn.execute(
            "CREATE TABLE runtime_job (job_id TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

    def test_v4_claiming_post_v4_tables_refused(self, tmp_path) -> None:
        db = tmp_path / "lying-v4.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.executescript(V5_ADDITIONS_DDL)
        conn.execute("PRAGMA user_version = 4")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="unknown hybrid"):
            open_metadata_db(db)

    def test_newer_schema_refused(self, tmp_path) -> None:
        db = tmp_path / "newer.sqlite3"
        conn = open_metadata_db(db)
        conn.execute("PRAGMA user_version = 6")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="not openable by this build"):
            open_metadata_db(db)

    def test_failed_migration_rolls_back(self, tmp_path) -> None:
        db = tmp_path / "rollback.sqlite3"
        conn = open_raw_connection(db)
        conn.executescript(
            "CREATE TABLE evidence_artifact (evidence_id TEXT PRIMARY KEY)"
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()

        def broken(c) -> None:
            c.execute("CREATE TABLE half_written (x TEXT)")
            raise RuntimeError("injected migration crash")

        bad = Migration(from_version=1, to_version=2,
                        migration_id="P2-R5R-TEST-BROKEN", apply=broken)
        runner = MigrationRunner(conn, clock=lambda: "t")
        conn.execute("DELETE FROM schema_migration_ledger")
        conn.commit()
        with pytest.raises(RuntimeError, match="injected migration crash"):
            runner.migrate_to(2, {2: bad})
        assert _version(conn) == 1
        assert runner.ledger() == []
        assert "half_written" not in _tables(conn)
        conn.close()


class TestNoHiddenCompletion:
    def test_build_local_runtime_refuses_incomplete_db_claiming_v5(
        self, tmp_path
    ) -> None:
        """Composition root must NOT silently complete schema v5 with raw DDL."""
        db = tmp_path / "stamped.sqlite3"
        conn = open_metadata_db(db)
        # Strip the runtime shape but keep the v5 stamp: the DB now lies.
        for table in ("runtime_job", "runtime_step", "runtime_job_event",
                      "runtime_checkpoint", "runtime_idempotency",
                      "runtime_execution", "runtime_queue_claim",
                      "runtime_budget", "governance_approval_use"):
            conn.execute(f"DROP TABLE {table}")
        conn.execute("PRAGMA user_version = 5")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError):
            build_local_runtime(db)
        # And nothing was silently created by the failed attempt.
        probe = open_raw_connection(db)
        try:
            assert "runtime_job" not in _tables(probe)
            assert "runtime_execution" not in _tables(probe)
        finally:
            probe.close()

    def test_build_local_runtime_adds_no_tables(self, tmp_path) -> None:
        db = tmp_path / "clean.sqlite3"
        seed = open_metadata_db(db)
        before = _tables(seed)
        seed.close()
        rt = build_local_runtime(db)
        try:
            assert _tables(rt.conn) == before
            assert _version(rt.conn) == CURRENT_SCHEMA_VERSION
        finally:
            rt.conn.close()


class TestOnePhysicalSchema:
    """v5 must be ONE physical schema, however it was reached."""

    _AUTHORITY_DDL = (
        RUNTIME_DDL_MIGRATION,
        V5_ADDITIONS_DDL,
    )

    def _authority_ddl(self) -> tuple:
        from qcae.infrastructure.persistence.sqlite_approval_registry import (
            APPROVAL_DDL,
        )
        from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
        from qcae.infrastructure.persistence.sqlite_policy_log import GOVERNANCE_DDL
        from qcae.infrastructure.persistence.sqlite_runtime_store import RUNTIME_DDL
        from qcae.infrastructure.queue.sqlite_step_queue import QUEUE_INTEGRITY_DDL

        return self._AUTHORITY_DDL + (
            RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
            APPROVAL_DDL,
        )

    def _authority_shape(self, conn) -> set:
        tables = set()
        for ddl in self._authority_ddl():
            scratch = open_raw_connection(":memory:")
            try:
                scratch.executescript(ddl)
                tables |= {
                    r[0] for r in scratch.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")
                }
            finally:
                scratch.close()
        shape = set()
        for kind, name, sql in conn.execute(
            "SELECT type, name, sql FROM sqlite_master"
            " WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall():
            text = (sql or "").strip()
            if kind == "table" and name in tables:
                shape.add((kind, name, text))
            elif kind == "index" and any(t in text for t in tables):
                shape.add((kind, name, text))
        return shape

    def test_fresh_v5_and_migrated_v5_are_the_same_physical_schema(
        self, tmp_path
    ) -> None:
        fresh = open_metadata_db(tmp_path / "fresh5.sqlite3")
        fresh_shape = self._authority_shape(fresh)
        fresh.close()

        db = tmp_path / "migrated5.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.execute("DELETE FROM schema_migration_ledger")
        conn.commit()
        MigrationRunner(conn, clock=lambda: "t").migrate_to(5, {5: V4_TO_V5})
        migrated_shape = self._authority_shape(conn)
        conn.close()

        assert fresh_shape, "authority schema empty"
        assert fresh_shape == migrated_shape, (
            f"only fresh: {sorted(fresh_shape - migrated_shape)}; "
            f"only migrated: {sorted(migrated_shape - fresh_shape)}"
        )


class TestV5Additions:
    def test_v5_creates_only_genuinely_post_v4_structures(self) -> None:
        conn = open_raw_connection(":memory:")
        conn.executescript(V5_ADDITIONS_DDL)
        names = _tables(conn)
        assert names == set(V5_ONLY_TABLES)
        conn.close()

    def test_v4_to_v5_preserves_rows_and_adds_tables(self, tmp_path) -> None:
        db = tmp_path / "preserve.sqlite3"
        _true_v4(db)
        conn = open_raw_connection(db)
        conn.executescript(
            "INSERT INTO runtime_job (job_id, deterministic_id, status, job_type,"
            " payload_json, payload_digest) VALUES"
            " ('job-keep','det','RUNNING','GENERIC','{\"a\":1}','d')"
        )
        conn.commit()
        conn.execute("DELETE FROM schema_migration_ledger")
        conn.commit()
        runner = MigrationRunner(conn, clock=lambda: "2026-01-01T00:00:00Z")
        runner.migrate_to(5, {5: V4_TO_V5})
        assert _version(conn) == 5
        assert conn.execute(
            "SELECT payload_json FROM runtime_job WHERE job_id='job-keep'"
        ).fetchone()[0] == '{"a":1}'
        entry = runner.ledger()[0]
        assert entry.pre_digest != entry.post_digest
        conn.close()
