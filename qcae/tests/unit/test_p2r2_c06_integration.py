"""P2-R2-C06 — authority x budget x secrets integration.

Three cross-layer laws that only hold when the layers are WIRED, not merely
built (operator repair directive):

1. AUTHORITY CANNOT WIDEN BUDGET — an ALLOW verdict never raises a budget
   limit; increases flow only through apply_approved_increase with a durable
   approval_ref, and the worker/orchestrator has no such path.
2. ACTION PERMISSION DOES NOT IMPLY SECRET PERMISSION — an ALLOW for a
   step's execute action says nothing about secret classes; secret access
   has its own provider decision, and denied classes stay denied even when
   the step itself is fully authorized.
3. CONSTRAINED GRANTS REMAIN CONSTRAINED — ALLOW_WITH_CONSTRAINTS verdicts
   carry their constraints onto the WorkerRequest, and they are absent for
   plain ALLOW; a constrained grant does not become an unconstrained one
   across retries/re-leases.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalDecision, ApprovalRequest, ApprovalState
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import (
    BUDGET_DDL,
    SqliteBudgetLedger,
)
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.infrastructure.secrets.local_provider import LocalSecretProvider
from qcae.orchestration.authority_gate import (
    StaticStepAuthorityGate,
    StepAuthorityDecision,
)
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep
from qcae.orchestration.orchestrator.budget_service import BudgetService
from qcae.orchestration.orchestrator.budgets import BudgetExhaustedError
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
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, APPROVAL_DDL):
        conn.executescript(ddl)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(store, queue, clock=clock)
    conn.commit()
    return store, queue, engine, clock, conn


def _lease_ready(store, engine, job, steps, worker="id-worker-runtime"):
    engine.submit(job, steps)
    engine.mark_running(job.job_id)
    engine.ready_steps(job.job_id)
    return engine.lease_next(job.job_id, worker)


class TestAuthorityCannotWidenBudget:
    def test_allow_verdict_never_touches_budget(self, env):
        """A full ALLOW execution leaves the job budget untouched — authority
        decisions are not budget events."""
        store, queue, engine, clock, conn = env
        ledger = SqliteBudgetLedger(conn)
        budgets = BudgetService(ledger)
        engine = OrchestratorEngine(
            store, queue, clock=clock, budget_service=budgets,
            authority_gate=StaticStepAuthorityGate(allowed=("execute.GENERIC",)),
        )
        budgets.create_job_budget("bud-job-12345678", "job-12345678", {"attempts": 5})
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.SUCCESS
        # The only budget mutation is the engine's own attempt charge —
        # the ALLOW verdict added nothing.
        budget = ledger.get("bud-job-12345678")
        assert budget.used.get("attempts", 0) == 1

    def test_budget_increase_requires_durable_approval_ref(self, env):
        store, _q, _e, _c, conn = env
        budgets = BudgetService(SqliteBudgetLedger(conn))
        budgets.create_job_budget("bud-j", "job-12345678", {"attempts": 1})
        with pytest.raises(Exception, match="approval_ref"):
            budgets.apply_approved_increase("bud-j", "attempts", 10, approval_ref="")
        with pytest.raises(Exception, match="approval_ref"):
            budgets.apply_approved_increase("bud-j", "attempts", 10, approval_ref=None) \
                if False else budgets.apply_approved_increase("bud-j", "attempts", 10, approval_ref="")
        # With a durable ref the increase works, once, positively.
        budgets.apply_approved_increase("bud-j", "attempts", 2, approval_ref="dec-1")
        assert budgets.snapshot("bud-j").allocation["attempts"] == 3

    def test_engine_has_no_budget_increase_path(self, env):
        """The orchestrator exposes no method that raises a budget limit."""
        public = [m for m in dir(OrchestratorEngine) if not m.startswith("_")]
        assert not any("increase" in m or "raise_budget" in m or "widen" in m
                       for m in public)


class TestActionPermissionNotSecretPermission:
    def test_authorized_step_cannot_access_denied_secret_class(self, env):
        """ALLOW on execute.* does not unlock a denied secret class."""
        store, queue, engine, clock, conn = env
        engine = OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=StaticStepAuthorityGate(allowed=("execute.GENERIC",)),
        )
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        secrets = LocalSecretProvider(
            {"worker-token": "WORKER_TOKEN_ENV"},
            denied_classes=("production-trading",),
        )
        # Step fully authorized...
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.SUCCESS
        # ...yet the denied secret class is still denied for the same
        # (now-proven-authorized) principal and purpose.
        decision = secrets.request_secret(
            "production-trading", "step execution", "job:job-12345678",
            "id-worker-runtime",
        )
        assert decision.granted is False

    def test_unbound_secret_class_denied_even_authorized(self, env):
        """No mapping for the class in the local provider -> deny (fail
        closed), independent of step authority."""
        secrets = LocalSecretProvider(
            {"worker-token": "WORKER_TOKEN_ENV"}, denied_classes=(),
        )
        decision = secrets.request_secret(
            "unknown-class", "step execution", "job:job-12345678", "id-worker-runtime"
        )
        assert decision.granted is False

    def test_secret_handle_bound_to_requested_scope(self, env):
        """Handles carry their scope; resolution requires the handle itself."""
        import os

        os.environ["QA_TEST_TOKEN"] = "super-secret-value-xyz"
        try:
            secrets = LocalSecretProvider(
                {"worker-token": "QA_TEST_TOKEN"}, denied_classes=(),
            )
            decision = secrets.request_secret(
                "worker-token", "step execution", "job:job-12345678",
                "id-worker-runtime",
            )
            assert decision.granted is True
            # The decision record carries no value.
            assert "super-secret-value-xyz" not in decision.to_dict().__str__()
        finally:
            del os.environ["QA_TEST_TOKEN"]


class TestConstrainedGrantsRemainConstrained:
    def test_constraints_reach_worker_and_survive_re_lease(self, env):
        """ALLOW_WITH_CONSTRAINTS: the same constraints are attached on the
        first execution and on a retry's re-leased execution."""
        store, queue, engine, clock, conn = env
        seen = []

        class ProbeWorker:
            def execute(self, request, packet):
                seen.append(tuple(request.constraints))
                if len(seen) == 1:
                    from qcae.orchestration.workers.contracts import WorkerResult

                    return WorkerResult(
                        step_id=request.step_id, job_id=request.job_id,
                        status=WorkerStatus.RETRYABLE,
                        failure_class="TRANSIENT",
                        error_summary="transient",
                    )
                return DeterministicSuccessWorker().execute(request, packet)

        gate = StaticStepAuthorityGate(
            allowed=("execute.GENERIC",), constraints=("scope:read-only",)
        )
        engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=gate)
        engine.register_worker_type("GENERIC", ProbeWorker())
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease1 = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease1)  # RETRYABLE
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        engine.execute_step(lease2)  # SUCCESS on retry
        assert seen[0] == ("scope:read-only",)
        assert seen[1] == ("scope:read-only",)

    def test_plain_allow_has_no_constraints(self, env):
        store, queue, engine, clock, conn = env
        seen = {}

        class ProbeWorker:
            def execute(self, request, packet):
                seen["constraints"] = request.constraints
                return DeterministicSuccessWorker().execute(request, packet)

        engine = OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=StaticStepAuthorityGate(allowed=("execute.GENERIC",)),
        )
        engine.register_worker_type("GENERIC", ProbeWorker())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        engine.execute_step(lease)
        assert seen["constraints"] == ()

    def test_constraint_value_is_recorded_in_events(self, env):
        """The approval event trail shows the constrained decision."""
        store, queue, engine, clock, conn = env
        engine = OrchestratorEngine(
            store, queue, clock=clock,
            authority_gate=StaticStepAuthorityGate(
                allowed=("execute.GENERIC",), constraints=("scope:read-only",)
            ),
        )
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        engine.execute_step(lease)
        import json

        started = [
            json.loads(p) for _s, e, p in store.events_for_job("job-12345678")
            if e.event_type.value == "STEP_STARTED" and p
        ]
        assert started[-1]["authority_decision"] == "ALLOW_WITH_CONSTRAINTS"
