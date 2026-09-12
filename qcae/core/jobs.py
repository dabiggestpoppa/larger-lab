"""Job/Step state contracts (Book V 15.2 "Job/Step state contracts").

P0 scope: deterministic identity, typed status, and serialization shape. The
queue, leases, and resumability semantics are P2 (canon 18.1 Phase 2) and will
extend these records additively with new schema versions.

Deterministic identity (master prompt §27 "Job / Step deterministic identity"):
``deterministic_id`` derives from content (job kind + subject + creator-supplied
key), so re-enqueueing the same logical work produces the same identity and
idempotency checks can rely on it. Server-assigned ``job_id`` remains unique per
physical job.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


def deterministic_job_id(job_kind: str, subject_ref: str, idempotency_key: str) -> str:
    """Deterministic content-derived job identity.

    Same logical work + key => same id, independent of submission time or host.
    """
    payload = f"{job_kind}\x1f{subject_ref}\x1f{idempotency_key}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"job-{job_kind}-{digest}"


@dataclass(frozen=True)
class Step(SerializableRecord):
    SCHEMA_VERSION = 1

    step_id: str
    step_kind: str
    status: StepStatus = StepStatus.PENDING

    # Ordered refs to evidence digests produced by this step.
    evidence_digests: Tuple[str, ...] = ()

    error: str = ""

    _COERCIONS = {"status": lambda v: v if isinstance(v, StepStatus) else _coerce_step(v)}

    def validate(self) -> None:
        require_identifier(self.step_id, "step_id")
        require_non_empty_str(self.step_kind, "step_kind")
        if not isinstance(self.status, StepStatus):
            raise QcaeValidationError(
                f"status must be a StepStatus member, got {self.status!r}"
            )
        for digest in self.evidence_digests:
            if not isinstance(digest, str) or len(digest) < 8:
                raise QcaeValidationError(
                    f"evidence_digests entries must be content digests, got {digest!r}"
                )
        if self.status == StepStatus.FAILED and not self.error:
            raise QcaeValidationError("failed steps must record their error")


@dataclass(frozen=True)
class Job(SerializableRecord):
    SCHEMA_VERSION = 1

    job_id: str
    deterministic_id: str
    job_kind: str

    # The capability/atom/contract/candidate this job operates on.
    subject_ref: str

    status: JobStatus = JobStatus.PENDING
    steps: Tuple[Step, ...] = ()

    # Worker/agent roster placement (master prompt §7); logical name only.
    worker_role: str = ""
    context_packet_ref: str = ""
    created_by: str = ""
    created_at: str = ""

    _NESTED_RECORDS = {"steps": Step}
    _COERCIONS = {"status": lambda v: v if isinstance(v, JobStatus) else _coerce_job(v)}

    def validate(self) -> None:
        require_identifier(self.job_id, "job_id")
        require_identifier(self.deterministic_id, "deterministic_id")
        if not self.deterministic_id.startswith("job-"):
            raise QcaeValidationError(
                "deterministic_id must be produced by deterministic_job_id()"
            )
        require_non_empty_str(self.job_kind, "job_kind")
        require_identifier(self.subject_ref, "subject_ref")
        if not isinstance(self.status, JobStatus):
            raise QcaeValidationError(
                f"status must be a JobStatus member, got {self.status!r}"
            )
        require_no_duplicates(self.steps, "steps")
        step_ids = [step.step_id for step in self.steps]
        require_no_duplicates(step_ids, "step_id")
        for step in self.steps:
            step.validate()
        if self.created_by:
            require_non_empty_str(self.created_by, "created_by")


def _coerce_job(value):
    try:
        return JobStatus(value)
    except ValueError:
        return value


def _coerce_step(value):
    try:
        return StepStatus(value)
    except ValueError:
        return value


def make_job(**kwargs) -> Job:
    """Build and validate a job in one call."""
    job = Job(**kwargs)
    job.validate()
    return job
