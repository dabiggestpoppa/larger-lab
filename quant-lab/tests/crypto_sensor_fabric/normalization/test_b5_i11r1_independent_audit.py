"""SENSOR-B5-I11R1 - independent liquidation audit.

Two purposes, deliberately separated:

1. **Positive PIT conversion coverage** (A11-12), using synthetic but valid
   :class:`ContractTermsSnapshot` fixtures and a PIT :class:`ReferencePriceEvidence`.
   The liquidation price is varied independently of the reference price so that
   "uses the reference price" is measured rather than assumed, and the expected
   values are computed here with independent Decimal arithmetic.
2. **Independent adversarial probes** for the rest of the A11 surface, using
   fresh counterexamples rather than re-running the I11E1 suite.

The semantic-authority probe records the *observed* behaviour of a defect
(F_I11R1_02) and marks the required behaviour as a strict xfail, so the suite is
green today and will fail loudly the moment the defect is repaired.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import AggressorSide, LiquidationRole
from crypto_sensor_fabric.normalization.enums import (
    NormalizationStatus,
    PayoffType,
    QuarantineReason,
)
from crypto_sensor_fabric.normalization.sensors import (
    LiquidationAggregationScope,
    LiquidationObservationInput,
    LiquidationPositionSide,
    LiquidationZeroIntervalState,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.terms.conversion import (
    ReferencePriceEvidence,
    ReferencePriceType,
)
from crypto_sensor_fabric.normalization.terms.snapshot import ContractTermsSnapshot
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "b" * 64
_AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
_CUTOFF = datetime(2026, 3, 1, 13, 0, tzinfo=timezone.utc)
_LATE = datetime(2026, 3, 1, 14, 0, tzinfo=timezone.utc)

_LINEAR_TERMS = dict(
    payoff=PayoffType.LINEAR,
    multiplier="0.01",
    inverse=False,
    price_unit="USDT",
    quantity_unit="BTC",
    multiplier_unit="CONTRACTS",
)

_INVERSE_TERMS = dict(
    payoff=PayoffType.INVERSE,
    multiplier="100",
    inverse=True,
    price_unit="USD",
    quantity_unit="BTC",
    multiplier_unit="CONTRACTS",
)


def _terms(**overrides: object) -> ContractTermsSnapshot:
    base: dict[str, object] = dict(
        contract_instance_id="ci-1",
        economic_contract_id="econ-1",
        contract_terms_version="terms-v1",
        contract_multiplier=Decimal("0.01"),
        multiplier_unit="CONTRACTS",
        price_unit="USDT",
        quantity_unit="BTC",
        payoff_type=PayoffType.LINEAR,
        inverse_flag=False,
        quanto_flag=False,
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        tick_size=Decimal("0.5"),
        lot_size=Decimal("1"),
        source_evidence_refs=("terms-ref-1",),
    )
    if "payoff" in overrides:
        overrides["payoff_type"] = overrides.pop("payoff")
    if "inverse" in overrides:
        overrides["inverse_flag"] = overrides.pop("inverse")
    if "multiplier" in overrides:
        overrides["contract_multiplier"] = Decimal(str(overrides.pop("multiplier")))
    base.update(overrides)
    return ContractTermsSnapshot(**base)  # type: ignore[arg-type]


def _price(
    value: str = "60000",
    *,
    price_unit: str = "USDT",
    base_unit: str = "BTC",
    available_at: datetime = _AT,
) -> ReferencePriceEvidence:
    return ReferencePriceEvidence(
        reference_price=Decimal(value),
        reference_price_type=ReferencePriceType.PROVIDER_INDEX,
        reference_price_time=_AT,
        reference_price_source="BINANCE_INDEX",
        market_available_at=available_at,
        reference_price_unit=price_unit,
        reference_price_base_unit=base_unit,
        source_evidence_refs=("px-ref-1",),
    )


def _payload(**overrides: object) -> LiquidationObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSD_PERP",
        contract_instance_id="ci-1",
        liquidation_event_id="liq-1",
        position_side_liquidated=LiquidationPositionSide.LONG,
        execution_side=AggressorSide.SELL,
        quantity_native=Decimal("250"),
        quantity_native_unit="CONTRACTS",
        price_native=Decimal("61234.5"),
        aggregation_scope=LiquidationAggregationScope.EVENT_LEVEL,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
    )
    base.update(overrides)
    return LiquidationObservationInput(**base)  # type: ignore[arg-type]


def _flags(record: object) -> set[str]:
    return {flag.value for flag in record.quality_flags}  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# A11-12 - positive PIT conversion coverage (linear)
# ---------------------------------------------------------------------------


def test_linear_contracts_convert_to_base_and_quote_with_pit_terms() -> None:
    record = normalize_liquidation(
        _payload(),
        terms=_terms(**_LINEAR_TERMS),
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is False
    # 250 contracts x 0.01 BTC/contract, computed independently.
    assert record.quantity_base.value == Decimal("250") * Decimal("0.01")
    assert record.quantity_base.output_unit == "BTC"
    assert record.quantity_base.methodology_version == "B5_I04B_CONVERSION_V1"
    assert record.quantity_base.conversion_lineage_refs

    assert record.liquidation_quote_notional is not None
    assert record.liquidation_quote_notional.value == Decimal("2.5") * Decimal("60000")
    assert record.liquidation_quote_notional.output_unit == "USDT"


# ---------------------------------------------------------------------------
# A11-12 - positive PIT conversion coverage (inverse)
# ---------------------------------------------------------------------------


def test_inverse_contracts_use_the_reference_price_for_the_base_leg() -> None:
    record = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5")),
        terms=_terms(**_INVERSE_TERMS),
        reference_price=_price("60000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    expected_face = Decimal("2.5") * Decimal("100")  # 250 USD
    expected_base = expected_face / Decimal("60000")
    assert record.liquidation_quote_notional is not None
    assert record.liquidation_quote_notional.value == expected_face
    assert record.liquidation_quote_notional.output_unit == "USD"
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is False
    assert record.quantity_base.value == expected_base
    assert record.quantity_base.output_unit == "BTC"


def test_inverse_base_is_invariant_to_the_liquidation_price() -> None:
    """The trade price must never enter the inverse base derivation."""
    terms = _terms(**_INVERSE_TERMS)
    low = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5"), price_native=Decimal("1")),
        terms=terms,
        reference_price=_price("60000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    high = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5"), price_native=Decimal("999999")),
        terms=terms,
        reference_price=_price("60000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    assert low.quantity_base is not None and high.quantity_base is not None
    assert low.quantity_base.value == high.quantity_base.value
    assert low.quantity_base.value == Decimal("250") / Decimal("60000")


def test_inverse_base_tracks_the_reference_price_when_it_moves_alone() -> None:
    terms = _terms(**_INVERSE_TERMS)
    at_60k = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5")),
        terms=terms,
        reference_price=_price("60000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    at_30k = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5")),
        terms=terms,
        reference_price=_price("30000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    assert at_60k.quantity_base is not None and at_30k.quantity_base is not None
    assert at_60k.quantity_base.value == Decimal("250") / Decimal("60000")
    assert at_30k.quantity_base.value == Decimal("250") / Decimal("30000")
    # ... while the quote-denominated contract face is unchanged.
    assert at_30k.liquidation_quote_notional is not None
    assert at_60k.liquidation_quote_notional is not None
    assert (
        at_30k.liquidation_quote_notional.value
        == at_60k.liquidation_quote_notional.value
    )


# ---------------------------------------------------------------------------
# A11-12 - invalid and missing PIT terms must block, never guess
# ---------------------------------------------------------------------------


def test_missing_pit_terms_block_the_derivation_without_guessing() -> None:
    record = normalize_liquidation(
        _payload(),
        terms=None,
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is True
    assert record.quantity_base.value is None
    assert record.quantity_base.missingness_reason is not None


@pytest.mark.parametrize(
    "terms_factory",
    [
        pytest.param(
            lambda: _terms(**{**_LINEAR_TERMS, "multiplier_unit": "USD"}), id="dimension"
        ),
        pytest.param(lambda: _terms(**_LINEAR_TERMS, quanto_flag=True), id="quanto"),
        pytest.param(
            lambda: _terms(**{**_LINEAR_TERMS, "payoff": PayoffType.UNKNOWN}),
            id="unknown-payoff",
        ),
        pytest.param(lambda: _terms(**_INVERSE_TERMS), id="family-mismatch"),
    ],
)
def test_incompatible_pit_terms_block_the_derivation(terms_factory: object) -> None:
    record = normalize_liquidation(
        _payload(),
        terms=terms_factory(),  # type: ignore[operator]
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is True
    assert record.quantity_base.value is None


def test_price_observed_after_the_knowledge_cutoff_blocks_conversion() -> None:
    record = normalize_liquidation(
        _payload(),
        terms=_terms(**_LINEAR_TERMS),
        reference_price=_price("60000", available_at=_LATE),
        knowledge_cutoff=_CUTOFF,
    )
    # The base leg is price-free, so only the quote leg can be blocked here.
    assert record.liquidation_quote_notional is not None
    assert record.liquidation_quote_notional.blocked is True
    assert record.liquidation_quote_notional.value is None


def test_price_dimension_mismatch_blocks_conversion() -> None:
    record = normalize_liquidation(
        _payload(),
        terms=_terms(**_LINEAR_TERMS),
        reference_price=_price("60000", base_unit="ETH"),
        knowledge_cutoff=_CUTOFF,
    )
    assert record.liquidation_quote_notional is not None
    assert record.liquidation_quote_notional.blocked is True


# ---------------------------------------------------------------------------
# A11-14 - provider semantic authority (CRITICAL)
# ---------------------------------------------------------------------------


def test_untrusted_boolean_promotes_canonical_sides_today() -> None:
    """F_I11R1_02, recorded as observed evidence rather than as acceptable law.

    The caller supplies ``provider_semantics_verified=True`` with no registry
    row, no confidence and no evidence reference.  The canonical side fields are
    populated anyway, while the same record still carries
    ``SEMANTICS_UNVERIFIED`` -- the record contradicts itself.
    """
    record = normalize_liquidation(_payload(provider_semantics_verified=True))
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.execution_side is AggressorSide.SELL
    assert "SEMANTICS_UNVERIFIED" in _flags(record)
    assert record.normalization_status is NormalizationStatus.NATIVE_ONLY


@pytest.mark.xfail(
    strict=True,
    reason=(
        "F_I11R1_02: canonical admission must be a property of the I09 "
        "provider-evidence ladder, never a caller choice (bloc_05/03 section 13)"
    ),
)
def test_canonical_sides_must_not_be_promoted_by_a_caller_boolean() -> None:
    record = normalize_liquidation(_payload(provider_semantics_verified=True))
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN


def test_a_false_boolean_keeps_the_provider_reading_provisional() -> None:
    record = normalize_liquidation(_payload())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN
    assert record.provisional_position_side is LiquidationPositionSide.LONG
    assert record.provisional_execution_side is AggressorSide.SELL


def test_a_contradictory_claim_is_quarantined_even_when_marked_verified() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.LONG,
            execution_side=AggressorSide.BUY,
            provider_semantics_verified=True,
        )
    )
    assert record.normalization_status is NormalizationStatus.QUARANTINED
    assert record.quarantine_reason is QuarantineReason.INVALID_SIDE_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


# ---------------------------------------------------------------------------
# Fresh counterexamples for the rest of the A11 surface
# ---------------------------------------------------------------------------


def test_zero_aggregate_over_a_known_gap_is_not_a_verified_zero() -> None:
    record = normalize_liquidation(
        _payload(
            liquidation_event_id=None,
            quantity_native=Decimal("0"),
            quantity_native_unit="BTC",
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
            count=0,
            provider_reports_completed_intervals=True,
            interval_closed=True,
            source_coverage_state=CoverageState.KNOWN_GAP,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING
    assert record.quantity_native == Decimal("0")  # retained as native evidence


def test_zero_aggregate_with_every_condition_held_is_a_verified_zero() -> None:
    record = normalize_liquidation(
        _payload(
            liquidation_event_id=None,
            quantity_native=Decimal("0"),
            quantity_native_unit="BTC",
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
            count=0,
            provider_reports_completed_intervals=True,
            interval_closed=True,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.VERIFIED_ZERO


def test_maker_taker_role_and_revision_state_survive_unchanged() -> None:
    record = normalize_liquidation(
        _payload(maker_taker_role=LiquidationRole.TAKER)
    )
    assert record.maker_taker_role is LiquidationRole.TAKER
    assert record.source_revision_state is RevisionState.STABLE
    assert record.source_revision_id == "rev-1"


def test_cross_venue_rows_are_not_synthesised_into_one() -> None:
    binance = normalize_liquidation(_payload(venue="BINANCE", provider="BINANCE_USDM"))
    okx = normalize_liquidation(_payload(venue="OKX", provider="OKX_SWAP"))
    assert binance.venue != okx.venue
    assert binance.provider != okx.provider
    assert binance.model_dump_json() != okx.model_dump_json()


def test_usd_notional_stays_blocked_with_its_citation() -> None:
    record = normalize_liquidation(
        _payload(),
        terms=_terms(**_LINEAR_TERMS),
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert record.liquidation_usd is not None
    assert record.liquidation_usd.blocked is True
    assert record.liquidation_usd.value is None
    assert record.liquidation_usd.unresolved_citation == "B5_I08_UNITS_V1"


def test_an_aggregate_without_a_count_is_refused_at_construction() -> None:
    with pytest.raises(ValueError):
        _payload(
            liquidation_event_id=None,
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
        )
