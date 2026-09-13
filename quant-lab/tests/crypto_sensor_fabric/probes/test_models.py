"""Core probe model tests (T2-MODEL-01 .. T2-MODEL-06)."""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.base import canonical_bytes
from crypto_sensor_fabric.contracts.enums import MissingReason, SensorFamily
from crypto_sensor_fabric.probes.enums import (
    CapabilityMissingness,
    CapabilityStatus,
    EvidenceLevel,
    Granularity,
    ProbeFailureClass,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import (
    CapabilityClaim,
    CapabilityProbeAttempt,
    CapabilityProbeRequest,
    missingness_to_bloc1_reason,
)
from pydantic import ValidationError


def request_payload(**overrides) -> dict:
    payload = {
        "provider_id": "KRAKEN_FUTURES",
        "sensor_family": "MECHANICAL_OPEN_INTEREST",
        "venue_market": "KRAKEN_FUTURES",
        "instrument_native": "PI_XBTUSD",
        "canonical_asset_hint": "BTC",
        "requested_start": "2022-06-15T00:00:00Z",
        "requested_end": "2022-06-16T00:00:00Z",
        "requested_granularity": "5m",
        "access_mode": "PUBLIC_REST",
        "query_mode": "TIME_RANGE",
        "probe_run_id": "run_2026_08_29_001",
        "provider_hints": {"endpoint_id": "analytics/v1"},
    }
    payload.update(overrides)
    return payload


def attempt_payload(**overrides) -> dict:
    payload = {
        "probe_id": "kraken_oi_btc_2022_5m_001",
        "probe_run_id": "run_2026_08_29_001",
        "provider_id": "KRAKEN_FUTURES",
        "sensor_family": "MECHANICAL_OPEN_INTEREST",
        "venue_market": "KRAKEN_FUTURES",
        "instrument_native": "PI_XBTUSD",
        "canonical_asset_hint": "BTC",
        "requested_start": "2022-06-15T00:00:00Z",
        "requested_end": "2022-06-16T00:00:00Z",
        "requested_granularity": "5m",
        "access_mode": "PUBLIC_REST",
        "query_mode": "TIME_RANGE",
        "request_method": "GET",
        "request_fingerprint": "fp-001",
        "response_status_class": "VERIFIED_SAMPLE",
        "http_status_or_file_status": 200,
        "rows_returned": 288,
        "first_timestamp_returned": "2022-06-15T00:00:00Z",
        "last_timestamp_returned": "2022-06-15T23:55:00Z",
        "native_timestamp_fields": ["time"],
        "native_units_summary": {"oi": "CONTRACTS"},
        "pagination_detected": False,
        "pagination_complete": True,
        "rate_limit_metadata": {},
        "requires_auth": False,
        "requires_payment": False,
        "geo_block_detected": False,
        "payload_schema_fingerprint": "sha256:abc",
        "payload_hash_sample": "sha256:def",
        "error_class": None,
        "error_detail_redacted": None,
        "started_at": "2026-08-29T08:00:00Z",
        "finished_at": "2026-08-29T08:00:01Z",
        "probe_version": "sensor-probe-v1",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# T2-MODEL-01 / T2-MODEL-02 — request validates canonical dimensions
# ---------------------------------------------------------------------------


def test_t2_model_01_request_validates():
    request = CapabilityProbeRequest.model_validate(request_payload())
    assert request.provider_id == "KRAKEN_FUTURES"
    assert request.sensor_family is SensorFamily.MECHANICAL_OPEN_INTEREST
    assert request.requested_granularity is Granularity.G5M
    assert request.requested_end >= request.requested_start


def test_t2_model_02_invalid_sensor_enum_fails_closed():
    with pytest.raises(ValidationError):
        CapabilityProbeRequest.model_validate(
            request_payload(sensor_family="NOT_A_SENSOR")
        )


def test_t2_model_02_invalid_granularity_fails_closed():
    with pytest.raises(ValidationError):
        CapabilityProbeRequest.model_validate(request_payload(requested_granularity="2h"))


def test_t2_model_02_invalid_provider_empty_fails():
    with pytest.raises(ValidationError):
        CapabilityProbeRequest.model_validate(request_payload(provider_id=""))


def test_t2_model_02_inverted_window_fails():
    with pytest.raises(ValidationError):
        CapabilityProbeRequest.model_validate(
            request_payload(
                requested_start="2022-06-16T00:00:00Z",
                requested_end="2022-06-15T00:00:00Z",
            )
        )


# ---------------------------------------------------------------------------
# T2-MODEL-03 — deterministic serialization
# ---------------------------------------------------------------------------


def test_t2_model_03_deterministic_serialization():
    first = CapabilityProbeAttempt.model_validate(attempt_payload())
    second = CapabilityProbeAttempt.model_validate(attempt_payload())
    assert canonical_bytes(first) == canonical_bytes(second)


def test_t2_model_03_deterministic_across_instances():
    payload = attempt_payload()
    a = CapabilityProbeAttempt.model_validate(payload)
    b = CapabilityProbeAttempt.model_validate(payload)
    assert a.model_dump(mode="json") == b.model_dump(mode="json")


# ---------------------------------------------------------------------------
# T2-MODEL-05 — failed probes still emit evidence
# ---------------------------------------------------------------------------


def test_t2_model_05_failed_attempt_is_valid_evidence():
    attempt = CapabilityProbeAttempt.model_validate(
        attempt_payload(
            response_status_class="FAILED",
            rows_returned=None,
            first_timestamp_returned=None,
            last_timestamp_returned=None,
            error_class="F_ACCESS_PAYMENT",
            error_detail_redacted="***REDACTED***",
            payload_schema_fingerprint=None,
            payload_hash_sample=None,
        )
    )
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_PAYMENT
    assert attempt.response_status_class is ResponseStatusClass.FAILED


def test_t2_model_05_failed_without_error_class_fails():
    with pytest.raises(ValidationError, match="error_class"):
        CapabilityProbeAttempt.model_validate(
            attempt_payload(response_status_class="FAILED", error_class=None)
        )


# ---------------------------------------------------------------------------
# T2-MODEL-06 — unattempted is not unsupported
# ---------------------------------------------------------------------------


def test_t2_model_06_unattempted_never_unsupported():
    attempt = CapabilityProbeAttempt.model_validate(
        attempt_payload(
            response_status_class="NOT_ATTEMPTED",
            error_class=None,
            rows_returned=None,
        )
    )
    assert attempt.response_status_class is ResponseStatusClass.NOT_ATTEMPTED
    assert attempt.error_class is None
    # serialization keeps the explicit NOT_ATTEMPTED state; never coerced
    assert attempt.model_dump(mode="json")["response_status_class"] == "NOT_ATTEMPTED"


def test_t2_model_06_claim_unverified_default():
    claim = CapabilityClaim.model_validate(
        {
            "claim_id": "claim-1",
            "provider_id": "X",
            "sensor_family": "MECHANICAL_TRADE",
            "venue_market": "X",
            "access_mode": "PUBLIC_REST",
        }
    )
    assert claim.capability_status is CapabilityStatus.UNVERIFIED
    assert claim.evidence_level is EvidenceLevel.E0_CLAIM_ONLY


# ---------------------------------------------------------------------------
# Claim invariants
# ---------------------------------------------------------------------------


def test_claim_verified_requires_runtime_evidence():
    with pytest.raises(ValidationError, match="runtime evidence"):
        CapabilityClaim.model_validate(
            {
                "claim_id": "claim-2",
                "provider_id": "X",
                "sensor_family": "MECHANICAL_TRADE",
                "venue_market": "X",
                "access_mode": "PUBLIC_REST",
                "capability_status": "VERIFIED",
                "evidence_level": "E0_CLAIM_ONLY",
            }
        )


def test_claim_boundaries_ordered():
    with pytest.raises(ValidationError):
        CapabilityClaim.model_validate(
            {
                "claim_id": "claim-3",
                "provider_id": "X",
                "sensor_family": "MECHANICAL_TRADE",
                "venue_market": "X",
                "access_mode": "PUBLIC_REST",
                "earliest_verified_history": "2024-06-15T00:00:00Z",
                "latest_verified_history": "2022-06-15T00:00:00Z",
            }
        )


# ---------------------------------------------------------------------------
# Missingness mapping (03 §6)
# ---------------------------------------------------------------------------


def test_missingness_maps_faithfully():
    reason, note = missingness_to_bloc1_reason(
        CapabilityMissingness.OUTSIDE_PROVIDER_RETENTION
    )
    assert reason is MissingReason.OUTSIDE_PROVIDER_HISTORY
    assert note is None


@pytest.mark.parametrize(
    "missingness",
    [CapabilityMissingness.PRE_LISTING, CapabilityMissingness.PAYMENT_BLOCKED],
)
def test_missingness_without_faithful_bloc1_member_flags_refinement(
    missingness: CapabilityMissingness,
):
    reason, note = missingness_to_bloc1_reason(missingness)
    assert reason is None
    assert note is not None
    assert "BLOC5_SCHEMA_REFINEMENT_PENDING" in note
