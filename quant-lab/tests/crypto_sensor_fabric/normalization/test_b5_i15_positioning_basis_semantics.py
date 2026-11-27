"""SENSOR-B5-I15 - positioning and basis normalizer semantics (+ adversarial).

Each test maps to a frozen clause of bloc_05/04 sections 8 and 9.  Assertions are
on observable record fields only.  Offline, deterministic, provider-import free.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import SemanticEquivalence
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.sensors import (
    BasisObservationInput,
    BasisReferenceRefusal,
    BasisUnit,
    PositioningMetricType,
    PositioningObservationInput,
    normalize_basis,
    normalize_positioning,
)
from crypto_sensor_fabric.normalization.terms.conversion import ReferencePriceType
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "d" * 64


def _positioning(wave1, **overrides: object) -> PositioningObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_positioning_id="POS-1",
        metric_type=PositioningMetricType.TOP_TRADER_ACCOUNT_RATIO,
        numerator_definition="LONG_ACCOUNTS",
        denominator_definition="SHORT_ACCOUNTS",
        population_scope="TOP_100_ACCOUNTS_BY_POSITION",
        population_size=100,
        value_native=Decimal("1.232"),
        value_unit="RATIO",
        provider_metric_name="topTraderLongShortAccsRatio",
        provider_methodology_ref="BINANCE_TOP_TRADER_ACCOUNT_RATIO_V1",
        semantic_equivalence=SemanticEquivalence.NORMALIZABLE_COMPARABLE,
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
    return PositioningObservationInput(**base)  # type: ignore[arg-type]


def _basis(wave1, **overrides: object) -> BasisObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        native_basis_id="BASIS-1",
        futures_reference="CANON:BTCUSDT:PERP:LINEAR:1",
        spot_reference="CANON:BTCUSDT:SPOT",
        spot_reference_venue="BINANCE",
        basis_value_native=Decimal("12.5"),
        basis_unit=BasisUnit.ABSOLUTE_PRICE,
        reference_price=Decimal("61222"),
        reference_price_type=ReferencePriceType.PROVIDER_INDEX,
        reference_price_unit="USDT",
        reference_price_at=wave1.AT,
        reference_available_at=wave1.AT,
        provider_methodology_ref="BINANCE_INDEX_BASIS_V1",
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
    return BasisObservationInput(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 04 8 -- positioning populations are not interchangeable
# ---------------------------------------------------------------------------


def test_a_ratio_keeps_its_type_and_population(wave1) -> None:
    record = normalize_positioning(_positioning(wave1))
    assert record.positioning_metric_type is PositioningMetricType.TOP_TRADER_ACCOUNT_RATIO
    assert record.population_scope == "TOP_100_ACCOUNTS_BY_POSITION"
    assert record.numerator_definition == "LONG_ACCOUNTS"
    assert record.denominator_definition == "SHORT_ACCOUNTS"
    assert record.value_native == Decimal("1.232")


def test_there_is_no_generic_long_short_ratio_field(wave1) -> None:
    record = normalize_positioning(_positioning(wave1))
    assert not hasattr(record, "long_short_ratio")


def test_the_same_population_on_both_sides_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="must differ"):
        normalize_positioning(
            _positioning(wave1, denominator_definition="LONG_ACCOUNTS")
        )


def test_a_provider_defined_ratio_needs_its_methodology(wave1) -> None:
    with pytest.raises(ValueError, match="requires provider_methodology_ref"):
        _positioning(
            wave1,
            metric_type=PositioningMetricType.PROVIDER_DEFINED_RATIO,
            provider_methodology_ref=None,
        )


def test_a_provider_defined_ratio_cannot_claim_a_canonical_family(wave1) -> None:
    record = normalize_positioning(
        _positioning(
            wave1,
            metric_type=PositioningMetricType.PROVIDER_DEFINED_RATIO,
            value_unit="PERCENT",
        )
    )
    assert record.canonical_metric_family is None


def test_a_non_ratio_dimension_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="not a ratio dimension"):
        _positioning(wave1, value_unit="USD")


def test_positioning_is_byte_deterministic(wave1) -> None:
    assert canonical_json_bytes(normalize_positioning(_positioning(wave1))) == (
        canonical_json_bytes(normalize_positioning(_positioning(wave1)))
    )


# ---------------------------------------------------------------------------
# 04 9 -- basis reference identity
# ---------------------------------------------------------------------------


def test_a_valid_basis_is_comparable(wave1) -> None:
    record = normalize_basis(_basis(wave1), knowledge_cutoff=wave1.CUTOFF)
    assert record.basis_comparable is True
    assert record.reference_refusal is None
    assert record.reference_price_type is ReferencePriceType.PROVIDER_INDEX
    assert record.futures_reference != record.spot_reference


def test_a_late_reference_is_refused(wave1) -> None:
    late = datetime(2026, 3, 1, 14, 0, tzinfo=timezone.utc)
    record = normalize_basis(
        _basis(wave1, reference_available_at=late), knowledge_cutoff=wave1.CUTOFF
    )
    assert record.basis_comparable is False
    assert record.reference_refusal is BasisReferenceRefusal.LATE_REFERENCE
    assert "PIT_LATE_CORRECTION" in {flag.value for flag in record.quality_flags}


def test_a_type_substituted_reference_is_refused(wave1) -> None:
    record = normalize_basis(
        _basis(wave1, reference_price_type=ReferencePriceType.TRADE_PRICE),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.reference_refusal is BasisReferenceRefusal.TYPE_NOT_APPROVED


def test_a_reference_without_availability_is_refused(wave1) -> None:
    record = normalize_basis(
        _basis(wave1, reference_available_at=None), knowledge_cutoff=wave1.CUTOFF
    )
    assert record.reference_refusal is BasisReferenceRefusal.NO_REFERENCE_AVAILABILITY


def test_a_missing_reference_is_refused(wave1) -> None:
    record = normalize_basis(
        _basis(
            wave1,
            reference_price=None,
            reference_price_type=None,
            reference_price_unit=None,
        ),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.reference_refusal is BasisReferenceRefusal.NOT_SUPPLIED


def test_an_absolute_basis_without_a_price_unit_is_a_dimension_mismatch(wave1) -> None:
    record = normalize_basis(
        _basis(wave1, reference_price_unit=None), knowledge_cutoff=wave1.CUTOFF
    )
    assert record.reference_refusal is BasisReferenceRefusal.UNIT_MISMATCH


def test_cross_venue_synthesis_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="cross-venue synthesis"):
        _basis(wave1, spot_reference_venue="COINBASE")


def test_a_basis_against_itself_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="different instruments"):
        _basis(wave1, spot_reference="CANON:BTCUSDT:PERP:LINEAR:1")


def test_annualized_basis_requires_its_method(wave1) -> None:
    with pytest.raises(ValueError, match="requires annualization_method"):
        _basis(wave1, basis_unit=BasisUnit.ANNUALIZED_PERCENT)


def test_annualized_basis_with_a_method_is_comparable(wave1) -> None:
    record = normalize_basis(
        _basis(
            wave1,
            basis_unit=BasisUnit.ANNUALIZED_PERCENT,
            annualization_method="SIMPLE_LINEAR_TO_EXPIRY_V1",
            expiry=datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
        ),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.basis_comparable is True
    assert record.annualization_method == "SIMPLE_LINEAR_TO_EXPIRY_V1"


def test_a_raw_basis_may_not_carry_an_annualization_method(wave1) -> None:
    with pytest.raises(ValueError, match="unit substitution"):
        _basis(wave1, annualization_method="SIMPLE_LINEAR_TO_EXPIRY_V1")


def test_no_derived_basis_number_is_minted(wave1) -> None:
    record = normalize_basis(_basis(wave1), knowledge_cutoff=wave1.CUTOFF)
    for absent in ("basis_bps", "basis_percent", "basis_annualized"):
        assert not hasattr(record, absent), absent


def test_basis_is_byte_deterministic(wave1) -> None:
    first = normalize_basis(_basis(wave1), knowledge_cutoff=wave1.CUTOFF)
    second = normalize_basis(_basis(wave1), knowledge_cutoff=wave1.CUTOFF)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
