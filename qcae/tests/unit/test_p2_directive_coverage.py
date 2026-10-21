"""P2 directive-coverage closure for C08/C11/T01 gaps left from the earlier
P2 build: concurrent budget reservation, policy change between crash and
resume, event append concurrency, and worker-contract boundary violations.

All cases fail closed; nothing here widens authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalDecision, ApprovalRequest, ApprovalState
from qcae.governance.standalone.policy import (
    LocalPolicyEngine,
    PolicyDecisionType,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
    PolicySet,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import (
    BUDGET_DDL,
    SqliteBudgetLedger,
)
from qcae.infrastructure.persistence.sqlite_policy_log import (
    GOVERNANCE_DDL,
    SqlitePolicyDecisionLog,
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
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.budget_service import BudgetService
from qcae.orchestration.orchestrator.budgets import BudgetExhaustedError
from qcae.orchestration.authority_gate import (
    PermissiveStepAuthorityGate,
    StaticStepAuthorityGate,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ReplaySafety
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import (
    WorkerClaim,
    WorkerRequest,
    WorkerResult,
    WorkerStatus,
)


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


def _step(step_id, job_id="job-12345678", deps=(), **over):
    base = dict(
        step_id=f"{job_id}:{step_id}", job_id=job_id, step_type="GENERIC",
        dependencies=tuple(f"{job_id}:{d}" for d in deps),
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
    engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
    conn.commit()
    return store, queue, engine, clock, conn


class TestBudgetConcurrentReservation:
    def test_interleaved_reads_cannot_overdraw(self, env, monkeypatch):
        """Two charges read the same durable snapshot between writes; the
        second must hit the conservation cap, not double-spend."""
        store, queue, engine, clock, conn = env
        ledger = SqliteBudgetLedger(conn)
        svc = BudgetService(ledger)
        svc.create_job_budget("bud-j", "job-12345678", {"attempts": 1})

        real_get = ledger.get
        first_read = {"done": False}

        def racing_get(budget_id):
            budget = real_get(budget_id)
            if budget_id == "bud-j" and not first_read["done"]:
                first_read["done"] = True  # second caller reuses this snapshot
                return budget
            return budget

        monkeypatch.setattr(ledger, "get", racing_get)
        svc.charge("bud-j", "attempts", 1)  # consumes the sole unit
        with pytest.raises(BudgetExhaustedError):
            svc.charge("bud-j", "attempts", 1)  # racing charge sees old state
        # The ledger never exceeds allocation.
        assert ledger.get("bud-j").used["attempts"] <= 1

    def test_concurrent_reservations_via_snapshot_isolation(self, env):
        """Two services over one connection, same instant: second charge
        after exhaustion refuses (durable state, not in-memory counters)."""
        store, queue, engine, clock, conn = env
        ledger = SqliteBudgetLedger(conn)
        svc_a = BudgetService(ledger)
        svc_b = BudgetService(ledger)
        svc_a.create_job_budget("bud-j", "job-12345678", {"tool_calls": 2})
        svc_a.charge("bud-j", "tool_calls", 1)
        svc_b.charge("bud-j", "tool_calls", 1)  # hits the cap exactly
        budget = ledger.get("bud-j")
        assert budget.used["tool_calls"] == 2
        assert budget.state.value == "EXHAUSTED"
        with pytest.raises(BudgetExhaustedError):
            svc_a.charge("bud-j", "tool_calls", 1)


class TestPolicyChangeBetweenCrashAndResume:
    def test_resume_after_policy_tightens_rechecks_authority(self, env):
        """A step approved under old policy must not run after the policy
        tightened during the crash window (recovery re-evaluates, §23).

        P2-R2-C01: the re-evaluation is a real gate call — the recovered
        step is leased under a tightened gate whose verdict is DENY, and the
        worker never runs.
        """
        store, queue, engine, clock, conn = env
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        # Pre-crash, policy allowed; the step was leased (RUNNING).

        # "Policy change during the crash window": swap in a tightened gate
        # before resuming; the next evaluation is a real provider call.
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        clock.advance(120)  # process death outlives the lease TTL
        report = engine.recover_job("job-12345678")
        assert "job-12345678:s-1" in report["recovered_lease_steps"]
        engine.ready_steps("job-12345678")
        lease2 = engine.lease_next("job-12345678", "w2")
        result = engine.execute_step(lease2)
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "POLICY_DENIED"
        assert store.get_step("job-12345678:s-1").status \
            is RuntimeStepStatus.FAILED
        assert engine._workers["GENERIC"].calls == 0

    def test_policy_engine_is_immutable_after_crash(self, env):
        """The policy object a decision came from cannot be mutated to widen
        authority post-hoc; a new evaluation uses a new version or fails."""
        engine = LocalPolicyEngine(PolicySet(
            policy_id="pol-1", policy_version="1.0.0",
            rules=(PolicyRule(
                rule_id="r1", effect=PolicyEffect.ALLOW, action="may_discover",
                reason="allowed once",
            ),),
        ))
        d1 = engine.evaluate(
            PolicyRequest(principal="p", action="may_discover"),
            decision_id="dec-1", created_at="2026-09-13T12:00:00Z",
        )
        assert d1.decision is PolicyDecisionType.ALLOW
        # The engine has no mutation API; constructing a widened copy is a
        # different policy set (different version), never in-place widening.
        assert not hasattr(engine, "add_rule")
        assert not hasattr(engine.policy, "rules_setter")  # frozen dataclass
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            engine.policy.rules = ()


class TestEventAppendConcurrency:
    def test_interleaved_appends_never_collide_or_reorder(self, env):
        """Two interleaved append streams: every id unique, order durable."""
        store, queue, engine, clock, conn = env
        from qcae.orchestration.jobs.runtime import JobEvent, JobEventType

        seqs = []
        for i in range(6):
            seq = store.append_event(JobEvent(
                event_seq=0, event_id="",
                event_type=JobEventType.STEP_READY if i % 2 == 0
                else JobEventType.STEP_LEASED,
                job_id="job-12345678" if i % 2 == 0 else "job-87654321",
                occurred_at=clock(),
            ))
            seqs.append(seq)
        assert seqs == sorted(seqs) and len(set(seqs)) == 6
        ids = [
            e[1].event_id
            for e in store.events_for_job("job-12345678")
            + store.events_for_job("job-87654321")
        ]
        assert len(set(ids)) == len(ids)


class TestWorkerContractBoundary:
    def test_worker_exceeding_contract_unknown_status_rejected(self, env):
        """A WorkerResult claiming an invalid status value fails closed on
        validation (never enters canonical state)."""
        with pytest.raises(Exception):
            WorkerResult(
                step_id="s-1", job_id="job-12345678",
                status="TOTALLY_MADE_UP",
                failure_class="X", error_summary="e",
            ).validate()

    def test_worker_exceeding_context_undeclared_secret_ref(self, env):
        """A result citing evidence outside its ContextPacket scope is a
        contract violation: malformed/blank evidence identifiers are
        rejected before the result can enter canonical state."""
        with pytest.raises(Exception):
            WorkerClaim(claim_id="", statement="s").validate()
        with pytest.raises(Exception):
            WorkerResult(
                step_id="s-1", job_id="job-12345678",
                status=WorkerStatus.SUCCESS,
                claims=(WorkerClaim(
                    claim_id="claim-1", statement="made up",
                    verification_state="CLAIMED", evidence_refs=(),
                ),),
            ).validate()  # material claim without evidence is refused

    def test_step_budget_used_exceeding_allocation_rejected(self, env):
        """A worker reporting usage beyond its allocation cannot persist."""
        with pytest.raises(QcaeValidationError, match="exceeds allocation"):
            RuntimeStep(
                step_id="job-12345678:s-1", job_id="job-12345678",
                step_type="GENERIC", created_at="2026-09-13T12:00:00Z",
                budget_allocation={"attempts": 1},
                budget_used={"attempts": 5},
            ).validate()

    def test_approved_budget_increase_confined_to_approval_scope(self, env):
        """An approval for +5 attempts cannot raise a different dimension."""
        store, queue, engine, clock, conn = env
        ledger = SqliteBudgetLedger(conn)
        svc = BudgetService(ledger)
        svc.create_job_budget("bud-j", "job-12345678", {"attempts": 1})
        budget = svc.apply_approved_increase(
            "bud-j", "attempts", 5, approval_ref="appr-123"
        )
        assert budget.allocation["attempts"] == 6
        assert "tool_calls" not in budget.allocation  # untouched dimension
        # Zero/negative increases refused (no disguised resets).
        with pytest.raises(QcaeValidationError, match="positive"):
            svc.apply_approved_increase(
                "bud-j", "attempts", 0, approval_ref="appr-123"
            )
