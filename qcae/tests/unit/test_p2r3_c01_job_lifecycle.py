"""P2-R3-C01 — job lifecycle truth (operator-loop finding A).

The durable job snapshot and the append-oriented event stream must tell the
same story: submit ends QUEUED (JOB_CREATED + JOB_QUEUED, each exactly
once), the first granted lease moves the job RUNNING, the final step
success moves it SUCCEEDED with exactly one JOB_SUCCEEDED, and reads
cannot retrigger or resurrect anything.
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
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.jobs.runtime import (
    JobEventType,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker

NOW = "2026-09-17T12:00:00Z"
JOB = "job-lifecycle1"


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(**over):
    base = dict(
        job_id=JOB,
        deterministic_id=deterministic_job_id("discovery", "cap-lc", "k-lc"),
        job_type="DISCOVERY",
        subject_ref="cap-lc",
        created_by="operator",
        created_at=NOW,
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, deps=(), **over):
    base = dict(
        step_id=step_id,
        job_id=JOB,
        step_type="GENERIC",
        dependencies=tuple(deps),
        created_at=NOW,
        idempotency_key=f"{JOB}:{step_id}",
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


def _event_types(store, job_id=JOB):
    return [
        ev.event_type for _seq, ev, _payload in store.events_for_job(job_id)
    ]


def _run_one(engine, store, worker="id-worker-lc"):
    engine.ready_steps(JOB)
    lease = engine.lease_next(JOB, worker)
    assert lease is not None
    return engine.execute_step(lease)


class TestSubmitTruth:
    def test_submit_ends_queued(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        assert store.get_job(JOB).status is RuntimeJobStatus.QUEUED

    def test_created_and_queued_events_exactly_once(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        types = _event_types(store)
        assert types.count(JobEventType.JOB_CREATED) == 1
        assert types.count(JobEventType.JOB_QUEUED) == 1

    def test_queued_job_stays_queued_without_execution(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        engine.ready_steps(JOB)
        # Readiness derivation alone never promotes the job (finding A).
        assert store.get_job(JOB).status is RuntimeJobStatus.QUEUED


class TestRunTruth:
    def test_first_execution_moves_running_then_final_success(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])

        _run_one(engine, store)
        assert store.get_job(JOB).status is RuntimeJobStatus.RUNNING

        _run_one(engine, store)
        job = store.get_job(JOB)
        assert job.status is RuntimeJobStatus.SUCCEEDED
        assert store.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED
        assert store.get_step("s-2").status is RuntimeStepStatus.SUCCEEDED

    def test_job_succeeded_exactly_once(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        _run_one(engine, store)
        _run_one(engine, store)
        assert _event_types(store).count(JobEventType.JOB_SUCCEEDED) == 1

    def test_repeated_reads_cannot_retrigger_success(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        _run_one(engine, store)
        assert store.get_job(JOB).status is RuntimeJobStatus.SUCCEEDED
        # Idempotent reads/derived ops must not re-finalize.
        for _ in range(3):
            engine.write_checkpoint(JOB)
            engine.ready_steps(JOB)
            assert store.get_job(JOB).status is RuntimeJobStatus.SUCCEEDED
        assert _event_types(store).count(JobEventType.JOB_SUCCEEDED) == 1

    def test_terminal_job_cannot_be_rerun(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        _run_one(engine, store)
        # No READY steps remain; nothing is claimable; the terminal snapshot
        # cannot be moved back into an executable state.
        assert engine.lease_next(JOB, "id-worker-lc") is None
        engine.mark_running(JOB)
        assert store.get_job(JOB).status is RuntimeJobStatus.SUCCEEDED


class TestSubmissionFailClosed:
    def test_empty_graph_refused(self, env):
        _store, _queue, engine, _clock, _conn = env
        with pytest.raises(QcaeValidationError):
            engine.submit(_job(), [])
        _store, _queue, engine2, _clock2, _conn2 = env
        assert engine2._store.get_job(JOB) is None

    def test_submission_is_all_or_nothing(self, env):
        store, _queue, engine, _clock, _conn = env
        # A bad step makes the whole transaction roll back: no job row.
        bad = _step("s-bad", max_attempts=0)
        with pytest.raises(Exception):
            engine.submit(_job(), [_step("s-1"), bad])
        assert store.get_job(JOB) is None
