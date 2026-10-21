"""Typed operator outcomes for a job run that cannot proceed (P2-R5-I0R).

Canon Book V 15.12 defines the public error model; ``CONTRACT_NOT_READY`` and
the unknown-identity standing are domain categories, not prose. Two typed
records close the standing gap the operator playtest found:

- ``JobMissingOutcome`` — the requested job does not exist. A mistyped id
  receives the same unknown-job standing ``job status``/``job events``
  already answer, never "no eligible step to run", which would claim the
  job exists but has nothing to do.
- ``StepNotReadyOutcome`` — the job exists but no step is currently
  claimable, carried with a *typed reason* (Book V 15.12 ``NOT_READY``
  standing) instead of an unexplained null.

Both are truth-without-an-exception-path outcomes, like
``WorkerUnavailable`` (P2-R3-C02): the CLI maps them to stable exit codes,
no state was mutated, and the reason vocabulary is exhaustive over the
runtime's own step states. Execution mutations: 0 — nothing is leased,
claimed, charged, or evented by either outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

__all__ = ["NOT_READY_REASONS", "JobMissingOutcome", "StepNotReadyOutcome"]


class NotReadyReason:
    """Typed reasons a job with an eligible worker can still not run a step.

    Each reason is derived from the durable step rows, so the CLI's answer is
    a reading of durable state, never an interpretation:

    - ``NO_ELIGIBLE_STEP`` — no step is claimable now (dependencies pending,
      every step terminal, or nothing left to claim);
    - ``SCHEDULE_NOT_ELAPSED`` — an eligible step's effective ``not_before``
      is still in the future (P2-R4-C04 scheduling truth);
    - ``STEP_WAITING_POLICY`` — an eligible step waits in WAITING_POLICY for
      an operator grant (canon 15.12 ``APPROVAL_REQUIRED``);
    - ``STEP_WAITING_INPUT`` — an eligible step waits in WAITING_INPUT for
      operator resolution;
    - ``STEP_RETRY_SCHEDULED`` — the step's retry backoff has not elapsed.
    """

    NO_ELIGIBLE_STEP = "NO_ELIGIBLE_STEP"
    SCHEDULE_NOT_ELAPSED = "SCHEDULE_NOT_ELAPSED"
    STEP_WAITING_POLICY = "STEP_WAITING_POLICY"
    STEP_WAITING_INPUT = "STEP_WAITING_INPUT"
    STEP_RETRY_SCHEDULED = "STEP_RETRY_SCHEDULED"


#: The exhaustive reason vocabulary a ``StepNotReadyOutcome`` may carry.
NOT_READY_REASONS: Tuple[str, ...] = (
    NotReadyReason.NO_ELIGIBLE_STEP,
    NotReadyReason.SCHEDULE_NOT_ELAPSED,
    NotReadyReason.STEP_WAITING_POLICY,
    NotReadyReason.STEP_WAITING_INPUT,
    NotReadyReason.STEP_RETRY_SCHEDULED,
)


class JobMissingOutcome:
    """Typed unknown-job result (truth without an exception path).

    Same standing ``job status`` answers for an unknown id, now shared by
    ``job run`` so one identifier has one standing on every surface.
    """

    REASON = "JOB_NOT_FOUND"

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id

    @property
    def reason(self) -> str:
        return self.REASON

    def message(self) -> str:
        # Byte-identical to the standing `job status` prints for an unknown
        # id (P2-R5): one identifier, one standing, on every surface.
        return f"unknown job {self.job_id}"

    def __repr__(self) -> str:  # pragma: no cover - repr symmetry
        return f"JobMissingOutcome(job_id={self.job_id!r})"


@dataclass(frozen=True)
class StepNotReadyOutcome:
    """Typed NOT_READY result: the job exists, no step may run right now."""

    job_id: str
    reason: str

    def __post_init__(self) -> None:
        if self.reason not in NOT_READY_REASONS:
            raise ValueError(
                f"reason {self.reason!r} is not one of {NOT_READY_REASONS}; "
                "an unexplained not-ready is the defect this record exists to prevent"
            )

    @property
    def standing(self) -> str:
        """The canon 15.12 error-model category this outcome reports."""
        return "CONTRACT_NOT_READY"

    def message(self) -> str:
        return f"job {self.job_id!r} is not ready to run a step: {self.reason}"

    def __repr__(self) -> str:  # pragma: no cover - repr symmetry
        return f"StepNotReadyOutcome(job_id={self.job_id!r}, reason={self.reason!r})"
