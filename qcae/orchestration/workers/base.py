"""Worker interface + P2 test workers (P2-C06, directive §20).

P2 proves orchestration semantics with deterministic test workers; P3+
supplies domain workers (GitHubWorker, DeepWikiWorker, ...) behind the same
interface.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from qcae.orchestration.context.packet import ContextPacket
from qcae.orchestration.workers.contracts import (
    WorkerClaim,
    WorkerRequest,
    WorkerResult,
    WorkerStatus,
)

__all__ = [
    "Worker",
    "EchoWorker",
    "DeterministicSuccessWorker",
    "RetryOnceWorker",
    "PermanentFailureWorker",
    "ApprovalRequiredWorker",
    "CrashWorker",
]


@runtime_checkable
class Worker(Protocol):
    """Minimum worker protocol (Book V 12.3)."""

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        ...


def _base_result(request: WorkerRequest, status: WorkerStatus, **over) -> WorkerResult:
    data = dict(
        step_id=request.step_id,
        job_id=request.job_id,
        status=status,
    )
    data.update(over)
    return WorkerResult(**data)


class EchoWorker:
    """Returns SUCCESS echoing the request's inputs as outputs (smoke worker)."""

    worker_type = "echo"

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        return _base_result(
            request,
            WorkerStatus.SUCCESS,
            output_artifact_refs=tuple(request.requested_outputs),
            evidence_refs=tuple(request.input_artifact_refs),
        )


class DeterministicSuccessWorker:
    """Always SUCCESS with a fixed evidence ref (idempotency fixtures)."""

    worker_type = "deterministic-success"

    def __init__(self, evidence_ref: str = "ev-deterministic") -> None:
        self._evidence = evidence_ref
        self.calls = 0

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        self.calls += 1
        return _base_result(
            request, WorkerStatus.SUCCESS, evidence_refs=(self._evidence,)
        )


class RetryOnceWorker:
    """Fails TRANSIENT on first attempt, succeeds afterwards (bounded retry)."""

    worker_type = "retry-once"

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        self.calls += 1
        if self.calls == 1:
            return _base_result(
                request,
                WorkerStatus.RETRYABLE,
                failure_class="TRANSIENT",
                error_summary="simulated transient provider failure",
            )
        return _base_result(request, WorkerStatus.SUCCESS, evidence_refs=("ev-retry-ok",))


class PermanentFailureWorker:
    """Always FAILED/PERMANENT — must never be retried."""

    worker_type = "permanent-failure"

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        return _base_result(
            request,
            WorkerStatus.FAILED,
            failure_class="PERMANENT",
            error_summary="unrecoverable worker failure",
        )


class ApprovalRequiredWorker:
    """Reports BLOCKED_POLICY with APPROVAL_REQUIRED classification."""

    worker_type = "approval-required"

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        return _base_result(
            request,
            WorkerStatus.BLOCKED_POLICY,
            failure_class="APPROVAL_REQUIRED",
            error_summary="action requires operator approval",
            recommended_next_actions=("request-approval",),
        )


class CrashWorker:
    """Simulates process death: raises before returning any result."""

    worker_type = "crash"

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: WorkerRequest, packet: ContextPacket) -> WorkerResult:
        self.calls += 1
        raise RuntimeError("simulated worker crash")
