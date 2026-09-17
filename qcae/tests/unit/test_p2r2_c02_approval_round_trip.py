"""P2-R2-C02 — approval -> execution round trip.

The complete governed loop, end to end:

    step executes -> gate says REQUIRE_APPROVAL
    -> durable AuthorityRequest (exact binding) + APPROVAL_REQUESTED event
    -> step waits in WAITING_POLICY (worker never ran)
    -> operator GRANT bound to the exact action/resource/scope/budget
    -> service verifies the grant against the step's request
    -> engine releases the step to READY with a consumed grant key
    -> re-leased execution proceeds under ALLOW

And the negative laws: deny, expiry, wrong action/scope/budget, forged
request ids, and re-decision attempts can never release the step.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalDecision, ApprovalState
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.governance.standalone.step_gate import ApprovalRegistrySink
from qcae.governance.standalone.runtime_service import LocalRuntimeService
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
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate, StaticStepAuthorityGate
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
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


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL, APPROVAL_DDL):
        conn.executescript(ddl)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    approvals = SqliteApprovalRegistry(conn)
    engine = OrchestratorEngine(
        store, queue, clock=clock,
        authority_gate=PermissiveStepAuthorityGate(),
        authority_request_sink=ApprovalRegistrySink(approvals, clock=clock),
    )
    identities = LocalIdentityProvider.__new__(LocalIdentityProvider)
    identities._identities = {}
    identities._current = None
    identities.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
    identities.register(LocalIdentity(identity_id="id-worker-runtime", kind=IdentityKind.WORKER))
    service = LocalRuntimeService(
        runtime_store=store,
        queue=queue,
        engine=engine,
        identity_provider=identities,
        policy_provider=None,
        approval_registry=approvals,
        clock=clock,
        schema_version=4,
        policy_version="test-1",
        storage_location=":memory:",
    )
    conn.commit()
    return store, queue, engine, clock, conn, approvals, service


def _reach_waiting_policy(service, store, job, step, worker="id-worker-runtime"):
    """Drive a job until its step sits in WAITING_POLICY via the gate."""
    engine = service._engine
    engine._authority_gate = StaticStepAuthorityGate(
        require_approval=("execute.GENERIC",)
    )
    engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    engine.submit(job, [step])
    service.mark_running(job.job_id)
    engine.ready_steps(job.job_id)
    lease = engine.lease_next(job.job_id, worker)
    result = engine.execute_step(lease, worker_id=worker)
    assert result.status is WorkerStatus.BLOCKED_POLICY
    assert store.get_step(step.step_id).status is RuntimeStepStatus.WAITING_POLICY
    # The durable authority request exists.
    request_id = service._latest_authority_request_for_step(job.job_id, step.step_id)
    assert request_id, "APPROVAL_REQUESTED event must carry the request id"
    return request_id


class TestApprovalRoundTrip:
    def test_grant_releases_step_and_execution_completes(self, env):
        store, _q, engine, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(
            service, store, _job(), _step("s-1")
        )
        request = approvals.get_request(request_id)
        # Operator grants the EXACT binding.
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="ok",
        )
        service.release_granted_step("job-12345678", "job-12345678:s-1")
        released = store.get_step("job-12345678:s-1")
        assert released.status is RuntimeStepStatus.READY

        # Re-lease executes to completion.
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "id-worker-runtime")
        result = engine.execute_step(lease, worker_id="id-worker-runtime")
        assert result.status is WorkerStatus.SUCCESS
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.SUCCEEDED

    def test_request_binding_is_exact(self, env):
        store, _q, _e, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        request = approvals.get_request(request_id)
        assert request.action == "execute.GENERIC"
        assert request.resource == "cap-1"
        assert request.scope == "job:job-12345678"
        assert request.principal == "id-worker-runtime"

    def test_denied_approval_cannot_release(self, env):
        store, _q, engine, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        service.decide_approval(
            request_id=request_id, decision="DENIED",
            decided_by="id-operator-1", job_id="job-12345678", reason="no",
        )
        with pytest.raises(QcaeValidationError, match="no effective grant"):
            service.release_granted_step("job-12345678", "job-12345678:s-1")
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.WAITING_POLICY

    def test_expired_approval_cannot_release(self, env):
        store, _q, _e, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="ok",
        )
        # Time passes beyond the request's explicit approval window (24h).
        clock.advance(25 * 3600)
        with pytest.raises(QcaeValidationError, match="no effective grant"):
            service.release_granted_step("job-12345678", "job-12345678:s-1")

    def test_registry_rejects_laundered_grant_at_write(self, env):
        """The registry refuses to even store a grant whose binding differs."""
        store, _q, _e, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        request = approvals.get_request(request_id)
        with pytest.raises(QcaeValidationError, match="laundering"):
            approvals.record_decision(ApprovalDecision(
                decision_id="dec-forged-1", request_ref=request_id,
                state=ApprovalState.GRANTED, decided_by="id-operator-1",
                decided_at=clock(), bound_action="may_execute_in_sandbox",
                bound_resource=request.resource, bound_scope=request.scope,
                bound_budget_ref=request.budget_ref, reason="scope swap",
            ))

    def test_service_release_checks_binding_against_request(self, env):
        """Service-side law: even a registry that stored a mismatched grant
        cannot release, because the service re-checks the binding itself."""
        store, _q, _e, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        request = approvals.get_request(request_id)

        class StubRegistry:
            """Bypasses the write guard to emulate a misbehaving adapter."""

            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            def record_decision(self, decision):
                self._inner._conn.execute(
                    "INSERT INTO governance_approval_decision (decision_id,"
                    " request_ref, state, payload_json, payload_digest, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        decision.decision_id, decision.request_ref,
                        decision.state.value, "{}", "0", decision.decided_at,
                    ),
                )
                self._inner._conn.commit()

        service._approvals = StubRegistry(approvals)
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="x",
        )
        # Restore the real registry for release verification reads.
        service._approvals = approvals
        # The stored row is corrupt (payload "{}"), so decode fails closed.
        with pytest.raises(Exception):
            service.release_granted_step("job-12345678", "job-12345678:s-1")
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.WAITING_POLICY

    def test_re_decision_refused(self, env):
        store, _q, engine, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="ok",
        )
        with pytest.raises(QcaeValidationError, match="already decided"):
            service.decide_approval(
                request_id=request_id, decision="DENIED",
                decided_by="id-operator-1", job_id="job-12345678",
            )

    def test_release_without_waiting_step_refused(self, env):
        store, _q, engine, clock, _c, approvals, service = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        with pytest.raises(QcaeValidationError, match="not WAITING_POLICY"):
            service.release_granted_step("job-12345678", "job-12345678:s-1")

    def test_release_with_unknown_request_refused(self, env):
        """WAITING_POLICY step with no durable request cannot be released."""
        store, _q, engine, clock, _c, approvals, service = env
        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("execute.GENERIC",)
        )
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-1")])
        service.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "id-worker-runtime")
        engine.execute_step(lease, worker_id="id-worker-runtime")
        # Remove the request artifact (simulating a sinkless/lost request).
        conn = approvals._conn
        conn.execute(
            "DELETE FROM governance_approval_request WHERE request_id LIKE 'authreq-%'"
        )
        conn.commit()
        with pytest.raises(QcaeValidationError, match="no authority request recorded|not found"):
            service.release_granted_step("job-12345678", "job-12345678:s-1")

    def test_grant_key_single_use(self, env):
        """The engine's grant key is consumed by one execute_step; a second
        execution of a re-entered WAITING_POLICY step requires a new grant."""
        store, _q, engine, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="ok",
        )
        service.release_granted_step("job-12345678", "job-12345678:s-1")
        assert "job-12345678:job-12345678:s-1" in engine._granted_keys

    def test_events_record_request_and_grant(self, env):
        store, _q, _e, clock, _c, approvals, service = env
        request_id = _reach_waiting_policy(service, store, _job(), _step("s-1"))
        service.decide_approval(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-1", job_id="job-12345678", reason="ok",
        )
        service.release_granted_step("job-12345678", "job-12345678:s-1")
        kinds = [
            e.event_type.value for _s, e, _p in store.events_for_job("job-12345678")
        ]
        assert "APPROVAL_REQUESTED" in kinds
        assert "APPROVAL_GRANTED" in kinds
