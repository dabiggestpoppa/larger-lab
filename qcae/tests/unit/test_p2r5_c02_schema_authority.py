"""P2-R5-C02 — schema authority (directive §16 / schema invariant).

Schema invariant: ``PRAGMA user_version == CURRENT_SCHEMA_VERSION ==
RuntimeIdentity.schema_version == freeze manifest schema version`` (all == 5).

Historical migrations are immutable; ``V4_TO_V5`` is additive for
``governance_approval_use``. Production startup migrates; a legacy
misversioned database is refused with a clear error.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.backup_restore import BackupService
from qcae.infrastructure.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    MigrationRunner,
    V3_TO_V4,
    V4_TO_V5,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import (
    CURRENT_SCHEMA_VERSION as FACTORY_CURRENT,
    open_metadata_db,
    open_raw_connection,
)
from qcae.governance.standalone.runtime_service import LocalRuntimeService
from qcae.interfaces.cli.app import build_local_runtime
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStepStatus


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TestSchemaInvariant:
    def test_constant_equals_five(self) -> None:
        assert CURRENT_SCHEMA_VERSION == 5
        assert FACTORY_CURRENT == 5

    def test_open_metadata_db_creates_at_current_version(self, tmp_path) -> None:
        db = tmp_path / "fresh.sqlite3"
        conn = open_metadata_db(db)
        try:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            assert version == CURRENT_SCHEMA_VERSION == 5
        finally:
            conn.close()

    def test_migration_chain_brings_v4_to_v5(self, tmp_path) -> None:
        db = tmp_path / "migrate.sqlite3"
        conn = open_metadata_db(db)
        conn.executescript(RUNTIME_DDL)
        conn.executescript(APPROVAL_DDL)
        conn.execute("PRAGMA user_version = 4")
        conn.commit()
        conn.close()

        conn2 = open_raw_connection(str(db))
        conn2.executescript(
            "CREATE TABLE IF NOT EXISTS schema_migration_ledger ("
            "seq INTEGER PRIMARY KEY AUTOINCREMENT, from_version INTEGER, "
            "to_version INTEGER, migration_id TEXT, applied_at TEXT, "
            "pre_digest TEXT, post_digest TEXT)"
        )
        runner = MigrationRunner(conn2, clock=_iso_now)
        assert runner.current_version() == 4
        runner.migrate_to(5, {5: V4_TO_V5})
        assert runner.current_version() == 5
        assert len(runner.ledger()) == 1
        assert runner.ledger()[0].migration_id == V4_TO_V5.migration_id
        conn2.close()

    def test_v4_to_v5_is_additive_preserves_approval_use_rows(self, tmp_path) -> None:
        db = tmp_path / "additive.sqlite3"
        conn = open_metadata_db(db)
        conn.executescript(RUNTIME_DDL)
        conn.executescript(APPROVAL_DDL)
        approvals = SqliteApprovalRegistry(conn)
        from qcae.governance.standalone.approvals import GrantUse

        use = GrantUse(
            use_id="use-1", decision_ref="dec-1", step_id="s-1",
            used_at="2026-11-07T00:00:00Z",
        )
        approvals.mark_grant_used(use)
        conn.execute("PRAGMA user_version = 4")
        conn.commit()
        conn.close()

        conn2 = open_raw_connection(str(db))
        conn2.executescript(
            "CREATE TABLE IF NOT EXISTS schema_migration_ledger ("
            "seq INTEGER PRIMARY KEY AUTOINCREMENT, from_version INTEGER, "
            "to_version INTEGER, migration_id TEXT, applied_at TEXT, "
            "pre_digest TEXT, post_digest TEXT)"
        )
        runner = MigrationRunner(conn2, clock=_iso_now)
        runner.migrate_to(5, {5: V4_TO_V5})
        uses = SqliteApprovalRegistry(conn2).uses_for_decision("dec-1")
        assert len(uses) == 1
        assert uses[0].step_id == "s-1"
        assert conn2.execute(
            "SELECT 1 FROM sqlite_master WHERE name='ix_approval_use_step'"
        ).fetchone() is not None
        conn2.close()

    def test_historical_migrations_immutable(self) -> None:
        assert V3_TO_V4.from_version == 3
        assert V3_TO_V4.to_version == 4
        assert V3_TO_V4.migration_id == "P2-0004-runtime-governance-tables"
        assert V4_TO_V5.from_version == 4
        assert V4_TO_V5.to_version == 5


class TestBuildLocalRuntimeRunsMigrations:
    def test_build_local_runtime_reports_current_schema(self, tmp_path) -> None:
        db = tmp_path / "runtime.sqlite3"
        rt = build_local_runtime(db)
        identity = rt.service.identity()
        assert identity.schema_version == CURRENT_SCHEMA_VERSION == 5

    def test_db_left_at_current_version_after_build(self, tmp_path) -> None:
        db = tmp_path / "runtime2.sqlite3"
        build_local_runtime(db)
        conn = open_metadata_db(db)
        try:
            assert (
                int(conn.execute("PRAGMA user_version").fetchone()[0])
                == CURRENT_SCHEMA_VERSION
            )
        finally:
            conn.close()


class TestLegacyMisversionedDatabase:
    def test_database_newer_than_current_refused(self, tmp_path) -> None:
        db = tmp_path / "new.sqlite3"
        conn = open_metadata_db(db)
        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION + 1}")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="newer than this build"):
            open_metadata_db(db)

    def test_legacy_database_without_production_chain_refused(self, tmp_path) -> None:
        db = tmp_path / "legacy.sqlite3"
        conn = open_metadata_db(db)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        with pytest.raises(QcaeValidationError, match="legacy misversioned"):
            open_metadata_db(db)

    def test_database_at_current_opens_cleanly(self, tmp_path) -> None:
        db = tmp_path / "current.sqlite3"
        conn = open_metadata_db(db)
        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
        conn.commit()
        conn.close()
        conn2 = open_metadata_db(db)
        try:
            assert (
                int(conn2.execute("PRAGMA user_version").fetchone()[0])
                == CURRENT_SCHEMA_VERSION
            )
        finally:
            conn2.close()


class TestBackupManifestSchema:
    def test_manifest_schema_version_matches_current(self, tmp_path) -> None:
        db = tmp_path / "backup.sqlite3"
        conn = open_metadata_db(db)
        manifest = BackupService(conn).backup(tmp_path / "backupdir")
        assert manifest["schema_version"] == CURRENT_SCHEMA_VERSION == 5
        conn.close()
