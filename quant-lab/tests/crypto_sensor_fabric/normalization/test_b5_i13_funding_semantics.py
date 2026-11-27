"""SENSOR-B5-I13 - funding normalizer semantics (frozen clauses + adversarial).

Each test maps to a frozen clause of bloc_05/04 section 5.  Assertions are on
observable record fields only.  Offline, deterministic, provider-import free.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import MissingnessReason
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.sensors import (
    FUNDING_EQUIV_METHODOLOGY_ID,
    FundingObservationInput,
    FundingRateKind,
    FundingRateUnit,
    SensorAdmissionRefusal,
    normalize_funding,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "b" * 64
_FAMILY = SensorFamily.MECHANICAL_FUNDING


def _payload(wave1, **overrides: object) -> FundingObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_funding_id="FUND-1",
        funding_rate_native=Decimal("0.0001"),
        native_rate_unit_token="RATE",
        native_rate_unit_field="fundingRate",
        rate_reading=FundingRateUnit.RATE_FRACTION,
        funding_rate_kind=FundingRateKind.REALIZED,
        funding_interval_seconds=28800,
        interval_start_at=datetime(2026, 3, 1, 4, 0, tzinfo=timezone.utc),
        interval_end_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        interval_closed=True,
        interval_time_convention=wave1.interval_convention,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
        event_at=wave1.AT,
    )
    base.update(overrides)
    return FundingObservationInput(**base)  # type: ignore[arg-type]


def _admitted(wave1):
    registry = wave1.registry(
        (wave1.row("fundingRate", "funding_rate_unit", family=_FAMILY),)
    )
    return wave1.authority(registry)


# ---------------------------------------------------------------------------
# 04 5.2 -- interval-scaled comparables
# ---------------------------------------------------------------------------


def test_8h_native_matches_its_own_equivalent(wave1) -> None:
    record = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    assert record.funding_rate_per_8h_simple_equiv.blocked is False
    assert record.funding_rate_per_8h_simple_equiv.value == Decimal("0.0001")
    assert record.funding_rate_per_day_simple_equiv.value == Decimal("0.0003")


def test_4h_native_scales_to_two_8h_periods(wave1) -> None:
    record = normalize_funding(
        _payload(
            wave1,
            funding_rate_native=Decimal("0.0004"),
            funding_interval_seconds=14400,
            interval_start_at=datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc),
            interval_end_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        ),
        registry=_admitted(wave1),
    )
    assert record.funding_rate_per_8h_simple_equiv.value == Decimal("0.0008")
    assert record.funding_rate_per_day_simple_equiv.value == Decimal("0.0024")
    assert record.funding_interval_seconds == 14400


def test_the_equivalent_cites_the_frozen_methodology(wave1) -> None:
    record = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    amount = record.funding_rate_per_8h_simple_equiv
    assert amount.methodology_id == FUNDING_EQUIV_METHODOLOGY_ID
    assert amount.output_unit == "RATE_FRACTION"
    assert any("28800" in ref for ref in amount.conversion_lineage_refs)


def test_an_unknown_interval_refuses_the_equivalents(wave1) -> None:
    record = normalize_funding(
        _payload(
            wave1,
            funding_interval_seconds=None,
            interval_start_at=None,
            interval_end_at=None,
            interval_closed=None,
            interval_time_convention=None,
        ),
        registry=_admitted(wave1),
    )
    assert record.funding_rate_per_8h_simple_equiv.blocked is True
    assert (
        record.funding_rate_per_8h_simple_equiv.missingness_reason
        is MissingnessReason.TIME_BLOCKED
    )
    assert record.funding_rate_native == Decimal("0.0001")


def test_an_interval_contradiction_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="contradicts the period bounds"):
        _payload(wave1, funding_interval_seconds=3600)


# ---------------------------------------------------------------------------
# 04 5.1/5.3 -- readings and dimensions
# ---------------------------------------------------------------------------


def test_predicted_funding_never_overwrites_realized(wave1) -> None:
    predicted = normalize_funding(
        _payload(wave1, funding_rate_kind=FundingRateKind.PREDICTED),
        registry=_admitted(wave1),
    )
    realized = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    assert predicted.funding_rate_kind is FundingRateKind.PREDICTED
    assert realized.funding_rate_kind is FundingRateKind.REALIZED
    # Neither row carries a combined "funding rate" field to overwrite.
    assert not hasattr(predicted, "funding_rate")
    assert not hasattr(predicted, "funding_rate_annualized")


def test_a_flow_amount_is_not_a_rate(wave1) -> None:
    with pytest.raises(ValueError, match="not a funding-rate dimension"):
        _payload(wave1, rate_reading=FundingRateUnit.FLOW_AMOUNT)


def test_a_pnl_amount_is_not_a_rate(wave1) -> None:
    with pytest.raises(ValueError, match="not a funding-rate dimension"):
        _payload(wave1, rate_reading=FundingRateUnit.PNL_AMOUNT)


def test_no_usd_funding_amount_field_exists(wave1) -> None:
    record = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    for absent in (
        "funding_amount_usd",
        "funding_payment_usd",
        "funding_rate_annualized",
    ):
        assert not hasattr(record, absent), absent


# ---------------------------------------------------------------------------
# 03 11-13 -- semantic admission
# ---------------------------------------------------------------------------


def test_a_caller_minted_registry_cannot_certify_the_rate_unit(wave1) -> None:
    registry = wave1.registry(
        (wave1.row("fundingRate", "funding_rate_unit", family=_FAMILY),)
    )
    record = normalize_funding(_payload(wave1), registry=registry)
    assert record.rate_unit_admission is not None
    assert record.rate_unit_admission.refusal is SensorAdmissionRefusal.UNTRUSTED_AUTHORITY
    assert record.funding_rate_per_8h_simple_equiv.blocked is True
    assert record.funding_rate_native == Decimal("0.0001")


def test_provider_specific_rate_keeps_native_only(wave1) -> None:
    record = normalize_funding(
        _payload(
            wave1,
            native_rate_unit_token="TICKS",
            rate_reading=FundingRateUnit.PROVIDER_SPECIFIC,
        ),
        registry=_admitted(wave1),
    )
    assert record.funding_rate_unit == "TICKS"
    assert record.funding_rate_per_8h_simple_equiv.blocked is True
    assert (
        record.funding_rate_per_8h_simple_equiv.missingness_reason
        is MissingnessReason.SEMANTICS_BLOCKED
    )


def test_funding_is_byte_deterministic(wave1) -> None:
    first = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    second = normalize_funding(_payload(wave1), registry=_admitted(wave1))
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
