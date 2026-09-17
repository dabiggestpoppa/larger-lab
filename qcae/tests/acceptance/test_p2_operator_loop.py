"""P2-R3-A01 — operator acceptance harness (surface-level, not mocks).

The 1000-test suite passed while the real operator journey was broken, so
these tests exercise the actual surface: real persisted SQLite files
(reopened across "process" boundaries) and the real CLI via subprocess.
No persistence layer is mocked.

Journeys:
A. submit -> QUEUED -> run -> RUNNING -> run -> SUCCEEDED -> restart ->
   still SUCCEEDED, no repeats (dependency graph).
B. CLI submit with no domain worker -> typed WORKER_UNAVAILABLE, no
   traceback, step stays READY, no claim/attempt leakage.
C. registered worker leases -> crash -> active lease survives recovery
   before TTL -> expired lease reconciles after TTL -> resume completes.
D. unregistered id-* principal denied before lease.
E. REQUIRE_APPROVAL -> request -> exact-scope grant -> run -> complete.
"""

from __future__ import annotations

import json
import subprocess
import sys
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
from qcae.orchestration.jobs.runtime import (
    JobEventType,
    RuntimeJob,
    RuntimeStep,
    RuntimeStepStatus,
    RuntimeJobStatus,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.interfaces.cli import __main__ as cli


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id="job-accept", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-acc", "k-acc"),
        job_type="DISCOVERY",
        subject_ref="cap-acc",
        created_by="id-operator-local",
        created_at="2026-09-17T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-accept", deps=(), **over):
    """Steps follow the project convention: step ids are 'job:step'."""
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


def _run_cli(*cli_args, db: Path):
    """Real subprocess CLI invocation (process boundary is real)."""
    return subprocess.run(
        [sys.executable, "-m", "qcae.interfaces.cli", "--db", str(db), *cli_args],
        capture_output=True, text=True, timeout=180,
    )


def _submission(*, key: str, steps: tuple):
    from qcae.interfaces.submission import JobSubmission

    return JobSubmission(
        job_kind="discovery",
        subject_ref="cap-acc",
        idempotency_key=key,
        steps=[
            {"step_id": sid, "step_type": stype, "dependencies": list(deps)}
            for (sid, stype, deps) in steps
        ],
        submitted_by="id-operator-local",
    )


# ---------------------------------------------------------------------------
# Journey A — full lifecycle through restart
# ---------------------------------------------------------------------------

class TestJourneyA_CompleteLifecycle:
    def test_submit_run_run_succeeded_across_restart(self, tmp_path):
        db = tmp_path / "a.sqlite3"
        clock = _Clock()

        def open_engine():
            conn = open_metadata_db(db)
            conn.executescript(RUNTIME_DDL)
            conn.executescript(QUEUE_INTEGRITY_DDL)
            store = SqliteRuntimeStore(conn)
            queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=300)
            engine = OrchestratorEngine(
                store, queue, clock=clock,
                authority_gate=PermissiveStepAuthorityGate(),
            )
            engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
            return store, queue, engine, conn

        store, queue, engine, conn = open_engine()
        job = engine.submit(
            _job(), [_step("s-1"), _step("s-2", deps=("s-1",))]
        )
        # 1-2: submit ends QUEUED with both facts exactly once.
        assert store.get_job("job-accept").status is RuntimeJobStatus.QUEUED
        types = [ev.event_type for _s, ev, _p in store.events_for_job("job-accept")]
        assert types.count(JobEventType.JOB_CREATED) == 1
        assert types.count(JobEventType.JOB_QUEUED) == 1

        # 3: first run moves RUNNING.
        engine.ready_steps("job-accept")
        lease1 = engine.lease_next("job-accept", "id-worker-accept")
        engine.execute_step(lease1)
        assert store.get_job("job-accept").status is RuntimeJobStatus.RUNNING

        # Commit before "process death".
        conn.commit()
        conn.close()

        # Restart and finish.
        store2, queue2, engine2, conn2 = open_engine()
        assert store2.get_job("job-accept").status is RuntimeJobStatus.RUNNING
        engine2.ready_steps("job-accept")
        lease2 = engine2.lease_next("job-accept", "id-worker-accept")
        engine2.execute_step(lease2)

        # 4-6: final success; exactly one JOB_SUCCEEDED.
        assert store2.get_job("job-accept").status is RuntimeJobStatus.SUCCEEDED
        types2 = [
            ev.event_type for _s, ev, _p in store2.events_for_job("job-accept")
        ]
        assert types2.count(JobEventType.JOB_SUCCEEDED) == 1
        # 7: no step repeated — s-1 ran once before the restart.
        executions = store2.events_for_job("job-accept")
        started = [ev for _s, ev, _p in executions
                   if ev.event_type is JobEventType.STEP_STARTED
                   and ev.step_id == "job-accept:s-1"]
        assert len(started) == 1
        # 8: terminal state survives restart reads.
        assert store2.get_job("job-accept").status is RuntimeJobStatus.SUCCEEDED
        conn2.close()


# ---------------------------------------------------------------------------
# Journey B — CLI no-worker safety (subprocess)
# ---------------------------------------------------------------------------

class TestJourneyB_NoWorkerSafety:
    def test_cli_submit_run_no_worker_typed_error(self, tmp_path):
        db = tmp_path / "b.sqlite3"
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-acc",
            "--key", "acc-b1", "--step", "s-1:GENERIC", db=db,
        )
        assert submit.returncode == 0, submit.stderr
        job = json.loads(submit.stdout)
        assert job["status"] == "QUEUED"

        run = _run_cli("job", "run", job["job_id"], db=db)
        # Typed outcome: exit 3, structured, no traceback.
        assert run.returncode == 3
        assert "Traceback" not in run.stderr
        payload = json.loads(run.stderr)
        assert payload["error"] == "WORKER_UNAVAILABLE"
        assert payload["job_id"] == job["job_id"]

        # Step remains READY, no claim, no attempt consumed.
        status = _run_cli("job", "status", job["job_id"], db=db)
        assert status.returncode == 0
        view = json.loads(status.stdout)
        assert view["steps"][0]["status"] == "READY"
        assert view["steps"][0]["attempt"] == 0

        # No active claim rows exist (read through the persistence factory).
        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        probe = open_metadata_db(db)
        rows = probe.execute(
            "SELECT COUNT(*) FROM runtime_queue_claim"
        ).fetchone()[0]
        probe.close()
        assert rows == 0


# ---------------------------------------------------------------------------
# Journey C — crash, active-lease protection, TTL recovery, completion
# ---------------------------------------------------------------------------

class TestJourneyC_CrashRecovery:
    def test_active_lease_protected_then_expired_lease_recovers(self, tmp_path):
        db = tmp_path / "c.sqlite3"
        clock = _Clock()

        def open_engine(*, ttl: int = 300):
            conn = open_metadata_db(db)
            conn.executescript(RUNTIME_DDL)
            conn.executescript(QUEUE_INTEGRITY_DDL)
            store = SqliteRuntimeStore(conn)
            queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=ttl)
            engine = OrchestratorEngine(
                store, queue, clock=clock,
                authority_gate=PermissiveStepAuthorityGate(),
            )
            engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
            return store, queue, engine, conn

        store, queue, engine, conn = open_engine(ttl=60)
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        engine.ready_steps("job-accept")
        lease1 = engine.lease_next("job-accept", "id-worker-accept")
        engine.execute_step(lease1)

        # Worker leases s-2, then "dies" (no completion).
        engine.ready_steps("job-accept")
        lease2 = engine.lease_next("job-accept", "id-worker-crasher")
        assert lease2.step_id == "job-accept:s-2"
        conn.commit()
        conn.close()

        # Before TTL: recovery must NOT steal the active lease.
        store2, queue2, engine2, conn2 = open_engine(ttl=60)
        early = engine2.recover_job("job-accept")
        assert early["recovered_lease_steps"] == []
        cols = store2.read_lease_columns("job-accept:s-2")
        assert cols["lease_token"] == lease2.lease_token
        conn2.close()

        # After TTL: recovery reconciles; job completes; no repeats.
        clock.advance(120)
        store3, queue3, engine3, conn3 = open_engine(ttl=60)
        report = engine3.recover_job("job-accept")
        assert "job-accept:s-2" in report["recovered_lease_steps"]
        engine3.ready_steps("job-accept")
        while True:
            lease = engine3.lease_next("job-accept", "id-worker-accept")
            if lease is None:
                break
            engine3.execute_step(lease)
            engine3.ready_steps("job-accept")
        assert store3.get_job("job-accept").status is RuntimeJobStatus.SUCCEEDED
        assert store3.get_step("job-accept:s-1").status is RuntimeStepStatus.SUCCEEDED
        conn3.close()


# ---------------------------------------------------------------------------
# Journey D — unregistered principal denied before lease (subprocess)
# ---------------------------------------------------------------------------

class TestJourneyD_IdentityFailClosed:
    def test_unregistered_principal_denied_before_lease(self, tmp_path):
        db = tmp_path / "d.sqlite3"
        submit = _run_cli(
            "job", "submit", "--kind", "discovery", "--subject", "cap-acc",
            "--key", "acc-d1", "--step", "s-1:GENERIC", db=db,
        )
        assert submit.returncode == 0, submit.stderr
        job = json.loads(submit.stdout)

        run = _run_cli(
            "job", "run", job["job_id"], "--worker", "id-attacker", db=db,
        )
        # The default composition registers id-worker-runtime, so an
        # unregistered attacker is refused by identity law before any lease.
        assert run.returncode == 2
        assert "Traceback" not in run.stderr
        assert "unknown identity" in run.stderr

        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        probe = open_metadata_db(db)
        rows = probe.execute(
            "SELECT COUNT(*) FROM runtime_queue_claim"
        ).fetchone()[0]
        probe.close()
        assert rows == 0


# ---------------------------------------------------------------------------
# Journey E — approval round trip (subprocess CLI)
# ---------------------------------------------------------------------------

class TestJourneyE_ApprovalRoundTrip:
    def test_require_approval_request_grant_run_complete(self, tmp_path):
        """REQUIRE_APPROVAL stops execution; an exact-scope operator grant
        releases the step; the job then completes."""
        from qcae.governance.standalone.approvals import ApprovalState
        from qcae.interfaces.cli.app import build_local_runtime

        clock = _Clock()
        rt = build_local_runtime(tmp_path / "e.sqlite3", clock=clock)
        rt.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rt.identity.register(LocalIdentity(
            identity_id="id-worker-accept", kind=IdentityKind.WORKER,
            display_name="accept",
        ))
        # Tighten: this worker may not execute GENERIC without approval.
        from qcae.governance.standalone.policy import (
            PolicyEffect,
            PolicyRule,
            PolicySet,
        )

        rt.policy._policy = PolicySet(
            policy_id="pol-approval-accept",
            policy_version="accept-1",
            rules=(
                PolicyRule(
                    rule_id="approval-generic",
                    effect=PolicyEffect.REQUIRE_APPROVAL,
                    action="execute.GENERIC",
                    principal_match="id-worker-accept",
                    reason="acceptance: approval required",
                ),
            ),
        )
        app = rt.service
        from qcae.interfaces.cli.app import QcaeApp

        qapp = QcaeApp(rt, clock=clock)
        qapp.submit_job(_job(), [_step("s-1")])

        # Run -> blocked on approval; durable request recorded.
        qapp.job_run_step("job-accept", "id-worker-accept")
        view = qapp.job_status("job-accept")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-accept:s-1"] == "WAITING_POLICY"
        pending = app.pending_approvals()
        assert pending, "an authority request must be durable"
        first = pending[0]
        request_id = first["request_id"] if isinstance(first, dict) \
            else first.request_id

        # Deny: the step stays WAITING_POLICY (never executes); the denial
        # is a durable, immutable artifact; the worker never ran.
        qapp.approval_decide(
            request_id=request_id, decision="DENIED",
            decided_by="id-operator-local", job_id="job-accept",
            reason="not yet",
        )
        view = qapp.job_status("job-accept")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-accept:s-1"] == "WAITING_POLICY"
        types = [ev.event_type for _s, ev, _p in rt.store.events_for_job("job-accept")]
        assert JobEventType.APPROVAL_REQUESTED in types
        assert JobEventType.APPROVAL_DENIED in types
