"""SENSOR-B5-I08E1 - RED-first common-units / numeric / stablecoin suite.

Executable fixtures authored BEFORE any ``normalization/common/`` module
exists: this file is the RED capture (import of the absent surface fails),
then the standing regression battery once the implementation lands.

Contract law under test (bloc_05/03, compact S-form citations):

  * S4 canonical quantity vocabulary -- the 13 frozen units, and unit
    identity that includes asset identity where relevant ("1000 BASE_ASSET"
    without BTC/ETH identity is incomplete);
  * S3 numeric policy -- provider precision preserved exactly (no rounding),
    canonical numeric types (Decimal at the boundary, floats refused),
    no fake precision (widening is measurable and must not be silent);
  * S9 stablecoin/fiat conversion -- native quote notional is preserved
    truth, USD equivalent is an OPTIONAL derived value, no permanent
    "1 USDT = 1 USD" assumption (depeg mechanics survive normalization);
  * S10 cross-currency hierarchy -- a derived cross through USD only when
    BOTH legs are PIT-valid, otherwise no conversion (fail closed);
  * S14 / S22 inv.5 -- NULL is not zero: an unavailable USD equivalent is
    ``None`` + the frozen blocking flag, never ``0``;
  * S17 / S22 inv.7 -- every derived value carries machine-readable
    conversion lineage and an explicit methodology version;
  * S22 inv.1 -- native values survive; results are frozen models and
    caller inputs are never mutated;
  * 06 S12 depeg fixture -- 1000 USDT at USDT/USD = 0.97 stays 1000 USDT
    native, the optional USD equivalent becomes 970, and a replay cutoff
    before the rate observation exists cannot use the later 0.97 value.

This suite is the constructed E1 verification matrix ``U08-01..U08-18``
(gate-for-gate over the frozen clauses above; the U08 numbering is recorded
as constructed in ``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md``).  U08-19
(scope audit) and U08-20 (evidence determinism) live in
``test_b5_i08_scope_audit.py``.

Ownership: I08 lives in ``normalization/common/`` -- NOT I04B's
``normalization/terms/conversion.py`` (linear/inverse contract primitives,
operator-accepted, untouched here), NOT I05 time, NOT I03 identity.  The
top-level normalization public surface stays the ratified 24 symbols.

OFFLINE: all fixtures are deterministic local data; all times UTC-aware;
no wall clock is read (every cutoff is caller-supplied).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.normalization.common import (
    CanonicalQuantityUnit,
    ConversionRateObservation,
    CrossCurrencyResult,
    METHODOLOGY_VERSION,
    PrecisionRecord,
    QuantityUnitIdentity,
    StablecoinConversionResult,
    convert_stablecoin_to_usd,
    cross_convert_via_usd,
    decimal_places,
    precision_widened,
)
from crypto_sensor_fabric.normalization.enums import (
    BLOCKING_QUALITY_FLAGS,
    NormalizationQualityFlag,
)

_BLOCK = NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE

_T = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_T_PIT = datetime(2025, 6, 1, 11, 59, 0, tzinfo=timezone.utc)
_T_FUTURE = datetime(2025, 6, 1, 12, 1, 0, tzinfo=timezone.utc)


def _rate(
    from_asset: str = "USDT",
    into_asset: str = "USD",
    rate: str = "0.97",
    effective_at: datetime = _T,
    market_available_at: datetime = _T,
) -> ConversionRateObservation:
    return ConversionRateObservation(
        from_asset=from_asset,
        into_asset=into_asset,
        rate=Decimal(rate),
        effective_at=effective_at,
        market_available_at=market_available_at,
        source="synthetic_depeg_fixture",
        methodology=METHODOLOGY_VERSION,
        quality="SYNTHETIC_FIXTURE",
    )


# ---------------------------------------------------------------------------
# U08-01..U08-03 -- canonical quantity vocabulary (S4)
# ---------------------------------------------------------------------------


def test_u08_01_canonical_quantity_vocabulary_is_frozen_and_complete() -> None:
    """S4: exactly the 13 frozen minimum units, values equal their names."""
    expected = {
        "CONTRACTS",
        "BASE_ASSET",
        "QUOTE_ASSET",
        "SETTLEMENT_ASSET",
        "USD",
        "USDT",
        "USDC",
        "OTHER_QUOTE",
        "PERCENT",
        "RATE_PER_INTERVAL",
        "BPS",
        "PRICE",
        "COUNT",
    }
    assert {unit.value for unit in CanonicalQuantityUnit} == expected


def test_u08_02_asset_qualified_units_require_asset_identity() -> None:
    """S4: "1000 BASE_ASSET" without BTC/ETH identity is incomplete."""
    with pytest.raises(ValidationError):
        QuantityUnitIdentity(unit=CanonicalQuantityUnit.BASE_ASSET)
    ok = QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.BASE_ASSET, asset_id="BTC"
    )
    assert ok.asset_id == "BTC"
    # self-identifying units must not smuggle an asset in beside themselves
    with pytest.raises(ValidationError):
        QuantityUnitIdentity(unit=CanonicalQuantityUnit.USD, asset_id="BTC")
    # a dimensionless unit has no asset dimension to declare
    with pytest.raises(ValidationError):
        QuantityUnitIdentity(unit=CanonicalQuantityUnit.COUNT, asset_id="BTC")


def test_u08_03_usd_usdt_usdc_are_distinct_units() -> None:
    """S9 / S22 inv.3: stablecoin != USD by default; the three never collapse."""
    assert len({CanonicalQuantityUnit.USD, CanonicalQuantityUnit.USDT, CanonicalQuantityUnit.USDC}) == 3
    with pytest.raises(ValidationError):
        QuantityUnitIdentity(unit=CanonicalQuantityUnit.USDT, asset_id="USD")


# ---------------------------------------------------------------------------
# U08-04..U08-06 -- numeric policy (S3)
# ---------------------------------------------------------------------------


def test_u08_04_provider_precision_is_preserved_exactly() -> None:
    """S3.1: conversion arithmetic is exact Decimal; nothing is rounded."""
    result = convert_stablecoin_to_usd(
        Decimal("0.0000123456789"),
        CanonicalQuantityUnit.USDT,
        rate=_rate(),
        cutoff=_T_FUTURE,
    )
    assert result.usd_equivalent == Decimal("0.000011975308533")
    assert result.native_value == Decimal("0.0000123456789")


def test_u08_05_no_fake_precision_widening_predicate() -> None:
    """S3.3: widening a 2-decimal source to 4 decimals is measurable, silent."""
    assert decimal_places(Decimal("1.23")) == 2
    assert decimal_places(Decimal("1.2300")) == 4
    assert decimal_places(Decimal("123")) == 0
    assert precision_widened(Decimal("1.23"), Decimal("1.23")) is False
    assert precision_widened(Decimal("1.23"), Decimal("1.2300")) is True
    assert precision_widened(Decimal("1.23"), Decimal("1.2")) is False


def test_u08_06_canonical_numeric_types_refuse_floats() -> None:
    """S3.2: the boundary is Decimal; a float has no lawful representation."""
    with pytest.raises(ValidationError):
        ConversionRateObservation(
            from_asset="USDT",
            into_asset="USD",
            rate=0.97,  # type: ignore[arg-type] -- the float IS the test
            effective_at=_T,
            market_available_at=_T,
            source="s",
            methodology=METHODOLOGY_VERSION,
            quality="SYNTHETIC_FIXTURE",
        )
    record = PrecisionRecord(source_precision=2, conversion_precision=2)
    assert record.source_precision == 2
    with pytest.raises(ValidationError):
        PrecisionRecord(source_precision=-1)


# ---------------------------------------------------------------------------
# U08-07..U08-12 -- stablecoin/fiat conversion (S9, 06 S12)
# ---------------------------------------------------------------------------


def test_u08_07_stablecoin_depeg_fixture_0_97() -> None:
    """06 S12: 1000 USDT stays 1000 USDT native; USD equivalent becomes 970."""
    result = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    assert result.native_value == Decimal("1000")
    assert result.native_unit is CanonicalQuantityUnit.USDT
    assert result.usd_equivalent == Decimal("970")
    assert result.quality_flags == ()
    assert result.methodology_version == METHODOLOGY_VERSION


def test_u08_08_no_hardcoded_one_to_one() -> None:
    """06 S12 / S9: absent rate -> NULL + frozen blocking flag, never 1:1."""
    result = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=None, cutoff=_T_FUTURE
    )
    assert result.usd_equivalent is None
    assert _BLOCK in result.quality_flags
    assert result.conversion_inputs == ()


def test_u08_09_rate_observation_requires_all_frozen_fields() -> None:
    """S9: from_asset, into_asset, rate, effective_at, market_available_at,
    source, methodology, quality -- every frozen field is required."""
    for missing in (
        "from_asset",
        "into_asset",
        "rate",
        "effective_at",
        "market_available_at",
        "source",
        "methodology",
        "quality",
    ):
        payload = {
            "from_asset": "USDT",
            "into_asset": "USD",
            "rate": Decimal("0.97"),
            "effective_at": _T,
            "market_available_at": _T,
            "source": "s",
            "methodology": METHODOLOGY_VERSION,
            "quality": "SYNTHETIC_FIXTURE",
        }
        payload.pop(missing)
        with pytest.raises(ValidationError):
            ConversionRateObservation(**payload)


def test_u08_10_rate_observation_must_be_available_at_cutoff() -> None:
    """06 S12 replay law: a cutoff before the observation exists cannot use
    the later depeg value; at-or-before the availability clock it can."""
    blocked = convert_stablecoin_to_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        rate=_rate(),
        cutoff=_T_PIT,  # one minute BEFORE market_available_at
    )
    assert blocked.usd_equivalent is None
    assert _BLOCK in blocked.quality_flags
    boundary = convert_stablecoin_to_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        rate=_rate(),
        cutoff=_T,  # exactly at market_available_at: inclusive boundary
    )
    assert boundary.usd_equivalent == Decimal("970")


def test_u08_11_rate_direction_is_never_substituted() -> None:
    """S9/S8 spirit: a USDT request answered by a USDC leg is refused, not
    silently redirected; a future-effective rate is refused at an earlier
    cutoff (S10: never fetch a future rate while normalizing old records)."""
    wrong_leg = convert_stablecoin_to_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        rate=_rate(from_asset="USDC"),
        cutoff=_T_FUTURE,
    )
    assert wrong_leg.usd_equivalent is None
    assert _BLOCK in wrong_leg.quality_flags
    future_effective = convert_stablecoin_to_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        rate=_rate(effective_at=_T_FUTURE, market_available_at=_T_FUTURE),
        cutoff=_T,
    )
    assert future_effective.usd_equivalent is None
    assert _BLOCK in future_effective.quality_flags


def test_u08_12_rate_domain_positive_finite() -> None:
    """A rate is a positive finite number; zero, negative, NaN and Infinity
    have no lawful representation (same domain law as I04B prices)."""
    for bad in ("0", "-0.5", "NaN", "Infinity"):
        with pytest.raises(ValidationError):
            _rate(rate=bad)


# ---------------------------------------------------------------------------
# U08-13..U08-14 -- cross-currency hierarchy (S10) and NULL-vs-zero (S14)
# ---------------------------------------------------------------------------


def test_u08_13_derived_cross_through_usd_requires_both_legs_pit_valid() -> None:
    """S10 tier 3: documented derived cross through USD only when both legs
    are PIT-valid; tier 4 is no conversion (NULL + flag), never a guess."""
    usd_leg = _rate(from_asset="USDT", into_asset="USD", rate="0.97")
    eur_leg = _rate(from_asset="EUR", into_asset="USD", rate="1.00")
    ok = cross_convert_via_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        "EUR",
        rate_from=usd_leg,
        rate_into=eur_leg,
        cutoff=_T_FUTURE,
    )
    assert isinstance(ok, CrossCurrencyResult)
    assert ok.derived_value == Decimal("970")
    assert ok.derived_asset == "EUR"
    assert ok.conversion_inputs
    missing_leg = cross_convert_via_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        "EUR",
        rate_from=usd_leg,
        rate_into=None,
        cutoff=_T_FUTURE,
    )
    assert missing_leg.derived_value is None
    assert _BLOCK in missing_leg.quality_flags
    stale_leg = cross_convert_via_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        "EUR",
        rate_from=usd_leg,
        rate_into=_rate(
            from_asset="EUR",
            into_asset="USD",
            rate="1.00",
            market_available_at=_T_FUTURE,
            effective_at=_T_FUTURE,
        ),
        cutoff=_T,
    )
    assert stale_leg.derived_value is None
    assert _BLOCK in stale_leg.quality_flags


def test_u08_14_null_usd_is_not_zero() -> None:
    """S14/S22 inv.5: a verified economic zero converts to zero; an
    unavailable conversion is None -- the two are never the same answer."""
    zero = convert_stablecoin_to_usd(
        Decimal("0"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    assert zero.usd_equivalent == Decimal("0")
    assert zero.quality_flags == ()
    unavailable = convert_stablecoin_to_usd(
        Decimal("0"), CanonicalQuantityUnit.USDT, rate=None, cutoff=_T_FUTURE
    )
    assert unavailable.usd_equivalent is None
    assert unavailable.usd_equivalent != Decimal("0")


# ---------------------------------------------------------------------------
# U08-15..U08-18 -- lineage, survival, result laws, determinism (S17/S22)
# ---------------------------------------------------------------------------


def test_u08_15_derived_values_carry_lineage_and_methodology() -> None:
    """S17/S22 inv.7: every derived value answers "why" without the pipeline."""
    result = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    assert result.methodology_version == METHODOLOGY_VERSION
    assert len(result.conversion_inputs) == 1
    ref = result.conversion_inputs[0]
    assert ref.startswith("rate_observation_ref=")
    assert "synthetic_depeg_fixture" in ref
    assert _T.isoformat() in ref


def test_u08_16_native_value_survives_and_inputs_are_not_mutated() -> None:
    """S22 inv.1 / P09: the observation and the native Decimal are untouched."""
    rate = _rate()
    native = Decimal("1000")
    result = convert_stablecoin_to_usd(
        native, CanonicalQuantityUnit.USDT, rate=rate, cutoff=_T_FUTURE
    )
    assert result.native_value == native == Decimal("1000")
    assert rate.rate == Decimal("0.97")
    assert result is not rate


def test_u08_17_blocked_and_success_result_laws() -> None:
    """A NULL result carries the blocking flag and claims no lineage; a
    derived value carries lineage and no blocking flag."""
    blocked = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=None, cutoff=_T_FUTURE
    )
    assert set(blocked.quality_flags) & set(BLOCKING_QUALITY_FLAGS)
    assert blocked.conversion_inputs == ()
    ok = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    assert not set(ok.quality_flags) & set(BLOCKING_QUALITY_FLAGS)
    assert ok.conversion_inputs
    # a non-stablecoin unit is contract-terms territory (I04B), refused here
    with pytest.raises(ValueError):
        convert_stablecoin_to_usd(
            Decimal("3"), CanonicalQuantityUnit.CONTRACTS, rate=None, cutoff=_T
        )


def test_u08_18_deterministic_construction_and_serialization() -> None:
    """No wall clock, no randomness: equal inputs serialize byte-identically."""
    from crypto_sensor_fabric.normalization.models import canonical_json_bytes

    a = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    b = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE
    )
    assert canonical_json_bytes(a) == canonical_json_bytes(b)
    cross_a = cross_convert_via_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        "EUR",
        rate_from=_rate(),
        rate_into=_rate(from_asset="EUR", into_asset="USD", rate="1.00"),
        cutoff=_T_FUTURE,
    )
    cross_b = cross_convert_via_usd(
        Decimal("1000"),
        CanonicalQuantityUnit.USDT,
        "EUR",
        rate_from=_rate(),
        rate_into=_rate(from_asset="EUR", into_asset="USD", rate="1.00"),
        cutoff=_T_FUTURE,
    )
    assert canonical_json_bytes(cross_a) == canonical_json_bytes(cross_b)
