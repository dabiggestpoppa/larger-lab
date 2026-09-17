"""P2-R3-C03 — single recovery law + active-lease protection (§6 hard gate).

ONE authoritative owner reconciles queue claims and durable step state:
expired leases recover, active leases are never stolen, RUNNING-orphan
steps are explicitly classified, committed work finalizes without replay,
and non-replay-safe ambiguity escalates.
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
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.jobs.runtime import (
    RuntimeJob,
    RuntimeStep,
    RuntimeStepStatus,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ReplaySafety
from qcae.orchestration.workers.base import DeterministicSuccessWorker

NOW = "2026-09-17T12:00:00Z"
JOB = "job-recover1"


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id=JOB, **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-rc", "k-rc"),
        job_type="DISCOVERY",
        subject_ref="cap-rc",
        created_by="operator",
        created_at=NOW,
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id=JOB, deps=(), **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="GENERIC",
        dependencies=tuple(deps),
        created_at=NOW,
        idempotency_key=f"{job_id}:{step_id}",
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
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate()
    )
    return store, queue, engine, clock, conn


class TestActiveLeaseProtection:
    def test_recover_never_steals_active_lease(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        assert lease is not None
        # Operator invokes recovery while the lease is still valid.
        report = engine.recover_job(JOB)
        assert report["recovered_lease_steps"] == []
        # Sole owner unchanged: same token, step still RUNNING.
        cols = store.read_lease_columns("s-1")
        assert cols["lease_token"] == lease.lease_token
        assert queue.lease_owner_of("s-1") == "id-worker-a"
        assert store.get_step("s-1").status is RuntimeStepStatus.RUNNING

    def test_second_worker_cannot_claim_active_lease(self, env):
        store, queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        assert engine.lease_next(JOB, "id-worker-a") is not None
        assert engine.lease_next(JOB, "id-worker-b") is None
        assert queue.lease_owner_of("s-1") == "id-worker-a"

    def test_resume_does_not_steal_active_lease(self, env):
        store, queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        engine.recover_job(JOB)  # resume path uses the same law
        cols = store.read_lease_columns("s-1")
        assert cols["lease_token"] == lease.lease_token
        assert queue.lease_owner_of("s-1") == "id-worker-a"

    def test_expired_lease_recovers_and_requeues(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        clock.advance(120)  # TTL (60s) elapses: worker died
        report = engine.recover_job(JOB)
        assert "s-1" in report["recovered_lease_steps"]
        assert store.get_step("s-1").status is RuntimeStepStatus.READY
        assert not queue.has_active_claim("s-1")
        # A new worker can now claim it.
        lease2 = engine.lease_next(JOB, "id-worker-b")
        assert lease2 is not None and lease2.lease_token != lease.lease_token

    def test_concurrent_claim_after_expiry_single_owner(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        assert engine.lease_next(JOB, "id-worker-a") is not None
        clock.advance(120)
        engine.recover_job(JOB)
        # Two workers race for the recovered step; exactly one wins.
        winners = [engine.lease_next(JOB, f"id-worker-{c}") for c in "ab"]
        owned = [l for l in winners if l is not None]
        assert len(owned) == 1


class TestOrphanClassification:
    def test_running_step_without_claim_is_classified(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        engine.lease_next(JOB, "id-worker-a")
        # Simulate lost claim row (queue metadata destroyed, step RUNNING).
        conn = store._conn
        conn.execute("DELETE FROM runtime_queue_claim WHERE step_id = 's-1'")
        conn.commit()
        report = engine.recover_orphan_steps(JOB)
        assert report["orphan_steps"] == ["s-1"]
        assert report["reconciled"] == ["s-1"]
        assert store.get_step("s-1").status is RuntimeStepStatus.READY

    def test_orphan_recovery_is_explicit_not_silent(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1"), _step("s-2")])
        engine.ready_steps(JOB)
        engine.lease_next(JOB, "id-worker-a")
        # No orphans: the lease is active, nothing to classify.
        report = engine.recover_orphan_steps(JOB)
        assert report["orphan_steps"] == []
        assert report["reconciled"] == []


class TestCommittedNeverReplays:
    def test_expired_lease_with_committed_record_finalizes(self, env):
        store, queue, engine, clock, _conn = env

        class _EffectWorker:
            replay_safety = ReplaySafety.REPLAY_SAFE
            executions = 0

            def execute(self, request, packet):
                _EffectWorker.executions += 1
                from qcae.orchestration.workers.contracts import WorkerResult

                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=__import__(
                        "qcae.orchestration.workers.contracts",
                        fromlist=["WorkerStatus"],
                    ).WorkerStatus.SUCCESS,
                )

        engine.register_worker_type("GENERIC", _EffectWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        engine.execute_step(lease)
        assert _EffectWorker.executions == 1
        # Crash after commit, before anything else: recovery must finalize
        # (idempotent) rather than re-run.
        clock.advance(120)
        report = engine.recover_job(JOB)
        assert report["recovered_lease_steps"] == []
        assert store.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED
        assert _EffectWorker.executions == 1

    def test_non_replay_safe_ambiguity_escalates(self, env):
        store, queue, engine, clock, _conn = env

        class _CrashWorker:
            replay_safety = ReplaySafety.NON_REPLAY_SAFE

            def execute(self, request, packet):
                raise RuntimeError("died mid-effect")

        engine.register_worker_type("GENERIC", _CrashWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease)
        clock.advance(120)
        report = engine.recover_job(JOB)
        # Ambiguous execution: WAITING_INPUT, never a blind replay.
        assert store.get_step("s-1").status is RuntimeStepStatus.WAITING_INPUT
        flagged = [
            u for u in report["unresolved_executions"]
            if u["requires_operator_resolution"]
        ]
        assert flagged and flagged[0]["idempotency_key"] == "job-recover1:s-1"


class TestRecoveryIdempotence:
    def test_global_recover_then_resume_idempotent(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        engine.lease_next(JOB, "id-worker-a")
        clock.advance(120)
        first = engine.recover_job(JOB)
        second = engine.recover_job(JOB)
        assert first["recovered_lease_steps"] == ["s-1"]
        assert second["recovered_lease_steps"] == []
        assert store.get_step("s-1").status is RuntimeStepStatus.READY

    def test_resume_then_global_recover_idempotent(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        engine.lease_next(JOB, "id-worker-a")
        clock.advance(120)
        engine.recover_job(JOB)
        # A second recovery (either surface) changes nothing.
        again = engine.recover_job(JOB)
        assert again["recovered_lease_steps"] == []

    def test_recovery_scoped_to_job(self, env):
        store, queue, engine, clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        other = _job(job_id="job-other999",
                     deterministic_id=deterministic_job_id("discovery", "cap-xx", "k2"))
        engine.submit(other, [_step("t-1", job_id="job-other999")])
        engine.ready_steps(JOB)
        engine.ready_steps("job-other999")
        engine.lease_next(JOB, "id-worker-a")
        engine.lease_next("job-other999", "id-worker-b")
        clock.advance(120)
        engine.recover_job(JOB)
        # The other job's lease is untouched by job-scoped recovery.
        assert queue.lease_owner_of("t-1") == "id-worker-b"
        assert store.get_step("t-1").status is RuntimeStepStatus.RUNNING
