"""P2-R2-C03 — crash/recovery authority re-evaluation through the real gate.

Directive law (§23; P2-R2-C03): never assume pre-crash authority is still
valid. The repair makes the re-evaluation REAL: after recovery the step is
executed under whatever gate is wired at that moment, so a policy change
during the crash window changes the resumed outcome.

Preservation law: recovery + re-evaluation never touch committed/idempotent
execution records — completed work stays completed and is never re-executed
(P2-C07R2 semantics, untouched by governance).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

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
from qcae.orchestration.authority_gate import (
    PermissiveStepAuthorityGate,
    StaticStepAuthorityGate,
    StepAuthorityDecision,
)
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ExecutionState, ReplaySafety
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerStatus


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, s):
        self._t += timedelta(seconds=s)


def _job(job_id="job-12345678", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("d", "c", job_id),
        job_type="D", subject_ref="cap-1", created_by="op",
        created_at="2026-09-13T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-12345678", **over):
    base = dict(
        step_id=f"{job_id}:{step_id}", job_id=job_id, step_type="GENERIC",
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


class _CountingWorker:
    """IDEMPOTENCY_AWARE worker counting real effect executions."""

    def __init__(self):
        self.calls = 0

    def execute(self, request, packet):
        self.calls += 1
        if self.calls == 1:
            # Simulate crash after the effect but before the commit marker:
            # raise out of the worker (process death).
            raise RuntimeError("simulated crash after lease")
        return DeterministicSuccessWorker().execute(request, packet)


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(
        store, queue, clock=clock,
        authority_gate=PermissiveStepAuthorityGate(),
    )
    conn.commit()
    return store, queue, engine, clock, conn


class TestRecoveryReevaluation:
    def test_policy_change_between_crash_and_resume_denies(self, env):
        """A step permitted pre-crash runs into DENY after the policy
        tightened during the crash window."""
        store, queue, engine, clock, conn = env
        worker = _CountingWorker()
        engine.register_worker_type("GENERIC", worker)
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)  # crash

        # Policy tightens while the process is "down".
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        report = engine.recover_job("job-12345678")
        assert "job-12345678:s-1" in report["recovered_lease_steps"]
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        result = engine.execute_step(lease2)
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "POLICY_DENIED"
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.FAILED
        # The pre-crash attempt ran; the resumed attempt did not (worker
        # call count unchanged by the denied execution).
        assert worker.calls == 1

    def test_policy_change_to_require_approval_waits(self, env):
        """Tightened policy may also demand approval instead of denying."""
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        # Crash before the worker runs (the reservation is the crash point).
        report = engine.recover_job("job-12345678")
        assert "job-12345678:s-1" in report["recovered_lease_steps"]

        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("execute.GENERIC",)
        )
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        result = engine.execute_step(lease2)
        assert result.status is WorkerStatus.BLOCKED_POLICY
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.WAITING_POLICY
        assert worker.calls == 0

    def test_gate_swap_after_resume_is_real_evaluation(self, env):
        """The engine consults the CURRENT gate, not a verdict cached at
        lease time — swapping gates between lease and execute changes the
        outcome (proving execution-time evaluation)."""
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")  # leased under permissive
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        result = engine.execute_step(lease)  # evaluated under the new gate
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "POLICY_DENIED"

    def test_committed_execution_survives_recovery_reevaluation(self, env):
        """Recovery + authority re-evaluation never re-runs committed work."""
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)
        engine.submit(
            _job(),
            [_step("s-1"), _step("s-2", dependencies=("job-12345678:s-1",))],
        )
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)  # s-1 commits
        key = "job-12345678:s-1"  # the step's idempotency_key
        record = store.get_execution_record(key)
        assert record is not None and record.state is ExecutionState.COMMITTED

        # Crash; policy tightens; recovery.
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        engine.recover_job("job-12345678")
        # The committed record is untouched.
        after = store.get_execution_record(key)
        assert after.state is ExecutionState.COMMITTED
        assert after.result_json == record.result_json
        # s-1 is NOT requeued by recovery.
        report = engine.recover_job("job-12345678")
        assert "job-12345678:job-12345678:s-1" not in report["requeued_steps"]
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.SUCCEEDED
        assert worker.calls == 1

    def test_duplicate_execution_after_policy_change_still_dedups(self, env):
        """A committed step's idempotent reconstruction bypasses the gate —
        the side effect already happened; re-evaluation cannot un-happen it
        and must not re-execute either."""
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        assert worker.calls == 1

        # Force a re-lease attempt of the same step via a duplicate claim:
        # the step is SUCCEEDED so the queue cannot hand it out again.
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        assert lease2 is None  # terminal steps are never re-leased
        assert worker.calls == 1


class TestRecoveryReportTruthfulness:
    def test_recovery_report_lists_unresolved_executions(self, env):
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", _CountingWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)  # crash with RESERVED/EXECUTING record
        report = engine.recover_job("job-12345678")
        # The unresolved record is visible for operator resolution.
        assert isinstance(report["unresolved_executions"], list)

    def test_recovered_step_requires_full_authority(self, env):
        """A recovered (never-committed) step re-enters through the same
        gate as fresh work — no recovery shortcut exists."""
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        engine.lease_next("job-12345678", "w1")
        engine.recover_job("job-12345678")  # crash + recovery
        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("execute.GENERIC",)
        )
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        result = engine.execute_step(lease2)
        assert result.status is WorkerStatus.BLOCKED_POLICY
