"""P2-C10 — standalone runtime service qualification (directive §31, §35, §59-60)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.decisions.authority import AuthorityRequest, PolicyAction
from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
)
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.governance.standalone.runtime_service import (
    OCE_MODE,
    LocalRuntimeService,
)
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
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import (
    ApprovalRequiredWorker,
    DeterministicSuccessWorker,
)
from qcae.orchestration.workers.contracts import WorkerStatus
from qcae.tests.unit.test_p2_governance import _engine as _policy_engine


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds):
        self._t += timedelta(seconds=seconds)


@pytest.fixture()
def svc():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL, APPROVAL_DDL):
        conn.executescript(ddl)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
    engine._workers["GENERIC"] = DeterministicSuccessWorker()
    engine._workers["APPROVAL"] = ApprovalRequiredWorker()
    identities = LocalIdentityProvider()
    identities.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
    identities.register(LocalIdentity(identity_id="id-worker-1", kind=IdentityKind.WORKER))
    return (
        LocalRuntimeService(
            runtime_store=store,
            queue=queue,
            engine=engine,
            identity_provider=identities,
            policy_provider=None,
            approval_registry=SqliteApprovalRegistry(conn),
            clock=clock,
            schema_version=4,
            policy_version="1.0.0",
            storage_location=":memory:",
        ),
        store,
        clock,
    )


def _job(job_id="job-12345678"):
    return RuntimeJob(
        job_id=job_id,
        deterministic_id=deterministic_job_id("d", "c", job_id),
        job_type="D", subject_ref="cap-1", created_by="id-operator-1",
        created_at="2026-09-13T12:00:00Z",
    )


def _step(step_id, job_id="job-12345678", step_type="GENERIC", deps=()):
    """Step ids are globally unique: prefix with the job id (PK is step_id)."""
    full_id = f"{job_id}:{step_id}" if ":" not in step_id else step_id
    return RuntimeStep(
        step_id=full_id, job_id=job_id, step_type=step_type,
        dependencies=tuple(f"{job_id}:{d}" if ":" not in d else d for d in deps),
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )


def _run_all(svc, store, job_id, worker="w1"):
    svc._engine.mark_running(job_id)
    for _ in range(8):
        svc.ready_steps(job_id)
        lease = svc.lease_next(job_id, worker)
        if lease is None:
            break
        result = svc.execute_step(lease)
        if result.status not in (WorkerStatus.SUCCESS, WorkerStatus.RETRYABLE):
            break


class TestRuntimeIdentity:
    def test_identity_inspectable(self, svc):
        svc, _store, _clock = svc
        ident = svc.identity()
        assert ident.runtime_id
        assert ident.schema_version == 4
        assert ident.policy_version == "1.0.0"
        assert ident.oce_mode == "OCE_ABSENT"
        assert "GENERIC" in ident.registered_workers

    def test_no_oce_import_in_service(self):
        """OCE absence is structural: no OCE module is loaded by the service."""
        svc_mod = sys.modules.get("qcae.governance.standalone.runtime_service")
        assert svc_mod is not None
        src = open(svc_mod.__file__, encoding="utf-8").read()
        assert "import oce" not in src.replace(" ", "")
        assert "from qcae.governance.oce" not in src


class TestServiceFlows:
    def test_submit_run_complete(self, svc):
        svc, store, clock = svc
        svc.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        _run_all(svc, store, "job-12345678")
        view = svc.inspect("job-12345678")
        statuses = {s.step_id.split(":")[-1]: s.status for s in view["steps"]}
        assert statuses["s-1"] is RuntimeStepStatus.SUCCEEDED
        assert statuses["s-2"] is RuntimeStepStatus.SUCCEEDED
        assert view["checkpoint"] is not None

    def test_inspect_unknown_job(self, svc):
        svc, _store, _clock = svc
        assert svc.inspect("job-nonexistent") is None

    def test_list_jobs_by_status(self, svc):
        svc, _store, _clock = svc
        svc.submit(_job(), [_step("s-1")])
        svc.submit(_job("job-aaaaaaaa"), [_step("s-1", job_id="job-aaaaaaaa")])
        queued = svc.list_jobs()
        assert len(queued) == 2

    def test_cancel_queued_job_immediately(self, svc):
        svc, store, clock = svc
        svc.submit(_job(), [_step("s-1")])
        cancelled = svc.cancel("job-12345678", reason="operator request")
        assert cancelled.status.value == "CANCELLED"
        step = store.get_step("job-12345678:s-1")
        assert step.status is RuntimeStepStatus.CANCELLED

    def test_cancel_terminal_job_rejected(self, svc):
        svc, store, clock = svc
        svc.submit(_job(), [_step("s-1")])
        _run_all(svc, store, "job-12345678")
        with pytest.raises(QcaeValidationError, match="terminal"):
            svc.cancel("job-12345678")

    def test_approval_flow_via_service(self, svc):
        svc, store, clock = svc
        svc.submit(_job(), [_step("s-1", step_type="APPROVAL")])
        svc.ready_steps("job-12345678")
        lease = svc.lease_next("job-12345678", "w1")
        result = svc.execute_step(lease)
        assert result.status is WorkerStatus.BLOCKED_POLICY
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.WAITING_POLICY

        # Operator records an approval; registry persists request+decision.
        svc._approvals.add_request(ApprovalRequest(
            request_id="req-00000021", principal="id-worker-1",
            action="may_execute_in_sandbox", resource="cand-1",
            scope="sandbox:isolated", budget_ref="bud-1",
            justification="needed", created_at=clock(),
        ))
        svc.record_approval(ApprovalDecision(
            decision_id="dec-00000021", request_ref="req-00000021",
            state=ApprovalState.GRANTED, decided_by="id-operator-1",
            decided_at=clock(), bound_action="may_execute_in_sandbox",
            bound_resource="cand-1", bound_scope="sandbox:isolated",
            bound_budget_ref="bud-1", reason="ok",
        ))
        assert svc.pending_approvals() == []

    def test_unknown_identity_rejected_at_submit(self, svc):
        svc, _store, _clock = svc
        with pytest.raises(QcaeValidationError, match="unknown identity"):
            svc.submit(_job(), [_step("s-1")], submitted_by="id-ghost")

    def test_expired_lease_recovery_via_service(self, svc):
        svc, store, clock = svc
        svc.submit(_job(), [_step("s-1")])
        svc.ready_steps("job-12345678")
        lease = svc.lease_next("job-12345678", "w1")
        clock.advance(120)
        recovered = svc.recover_expired_leases()
        assert "job-12345678:s-1" in recovered
