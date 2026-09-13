"""Worker contracts (P2-C06; Book V 12.3, directive §19).

Typed handoff envelopes. Status vocabulary is canon 12.3 verbatim:

    SUCCESS PARTIAL FAILED BLOCKED_POLICY BLOCKED_INPUT INCONCLUSIVE
    RETRYABLE CANCELLED

Failures are never encoded only as free-form text (12.3 invariant; directive
§19: "No prose-only handoff"). Material claims carry evidence references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)

__all__ = [
    "WorkerStatus",
    "WorkerRequest",
    "WorkerResult",
    "WorkerClaim",
    "make_worker_request",
]


class WorkerStatus(StrEnum):
    """Book V 12.3 status vocabulary, verbatim."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    BLOCKED_POLICY = "BLOCKED_POLICY"
    BLOCKED_INPUT = "BLOCKED_INPUT"
    INCONCLUSIVE = "INCONCLUSIVE"
    RETRYABLE = "RETRYABLE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class WorkerClaim(SerializableRecord):
    """One structured assertion with verification state (12.3 claims discipline)."""

    SCHEMA_VERSION = 1

    claim_id: str
    statement: str
    verification_state: str  # CLAIMED / SOURCE_SUPPORTED / RUNTIME_VERIFIED /
    # CONTRACT_VERIFIED / DOMAIN_VERIFIED — never collapsed into one "true".
    evidence_refs: Tuple[str, ...] = ()

    def validate(self) -> None:
        require_identifier(self.claim_id, "claim_id")
        require_non_empty_str(self.statement, "statement")
        require_non_empty_str(self.verification_state, "verification_state")
        require_no_duplicates(self.evidence_refs, "evidence_refs")


@dataclass(frozen=True)
class WorkerRequest(SerializableRecord):
    """Book V 12.3 WorkerRequest, minimum fields."""

    SCHEMA_VERSION = 1

    job_id: str
    step_id: str
    worker_type: str
    contract_ref: str = ""
    input_artifact_refs: Tuple[str, ...] = ()
    requested_outputs: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()
    policy_context_ref: str = ""
    budget_ref: str = ""
    deadline: str = ""
    idempotency_key: str = ""
    context_packet_id: str = ""

    def validate(self) -> None:
        require_identifier(self.job_id, "job_id")
        require_identifier(self.step_id, "step_id")
        require_non_empty_str(self.worker_type, "worker_type")
        require_no_duplicates(self.input_artifact_refs, "input_artifact_refs")
        require_no_duplicates(self.requested_outputs, "requested_outputs")


@dataclass(frozen=True)
class WorkerResult(SerializableRecord):
    """Book V 12.3 WorkerResult, minimum fields."""

    SCHEMA_VERSION = 1

    step_id: str
    job_id: str
    status: WorkerStatus

    output_artifact_refs: Tuple[str, ...] = ()
    evidence_refs: Tuple[str, ...] = ()
    claims: Tuple[WorkerClaim, ...] = ()
    uncertainties: Tuple[str, ...] = ()
    contradictions: Tuple[str, ...] = ()
    policy_event_refs: Tuple[str, ...] = ()
    budget_used: dict = field(default_factory=dict)
    logs_ref: str = ""
    recommended_next_actions: Tuple[str, ...] = ()
    failure_class: str = ""
    error_summary: str = ""

    _COERCIONS = {
        "status": lambda v: coerce_enum(v, WorkerStatus),
    }
    _NESTED_RECORDS = {"claims": WorkerClaim}

    def validate(self) -> None:
        require_identifier(self.step_id, "step_id")
        require_identifier(self.job_id, "job_id")
        if not isinstance(self.status, WorkerStatus):
            raise QcaeValidationError(
                f"status must be a WorkerStatus member, got {self.status!r}"
            )
        require_no_duplicates(self.output_artifact_refs, "output_artifact_refs")
        require_no_duplicates(self.evidence_refs, "evidence_refs")
        require_no_duplicates(self.contradictions, "contradictions")
        if not isinstance(self.budget_used, dict):
            raise QcaeValidationError("budget_used must be a dict")
        if self.status in (WorkerStatus.FAILED, WorkerStatus.RETRYABLE):
            if not self.failure_class:
                raise QcaeValidationError(
                    "FAILED/RETRYABLE results must carry failure_class"
                )
            if not self.error_summary:
                raise QcaeValidationError(
                    "FAILED/RETRYABLE results must carry error_summary"
                )
        # Material claims carry evidence (12.3: missing evidence cannot be
        # patched by conversational inference).
        for claim in self.claims:
            claim.validate()
            if not claim.evidence_refs:
                raise QcaeValidationError(
                    f"claim {claim.claim_id!r} has no evidence refs"
                )


def make_worker_request(**kwargs) -> WorkerRequest:
    request = WorkerRequest(**kwargs)
    request.validate()
    return request


def make_worker_result(**kwargs) -> WorkerResult:
    result = WorkerResult(**kwargs)
    result.validate()
    return result
