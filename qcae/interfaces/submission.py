"""Canonical job submission (P2-R2-C04; Book V 12.1, 13.7).

A structured, validated submission envelope: interfaces (CLI today, HTTP/OCE
tomorrow) hand this record to the application service, which validates it
CANONICALLY before any persistence. Submission then flows through the
engine's atomic path (P2-C07R3): job + steps + initial events + queue
metadata commit together or not at all.

Laws:

- ``deterministic_id`` is derived here from (job_kind, subject, key) so the
  same logical work submitted twice is refused, not duplicated;
- step graphs are validated (cycle / self-dep / missing-dep fail closed)
  before submission, by the same StepGraph the engine uses;
- validation happens BEFORE persistence — a malformed submission persists
  nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)
from qcae.orchestration.jobs.graph import StepGraph
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep

__all__ = ["JobSubmission", "make_submission_job", "make_submission_steps"]


@dataclass(frozen=True)
class JobSubmission(SerializableRecord):
    """Canonical, versioned submission envelope (Book V 13.7 input contract)."""

    SCHEMA_VERSION = 1

    job_kind: str
    subject_ref: str
    idempotency_key: str

    #: One entry per step: {"step_id", "step_type", "dependencies": [...]}.
    #: Kept JSON-native so the envelope round-trips through any interface.
    steps: Tuple[dict, ...] = ()

    submitted_by: str = ""
    step_graph_version: str = "v1"
    priority: int = 0
    not_before: str = ""

    def validate(self) -> None:
        require_non_empty_str(self.job_kind, "job_kind")
        require_identifier(self.subject_ref, "subject_ref")
        require_non_empty_str(self.idempotency_key, "idempotency_key")
        if not self.steps:
            raise QcaeValidationError("submission must declare at least one step")
        seen: List[str] = []
        for i, step in enumerate(self.steps):
            if not isinstance(step, dict):
                raise QcaeValidationError(f"steps[{i}] must be an object")
            sid = step.get("step_id", "")
            require_identifier(sid, f"steps[{i}].step_id")
            require_non_empty_str(step.get("step_type", ""), f"steps[{i}].step_type")
            deps = step.get("dependencies", [])
            if not isinstance(deps, (list, tuple)):
                raise QcaeValidationError(f"steps[{i}].dependencies must be a list")
            for d in deps:
                if not isinstance(d, str) or not d:
                    raise QcaeValidationError(
                        f"steps[{i}].dependencies entries must be step ids"
                    )
            if sid in seen:
                raise QcaeValidationError(f"duplicate step_id {sid!r} in submission")
            seen.append(sid)
        # Dependency targets must exist within the submission.
        ids = set(seen)
        for i, step in enumerate(self.steps):
            for d in step.get("dependencies", []):
                if d not in ids:
                    raise QcaeValidationError(
                        f"steps[{i}] depends on unknown step {d!r}"
                    )
                if d == step.get("step_id"):
                    raise QcaeValidationError(
                        f"steps[{i}] cannot depend on itself"
                    )
        if self.submitted_by:
            require_non_empty_str(self.submitted_by, "submitted_by")


def make_submission_job(submission: JobSubmission, *, created_at: str,
                        job_id: str) -> RuntimeJob:
    """Build the durable RuntimeJob from a validated submission."""
    return RuntimeJob(
        job_id=job_id,
        deterministic_id=deterministic_job_id(
            submission.job_kind, submission.subject_ref, submission.idempotency_key
        ),
        job_type=submission.job_kind,
        subject_ref=submission.subject_ref,
        created_by=submission.submitted_by or "id-operator-local",
        created_at=created_at,
        step_graph_version=submission.step_graph_version,
        priority=submission.priority,
    )


def make_submission_steps(submission: JobSubmission, *, created_at: str,
                          job_id: str) -> List[RuntimeStep]:
    """Build the durable RuntimeStep list from a validated submission."""
    steps = [
        RuntimeStep(
            step_id=f"{job_id}:{s['step_id']}",
            job_id=job_id,
            step_type=s["step_type"],
            dependencies=tuple(f"{job_id}:{d}" for d in s.get("dependencies", [])),
            created_at=created_at,
            idempotency_key=f"{job_id}:{s['step_id']}",
        )
        for s in submission.steps
    ]
    # Canonical graph law check with the engine's own graph primitive.
    StepGraph(steps)
    return steps
