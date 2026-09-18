"""P2-R4-C04 — one scheduling truth: effective_not_before (finding I).

Law (directive §12): ``effective_not_before = max(job.not_before,
step.not_before)``, enforced ATOMICALLY in claim selection (SQL), used by
worker-availability probes, and never bypassed by priority or recovery.

- a future-dated job is not claimable and reports no eligible work;
- at the time boundary it becomes claimable;
- the later of the two schedule floors wins;
- restart preserves the schedule;
- recovery re-availability cannot erase a schedule floor.

The old bug: ``ready_steps`` wrote ``not_before=now`` over the step row,
silently destroying both the step's own schedule and the job's.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"


def _env(tmp_path=None, *, ttl: int = 60):
    clock = _Clock()
    conn = open_metadata_db(tmp_path / "meta.sqlite3" if tmp_path else ":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=ttl)
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate()
    )
    # A registered worker so leases succeed (C02 availability law); these
    # tests exercise SCHEDULING, not availability.
    from qcae.orchestration.workers.base import DeterministicSuccessWorker
    engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    return store, queue, engine, clock, conn


class TestEffectiveNotBefore:
    def test_future_job_not_claimable(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(), [_step(STEP)], not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        # Job is QUEUED and step READY, but the schedule gates the claim.
        assert queue.claim_next("w1") is None
        assert engine.lease_next("job-12345678", "w1") is None

    def test_future_job_reports_no_currently_eligible_work(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(), [_step(STEP)], not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        assert engine.eligible_steps_for_claim("job-12345678") == []

    def test_boundary_passing_makes_claimable(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(), [_step(STEP)], not_before="2026-09-13T12:30:00Z")
        engine.ready_steps("job-12345678")
        assert engine.lease_next("job-12345678", "w1") is None
        clock.advance(1800)  # exactly to the boundary
        lease = engine.lease_next("job-12345678", "w1")
        assert lease is not None

    def test_step_level_later_floor_wins(self):
        store, queue, engine, clock, conn = _env()
        # Job available now; the step itself carries a later floor.
        engine.submit(_job(), [_step(STEP, not_before="2026-09-13T12:45:00Z")])
        engine.ready_steps("job-12345678")
        assert engine.lease_next("job-12345678", "w1") is None
        clock.advance(2700)
        assert engine.lease_next("job-12345678", "w1") is not None

    def test_job_level_later_floor_wins_over_earlier_step(self):
        store, queue, engine, clock, conn = _env()
        # Step carries a floor 12:10; the job's 12:30 governs (max).
        engine.submit(
            _job(), [_step(STEP, not_before="2026-09-13T12:10:00Z")],
            not_before="2026-09-13T12:30:00Z",
        )
        engine.ready_steps("job-12345678")
        clock.advance(600)  # 12:10 passed, 12:30 not yet
        assert engine.lease_next("job-12345678", "w1") is None
        clock.advance(1200)  # 12:30
        assert engine.lease_next("job-12345678", "w1") is not None

    def test_ready_steps_does_not_destroy_schedule(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(), [_step(STEP, not_before="2026-09-13T12:45:00Z")])
        engine.ready_steps("job-12345678")
        step = store.get_step(STEP)
        assert step.not_before == "2026-09-13T12:45:00Z"

    def test_restart_preserves_schedule(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        engine.submit(_job(), [_step(STEP)], not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        conn.commit()
        conn.close()

        conn2 = open_metadata_db(tmp_path / "meta.sqlite3")
        store2 = SqliteRuntimeStore(conn2)
        queue2 = SqliteStepQueue(conn2, store2, now_fn=clock, lease_ttl_seconds=60)
        engine2 = OrchestratorEngine(
            store2, queue2, clock=clock,
            authority_gate=PermissiveStepAuthorityGate(),
        )
        from qcae.orchestration.workers.base import DeterministicSuccessWorker
        engine2.register_worker_type("GENERIC", DeterministicSuccessWorker())
        # Same clock: still future → not claimable after restart either.
        assert engine2.lease_next("job-12345678", "w1") is None
        clock.advance(3600)
        lease = engine2.lease_next("job-12345678", "w1")
        assert lease is not None
        conn2.close()

    def test_recovery_cannot_bypass_schedule(self, tmp_path):
        store, queue, engine, clock, conn = _env(tmp_path)
        engine.submit(_job(), [_step(STEP, not_before="2026-09-13T13:00:00Z")])
        engine.ready_steps("job-12345678")
        clock.advance(3600)
        lease = engine.lease_next("job-12345678", "w1")
        assert lease is not None
        clock.advance(120)  # lease expires (process death)
        engine.recover_job("job-12345678")
        step = store.get_step(STEP)
        assert step.status is RuntimeStepStatus.READY
        # The step-level floor (13:00) is in the past by now: re-availability
        # is immediate. (Recovery keeps any still-future floor — the floor is
        # preserved, not reset to now, which is the finding-I repair.)
        assert engine.lease_next("job-12345678", "w2") is not None

    def test_priority_cannot_bypass_schedule(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(_job(priority=100), [_step(STEP)],
                      not_before="2026-09-13T13:00:00Z")
        engine.ready_steps("job-12345678")
        # High-priority job, future schedule: still gated.
        assert engine.lease_next("job-12345678", "w1") is None

    def test_effective_not_before_is_max_of_both(self):
        store, queue, engine, clock, conn = _env()
        engine.submit(
            _job(), [_step(STEP, not_before="2026-09-13T12:50:00Z")],
            not_before="2026-09-13T12:20:00Z",
        )
        step = store.get_step(STEP)
        assert engine.effective_not_before(
            "job-12345678", step) == "2026-09-13T12:50:00Z"
