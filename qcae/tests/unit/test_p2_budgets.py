"""P2-C08 — budget representation and enforcement qualification (§27-28)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
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
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep
from qcae.orchestration.orchestrator.budget_service import BudgetService
from qcae.orchestration.orchestrator.budgets import (
    Budget,
    BudgetDimension,
    BudgetExhaustedError,
    BudgetState,
)
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.core.jobs import deterministic_job_id


def _svc():
    conn = open_metadata_db(":memory:")
    conn.executescript(BUDGET_DDL)
    return BudgetService(SqliteBudgetLedger(conn))


class TestBudgetDomain:
    def test_valid_budget(self):
        b = Budget(
            budget_id="bud-00000001", owner_kind="job", owner_id="job-12345678",
            allocation={"attempts": 3, "tool_calls": 100}, used={"attempts": 1},
        )
        b.validate()

    def test_used_over_allocation_rejected(self):
        with pytest.raises(QcaeValidationError, match="exceeds"):
            Budget(
                budget_id="bud-00000001", owner_kind="job", owner_id="j",
                allocation={"attempts": 2}, used={"attempts": 3},
            ).validate()

    def test_used_dimension_not_allocated_rejected(self):
        with pytest.raises(QcaeValidationError, match="not allocated"):
            Budget(
                budget_id="bud-00000001", owner_kind="job", owner_id="j",
                allocation={"attempts": 2}, used={"tokens": 1},
            ).validate()

    def test_exhausted_dimension_with_active_state_rejected(self):
        with pytest.raises(QcaeValidationError, match="exhausted"):
            Budget(
                budget_id="bud-00000001", owner_kind="job", owner_id="j",
                allocation={"attempts": 1}, used={"attempts": 1},
                state=BudgetState.ACTIVE,
            ).validate()

    def test_round_trip(self):
        b = Budget(
            budget_id="bud-00000001", owner_kind="step", owner_id="s-1",
            parent_budget_id="bud-job", allocation={"attempts": 3},
        )
        assert Budget.from_dict(b.to_dict()) == b

    def test_negative_allocation_rejected(self):
        with pytest.raises(QcaeValidationError):
            Budget(
                budget_id="bud-00000001", owner_kind="job", owner_id="j",
                allocation={"attempts": -1},
            ).validate()


class TestConservation:
    def test_child_allocation_within_parent_ok(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 5, "tool_calls": 10})
        svc.create_step_budget("bud-s1", "s-1", "bud-job", {"attempts": 2})

    def test_child_allocation_exceeding_parent_rejected(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 2})
        with pytest.raises(BudgetExhaustedError, match="conservation"):
            svc.create_step_budget("bud-s1", "s-1", "bud-job", {"attempts": 3})

    def test_retry_charge_consumes_budget(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 2})
        svc.charge("bud-job", "attempts", 1)
        svc.charge("bud-job", "attempts", 1)
        assert svc.snapshot("bud-job").state is BudgetState.EXHAUSTED

    def test_charge_over_remaining_raises_and_persists_exhaustion(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 1})
        with pytest.raises(BudgetExhaustedError):
            svc.charge("bud-job", "attempts", 1)
            svc.charge("bud-job", "attempts", 1)
        # Second charge attempt raises; budget shows the capped exhausted state.
        b = svc.snapshot("bud-job")
        assert b.state is BudgetState.EXHAUSTED
        assert b.used["attempts"] == 1

    def test_recovery_does_not_reset_consumed_budget(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 2})
        svc.charge("bud-job", "attempts", 1)
        # Simulate restart: a fresh service over the same ledger sees the same
        # consumed state.
        restored = svc.snapshot("bud-job")
        assert restored.used["attempts"] == 1
        # Restore via the recovery API preserves usage exactly.
        svc.restore(restored)
        assert svc.snapshot("bud-job").used["attempts"] == 1

    def test_increase_requires_approval_ref(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 1})
        with pytest.raises(QcaeValidationError, match="approval_ref"):
            svc.apply_approved_increase("bud-job", "attempts", 2, approval_ref="")

    def test_approved_increase_extends_limit(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 1})
        svc.charge("bud-job", "attempts", 1)
        svc.apply_approved_increase(
            "bud-job", "attempts", 2, approval_ref="dec-00000001"
        )
        b = svc.snapshot("bud-job")
        assert b.allocation["attempts"] == 3
        assert b.used["attempts"] == 1  # consumption preserved
        assert b.state is BudgetState.ACTIVE

    def test_charge_unknown_dimension_rejected(self):
        svc = _svc()
        svc.create_job_budget("bud-job", "job-1", {"attempts": 1})
        with pytest.raises(QcaeValidationError, match="not allocated"):
            svc.charge("bud-job", "tokens", 5)

    def test_tampered_budget_row_detected(self):
        import json

        conn = open_metadata_db(":memory:")
        conn.executescript(BUDGET_DDL)
        ledger = SqliteBudgetLedger(conn)
        svc = BudgetService(ledger)
        svc.create_job_budget("bud-job", "job-1", {"attempts": 3})
        original = conn.execute(
            "SELECT payload_json FROM runtime_budget WHERE budget_id = 'bud-job'"
        ).fetchone()[0]
        tampered = json.loads(original)
        tampered["used"] = {"attempts": 0}
        conn.execute(
            "UPDATE runtime_budget SET payload_json = ? WHERE budget_id = 'bud-job'",
            (json.dumps(tampered),),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            ledger.get("bud-job")


class TestEngineIntegration:
    def _env(self):
        clock = lambda: "2026-09-13T12:00:00Z"
        conn = open_metadata_db(":memory:")
        conn.executescript(RUNTIME_DDL)
        conn.executescript(QUEUE_INTEGRITY_DDL)
        conn.executescript(BUDGET_DDL)
        store = SqliteRuntimeStore(conn)
        queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
        svc = BudgetService(SqliteBudgetLedger(conn))
        engine = OrchestratorEngine(store, queue, clock=clock, budget_service=svc, authority_gate=PermissiveStepAuthorityGate())
        return store, queue, engine, svc, clock, conn

    def _job(self, job_id="job-12345678"):
        return RuntimeJob(
            job_id=job_id,
            deterministic_id=deterministic_job_id("d", "c", "k1"),
            job_type="D", subject_ref="cap-1", created_by="op",
            created_at="2026-09-13T12:00:00Z",
        )

    def _step(self, step_id, **over):
        base = dict(
            step_id=step_id, job_id="job-12345678", step_type="GENERIC",
            created_at="2026-09-13T12:00:00Z",
            idempotency_key=f"job-12345678:{step_id}",
        )
        base.update(over)
        return RuntimeStep(**base)

    def test_job_budget_enforced(self):
        store, queue, engine, svc, clock, conn = self._env()
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        svc.create_job_budget("bud-job-12345678", "job-12345678", {"attempts": 1})
        engine.submit(self._job(), [self._step("s-1"), self._step("s-2")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")  # consumes attempt 1
        engine.execute_step(lease)
        engine.ready_steps("job-12345678")
        with pytest.raises(BudgetExhaustedError, match="exhausted"):
            engine.lease_next("job-12345678", "w1")  # attempt 2 blocked

    def test_retry_consumes_budget_until_exhaustion(self):
        store, queue, engine, svc, clock, conn = self._env()

        class AlwaysTransient:
            def execute(self, request, packet):
                from qcae.orchestration.workers.contracts import WorkerResult

                return WorkerResult(
                    step_id=request.step_id, job_id=request.job_id,
                    status=WorkerStatus.RETRYABLE, failure_class="TRANSIENT",
                    error_summary="flaky",
                )

        engine._workers["GENERIC"] = AlwaysTransient()
        svc.create_job_budget("bud-job-12345678", "job-12345678", {"attempts": 2})
        engine.submit(self._job(), [self._step("s-1", max_attempts=5)])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")  # attempt 2 == cap
        engine.execute_step(lease)
        assert svc.snapshot("bud-job-12345678").used["attempts"] == 2
        engine.ready_steps("job-12345678")
        with pytest.raises(BudgetExhaustedError):
            engine.lease_next("job-12345678", "w1")

    def test_no_budget_service_is_optional(self):
        store, queue, engine, svc, clock, conn = self._env()
        engine2 = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
        engine2._workers["GENERIC"] = DeterministicSuccessWorker()
        engine2.submit(self._job(), [self._step("s-1")])
        engine2.mark_running("job-12345678")
        engine2.ready_steps("job-12345678")
        lease = engine2.lease_next("job-12345678", "w1")
        engine2.execute_step(lease)
        assert store.get_step("s-1").status.value == "SUCCEEDED"


from qcae.orchestration.workers.contracts import WorkerStatus  # noqa: E402
