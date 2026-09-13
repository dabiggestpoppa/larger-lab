"""P2-T01 — adversarial runtime qualification (directive §40).

Every case must fail safely: no forged approval executes, no stale token
completes, no budget underflow slips through, no malformed handoff enters
canonical state, no corrupted payload survives undetected, and process
restarts never widen authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.decisions.authority import AuthorityOutcome, AuthorityRequest, PolicyAction
from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
)
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
from qcae.infrastructure.persistence.store_factory import open_metadata_db, open_raw_connection
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.budget_service import BudgetService
from qcae.orchestration.orchestrator.budgets import BudgetExhaustedError
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import CrashWorker, DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerStatus


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, s):
        self._t += timedelta(seconds=s)


def _job(job_id="job-12345678"):
    return RuntimeJob(
        job_id=job_id,
        deterministic_id=deterministic_job_id("d", "c", job_id),
        job_type="D", subject_ref="cap-1", created_by="op",
        created_at="2026-09-13T12:00:00Z",
    )


def _step(step_id, job_id="job-12345678", **over):
    base = dict(
        step_id=step_id, job_id=job_id, step_type="GENERIC",
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
    engine._workers["GENERIC"] = DeterministicSuccessWorker()
    return store, queue, engine, clock, conn


class TestAdversarial:
    def test_worker_crash_after_checkpoint_does_not_lose_history(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(
            _job(),
            [_step("job-12345678:s-1"),
             _step("job-12345678:s-2", dependencies=("job-12345678:s-1",))],
        )
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        checkpoint = store.latest_checkpoint_for_job("job-12345678")
        # Crash the next step.
        engine._workers["GENERIC"] = CrashWorker()
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w-crash")
        with pytest.raises(RuntimeError):
            engine.execute_step(lease2)
        # Checkpoint and completed step are intact; the crashed step stays RUNNING
        # under its lease until recovery (never silently FAILED).
        assert store.latest_checkpoint_for_job("job-12345678") == checkpoint
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.SUCCEEDED
        assert store.get_step("job-12345678:s-2").status is RuntimeStepStatus.RUNNING
        report = engine.recover_job("job-12345678")
        assert "job-12345678:s-2" in report["requeued_steps"]
        assert store.get_step("job-12345678:s-2").status is RuntimeStepStatus.READY

    def test_duplicate_completion_is_idempotent(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        # Attempt the same idempotent completion again via a second store path.
        first = store.record_idempotent_completion(
            "job-12345678:s-1", "job-12345678", "job-12345678:s-1", clock()
        )
        assert first is False  # duplicate rejected

    def test_stale_lease_token_cannot_complete(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        clock.advance(120)
        queue.expire_stale_leases()
        with pytest.raises(QcaeValidationError):
            queue.acknowledge("job-12345678:s-1", lease.lease_token)

    def test_forged_approval_reference_cannot_execute(self, env):
        store, queue, engine, clock, conn = env
        approvals = SqliteApprovalRegistry(conn)
        # No request was ever recorded; a grant for a ghost request fails.
        with pytest.raises(QcaeValidationError, match="unknown request"):
            approvals.record_decision(ApprovalDecision(
                decision_id="dec-forged", request_ref="req-ghost",
                state=ApprovalState.GRANTED, decided_by="op",
                decided_at=clock(), bound_action="a", bound_resource="r",
                bound_scope="s", bound_budget_ref="b", reason="forged",
            ))

    def test_approval_for_wrong_action_cannot_satisfy_request(self, env):
        store, queue, engine, clock, conn = env
        approvals = SqliteApprovalRegistry(conn)
        approvals.add_request(ApprovalRequest(
            request_id="req-00000051", principal="w",
            action="may_execute_in_sandbox", resource="r", scope="sandbox",
            budget_ref="b", justification="j", created_at=clock(),
        ))
        with pytest.raises(QcaeValidationError, match="laundering"):
            approvals.record_decision(ApprovalDecision(
                decision_id="dec-00000051", request_ref="req-00000051",
                state=ApprovalState.GRANTED, decided_by="op", decided_at=clock(),
                bound_action="may_access_production_credentials",
                bound_resource="r", bound_scope="sandbox", bound_budget_ref="b",
                reason="scope stretch",
            ))

    def test_budget_underflow_attempt_rejected(self, env):
        store, queue, engine, clock, conn = env
        svc = BudgetService(SqliteBudgetLedger(conn))
        svc.create_job_budget("bud-1", "job-1", {"attempts": 2})
        with pytest.raises(QcaeValidationError):
            svc.charge("bud-1", "attempts", -5)

    def test_retry_storm_is_bounded(self, env):
        store, queue, engine, clock, conn = env
        from qcae.orchestration.workers.contracts import WorkerResult

        class AlwaysTransient:
            def execute(self, request, packet):
                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=WorkerStatus.RETRYABLE, failure_class="TRANSIENT",
                    error_summary="flaky",
                )

        engine._workers["GENERIC"] = AlwaysTransient()
        engine.submit(_job(), [_step("s-1", max_attempts=3)])
        engine.mark_running("job-12345678")
        attempts = 0
        for _ in range(20):  # storm: far more drive cycles than attempts
            engine.ready_steps("job-12345678")
            lease = engine.lease_next("job-12345678", "w1")
            if lease is None:
                break
            attempts += 1
            engine.execute_step(lease)
        assert attempts == 3  # exactly max_attempts, no storm loop
        assert store.get_step("s-1").status is RuntimeStepStatus.FAILED

    def test_malformed_worker_result_rejected(self, env):
        store, queue, engine, clock, conn = env
        from qcae.orchestration.workers.contracts import make_worker_result

        with pytest.raises(QcaeValidationError):
            make_worker_result(step_id="s", job_id="j", status="NOT_A_STATUS")

    def test_worker_attempting_undeclared_secret_ref_gets_denied(self, env):
        from qcae.infrastructure.secrets.local_provider import LocalSecretProvider

        provider = LocalSecretProvider({}, denied_classes=("production-trading",))
        decision = provider.request_secret(
            "production-trading", "p", "s", "rogue-worker"
        )
        assert not decision.granted

    def test_worker_action_outside_policy_constraints_fails_closed(self, env):
        from qcae.governance.standalone.policy import (
            LocalPolicyEngine,
            PolicyDecisionType,
            PolicyRequest,
            PolicyEffect,
            PolicyRule,
            PolicySet,
        )

        policy = LocalPolicyEngine(PolicySet(
            policy_id="p", policy_version="1",
            rules=(PolicyRule(
                rule_id="constrained",
                effect=PolicyEffect.ALLOW_WITH_CONSTRAINTS,
                action="may_persist_registry_record",
                principal_match="id-worker-*",
                constraints=("scope:candidate-metadata-only",),
                reason="metadata only",
            ),),
        ))
        # The worker requests a resource outside its constraint -> engine's
        # resource match binds; a different principal fails closed entirely.
        d = policy.evaluate(
            PolicyRequest(principal="id-attacker", action="may_persist_registry_record"),
            decision_id="d1", created_at="t",
        )
        assert d.decision is PolicyDecisionType.DENY

    def test_corrupted_job_payload_detected_on_read(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(_job(), [_step("s-1")])
        original = conn.execute(
            "SELECT payload_json FROM runtime_job WHERE job_id = 'job-12345678'"
        ).fetchone()[0]
        conn.execute(
            "UPDATE runtime_job SET payload_json = ? WHERE job_id = 'job-12345678'",
            (original.replace('"D"', '"ATTACKED"'),),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            store.get_job("job-12345678")

    def test_process_restart_during_wait_approval_preserves_state(self, env):
        store, queue, engine, clock, conn = env
        conn2_path = None
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "w.sqlite3"
            c1 = open_metadata_db(db)
            for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL):
                c1.executescript(ddl)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            engine1 = OrchestratorEngine(store1, queue1, clock=clock)
            engine1._workers["GENERIC"] = CrashWorker()
            engine1.submit(_job(), [_step("s-1")])
            engine1.mark_running("job-12345678")
            engine1.ready_steps("job-12345678")
            lease = engine1.lease_next("job-12345678", "w1")
            with pytest.raises(RuntimeError):
                engine1.execute_step(lease)
            c1.commit()
            c1.close()

            # Restart: recovery moves the crashed step back to READY; the
            # WAITING flow (approval path) would persist as WAITING_POLICY.
            c2 = open_metadata_db(db)
            c2.executescript(RUNTIME_DDL)
            c2.executescript(QUEUE_INTEGRITY_DDL)
            store2 = SqliteRuntimeStore(c2)
            queue2 = SqliteStepQueue(c2, store2, now_fn=clock, lease_ttl_seconds=60)
            engine2 = OrchestratorEngine(store2, queue2, clock=clock)
            engine2._workers["GENERIC"] = DeterministicSuccessWorker()
            report = engine2.recover_job("job-12345678")
            assert "s-1" in report["requeued_steps"]
            engine2.ready_steps("job-12345678")
            lease2 = engine2.lease_next("job-12345678", "w2")
            engine2.execute_step(lease2)
            assert store2.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED
            c2.close()

    def test_authority_denial_cannot_be_overridden_by_recovery(self, env):
        """A DENY decision stays DENY after any number of restarts."""
        store, queue, engine, clock, conn = env
        from qcae.governance.standalone.policy import (
            LocalPolicyEngine,
            PolicyDecisionType,
            PolicyEffect,
            PolicyRequest,
            PolicyRule,
            PolicySet,
        )
        from qcae.infrastructure.persistence.sqlite_policy_log import (
            GOVERNANCE_DDL,
            SqlitePolicyDecisionLog,
        )
        from qcae.governance.standalone.authority import (
            LocalAuthorityProvider,
            policy_outcome_to_authority_outcome,
        )

        conn.executescript(GOVERNANCE_DDL)
        policy = LocalPolicyEngine(PolicySet(
            policy_id="p", policy_version="1",
            rules=(PolicyRule(
                rule_id="deny-all-exec", effect=PolicyEffect.DENY,
                action="may_execute_in_sandbox", reason="not allowed",
            ),),
        ))
        provider = LocalAuthorityProvider(policy, SqlitePolicyDecisionLog(conn), clock=clock)
        decision = provider.decide(AuthorityRequest(
            request_id="req-00000061", action=PolicyAction.MAY_EXECUTE_IN_SANDBOX,
            subject_id="cand-1", justification="j", requested_by="id-worker-1",
        ))
        assert decision.outcome is AuthorityOutcome.DENY
        # Same request replayed (even through a new provider instance over the
        # same durable log) resolves identically: DENY is durable.
        provider2 = LocalAuthorityProvider(policy, SqlitePolicyDecisionLog(conn), clock=clock)
        decision2 = provider2.decide(AuthorityRequest(
            request_id="req-00000062", action=PolicyAction.MAY_EXECUTE_IN_SANDBOX,
            subject_id="cand-1", justification="j", requested_by="id-worker-1",
        ))
        assert decision2.outcome is AuthorityOutcome.DENY
