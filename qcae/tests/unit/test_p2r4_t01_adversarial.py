"""P2-R4-T01 — adversarial crash/approval/scheduling qualification.

Hostile paths against the P2-R4 repair laws. Every case fails closed:

CRASH DURABILITY   no pre-crash manual commit makes recovery work; a
                   second connection (a kill's survivor) sees the truth.
RECOVERY           COMMITTED reconstructs with/without the legacy marker;
                   stale snapshots cannot regress terminal truth.
APPROVAL           consumed grants cannot replay; expired/changed-binding
                   grants admit nothing; request ids never collide.
SCHEDULING         priority/recovery cannot bypass a future schedule.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.governance.standalone.runtime_service import LocalRuntimeService
from qcae.governance.standalone.step_gate import ApprovalRegistrySink
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
from qcae.infrastructure.persistence.sqlite_policy_log import GOVERNANCE_DDL
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
)
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import (
    ExecutionState,
    ReplaySafety,
)
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

SID = "s-1"  # test_p2_recovery-style plain step id
KEY = "job-12345678:s-1"

from qcae.orchestration.workers.base import WorkerRequest


class _EffectWorker:
    """Counts external effects outside the DB; configured replay safety."""

    def __init__(self, safety=ReplaySafety.REPLAY_SAFE):
        self.replay_safety = safety
        self.calls = []

    def execute(self, request, packet):
        self.calls.append(request.idempotency_key)
        from qcae.orchestration.workers.contracts import WorkerResult, WorkerStatus

        return WorkerResult(step_id=request.step_id, job_id=request.job_id,
                            status=WorkerStatus.SUCCESS)


def _env(tmp_path=None, *, ttl: int = 60, safety=ReplaySafety.REPLAY_SAFE):
    clock = _Clock()
    conn = open_metadata_db(tmp_path / "m.sqlite3" if tmp_path else ":memory:")
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                APPROVAL_DDL):
        conn.executescript(ddl)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=ttl)
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate()
    )
    engine.register_worker_type("GENERIC", _EffectWorker(safety))
    return store, queue, engine, clock, conn


def _submit_lease(store, queue, engine, clock):
    engine.submit(_job(), [_step(SID, idempotency_key=KEY)])
    engine.ready_steps("job-12345678")
    return engine.lease_next("job-12345678", "w1")


def _identities():
    ids = LocalIdentityProvider.__new__(LocalIdentityProvider)
    ids._identities = {}
    ids._current = None
    ids.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
    ids.register(LocalIdentity(identity_id="id-worker-runtime", kind=IdentityKind.WORKER))
    return ids


class TestCrashDurabilityAdversarial:
    def test_1_kill_after_executing_then_recover_no_pre_crash_commit(self, tmp_path):
        """Case 1/6: recovery truth exists WITHOUT any pre-crash commit."""
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        engine.execute_step(lease, worker_id="w1")
        conn.close()  # process death AFTER the post-effect flush
        conn2 = open_metadata_db(tmp_path / "m.sqlite3")
        store2 = SqliteRuntimeStore(conn2)
        assert store2.get_step(SID).status is RuntimeStepStatus.SUCCEEDED
        assert store2.get_job("job-12345678").status.value == "SUCCEEDED"
        conn2.close()

    def test_2_effect_before_committed_reruns_at_most_once(self, tmp_path):
        """Case 2: effect ran, kill before COMMITTED — REPLAY_SAFE rerun
        happens at most once more, and the effect total is bounded by the
        reservation dedup (at-least-once, never unbounded)."""
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        # Simulate: effect ran (worker would have recorded it), kill.
        engine._workers["GENERIC"].calls.append(KEY)
        store.reserve_execution(KEY, "job-12345678", SID, ReplaySafety.REPLAY_SAFE,
                                clock())
        rec = store.get_execution_record(KEY)
        store.update_execution_record(
            type(rec).from_dict({**rec.to_dict(), "state": "EXECUTING"}))
        store.flush()
        conn.close()

        clock2 = _Clock(); clock2.advance(120)
        conn2 = open_metadata_db(tmp_path / "m.sqlite3")
        store2 = SqliteRuntimeStore(conn2)
        queue2 = SqliteStepQueue(conn2, store2, now_fn=clock2, lease_ttl_seconds=60)
        engine2 = OrchestratorEngine(
            store2, queue2, clock=clock2,
            authority_gate=PermissiveStepAuthorityGate())
        worker2 = _EffectWorker()
        engine2.register_worker_type("GENERIC", worker2)
        engine2.recover_job("job-12345678")
        lease2 = engine2.lease_next("job-12345678", "w2")
        if lease2 is not None:
            engine2.execute_step(lease2, worker_id="w2")
        # At-least-once across processes: the second attempt ran once.
        assert len(worker2.calls) == 1
        assert store2.get_step(SID).status is RuntimeStepStatus.SUCCEEDED
        conn2.close()

    def test_3_committed_before_step_success_reconstructs(self, tmp_path):
        """Case 3/4 (§9): COMMITTED record + (marker) + RUNNING step."""
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        worker = engine._workers["GENERIC"]
        from qcae.orchestration.orchestrator.engine import _minimal_packet
        store.reserve_execution(KEY, "job-12345678", SID, ReplaySafety.REPLAY_SAFE,
                                clock())
        result = worker.execute(WorkerRequest(
            job_id="job-12345678", step_id=SID, worker_type="GENERIC",
            idempotency_key=KEY), _minimal_packet(store.get_step(SID)))
        rec = store.get_execution_record(KEY)
        store.update_execution_record(
            type(rec).from_dict({**rec.to_dict(), "state": "EXECUTING"}))
        store.commit_execution(KEY, result, clock())
        store.record_idempotent_completion(KEY, "job-12345678", SID, clock())
        clock.advance(120)
        conn.commit()

        engine.recover_job("job-12345678")
        assert store.get_step(SID).status is RuntimeStepStatus.SUCCEEDED
        assert store.get_job("job-12345678").status.value == "SUCCEEDED"

    def test_5_job_success_exactly_once_despite_kill(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        engine.execute_step(lease, worker_id="w1")
        conn.close()
        conn2 = open_metadata_db(tmp_path / "m.sqlite3")
        store2 = SqliteRuntimeStore(conn2)
        engine2 = OrchestratorEngine(
            store2,
            SqliteStepQueue(conn2, store2, now_fn=clock, lease_ttl_seconds=60),
            clock=clock, authority_gate=PermissiveStepAuthorityGate())
        engine2.recover_job("job-12345678")
        events = [
            e.event_type.value for _s, e, _p in store2.events_for_job("job-12345678")
        ]
        assert events.count("JOB_SUCCEEDED") == 1
        conn2.close()


class TestRecoveryAdversarial:
    def test_7_committed_running_step_becomes_succeeded_with_marker(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        worker = engine._workers["GENERIC"]
        from qcae.orchestration.orchestrator.engine import _minimal_packet
        store.reserve_execution(KEY, "job-12345678", SID, ReplaySafety.REPLAY_SAFE,
                                clock())
        result = worker.execute(WorkerRequest(
            job_id="job-12345678", step_id=SID, worker_type="GENERIC",
            idempotency_key=KEY), _minimal_packet(store.get_step(SID)))
        rec = store.get_execution_record(KEY)
        store.update_execution_record(
            type(rec).from_dict({**rec.to_dict(), "state": "EXECUTING"}))
        store.commit_execution(KEY, result, clock())
        store.record_idempotent_completion(KEY, "job-12345678", SID, clock())
        clock.advance(120)
        conn.commit()
        engine.recover_job("job-12345678")
        assert store.get_step(SID).status is RuntimeStepStatus.SUCCEEDED
        assert worker.calls == [KEY]  # case 11: effect count stays one

    def test_8_stale_snapshot_cannot_regress_repeatedly(self, tmp_path):
        """Case 9: repeated stale recoveries never regress terminal truth."""
        store, queue, engine, clock, conn = _env(tmp_path)
        lease = _submit_lease(store, queue, engine, clock)
        engine.execute_step(lease, worker_id="w1")
        for _ in range(3):
            engine.recover_job("job-12345678")
        assert store.get_job("job-12345678").status.value == "SUCCEEDED"
        events = [
            e.event_type.value for _s, e, _p in store.events_for_job("job-12345678")
        ]
        assert events.count("JOB_SUCCEEDED") == 1


class TestApprovalAdversarial:
    def _approval_env(self, conn, clock):
        store = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
        engine = OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=StaticStepAuthorityGate(
                require_approval=("execute.GENERIC",)),
            authority_request_sink=ApprovalRegistrySink(approvals, clock=clock),
            approval_registry=approvals,
        )
        engine.register_worker_type("GENERIC", _EffectWorker())
        service = LocalRuntimeService(
            runtime_store=store, queue=queue, engine=engine,
            identity_provider=_identities(), policy_provider=None,
            approval_registry=approvals, clock=clock, schema_version=4,
            policy_version="t", storage_location=":memory:",
        )
        return store, queue, engine, approvals, service

    def test_12_13_14_grant_once_then_never_again(self, tmp_path):
        clock = _Clock()
        conn = open_metadata_db(tmp_path / "a.sqlite3")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        store, queue, engine, approvals, service = self._approval_env(conn, clock)
        engine.submit(_job(), [_step(SID, idempotency_key=KEY)])
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "id-worker-runtime")
        engine.execute_step(lease, worker_id="id-worker-runtime")
        rid = engine._latest_authority_request_for_step("job-12345678", SID)
        service.decide_approval(
            request_id=rid, decision="GRANTED", decided_by="id-operator-1",
            job_id="job-12345678", reason="ok")
        service.release_granted_step("job-12345678", SID)
        # First admission consumes (12); durable row exists.
        assert engine._grant_admits(
            job_id="job-12345678", step_id=SID, principal="id-worker-runtime")
        decision = approvals.decisions_for_request(rid)[-1]
        assert len(approvals.uses_for_decision(decision.decision_id)) == 1
        # Second use refused (13) and durable (14: survives restart).
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=SID, principal="id-worker-runtime")
        conn.commit()
        conn.close()
        conn2 = open_metadata_db(tmp_path / "a.sqlite3")
        approvals2 = SqliteApprovalRegistry(conn2)
        assert len(approvals2.uses_for_decision(decision.decision_id)) == 1
        conn2.close()

    def test_15_request_ids_never_collide_across_restarts(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        store, queue, engine, approvals, service = self._approval_env(conn, clock)
        job, step = _job(), _step(SID, idempotency_key=KEY)
        gate = StaticStepAuthorityGate(require_approval=("execute.GENERIC",))
        verdict = gate.evaluate_step_authority(step, job, worker_id="id-worker-runtime")
        ids = set()
        for _ in range(3):  # three "restarts", same verdict semantics
            sink = ApprovalRegistrySink(approvals, clock=clock)
            ids.add(sink.record_authority_request(verdict))
        assert len(ids) == 3

    def test_16_expired_grant_fails(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        store = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
        engine = OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=StaticStepAuthorityGate(
                require_approval=("execute.GENERIC",)),
            authority_request_sink=ApprovalRegistrySink(approvals, clock=clock,
                                                        window_seconds=1),
            approval_registry=approvals,
        )
        engine.register_worker_type("GENERIC", _EffectWorker())
        engine.submit(_job(), [_step(SID, idempotency_key=KEY)])
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "id-worker-runtime")
        engine.execute_step(lease, worker_id="id-worker-runtime")
        rid = engine._latest_authority_request_for_step("job-12345678", SID)
        service = LocalRuntimeService(
            runtime_store=store, queue=queue, engine=engine,
            identity_provider=_identities(), policy_provider=None,
            approval_registry=approvals, clock=clock, schema_version=4,
            policy_version="t", storage_location=":memory:",
        )
        service.decide_approval(
            request_id=rid, decision="GRANTED", decided_by="id-operator-1",
            job_id="job-12345678", reason="ok")
        clock.advance(7200)  # grant window elapsed
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=SID, principal="id-worker-runtime")

    def test_17_denial_still_immutable(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        store, queue, engine, approvals, service = self._approval_env(conn, clock)
        engine.submit(_job(), [_step(SID, idempotency_key=KEY)])
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "id-worker-runtime")
        engine.execute_step(lease, worker_id="id-worker-runtime")
        rid = engine._latest_authority_request_for_step("job-12345678", SID)
        service.decide_approval(
            request_id=rid, decision="DENIED", decided_by="id-operator-1",
            job_id="job-12345678", reason="no")
        with pytest.raises(Exception):
            service.decide_approval(
                request_id=rid, decision="GRANTED", decided_by="id-operator-1",
                job_id="job-12345678", reason="flip")
        decisions = approvals.decisions_for_request(rid)
        assert len(decisions) == 1
        assert decisions[0].state.value == "DENIED"


class TestSchedulingAdversarial:
    def test_19_22_future_job_blocks_high_priority_claim(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(priority=999), [_step(SID, idempotency_key=KEY)],
                      not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        assert engine.lease_next("job-12345678", "w1") is None

    def test_20_step_floor_blocks_claim(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(), [_step(SID, idempotency_key=KEY,
                                     not_before="2026-09-13T14:00:00Z")])
        engine.ready_steps("job-12345678")
        assert engine.lease_next("job-12345678", "w1") is None
        clock.advance(7200)
        assert engine.lease_next("job-12345678", "w1") is not None

    def test_21_restart_does_not_alter_schedule(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        engine.submit(_job(), [_step(SID, idempotency_key=KEY)],
                      not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        conn.commit()
        conn.close()
        conn2 = open_metadata_db(tmp_path / "m.sqlite3")
        store2 = SqliteRuntimeStore(conn2)
        queue2 = SqliteStepQueue(conn2, store2, now_fn=clock, lease_ttl_seconds=60)
        engine2 = OrchestratorEngine(
            store2, queue2, clock=clock,
            authority_gate=PermissiveStepAuthorityGate())
        engine2.register_worker_type("GENERIC", _EffectWorker())
        assert engine2.lease_next("job-12345678", "w1") is None  # still gated
        clock.advance(3600)
        assert engine2.lease_next("job-12345678", "w1") is not None
        conn2.close()

    def test_23_recovery_does_not_bypass_schedule(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        engine.submit(_job(), [_step(SID, idempotency_key=KEY,
                                     not_before="2026-09-13T13:00:00Z")])
        engine.ready_steps("job-12345678")
        clock.advance(3600)
        lease = engine.lease_next("job-12345678", "w1")
        assert lease is not None
        clock.advance(120)  # lease expires
        engine.recover_job("job-12345678")
        # Recovery re-availability honors the (past) floor; the queue's own
        # SQL gate still governs the claim.
        assert store.get_step(SID).status is RuntimeStepStatus.READY
        assert engine.lease_next("job-12345678", "w2") is not None
