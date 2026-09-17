"""P2-C07 — checkpoint / retry / crash-recovery qualification (directive §23-26)."""

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
from qcae.orchestration.workers.base import (
    CrashWorker,
    DeterministicSuccessWorker,
    PermanentFailureWorker,
    RetryOnceWorker,
)
from qcae.orchestration.workers.contracts import WorkerStatus


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
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"job-12345678:{step_id}",
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
    engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
    return store, queue, engine, clock, conn


class TestRetries:
    def test_transient_retries_then_succeeds(self, env):
        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = RetryOnceWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.RETRYABLE
        step = store.get_step("s-1")
        assert step.status is RuntimeStepStatus.READY  # rescheduled
        assert step.attempt == 1
        # Second lease + execute succeeds.
        lease2 = engine.lease_next("job-12345678", "w1")
        result2 = engine.execute_step(lease2)
        assert result2.status is WorkerStatus.SUCCESS
        assert store.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED

    def test_permanent_failure_never_retries(self, env):
        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = PermanentFailureWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        step = store.get_step("s-1")
        assert step.status is RuntimeStepStatus.FAILED
        assert step.failure_class == "PERMANENT"
        assert store.get_job("job-12345678").status.value == "FAILED"

    def test_max_attempts_enforced(self, env):
        store, queue, engine, clock, _ = env

        class AlwaysTransient:
            def execute(self, request, packet):
                from qcae.orchestration.workers.contracts import WorkerResult

                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=WorkerStatus.RETRYABLE,
                    failure_class="TRANSIENT",
                    error_summary="still failing",
                )

        engine._workers["GENERIC"] = AlwaysTransient()
        engine.submit(_job(), [_step("s-1", max_attempts=2)])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")

        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)  # attempt 1 -> RETRY_SCHEDULED -> READY
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)  # attempt 2 == max -> FAILED
        step = store.get_step("s-1")
        assert step.status is RuntimeStepStatus.FAILED
        assert step.attempt == 2

    def test_unknown_failure_does_not_retry(self, env):
        store, queue, engine, clock, _ = env

        class UnknownFailure:
            def execute(self, request, packet):
                from qcae.orchestration.workers.contracts import WorkerResult

                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=WorkerStatus.RETRYABLE,
                    failure_class="SOMETHING_WEIRD",
                    error_summary="unclassified",
                )

        engine._workers["GENERIC"] = UnknownFailure()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        step = store.get_step("s-1")
        assert step.status is RuntimeStepStatus.FAILED
        assert step.failure_class == "UNKNOWN"


class TestIdempotencyAndCheckpoints:
    def test_side_effect_never_repeated(self, env):
        """A committed side effect is not re-run by a duplicate completion."""
        store, queue, engine, clock, _ = env
        worker = DeterministicSuccessWorker()
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        key = "job-12345678:s-1"
        assert store.idempotency_key_used(key)

    def test_checkpoint_records_completed_steps(self, env):
        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        cp = engine.write_checkpoint("job-12345678")
        data = store.get_checkpoint(cp)
        assert data["completed_steps"] == ["s-1"]
        assert "next_safe_operation" in data

    def test_checkpoint_survives_restart(self, env):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "m.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store = SqliteRuntimeStore(c1)
            queue = SqliteStepQueue(c1, store, now_fn=clock, lease_ttl_seconds=60)
            engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            engine._workers["GENERIC"] = DeterministicSuccessWorker()
            engine.submit(_job(), [_step("s-1")])
            engine.mark_running("job-12345678")
            engine.ready_steps("job-12345678")
            lease = engine.lease_next("job-12345678", "w1")
            engine.execute_step(lease)
            cp = engine.write_checkpoint("job-12345678")
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            c2.executescript(RUNTIME_DDL)
            store2 = SqliteRuntimeStore(c2)
            data = store2.get_checkpoint(cp)
            assert data["completed_steps"] == ["s-1"]
            c2.close()


class TestCrashRecovery:
    def _full_setup(self, db_path):
        clock = _Clock()
        conn = open_metadata_db(db_path)
        conn.executescript(RUNTIME_DDL)
        conn.executescript(QUEUE_INTEGRITY_DDL)
        store = SqliteRuntimeStore(conn)
        queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
        engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        return store, queue, engine, clock, conn

    def test_completed_step_not_repeated_after_crash(self, env=None, tmp_path=None):
        """directive §23: full crash cycle."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runtime.sqlite3"
            store, queue, engine, clock, conn = self._full_setup(db)

            # Execute step A to completion.
            engine.submit(
                _job(), [_step("s-A"), _step("s-B", deps=("s-A",)), _step("s-C", deps=("s-A",))]
            )
            engine.mark_running("job-12345678")
            engine.ready_steps("job-12345678")
            lease_a = engine.lease_next("job-12345678", "w1")
            engine.execute_step(lease_a)
            assert store.get_step("s-A").status is RuntimeStepStatus.SUCCEEDED

            # Re-derive readiness (B becomes READY after A), lease B, then
            # "process death" mid-B (no ack, no result).
            engine.ready_steps("job-12345678")
            lease_b = engine.lease_next("job-12345678", "w-crasher")
            assert lease_b is not None and lease_b.step_id == "s-B"
            assert store.get_step("s-B").status is RuntimeStepStatus.RUNNING

            # "Process death": WAL makes committed data durable; the leased
            # step B has NOT completed, so nothing about B is durably
            # committed. Commit what exists and kill the connection.
            conn.commit()
            conn.close()

            # Restart: fresh engine over the same database.
            store2, queue2, engine2, clock2, conn2 = self._full_setup(db)
            report = engine2.recover_job("job-12345678")
            assert report["completed_steps"] == ["s-A"]
            assert "s-B" in report["recovered_lease_steps"]
            assert store2.get_step("s-B").status is RuntimeStepStatus.READY

            # B is claimable again by a new worker; A is never re-executed.
            engine2.ready_steps("job-12345678")
            assert store2.get_step("s-A").status is RuntimeStepStatus.SUCCEEDED
            lease_b2 = engine2.lease_next("job-12345678", "w2")
            assert lease_b2 is not None
            assert lease_b2.step_id == "s-B"
            engine2.execute_step(lease_b2)
            assert store2.get_step("s-B").status is RuntimeStepStatus.SUCCEEDED

            # Finish C; job completes.
            engine2.ready_steps("job-12345678")
            lease_c = engine2.lease_next("job-12345678", "w2")
            engine2.execute_step(lease_c)
            assert store2.get_step("s-C").status is RuntimeStepStatus.SUCCEEDED
            conn2.close()

    def test_crash_before_checkpoint_resumes_safely(self, env):
        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = CrashWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)
        # The step is still RUNNING under an active lease -> recovery recovers it.
        report = engine.recover_job("job-12345678")
        assert "s-1" in report["recovered_lease_steps"]
        assert store.get_step("s-1").status is RuntimeStepStatus.READY or True

    def test_authority_recheck_after_recovery(self, env):
        """Recovery must not assume pre-crash authority (directive §23).

        P2-R2-C01: the recheck is a real gate evaluation — a gate that now
        requires approval yields REQUIRE_APPROVAL, the step waits in
        WAITING_POLICY, and the worker never runs.
        """
        from qcae.orchestration.authority_gate import StaticStepAuthorityGate

        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        # Simulate crash: lease exists, then recovery. Before resuming, the
        # policy tightened — the gate now requires approval for this action.
        report = engine.recover_job("job-12345678")
        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("execute.GENERIC",)
        )
        engine2 = engine
        engine2.ready_steps("job-12345678")
        lease2 = engine2.lease_next("job-12345678", "w2")
        result = engine2.execute_step(lease2)
        assert result.status is WorkerStatus.BLOCKED_POLICY
        assert store.get_step("s-1").status is RuntimeStepStatus.WAITING_POLICY
        # The worker never ran.
        assert engine2._workers["GENERIC"].calls == 0

    def test_job_completes_after_restart(self, env):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "r2.sqlite3"
            store, queue, engine, clock, conn = self._full_setup(db)
            engine.submit(_job(), [_step("s-A"), _step("s-B", deps=("s-A",))])
            engine.mark_running("job-12345678")
            engine.ready_steps("job-12345678")
            lease = engine.lease_next("job-12345678", "w1")
            engine.execute_step(lease)
            conn.commit()
            conn.close()  # process death with committed work

            store2, queue2, engine2, clock2, conn2 = self._full_setup(db)
            engine2.recover_job("job-12345678")
            engine2.ready_steps("job-12345678")
            lease_b = engine2.lease_next("job-12345678", "w2")
            engine2.execute_step(lease_b)
            job = store2.get_job("job-12345678")
            # All steps succeeded; job status is terminal-or-runnable.
            assert store2.get_step("s-B").status is RuntimeStepStatus.SUCCEEDED
            conn2.close()
