"""P2-C01 — runtime domain and fail-closed state machines (ADR-0008)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeStateTransitionError, QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.orchestration.jobs import (
    FailureClass,
    JobEvent,
    JobEventType,
    LeaseInfo,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
    assert_job_transition,
    assert_step_transition,
    is_terminal_job,
    is_terminal_step,
    legal_job_transitions,
    legal_step_transitions,
)


def _job(**over):
    base = dict(
        job_id="job-12345678",
        deterministic_id=deterministic_job_id("discovery", "cap-0001", "k1"),
        job_type="DISCOVERY",
        subject_ref="cap-0001",
        created_by="operator",
        created_at="2026-09-13T00:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(**over):
    base = dict(
        step_id="s-00000001",
        job_id="job-12345678",
        step_type="FETCH",
        created_at="2026-09-13T00:00:00Z",
    )
    base.update(over)
    return RuntimeStep(**base)


class TestJobStateMachine:
    def test_created_to_queued_to_running_is_legal(self):
        assert_job_transition(RuntimeJobStatus.CREATED, RuntimeJobStatus.QUEUED)
        assert_job_transition(RuntimeJobStatus.QUEUED, RuntimeJobStatus.RUNNING)

    def test_succeeded_to_running_rejected(self):
        with pytest.raises(QcaeStateTransitionError):
            assert_job_transition(
                RuntimeJobStatus.SUCCEEDED, RuntimeJobStatus.RUNNING
            )

    def test_failed_must_not_reenter_running_directly(self):
        # Recovery goes through explicit RETRY semantics at the step level or
        # a new job; FAILED is terminal at the job level (ADR-0008).
        with pytest.raises(QcaeStateTransitionError):
            assert_job_transition(RuntimeJobStatus.FAILED, RuntimeJobStatus.RUNNING)

    def test_terminal_states_have_no_outgoing_transitions(self):
        for terminal in (
            RuntimeJobStatus.SUCCEEDED,
            RuntimeJobStatus.FAILED,
            RuntimeJobStatus.CANCELLED,
        ):
            assert legal_job_transitions(terminal) == frozenset()
            assert is_terminal_job(terminal)

    def test_unknown_state_fails_closed(self):
        with pytest.raises(QcaeStateTransitionError):
            assert_job_transition("NOT_A_STATE", RuntimeJobStatus.RUNNING)

    def test_waiting_approval_paths(self):
        assert RuntimeJobStatus.RUNNING in legal_job_transitions(
            RuntimeJobStatus.WAITING_APPROVAL
        )
        assert RuntimeJobStatus.BLOCKED in legal_job_transitions(
            RuntimeJobStatus.WAITING_APPROVAL
        )
        # No silent shortcut from WAITING_APPROVAL to SUCCEEDED.
        with pytest.raises(QcaeStateTransitionError):
            assert_job_transition(
                RuntimeJobStatus.WAITING_APPROVAL, RuntimeJobStatus.SUCCEEDED
            )


class TestStepStateMachine:
    def test_canon_136_vocabulary_is_verbatim(self):
        assert {s.value for s in RuntimeStepStatus} == {
            "PENDING", "READY", "RUNNING", "WAITING_POLICY", "WAITING_INPUT",
            "RETRY_SCHEDULED", "SUCCEEDED", "PARTIAL", "FAILED", "CANCELLED",
            "STALE",
        }

    def test_pending_ready_running_legal(self):
        assert_step_transition(RuntimeStepStatus.PENDING, RuntimeStepStatus.READY)
        assert_step_transition(RuntimeStepStatus.READY, RuntimeStepStatus.RUNNING)

    def test_running_to_retry_scheduled_legal(self):
        assert_step_transition(
            RuntimeStepStatus.RUNNING, RuntimeStepStatus.RETRY_SCHEDULED
        )

    def test_retry_scheduled_back_to_ready(self):
        assert_step_transition(
            RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.READY
        )

    def test_succeeded_is_terminal(self):
        with pytest.raises(QcaeStateTransitionError):
            assert_step_transition(
                RuntimeStepStatus.SUCCEEDED, RuntimeStepStatus.RUNNING
            )
        assert is_terminal_step(RuntimeStepStatus.SUCCEEDED)
        assert is_terminal_step(RuntimeStepStatus.CANCELLED)

    def test_waiting_policy_cannot_jump_to_succeeded(self):
        with pytest.raises(QcaeStateTransitionError):
            assert_step_transition(
                RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.SUCCEEDED
            )

    def test_failed_can_enter_retry_scheduled_only(self):
        assert legal_step_transitions(RuntimeStepStatus.FAILED) == frozenset(
            {RuntimeStepStatus.RETRY_SCHEDULED}
        )

    def test_is_open_vs_terminal(self):
        from qcae.orchestration.jobs.graph import is_open

        assert is_open(_step(status=RuntimeStepStatus.RUNNING))
        assert not is_open(_step(status=RuntimeStepStatus.SUCCEEDED))
        assert not is_open(_step(status=RuntimeStepStatus.CANCELLED))


class TestRecordValidation:
    def test_job_round_trip(self):
        job = _job()
        restored = RuntimeJob.from_dict(job.to_dict())
        assert restored == job
        assert restored.digest() == job.digest()

    def test_step_round_trip_with_lease(self):
        step = _step(
            lease=LeaseInfo(
                lease_owner="worker-1",
                lease_token="tok-1",
                leased_at="2026-09-13T00:00:01Z",
                lease_expires_at="2026-09-13T00:05:01Z",
            ),
            budget_allocation={"attempts": 3},
            budget_used={"attempts": 1},
        )
        restored = RuntimeStep.from_dict(step.to_dict())
        assert restored == step
        assert restored.lease == step.lease

    def test_job_requires_deterministic_id_prefix(self):
        with pytest.raises(QcaeValidationError):
            _job(deterministic_id="not-a-job-id").validate()

    def test_step_rejects_self_dependency(self):
        with pytest.raises(QcaeValidationError):
            _step(dependencies=("s-00000001",)).validate()

    def test_step_rejects_attempt_over_max(self):
        with pytest.raises(QcaeValidationError):
            _step(attempt=4, max_attempts=3).validate()

    def test_step_rejects_budget_overrun_in_record(self):
        with pytest.raises(QcaeValidationError):
            _step(
                budget_allocation={"attempts": 2},
                budget_used={"attempts": 3},
            ).validate()

    def test_step_rejects_unknown_budget_dimension(self):
        with pytest.raises(QcaeValidationError):
            _step(
                budget_allocation={"attempts": 2},
                budget_used={"tokens": 1},
            ).validate()

    def test_failed_step_requires_failure_class(self):
        with pytest.raises(QcaeValidationError):
            _step(status=RuntimeStepStatus.FAILED).validate()

    def test_failed_step_with_class_ok(self):
        s = _step(
            status=RuntimeStepStatus.FAILED,
            failure_class=FailureClass.TRANSIENT.value,
        )
        s.validate()

    def test_completed_at_requires_started_at(self):
        with pytest.raises(QcaeValidationError):
            _step(completed_at="2026-09-13T00:00:02Z").validate()

    def test_job_rejects_non_status(self):
        with pytest.raises(QcaeValidationError):
            _job(status="GARBAGE").validate()


class TestEventRecord:
    def test_event_round_trip(self):
        event = JobEvent(
            event_seq=1,
            event_id="ev-00000001",
            event_type=JobEventType.JOB_CREATED,
            job_id="job-12345678",
            occurred_at="2026-09-13T00:00:00Z",
        )
        restored = JobEvent.from_dict(event.to_dict())
        assert restored == event

    def test_event_requires_valid_type(self):
        with pytest.raises(QcaeValidationError):
            JobEvent(
                event_seq=1,
                event_id="ev-00000001",
                event_type="NOT_AN_EVENT",
                job_id="job-12345678",
                occurred_at="2026-09-13T00:00:00Z",
            ).validate()

    def test_event_requires_seq_positive(self):
        with pytest.raises(QcaeValidationError):
            JobEvent(
                event_seq=0,
                event_id="ev-00000001",
                event_type=JobEventType.JOB_CREATED,
                job_id="job-12345678",
                occurred_at="2026-09-13T00:00:00Z",
            ).validate()
