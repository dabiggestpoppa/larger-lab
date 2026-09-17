"""P2-C07R2 — durable idempotency / execution semantics (repair directive §2.2).

Crash-window law under test:

- the idempotency key is RESERVED before execution;
- COMMITTED reconstructs the prior result without re-executing;
- unresolved EXECUTING after a crash is never silently treated as safe;
- NON_REPLAY_SAFE ambiguity escalates to explicit recovery, never a rerun;
- the orchestrator claims at-least-once + durable dedup, never exactly-once.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

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
from qcae.orchestration.orchestrator.execution import (
    ExecutionRecord,
    ExecutionState,
    ReplaySafety,
)
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import (
    WorkerRequest,
    WorkerResult,
    WorkerStatus,
)
from qcae.core.jobs import deterministic_job_id


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


class _CounterWorker:
    """Records every real execution; classifies its replay safety."""

    def __init__(self, replay_safety=ReplaySafety.REPLAY_SAFE, effect=0):
        self.replay_safety = replay_safety
        self.effect = effect
        self.executions = 0

    def execute(self, request: WorkerRequest, packet) -> WorkerResult:
        self.executions += 1
        return WorkerResult(
            step_id=request.step_id,
            job_id=request.job_id,
            status=WorkerStatus.SUCCESS,
            evidence_refs=(f"ev-{request.idempotency_key}-{self.executions}",),
        )


class _CrashMidExecutionWorker:
    """Simulates death after the effect but before returning a result."""

    def __init__(self):
        self.executions = 0

    def execute(self, request: WorkerRequest, packet) -> WorkerResult:
        self.executions += 1
        raise RuntimeError("process death mid-execution")


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


def _drive_ready(store, queue, engine, clock, job_id="job-12345678"):
    engine.mark_running(job_id)
    engine.ready_steps(job_id)
    return engine.lease_next(job_id, "w1")


class TestExecutionRecordBasics:
    def test_record_round_trip_and_validation(self, env):
        store, _, _, clock, _ = env
        assert store.reserve_execution("k1", "job-12345678", "s-1",
                                       ReplaySafety.IDEMPOTENCY_AWARE, clock())
        rec = store.get_execution_record("k1")
        assert rec.state is ExecutionState.RESERVED
        # Duplicate reservation is deterministic: refused.
        assert not store.reserve_execution("k1", "job-12345678", "s-1",
                                           ReplaySafety.IDEMPOTENCY_AWARE, clock())
        # Advance to EXECUTING then COMMITTED with a durable result.
        from dataclasses import replace

        store.update_execution_record(
            replace(rec, state=ExecutionState.EXECUTING)
        )
        result = WorkerResult(
            step_id="s-1", job_id="job-12345678",
            status=WorkerStatus.SUCCESS, evidence_refs=("ev-1",),
        )
        assert store.commit_execution("k1", result, clock())
        committed = store.get_execution_record("k1")
        assert committed.state is ExecutionState.COMMITTED
        # Reconstruction returns the prior result without re-execution.
        rebuilt = committed.reconstruct_result()
        assert rebuilt.evidence_refs == ("ev-1",)
        assert not store.commit_execution("k1", result, clock())  # idempotent

    def test_uncommitted_record_has_no_result(self, env):
        store, _, _, clock, _ = env
        store.reserve_execution("k2", "job-12345678", "s-1",
                                ReplaySafety.REPLAY_SAFE, clock())
        with pytest.raises(Exception, match="no committed result"):
            store.get_execution_record("k2").reconstruct_result()

    def test_illegal_execution_transition_rejected(self, env):
        from qcae.orchestration.orchestrator.execution import (
            assert_execution_transition,
        )
        from qcae.core.errors import QcaeStateTransitionError

        with pytest.raises(QcaeStateTransitionError):
            assert_execution_transition(
                ExecutionState.COMMITTED, ExecutionState.RESERVED
            )


class TestCrashWindows:
    """Directive §2.2 crash windows A-G."""

    def test_window_A_crash_before_worker_execution(self, env):
        """Reservation durable, no execution: recovery re-leases safely."""
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.REPLAY_SAFE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1")])
        lease = _drive_ready(store, queue, engine, clock)
        # Reserve happened? No — lease only. Simulate: reserve then die before
        # the worker runs.
        key = "job-12345678:s-1"
        store.reserve_execution(key, "job-12345678", "s-1",
                                ReplaySafety.REPLAY_SAFE, clock())
        report = engine.recover_job("job-12345678")
        assert report["unresolved_executions"][0]["idempotency_key"] == key
        assert report["unresolved_executions"][0]["requires_operator_resolution"] is False
        # REPLAY_SAFE: re-execution is harmless and allowed.
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        engine.execute_step(lease2)
        assert worker.executions == 1  # died before executing; ran once total

    def test_window_B_crash_during_execution_no_commit(self, env):
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.IDEMPOTENCY_AWARE)
        crasher = _CrashMidExecutionWorker()
        crasher.replay_safety = ReplaySafety.IDEMPOTENCY_AWARE
        engine._workers["GENERIC"] = crasher
        engine.submit(_job(), [_step("s-1")])
        lease = _drive_ready(store, queue, engine, clock)
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)
        # EXECUTING record unresolved; recovery reports it.
        report = engine.recover_job("job-12345678")
        unresolved = {u["idempotency_key"]: u for u in report["unresolved_executions"]}
        assert unresolved["job-12345678:s-1"]["state"] == "EXECUTING"
        assert crasher.executions == 1
        # Retry executes exactly one more time (at-least-once, dedup by key).
        engine._workers["GENERIC"] = worker
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        engine.execute_step(lease2)
        assert worker.executions == 1
        assert store.get_execution_record("job-12345678:s-1").state \
            is ExecutionState.COMMITTED

    def test_window_C_effect_committed_result_recorded(self, env):
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.IDEMPOTENCY_AWARE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1")])
        lease = _drive_ready(store, queue, engine, clock)
        engine.execute_step(lease)
        rec = store.get_execution_record("job-12345678:s-1")
        assert rec.state is ExecutionState.COMMITTED
        assert worker.executions == 1

    def test_window_D_effect_committed_marker_lost_reconstructs(self, env):
        """Effect committed, orchestrator died before step-state transition."""
        store, queue, engine, clock, conn = env
        worker = _CounterWorker(ReplaySafety.IDEMPOTENCY_AWARE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        lease = _drive_ready(store, queue, engine, clock)
        engine.execute_step(lease)
        assert worker.executions == 1
        conn.commit()

        # "Crash" before the graph advanced. New engine over same DB; the
        # execution record is COMMITTED so the retry reconstructs.
        engine2 = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
        engine2._workers["GENERIC"] = worker
        engine2.mark_running("job-12345678")
        # s-1 already succeeded; s-2 becomes ready. Give s-2 the same
        # idempotency key as the committed s-1 record BEFORE leasing (no lease
        # columns to preserve yet), simulating the duplicate-completion path.
        engine2.ready_steps("job-12345678")
        from dataclasses import replace

        step2 = replace(store.get_step("s-2"), idempotency_key="job-12345678:s-1")
        store.update_step(step2)
        lease2 = engine2.lease_next("job-12345678", "w2")
        assert lease2.step_id == "s-2"
        result = engine2.execute_step(lease2)
        # No re-execution: the prior committed result is reconstructed.
        assert worker.executions == 1
        assert result.evidence_refs == ("ev-job-12345678:s-1-1",)

    def test_window_E_duplicate_retry_after_committed(self, env):
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.REPLAY_SAFE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1")])
        lease = _drive_ready(store, queue, engine, clock)
        engine.execute_step(lease)
        assert worker.executions == 1
        # A second lease of the same (terminal) step would fail lease law, so
        # prove dedup at the store contract level: re-execution with the same
        # key reconstructs and never reaches the worker.
        from qcae.orchestration.orchestrator.execution import ReplaySafety as RS

        assert not store.reserve_execution(
            "job-12345678:s-1", "job-12345678", "s-1", RS.REPLAY_SAFE, clock()
        )
        prior = store.get_execution_record("job-12345678:s-1")
        assert prior.state is ExecutionState.COMMITTED
        rebuilt = prior.reconstruct_result()
        assert rebuilt.status is WorkerStatus.SUCCESS

    def test_window_F_non_replay_safe_ambiguous_crash_escalates(self, env):
        """Ambiguous outcome for NON_REPLAY_SAFE: explicit recovery, no rerun."""
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.NON_REPLAY_SAFE)
        crasher = _CrashMidExecutionWorker()
        crasher.replay_safety = ReplaySafety.NON_REPLAY_SAFE
        engine._workers["GENERIC"] = crasher
        engine.submit(_job(), [_step("s-1")])
        lease = _drive_ready(store, queue, engine, clock)
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)
        engine.recover_job("job-12345678")
        # Re-lease after recovery; the unresolved EXECUTING record must route
        # the retry into explicit WAITING_INPUT escalation — NOT a rerun.
        engine._workers["GENERIC"] = worker
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        result = engine.execute_step(lease2)
        assert result.status is WorkerStatus.BLOCKED_INPUT
        assert store.get_step("s-1").status is RuntimeStepStatus.WAITING_INPUT
        assert worker.executions == 0  # never re-executed the ambiguous effect
        report = engine.recover_job("job-12345678")
        flagged = [
            u for u in report["unresolved_executions"]
            if u["requires_operator_resolution"]
        ]
        assert flagged and flagged[0]["idempotency_key"] == "job-12345678:s-1"

    def test_window_G_restart_with_same_key(self, env):
        """Fresh process, same key: deterministic dedup, no double effect."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "exec.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            engine1 = OrchestratorEngine(store1, queue1, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            worker = _CounterWorker(ReplaySafety.IDEMPOTENCY_AWARE)
            engine1._workers["GENERIC"] = worker
            engine1.submit(_job(), [_step("s-1")])
            lease = _drive_ready(store1, queue1, engine1, clock)
            engine1.execute_step(lease)
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            store2 = SqliteRuntimeStore(c2)
            # Same key re-reservation is refused after restart.
            assert not store2.reserve_execution(
                "job-12345678:s-1", "job-12345678", "s-1",
                ReplaySafety.IDEMPOTENCY_AWARE, clock(),
            )
            rec = store2.get_execution_record("job-12345678:s-1")
            assert rec.state is ExecutionState.COMMITTED
            assert rec.reconstruct_result().status is WorkerStatus.SUCCESS
            c2.close()

    def test_no_false_exactly_once_claim(self, env):
        """At-least-once + dedup: the worker CAN run twice across retries; the
        EFFECT is deduplicated by the key contract, not by orchestration."""
        store, queue, engine, clock, _ = env
        worker = _CounterWorker(ReplaySafety.IDEMPOTENCY_AWARE)
        engine._workers["GENERIC"] = worker
        engine.submit(_job(), [_step("s-1", max_attempts=3)])
        lease = _drive_ready(store, queue, engine, clock)

        class _FlakyThenSuccess(worker.__class__):
            def execute(self, request, packet):
                self.executions += 1
                if self.executions == 1:
                    return WorkerResult(
                        step_id=request.step_id, job_id=request.job_id,
                        status=WorkerStatus.RETRYABLE,
                        failure_class="TRANSIENT",
                        error_summary="transient",
                    )
                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=WorkerStatus.SUCCESS,
                    evidence_refs=("ev-flaky-ok",),
                )

        flaky = _FlakyThenSuccess(ReplaySafety.IDEMPOTENCY_AWARE)
        engine._workers["GENERIC"] = flaky
        r1 = engine.execute_step(lease)
        assert r1.status is WorkerStatus.RETRYABLE
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w1")
        r2 = engine.execute_step(lease2)
        assert r2.status is WorkerStatus.SUCCESS
        # Two worker invocations (at-least-once); record committed once.
        assert flaky.executions == 2
        rec = store.get_execution_record("job-12345678:s-1")
        assert rec.state is ExecutionState.COMMITTED
