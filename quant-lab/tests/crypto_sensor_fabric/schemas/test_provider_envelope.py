"""ProviderEnvelope provenance contract tests (02 §3)."""

from __future__ import annotations

from datetime import UTC

import pytest
from crypto_sensor_fabric.contracts.enums import (
    AccessClass,
    RetrievalMode,
    SensorFamily,
)
from crypto_sensor_fabric.schemas import ProviderEnvelope
from pydantic import ValidationError


def _envelope_payload(**overrides) -> dict:
    payload = {
        "envelope_id": "env-0001",
        "provider": "FIXTURE_PROVIDER_A",
        "venue_hint": "FIXTURE_VENUE_A",
        "sensor_family_hint": SensorFamily.MECHANICAL_TRADE,
        "endpoint_id": "FIXTURE/TRADES/V1",
        "request_id": "req-0001",
        "retrieval_mode": RetrievalMode.REST,
        "request_started_at": "2024-03-01T11:59:58Z",
        "response_received_at": "2024-03-01T12:00:01Z",
        "source_symbol": "BTC-USDT-PERP",
        "source_interval": None,
        "requested_start": None,
        "requested_end": None,
        "raw_object_uri": "file://fixtures/t0/raw/2024/03/01/trade-0001.json",
        "raw_checksum": "sha256:aa00000000000000000000000000000000000000000000000000000000000001",
        "http_status": 200,
        "access_class": AccessClass.FREE_AUTOMATED,
        "adapter_version": "0.1.0",
        "quality_flags": [],
        "source_metadata": {"page": 1},
    }
    payload.update(overrides)
    return payload


def test_envelope_requires_raw_pointer():
    with pytest.raises(ValidationError):
        ProviderEnvelope.model_validate(_envelope_payload(raw_object_uri=None))


def test_envelope_requires_sensor_family_hint():
    with pytest.raises(ValidationError):
        ProviderEnvelope.model_validate(_envelope_payload(sensor_family_hint=None))


def test_envelope_naive_timestamp_fails():
    with pytest.raises(ValidationError):
        ProviderEnvelope.model_validate(
            _envelope_payload(response_received_at="2024-03-01T12:00:01")
        )


def test_envelope_timestamps_normalized_to_utc():
    envelope = ProviderEnvelope.model_validate(
        _envelope_payload(request_started_at="2024-03-01T13:59:58+02:00")
    )
    assert envelope.request_started_at.tzinfo == UTC
    assert envelope.request_started_at.hour == 11


def test_envelope_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ProviderEnvelope.model_validate(_envelope_payload(unexpected="x"))


def test_envelope_is_not_a_canonical_observation():
    """Envelope never carries canonical observation fields (provenance only)."""
    envelope = ProviderEnvelope.model_validate(_envelope_payload())
    assert not hasattr(envelope, "effective_at")
    assert not hasattr(envelope, "sensor_family")
