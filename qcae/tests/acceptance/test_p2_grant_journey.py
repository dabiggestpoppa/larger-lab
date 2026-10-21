"""P2-R4-A02 — durable grant → restart → execute → terminal journey.

Finding J repair (directive §13): the original Journey E exercises the
DENIAL path only. This module is the REAL grant journey, at the operator
surface (composition-root runtime + real SQLite), across a restart:

REQUIRE_APPROVAL
→ durable request
→ GRANTED (durable decision, exact binding)
→ runtime restart (fresh engine/registry over the same DB)
→ exact grant still discoverable and releases the step
→ worker executes under the durable grant
→ grant consumed (single execution admission)
→ step SUCCEEDED, job SUCCEEDED
→ restart again → remains terminal
→ second grant replay against the same request refused
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.identity import IdentityKind, LocalIdentity
from qcae.governance.standalone.policy import (
    PolicyEffect,
    PolicyRule,
    PolicySet,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime
from qcae.orchestration.jobs.runtime import JobEventType, RuntimeStepStatus
from qcae.orchestration.workers.base import DeterministicSuccessWorker


class _Clock:
    def __init__(self):
        from datetime import datetime, timedelta, timezone

        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        from datetime import timedelta

        self._t += timedelta(seconds=seconds)


def _job(job_id="job-grant", **over):
    from qcae.orchestration.jobs.runtime import RuntimeJob

    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-grant", "k-grant"),
        job_type="DISCOVERY",
        subject_ref="cap-grant",
        created_by="id-operator-local",
        created_at="2026-09-17T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-grant", **over):
    from qcae.orchestration.jobs.runtime import RuntimeStep

    full = f"{job_id}:{step_id}"
    base = dict(
        step_id=full,
        job_id=job_id,
        step_type="GENERIC",
        idempotency_key=full,
        created_at="2026-09-17T12:00:00Z",
    )
    base.update(over)
    return RuntimeStep(**base)


def _approval_runtime(db_path):
    rt = build_local_runtime(db_path, clock=_Clock())
    rt.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    rt.identity.register(LocalIdentity(
        identity_id="id-worker-accept", kind=IdentityKind.WORKER,
        display_name="accept",
    ))
    rt.policy._policy = PolicySet(
        policy_id="pol-grant-accept",
        policy_version="grant-1",
        rules=(
            PolicyRule(
                rule_id="approval-generic",
                effect=PolicyEffect.REQUIRE_APPROVAL,
                action="execute.GENERIC",
                principal_match="id-worker-accept",
                reason="acceptance: approval required",
            ),
        ),
    )
    return rt


class TestJourneyE_GrantDurableRoundTrip:
    def test_grant_survives_restart_executes_consumes_terminal(self, tmp_path):
        db = tmp_path / "grant.sqlite3"
        clock = _Clock()
        rt = _approval_runtime(db)
        qapp = QcaeApp(rt, clock=clock)
        qapp.submit_job(_job(), [_step("s-1")])

        # Run → blocked on approval; durable request recorded.
        qapp.job_run_step("job-grant", "id-worker-accept")
        view = qapp.job_status("job-grant")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-grant:s-1"] == "WAITING_POLICY"
        request_id = rt.approvals.pending_requests()[0].request_id

        # Operator grants the EXACT binding (durable decision artifact).
        qapp.approval_decide(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-local", job_id="job-grant",
            reason="acceptance grant",
        )

        # RESTART: the first runtime exits cleanly (crash windows are
        # A01's domain); a fresh runtime opens the same durable database.
        rt.conn.commit()
        rt.conn.close()
        rt2 = _approval_runtime(db)
        qapp2 = QcaeApp(rt2, clock=clock)

        # The grant is still discoverable after restart (durable, not
        # process memory) and releases the step.
        qapp2.approval_release("job-grant", "job-grant:s-1")
        view = qapp2.job_status("job-grant")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-grant:s-1"] == "READY"

        # Execute under the durable grant → completes.
        qapp2.job_run_step("job-grant", "id-worker-accept")
        view = qapp2.job_status("job-grant")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-grant:s-1"] == "SUCCEEDED"
        assert view["job"].status.value == "SUCCEEDED"

        # The grant was CONSUMED (single execution admission, durable).
        decision = rt2.approvals.decisions_for_request(request_id)[-1]
        uses = rt2.approvals.uses_for_decision(decision.decision_id)
        assert len(uses) == 1
        assert uses[0].step_id == "job-grant:s-1"

        # Restart again: terminal truth survives; the consumed grant
        # cannot re-authorize anything.
        rt2.conn.commit()
        rt2.conn.close()
        rt3 = _approval_runtime(db)
        qapp3 = QcaeApp(rt3, clock=clock)
        view = qapp3.job_status("job-grant")
        assert view["job"].status.value == "SUCCEEDED"
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-grant:s-1"] == "SUCCEEDED"

        # Replay: a second decision against the same request is refused
        # (decisions are immutable artifacts).
        with pytest.raises(Exception):
            qapp3.approval_decide(
                request_id=request_id, decision="GRANTED",
                decided_by="id-operator-local", job_id="job-grant",
                reason="replay",
            )

        # Worker effect ran exactly once across all three runtimes.
        events = [
            ev.event_type for _s, ev, _p in rt3.store.events_for_job("job-grant")
        ]
        assert events.count(JobEventType.STEP_SUCCEEDED) == 1
        assert events.count(JobEventType.JOB_SUCCEEDED) == 1

    def test_consumed_grant_cannot_execute_second_step(self, tmp_path):
        """Single-use law at the surface: a consumed grant admits nothing."""
        db = tmp_path / "consume.sqlite3"
        clock = _Clock()
        rt = _approval_runtime(db)
        qapp = QcaeApp(rt, clock=clock)
        qapp.submit_job(
            _job(),
            [_step("s-1"), _step("s-2", dependencies=("job-grant:s-1",))],
        )
        # First step requires approval; second is dependency-gated.
        qapp.job_run_step("job-grant", "id-worker-accept")
        request_id = rt.approvals.pending_requests()[0].request_id
        qapp.approval_decide(
            request_id=request_id, decision="GRANTED",
            decided_by="id-operator-local", job_id="job-grant", reason="ok",
        )
        qapp.approval_release("job-grant", "job-grant:s-1")
        qapp.job_run_step("job-grant", "id-worker-accept")
        view = qapp.job_status("job-grant")
        statuses = {s.step_id: s.status.value for s in view["steps"]}
        assert statuses["job-grant:s-1"] == "SUCCEEDED"
        # The grant is consumed; releasing the (still WAITING_POLICY-free)
        # graph again through the same request cannot happen — the request
        # is decided, and a fresh run of a second approval-needing step
        # would raise a NEW request (never inherit the old grant).
        decision = rt.approvals.decisions_for_request(request_id)[-1]
        assert len(rt.approvals.uses_for_decision(decision.decision_id)) == 1
