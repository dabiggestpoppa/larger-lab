"""Normalized rate-limit telemetry (01 §12 / 03 §10, SENSOR-B3-I03).

`RateLimitSnapshot` (models.py) is the serialized form; this module builds it
from common provider headers (X-RateLimit-*, Retry-After) with an explicit
UNKNOWN default.  No rate-limit numbers are ever invented.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .models import RateLimitSnapshot


def rate_limit_from_headers(
    headers: dict[str, str] | None,
    *,
    capacity_header: str = "X-RateLimit-Limit",
    remaining_header: str = "X-RateLimit-Remaining",
    reset_header: str = "X-RateLimit-Reset",
    retry_after_header: str = "Retry-After",
    now: datetime | None = None,
) -> RateLimitSnapshot:
    """Build a RateLimitSnapshot from provider response headers.

    Header naming differs across providers; adapters pass their own header
    names.  Missing/unknown values stay None with limit_known=False.
    """
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    capacity_raw = headers.get(capacity_header.lower())
    remaining_raw = headers.get(remaining_header.lower())
    reset_raw = headers.get(reset_header.lower())
    retry_after_raw = headers.get(retry_after_header.lower())

    def _int_or_none(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    capacity = _int_or_none(capacity_raw)
    remaining = _int_or_none(remaining_raw)

    reset_at: datetime | None = None
    now = now or datetime.now(UTC)
    if reset_raw is not None:
        # provider may send epoch seconds or a delay
        try:
            reset_epoch = float(reset_raw)
            if reset_epoch < 1e12:  # seconds
                reset_at = datetime.fromtimestamp(reset_epoch, tz=UTC)
            else:  # milliseconds
                reset_at = datetime.fromtimestamp(reset_epoch / 1000, tz=UTC)
        except (ValueError, OSError, OverflowError):
            reset_at = None

    retry_after_seconds: float | None = None
    if retry_after_raw is not None:
        try:
            retry_after_seconds = float(retry_after_raw)
        except ValueError:
            retry_after_seconds = None

    return RateLimitSnapshot(
        limit_known=capacity is not None and remaining is not None,
        limit_capacity=capacity,
        limit_remaining=remaining,
        reset_at=reset_at,
        retry_after_seconds=retry_after_seconds,
        provider_native_headers={
            k: v for k, v in headers.items() if "ratelimit" in k or "retry" in k
        },
    )


def unknown_rate_limit() -> RateLimitSnapshot:
    """Explicit UNKNOWN rate-limit state (never invented numbers)."""
    return RateLimitSnapshot(limit_known=False)
