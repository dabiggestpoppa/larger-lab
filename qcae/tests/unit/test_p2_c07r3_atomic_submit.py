"""P2-C07R3 — atomic job submission (repair directive §2.3).

Law under test: job identity + every step + the initial events + queue
metadata commit in ONE transaction — any injected failure rolls back to no
partial job, no orphan steps, no partial event history. The word "atomic"
is proven, not claimed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
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


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _job(job_id="job-12345678", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-0001", "k1"),
        job_type="DISCOVERY",
        subject_ref="cap-0001",
        created_by="operator",
        created_at="2026-09-13T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, deps=(), **over):
    base = dict(
        step_id=step_id,
        job_id="job-12345678",
        step_type="GENERIC",
        dependencies=tuple(deps),
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"job-12345678:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate())
    return store, queue, engine, clock, conn


class TestAtomicSubmission:
    def test_happy_path_writes_everything(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(_job(), [_step("s-1"), _step("s-2", deps=("s-1",))])
        assert store.get_job("job-12345678") is not None
        assert store.get_step("s-1") is not None
        assert store.get_step("s-2") is not None
        kinds = [e[1].event_type.value for e in store.events_for_job("job-12345678")]
        assert kinds == ["JOB_CREATED", "JOB_QUEUED"]

    def test_failure_after_job_insert_rolls_back_everything(self, env, monkeypatch):
        store, queue, engine, clock, conn = env
        real_add_step = store.add_step
        calls = {"n": 0}

        def exploding_add_step(step, **kw):
            calls["n"] += 1
            raise RuntimeError("injected failure after job insert")

        monkeypatch.setattr(store, "add_step", exploding_add_step)
        with pytest.raises(RuntimeError, match="injected failure"):
            engine.submit(_job(), [_step("s-1"), _step("s-2")])
        # No partial job, no orphan steps, no partial event history.
        assert store.get_job("job-12345678") is None
        assert store.list_steps_for_job("job-12345678") == []
        assert store.events_for_job("job-12345678") == []
        assert not store.deterministic_id_exists(_job().deterministic_id)

    def test_failure_on_nth_step_insert_rolls_back_everything(self, env, monkeypatch):
        store, queue, engine, clock, conn = env
        real_add_step = store.add_step
        calls = {"n": 0}

        def exploding_add_step(step, **kw):
            calls["n"] += 1
            if calls["n"] == 2:  # second step insert fails
                raise RuntimeError("injected failure on Nth step")
            return real_add_step(step, **kw)

        monkeypatch.setattr(store, "add_step", exploding_add_step)
        with pytest.raises(RuntimeError, match="injected failure on Nth"):
            engine.submit(_job(), [_step("s-1"), _step("s-2"), _step("s-3")])
        assert store.get_job("job-12345678") is None
        assert store.get_step("s-1") is None  # first step did NOT survive
        assert store.events_for_job("job-12345678") == []

    def test_failure_before_final_event_rolls_back_everything(self, env, monkeypatch):
        store, queue, engine, clock, conn = env
        real_append = store.append_event
        calls = {"n": 0}

        def exploding_append(event, payload_json=""):
            calls["n"] += 1
            if calls["n"] == 2:  # the JOB_QUEUED event fails
                raise RuntimeError("injected failure before final event")
            return real_append(event, payload_json=payload_json)

        monkeypatch.setattr(store, "append_event", exploding_append)
        with pytest.raises(RuntimeError, match="injected failure before final"):
            engine.submit(_job(), [_step("s-1")])
        assert store.get_job("job-12345678") is None
        assert store.get_step("s-1") is None
        assert store.events_for_job("job-12345678") == []

    def test_duplicate_deterministic_id_refused_no_writes(self, env):
        store, queue, engine, clock, conn = env
        engine.submit(_job(), [_step("s-1")])
        before_events = len(store.events_for_job("job-12345678"))
        with pytest.raises(QcaeValidationError, match="deterministic_id"):
            engine.submit(_job(), [_step("s-1")])
        assert len(store.events_for_job("job-12345678")) == before_events

    def test_malformed_step_rejects_whole_submission(self, env):
        store, queue, engine, clock, conn = env
        with pytest.raises(Exception):
            engine.submit(_job(), [_step("s-1"), _step("s-cycle", deps=("s-cycle",))])
        assert store.get_job("job-12345678") is None

    def test_store_transaction_helper_rolls_back(self, env):
        """The transaction boundary itself is real (BEGIN/COMMIT/ROLLBACK)."""
        store, queue, engine, clock, conn = env
        with pytest.raises(RuntimeError):
            with store.transaction() as tx:
                tx.add_job(_job())
                raise RuntimeError("boom inside transaction")
        assert store.get_job("job-12345678") is None
        # And the connection is usable afterward (rollback left no open txn).
        store.add_job(_job(job_id="job-87654321"))
        assert store.get_job("job-87654321") is not None
