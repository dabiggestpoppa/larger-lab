"""SENSOR-B5-I11E1 - liquidation normalizer semantics (ten families + adversarial).

Each family maps to a frozen clause of bloc_05/04 section 3 and is asserted
against observable record fields only, never against a private helper.  The
suite is offline, deterministic and free of provider imports.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import AggressorSide, LiquidationRole
from crypto_sensor_fabric.normalization.sensors import (
    LiquidationAggregationScope,
    LiquidationObservationInput,
    LiquidationPositionSide,
    LiquidationZeroIntervalState,
    T1LiquidationRecord,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.sensors.liquidation import (
    ContradictoryLiquidationSideError,
    require_consistent_liquidation_sides,
)
from crypto_sensor_fabric.normalization.enums import (
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    QuarantineReason,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "a" * 64


def _payload(**overrides: object) -> LiquidationObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        liquidation_event_id="liq-1",
        position_side_liquidated=LiquidationPositionSide.LONG,
        execution_side=AggressorSide.SELL,
        quantity_native=Decimal("2.5"),
        quantity_native_unit="BTC",
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


def _aggregate(**overrides: object) -> LiquidationObservationInput:
    base: dict[str, object] = dict(
        liquidation_event_id=None,
        quantity_native=Decimal("120.0"),
        quantity_native_unit="USDT",
        aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
        count=7,
        provider_reports_completed_intervals=True,
        interval_closed=True,
    )
    base.update(overrides)
    return _payload(**base)


def _flag_values(record: T1LiquidationRecord) -> set[str]:
    return {flag.value for flag in record.quality_flags}


# ---------------------------------------------------------------------------
# I11-SIDE (04 section 3.1): four separate facts, never collapsed
# ---------------------------------------------------------------------------


def test_a_verified_long_liquidation_keeps_both_sides_independently() -> None:
    record = normalize_liquidation(_payload(provider_semantics_verified=True))
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.execution_side is AggressorSide.SELL


def test_a_verified_short_liquidation_keeps_both_sides_independently() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.SHORT,
            execution_side=AggressorSide.BUY,
            provider_semantics_verified=True,
        )
    )
    assert record.position_side_liquidated is LiquidationPositionSide.SHORT
    assert record.execution_side is AggressorSide.BUY


def test_position_side_never_implies_execution_side() -> None:
    """LONG with no execution evidence must not manufacture SELL (04 section 3.1)."""
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.LONG,
            execution_side=AggressorSide.UNKNOWN,
            provider_semantics_verified=True,
        )
    )
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.execution_side is AggressorSide.UNKNOWN


def test_execution_side_never_implies_position_side() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.UNKNOWN,
            execution_side=AggressorSide.SELL,
            provider_semantics_verified=True,
        )
    )
    assert record.execution_side is AggressorSide.SELL
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_uncertified_semantics_keep_the_canonical_slots_unknown() -> None:
    """The provider reading is provisional, not canonical (06 section 9)."""
    record = normalize_liquidation(_payload(provider_semantics_verified=False))
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN
    assert record.provisional_position_side is LiquidationPositionSide.LONG
    assert record.provisional_execution_side is AggressorSide.SELL
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED.value in _flag_values(record)


def test_native_provider_side_fields_are_preserved_verbatim() -> None:
    record = normalize_liquidation(
        _payload(
            native_position_side_field="side",
            native_position_side_value="LONG",
            native_execution_side_field="orderSide",
            native_execution_side_value="SELL",
        )
    )
    assert record.native_position_side_field == "side"
    assert record.native_position_side_value == "LONG"
    assert record.native_execution_side_value == "SELL"


def test_the_canonical_position_side_is_never_inferred_from_price() -> None:
    """A price observation cannot promote an unknown side (04 section 3.1, F17)."""
    low = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.UNKNOWN,
            execution_side=AggressorSide.UNKNOWN,
            price_native=Decimal("1.0001"),
        )
    )
    high = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.UNKNOWN,
            execution_side=AggressorSide.UNKNOWN,
            price_native=Decimal("999999"),
        )
    )
    assert low.position_side_liquidated is high.position_side_liquidated
    assert low.position_side_liquidated is LiquidationPositionSide.UNKNOWN


# ---------------------------------------------------------------------------
# I11-SIDE adversarial: contradictory evidence is quarantined, not reconciled
# ---------------------------------------------------------------------------


def test_long_liquidation_with_buy_execution_is_quarantined() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.LONG,
            execution_side=AggressorSide.BUY,
        )
    )
    assert record.normalization_status is NormalizationStatus.QUARANTINED
    assert record.missingness_reason is MissingnessReason.QUARANTINED
    assert record.quarantine_reason is QuarantineReason.INVALID_SIDE_MAPPING
    assert record.quarantine_evidence_refs == ("proj-1",)
    assert record.quarantine_remediation and record.quarantine_remediation.strip()
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_short_liquidation_with_sell_execution_is_quarantined() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.SHORT,
            execution_side=AggressorSide.SELL,
        )
    )
    assert record.normalization_status is NormalizationStatus.QUARANTINED
    assert record.quarantine_reason is QuarantineReason.INVALID_SIDE_MAPPING


def test_the_strict_form_raises_instead_of_quarantining() -> None:
    with pytest.raises(ContradictoryLiquidationSideError):
        require_consistent_liquidation_sides(
            LiquidationPositionSide.LONG, AggressorSide.BUY
        )
    require_consistent_liquidation_sides(
        LiquidationPositionSide.LONG, AggressorSide.SELL
    )
    require_consistent_liquidation_sides(
        LiquidationPositionSide.UNKNOWN, AggressorSide.BUY
    )


def test_a_quarantined_row_makes_no_canonical_side_claim() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.SHORT,
            execution_side=AggressorSide.SELL,
            provider_semantics_verified=True,
        )
    )
    assert record.execution_side is AggressorSide.UNKNOWN
    assert record.provisional_position_side is LiquidationPositionSide.SHORT


# ---------------------------------------------------------------------------
# I11-SCOPE (04 section 3.3): five tokens, count coherence
# ---------------------------------------------------------------------------


def test_the_five_frozen_aggregation_scopes_are_exactly_present() -> None:
    assert sorted(scope.value for scope in LiquidationAggregationScope) == [
        "EVENT_LEVEL",
        "INTERVAL_AGGREGATE",
        "PROVIDER_MULTI_EVENT_AGGREGATE",
        "TRADE_LEVEL",
        "UNKNOWN",
    ]


def test_an_aggregate_without_count_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="requires count"):
        _aggregate(count=None)


def test_an_event_with_a_count_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="must not carry count"):
        _payload(count=3)


def test_an_aggregate_may_not_carry_an_event_identity() -> None:
    with pytest.raises(ValueError, match="must not carry liquidation_event_id"):
        _aggregate(liquidation_event_id="liq-agg")


def test_provider_multi_event_aggregate_is_its_own_scope() -> None:
    record = normalize_liquidation(
        _aggregate(aggregation_scope=LiquidationAggregationScope.PROVIDER_MULTI_EVENT_AGGREGATE)
    )
    assert (
        record.aggregation_scope
        is LiquidationAggregationScope.PROVIDER_MULTI_EVENT_AGGREGATE
    )
    assert record.count == 7
    assert record.liquidation_event_id is None


def test_unknown_scope_neither_requires_nor_forbids_count() -> None:
    record = normalize_liquidation(
        _payload(
            aggregation_scope=LiquidationAggregationScope.UNKNOWN,
            count=None,
        )
    )
    assert record.aggregation_scope is LiquidationAggregationScope.UNKNOWN


# ---------------------------------------------------------------------------
# I11-AGGREGATE (04 section 3.4): positions side, never aggressor flow
# ---------------------------------------------------------------------------


def test_a_long_liquidation_aggregate_is_a_position_side_claim_not_aggressor_flow() -> None:
    record = normalize_liquidation(
        _aggregate(
            position_side_liquidated=LiquidationPositionSide.LONG,
            execution_side=AggressorSide.UNKNOWN,
            aggressor_side=AggressorSide.UNKNOWN,
            provider_semantics_verified=True,
        )
    )
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.aggressor_side is AggressorSide.UNKNOWN
    assert record.count == 7
    assert record.aggregation_scope is LiquidationAggregationScope.INTERVAL_AGGREGATE


def test_a_short_aggregate_never_becomes_buy_aggressor_flow() -> None:
    record = normalize_liquidation(
        _aggregate(
            position_side_liquidated=LiquidationPositionSide.SHORT,
            execution_side=AggressorSide.UNKNOWN,
            provider_semantics_verified=True,
        )
    )
    assert record.aggressor_side is AggressorSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN


def test_an_aggregate_is_never_expanded_into_one_event() -> None:
    record = normalize_liquidation(_aggregate())
    assert record.liquidation_event_id is None
    assert record.native_event_id is None
    assert record.count == 7


# ---------------------------------------------------------------------------
# I11-ROLE (04 section 3.2): maker/taker roles survive as their own field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "role",
    [LiquidationRole.MAKER, LiquidationRole.TAKER, LiquidationRole.BOTH, LiquidationRole.UNKNOWN],
)
def test_liquidation_roles_are_retained(role: LiquidationRole) -> None:
    record = normalize_liquidation(_payload(maker_taker_role=role))
    assert record.maker_taker_role is role


def test_an_absent_role_stays_absent_rather_than_unknown() -> None:
    record = normalize_liquidation(_payload(maker_taker_role=None))
    assert record.maker_taker_role is None


# ---------------------------------------------------------------------------
# I11-ZERO (04 section 3.5): verified zero versus missing
# ---------------------------------------------------------------------------


def test_a_verified_zero_interval_is_admitted() -> None:
    record = normalize_liquidation(
        _aggregate(
            quantity_native=Decimal("0"),
            count=0,
            provider_reports_completed_intervals=True,
            interval_closed=True,
            source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.VERIFIED_ZERO
    assert record.quantity_native == 0


def test_a_zero_without_completed_interval_claim_is_unverified() -> None:
    record = normalize_liquidation(
        _aggregate(
            quantity_native=Decimal("0"),
            count=0,
            provider_reports_completed_intervals=False,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING
    assert record.normalization_status is not NormalizationStatus.NORMALIZED


def test_a_zero_without_verified_coverage_is_unverified() -> None:
    record = normalize_liquidation(
        _aggregate(
            quantity_native=Decimal("0"),
            count=0,
            source_coverage_state=CoverageState.KNOWN_GAP,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING
    assert NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED.value in _flag_values(
        record
    )


def test_a_zero_on_an_open_interval_is_unverified() -> None:
    record = normalize_liquidation(
        _aggregate(quantity_native=Decimal("0"), count=0, interval_closed=False)
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING


def test_a_zero_event_scope_is_not_an_interval_claim() -> None:
    record = normalize_liquidation(
        _payload(
            quantity_native=Decimal("0"),
            aggregation_scope=LiquidationAggregationScope.EVENT_LEVEL,
            provider_reports_completed_intervals=True,
            interval_closed=True,
        )
    )
    assert record.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING


def test_an_unverified_zero_keeps_a_typed_missingness_cause() -> None:
    record = normalize_liquidation(
        _aggregate(quantity_native=Decimal("0"), count=0, interval_closed=None)
    )
    assert record.missingness_reason is MissingnessReason.SOURCE_GAP


def test_a_nonzero_aggregate_is_not_a_zero_interval() -> None:
    record = normalize_liquidation(_aggregate())
    assert record.zero_interval_state is LiquidationZeroIntervalState.NOT_APPLICABLE


def test_a_zero_cannot_be_built_without_declaring_its_state() -> None:
    from crypto_sensor_fabric.normalization.enums import LineageState
    from crypto_sensor_fabric.normalization.models import (
        ObservationTimeEnvelope,
        T1LineageRef,
        T1Quality,
        T1VersionContext,
    )
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.normalization.enums import QualityDimensionState

    with pytest.raises(ValueError, match="requires an explicit zero_interval_state"):
        T1LiquidationRecord(
            sensor_family=SensorFamily.MECHANICAL_LIQUIDATION,
            provider="p",
            venue="v",
            native_instrument="i",
            normalization_generation="g",
            source_revision_id="r",
            source_revision_state=RevisionState.STABLE,
            source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
            time=ObservationTimeEnvelope(),
            native_values=(),
            normalization_status=NormalizationStatus.NATIVE_ONLY,
            lineage_state=LineageState.LINEAGE_COMPLETE,
            lineage=T1LineageRef(
                raw_projection_refs=("p1",),
                acquisition_refs=("a1",),
                evidence_blob_hashes=(_DIGEST,),
                code_version="c",
                config_version="cf",
            ),
            quality=T1Quality(
                identity_quality=QualityDimensionState.PARTIAL,
                time_quality=QualityDimensionState.UNKNOWN,
                semantic_quality=QualityDimensionState.UNKNOWN,
                unit_quality=QualityDimensionState.UNKNOWN,
                lineage_quality=QualityDimensionState.VERIFIED,
                source_integrity_quality=QualityDimensionState.VERIFIED,
                coverage_quality=QualityDimensionState.UNKNOWN,
                replay_quality=QualityDimensionState.UNKNOWN,
            ),
            quality_flags=(
                NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
                NormalizationQualityFlag.LINEAGE_COMPLETE,
            ),
            versions=T1VersionContext(),
            quantity_native=Decimal("0"),
            quantity_native_unit="BTC",
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
            count=0,
        )


# ---------------------------------------------------------------------------
# I11-USD (04 section 3.3 + B5_I08_UNITS_V1)
# ---------------------------------------------------------------------------


def test_liquidation_usd_is_blocked_with_its_citation_preserved() -> None:
    record = normalize_liquidation(_payload())
    assert record.liquidation_usd is not None
    assert record.liquidation_usd.blocked is True
    assert record.liquidation_usd.value is None
    assert record.liquidation_usd.unresolved_citation == "B5_I08_UNITS_V1"


def test_no_stablecoin_parity_shortcut_produces_usd() -> None:
    """A USDT-denominated row must not become USD by assuming 1:1."""
    record = normalize_liquidation(_aggregate(quantity_native_unit="USDT"))
    assert record.liquidation_usd is not None and record.liquidation_usd.value is None
    assert record.liquidation_quote_notional is None


def test_unit_conversion_blocked_flag_is_present() -> None:
    record = normalize_liquidation(_payload())
    assert (
        NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED.value in _flag_values(record)
    )


# ---------------------------------------------------------------------------
# I11-PIT (03 sections 11-13): derived amounts refuse without evidence
# ---------------------------------------------------------------------------


def test_a_contract_denominated_liquidation_without_terms_blocks_the_base_quantity() -> None:
    record = normalize_liquidation(_payload(quantity_native_unit="CONTRACTS"))
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is True
    assert record.quantity_base.value is None
    assert record.quantity_base.missingness_reason is MissingnessReason.CONVERSION_BLOCKED


def test_a_base_denominated_liquidation_derives_nothing() -> None:
    record = normalize_liquidation(_payload(quantity_native_unit="BTC"))
    assert record.quantity_base is None
    assert record.liquidation_quote_notional is None


def test_price_native_is_preserved_and_is_not_a_reference_price() -> None:
    record = normalize_liquidation(_payload(price_native=Decimal("61234.5")))
    assert record.price_native == Decimal("61234.5")
    assert record.price_reference is None
    assert any(
        native.native_field_name == "price" for native in record.native_values
    )


# ---------------------------------------------------------------------------
# I11-IDENTITY / I11-LINEAGE
# ---------------------------------------------------------------------------


def test_a_missing_event_id_is_flagged_not_invented() -> None:
    record = normalize_liquidation(
        _payload(
            liquidation_event_id=None,
            aggregation_scope=LiquidationAggregationScope.TRADE_LEVEL,
        )
    )
    assert record.liquidation_event_id is None
    assert NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING.value in _flag_values(
        record
    )
    assert NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY.value in _flag_values(record)


def test_the_event_id_and_native_identity_are_carried() -> None:
    record = normalize_liquidation(_payload())
    assert record.liquidation_event_id == "liq-1"
    assert record.native_event_id == "liq-1"


def test_lineage_references_survive_unchanged() -> None:
    record = normalize_liquidation(_payload())
    assert record.lineage.raw_projection_refs == ("proj-1",)
    assert record.lineage.acquisition_refs == ("acq-1",)
    assert record.lineage.evidence_blob_hashes == (_DIGEST,)
    assert record.source_revision_id == "rev-1"
    assert record.source_revision_state is RevisionState.STABLE
    assert record.source_coverage_state is CoverageState.COMPLETE_SOURCE_BOUNDARY


def test_no_duplicate_collapse_verdict_is_produced() -> None:
    record = normalize_liquidation(_payload())
    for forbidden in ("DUPLICATE_CONFIRMED", "DUPLICATE_CANDIDATE"):
        assert forbidden not in _flag_values(record)


def test_cross_venue_rows_stay_distinct() -> None:
    a = normalize_liquidation(_payload(venue="BINANCE"))
    b = normalize_liquidation(_payload(venue="BYBIT"))
    assert a.canonical_json() != b.canonical_json()
    assert a.venue == "BINANCE" and b.venue == "BYBIT"


# ---------------------------------------------------------------------------
# I11-INTERFACE: determinism, scope, sensor family
# ---------------------------------------------------------------------------


def test_normalization_is_deterministic() -> None:
    first = normalize_liquidation(_payload())
    second = normalize_liquidation(_payload())
    assert first.canonical_json() == second.canonical_json()


def test_the_record_is_bound_to_the_liquidation_sensor_family() -> None:
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    record = normalize_liquidation(_payload())
    assert record.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION


def test_a_contract_instance_mismatch_is_refused() -> None:
    class _Terms:
        contract_instance_id = "ci-other"

    with pytest.raises(ValueError, match="contradicts the PIT terms"):
        normalize_liquidation(
            _payload(contract_instance_id="ci-1"),
            terms=_Terms(),  # type: ignore[arg-type]
        )


def test_the_record_rejects_a_trade_sensor_family() -> None:
    record = normalize_liquidation(_payload())
    dumped = record.model_dump()
    dumped["sensor_family"] = "MECHANICAL_TRADE"
    with pytest.raises(ValueError, match="MECHANICAL_LIQUIDATION"):
        T1LiquidationRecord(**dumped)

def test_the_accepted_i04b_primitives_are_imported_not_reimplemented() -> None:
    """A11-12: I11 reuses the accepted conversion primitives by import."""
    from crypto_sensor_fabric.normalization.sensors import liquidation as module
    from crypto_sensor_fabric.normalization.terms import conversion

    for name in (
        "linear_base_exposure",
        "contracts_to_quote_notional",
        "inverse_quote_face",
        "inverse_base_from_quote",
    ):
        assert getattr(module, name) is getattr(conversion, name), name


def test_no_conversion_arithmetic_is_reimplemented_in_the_module() -> None:
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "crypto_sensor_fabric"
        / "normalization"
        / "sensors"
        / "liquidation.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("* multiplier", "/ price", "ROUND_HALF"):
        assert forbidden not in text, forbidden
