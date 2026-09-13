"""P2 runtime job/step domain (ADR-0008; Book V 12.1, 13.6).

The frozen P0 ``Job``/``Step`` records (``qcae.core.jobs``) remain the identity
layer. This module adds the *executable* runtime layer: operational state
machines with explicit, fail-closed transition tables, lease/budget/
checkpoint/authority wiring, and an append-oriented event stream.

State vocabularies (ADR-0008):

- ``RuntimeStepStatus`` is the Book V 13.6 vocabulary, verbatim.
- ``RuntimeJobStatus`` is the P2 operator-directive job-level set.

Transition tables are explicit and closed-world: any transition not listed
raises ``QcaeStateTransitionError`` (Book I lifecycle doctrine; recovery and
retry use explicit transitions, never arbitrary mutation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import FrozenSet, Optional, Tuple

from qcae.core.errors import QcaeStateTransitionError, QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)

__all__ = [
    "RuntimeJobStatus",
    "RuntimeStepStatus",
    "JobEventType",
    "FailureClass",
    "JOB_TRANSITIONS",
    "STEP_TRANSITIONS",
    "TERMINAL_JOB_STATES",
    "TERMINAL_STEP_STATES",
    "assert_job_transition",
    "legal_job_transitions",
    "is_terminal_job",
    "assert_step_transition",
    "legal_step_transitions",
    "is_terminal_step",
    "RuntimeJob",
    "RuntimeStep",
    "JobEvent",
    "LeaseInfo",
    "make_runtime_job",
    "make_runtime_step",
    "make_job_event",
]


class RuntimeJobStatus(StrEnum):
    """Job-level runtime states (P2 directive §5; ADR-0008)."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RETRY_PENDING = "RETRY_PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class RuntimeStepStatus(StrEnum):
    """Step states — Book V 13.6 vocabulary, verbatim (ADR-0008)."""

    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_POLICY = "WAITING_POLICY"
    WAITING_INPUT = "WAITING_INPUT"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    STALE = "STALE"


class JobEventType(StrEnum):
    """Append-oriented event vocabulary (P2 directive §9)."""

    JOB_CREATED = "JOB_CREATED"
    JOB_QUEUED = "JOB_QUEUED"
    STEP_READY = "STEP_READY"
    STEP_LEASED = "STEP_LEASED"
    STEP_STARTED = "STEP_STARTED"
    CHECKPOINT_WRITTEN = "CHECKPOINT_WRITTEN"
    STEP_SUCCEEDED = "STEP_SUCCEEDED"
    STEP_FAILED = "STEP_FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    JOB_SUCCEEDED = "JOB_SUCCEEDED"
    JOB_FAILED = "JOB_FAILED"
    JOB_CANCELLED = "JOB_CANCELLED"


class FailureClass(StrEnum):
    """Bounded failure taxonomy (P2 directive §26; Book V 12.6)."""

    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    INVALID_INPUT = "INVALID_INPUT"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    UNKNOWN = "UNKNOWN"


#: Job-level legal transitions. Anything not listed is illegal, including
#: transitions out of terminal states (SUCCEEDED/FAILED/CANCELLED).
JOB_TRANSITIONS = {
    # CREATED: only enqueue or cancel.
    (RuntimeJobStatus.CREATED, RuntimeJobStatus.QUEUED),
    (RuntimeJobStatus.CREATED, RuntimeJobStatus.CANCELLED),
    (RuntimeJobStatus.CREATED, RuntimeJobStatus.BLOCKED),
    # QUEUED: dispatch or cancel.
    (RuntimeJobStatus.QUEUED, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.QUEUED, RuntimeJobStatus.CANCELLED),
    (RuntimeJobStatus.QUEUED, RuntimeJobStatus.BLOCKED),
    # RUNNING: forward progress, waits, retry, or safe cancel.
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.WAITING),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.WAITING_APPROVAL),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.RETRY_PENDING),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.SUCCEEDED),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.FAILED),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.CANCELLED),
    (RuntimeJobStatus.RUNNING, RuntimeJobStatus.BLOCKED),
    # WAITING (external input): resume, fail, cancel, block.
    (RuntimeJobStatus.WAITING, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.WAITING, RuntimeJobStatus.FAILED),
    (RuntimeJobStatus.WAITING, RuntimeJobStatus.CANCELLED),
    (RuntimeJobStatus.WAITING, RuntimeJobStatus.BLOCKED),
    # WAITING_APPROVAL: grant resumes, denial blocks or fails.
    (RuntimeJobStatus.WAITING_APPROVAL, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.WAITING_APPROVAL, RuntimeJobStatus.BLOCKED),
    (RuntimeJobStatus.WAITING_APPROVAL, RuntimeJobStatus.FAILED),
    (RuntimeJobStatus.WAITING_APPROVAL, RuntimeJobStatus.CANCELLED),
    # RETRY_PENDING: back to running (bounded by retry policy).
    (RuntimeJobStatus.RETRY_PENDING, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.RETRY_PENDING, RuntimeJobStatus.FAILED),
    (RuntimeJobStatus.RETRY_PENDING, RuntimeJobStatus.CANCELLED),
    # BLOCKED: unblock into running, fail, or cancel. Never auto-restart.
    (RuntimeJobStatus.BLOCKED, RuntimeJobStatus.RUNNING),
    (RuntimeJobStatus.BLOCKED, RuntimeJobStatus.FAILED),
    (RuntimeJobStatus.BLOCKED, RuntimeJobStatus.CANCELLED),
}

TERMINAL_JOB_STATES: FrozenSet[RuntimeJobStatus] = frozenset(
    {RuntimeJobStatus.SUCCEEDED, RuntimeJobStatus.FAILED, RuntimeJobStatus.CANCELLED}
)

#: Step-level legal transitions (Book V 13.6). WAITING_POLICY is entered by
#: the authority layer (REQUIRE_APPROVAL / DENY paths); READY derives from
#: satisfied dependencies, valid inputs, budget, and policy.
STEP_TRANSITIONS = {
    (RuntimeStepStatus.PENDING, RuntimeStepStatus.READY),
    (RuntimeStepStatus.PENDING, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.PENDING, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.READY, RuntimeStepStatus.RUNNING),
    (RuntimeStepStatus.READY, RuntimeStepStatus.WAITING_POLICY),
    (RuntimeStepStatus.READY, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.READY, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.RUNNING),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.SUCCEEDED),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.PARTIAL),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.FAILED),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.RETRY_SCHEDULED),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.WAITING_POLICY),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.WAITING_INPUT),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.RUNNING, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.READY),
    (RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.FAILED),
    (RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.WAITING_INPUT),
    (RuntimeStepStatus.WAITING_POLICY, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.WAITING_INPUT, RuntimeStepStatus.READY),
    (RuntimeStepStatus.WAITING_INPUT, RuntimeStepStatus.FAILED),
    (RuntimeStepStatus.WAITING_INPUT, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.WAITING_INPUT, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.READY),
    (RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.FAILED),
    (RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.PARTIAL, RuntimeStepStatus.READY),
    (RuntimeStepStatus.PARTIAL, RuntimeStepStatus.FAILED),
    (RuntimeStepStatus.PARTIAL, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.PARTIAL, RuntimeStepStatus.STALE),
    (RuntimeStepStatus.STALE, RuntimeStepStatus.READY),
    (RuntimeStepStatus.STALE, RuntimeStepStatus.CANCELLED),
    (RuntimeStepStatus.FAILED, RuntimeStepStatus.RETRY_SCHEDULED),
}

TERMINAL_STEP_STATES: FrozenSet[RuntimeStepStatus] = frozenset(
    {RuntimeStepStatus.SUCCEEDED, RuntimeStepStatus.CANCELLED}
)

_JOB_TRANSITIONS_SET = {
    (a, b) for (a, b) in JOB_TRANSITIONS
}
_STEP_TRANSITIONS_SET = set(STEP_TRANSITIONS)


def assert_job_transition(
    current: RuntimeJobStatus, target: RuntimeJobStatus
) -> None:
    """Fail closed unless the transition is explicitly legal."""
    if not isinstance(current, RuntimeJobStatus) or not isinstance(
        target, RuntimeJobStatus
    ):
        raise QcaeStateTransitionError(
            f"unknown runtime job state(s): {current!r} -> {target!r}"
        )
    if (current, target) not in _JOB_TRANSITIONS_SET:
        raise QcaeStateTransitionError(
            f"illegal runtime job transition {current.value} -> {target.value}"
        )


def legal_job_transitions(current: RuntimeJobStatus) -> FrozenSet[RuntimeJobStatus]:
    return frozenset(
        b for (a, b) in _JOB_TRANSITIONS_SET if a == current
    )


def is_terminal_job(state: RuntimeJobStatus) -> bool:
    return state in TERMINAL_JOB_STATES


def assert_step_transition(
    current: RuntimeStepStatus, target: RuntimeStepStatus
) -> None:
    if not isinstance(current, RuntimeStepStatus) or not isinstance(
        target, RuntimeStepStatus
    ):
        raise QcaeStateTransitionError(
            f"unknown runtime step state(s): {current!r} -> {target!r}"
        )
    if (current, target) not in _STEP_TRANSITIONS_SET:
        raise QcaeStateTransitionError(
            f"illegal runtime step transition {current.value} -> {target.value}"
        )


def legal_step_transitions(current: RuntimeStepStatus) -> FrozenSet[RuntimeStepStatus]:
    return frozenset(
        b for (a, b) in _STEP_TRANSITIONS_SET if a == current
    )


def is_terminal_step(state: RuntimeStepStatus) -> bool:
    return state in TERMINAL_STEP_STATES


@dataclass(frozen=True)
class LeaseInfo(SerializableRecord):
    """Lease ownership for one step (Book V 13.6 leasing; P2 directive §22)."""

    SCHEMA_VERSION = 1

    lease_owner: str
    lease_token: str
    leased_at: str
    lease_expires_at: str

    def validate(self) -> None:
        require_non_empty_str(self.lease_owner, "lease_owner")
        require_non_empty_str(self.lease_token, "lease_token")
        require_non_empty_str(self.leased_at, "leased_at")
        require_non_empty_str(self.lease_expires_at, "lease_expires_at")


@dataclass(frozen=True)
class RuntimeStep(SerializableRecord):
    """Durable unit of work (P2 directive §6; Book V 13.6)."""

    SCHEMA_VERSION = 1

    step_id: str
    job_id: str
    step_type: str

    # Deterministic logical identity: stable under re-planning of the same
    # job graph so repeated orchestration cannot duplicate logical steps.
    logical_step_id: str = ""

    dependencies: Tuple[str, ...] = ()
    status: RuntimeStepStatus = RuntimeStepStatus.PENDING

    attempt: int = 0
    max_attempts: int = 3

    lease: Optional[LeaseInfo] = None

    input_ref: str = ""
    output_refs: Tuple[str, ...] = ()
    evidence_refs: Tuple[str, ...] = ()
    checkpoint_ref: str = ""
    idempotency_key: str = ""

    # Budget allocation for this step (dimension -> units); conservation is
    # enforced by the budget layer (P2-C08).
    budget_allocation: dict = field(default_factory=dict)
    budget_used: dict = field(default_factory=dict)

    authority_requirement: str = ""
    failure_class: str = ""
    not_before: str = ""

    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""

    _NESTED_RECORDS = {"lease": LeaseInfo}
    _COERCIONS = {"status": lambda v: coerce_enum(v, RuntimeStepStatus)}

    def validate(self) -> None:
        require_identifier(self.step_id, "step_id")
        require_identifier(self.job_id, "job_id")
        require_non_empty_str(self.step_type, "step_type")
        require_no_duplicates(self.dependencies, "dependencies")
        if self.step_id in self.dependencies:
            raise QcaeValidationError("step cannot depend on itself")
        if not isinstance(self.status, RuntimeStepStatus):
            raise QcaeValidationError(
                f"status must be a RuntimeStepStatus member, got {self.status!r}"
            )
        if self.attempt < 0:
            raise QcaeValidationError("attempt must be >= 0")
        if self.max_attempts < 1:
            raise QcaeValidationError("max_attempts must be >= 1")
        if self.attempt > self.max_attempts:
            raise QcaeValidationError(
                f"attempt {self.attempt} exceeds max_attempts {self.max_attempts}"
            )
        if self.lease is not None:
            self.lease.validate()
        if not isinstance(self.budget_allocation, dict) or not isinstance(
            self.budget_used, dict
        ):
            raise QcaeValidationError("budget fields must be dicts")
        for dim, used in self.budget_used.items():
            if dim not in self.budget_allocation:
                raise QcaeValidationError(
                    f"budget_used dimension {dim!r} not in allocation"
                )
            if self.budget_allocation[dim] < used:
                raise QcaeValidationError(
                    f"budget_used for {dim!r} exceeds allocation"
                )
        if self.status == RuntimeStepStatus.FAILED and not self.failure_class:
            raise QcaeValidationError("failed steps must record failure_class")
        for ts in (self.created_at, self.started_at, self.completed_at):
            if ts:
                require_non_empty_str(ts, "timestamp")
        if self.started_at and not self.created_at:
            raise QcaeValidationError("started_at requires created_at")
        if self.completed_at and not self.started_at:
            raise QcaeValidationError("completed_at requires started_at")


@dataclass(frozen=True)
class RuntimeJob(SerializableRecord):
    """Durable job record (P2 directive §4; Book V 12.1 state discipline)."""

    SCHEMA_VERSION = 1

    job_id: str
    deterministic_id: str
    job_type: str

    # Objective / contract / capability this job operates on.
    subject_ref: str = ""

    status: RuntimeJobStatus = RuntimeJobStatus.CREATED
    priority: int = 0

    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    budget_ref: str = ""
    authority_context_ref: str = ""
    current_checkpoint_ref: str = ""
    step_graph_version: str = ""

    parent_job_id: str = ""
    evidence_refs: Tuple[str, ...] = ()
    failure_ref: str = ""
    escalation_ref: str = ""

    _COERCIONS = {"status": lambda v: coerce_enum(v, RuntimeJobStatus)}

    def validate(self) -> None:
        require_identifier(self.job_id, "job_id")
        require_identifier(self.deterministic_id, "deterministic_id")
        if not self.deterministic_id.startswith("job-"):
            raise QcaeValidationError(
                "deterministic_id must be produced by deterministic_job_id()"
            )
        require_non_empty_str(self.job_type, "job_type")
        require_identifier(self.subject_ref, "subject_ref")
        if not isinstance(self.status, RuntimeJobStatus):
            raise QcaeValidationError(
                f"status must be a RuntimeJobStatus member, got {self.status!r}"
            )
        if self.created_by:
            require_non_empty_str(self.created_by, "created_by")
        if self.updated_at and not self.created_at:
            raise QcaeValidationError("updated_at requires created_at")


@dataclass(frozen=True)
class JobEvent(SerializableRecord):
    """One append-oriented runtime fact (P2 directive §9).

    Events are facts, not commands; historical truth lives here and is never
    rewritten from mutable rows (Book V 12.1: conversation context is never
    the canonical job state).
    """

    SCHEMA_VERSION = 1

    event_seq: int
    event_id: str
    event_type: JobEventType
    job_id: str

    step_id: str = ""
    occurred_at: str = ""
    actor: str = ""
    payload_json: str = ""

    _COERCIONS = {"event_type": lambda v: coerce_enum(v, JobEventType)}

    def validate(self) -> None:
        if self.event_seq < 1:
            raise QcaeValidationError("event_seq must be >= 1")
        require_identifier(self.event_id, "event_id")
        if not isinstance(self.event_type, JobEventType):
            raise QcaeValidationError(
                f"event_type must be a JobEventType member, got {self.event_type!r}"
            )
        require_identifier(self.job_id, "job_id")
        require_non_empty_str(self.occurred_at, "occurred_at")


def make_runtime_job(**kwargs) -> RuntimeJob:
    job = RuntimeJob(**kwargs)
    job.validate()
    return job


def make_runtime_step(**kwargs) -> RuntimeStep:
    step = RuntimeStep(**kwargs)
    step.validate()
    return step


def make_job_event(**kwargs) -> JobEvent:
    event = JobEvent(**kwargs)
    event.validate()
    return event
