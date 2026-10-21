"""P2-C03 — queue and lease qualification (directive §21-22)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.persistence.sqlite_runtime_store import RUNTIME_DDL, SqliteRuntimeStore
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


def _ready_step(step_id, job_id="job-12345678", status=RuntimeStepStatus.READY, **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="GENERIC",
        status=status,
        created_at="2026-09-13T12:00:00Z",
    )
    base.update(over)
    return RuntimeStep(**base)


class TestClaim:
    def test_claim_returns_lease(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("worker-a")
        assert lease is not None
        assert lease.step_id == "s-1"
        assert lease.lease_owner == "worker-a"
        assert lease.lease_expires_at > clock.now()

    def test_empty_queue_returns_none(self, env):
        _, queue, _, _ = env
        assert queue.claim_next("worker-a") is None

    def test_two_claimers_cannot_both_own(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        first = queue.claim_next("worker-a")
        second = queue.claim_next("worker-b")
        assert first is not None
        assert second is None
        assert queue.lease_owner_of("s-1") == "worker-a"

    def test_claim_skips_other_step_types(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1", step_type="PROVE"), not_before=clock.now())
        assert queue.claim_next("w", step_types=["FETCH"]) is None
        assert queue.claim_next("w", step_types=["PROVE"]) is not None

    def test_priority_not_bypassing_policy_state(self, env):
        """Queue only surfaces READY steps — WAITING_POLICY never claimed."""
        store, queue, clock, _ = env
        store.add_step(
            _ready_step("s-blocked", status=RuntimeStepStatus.WAITING_POLICY),
            not_before=clock.now(),
        )
        assert queue.claim_next("w") is None


class TestNotBefore:
    def test_future_step_not_claimed(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before="2026-09-13T13:00:00Z")
        assert queue.claim_next("w") is None

    def test_not_before_honored_then_claimable(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        clock.advance(3600)
        lease = queue.claim_next("w")
        assert lease is not None and lease.step_id == "s-1"


class TestAcknowledge:
    def test_owner_may_ack(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        queue.acknowledge(lease.step_id, lease.lease_token)

    def test_wrong_token_cannot_ack(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        with pytest.raises(QcaeValidationError, match="not the owner"):
            queue.acknowledge(lease.step_id, "forged-token")

    def test_double_ack_rejected(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        queue.acknowledge(lease.step_id, lease.lease_token)
        with pytest.raises(QcaeValidationError, match="already acknowledged"):
            queue.acknowledge(lease.step_id, lease.lease_token)

    def test_release_requires_owner(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        with pytest.raises(QcaeValidationError, match="not the owner"):
            queue.release(lease.step_id, "wrong", back_to=RuntimeStepStatus.READY)
        queue.release(lease.step_id, lease.lease_token, back_to=RuntimeStepStatus.READY)
        assert queue.has_active_claim("s-1") is False


class TestExpiry:
    def test_expired_lease_is_recoverable(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        clock.advance(120)  # TTL 60s
        recovered = queue.expire_stale_leases()
        assert recovered == ["s-1"]
        # Another worker can now claim.
        lease2 = queue.claim_next("w2")
        assert lease2 is not None and lease2.step_id == "s-1"
        assert lease2.lease_token != lease.lease_token

    def test_active_lease_not_recovered(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        queue.claim_next("w1")
        clock.advance(10)
        assert queue.expire_stale_leases() == []

    def test_expired_lease_blocks_old_owner_from_ack(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        lease = queue.claim_next("w1")
        clock.advance(120)
        queue.expire_stale_leases()
        with pytest.raises(QcaeValidationError, match="no active claim"):
            queue.acknowledge(lease.step_id, lease.lease_token)

    def test_claim_after_expiry_replaces_row_atomically(self, env):
        store, queue, clock, _ = env
        store.add_step(_ready_step("s-1"), not_before=clock.now())
        queue.claim_next("w1")
        clock.advance(120)
        a = queue.claim_next("w2")
        b = queue.claim_next("w3")
        assert (a is None) != (b is None)  # exactly one new owner
