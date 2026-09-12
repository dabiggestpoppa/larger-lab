"""Failure-class and redaction tests (04 §12-13, T2-MODEL-04)."""

from __future__ import annotations

from crypto_sensor_fabric.probes.enums import (
    CapabilityMissingness,
    ProbeFailureClass,
    ProbeFailureFamily,
)
from crypto_sensor_fabric.probes.failures import (
    classify_http_status,
    failure_family,
    failure_to_bloc1_missing_reason,
    failure_to_missingness,
    is_hard_block,
    is_retryable,
)
from crypto_sensor_fabric.probes.redaction import (
    redact_mapping,
    redact_url,
    redact_value,
    scrub_secrets,
)

ALL_FAILURE_CLASSES = list(ProbeFailureClass)


def test_every_failure_class_has_a_family():
    for cls in ALL_FAILURE_CLASSES:
        assert failure_family(cls) in ProbeFailureFamily, cls.value


def test_every_failure_class_maps_to_missingness_or_none():
    for cls in ALL_FAILURE_CLASSES:
        result = failure_to_missingness(cls)
        assert result is None or isinstance(result, CapabilityMissingness)


def test_retryable_transient_classes():
    for cls in (
        ProbeFailureClass.F_NETWORK_TIMEOUT,
        ProbeFailureClass.F_SERVER_5XX,
        ProbeFailureClass.F_ACCESS_RATE_LIMIT,
        ProbeFailureClass.F_QUOTA_EXHAUSTED,
    ):
        assert is_retryable(cls)
        assert not is_hard_block(cls)


def test_hard_blocks_never_retried():
    for cls in (
        ProbeFailureClass.F_ACCESS_PAYMENT,
        ProbeFailureClass.F_ACCESS_GEO,
        ProbeFailureClass.F_ACCESS_AUTH,
        ProbeFailureClass.F_UNSUPPORTED_SENSOR,
        ProbeFailureClass.F_CHECKSUM_FAILURE,
    ):
        assert is_hard_block(cls)
        assert not is_retryable(cls)


def test_pre_listing_is_instrument_state_not_provider_block():
    assert not is_hard_block(ProbeFailureClass.F_PRE_LISTING)
    assert not is_retryable(ProbeFailureClass.F_PRE_LISTING)
    assert failure_to_missingness(ProbeFailureClass.F_PRE_LISTING) is (
        CapabilityMissingness.PRE_LISTING
    )


def test_http_status_classification():
    assert classify_http_status(401) is ProbeFailureClass.F_ACCESS_AUTH
    assert classify_http_status(403) is ProbeFailureClass.F_ACCESS_AUTH
    assert classify_http_status(404) is ProbeFailureClass.F_ENDPOINT_REMOVED
    assert classify_http_status(429) is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    assert classify_http_status(451) is ProbeFailureClass.F_ACCESS_GEO
    assert classify_http_status(500) is ProbeFailureClass.F_SERVER_5XX
    assert classify_http_status(422) is ProbeFailureClass.F_CLIENT_4XX
    assert classify_http_status(200) is ProbeFailureClass.F_UNKNOWN


def test_failure_maps_to_bloc1_missingness():
    reason, note = failure_to_bloc1_missing_reason(
        ProbeFailureClass.F_HISTORY_TRUNCATED
    )
    assert reason is not None
    assert note is None


def test_payment_blocked_has_no_faithful_bloc1_member():
    reason, note = failure_to_bloc1_missing_reason(
        ProbeFailureClass.F_ACCESS_PAYMENT
    )
    assert reason is None
    assert "BLOC5_SCHEMA_REFINEMENT_PENDING" in (note or "")


# ---------------------------------------------------------------------------
# Redaction (T2-MODEL-04)
# ---------------------------------------------------------------------------


def test_redact_value_by_secret_key():
    assert redact_value("api_key", "sk_live_1234567890abcdef") == "***REDACTED***"
    assert redact_value("Authorization", "Bearer abc") == "***REDACTED***"
    assert redact_value("symbol", "BTC") == "BTC"


def test_redact_headers():
    headers = {
        "X-API-Key": "fake-key-123",
        "Authorization": "Bearer fake-token",
        "User-Agent": "sensor-probe/1",
        "Accept": "application/json",
    }
    redacted = redact_mapping(headers)
    assert redacted["X-API-Key"] == "***REDACTED***"
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["User-Agent"] == "sensor-probe/1"
    assert "fake-key-123" not in str(redacted)
    assert "fake-token" not in str(redacted)


def test_redact_query_params():
    url = "https://api.example.com/v1/data?symbol=BTC&apiKey=super-secret-42&limit=5"
    redacted = redact_url(url)
    assert "super-secret-42" not in redacted
    assert "apiKey=***REDACTED***" in redacted
    assert "symbol=BTC" in redacted
    assert "limit=5" in redacted


def test_redact_url_userinfo():
    url = "https://user:pass@archive.example.com/file.zip"
    assert "pass" not in redact_url(url)


def test_scrub_secrets_from_free_text():
    message = "invalid api key: sk-abcdef1234567890abcdef"
    scrubbed = scrub_secrets(message)
    assert "sk-abcdef1234567890abcdef" not in scrubbed


def test_scrub_secrets_none_safe():
    assert scrub_secrets(None) is None
