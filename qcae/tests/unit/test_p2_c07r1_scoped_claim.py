"""P2-C07R1 — job-scoped atomic queue claim (repair directive §2.1).

Law under test: a worker must never obtain ownership of an ineligible step
merely to discover afterward that the step was ineligible. Eligibility is
enforced inside the atomic claim operation; there is no global
claim-then-filter and no claim-then-release scheduling path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.jobs.runtime import RuntimeStep, RuntimeStepStatus


class _Clock:
    def __init__(self) -> None:
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def now(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock.now, lease_ttl_seconds=60)
    return store, queue, clock, conn


def _ready_step(step_id, job_id="job-A", **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="GENERIC",
        status=RuntimeStepStatus.READY,
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


class TestJobScopedClaim:
    def test_job_a_can_never_claim_job_b(self, env):
        """lease_next(job_A) can never claim job_B's READY step."""
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        store.add_step(_ready_step("b-1", job_id="job-B"), not_before=clock.now())

        lease = queue.claim_next("w1", job_id="job-A")
        assert lease is not None
        assert lease.job_id == "job-A"
        assert lease.step_id == "a-1"

    def test_job_b_remains_immediately_claimable(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        store.add_step(_ready_step("b-1", job_id="job-B"), not_before=clock.now())

        lease_a = queue.claim_next("w1", job_id="job-A")
        assert lease_a is not None
        # job-B was untouched by job-A's claim — claimable right now.
        lease_b = queue.claim_next("w2", job_id="job-B")
        assert lease_b is not None
        assert lease_b.step_id == "b-1"
        assert lease_b.lease_owner == "w2"

    def test_foreign_step_survives_engine_scoping_untouched(self, env):
        """Engine lease_next must not strand another job's step."""
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        store.add_step(_ready_step("b-1", job_id="job-B"), not_before=clock.now())

        lease = queue.claim_next(
            "w1", eligible_step_ids={"a-1"}, job_id="job-A"
        )
        assert lease is not None and lease.step_id == "a-1"
        # job-B's step has no claim row and stays READY.
        assert queue.has_active_claim("b-1") is False
        assert store.get_step("b-1").status is RuntimeStepStatus.READY

    def test_empty_eligible_set_creates_no_claim_rows(self, env):
        store, queue, clock, conn = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        # Explicitly empty eligibility: nothing to claim, nothing written.
        assert queue.claim_next("w1", eligible_step_ids=set()) is None
        rows = conn.execute("SELECT COUNT(*) FROM runtime_queue_claim").fetchone()[0]
        assert rows == 0

    def test_disjoint_eligible_set_returns_none(self, env):
        store, queue, clock, conn = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        assert queue.claim_next("w1", eligible_step_ids={"nonexistent"}) is None
        rows = conn.execute("SELECT COUNT(*) FROM runtime_queue_claim").fetchone()[0]
        assert rows == 0

    def test_ineligible_ready_step_not_claimed_even_if_only_candidate(self, env):
        """An eligible set excluding the only READY step must yield None."""
        store, queue, clock, conn = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        assert queue.claim_next("w1", eligible_step_ids={"a-OTHER"}) is None
        assert queue.has_active_claim("a-1") is False


class TestClaimConcurrency:
    def test_concurrent_claims_yield_one_owner(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        first = queue.claim_next("w1", job_id="job-A")
        second = queue.claim_next("w2", job_id="job-A")
        assert first is not None
        assert second is None
        assert queue.lease_owner_of("a-1") == "w1"

    def test_lost_race_falls_through_to_next_candidate(self, env):
        """A lost claim race must not strand the remaining eligible step."""
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        store.add_step(_ready_step("a-2", job_id="job-A"), not_before=clock.now())
        first = queue.claim_next("w1", job_id="job-A")
        second = queue.claim_next("w2", job_id="job-A")
        assert first is not None and second is not None
        assert {first.step_id, second.step_id} == {"a-1", "a-2"}
        assert first.lease_token != second.lease_token


class TestExpiryInteraction:
    def test_stale_lease_still_recovers_correctly(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        lease = queue.claim_next("w1", job_id="job-A")
        assert lease is not None
        clock.advance(120)  # TTL 60s
        assert queue.expire_stale_leases() == ["a-1"]
        lease2 = queue.claim_next("w2", job_id="job-A")
        assert lease2 is not None
        assert lease2.lease_token != lease.lease_token

    def test_job_scoped_claim_after_expiry(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("a-1", job_id="job-A"), not_before=clock.now())
        store.add_step(_ready_step("b-1", job_id="job-B"), not_before=clock.now())
        queue.claim_next("w1", job_id="job-A")
        clock.advance(120)
        # Expired job-A lease is re-claimable job-scoped; job-B untouched.
        assert queue.claim_next("w2", job_id="job-A") is not None
        assert queue.has_active_claim("b-1") is False
