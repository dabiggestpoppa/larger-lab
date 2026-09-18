"""P2-R4-C03 — durable single-use grants + restart-safe request ids.

Finding G repair law (directive §6/§7/§8):

- approval authority is a DURABLE grant in the approval registry, never a
  process-memory set (the old ``_granted_keys`` vanished on restart and was
  never consumed);
- a grant admits exactly ONE execution (single execution admission); the
  consumption record is durable, so a consumed grant cannot be replayed in
  any process;
- a grant that was never used survives restart;
- an expired / denied / wrong-principal grant admits nothing;
- authority-request identity is restart-safe: no in-memory counter that
  resets (and collides) after restart.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcae.governance.standalone.approvals import ApprovalState
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
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"  # RuntimeStep identity as built by test_p2_recovery._step


def _engine(stack, conn, clock, approvals, *, sink_window=None):
    """Build an engine with the durable registry + sink wired (C03 style)."""
    sink_kwargs = {"window_seconds": sink_window} if sink_window else {}
    return OrchestratorEngine(
        stack, SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60),
        clock=clock,
        authority_gate=StaticStepAuthorityGate(require_approval=("execute.GENERIC",)),
        authority_request_sink=ApprovalRegistrySink(approvals, clock=clock, **sink_kwargs),
        approval_registry=approvals,
    )


def _identities():
    ids = LocalIdentityProvider.__new__(LocalIdentityProvider)
    ids._identities = {}
    ids._current = None
    ids.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
    ids.register(LocalIdentity(identity_id="id-worker-runtime", kind=IdentityKind.WORKER))
    return ids


def _service(conn, stack, queue, clock, engine, approvals):
    return LocalRuntimeService(
        runtime_store=stack, queue=queue, engine=engine,
        identity_provider=_identities(), policy_provider=None,
        approval_registry=approvals, clock=clock, schema_version=4,
        policy_version="test-1", storage_location=str(conn),
    )


def _reach_waiting_policy(stack, queue, engine, clock, job_id="job-12345678"):
    engine.submit(_job(job_id=job_id), [_step(STEP, idempotency_key=f"{job_id}:{STEP}")])
    engine.ready_steps(job_id)
    lease = engine.lease_next(job_id, "id-worker-runtime")
    result = engine.execute_step(lease, worker_id="id-worker-runtime")
    assert result.status.value == "BLOCKED_POLICY"
    assert stack.get_step(STEP).status is RuntimeStepStatus.WAITING_POLICY
    rid = engine._latest_authority_request_for_step(job_id, STEP)
    assert rid
    return rid


def _grant_and_release(service, approvals, rid, job_id="job-12345678"):
    service.decide_approval(
        request_id=rid, decision="GRANTED", decided_by="id-operator-1",
        job_id=job_id, reason="ok",
    )
    service.release_granted_step(job_id, STEP)
    decision = approvals.decisions_for_request(rid)[-1]
    assert decision.state is ApprovalState.GRANTED
    return decision


class TestDurableGrantAdmission:
    """§7 grant consumption law."""

    def test_grant_admits_exactly_one_execution(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        _grant_and_release(_service(conn, stack, queue, clock, engine, approvals),
                           approvals, rid)
        # First admission consumes the grant; a second is refused.
        assert engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        # Consumption is durable.
        decision = approvals.decisions_for_request(rid)[-1]
        uses = approvals.uses_for_decision(decision.decision_id)
        assert len(uses) == 1
        assert uses[0].step_id == STEP

    def test_grant_survives_restart_before_use(self, tmp_path):
        clock = _Clock()
        db = tmp_path / "meta.sqlite3"
        conn = open_metadata_db(db)
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        _grant_and_release(_service(conn, stack, queue, clock, engine, approvals),
                           approvals, rid)
        conn.commit()
        conn.close()  # restart BEFORE the grant is consumed

        # New process: fresh engine + registry over the same durable state.
        conn2 = open_metadata_db(db)
        stack2 = SqliteRuntimeStore(conn2)
        approvals2 = SqliteApprovalRegistry(conn2)
        queue2 = SqliteStepQueue(conn2, stack2, now_fn=clock, lease_ttl_seconds=60)
        engine2 = _engine(stack2, conn2, clock, approvals2)
        engine2.register_worker_type("GENERIC", DeterministicSuccessWorker())
        # The unreleased grant is still discoverable and admits execution.
        assert engine2._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        conn2.close()

    def test_consumed_grant_cannot_replay_after_restart(self, tmp_path):
        clock = _Clock()
        db = tmp_path / "meta.sqlite3"
        conn = open_metadata_db(db)
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        _grant_and_release(_service(conn, stack, queue, clock, engine, approvals),
                           approvals, rid)
        assert engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        conn.commit()
        conn.close()  # restart AFTER consumption

        conn2 = open_metadata_db(db)
        approvals2 = SqliteApprovalRegistry(conn2)
        stack2 = SqliteRuntimeStore(conn2)
        engine2 = _engine(stack2, conn2, clock, approvals2)
        # The consumed grant cannot authorize anything in the new process.
        assert not engine2._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        conn2.close()

    def test_expired_grant_admits_nothing(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals, sink_window=60)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        _grant_and_release(_service(conn, stack, queue, clock, engine, approvals),
                           approvals, rid)
        clock.advance(3600)  # past the 60s approval window
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")

    def test_wrong_principal_admitted_nothing(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        _grant_and_release(_service(conn, stack, queue, clock, engine, approvals),
                           approvals, rid)
        # The grant admits the requesting principal only (identity binding).
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-operator-1")

    def test_denied_or_missing_grant_admits_nothing(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        stack = SqliteRuntimeStore(conn)
        approvals = SqliteApprovalRegistry(conn)
        queue = SqliteStepQueue(conn, stack, now_fn=clock, lease_ttl_seconds=60)
        engine = _engine(stack, conn, clock, approvals)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        # No request at all -> nothing admits.
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")
        rid = _reach_waiting_policy(stack, queue, engine, clock)
        service = _service(conn, stack, queue, clock, engine, approvals)
        service.decide_approval(
            request_id=rid, decision="DENIED", decided_by="id-operator-1",
            job_id="job-12345678", reason="no",
        )
        assert not engine._grant_admits(
            job_id="job-12345678", step_id=STEP, principal="id-worker-runtime")


class TestRequestIdentityRestartSafety:
    """§8: no in-memory counter; restart cannot collide request ids."""

    def _verdict(self, engine):
        job = _job()
        step = _step("s-1")
        engine.submit(job, [step])
        gate = StaticStepAuthorityGate(require_approval=("execute.GENERIC",))
        return gate.evaluate_step_authority(
            step, job, worker_id="id-worker-runtime")

    def test_new_sink_after_restart_never_collides(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        approvals = SqliteApprovalRegistry(conn)
        engine = _engine(SqliteRuntimeStore(conn), conn, clock, approvals)
        verdict = self._verdict(engine)

        sink1 = ApprovalRegistrySink(approvals, clock=clock)
        id1 = sink1.record_authority_request(verdict)
        # "Restart": a brand-new sink instance with the same verdict.
        sink2 = ApprovalRegistrySink(approvals, clock=clock)
        id2 = sink2.record_authority_request(verdict)
        assert id1 != id2, "restart reset the counter and collided ids"
        # Both requests are durably stored — no collision rejection.
        assert approvals.get_request(id1) is not None
        assert approvals.get_request(id2) is not None
        # Same semantics share a deterministic digest segment; uniqueness
        # comes from the suffix, not process-local counter state.
        seg1 = id1.split("-")[-2]
        seg2 = id2.split("-")[-2]
        assert seg1 == seg2

    def test_distinct_semantics_distinct_digest(self):
        clock = _Clock()
        conn = open_metadata_db(":memory:")
        for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                    APPROVAL_DDL):
            conn.executescript(ddl)
        approvals = SqliteApprovalRegistry(conn)
        engine = _engine(SqliteRuntimeStore(conn), conn, clock, approvals)
        verdict = self._verdict(engine)
        sink = ApprovalRegistrySink(approvals, clock=clock)
        id1 = sink.record_authority_request(verdict)

        gate = StaticStepAuthorityGate(require_approval=("execute.OTHER",))
        verdict2 = gate.evaluate_step_authority(
            _step("s-2"), _job(), worker_id="id-worker-runtime")
        id2 = sink.record_authority_request(verdict2)
        assert id1.split("-")[-2] != id2.split("-")[-2]
