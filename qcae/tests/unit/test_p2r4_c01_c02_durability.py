"""P2-R4-C01/C02 — durable crash boundaries + COMMITTED reconstruction.

C01 (directive §3/§4): the engine commits durably at the PRE-EFFECT
boundary (lease, RUNNING, attempt, authority admission, idempotency
reservation, EXECUTING) and the POST-EFFECT boundary (result, COMMITTED,
step finalization, checkpoint, job finalization). No DB write transaction
spans ``worker.execute()``. Every test here observes a SECOND independent
connection — data visible only through the engine's own connection is
data a process kill would destroy.

C02 (directive §10/§11): a COMMITTED execution record reconstructs
canonical step/job truth whether or not the legacy completion marker
exists, and recovery never writes a stale snapshot over newer terminal
state.
"""

from __future__ import annotations

import sys
from dataclasses import replace as dc_replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
    RuntimeJobStatus,
    RuntimeStepStatus,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import (
    ExecutionRecord,
    ExecutionState,
    ReplaySafety,
)
from qcae.orchestration.workers.base import WorkerRequest
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

SID = "job-12345678:s-1"  # durable step identity (CLI convention)
KEY = SID  # idempotency key for the single step


class _CountingWorker:
    """Records its own external side effect; counts invocations."""

    def __init__(self, safety: ReplaySafety = ReplaySafety.REPLAY_SAFE) -> None:
        self.replay_safety = safety
        self.calls: list[str] = []

    def execute(self, request, packet):
        self.calls.append(request.idempotency_key)
        from qcae.orchestration.workers.contracts import WorkerResult, WorkerStatus

        return WorkerResult(
            step_id=request.step_id, job_id=request.job_id,
            status=WorkerStatus.SUCCESS,
            output_artifact_refs=(f"artifact:{request.step_id}",),
        )


def _env(tmp_path, *, ttl: int = 60):
    """File-backed runtime env; returns (store, queue, engine, clock, conn)."""
    clock = _Clock()
    conn = open_metadata_db(tmp_path / "meta.sqlite3")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=ttl)
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate()
    )
    engine._workers["GENERIC"] = _CountingWorker()
    return store, queue, engine, clock, conn


def _second_store(tmp_path):
    """An independent connection: sees only DURABLE (committed) state.

    Returns the raw connection (caller closes it) — the durability probe
    must be a separate handle, not the engine's connection.
    """
    return open_metadata_db(tmp_path / "meta.sqlite3")


def _lease_step(store, queue, engine, clock):
    """Submit + ready + lease the one-step job; stop at the pre-effect state."""
    engine.submit(_job(), [_step(SID, idempotency_key=KEY)])
    engine.ready_steps("job-12345678")
    lease = engine.lease_next("job-12345678", "w1")
    assert lease is not None
    return lease


def _worker_request(lease):
    return WorkerRequest(
        job_id=lease.job_id, step_id=lease.step_id,
        worker_type="GENERIC", idempotency_key=KEY,
    )


def _reserve_and_execute(store, engine, lease, worker, clock):
    """The engine's exact pre-effect sequence, driven from its public parts.

    Reservation + EXECUTING are durably written (as lease_next/execute_step
    do before the flush), then the external effect runs and the result is
    COMMITTED — but step-state finalization is left undone, which is the
    durable truth a process kill in crash window D/E leaves behind.
    Returns the committed WorkerResult.
    """
    from qcae.orchestration.orchestrator.engine import _minimal_packet

    store.reserve_execution(KEY, lease.job_id, SID, ReplaySafety.REPLAY_SAFE,
                            clock())
    record = store.get_execution_record(KEY)
    store.update_execution_record(ExecutionRecord.from_dict(
        {**record.to_dict(), "state": ExecutionState.EXECUTING.value}))
    # THE PRE-EFFECT DURABLE BOUNDARY (what execute_step does before the
    # worker runs): reservation + EXECUTING become durable here.
    store.flush()
    result = worker.execute(_worker_request(lease), _minimal_packet(
        store.get_step(SID)))
    # Post-effect writes are NOT flushed: they die with the process,
    # which is exactly crash window D/E's durable truth.
    store.commit_execution(KEY, result, clock())
    return result


class TestPreEffectDurability:
    """Crash windows A/B/C (directive §4): lease/reservation/EXECUTING."""

    def test_lease_truth_durable_without_any_manual_commit(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        _lease_step(store, queue, engine, clock)
        # No conn.commit() anywhere in this test. A second connection must
        # see the full pre-effect truth (crash window A).
        probe = _second_store(tmp_path)
        step = SqliteRuntimeStore(probe).get_step(SID)
        probe.close()
        assert step.status is RuntimeStepStatus.RUNNING
        assert step.attempt == 1
        assert step.lease.lease_owner == "w1"

    def test_no_write_transaction_spans_worker_execute(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        seen = {}

        class _ProbeWorker(_CountingWorker):
            def execute(self, request, packet):
                # The law (directive §3): the engine's write transaction is
                # CLOSED while external work runs, and the EXECUTING
                # reservation is already durable for another process.
                seen["in_transaction"] = conn.in_transaction
                seen["executing_durable"] = SqliteRuntimeStore(
                    _second_store(tmp_path)
                ).get_execution_record(request.idempotency_key)
                return super().execute(request, packet)

        engine._workers["GENERIC"] = _ProbeWorker()
        lease = _lease_step(store, queue, engine, clock)
        engine.execute_step(lease)
        assert seen["in_transaction"] is False, (
            "worker.execute() ran inside an open write transaction"
        )
        assert seen["executing_durable"].state is ExecutionState.EXECUTING

    def test_uncommitted_post_effect_writes_die_with_the_process(self, tmp_path):
        """Crash window D: post-effect writes land only at the flush.

        _complete() writes post-effect state; if the process dies before
        the engine's post-effect flush, exactly those writes are lost while
        every pre-effect write survives. That is the truth recovery works
        from.
        """
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _lease_step(store, queue, engine, clock)
        worker = engine._workers["GENERIC"]
        result = _reserve_and_execute(store, engine, lease, worker, clock)
        step = store.get_step(SID)
        engine._complete(step, result)
        assert len(worker.calls) == 1  # the external effect DID happen
        conn.close()  # close WITHOUT commit -> uncommitted writes are gone

        # A new process reopens: pre-effect truth survived, post-effect did not.
        store2 = SqliteRuntimeStore(_second_store(tmp_path))
        assert store2.get_step(SID).status is RuntimeStepStatus.RUNNING
        assert store2.get_execution_record(KEY).state is ExecutionState.EXECUTING
        store2._conn.close()


class TestCommittedReconstruction:
    """Directive §9/§11: COMMITTED reconstructs canonical truth."""

    def _committed_running_state(self, tmp_path, *, with_marker: bool):
        """Step RUNNING w/ expired lease + COMMITTED result in the record."""
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _lease_step(store, queue, engine, clock)
        worker = engine._workers["GENERIC"]
        # Crash window D/E: effect committed, step-state finalization lost.
        # The durable truth a kill leaves behind: COMMITTED record
        # (+ optional legacy marker), step still RUNNING, lease expired.
        result = _reserve_and_execute(store, engine, lease, worker, clock)
        if with_marker:
            store.record_idempotent_completion(KEY, lease.job_id, SID, clock())
        clock.advance(120)  # process death outlives the lease TTL
        conn.commit()
        return store, queue, engine, clock, conn, worker

    def test_committed_reconstruction_with_marker_present(self, tmp_path):
        store, queue, engine, clock, conn, worker = \
            self._committed_running_state(tmp_path, with_marker=True)
        assert store.get_step(SID).status is RuntimeStepStatus.RUNNING
        engine.recover_leased_steps([SID])
        # Canonical truth reconstructed despite the pre-existing marker
        # (§11: the marker never skips state reconstruction).
        step = store.get_step(SID)
        assert step.status is RuntimeStepStatus.SUCCEEDED
        assert step.output_refs == (f"artifact:{SID}",)
        assert store.get_job("job-12345678").status is RuntimeJobStatus.SUCCEEDED
        assert len(worker.calls) == 1  # effect never re-executed

    def test_committed_reconstruction_with_marker_absent(self, tmp_path):
        store, queue, engine, clock, conn, worker = \
            self._committed_running_state(tmp_path, with_marker=False)
        engine.recover_leased_steps([SID])
        assert store.get_step(SID).status is RuntimeStepStatus.SUCCEEDED
        assert store.get_job("job-12345678").status is RuntimeJobStatus.SUCCEEDED
        assert len(worker.calls) == 1

    def test_stale_snapshot_cannot_regress_terminal_job(self, tmp_path):
        """Finding H.A: recover_job must not write RUNNING over SUCCEEDED."""
        store, queue, engine, clock, conn, worker = \
            self._committed_running_state(tmp_path, with_marker=True)
        engine.recover_job("job-12345678")
        assert store.get_job("job-12345678").status is RuntimeJobStatus.SUCCEEDED
        # Idempotent: a second recovery observes terminal truth and cannot
        # regress it (the stale-snapshot bug wrote RUNNING right here).
        engine.recover_job("job-12345678")
        assert store.get_job("job-12345678").status is RuntimeJobStatus.SUCCEEDED
        job_succeeded = [
            ev for _seq, ev, _p in store.events_for_job("job-12345678")
            if ev.event_type is JobEventType.JOB_SUCCEEDED
        ]
        assert len(job_succeeded) == 1

    def test_job_succeeded_exactly_once_through_recovery(self, tmp_path):
        store, queue, engine, clock, conn, worker = \
            self._committed_running_state(tmp_path, with_marker=False)
        engine.recover_leased_steps([SID])
        engine.recover_job("job-12345678")
        job_succeeded = [
            ev for _seq, ev, _p in store.events_for_job("job-12345678")
            if ev.event_type is JobEventType.JOB_SUCCEEDED
        ]
        assert len(job_succeeded) == 1
        assert len(worker.calls) == 1
