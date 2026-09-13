"""Base-schema validation tests (B1-T01 .. B1-T05).

A complete, valid base payload is built by `_base_kwargs()`; each test removes
or mutates one aspect to prove the invariant fails closed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from crypto_sensor_fabric.contracts.base import (
    CanonicalObservationBase,
    canonical_bytes,
    canonical_dump,
)
from crypto_sensor_fabric.contracts.enums import (
    AccessClass,
    EvidenceClass,
    MarketType,
    QualityFlag,
    RetrievalMode,
    SemanticEquivalence,
    SensorFamily,
)
from pydantic import ValidationError

VALID_BASE: dict = {
    "observation_id": "obs-0001",
    "sensor_family": SensorFamily.MECHANICAL_TRADE,
    "provider": "FIXTURE_PROVIDER",
    "venue": "FIXTURE_VENUE",
    "evidence_class": EvidenceClass.FIRST_PARTY_EXCHANGE,
    "retrieval_mode": RetrievalMode.REST,
    "instrument_native": "BTC-USDT-PERP",
    "instrument_id_canonical": "CANON:BTCUSDT:PERP:LINEAR:1",
    "market_type": MarketType.PERPETUAL,
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "settlement_asset": "USDT",
    "contract_type": None,
    "contract_multiplier": 1.0,
    "is_inverse": False,
    "effective_at": "2024-03-01T12:00:00Z",
    "observed_at": "2024-03-01T12:00:00Z",
    "ingested_at": "2024-03-05T08:00:00Z",
    "window_start": None,
    "window_end": None,
    "source_interval": None,
    "endpoint_id": "FIXTURE/ENDPOINT/V1",
    "source_record_id": None,
    "raw_object_uri": "file://fixtures/t0/raw/2024/03/01/obs-0001.bin",
    "raw_checksum": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "access_class": AccessClass.FREE_AUTOMATED,
    "semantic_equivalence": SemanticEquivalence.NORMALIZABLE_COMPARABLE,
    "quality_flags": [],
    "adapter_version": "0.1.0",
    "schema_version": "1.0.0",
    "identity_version": "0.1.0",
    "normalization_version": None,
    "methodology_version": None,
}


def _base_kwargs(**overrides) -> dict:
    payload = dict(VALID_BASE)
    payload.update(overrides)
    return payload


def _valid() -> CanonicalObservationBase:
    return CanonicalObservationBase.model_validate(_base_kwargs())


# ---------------------------------------------------------------------------
# B1-T01 — required provenance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["provider", "venue", "raw_object_uri", "raw_checksum", "schema_version", "adapter_version"],
)
def test_t01_required_provenance_fields(field: str):
    payload = _base_kwargs(**{field: None})
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    ["provider", "venue", "raw_object_uri", "raw_checksum", "schema_version", "adapter_version"],
)
def test_t01_empty_strings_fail(field: str):
    payload = _base_kwargs(**{field: ""})
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(payload)


# ---------------------------------------------------------------------------
# B1-T02 — native symbol retention
# ---------------------------------------------------------------------------


def test_t02_instrument_native_required():
    payload = _base_kwargs(instrument_native=None)
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(payload)


def test_t02_instrument_native_empty_fails():
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(_base_kwargs(instrument_native=""))


# ---------------------------------------------------------------------------
# B1-T03 — canonical identity can fail safely
# ---------------------------------------------------------------------------


def test_t03_unresolved_identity_without_flag_fails():
    payload = _base_kwargs(instrument_id_canonical=None)
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(payload)


def test_t03_unresolved_identity_with_flag_validates():
    payload = _base_kwargs(
        instrument_id_canonical=None,
        quality_flags=[QualityFlag.INSTRUMENT_ID_UNRESOLVED],
    )
    model = CanonicalObservationBase.model_validate(payload)
    assert model.instrument_id_canonical is None
    assert QualityFlag.INSTRUMENT_ID_UNRESOLVED in model.quality_flags


# ---------------------------------------------------------------------------
# B1-T04 — time fields are timezone-aware UTC
# ---------------------------------------------------------------------------


def test_t04_naive_datetime_fails():
    payload = _base_kwargs(effective_at="2024-03-01T12:00:00")
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(payload)


def test_t04_naive_datetime_fails_on_all_time_fields():
    for field in ("effective_at", "observed_at", "ingested_at"):
        payload = _base_kwargs(**{field: "2024-03-01T12:00:00"})
        with pytest.raises(ValidationError, match="naive datetime"):
            CanonicalObservationBase.model_validate(payload)


def test_t04_aware_datetimes_normalized_to_utc():
    payload = _base_kwargs(effective_at="2024-03-01T14:00:00+02:00")
    model = CanonicalObservationBase.model_validate(payload)
    assert model.effective_at.tzinfo == UTC
    assert model.effective_at == datetime(2024, 3, 1, 12, 0, 0, tzinfo=UTC)


def test_t04_all_datetime_fields_aware_after_validation():
    model = _valid()
    for name in ("effective_at", "observed_at", "ingested_at"):
        value = getattr(model, name)
        assert value.tzinfo is not None
        assert value.utcoffset() == UTC.utcoffset(None)  # zero offset


# ---------------------------------------------------------------------------
# B1-T05 — raw traceability
# ---------------------------------------------------------------------------


def test_t05_every_observation_traces_to_raw_pointer_and_checksum():
    model = _valid()
    assert model.raw_object_uri
    assert model.raw_checksum
    dumped = canonical_dump(model)
    assert dumped["raw_object_uri"] == model.raw_object_uri
    assert dumped["raw_checksum"] == model.raw_checksum


def test_t05_missing_raw_checksum_fails():
    with pytest.raises(ValidationError):
        CanonicalObservationBase.model_validate(_base_kwargs(raw_checksum=None))


# ---------------------------------------------------------------------------
# Deterministic serialization sanity (exercised fully in B1-05 versioning)
# ---------------------------------------------------------------------------


def test_canonical_bytes_stable_across_calls():
    model = _valid()
    assert canonical_bytes(model) == canonical_bytes(model)
