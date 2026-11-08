"""Typed worker-availability outcome (P2-R3-C02).

A lease may be granted only when a compatible registered worker exists.
Without one, the eligible step stays READY, nothing is leased, and the
caller receives a typed ``WORKER_UNAVAILABLE`` outcome — never a claim,
an attempt, an event, or a budget charge (operator-loop finding B).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qcae.core.errors import QcaeValidationError

__all__ = ["WorkerUnavailableError", "WorkerAvailability", "WorkerUnavailable", "NoRunnableStep"]


class WorkerUnavailableError(RuntimeError):
    """Raised where an operator action requires a worker that does not exist.

    This is an expected operator outcome, not a programming defect: the CLI
    maps it to a stable exit code and a concise message (P2-R3-C05), so it
    must never surface as a raw traceback.
    """


@dataclass(frozen=True)
class WorkerAvailability:
    """Durable-less availability probe result for one job's eligible steps."""

    eligible_step_ids: tuple
    covered_step_ids: tuple
    uncovered_step_ids: tuple
    missing_step_types: tuple


class WorkerUnavailable:
    """Typed no-worker result (truth without an exception path)."""

    REASON = "WORKER_UNAVAILABLE"

    def __init__(self, job_id: str, missing_step_types: tuple) -> None:
        self.job_id = job_id
        self.missing_step_types = tuple(missing_step_types)

    @property
    def reason(self) -> str:
        return self.REASON

    def message(self) -> str:
        types = ", ".join(sorted(set(self.missing_step_types))) or "<none>"
        return (
            f"WORKER_UNAVAILABLE: no registered worker for step type(s) {types}; "
            f"nothing leased, step remains READY"
        )

    def __repr__(self) -> str:  # pragma: no cover - repr symmetry
        return f"WorkerUnavailable(job_id={self.job_id!r}, missing={self.missing_step_types!r})"


class NoRunnableStep:
    """Typed no-runnable-step outcome (P2-R5-C06).

    Distinct from WORKER_UNAVAILABLE (exit 3): the step exists and may even
    be covered by a worker, but something about its schedule, state, or the
    job itself means nothing can be leased right now. Carries a classified
    reason so the operator (CLI exit 5) never confuses "nothing to do" with
    an unknown or terminal job.
    """

    REASON = "NO_RUNNABLE_STEP"

    #: One of FUTURE_NOT_BEFORE, DEPENDENCY_PENDING, WAITING_POLICY,
    #: WAITING_INPUT, ACTIVE_LEASE, TERMINAL_JOB, UNKNOWN_JOB,
    #: or the generic NO_RUNNABLE_STEP.
    REASONS = (
        "FUTURE_NOT_BEFORE", "DEPENDENCY_PENDING", "WAITING_POLICY",
        "WAITING_INPUT", "ACTIVE_LEASE", "TERMINAL_JOB", "UNKNOWN_JOB",
    )

    def __init__(self, job_id: str, reason: str) -> None:
        if reason not in self.REASONS:
            raise QcaeValidationError(
                f"no_runnable reason must be one of {self.REASONS}, got {reason!r}"
            )
        self.job_id = job_id
        self.reason = reason

    @property
    def reason(self) -> str:
        return self._reason

    @reason.setter
    def reason(self, value: str) -> None:
        if value not in self.REASONS:
            raise QcaeValidationError(
                f"no_runnable reason must be one of {self.REASONS}, got {value!r}"
            )
        self._reason = value

    def message(self) -> str:
        return (
            f"NO_RUNNABLE_STEP: {self.reason} for job {self.job_id}; "
            f"nothing leased, nothing attempted"
        )

    def __repr__(self) -> str:  # pragma: no cover - repr symmetry
        return f"NoRunnableStep(job_id={self.job_id!r}, reason={self.reason!r})"


def worker_availability_for(engine, job_id: str) -> WorkerAvailability:
    """Classify one job's currently-claimable steps by worker coverage.

    Uses the engine's public registry surface; P3 supplies the first real
    discovery workers, so an empty registry is a normal runtime state that
    must be reportable, not an exception.
    """
    registered = set(engine.registered_worker_types())
    eligible = engine.eligible_steps_for_claim(job_id)
    covered: list = []
    uncovered: list = []
    missing: set = set()
    for step in eligible:
        if step.step_type in registered:
            covered.append(step.step_id)
        else:
            uncovered.append(step.step_id)
            missing.add(step.step_type)
    return WorkerAvailability(
        eligible_step_ids=tuple(s.step_id for s in eligible),
        covered_step_ids=tuple(covered),
        uncovered_step_ids=tuple(uncovered),
        missing_step_types=tuple(sorted(missing)),
    )
