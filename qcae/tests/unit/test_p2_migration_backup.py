"""P2-C12 — migration v3→v4 + backup/restore of runtime state (directive §37-38)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
)
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.migrations import (
    MigrationRunner,
    MIGRATION_LEDGER_DDL,
    V3_TO_V4,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import SqliteBudgetLedger
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    SqliteRuntimeStore,
    RUNTIME_DDL,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.budget_service import BudgetService


def _clock():
    return lambda: "2026-09-13T12:00:00Z"


def _job(job_id="job-12345678"):
    return RuntimeJob(
        job_id=job_id,
        deterministic_id=deterministic_job_id("d", "c", job_id),
        job_type="D", subject_ref="cap-1", created_by="op",
        created_at="2026-09-13T12:00:00Z",
    )


def _step(step_id, job_id="job-12345678", **over):
    base = dict(
        step_id=step_id, job_id=job_id, step_type="GENERIC",
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


class TestMigrationV3ToV4:
    def _seed_v3(self, db: Path):
        """Build a v3 database: base schema + P1 registry tables, version=3."""
        from qcae.infrastructure.persistence.sqlite_repository_registry import (
            REPOSITORY_REGISTRY_DDL,
        )
        from qcae.infrastructure.persistence.migrations import REPOSITORY_REVISION_DDL

        conn = open_metadata_db(db)
        conn.executescript(MIGRATION_LEDGER_DDL)
        conn.executescript(REPOSITORY_REGISTRY_DDL)
        conn.executescript(REPOSITORY_REVISION_DDL)
        conn.execute("PRAGMA user_version = 3")
        return conn

    def test_v3_database_migrates_to_v4_preserving_registry(self, tmp_path):
        db = tmp_path / "meta.sqlite3"
        conn = self._seed_v3(db)
        # Seed P1 registry rows.
        payload = json.dumps({
            "repository_id": "repo-1", "revision": "abc",
            "source_kind": "GIT", "canonical_locator": "https://example",
        })
        conn.execute(
            "INSERT INTO repository_record (repository_id, revision, source_kind,"
            " canonical_locator, payload_json, payload_digest) VALUES"
            " ('repo-1', 'abc', 'GIT', 'https://example', ?, ?)",
            (payload, "digest-placeholder"),
        )
        conn.commit()
        conn.close()

        # Migrate to v4 (raw connection: user_version=3 precedes this
        # build's base schema version, which is expected mid-migration).
        from qcae.infrastructure.persistence.store_factory import open_raw_connection

        conn2 = open_raw_connection(db)
        conn2.executescript(MIGRATION_LEDGER_DDL)
        runner2 = MigrationRunner(conn2, clock=_clock())
        assert runner2.current_version() == 3
        runner2.migrate_to(4, {4: V3_TO_V4})
        assert runner2.current_version() == 4
        # P1 data preserved.
        rows = conn2.execute(
            "SELECT COUNT(*) FROM repository_record").fetchone()[0]
        assert rows == 1
        # Runtime tables exist and are empty.
        assert conn2.execute(
            "SELECT COUNT(*) FROM runtime_job").fetchone()[0] == 0
        assert conn2.execute(
            "SELECT COUNT(*) FROM governance_escalation").fetchone()[0] == 0
        conn2.close()

    def test_v4_runtime_store_writable_after_migration(self, tmp_path):
        db = tmp_path / "m2.sqlite3"
        conn = self._seed_v3(db)
        runner = MigrationRunner(conn, clock=_clock())
        runner.migrate_to(4, {4: V3_TO_V4})
        store = SqliteRuntimeStore(conn)
        store.add_job(_job())
        store.add_step(_step("s-1"))
        assert store.get_job("job-12345678") is not None
        assert store.get_step("s-1") is not None
        conn.close()


class TestBackupRestoreRuntime:
    def _seed_runtime_state(self, db: Path):
        from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
        from qcae.infrastructure.persistence.sqlite_approval_registry import (
            APPROVAL_DDL,
        )

        conn = open_metadata_db(db)
        for ddl in (RUNTIME_DDL, BUDGET_DDL, APPROVAL_DDL):
            conn.executescript(ddl)
        store = SqliteRuntimeStore(conn)
        store.add_job(_job(status=None) if False else _job())
        store.add_step(_step("job-12345678:s-1", status=RuntimeStepStatus.SUCCEEDED))
        store.put_checkpoint("cp-1", "job-12345678", "", {"done": ["s-1"]},
                             "2026-09-13T12:00:00Z")
        ledger = SqliteBudgetLedger(conn)
        svc = BudgetService(ledger)
        svc.create_job_budget("bud-job-1", "job-12345678", {"attempts": 3})
        svc.charge("bud-job-1", "attempts", 1)
        approvals = SqliteApprovalRegistry(conn)
        approvals.add_request(ApprovalRequest(
            request_id="req-00000041", principal="w", action="a", resource="r",
            scope="s", budget_ref="b", justification="j",
            created_at="2026-09-13T12:00:00Z",
        ))
        approvals.record_decision(ApprovalDecision(
            decision_id="dec-00000041", request_ref="req-00000041",
            state=ApprovalState.GRANTED, decided_by="op",
            decided_at="2026-09-13T12:00:00Z",
            bound_action="a", bound_resource="r", bound_scope="s",
            bound_budget_ref="b", reason="ok",
        ))
        conn.commit()
        return conn

    def test_full_cycle_backup_restore(self, tmp_path):
        db = tmp_path / "runtime.sqlite3"
        conn = self._seed_runtime_state(db)
        conn.close()

        backup_dir = tmp_path / "backup"
        conn_b = open_metadata_db(db)
        manifest = BackupService(conn_b).backup(backup_dir)
        conn_b.close()
        # Runtime tables counted in the manifest (§38 coverage).
        assert manifest["registry_rows"]["runtime_job"] == 1
        assert manifest["registry_rows"]["runtime_step"] == 1
        assert manifest["registry_rows"]["runtime_checkpoint"] == 1
        assert manifest["registry_rows"]["runtime_budget"] == 1
        assert manifest["registry_rows"]["governance_approval_request"] == 1
        assert manifest["registry_rows"]["governance_approval_decision"] == 1

        # Destroy live state and restore.
        db.unlink()
        restored_db = tmp_path / "restored.sqlite3"
        RestoreService().restore(backup_dir, restored_db, tmp_path / "artifacts")

        conn_r = open_metadata_db(restored_db)
        conn_r.executescript(RUNTIME_DDL)
        store = SqliteRuntimeStore(conn_r)
        job = store.get_job("job-12345678")
        assert job is not None
        step = store.get_step("job-12345678:s-1")
        assert step.status is RuntimeStepStatus.SUCCEEDED  # completed stays completed
        assert store.get_checkpoint("cp-1") == {"done": ["s-1"]}
        budget = SqliteBudgetLedger(conn_r).get("bud-job-1")
        assert budget.used["attempts"] == 1  # consumption survives (no reset)
        approvals = SqliteApprovalRegistry(conn_r)
        grant = approvals.effective_grant("req-00000041", now="2026-09-13T12:01:00Z")
        assert grant is not None
        conn_r.close()

    def test_stale_leases_recovered_after_restore(self, tmp_path):
        from qcae.infrastructure.queue.sqlite_step_queue import (
            QUEUE_INTEGRITY_DDL,
            SqliteStepQueue,
        )

        db = tmp_path / "r2.sqlite3"
        conn = self._seed_runtime_state(db)
        conn.executescript(QUEUE_INTEGRITY_DDL)
        store = SqliteRuntimeStore(conn)
        queue = SqliteStepQueue(conn, store, now_fn=_clock(), lease_ttl_seconds=60)
        store.add_step(_step("job-12345678:s-2", status=RuntimeStepStatus.READY))
        queue.claim_next("w-crashed")
        conn.commit()
        conn.close()

        backup_dir = tmp_path / "backup2"
        conn_b = open_metadata_db(db)
        conn_b.executescript(QUEUE_INTEGRITY_DDL)
        BackupService(conn_b).backup(backup_dir)
        conn_b.close()

        restored_db = tmp_path / "restored2.sqlite3"
        RestoreService().restore(backup_dir, restored_db, tmp_path / "art2")
        conn_r = open_metadata_db(restored_db)
        conn_r.executescript(RUNTIME_DDL)
        conn_r.executescript(QUEUE_INTEGRITY_DDL)
        store = SqliteRuntimeStore(conn_r)
        queue = SqliteStepQueue(conn_r, store, now_fn=lambda: "2026-09-13T13:00:00Z",
                                lease_ttl_seconds=60)
        # The stale lease is recoverable, not permanently valid (§38/§58).
        recovered = queue.expire_stale_leases()
        assert "job-12345678:s-2" in recovered
        conn_r.close()
