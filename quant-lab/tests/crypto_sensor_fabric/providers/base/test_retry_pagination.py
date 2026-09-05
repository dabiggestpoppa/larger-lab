"""SENSOR-B3-I03 — retry classification, backoff, rate-limit, pagination, resume.

All offline: backoff math is asserted directly (no wall-clock sleeps), rate
limits are built from synthetic headers, and pagination protection is tested
with fake cursors/hashes/timestamps.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import (
    DuplicateAnnotation,
    PaginationMode,
    Retryability,
)
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    CapabilityUnavailable,
    GeoRestricted,
    PaginationFailure,
    ProviderUnavailable,
    RateLimited,
    TransportFailure,
)
from crypto_sensor_fabric.providers.base.models import ResumeToken
from crypto_sensor_fabric.providers.base.pagination import (
    CursorTracker,
    completion_from_provider_semantics,
    resume_token_round_trip,
)
from crypto_sensor_fabric.providers.base.rate_limit import (
    rate_limit_from_headers,
    unknown_rate_limit,
)
from crypto_sensor_fabric.providers.base.retry import (
    RetryPolicy,
    classify_retryability,
    is_retryable,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class TestRetryClassification:
    def test_transport_retryable(self) -> None:
        error = TransportFailure(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        )
        assert classify_retryability(error) is Retryability.RETRYABLE

    def test_rate_limited_retryable(self) -> None:
        error = RateLimited(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        )
        assert classify_retryability(error) is Retryability.RETRYABLE

    def test_provider_unavailable_retryable(self) -> None:
        error = ProviderUnavailable(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        )
        assert classify_retryability(error) is Retryability.RETRYABLE

    def test_geo_never_retryable(self) -> None:
        error = GeoRestricted(
            provider_id="BINANCE_USDM",
            sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        )
        assert classify_retryability(error) is Retryability.TERMINAL
        assert not is_retryable(error, RetryPolicy())

    def test_access_violation_terminal(self) -> None:
        error = AccessClassViolation(
            provider_id="X", sensor_family=SensorFamily.MECHANICAL_TRADE
        )
        assert classify_retryability(error) is Retryability.TERMINAL

    def test_capability_unavailable_terminal(self) -> None:
        error = CapabilityUnavailable(
            provider_id="X", sensor_family=SensorFamily.MECHANICAL_BASIS
        )
        assert classify_retryability(error) is Retryability.TERMINAL

    def test_explicit_retryability_overrides(self) -> None:
        error = TransportFailure(
            provider_id="X",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            retryability=Retryability.TERMINAL,
        )
        assert classify_retryability(error) is Retryability.TERMINAL


class TestBackoffPolicy:
    def test_bounded_exponential_growth(self) -> None:
        policy = RetryPolicy(
            max_attempts=4, base_delay_seconds=1.0, max_delay_seconds=8.0, jitter=False
        )
        assert policy.delay_for_attempt(0) == pytest.approx(1.0)
        assert policy.delay_for_attempt(1) == pytest.approx(2.0)
        assert policy.delay_for_attempt(2) == pytest.approx(4.0)
        # clamped at max
        assert policy.delay_for_attempt(10) == pytest.approx(8.0)

    def test_retry_after_overrides(self) -> None:
        policy = RetryPolicy(
            base_delay_seconds=0.1, jitter=False, retry_after_seconds=5.0
        )
        assert policy.delay_for_attempt(0) == pytest.approx(5.0)

    def test_budget_exhaustion(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0)
        assert policy.should_retry(1)
        assert policy.should_retry(2)
        assert not policy.should_retry(3)

    def test_jitter_bounds(self) -> None:
        policy = RetryPolicy(base_delay_seconds=2.0, jitter=True)
        rng = random.Random(42)
        values = [policy.delay_for_attempt(0, rng) for _ in range(50)]
        assert all(1.0 <= v <= 3.0 for v in values)  # base * [0.5, 1.0]


class TestRateLimitSnapshot:
    def test_parses_headers(self) -> None:
        snapshot = rate_limit_from_headers(
            {
                "X-RateLimit-Limit": "600",
                "X-RateLimit-Remaining": "512",
                "X-RateLimit-Reset": "1767225600",
                "Retry-After": "7",
            },
            now=NOW,
        )
        assert snapshot.limit_known
        assert snapshot.limit_capacity == 600
        assert snapshot.limit_remaining == 512
        assert snapshot.retry_after_seconds == 7.0

    def test_unknown_when_headers_absent(self) -> None:
        snapshot = rate_limit_from_headers({}, now=NOW)
        assert not snapshot.limit_known
        assert snapshot.limit_capacity is None

    def test_unknown_explicit(self) -> None:
        snapshot = unknown_rate_limit()
        assert not snapshot.limit_known

    def test_missing_remaining_means_unknown(self) -> None:
        snapshot = rate_limit_from_headers(
            {"X-RateLimit-Limit": "600"}, now=NOW
        )
        assert not snapshot.limit_known


class TestCursorLoopProtection:
    def test_repeated_cursor_raises(self) -> None:
        tracker = CursorTracker(
            "KRAKEN_FUTURES", SensorFamily.MECHANICAL_OPEN_INTEREST
        )
        tracker.observe_page(1, "cursor-1", "hash-1", NOW)
        tracker.observe_page(2, "cursor-2", "hash-2", NOW.replace(hour=1))
        with pytest.raises(PaginationFailure):
            tracker.observe_page(3, "cursor-1", "hash-3", NOW.replace(hour=2))

    def test_repeated_content_hash_flagged(self) -> None:
        tracker = CursorTracker("OKX_SWAP")
        annotations = tracker.observe_page(1, "c1", "same-hash", NOW)
        annotations = tracker.observe_page(2, "c2", "same-hash", NOW.replace(hour=1))
        assert annotations and DuplicateAnnotation.REPEATED_PAGE in annotations

    def test_non_monotonic_timestamp_raises(self) -> None:
        tracker = CursorTracker("GATE_FUTURES")
        tracker.observe_page(1, "c1", "h1", NOW.replace(hour=2))
        with pytest.raises(PaginationFailure):
            tracker.observe_page(2, "c2", "h2", NOW.replace(hour=1))

    def test_overlap_allowed_annotates_duplicate(self) -> None:
        tracker = CursorTracker("GATE_FUTURES")
        tracker.observe_page(1, "c1", "h1", NOW.replace(hour=2))
        annotations = tracker.observe_page(
            2,
            "c2",
            "h2",
            NOW.replace(hour=1),
            allow_timestamp_reversal_overlap=True,
        )
        assert annotations and DuplicateAnnotation.POSSIBLE_DUPLICATE in annotations

    def test_monotonic_traversal_clean(self) -> None:
        tracker = CursorTracker("DERIBIT")
        result = tracker.observe_page(1, "c1", "h1", NOW)
        result = tracker.observe_page(2, "c2", "h2", NOW.replace(hour=1))
        assert result is None or DuplicateAnnotation.REPEATED_PAGE not in result


class TestResumeToken:
    def test_roundtrip_deterministic(self) -> None:
        token = ResumeToken(
            mode=PaginationMode.CURSOR,
            provider_cursor="abc",
            page_number=4,
            last_timestamp=NOW,
            last_native_id="id-7",
            provider_native_state={"next": "xyz"},
        )
        assert resume_token_round_trip(token) == token

    def test_roundtrip_identity_preserved(self) -> None:
        token = ResumeToken(mode=PaginationMode.TIME_RANGE, last_timestamp=NOW)
        rebuilt = resume_token_round_trip(token)
        assert rebuilt.mode is PaginationMode.TIME_RANGE
        assert rebuilt.last_timestamp == NOW


class TestCompletionSemantics:
    def test_provider_says_more_means_incomplete(self) -> None:
        assert not completion_from_provider_semantics(
            page_size_hint=1000,
            rows_returned=1000,
            provider_says_more=True,
            cursor_advances=True,
        )

    def test_provider_says_done_means_complete(self) -> None:
        assert completion_from_provider_semantics(
            page_size_hint=1000,
            rows_returned=100,
            provider_says_more=False,
            cursor_advances=False,
        )

    def test_short_page_is_not_completion_without_signal(self) -> None:
        assert not completion_from_provider_semantics(
            page_size_hint=1000,
            rows_returned=100,
            provider_says_more=None,
            cursor_advances=True,
        )
