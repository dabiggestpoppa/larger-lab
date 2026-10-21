"""P2-C11 gap closure — CLI/application coverage required by the repair
directive §6: events, recover, approval decide, machine-readable output,
malformed input handling, and governance-bypass prevention."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalRequest
from qcae.interfaces.cli import __main__ as cli
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep
from qcae.orchestration.workers.base import DeterministicSuccessWorker


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
        job_type="D", subject_ref="cap-1", created_by="id-operator-1",
        created_at="2026-09-13T12:00:00Z",
    )


def _step(step_id, job_id="job-12345678", step_type="GENERIC", deps=()):
    full_id = f"{job_id}:{step_id}"
    return RuntimeStep(
        step_id=full_id, job_id=job_id, step_type=step_type,
        dependencies=tuple(f"{job_id}:{d}" for d in deps),
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )


@pytest.fixture()
def runtime(tmp_path):
    clock = _Clock()
    rt = build_local_runtime(
        tmp_path / "meta.sqlite3",
        workers={"GENERIC": DeterministicSuccessWorker()},
        clock=clock,
    )
    from qcae.governance.standalone.identity import IdentityKind, LocalIdentity

    for iid, kind in (("id-operator-1", IdentityKind.OPERATOR),):
        rt.identity.register(LocalIdentity(identity_id=iid, kind=kind))
    return rt


@pytest.fixture()
def app(runtime):
    return QcaeApp(runtime)


class TestJobEventsCommand:
    def test_events_machine_readable(self, runtime, app, tmp_path, capsys):
        app.submit_job(_job(), [_step("s-1")])
        out = tmp_path / "meta.sqlite3"
        rc = cli.main(["--db", str(out), "job", "events", "job-12345678"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert isinstance(payload, list)
        kinds = [e["type"] for e in payload]
        assert "JOB_CREATED" in kinds and "JOB_QUEUED" in kinds
        assert all("event_id" in e and e["event_id"] for e in payload)

    def test_events_unknown_job_exit_code(self, runtime, app, tmp_path, capsys):
        rc = cli.main(["--db", str(tmp_path / "meta.sqlite3"),
                       "job", "events", "job-nope"])
        assert rc == 2


class TestRecoverCommand:
    def test_recover_all_leases(self, runtime, app, tmp_path, capsys):
        rc = cli.main(["--db", str(tmp_path / "meta.sqlite3"), "recover"])
        assert rc == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_recover_resumes_job(self, runtime, app, tmp_path, capsys):
        app.submit_job(_job(), [_step("s-1")])
        rc = cli.main(["--db", str(tmp_path / "meta.sqlite3"),
                       "recover", "job-12345678"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["job_id"] == "job-12345678"


class TestApprovalDecide:
    def _request(self, job_id="job-12345678"):
        return ApprovalRequest(
            request_id="req-00000001", principal="id-worker-1",
            action="may_execute_in_sandbox", resource="sbx-1", scope="scope-A",
            budget_ref="bud-1", justification="needed for proof",
            created_at="2026-09-13T12:00:00Z",
        )

    def test_grant_and_deny_flows(self, runtime, app, tmp_path, capsys):
        app.submit_job(_job(), [_step("s-1")])
        runtime.approvals.add_request(self._request())
        runtime.conn.commit()  # the CLI opens its own connection
        rc = cli.main([
            "--db", str(tmp_path / "meta.sqlite3"),
            "approval", "decide", "req-00000001", "--decision", "GRANTED",
            "--decided-by", "id-operator-local", "--job-id", "job-12345678",
            "--reason", "operator approved",
        ])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["state"] == "GRANTED"
        # The decision is durable and exactly bound.
        grant = runtime.approvals.effective_grant(
            "req-00000001", now="2026-09-13T12:05:00Z"
        )
        assert grant is not None
        assert grant.bound_action == "may_execute_in_sandbox"
        # A later denial of the same request cannot overwrite the grant.
        rc2 = cli.main([
            "--db", str(tmp_path / "meta.sqlite3"),
            "approval", "decide", "req-00000001", "--decision", "DENIED",
            "--decided-by", "id-operator-local",
        ])
        assert rc2 == 2
        still = runtime.approvals.effective_grant(
            "req-00000001", now="2026-09-13T12:06:00Z"
        )
        assert still is not None

    def test_unknown_request_rejected(self, runtime, app, tmp_path, capsys):
        rc = cli.main([
            "--db", str(tmp_path / "meta.sqlite3"),
            "approval", "decide", "req-404", "--decision", "GRANTED",
            "--decided-by", "id-operator-1",
        ])
        assert rc == 2

    def test_unknown_deciding_identity_rejected(self, runtime, app, tmp_path, capsys):
        runtime.approvals.add_request(self._request())
        runtime.conn.commit()  # the CLI opens its own connection
        rc = cli.main([
            "--db", str(tmp_path / "meta.sqlite3"),
            "approval", "decide", "req-00000001", "--decision", "GRANTED",
            "--decided-by", "id-nobody",
        ])
        assert rc == 2


class TestServiceGuards:
    def test_decide_unknown_job_event_target_rejected(self, runtime, app):
        runtime.approvals.add_request(self._request() if hasattr(self, "_request") else ApprovalRequest(
            request_id="req-00000002", principal="id-worker-1",
            action="a", resource="r", scope="s", budget_ref="b",
            justification="j", created_at="2026-09-13T12:00:00Z",
        ))
        from qcae.core.errors import QcaeValidationError

        with pytest.raises(QcaeValidationError, match="unknown job"):
            app.approval_decide(
                request_id="req-00000002", decision="GRANTED",
                decided_by="id-operator-1", job_id="job-nope",
            )
