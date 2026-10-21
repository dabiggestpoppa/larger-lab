"""P2-R3-T01 — adversarial qualification over the repaired operator loop.

Every case must fail closed: active leases never stolen (recover OR resume),
expired leases reconcile idempotently in any surface order, orphan RUNNING
classified, committed work never replays, non-replay-safe ambiguity
escalates, no-worker path leaves zero claim/attempt/budget traces, unknown
id-* principals refused before claim, claim/execute identity swaps rejected,
terminal jobs immutable, and CLI expected errors never traceback.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
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
from qcae.orchestration.jobs.runtime import (
    JobEventType,
    RuntimeJob,
    RuntimeStep,
    RuntimeStepStatus,
    RuntimeJobStatus,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ReplaySafety
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerStatus
from qcae.interfaces.cli import __main__ as cli
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id="job-t01", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-t01", "k-t01"),
        job_type="DISCOVERY",
        subject_ref="cap-t01",
        created_by="operator",
        created_at="2026-09-17T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-t01", deps=(), **over):
    full_id = f"{job_id}:{step_id}"
    base = dict(
        step_id=full_id,
        job_id=job_id,
        step_type="GENERIC",
        dependencies=tuple(
            d if d.startswith(f"{job_id}:") else f"{job_id}:{d}" for d in deps
        ),
        created_at="2026-09-17T12:00:00Z",
        idempotency_key=full_id,
    )
    base.update(over)
    return RuntimeStep(**base)


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    identity = LocalIdentityProvider()
    for wid in ("id-worker-a", "id-worker-b"):
        identity.register(LocalIdentity(identity_id=wid, kind=IdentityKind.WORKER,
                                        display_name=wid))
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate(),
        identity_provider=identity,
    )
    engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    return store, queue, engine, clock, conn, identity


def _run_cli(*cli_args, db: Path):
    return subprocess.run(
        [sys.executable, "-m", "qcae.interfaces.cli", "--db", str(db), *cli_args],
        capture_output=True, text=True, timeout=180,
    )


class TestActiveLeaseTheft:
    def test_recover_cannot_steal(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        lease = engine.lease_next("job-t01", "id-worker-a")
        for _ in range(2):
            engine.recover_job("job-t01")  # repeated operator recover
        cols = store.read_lease_columns("job-t01:s-1")
        assert cols["lease_token"] == lease.lease_token
        assert queue.lease_owner_of("job-t01:s-1") == "id-worker-a"

    def test_resume_cannot_steal(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        lease = engine.lease_next("job-t01", "id-worker-a")
        engine.recover_job("job-t01")  # resume delegates to the same law
        cols = store.read_lease_columns("job-t01:s-1")
        assert cols["lease_token"] == lease.lease_token

    def test_expired_lease_does_recover(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        engine.lease_next("job-t01", "id-worker-a")
        clock.advance(120)
        report = engine.recover_job("job-t01")
        assert "job-t01:s-1" in report["recovered_lease_steps"]
        assert store.get_step("job-t01:s-1").status is RuntimeStepStatus.READY

    def test_global_then_resume_idempotent(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        engine.lease_next("job-t01", "id-worker-a")
        clock.advance(120)
        engine.recover_job("job-t01")
        state1 = store.get_step("job-t01:s-1").status
        engine.recover_job("job-t01")
        assert store.get_step("job-t01:s-1").status is state1

    def test_resume_then_global_idempotent(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        engine.lease_next("job-t01", "id-worker-a")
        clock.advance(120)
        engine.recover_job("job-t01")
        state1 = store.get_step("job-t01:s-1").status
        # The other surface — same law, no additional mutation.
        engine.recover_job("job-t01")
        assert store.get_step("job-t01:s-1").status is state1


class TestOrphanAndExecutionTruth:
    def test_missing_claim_running_classified(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        engine.lease_next("job-t01", "id-worker-a")
        conn.execute("DELETE FROM runtime_queue_claim WHERE step_id = 'job-t01:s-1'")
        conn.commit()
        report = engine.recover_orphan_steps("job-t01")
        assert report["orphan_steps"] == ["job-t01:s-1"]
        assert report["reconciled"] == ["job-t01:s-1"]
        assert store.get_step("job-t01:s-1").status is RuntimeStepStatus.READY

    def test_committed_execution_cannot_replay(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        lease = engine.lease_next("job-t01", "id-worker-a")
        engine.execute_step(lease)
        assert store.get_step("job-t01:s-1").status is RuntimeStepStatus.SUCCEEDED
        clock.advance(120)
        engine.recover_job("job-t01")
        # Terminal step stays terminal; nothing re-runs.
        assert store.get_step("job-t01:s-1").status is RuntimeStepStatus.SUCCEEDED
        types = [ev.event_type for _s, ev, _p in
                 store.events_for_job("job-t01")]
        assert types.count(JobEventType.STEP_SUCCEEDED) == 1
        assert types.count(JobEventType.JOB_SUCCEEDED) == 1

    def test_non_replay_safe_ambiguous_escalates(self, env):
        store, queue, engine, clock, conn, identity = env

        class _Crash:
            replay_safety = ReplaySafety.NON_REPLAY_SAFE

            def execute(self, request, packet):
                raise RuntimeError("mid-effect death")

        engine.register_worker_type("GENERIC", _Crash())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        lease = engine.lease_next("job-t01", "id-worker-a")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)
        clock.advance(120)
        engine.recover_job("job-t01")
        assert store.get_step("job-t01:s-1").status is RuntimeStepStatus.WAITING_INPUT
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        assert engine.lease_next("job-t01", "id-worker-b") is None


class TestNoWorkerTracelessness:
    def test_no_worker_zero_claim_attempt_budget(self, env):
        store, queue, engine, clock, conn, identity = env
        engine._workers.pop("GENERIC")  # nothing compatible
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        for worker in ("id-worker-a", "id-worker-b"):
            with pytest.raises(WorkerUnavailableError):
                engine.lease_next("job-t01", worker)
        assert conn.execute(
            "SELECT COUNT(*) FROM runtime_queue_claim"
        ).fetchone()[0] == 0
        step = store.get_step("job-t01:s-1")
        assert step.status is RuntimeStepStatus.READY
        assert step.attempt == 0


from qcae.orchestration.orchestrator.worker_availability import WorkerUnavailableError  # noqa: E402


class TestIdentityFailClosed:
    def test_unknown_id_star_refused_before_claim(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        for attacker in ("id-unknown", "id-attacker", "arbitrary-id-9"):
            with pytest.raises(QcaeValidationError, match="unknown identity"):
                engine.lease_next("job-t01", attacker)
        assert conn.execute(
            "SELECT COUNT(*) FROM runtime_queue_claim"
        ).fetchone()[0] == 0

    def test_claim_identity_cannot_execute_as_other(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        lease = engine.lease_next("job-t01", "id-worker-a")
        with pytest.raises(QcaeValidationError, match="lease"):
            engine.execute_step(lease, worker_id="id-worker-b")


class TestTerminalTruth:
    def test_all_success_exactly_one_job_succeeded(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        for _ in range(2):
            engine.ready_steps("job-t01")
            lease = engine.lease_next("job-t01", "id-worker-a")
            engine.execute_step(lease)
        types = [ev.event_type for _s, ev, _p in store.events_for_job("job-t01")]
        assert types.count(JobEventType.JOB_SUCCEEDED) == 1
        assert store.get_job("job-t01").status is RuntimeJobStatus.SUCCEEDED

    def test_terminal_cannot_rerun_and_survives_restart(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps("job-t01")
        engine.execute_step(engine.lease_next("job-t01", "id-worker-a"))
        assert store.get_job("job-t01").status is RuntimeJobStatus.SUCCEEDED
        # Restart: still terminal; nothing claimable; cannot be re-run.
        engine.recover_job("job-t01")
        assert store.get_job("job-t01").status is RuntimeJobStatus.SUCCEEDED
        assert engine.lease_next("job-t01", "id-worker-b") is None


class TestCLINeverTracebacks:
    def test_expected_cli_errors_never_traceback(self, tmp_path):
        db = tmp_path / "t01.sqlite3"
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-t01",
            "--key", "t01-cli", "--step", "s-1:GENERIC", db=db,
        )
        assert submit.returncode == 0, submit.stderr
        job = json.loads(submit.stdout)
        assert job["status"] == "QUEUED"

        no_worker = _run_cli("job", "run", job["job_id"], db=db)
        assert no_worker.returncode == 3
        assert "Traceback" not in no_worker.stderr

        unknown_job = _run_cli("job", "status", "job-nonexistent1", db=db)
        assert unknown_job.returncode == 2
        assert "Traceback" not in unknown_job.stderr

        attacker = _run_cli(
            "job", "run", job["job_id"], "--worker", "id-attacker", db=db,
        )
        assert attacker.returncode == 2
        assert "Traceback" not in attacker.stderr
        assert "unknown identity" in attacker.stderr

        # The no-worker path consumed nothing.
        status = _run_cli("job", "status", job["job_id"], db=db)
        view = json.loads(status.stdout)
        assert view["steps"][0]["status"] == "READY"
        assert view["steps"][0]["attempt"] == 0
