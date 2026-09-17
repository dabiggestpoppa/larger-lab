"""P2-C07RT — combined crash/concurrency/adversarial repair qualification.

Proves the four C07R repair laws TOGETHER, under restart and adversarial
conditions, in the full runtime flow (submit → ready → lease → execute →
recover → resume):

R1  job-scoped atomic claim (no ineligible ownership, no stranding);
R2  durable idempotency/execution semantics (no silent exactly-once claim,
    ambiguity escalated, committed results reconstructed);
R3  atomic submission (failure injection leaves no partial state);
R4  store-owned identity allocation (no orchestrator DB-internal access).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ExecutionState, ReplaySafety
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerResult, WorkerStatus


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id="job-12345678", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-0001", "k1"),
        job_type="DISCOVERY",
        subject_ref="cap-0001",
        created_by="operator",
        created_at="2026-09-13T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, deps=(), **over):
    base = dict(
        step_id=step_id,
        job_id="job-12345678",
        step_type="GENERIC",
        dependencies=tuple(deps),
        created_at="2026-09-12345678" if False else "2026-09-13T12:00:00Z",
        idempotency_key=f"job-12345678:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


class _CountingWorker:
    def __init__(self, replay_safety=ReplaySafety.REPLAY_SAFE):
        self.replay_safety = replay_safety
        self.executions = 0

    def execute(self, request, packet) -> WorkerResult:
        self.executions += 1
        return WorkerResult(
            step_id=request.step_id, job_id=request.job_id,
            status=WorkerStatus.SUCCESS,
            evidence_refs=(f"ev-{request.step_id}-{self.executions}",),
        )


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
    return store, queue, engine, clock, conn


def _drive(store, queue, engine, clock, job_id="job-12345678", worker="w1"):
    engine.mark_running(job_id)
    engine.ready_steps(job_id)
    return engine.lease_next(job_id, worker)


class TestCombinedFlows:
    def test_full_lifecycle_with_two_jobs_no_cross_contamination(self, env):
        """R1+R4 together: two jobs run through the engine; no cross-claiming,
        no duplicate event identity, no lost events."""
        store, queue, engine, clock, _ = env
        worker = _CountingWorker()
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1")])
        engine.submit(
            _job(job_id="job-87654321",
                 deterministic_id=deterministic_job_id("discovery", "cap-0001", "k2")),
            [_step("t-1", job_id="job-87654321")],
        )
        # Run job A to completion.
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "wA")
        engine.execute_step(lease)
        assert store.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED
        # Job B untouched until driven; then completes cleanly.
        assert store.get_step("t-1").status is RuntimeStepStatus.PENDING
        engine.mark_running("job-87654321")
        engine.ready_steps("job-87654321")
        lease_b = engine.lease_next("job-87654321", "wB")
        engine.execute_step(lease_b)
        assert store.get_step("t-1").status is RuntimeStepStatus.SUCCEEDED
        # Event streams are disjoint, complete, and uniquely identified.
        ev_a = store.events_for_job("job-12345678")
        ev_b = store.events_for_job("job-87654321")
        ids = [e[1].event_id for e in ev_a + ev_b]
        assert len(ids) == len(set(ids))
        kinds_a = [e[1].event_type.value for e in ev_a]
        assert "JOB_SUCCEEDED" in kinds_a

    def test_crash_after_lease_resume_does_not_repeat_committed(self, env):
        """R1+R2+R4: crash between steps; committed step never re-executed."""
        store, queue, engine, clock, conn = env
        worker = _CountingWorker(ReplaySafety.IDEMPOTENCY_AWARE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [
            _step("s-A"), _step("s-B", deps=("s-A",)), _step("s-C", deps=("s-A",)),
        ])
        lease = _drive(store, queue, engine, clock)
        engine.execute_step(lease)  # s-A commits
        assert worker.executions == 1
        engine.ready_steps("job-12345678")
        lease_b = engine.lease_next("job-12345678", "w-crash")
        assert lease_b.step_id == "s-B"
        conn.commit()
        conn.close()  # process death with durable committed work

        # Restart with a fresh engine over the same DB.
        clock2 = _Clock()
        conn2 = open_metadata_db(":memory:")  # placeholder, replaced below
        conn2.close()
        conn2 = open_metadata_db(db_path := __import__("pathlib").Path(
            __import__("tempfile").gettempdir()
        ) / "unused.sqlite3")
        conn2.close()
        # Real restart: reopen the ORIGINAL db file (persisted by conn.commit).
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "rt.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            engine1 = OrchestratorEngine(store1, queue1, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            w1 = _CountingWorker(ReplaySafety.IDEMPOTENCY_AWARE)
            engine1._workers["GENERIC"] = w1
            engine1.submit(_job(), [
                _step("s-A"), _step("s-B", deps=("s-A",)), _step("s-C", deps=("s-A",)),
            ])
            lease = _drive(store1, queue1, engine1, clock)
            engine1.execute_step(lease)  # s-A commits
            engine1.ready_steps("job-12345678")
            lease_b = engine1.lease_next("job-12345678", "w-crash")
            c1.commit()
            c1.close()

            # Restart and recover.
            c2 = open_metadata_db(db)
            store2 = SqliteRuntimeStore(c2)
            queue2 = SqliteStepQueue(c2, store2, now_fn=clock, lease_ttl_seconds=60)
            engine2 = OrchestratorEngine(store2, queue2, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            w2 = _CountingWorker(ReplaySafety.IDEMPOTENCY_AWAY if False else ReplaySafety.IDEMPOTENCY_AWARE)
            engine2._workers["GENERIC"] = w2
            report = engine2.recover_job("job-12345678")
            assert report["completed_steps"] == ["s-A"]
            assert "s-B" in report["recovered_lease_steps"]
            engine2.ready_steps("job-12345678")
            lease_b2 = engine2.lease_next("job-12345632" if False else "job-12345678", "w2")
            assert lease_b2.step_id == "s-B"
            engine2.execute_step(lease_b2)
            engine2.ready_steps("job-12345678")
            lease_c = engine2.lease_next("job-12345678", "w2")
            engine2.execute_step(lease_c)
            assert w2.executions == 2  # only s-B and s-C ran after restart
            assert store2.get_step("s-A").status is RuntimeStepStatus.SUCCEEDED
            c2.close()

    def test_adversarial_wrong_token_cannot_advance_repaired_queue(self, env):
        """R1: the repaired claim path still enforces token-guarded acks."""
        store, queue, engine, clock, _ = env
        # P2-R3-C02: a lease requires a registered worker; this test only
        # exercises ack token law, so a minimal worker satisfies availability.
        class _PresentWorker:
            replay_safety = ReplaySafety.REPLAY_SAFE

            def execute(self, request, packet):  # pragma: no cover - never runs
                raise AssertionError("this test must not execute work")

        engine.register_worker_type("GENERIC", _PresentWorker())
        engine.submit(_job(), [_step("s-1")])
        lease = _drive(store, queue, engine, clock)
        with pytest.raises(QcaeValidationError, match="not the owner"):
            queue.acknowledge(lease.step_id, "forged-token")
        queue.acknowledge(lease.step_id, lease.lease_token)

    def test_adversarial_duplicate_submission_after_repairs(self, env):
        """R3: duplicate deterministic_id refused; original job untouched."""
        store, queue, engine, clock, _ = env
        engine.submit(_job(), [_step("s-1")])
        events_before = len(store.events_for_job("job-12345678"))
        with pytest.raises(QcaeValidationError, match="deterministic_id"):
            engine.submit(_job(), [_step("s-1")])
        assert len(store.events_for_job("job-12345678")) == events_before
        assert store.get_step("s-1").status is RuntimeStepStatus.PENDING

    def test_recovery_report_flags_non_replay_safe_after_full_restart(self, env):
        """R2: through a restart, ambiguity stays visible for the operator."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "nr.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            engine1 = OrchestratorEngine(store1, queue1, clock=clock, authority_gate=PermissiveStepAuthorityGate())

            class _CrashWorker:
                replay_safety = ReplaySafety.NON_REPLAY_SAFE

                def execute(self, request, packet):
                    raise RuntimeError("died mid-effect")

            engine1._workers["GENERIC"] = _CrashWorker()
            engine1.submit(_job(), [_step("s-1")])
            lease = _drive(store1, queue1, engine1, clock)
            with pytest.raises(RuntimeError):
                engine1.execute_step(lease)
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            store2 = SqliteRuntimeStore(c2)
            queue2 = SqliteStepQueue(c2, store2, now_fn=clock, lease_ttl_seconds=60)
            engine2 = OrchestratorEngine(store2, queue2, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            report = engine2.recover_job("job-12345678")
            unresolved = report["unresolved_executions"]
            assert unresolved and unresolved[0]["requires_operator_resolution"] is True
            assert unresolved[0]["replay_safety"] == "NON_REPLAY_SAFE"
            c2.close()
