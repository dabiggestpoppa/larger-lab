"""P2-C02 — durable runtime store qualification (directive §8, §9)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.orchestration.jobs.runtime import (
    JobEvent,
    JobEventType,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
)


def _job(job_id="job-12345678", status=RuntimeJobStatus.CREATED, **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-0001", "k1"),
        job_type="DISCOVERY",
        subject_ref="cap-0001",
        status=status,
        created_by="operator",
        created_at="2026-09-13T00:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id="s-00000001", job_id="job-12345678", **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="FETCH",
        created_at="2026-09-13T00:00:00Z",
    )
    base.update(over)
    return RuntimeStep(**base)


def _store():
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    return SqliteRuntimeStore(conn), conn


class TestJobPersistence:
    def test_add_get_round_trip(self):
        store, _ = _store()
        store.add_job(_job())
        assert store.get_job("job-12345678") == _job()

    def test_duplicate_job_id_rejected(self):
        store, _ = _store()
        store.add_job(_job())
        with pytest.raises(QcaeValidationError, match="already exists"):
            store.add_job(_job())

    def test_duplicate_deterministic_id_detectable(self):
        store, _ = _store()
        j = _job()
        store.add_job(j)
        # Same logical work, different physical id -> deterministic id collides.
        j2 = _job(job_id="job-99999999")
        assert store.deterministic_id_exists(j2.deterministic_id)

    def test_update_job_persists(self):
        store, _ = _store()
        store.add_job(_job())
        store.update_job(_job(status=RuntimeJobStatus.QUEUED))
        assert store.get_job("job-12345678").status == RuntimeJobStatus.QUEUED

    def test_update_missing_job_rejected(self):
        store, _ = _store()
        with pytest.raises(QcaeValidationError, match="not found"):
            store.update_job(_job())

    def test_survives_restart(self):
        # File-backed restart proves real durability; connections are closed
        # before the temp dir is removed (Windows locks open WAL files).
        import tempfile
        from pathlib import Path

        job = _job(status=RuntimeJobStatus.RUNNING)
        step = _step(attempt=1)
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "meta.sqlite3"
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            s1 = SqliteRuntimeStore(c1)
            s1.add_job(job)
            s1.add_step(step)
            c1.commit()
            c1.close()

            c2 = open_metadata_db(db)
            c2.executescript(RUNTIME_DDL)
            s2 = SqliteRuntimeStore(c2)
            assert s2.get_job("job-12345678").status == RuntimeJobStatus.RUNNING
            assert s2.get_step("s-00000001").attempt == 1
            c2.close()

    def test_tampered_job_payload_detected(self):
        store, conn = _store()
        store.add_job(_job())
        original = conn.execute(
            "SELECT payload_json FROM runtime_job WHERE job_id = ?",
            ("job-12345678",),
        ).fetchone()[0]
        tampered = original.replace("operator", "attacker")
        assert tampered != original
        conn.execute(
            "UPDATE runtime_job SET payload_json = ? WHERE job_id = ?",
            (tampered, "job-12345678"),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            store.get_job("job-12345678")

    def test_list_by_status(self):
        store, _ = _store()
        store.add_job(_job(job_id="job-aaaaaaaa", status=RuntimeJobStatus.QUEUED))
        store.add_job(_job(job_id="job-bbbbbbbb", status=RuntimeJobStatus.CREATED))
        queued = store.list_jobs(status=RuntimeJobStatus.QUEUED)
        assert [j.job_id for j in queued] == ["job-aaaaaaaa"]


class TestStepPersistence:
    def test_step_round_trip_and_list(self):
        store, _ = _store()
        store.add_step(_step())
        store.add_step(_step("s-00000002"))
        steps = store.list_steps_for_job("job-12345678")
        assert [s.step_id for s in steps] == ["s-00000001", "s-00000002"]

    def test_duplicate_step_rejected(self):
        store, _ = _store()
        store.add_step(_step())
        with pytest.raises(QcaeValidationError, match="already exists"):
            store.add_step(_step())

    def test_lease_columns_round_trip(self):
        store, _ = _store()
        store.add_step(_step())
        step = store.get_step("s-00000001")
        from dataclasses import replace as dc_replace

        from qcae.orchestration.jobs.runtime import LeaseInfo

        leased = dc_replace(
            step,
            lease=LeaseInfo(
                lease_owner="w1",
                lease_token="tok-1",
                leased_at="2026-09-13T00:00:01Z",
                lease_expires_at="2026-09-13T00:05:01Z",
            ),
        )
        store.update_step(
            leased,
            lease_owner="w1",
            lease_token="tok-1",
            lease_expires_at="2026-09-13T00:05:01Z",
        )
        cols = store.read_lease_columns("s-00000001")
        assert cols["lease_owner"] == "w1"
        assert cols["lease_token"] == "tok-1"

    def test_tampered_step_detected(self):
        store, conn = _store()
        store.add_step(_step())
        original = conn.execute(
            "SELECT payload_json FROM runtime_step WHERE step_id = ?",
            ("s-00000001",),
        ).fetchone()[0]
        tampered = original.replace("FETCH", "MUTATED")
        assert tampered != original
        conn.execute(
            "UPDATE runtime_step SET payload_json = ? WHERE step_id = ?",
            (tampered, "s-00000001"),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            store.get_step("s-00000001")


class TestEventLog:
    def _event(self, n=1, event_type=JobEventType.JOB_CREATED, job_id="job-12345678"):
        return JobEvent(
            event_seq=0,
            event_id=f"ev-{n:08d}",
            event_type=event_type,
            job_id=job_id,
            occurred_at="2026-09-13T00:00:00Z",
        )

    def test_append_and_read_preserves_order(self):
        store, _ = _store()
        store.append_event(self._event(1))
        store.append_event(self._event(2, JobEventType.JOB_QUEUED))
        rows = store.events_for_job("job-12345678")
        assert [r[1].event_type for r in rows] == [
            JobEventType.JOB_CREATED,
            JobEventType.JOB_QUEUED,
        ]
        assert [r[0] for r in rows] == [1, 2]

    def test_event_digest_recorded(self):
        store, _ = _store()
        seq = store.append_event(self._event(3))
        assert seq == 1
        digest = store.event_digest_of("ev-00000003")
        assert digest and len(digest) == 64

    def test_event_history_not_rewritable_by_update_job(self):
        """Mutable job status never rewrites the event stream (§8/§9)."""
        store, _ = _store()
        store.add_job(_job())
        store.append_event(self._event(1))
        store.update_job(_job(status=RuntimeJobStatus.FAILED))
        rows = store.events_for_job("job-12345678")
        assert rows[0][1].event_type == JobEventType.JOB_CREATED

    def test_events_from_other_jobs_isolated(self):
        store, _ = _store()
        store.append_event(self._event(1))
        store.append_event(self._event(2, job_id="job-88888888"))
        assert len(store.events_for_job("job-12345678")) == 1
        assert len(store.events_for_job("job-88888888")) == 1


class TestCheckpoints:
    def test_put_get_round_trip(self):
        store, _ = _store()
        store.put_checkpoint(
            "cp-1", "job-12345678", "s-00000001",
            {"completed": ["s-00000001"], "evidence": ["abc123"]},
            "2026-09-13T00:00:00Z",
        )
        assert store.get_checkpoint("cp-1") == {
            "completed": ["s-00000001"],
            "evidence": ["abc123"],
        }

    def test_tampered_checkpoint_detected(self):
        store, conn = _store()
        store.put_checkpoint("cp-1", "j", "s", {"k": 1}, "2026-09-13T00:00:00Z")
        conn.execute(
            "UPDATE runtime_checkpoint SET payload_json = ? WHERE checkpoint_id = ?",
            ('{"k": 2}', "cp-1"),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            store.get_checkpoint("cp-1")

    def test_latest_checkpoint_by_created_at(self):
        store, _ = _store()
        store.put_checkpoint("cp-old", "job-12345678", "", {"n": 1},
                             "2026-09-13T00:00:00Z")
        store.put_checkpoint("cp-new", "job-12345678", "", {"n": 2},
                             "2026-09-13T00:01:00Z")
        assert store.latest_checkpoint_for_job("job-12345678") == {"n": 2}


class TestIdempotency:
    def test_first_write_wins(self):
        store, _ = _store()
        assert store.record_idempotent_completion(
            "key-1", "job-12345678", "s-00000001", "2026-09-13T00:00:00Z"
        )
        assert not store.record_idempotent_completion(
            "key-1", "job-12345678", "s-00000001", "2026-09-13T00:00:01Z"
        )
        assert store.idempotency_key_used("key-1")

    def test_distinct_keys_independent(self):
        store, _ = _store()
        assert store.record_idempotent_completion("k1", "j", "s", "t")
        assert not store.idempotency_key_used("k2")
