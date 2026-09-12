"""Probe runner lifecycle (bloc_02/01 §28-29, 04 §20, T2-PLAN-02).

Sequential, low-concurrency, deterministic execution:

- recent control steps run first; a hard-blocked recent control suppresses the
  deep-history steps for the same (provider, sensor, instrument, granularity)
  scope (F2.7 / T2-PLAN-02)
- retryable failures retried conservatively (default one retry), respecting
  Retry-After when present in rate-limit metadata
- hard blocks (payment/geo/auth/unsupported) are never retried
- every executed step emits an immutable CapabilityProbeAttempt (T2-MODEL-05)

The executor boundary is provider-specific; the runner stays provider-agnostic.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Protocol

from .enums import ProbeRunStatus, ResponseStatusClass
from .failures import is_hard_block, is_retryable
from .models import CapabilityProbeAttempt, CapabilityProbeRequest, ProbeRunResult
from .planner import ProbePlan

ProbeExecutor = Callable[[CapabilityProbeRequest], list[CapabilityProbeAttempt]]


class Executor(Protocol):
    """Provider-specific probe execution boundary."""

    def execute(self, request: CapabilityProbeRequest) -> list[CapabilityProbeAttempt]:
        """Execute one request; may traverse pagination, returning one attempt
        per page or a single summarized attempt."""
        ...


def _scope_key(request: CapabilityProbeRequest) -> tuple[str, str, str, str]:
    return (
        request.provider_id,
        request.sensor_family.value,
        request.instrument_native,
        request.requested_granularity.value,
    )


def _last_attempt(attempts: Sequence[CapabilityProbeAttempt]) -> CapabilityProbeAttempt:
    return attempts[-1]


def _stamp_era(
    attempts: Sequence[CapabilityProbeAttempt], era: str | None
) -> list[CapabilityProbeAttempt]:
    """Stamp the checkpoint era into attempts that do not already carry one.

    Evidence synthesis groups attempts by era (RECENT_CONTROL / 2021 / ...),
    so the runner guarantees the label survives regardless of executor detail.
    """
    if era is None:
        return list(attempts)
    stamped: list[CapabilityProbeAttempt] = []
    for attempt in attempts:
        if attempt.era_hint:
            stamped.append(attempt)
        else:
            stamped.append(attempt.model_copy(update={"era_hint": era}))
    return stamped


def run_plan(
    plan: ProbePlan,
    executor: Executor,
    probe_run_id: str,
    probe_version: str,
    retry_count: int = 1,
    now: datetime | None = None,
) -> ProbeRunResult:
    """Execute a plan deterministically with recent-control-first suppression."""
    started = now or datetime.now(UTC)
    result = ProbeRunResult(
        probe_run_id=probe_run_id,
        run_status=ProbeRunStatus.PARTIAL,
        started_at=started,
        probe_version=probe_version,
    )
    hard_blocked_scopes: set[tuple[str, str, str, str]] = set()
    executed_count = 0
    failed_final_count = 0
    transient_abort = False

    # Recent control first.
    for step in plan.recent_control_steps():
        attempts = _stamp_era(_execute_with_retry(step.request, executor, retry_count), step.era)
        result.attempts.extend(attempts)
        executed_count += 1
        last = _last_attempt(attempts)
        if last.response_status_class is ResponseStatusClass.FAILED:
            failed_final_count += 1
            if last.error_class is not None and is_hard_block(last.error_class):
                hard_blocked_scopes.add(_scope_key(step.request))
            elif last.error_class is not None and is_retryable(last.error_class):
                transient_abort = True

    # Historical steps, skipping scopes that hard-blocked at recent control.
    skipped: list[str] = []
    for step in plan.historical_steps():
        if _scope_key(step.request) in hard_blocked_scopes:
            skipped.append(step.probe_id)
            continue
        attempts = _stamp_era(_execute_with_retry(step.request, executor, retry_count), step.era)
        result.attempts.extend(attempts)
        executed_count += 1
        last = _last_attempt(attempts)
        if last.response_status_class is ResponseStatusClass.FAILED:
            failed_final_count += 1
            if last.error_class is not None and is_hard_block(last.error_class):
                hard_blocked_scopes.add(_scope_key(step.request))
            elif last.error_class is not None and is_retryable(last.error_class):
                transient_abort = True

    result.planned_but_skipped = skipped
    result.finished_at = datetime.now(UTC)
    result.run_status = _run_status(
        executed_count,
        failed_final_count,
        hard_blocked_scopes,
        transient_abort,
        skipped,
    )
    return result


def _execute_with_retry(
    request: CapabilityProbeRequest,
    executor: Executor,
    retry_count: int,
) -> list[CapabilityProbeAttempt]:
    attempts = list(executor.execute(request))
    if not attempts:
        # Executor contract violation: every request must emit evidence.
        raise RuntimeError(
            f"executor returned no attempts for probe {request.provider_id}/"
            f"{request.sensor_family.value}"
        )
    last = _last_attempt(attempts)
    remaining = retry_count
    while (
        remaining > 0
        and last.response_status_class is ResponseStatusClass.FAILED
        and last.error_class is not None
        and is_retryable(last.error_class)
    ):
        retry_attempts = list(executor.execute(request))
        attempts.extend(retry_attempts)
        last = _last_attempt(retry_attempts)
        remaining -= 1
    return attempts


def _run_status(
    executed_count: int,
    failed_final_count: int,
    hard_blocked_scopes: set[tuple[str, str, str, str]],
    transient_abort: bool,
    skipped: list[str],
) -> ProbeRunStatus:
    """Derive run status from final outcomes, not raw attempt counts.

    A retryable failure that succeeded on retry does not count as a
    limitation; only requests whose FINAL attempt failed contribute.
    """
    all_failed = executed_count > 0 and failed_final_count == executed_count
    if all_failed and hard_blocked_scopes:
        return ProbeRunStatus.ABORTED_HARD_BLOCK
    if all_failed and transient_abort:
        return ProbeRunStatus.ABORTED_TRANSIENT
    if skipped or failed_final_count:
        return ProbeRunStatus.COMPLETE_WITH_LIMITATIONS
    if executed_count:
        return ProbeRunStatus.COMPLETE
    return ProbeRunStatus.PARTIAL


def analyze_cursor_sequence(
    cursors: Sequence[str | None],
) -> tuple[bool, bool | None]:
    """Analyze a pagination cursor sequence.

    Returns (loop_detected, complete).

    - a repeated non-null cursor is F_PAGINATION_LOOP territory (loop=True)
    - termination at a null/absent cursor with no loop means complete=True
    - a non-null trailing cursor with no loop means complete=False (more pages)
    """
    if not cursors:
        return False, None
    seen: set[str] = set()
    for cursor in cursors:
        if cursor is None:
            return False, True
        if cursor in seen:
            return True, False
        seen.add(cursor)
    return False, False
