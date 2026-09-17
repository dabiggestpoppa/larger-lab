"""Typed retry model (01 §13-§14 / 03 §10, SENSOR-B3-I03).

Retry classification maps a typed failure to RETRYABLE / TERMINAL / UNKNOWN.
Geo/access/payment restrictions are NEVER retried as transient (03 §12-§13).
Backoff is bounded exponential + jitter; Retry-After is honored when
supplied; no infinite loops; retries stop at a per-request budget.

Tests use a fake clock — no real wall-clock sleeps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .enums import Retryability
from .errors import (
    AccessClassViolation,
    AcquisitionError,
    ArchiveIntegrityFailure,
    AuthenticationRequired,
    CapabilityUnavailable,
    GeoRestricted,
    HistoricalRangeUnavailable,
    InvalidInstrument,
    PaginationFailure,
    ProviderUnavailable,
    ProviderSemanticError,
    RateLimited,
    RetryExhausted,
    SchemaDrift,
    TransportFailure,
    UnsupportedGranularity,
)

#: Typed failures that are genuinely transient and may be retried
#: conservatively (01 §13).
RETRYABLE_ERROR_TYPES: frozenset[str] = frozenset(
    {
        ProviderUnavailable.failure_type,
        TransportFailure.failure_type,
        RateLimited.failure_type,
        # RetryExhausted itself is terminal for the request, never re-retried.
    }
)

#: Typed failures that are terminal for the request (01 §13).
TERMINAL_ERROR_TYPES: frozenset[str] = frozenset(
    {
        AccessClassViolation.failure_type,
        AuthenticationRequired.failure_type,
        CapabilityUnavailable.failure_type,
        GeoRestricted.failure_type,
        InvalidInstrument.failure_type,
        UnsupportedGranularity.failure_type,
        HistoricalRangeUnavailable.failure_type,
        PaginationFailure.failure_type,
        ArchiveIntegrityFailure.failure_type,
        SchemaDrift.failure_type,
        ProviderSemanticError.failure_type,
        RetryExhausted.failure_type,
    }
)


def classify_retryability(error: AcquisitionError) -> Retryability:
    """Retry classification of one typed failure (01 §13)."""
    if error.retryability is not Retryability.UNKNOWN:
        return error.retryability
    if error.failure_type in RETRYABLE_ERROR_TYPES:
        return Retryability.RETRYABLE
    if error.failure_type in TERMINAL_ERROR_TYPES:
        return Retryability.TERMINAL
    return Retryability.UNKNOWN


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff policy (01 §14)."""

    max_attempts: int = 3  # attempt + up to 2 retries
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    jitter: bool = True
    retry_after_seconds: float | None = None  # provider Retry-After override

    def delay_for_attempt(self, attempt: int, rng: random.Random | None = None) -> float:
        """Delay before the given retry attempt (attempt 0 = first retry).

        Exponential: base * 2^attempt, clamped to max_delay_seconds.
        Optional jitter smooths synchronized retry storms.
        """
        raw = self.base_delay_seconds * (2 ** max(attempt, 0))
        raw = min(raw, self.max_delay_seconds)
        if self.retry_after_seconds is not None:
            raw = max(raw, self.retry_after_seconds)
        if self.jitter and rng is not None:
            raw = raw * (0.5 + rng.random() * 0.5)
        elif self.jitter:
            raw = raw * (0.5 + random.random() * 0.5)
        return raw

    def should_retry(self, attempt: int) -> bool:
        """Whether another attempt is allowed after `attempt` previous failures.

        attempt counts completed attempts; a new attempt is allowed while
        attempt < max_attempts.
        """
        return attempt < self.max_attempts


def is_retryable(error: AcquisitionError, policy: RetryPolicy) -> bool:
    """True when this failure may be retried under the policy."""
    if classify_retryability(error) is Retryability.TERMINAL:
        return False
    return policy.max_attempts > 1
