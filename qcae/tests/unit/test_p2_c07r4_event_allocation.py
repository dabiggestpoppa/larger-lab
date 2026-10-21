"""P2-C07R4 — event identity / store abstraction (repair directive §2.4).

Law under test: identity and sequence allocation belong to the runtime
store. The orchestrator knows no sqlite connection, no table names, no
row-count sequencing; event ids are collision-safe across restarts and
concurrent appends, and event order is durable.
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
from qcae.orchestration.jobs.runtime import (
    JobEvent,
    JobEventType,
    RuntimeJob,
    RuntimeStep,
)
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker


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


class TestStoreOwnedIdentity:
    def test_append_event_assigns_seq_and_id(self, env):
        store, _, _, clock, _ = env
        seq1 = store.append_event(JobEvent(
            event_seq=0, event_id="", event_type=JobEventType.JOB_CREATED,
            job_id="job-12345678", occurred_at=clock(),
        ))
        seq2 = store.append_event(JobEvent(
            event_seq=0, event_id="", event_type=JobEventType.JOB_QUEUED,
            job_id="job-12345678", occurred_at=clock(),
        ))
        assert seq2 == seq1 + 1
        events = store.events_for_job("job-12345678")
        ids = [e[1].event_id for e in events]
        assert all(ids), "store must assign event ids"
        assert len(set(ids)) == 2, "event ids must be collision-free"

    def test_caller_supplied_seq_refused(self, env):
        store, _, _, clock, _ = env
        with pytest.raises(QcaeValidationError, match="store-assigned"):
            store.append_event(JobEvent(
                event_seq=7, event_id="ev-x", event_type=JobEventType.JOB_CREATED,
                job_id="job-12345678", occurred_at=clock(),
            ))

    def test_duplicate_explicit_event_id_rejected(self, env):
        store, _, _, clock, _ = env
        store.append_event(JobEvent(
            event_seq=0, event_id="ev-explicit-1",
            event_type=JobEventType.JOB_CREATED, job_id="job-12345678",
            occurred_at=clock(),
        ))
        with pytest.raises(QcaeValidationError, match="duplicate event_id"):
            store.append_event(JobEvent(
                event_seq=0, event_id="ev-explicit-1",
                event_type=JobEventType.JOB_QUEUED, job_id="job-12345678",
                occurred_at=clock(),
            ))

    def test_ids_unique_across_restart(self, env):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ev.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            store1 = SqliteRuntimeStore(c1)
            store1.append_event(JobEvent(
                event_seq=0, event_id="", event_type=JobEventType.JOB_CREATED,
                job_id="job-12345678", occurred_at=clock(),
            ))
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            store2 = SqliteRuntimeStore(c2)
            seq = store2.append_event(JobEvent(
                event_seq=0, event_id="", event_type=JobEventType.JOB_QUEUED,
                job_id="job-12345678", occurred_at=clock(),
            ))
            assert seq == 2  # durable monotonic sequence, not per-instance
            ids = [e[1].event_id for e in store2.events_for_job("job-12345678")]
            assert len(set(ids)) == 2
            c2.close()

    def test_engine_holds_no_event_or_checkpoint_counters(self, env):
        engine = env[2]
        for attr in dir(engine):
            if "event_counter" in attr or "checkpoint_seq" in attr:
                pytest.fail(f"orchestrator still owns identity state: {attr}")
        assert not hasattr(engine, "_next_event_id")

    def test_checkpoint_ids_unique_across_restart(self, env):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "cp.sqlite3"
            clock = _Clock()
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            engine1 = OrchestratorEngine(store1, queue1, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            engine1._workers["GENERIC"] = DeterministicSuccessWorker()
            engine1.submit(_job(), [_step("s-1")])
            engine1.mark_running("job-12345678")
            engine1.ready_steps("job-12345678")
            lease = engine1.lease_next("job-12345678", "w1")
            engine1.execute_step(lease)
            cp1 = engine1.write_checkpoint("job-12345678")
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            store2 = SqliteRuntimeStore(c2)
            queue2 = SqliteStepQueue(c2, store2, now_fn=clock, lease_ttl_seconds=60)
            engine2 = OrchestratorEngine(store2, queue2, clock=clock, authority_gate=PermissiveStepAuthorityGate())
            cp2 = engine2.write_checkpoint("job-12345678")
            assert cp1 != cp2
            assert store2.get_checkpoint(cp1) is not None
            assert store2.get_checkpoint(cp2) is not None
            c2.close()


class TestEventDurability:
    def test_multi_job_event_order_durable(self, env):
        store, queue, engine, clock, _ = env
        engine.submit(_job(), [_step("s-1")])
        from dataclasses import replace as dc_replace

        step_b = dc_replace(
            _step("b-s-1"),
            job_id="job-87654321",
            idempotency_key="job-87654321:b-s-1",
        )
        engine.submit(
            _job(job_id="job-87654321",
                 deterministic_id=deterministic_job_id("discovery", "cap-0001", "k2")),
            [step_b],
        )
        all_events = [
            (r[0], r[1].job_id) for r in store.events_for_job("job-12345678")
        ]
        other = [
            (r[0], r[1].job_id) for r in store.events_for_job("job-87654321")
        ]
        assert all_events and other
        # Global order is durable and non-overlapping by seq.
        seqs_a = {s for s, _ in all_events}
        seqs_b = {s for s, _ in other}
        assert seqs_a.isdisjoint(seqs_b)

    def test_engine_flow_assigns_no_duplicate_ids(self, env):
        store, queue, engine, clock, _ = env
        engine._workers["GENERIC"] = DeterministicSuccessWorker()
        engine.submit(_job(), [_step("s-1")])
        engine.mark_running("job-12345678")
        engine.ready_steps("job-12345678")
        lease = engine.lease_next("job-12345678", "w1")
        engine.execute_step(lease)
        events = store.events_for_job("job-12345678")
        ids = [e[1].event_id for e in events]
        assert len(ids) == len(set(ids))
        seqs = [e[0] for e in events]
        assert seqs == sorted(seqs)  # durable order
