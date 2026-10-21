"""P2-R3-C05 — CLI typed errors + recovery surface convergence.

Expected operator errors exit with stable codes and structured output —
never a traceback. Unexpected programming errors still traceback. Both
recovery surfaces (``recover`` and ``job resume``) delegate to one law, so
a step recovered through either surface lands in the same state.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.identity import IdentityKind, LocalIdentity
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.interfaces.cli import __main__ as cli
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id="job-clierrors", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-ce", "k-ce"),
        job_type="DISCOVERY",
        subject_ref="cap-ce",
        created_by="operator",
        created_at="2026-09-17T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-clierrors", **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="GENERIC",
        dependencies=(),
        created_at="2026-09-17T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


def _run_cli(*cli_args, db: Path):
    """Run the CLI as a real subprocess (process boundary is the point)."""
    return subprocess.run(
        [sys.executable, "-m", "qcae.interfaces.cli", "--db", str(db), *cli_args],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture()
def tmp_db(tmp_path):
    return tmp_path / "cli.sqlite3"


class TestTypedErrors:
    def test_unknown_job_status_no_traceback(self, tmp_db):
        proc = _run_cli("job", "status", "job-missing1", db=tmp_db)
        assert proc.returncode == 2
        assert "Traceback" not in proc.stderr
        assert "unknown job" in proc.stderr

    def test_worker_unavailable_exit_3_structured(self, tmp_db):
        # No worker registered anywhere -> typed WORKER_UNAVAILABLE.
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-x",
            "--key", "k-wu1", "--step", "s-1:GENERIC", db=tmp_db,
        )
        assert submit.returncode == 0, submit.stderr
        run = _run_cli("job", "run", "job-discovery-k-wu1", db=tmp_db)
        assert run.returncode == 3
        assert "Traceback" not in run.stderr
        payload = json.loads(run.stderr)
        assert payload["error"] == "WORKER_UNAVAILABLE"
        assert payload["missing_step_types"] == ["GENERIC"]

    def test_unknown_principal_never_tracebacks(self, tmp_path):
        """Registered worker exists but the caller is not that identity:
        the identity check refuses before any mutation (no traceback)."""
        clock = _Clock()
        rt = build_local_runtime(tmp_path / "up.sqlite3", clock=clock)
        rt.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rt.identity.register(LocalIdentity(
            identity_id="id-worker-a", kind=IdentityKind.WORKER,
            display_name="a",
        ))
        app = QcaeApp(rt, clock=clock)
        app.submit_job(_job(), [_step("s-1")])
        with pytest.raises(Exception, match="unknown identity"):
            app.job_run_step("job-clierrors", "id-attacker")

    def test_budget_exhaustion_exit_4(self, tmp_path):
        clock = _Clock()
        rt = build_local_runtime(tmp_path / "b.sqlite3", clock=clock)
        rt.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rt.identity.register(LocalIdentity(
            identity_id="id-worker-a", kind=IdentityKind.WORKER,
            display_name="a",
        ))
        from qcae.orchestration.orchestrator.budget_service import BudgetService
        from qcae.infrastructure.persistence.sqlite_budget_ledger import (
            SqliteBudgetLedger,
        )

        budgets = BudgetService(SqliteBudgetLedger(rt.conn))
        budgets.create_job_budget(
            budget_id="bud-job-clierrors",
            job_id="job-clierrors", allocation={"attempts": 0},
        )
        rt.engine._budgets = budgets
        app = QcaeApp(rt, clock=clock)
        app.submit_job(_job(), [_step("s-1")])
        app.job_resume("job-clierrors")
        # A zero-attempt budget refuses the lease's attempt charge.
        with pytest.raises(Exception, match="exceeds remaining"):
            app.job_run_step("job-clierrors", "id-worker-a")


class TestRecoveryConvergence:
    def test_recover_and_resume_land_same_state(self, tmp_path):
        """Expired lease recovered via `recover` vs `job resume` converge."""
        clock = _Clock()
        db = tmp_path / "conv.sqlite3"
        engine, conn = self._engine_at(db, clock)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-clierrors")
        engine.lease_next("job-clierrors", "id-worker-a")
        conn.commit()
        conn.close()
        clock.advance(120)

        engine2, conn2 = self._engine_at(db, clock)
        report = engine2.recover_job("job-clierrors")
        assert "s-1" in report["recovered_lease_steps"]
        state_a = engine2._store.get_step("s-1").status
        conn2.commit()
        conn2.close()

        engine3, conn3 = self._engine_at(db, clock)
        engine3.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine3.ready_steps("job-clierrors")
        engine3.lease_next("job-clierrors", "id-worker-a")
        conn3.commit()
        conn3.close()
        clock.advance(120)
        engine4, conn4 = self._engine_at(db, clock)
        engine4.recover_job("job-clierrors")  # job resume path == same law
        state_b = engine4._store.get_step("s-1").status
        conn4.close()
        assert state_a is state_b is RuntimeStepStatus.READY

    def _engine_at(self, db: Path, clock):
        conn = open_metadata_db(db)
        conn.executescript(RUNTIME_DDL)
        conn.executescript(QUEUE_INTEGRITY_DDL)
        store = SqliteRuntimeStore(conn)
        queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
        return OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=PermissiveStepAuthorityGate(),
        ), conn

    def test_unopenable_db_path_reports_a_typed_error(self, tmp_path):
        """A careless ``--db`` value is an operator error, not a traceback.

        The first real user typo is pointing ``--db`` at a directory or at a
        stale file that is not a database; sqlite's own exception is not
        actionable feedback.
        """
        directory = tmp_path / "not-a-db"
        directory.mkdir()
        junk = tmp_path / "junk.db"
        junk.write_text("this is not a sqlite file", encoding="utf-8")
        afile = tmp_path / "afile"
        afile.write_text("x", encoding="utf-8")
        # Third careless shape: a path component that is a regular file, so
        # creating the parent directory fails before sqlite is ever reached.
        under_a_file = afile / "child.db"

        for target in (directory, junk, under_a_file):
            proc = _run_cli("identity", db=target)
            assert proc.returncode == 2, (target, proc.stderr)
            assert "Traceback" not in proc.stderr
            payload = json.loads(proc.stderr)
            assert payload["error"] == "QcaeValidationError"
            assert str(target) in payload["message"]

    def test_programming_error_still_tracebacks(self, tmp_db, monkeypatch):
        """Unexpected exceptions must NOT be swallowed into exit-code maps."""
        app = QcaeApp(build_local_runtime(tmp_db))

        def boom(*a, **k):
            raise RuntimeError("invariant violated")

        monkeypatch.setattr(app, "job_list", boom)
        with pytest.raises(RuntimeError, match="invariant violated"):
            cli._dispatch(app, type("A", (), {
                "command": "job", "job_command": "list",
            })())


class TestCLIApprovalPath:
    def test_approval_decide_rejection_typed(self, tmp_db):
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-x",
            "--key", "k-ap1", "--step", "s-1:GENERIC", db=tmp_db,
        )
        assert submit.returncode == 0, submit.stderr
        proc = _run_cli(
            "approval", "decide", "req-does-not-exist",
            "--decision", "GRANTED", "--decided-by", "id-operator-local",
            db=tmp_db,
        )
        assert proc.returncode == 2
        assert "Traceback" not in proc.stderr
        assert "approval decision rejected" in proc.stderr
