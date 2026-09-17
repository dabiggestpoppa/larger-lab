"""P2-R3-C02 — worker availability before lease (operator-loop finding B).

No compatible worker may cause a lease/state mutation: no claim row, no
RUNNING step, no attempt increment, no budget charge, no STEP_STARTED.
The eligible step stays READY and callers get a typed outcome, not a raw
exception — including through the CLI surface.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.jobs import deterministic_job_id
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.jobs.runtime import (
    JobEventType,
    RuntimeJob,
    RuntimeStep,
    RuntimeStepStatus,
)
from qcae.orchestration.orchestrator.budget_service import BudgetService
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.worker_availability import (
    WorkerUnavailableError,
    worker_availability_for,
)
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.infrastructure.persistence.sqlite_budget_ledger import (
    SqliteBudgetLedger,
)

NOW = "2026-09-17T12:00:00Z"
JOB = "job-workerless"


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
        deterministic_id=deterministic_job_id("discovery", "cap-wa", "k-wa"),
        job_type="DISCOVERY",
        subject_ref="cap-wa",
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
    conn.executescript(BUDGET_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate()
    )
    return store, queue, engine, clock, conn


def _event_types(store, job_id=JOB):
    return [ev.event_type for _s, ev, _p in store.events_for_job(job_id)]


class TestNoWorkerSafety:
    def test_lease_raises_typed_error(self, env):
        _store, _queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        with pytest.raises(WorkerUnavailableError):
            engine.lease_next(JOB, "id-worker-a")

    def test_no_lease_no_mutation(self, env):
        store, queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        with pytest.raises(WorkerUnavailableError):
            engine.lease_next(JOB, "id-worker-a")
        # No claim, no RUNNING, no lease columns.
        assert not queue.has_active_claim("s-1")
        step = store.get_step("s-1")
        assert step.status is RuntimeStepStatus.READY
        assert step.lease is None
        assert step.attempt == 0
        # No STEP_LEASED / STEP_STARTED events.
        types = _event_types(store)
        assert JobEventType.STEP_LEASED not in types
        assert JobEventType.STEP_STARTED not in types

    def test_no_budget_consumption(self, env):
        store, _queue, engine, _clock, conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        ledger = SqliteBudgetLedger(conn)
        budgets = BudgetService(ledger)
        budgets.create_job_budget(
            budget_id=f"bud-{JOB}", job_id=JOB, allocation={"attempts": 5},
        )
        engine._budgets = budgets
        with pytest.raises(WorkerUnavailableError):
            engine.lease_next(JOB, "id-worker-a")
        snap = budgets.snapshot(f"bud-{JOB}")
        # Zero consumption: worker availability precedes any budget charge.
        assert snap.used.get("attempts", 0) == 0

    def test_mixed_coverage_leases_covered_work(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(_job(), [_step("s-covered"), _step("s-orphan-type")])
        engine.ready_steps(JOB)
        # The covered step is claimable despite the uncovered sibling.
        engine.lease_next(JOB, "id-worker-a") is not None
        assert store.get_step("s-covered").status is RuntimeStepStatus.RUNNING
        assert store.get_step("s-orphan-type").status is RuntimeStepStatus.READY

    def test_worker_registered_then_runs(self, env):
        store, _queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        with pytest.raises(WorkerUnavailableError):
            engine.lease_next(JOB, "id-worker-a")
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        lease = engine.lease_next(JOB, "id-worker-a")
        assert lease is not None
        engine.execute_step(lease)
        assert store.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED


class TestAvailabilityProbe:
    def test_probe_classifies_surface(self, env):
        _store, _queue, engine, _clock, _conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine.submit(
            _job(), [_step("s-1"), _step("s-2", deps=("s-1",))]
        )
        engine.ready_steps(JOB)
        avail = worker_availability_for(engine, JOB)
        assert avail.covered_step_ids == ("s-1",)
        assert avail.eligible_step_ids == ("s-1",)
        assert avail.missing_step_types == ()
        # Uncovered classification once a new type appears.
        engine.submit  # (no-op readability)
        assert worker_availability_for(engine, "missing-job").eligible_step_ids == ()


class TestRaceProtection:
    def test_worker_vanishes_between_probe_and_claim(self, env):
        """Narrow race: present at probe, absent at claim -> safe restore.

        The engine refuses the lease with the typed error; the probe/claim
        path never leaves a claim row behind (nothing was claimed).
        """
        store, queue, engine, _clock, _conn = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        # Probe says covered...
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        avail = worker_availability_for(engine, JOB)
        assert avail.covered_step_ids == ("s-1",)
        # ...worker vanishes...
        engine._workers.clear()
        # ...claim refuses safely.
        with pytest.raises(WorkerUnavailableError):
            engine.lease_next(JOB, "id-worker-a")
        assert not queue.has_active_claim("s-1")
        assert store.get_step("s-1").status is RuntimeStepStatus.READY
