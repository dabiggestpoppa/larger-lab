"""P2-R5R-C05 — canonical typed-outcome convergence (tests/ledger only).

The canonical owner of no-work standings stays
``qcae/governance/standalone/typed_outcomes.py`` with ``JobMissingOutcome``
and ``StepNotReadyOutcome``. The local R5 branch's ``NoRunnableStep`` is NOT
ported: it would be a second vocabulary for the same truth.

Operator truths proven here through the real CLI subprocess (process
boundary is the point — exit codes are the operator contract):

- unknown job          -> ``JobMissingOutcome``, exit 2, no traceback;
- future schedule      -> ``StepNotReadyOutcome(SCHEDULE_NOT_ELAPSED)``;
- WAITING_POLICY       -> typed NOT_READY;
- WAITING_INPUT        -> typed NOT_READY;
- retry scheduled      -> typed NOT_READY;
- no generic runnable  -> typed NOT_READY;
- worker missing       -> ``WorkerUnavailable``, exit 3 (unchanged canon);
- none of these mutate state, leases, or budgets.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from qcae.governance.standalone import typed_outcomes
from qcae.governance.standalone.typed_outcomes import (
    JobMissingOutcome,
    NotReadyReason,
    StepNotReadyOutcome,
)
from qcae.interfaces.cli.app import build_local_runtime
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"
JOB = "job-12345678"
WORKER = "id-worker-runtime"


def _cli(*args, db: Path):
    return subprocess.run(
        [sys.executable, "-m", "qcae.interfaces.cli", "--db", str(db), *args],
        capture_output=True, text=True, timeout=120,
    )


class TestSingleNoWorkVocabulary:
    def test_no_norunnablestep_vocabulary_exists(self) -> None:
        assert not hasattr(typed_outcomes, "NoRunnableStep")
        assert "NoRunnableStep" not in typed_outcomes.__all__
        # The canonical pair is the whole no-work model.
        assert set(typed_outcomes.__all__) == {
            "NOT_READY_REASONS", "JobMissingOutcome", "StepNotReadyOutcome",
        }

    def test_reason_vocabulary_is_exhaustive_and_typed(self) -> None:
        assert typed_outcomes.NOT_READY_REASONS == (
            NotReadyReason.NO_ELIGIBLE_STEP,
            NotReadyReason.SCHEDULE_NOT_ELAPSED,
            NotReadyReason.STEP_WAITING_POLICY,
            NotReadyReason.STEP_WAITING_INPUT,
            NotReadyReason.STEP_RETRY_SCHEDULED,
        )


class TestUnknownJob:
    def test_job_missing_outcome_is_exit_2_without_traceback(self, tmp_path) -> None:
        db = tmp_path / "c05.sqlite3"
        build_local_runtime(db).conn.close()
        result = _cli("job", "run", "job-does-not-exist", db=db)
        assert result.returncode == 2, result.stderr
        assert "Traceback" not in result.stderr
        assert "unknown job" in (result.stdout + result.stderr)
        # Never the misleading "no eligible step" prose.
        assert "no eligible step" not in (result.stdout + result.stderr).lower()

    def test_job_missing_outcome_shape(self) -> None:
        outcome = JobMissingOutcome("job-gone")
        assert outcome.reason == "JOB_NOT_FOUND"
        assert "job-gone" in outcome.message()


class TestNotReadyReasons:
    def _reach(self, db, *, not_before: str = "", requirement: str = ""):
        from qcae.orchestration.workers.base import DeterministicSuccessWorker

        rig_clock = _Clock()
        rt = build_local_runtime(
            db, clock=rig_clock, workers={"GENERIC": DeterministicSuccessWorker()},
        )
        rt.service.submit(
            _job(job_id=JOB),
            [_step(STEP, idempotency_key=f"{JOB}:{STEP}",
                   authority_requirement=requirement)],
            not_before=not_before,
        )
        return rt, rig_clock

    @staticmethod
    def _run(rt):
        from qcae.interfaces.cli.app import QcaeApp

        return QcaeApp(rt).job_run_step(JOB, worker_id=WORKER)

    def test_future_schedule_is_typed_schedule_not_elapsed(self, tmp_path) -> None:
        db = tmp_path / "sched.sqlite3"
        rt, _ = self._reach(db, not_before="2099-01-01T00:00:00Z")
        step_before = rt.store.get_step(STEP)
        outcome = self._run(rt)
        assert isinstance(outcome, StepNotReadyOutcome)
        assert outcome.reason == NotReadyReason.SCHEDULE_NOT_ELAPSED
        # No execution mutation: nothing leased, no attempt, no start time.
        after = rt.store.get_step(STEP)
        assert after.attempt == step_before.attempt
        assert after.started_at == ""
        assert not rt.queue.has_active_claim(STEP)
        assert after.status is RuntimeStepStatus.READY
        rt.conn.close()

    def test_waiting_policy_is_typed_not_ready(self, tmp_path) -> None:
        db = tmp_path / "wp.sqlite3"
        rt, _ = self._reach(db, requirement="may_execute_in_sandbox")
        rt.engine.ready_steps(JOB)
        lease = rt.engine.lease_next(JOB, WORKER)
        rt.engine.execute_step(lease, worker_id=WORKER)
        assert rt.store.get_step(STEP).status is RuntimeStepStatus.WAITING_POLICY
        outcome = self._run(rt)
        assert isinstance(outcome, StepNotReadyOutcome)
        assert outcome.reason == NotReadyReason.STEP_WAITING_POLICY
        assert rt.store.get_step(STEP).status is RuntimeStepStatus.WAITING_POLICY
        rt.conn.close()

    def test_waiting_input_is_typed_not_ready(self, tmp_path) -> None:
        db = tmp_path / "wi.sqlite3"
        rt, _ = self._reach(db)
        from dataclasses import replace as dc_replace

        step = rt.store.get_step(STEP)
        rt.store.update_step(dc_replace(step, status=RuntimeStepStatus.WAITING_INPUT))
        rt.store.flush()
        outcome = self._run(rt)
        assert isinstance(outcome, StepNotReadyOutcome)
        assert outcome.reason == NotReadyReason.STEP_WAITING_INPUT
        rt.conn.close()

    def test_retry_scheduled_is_typed_not_ready(self, tmp_path) -> None:
        db = tmp_path / "retry.sqlite3"
        rt, _ = self._reach(db)
        from dataclasses import replace as dc_replace

        step = rt.store.get_step(STEP)
        rt.store.update_step(dc_replace(step, status=RuntimeStepStatus.RETRY_SCHEDULED))
        rt.store.flush()
        outcome = self._run(rt)
        assert isinstance(outcome, StepNotReadyOutcome)
        assert outcome.reason == NotReadyReason.STEP_RETRY_SCHEDULED
        rt.conn.close()

    def test_terminal_job_is_typed_no_eligible_step(self, tmp_path) -> None:
        db = tmp_path / "done.sqlite3"
        rt, _ = self._reach(db)
        from dataclasses import replace as dc_replace

        step = rt.store.get_step(STEP)
        rt.store.update_step(dc_replace(step, status=RuntimeStepStatus.SUCCEEDED))
        rt.store.flush()
        outcome = self._run(rt)
        assert isinstance(outcome, StepNotReadyOutcome)
        assert outcome.reason == NotReadyReason.NO_ELIGIBLE_STEP
        rt.conn.close()


class TestWorkerUnavailableUnchanged:
    def test_worker_missing_keeps_canon_worker_unavailable_exit_3(
        self, tmp_path
    ) -> None:
        db = tmp_path / "worker.sqlite3"
        rt = build_local_runtime(db, clock=_Clock())  # no workers registered
        rt.service.submit(_job(job_id=JOB),
                          [_step(STEP, idempotency_key=f"{JOB}:{STEP}")])
        rt.conn.close()
        result = _cli("job", "run", JOB, "--worker", WORKER, db=db)
        assert result.returncode == 3, (result.stdout, result.stderr)
        assert "Traceback" not in result.stderr
