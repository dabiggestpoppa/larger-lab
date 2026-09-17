"""Failure classification, retry/hard-block semantics and missingness mapping
(03 §5-6 / T2-FREE-01..06, failure-class tests).

Every failure maps to one controlled `ProbeFailureClass` and retains redacted
provider-native detail.  Hard access blocks (payment/geo/auth) are never
auto-retried as if transient.
"""

from __future__ import annotations

from .enums import (
    CapabilityMissingness,
    ProbeFailureClass,
    ProbeFailureFamily,
)
from .models import missingness_to_bloc1_reason

#: family for every failure class.
FAILURE_FAMILY: dict[ProbeFailureClass, ProbeFailureFamily] = {
    ProbeFailureClass.F_ACCESS_GEO: ProbeFailureFamily.ACCESS,
    ProbeFailureClass.F_ACCESS_AUTH: ProbeFailureFamily.ACCESS,
    ProbeFailureClass.F_ACCESS_PAYMENT: ProbeFailureFamily.ACCESS,
    ProbeFailureClass.F_ACCESS_RATE_LIMIT: ProbeFailureFamily.ACCESS,
    ProbeFailureClass.F_NETWORK_TIMEOUT: ProbeFailureFamily.NETWORK_SERVER,
    ProbeFailureClass.F_NETWORK_DNS: ProbeFailureFamily.NETWORK_SERVER,
    ProbeFailureClass.F_NETWORK_TLS: ProbeFailureFamily.NETWORK_SERVER,
    ProbeFailureClass.F_SERVER_5XX: ProbeFailureFamily.NETWORK_SERVER,
    ProbeFailureClass.F_CLIENT_4XX: ProbeFailureFamily.NETWORK_SERVER,
    ProbeFailureClass.F_ENDPOINT_REMOVED: ProbeFailureFamily.ENDPOINT_ARCHIVE,
    ProbeFailureClass.F_ARCHIVE_NOT_FOUND: ProbeFailureFamily.ENDPOINT_ARCHIVE,
    ProbeFailureClass.F_SYMBOL_NOT_FOUND: ProbeFailureFamily.SYMBOL_LISTING,
    ProbeFailureClass.F_PRE_LISTING: ProbeFailureFamily.SYMBOL_LISTING,
    ProbeFailureClass.F_HISTORY_TRUNCATED: ProbeFailureFamily.HISTORY,
    ProbeFailureClass.F_EMPTY_VALID_WINDOW: ProbeFailureFamily.HISTORY,
    ProbeFailureClass.F_PAGINATION_LOOP: ProbeFailureFamily.PAGINATION,
    ProbeFailureClass.F_PAGINATION_TRUNCATED: ProbeFailureFamily.PAGINATION,
    ProbeFailureClass.F_SCHEMA_CHANGED: ProbeFailureFamily.SCHEMA,
    ProbeFailureClass.F_TIMESTAMP_UNCLEAR: ProbeFailureFamily.SEMANTIC,
    ProbeFailureClass.F_UNIT_UNCLEAR: ProbeFailureFamily.SEMANTIC,
    ProbeFailureClass.F_METHOD_UNCLEAR: ProbeFailureFamily.SEMANTIC,
    ProbeFailureClass.F_DUPLICATE_EXCESS: ProbeFailureFamily.QUALITY_CORRUPTION,
    ProbeFailureClass.F_GAP_EXCESS: ProbeFailureFamily.QUALITY_CORRUPTION,
    ProbeFailureClass.F_CHECKSUM_FAILURE: ProbeFailureFamily.QUALITY_CORRUPTION,
    ProbeFailureClass.F_PAYLOAD_CORRUPT: ProbeFailureFamily.QUALITY_CORRUPTION,
    ProbeFailureClass.F_QUOTA_EXHAUSTED: ProbeFailureFamily.ACCESS,
    ProbeFailureClass.F_DOC_RUNTIME_CONTRADICTION: (
        ProbeFailureFamily.DOC_RUNTIME_CONTRADICTION
    ),
    ProbeFailureClass.F_UNSUPPORTED_SENSOR: ProbeFailureFamily.UNSUPPORTED,
    ProbeFailureClass.F_UNKNOWN: ProbeFailureFamily.UNSUPPORTED,
}

#: Transient failures may be retried conservatively.
RETRYABLE: frozenset[ProbeFailureClass] = frozenset(
    {
        ProbeFailureClass.F_NETWORK_TIMEOUT,
        ProbeFailureClass.F_NETWORK_DNS,
        ProbeFailureClass.F_NETWORK_TLS,
        ProbeFailureClass.F_SERVER_5XX,
        ProbeFailureClass.F_ACCESS_RATE_LIMIT,
        ProbeFailureClass.F_QUOTA_EXHAUSTED,
    }
)

#: Hard blocks are deterministic access/support conditions; never retried
#: automatically, never bypassed.
HARD_BLOCK: frozenset[ProbeFailureClass] = frozenset(
    {
        ProbeFailureClass.F_ACCESS_GEO,
        ProbeFailureClass.F_ACCESS_AUTH,
        ProbeFailureClass.F_ACCESS_PAYMENT,
        ProbeFailureClass.F_ENDPOINT_REMOVED,
        ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
        ProbeFailureClass.F_UNSUPPORTED_SENSOR,
        ProbeFailureClass.F_CHECKSUM_FAILURE,
    }
)

#: failure class -> probe-layer missingness (03 §6).
FAILURE_MISSINGNESS: dict[ProbeFailureClass, CapabilityMissingness | None] = {
    ProbeFailureClass.F_PRE_LISTING: CapabilityMissingness.PRE_LISTING,
    ProbeFailureClass.F_SYMBOL_NOT_FOUND: CapabilityMissingness.UNSUPPORTED_INSTRUMENT,
    ProbeFailureClass.F_HISTORY_TRUNCATED: CapabilityMissingness.OUTSIDE_PROVIDER_RETENTION,
    ProbeFailureClass.F_ACCESS_PAYMENT: CapabilityMissingness.PAYMENT_BLOCKED,
    ProbeFailureClass.F_ACCESS_GEO: CapabilityMissingness.GEO_BLOCKED,
    ProbeFailureClass.F_ACCESS_AUTH: CapabilityMissingness.AUTH_BLOCKED,
    ProbeFailureClass.F_ACCESS_RATE_LIMIT: CapabilityMissingness.RATE_LIMITED,
    ProbeFailureClass.F_QUOTA_EXHAUSTED: CapabilityMissingness.RATE_LIMITED,
    ProbeFailureClass.F_UNSUPPORTED_SENSOR: CapabilityMissingness.SENSOR_NOT_SUPPORTED,
    ProbeFailureClass.F_SCHEMA_CHANGED: CapabilityMissingness.PROVIDER_SCHEMA_BREAK,
    ProbeFailureClass.F_ENDPOINT_REMOVED: CapabilityMissingness.ENDPOINT_UNAVAILABLE,
    ProbeFailureClass.F_ARCHIVE_NOT_FOUND: CapabilityMissingness.ENDPOINT_UNAVAILABLE,
    ProbeFailureClass.F_PAYLOAD_CORRUPT: CapabilityMissingness.DATA_BLOCKED,
    ProbeFailureClass.F_CHECKSUM_FAILURE: CapabilityMissingness.DATA_BLOCKED,
    ProbeFailureClass.F_PAGINATION_LOOP: CapabilityMissingness.DATA_BLOCKED,
    ProbeFailureClass.F_PAGINATION_TRUNCATED: CapabilityMissingness.PROVIDER_GAP,
    ProbeFailureClass.F_GAP_EXCESS: CapabilityMissingness.PROVIDER_GAP,
    ProbeFailureClass.F_EMPTY_VALID_WINDOW: CapabilityMissingness.OUTSIDE_PROVIDER_RETENTION,
}


def failure_family(cls: ProbeFailureClass) -> ProbeFailureFamily:
    return FAILURE_FAMILY.get(cls, ProbeFailureFamily.UNSUPPORTED)


def is_retryable(cls: ProbeFailureClass) -> bool:
    return cls in RETRYABLE


def is_hard_block(cls: ProbeFailureClass) -> bool:
    return cls in HARD_BLOCK


def failure_to_missingness(
    cls: ProbeFailureClass,
) -> CapabilityMissingness | None:
    return FAILURE_MISSINGNESS.get(cls)


def failure_to_bloc1_missing_reason(
    cls: ProbeFailureClass,
) -> tuple[object | None, str | None]:
    """Map a failure class toward Bloc 1 MissingReason at handoff.

    Returns (reason | None, note | None); a None reason means the distinction
    has no faithful Bloc 1 member and must be carried at the probe layer with
    the BLOC5_SCHEMA_REFINEMENT_PENDING note.
    """
    missingness = failure_to_missingness(cls)
    if missingness is None:
        return None, f"no missingness mapping for {cls.value}"
    return missingness_to_bloc1_reason(missingness)


def classify_http_status(
    status: int,
    provider_native_detail: str | None = None,
) -> ProbeFailureClass:
    """Common HTTP status -> failure class mapping (provider modules may refine)."""
    if status == 401 or status == 403:
        return ProbeFailureClass.F_ACCESS_AUTH
    if status == 404:
        return ProbeFailureClass.F_ENDPOINT_REMOVED
    if status == 429:
        return ProbeFailureClass.F_ACCESS_RATE_LIMIT
    if status == 451:
        return ProbeFailureClass.F_ACCESS_GEO
    if status >= 500:
        return ProbeFailureClass.F_SERVER_5XX
    if status >= 400:
        return ProbeFailureClass.F_CLIENT_4XX
    return ProbeFailureClass.F_UNKNOWN
