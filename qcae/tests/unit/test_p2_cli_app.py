"""P2-C11 — composition factory + CLI qualification (directive §32, Book V 13.7)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.jobs import deterministic_job_id
from qcae.interfaces.cli import __main__ as cli
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep
from qcae.orchestration.workers.base import (
    ApprovalRequiredWorker,
    DeterministicSuccessWorker,
)


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
        workers={"GENERIC": DeterministicSuccessWorker(),
                 "APPROVAL": ApprovalRequiredWorker()},
        clock=clock,
    )
    from qcae.governance.standalone.identity import IdentityKind, LocalIdentity

    rt.identity.register(
        LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR)
    )
    return rt


@pytest.fixture()
def app(runtime):
    return QcaeApp(runtime)


class TestFactory:
    def test_all_components_wired(self, runtime):
        assert runtime.store is not None
        assert runtime.queue is not None
        assert runtime.engine is not None
        assert runtime.service is not None
        assert runtime.authority is not None
        assert runtime.approvals is not None
        assert runtime.identity is not None
        assert runtime.policy is not None

    def test_default_policy_versioned_fail_closed(self, runtime):
        from qcae.governance.standalone.policy import PolicyDecisionType, PolicyRequest

        d = runtime.policy.evaluate(
            PolicyRequest(principal="id-worker-1", action="may_do_anything"),
            decision_id="d1", created_at="t",
        )
        assert d.decision is PolicyDecisionType.DENY

    def test_survives_reopen(self, runtime, tmp_path):
        runtime.engine.submit(_job(), [_step("s-1")])
        runtime.conn.commit()
        runtime.conn.close()
        rt2 = build_local_runtime(tmp_path / "meta.sqlite3",
                                  workers={"GENERIC": DeterministicSuccessWorker()})
        assert rt2.store.get_job("job-12345678") is not None
        rt2.conn.close()


class TestAppService:
    def test_submit_status_cancel(self, app):
        app.submit_job(_job(), [_step("s-1")])
        view = app.job_status("job-12345678")
        assert view["job"].job_id == "job-12345678"
        cancelled = app.job_cancel("job-12345678", reason="testing")
        assert cancelled.status.value == "CANCELLED"

    def test_run_step_and_complete(self, app):
        # P2-R2-C01: execution runs under a governed principal — the runtime
        # worker identity registered at composition. Unknown principals fail
        # policy evaluation closed (no rule match).
        app.submit_job(_job(), [_step("s-1")])
        app._rt.service.mark_running("job-12345678")
        result = app.job_run_step("job-12345678", "id-worker-runtime")
        assert result is not None
        assert result.status.value == "SUCCESS"

    def test_run_step_unknown_principal_fails_closed(self, app):
        """An unregistered principal fails closed BEFORE the claim (P2-R3-C04):
        no lease, no RUNNING step, no policy round-trip."""
        app.submit_job(_job(), [_step("s-1")])
        with pytest.raises(Exception) as excinfo:
            app.job_run_step("job-12345678", "ghost-worker")
        assert "unknown identity" in str(excinfo.value)
        # Nothing mutated: the step never left its queued-side state.
        view = app.job_status("job-12345678")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-12345678:s-1"] != "RUNNING"

    def test_authority_decision_via_app(self, app):
        from qcae.core.decisions.authority import AuthorityRequest, PolicyAction

        decision = app.authority_decision(AuthorityRequest(
            request_id="req-00000031", action=PolicyAction.MAY_DISCOVER,
            subject_id="cap-1", justification="prior art",
            requested_by="id-worker-1",
        ))
        assert decision.outcome.value == "GRANT"

    def test_identity_via_app(self, app):
        ident = app.runtime_identity()
        assert ident.oce_mode == "OCE_ABSENT"
        assert ident.policy_version == "1.1.0"  # P2-R2-C01 default policy


class TestCLI:
    def _run(self, capsys, *argv):
        rc = cli.main(list(argv))
        out = capsys.readouterr().out
        return rc, out

    def test_identity_command(self, runtime, capsys, tmp_path):
        runtime.conn.close()
        db = str(tmp_path / "meta.sqlite3")
        rc, out = self._run(capsys, "--db", db, "identity")
        assert rc == 0
        payload = json.loads(out)
        assert payload["oce_mode"] == "OCE_ABSENT"

    def test_job_status_command(self, runtime, app, capsys, tmp_path):
        app.submit_job(_job(), [_step("s-1")])
        runtime.conn.commit()
        runtime.conn.close()
        db = str(tmp_path / "meta.sqlite3")
        rc, out = self._run(capsys, "--db", db, "job", "status", "job-12345678")
        assert rc == 0
        payload = json.loads(out)
        assert payload["job"]["job_id"] == "job-12345678"

    def test_job_status_unknown_exit_code(self, runtime, capsys, tmp_path):
        runtime.conn.close()
        db = str(tmp_path / "meta.sqlite3")
        rc, _ = self._run(capsys, "--db", db, "job", "status", "job-nope")
        assert rc == 2

    def test_job_list_command(self, runtime, app, capsys, tmp_path):
        app.submit_job(_job(), [_step("s-1")])
        runtime.conn.commit()
        runtime.conn.close()
        db = str(tmp_path / "meta.sqlite3")
        rc, out = self._run(capsys, "--db", db, "job", "list")
        assert rc == 0
        assert "job-12345678" in out
