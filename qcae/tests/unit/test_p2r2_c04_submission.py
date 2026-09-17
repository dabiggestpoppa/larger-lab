"""P2-R2-C04 — canonical submission + CLI `job submit`.

Laws under test:

- JobSubmission validates canonically BEFORE persistence (malformed input
  persists nothing — no job, no steps, no events);
- submission flows through the engine's atomic path (C07R3);
- deterministic identity: the same logical submission twice is refused;
- durable across CLI process close;
- CLI is thin: it parses, calls the application service, and reports.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.identity import IdentityKind, LocalIdentity
from qcae.interfaces.cli import __main__ as cli
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime
from qcae.interfaces.submission import JobSubmission
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.workers.base import DeterministicSuccessWorker


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, s):
        self._t += timedelta(seconds=s)


def _submission(**over):
    base = dict(
        job_kind="discovery",
        subject_ref="cap-0001",
        idempotency_key="k-001",
        steps=(
            {"step_id": "s-1", "step_type": "GENERIC", "dependencies": []},
        ),
        submitted_by="id-operator-local",
    )
    base.update(over)
    return JobSubmission(**base)


@pytest.fixture()
def runtime(tmp_path):
    clock = _Clock()
    rt = build_local_runtime(
        tmp_path / "meta.sqlite3",
        workers={"GENERIC": DeterministicSuccessWorker()},
        clock=clock,
    )
    return rt


@pytest.fixture()
def app(runtime):
    return QcaeApp(runtime, clock=_Clock())


class TestSubmissionValidation:
    def test_valid_submission_persists_atomically(self, app, runtime):
        job = app.job_submit(_submission())
        assert job.deterministic_id.startswith("job-discovery-")
        assert runtime.store.get_job(job.job_id) is not None
        steps = runtime.store.list_steps_for_job(job.job_id)
        assert len(steps) == 1
        # Events commit with the submission (atomic path).
        kinds = [
            e.event_type.value for _s, e, _p in runtime.store.events_for_job(job.job_id)
        ]
        assert "JOB_CREATED" in kinds and "JOB_QUEUED" in kinds

    def test_empty_steps_rejected_before_persistence(self, app, runtime):
        with pytest.raises(QcaeValidationError):
            app.job_submit(_submission(steps=()))
        assert runtime.store.list_jobs() == []

    def test_unknown_dependency_rejected(self, app, runtime):
        with pytest.raises(QcaeValidationError, match="unknown step"):
            app.job_submit(_submission(steps=(
                {"step_id": "s-1", "step_type": "GENERIC", "dependencies": ["ghost"]},
            )))
        assert runtime.store.list_jobs() == []

    def test_self_dependency_rejected(self, app, runtime):
        with pytest.raises(QcaeValidationError, match="itself"):
            app.job_submit(_submission(steps=(
                {"step_id": "s-1", "step_type": "GENERIC", "dependencies": ["s-1"]},
            )))

    def test_duplicate_step_ids_rejected(self, app, runtime):
        with pytest.raises(QcaeValidationError, match="duplicate"):
            app.job_submit(_submission(steps=(
                {"step_id": "s-1", "step_type": "GENERIC", "dependencies": []},
                {"step_id": "s-1", "step_type": "GENERIC", "dependencies": []},
            )))

    def test_same_logical_submission_twice_refused(self, app, runtime):
        app.job_submit(_submission())
        with pytest.raises(QcaeValidationError, match="deterministic_id"):
            app.job_submit(_submission())
        # Exactly one durable job remains.
        assert len(runtime.store.list_jobs()) == 1

    def test_cycle_rejected_before_persistence(self, app, runtime):
        with pytest.raises(QcaeValidationError):
            app.job_submit(_submission(steps=(
                {"step_id": "a", "step_type": "GENERIC", "dependencies": ["b"]},
                {"step_id": "b", "step_type": "GENERIC", "dependencies": ["a"]},
            )))
        assert runtime.store.list_jobs() == []

    def test_unknown_submitter_fails_closed(self, app, runtime):
        with pytest.raises(QcaeValidationError, match="unknown identity"):
            app.job_submit(_submission(submitted_by="id-ghost"))
        assert runtime.store.list_jobs() == []


class TestSubmissionRoundTrip:
    def test_envelope_round_trips(self):
        s = _submission()
        rebuilt = JobSubmission.from_dict(s.to_dict())
        assert rebuilt == s
        assert rebuilt.digest() == s.digest()

    def test_submission_runs_to_completion(self, app, runtime):
        job = app.job_submit(_submission())
        runtime.service.mark_running(job.job_id)
        result = app.job_run_step(job.job_id, "id-worker-runtime")
        assert result is not None
        assert result.status.value == "SUCCESS"
        steps = runtime.store.list_steps_for_job(job.job_id)
        assert all(s.status is RuntimeStepStatus.SUCCEEDED for s in steps)


class TestCliSubmit:
    def test_cli_submit_durable(self, runtime, tmp_path):
        db = tmp_path / "cli.sqlite3"
        # Build the DB with a worker through one session (close = process end).
        rt = build_local_runtime(db, workers={"GENERIC": DeterministicSuccessWorker()})
        rt.conn.commit()
        rt.conn.close()

        argv = [
            "--db", str(db), "job", "submit",
            "--kind", "discovery", "--subject", "cap-0001", "--key", "cli-1",
            "--step", "s-1:GENERIC",
        ]
        rc = cli.main(argv)
        assert rc == 0
        # New process: the submitted job is durable.
        rt2 = build_local_runtime(db)
        jobs = rt2.store.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_type == "discovery"
        rt2.conn.close()

    def test_cli_submit_malformed_step_spec(self, tmp_path):
        db = tmp_path / "m.sqlite3"
        argv = [
            "--db", str(db), "job", "submit",
            "--kind", "d", "--subject", "cap-0001", "--key", "k",
            "--step", "bad-spec-without-type",
        ]
        rc = cli.main(argv)
        assert rc == 2

    def test_cli_submit_unknown_identity_rejected(self, runtime, tmp_path):
        db = tmp_path / "u.sqlite3"
        argv = [
            "--db", str(db), "job", "submit",
            "--kind", "d", "--subject", "cap-0001", "--key", "k",
            "--step", "s-1:GENERIC", "--submitted-by", "id-ghost",
        ]
        rc = cli.main(argv)
        assert rc == 2

    def test_cli_submit_duplicate_refused(self, tmp_path):
        db = tmp_path / "dup.sqlite3"
        rt = build_local_runtime(db, workers={"GENERIC": DeterministicSuccessWorker()})
        rt.conn.commit()
        rt.conn.close()
        argv = [
            "--db", str(db), "job", "submit",
            "--kind", "d", "--subject", "cap-0001", "--key", "k",
            "--step", "s-1:GENERIC",
        ]
        assert cli.main(argv) == 0
        assert cli.main(argv) == 2  # deterministic identity: refused
