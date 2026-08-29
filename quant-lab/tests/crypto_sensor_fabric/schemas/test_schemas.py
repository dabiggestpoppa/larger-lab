"""Sensor-schema validation tests (B1-T10 .. B1-T17) and the
no-default-zero invariant (B1-T50)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from crypto_sensor_fabric.contracts.base import (
    CanonicalObservationBase,
    MissingObservation,
)
from crypto_sensor_fabric.contracts.enums import (
    AggressorSide,
    LiquidationEventShape,
    NativeOIUnit,
    QualityFlag,
)
from crypto_sensor_fabric.schemas import (
    MechanicalBasis,
    MechanicalBookMetric,
    MechanicalBookSnapshot,
    MechanicalFunding,
    MechanicalLiquidation,
    MechanicalOpenInterest,
    MechanicalPositioning,
    MechanicalTrade,
    PriceLevel,
    ProviderEnvelope,
)
from pydantic import ValidationError

# Every canonical schema model (and envelope/level models) for the
# no-default-zero sweep (B1-T50).
SCHEMA_MODELS = [
    CanonicalObservationBase,
    ProviderEnvelope,
    PriceLevel,
    MechanicalTrade,
    MechanicalLiquidation,
    MechanicalOpenInterest,
    MechanicalFunding,
    MechanicalBookSnapshot,
    MechanicalBookMetric,
    MechanicalPositioning,
    MechanicalBasis,
    MissingObservation,
]


# ---------------------------------------------------------------------------
# B1-T50 — no default zero
# ---------------------------------------------------------------------------


def test_t50_no_default_zero_fields():
    for model_cls in SCHEMA_MODELS:
        for name, field in model_cls.model_fields.items():
            if field.default is not None:
                assert field.default != 0, (
                    f"{model_cls.__name__}.{name} fabricates a numeric zero default (B1-T50)"
                )
            if field.default_factory is not None:
                produced = field.default_factory()
                assert not isinstance(produced, (int, float)) or produced != 0, (
                    f"{model_cls.__name__}.{name} default factory fabricates zero (B1-T50)"
                )


# ---------------------------------------------------------------------------
# B1-T10 — trade side unknown allowed
# ---------------------------------------------------------------------------


def test_t10_trade_unknown_side_preserved(load_model):
    trade = load_model(MechanicalTrade, "trade_unknown_side.json")
    assert trade.aggressor_side is AggressorSide.UNKNOWN
    assert trade.maker_side is AggressorSide.UNKNOWN


def test_t10_trade_unknown_side_never_guessed(load_model):
    trade = load_model(MechanicalTrade, "trade_unknown_side.json")
    dumped = trade.model_dump(mode="json")
    assert dumped["aggressor_side"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# B1-T11 — liquidation shape separation
# ---------------------------------------------------------------------------


def test_t11_liquidation_shapes_distinct(load_model):
    trade_level = load_model(MechanicalLiquidation, "liquidation_trade_level.json")
    interval = load_model(MechanicalLiquidation, "liquidation_interval_aggregate.json")
    assert trade_level.event_shape is LiquidationEventShape.TRADE_LEVEL
    assert interval.event_shape is LiquidationEventShape.INTERVAL_AGGREGATE
    assert trade_level.event_shape != interval.event_shape


def test_t11_shape_survives_serialization(load_model):
    for fixture in ("liquidation_trade_level.json", "liquidation_interval_aggregate.json"):
        model = load_model(MechanicalLiquidation, fixture)
        round_tripped = MechanicalLiquidation.model_validate(model.model_dump(mode="json"))
        assert round_tripped.event_shape == model.event_shape


def test_t11_trade_level_is_not_interval_by_coercion(load_model):
    interval = load_model(MechanicalLiquidation, "liquidation_interval_aggregate.json")
    # A trade-level record must not silently adopt interval aggregate semantics:
    # building a trade-level liquidation from the aggregate payload keeps shape.
    aggregate_payload = interval.model_dump(mode="json")
    aggregate_payload["event_shape"] = "TRADE_LEVEL"
    trade_level = MechanicalLiquidation.model_validate(aggregate_payload)
    assert trade_level.event_shape is LiquidationEventShape.TRADE_LEVEL
    # and its numeric fields stay exactly what the source provided
    assert trade_level.liquidation_usd == interval.liquidation_usd


# ---------------------------------------------------------------------------
# B1-T12 / B1-T13 — OI native preservation + unresolved normalization
# ---------------------------------------------------------------------------


def test_t12_oi_native_preserved(load_model):
    oi = load_model(MechanicalOpenInterest, "oi_contracts_native.json")
    assert oi.oi_native == 125000
    assert oi.native_unit is NativeOIUnit.CONTRACTS
    assert oi.oi_base == 1250
    assert oi.oi_usd == 82000000


def test_t13_oi_unresolved_normalization_stays_null(load_model):
    oi = load_model(MechanicalOpenInterest, "oi_unresolved_units.json")
    assert oi.oi_base is None
    assert oi.oi_quote is None
    assert oi.oi_usd is None
    assert QualityFlag.UNIT_NORMALIZATION_UNAVAILABLE in oi.quality_flags


def test_t13_oi_unresolved_never_becomes_zero(load_model):
    oi = load_model(MechanicalOpenInterest, "oi_unresolved_units.json")
    dumped = oi.model_dump(mode="json")
    assert dumped["oi_usd"] is None


def test_t13_normalized_fields_require_methodology():
    payload = {
        "observation_id": "x",
        "provider": "P",
        "venue": "V",
        "sensor_family": "MECHANICAL_OPEN_INTEREST",
        "evidence_class": "FIRST_PARTY_EXCHANGE",
        "retrieval_mode": "REST",
        "instrument_native": "BTC-USDT-PERP",
        "instrument_id_canonical": "C:1",
        "market_type": "PERPETUAL",
        "effective_at": "2024-03-01T12:00:00Z",
        "observed_at": "2024-03-01T12:00:00Z",
        "ingested_at": "2024-03-05T08:00:00Z",
        "endpoint_id": "E",
        "raw_object_uri": "file://x",
        "raw_checksum": "sha256:00",
        "access_class": "FREE_AUTOMATED",
        "semantic_equivalence": "NORMALIZABLE_COMPARABLE",
        "adapter_version": "0.1.0",
        "schema_version": "1.0.0",
        "oi_native": 100,
        "native_unit": "CONTRACTS",
        "oi_usd": 6500000,
        "normalization_method": None,
    }
    with pytest.raises(ValidationError, match="normalization_method"):
        MechanicalOpenInterest.model_validate(payload)


# ---------------------------------------------------------------------------
# B1-T14 — funding native preservation
# ---------------------------------------------------------------------------


def test_t14_funding_8h_equivalent_requires_native(load_model):
    funding = load_model(MechanicalFunding, "funding_8h_native.json")
    assert funding.funding_rate_native == Decimal("0.0001")
    assert funding.funding_rate_8h_equivalent == Decimal("0.0001")


def test_t14_funding_8h_equivalent_without_native_fails():
    payload = {
        "observation_id": "x",
        "provider": "P",
        "venue": "V",
        "evidence_class": "FIRST_PARTY_EXCHANGE",
        "retrieval_mode": "REST",
        "instrument_native": "BTC-USDT-PERP",
        "instrument_id_canonical": "C:1",
        "market_type": "PERPETUAL",
        "effective_at": "2024-03-01T12:00:00Z",
        "observed_at": "2024-03-01T12:00:00Z",
        "ingested_at": "2024-03-05T08:00:00Z",
        "endpoint_id": "E",
        "raw_object_uri": "file://x",
        "raw_checksum": "sha256:00",
        "access_class": "FREE_AUTOMATED",
        "semantic_equivalence": "NORMALIZABLE_COMPARABLE",
        "adapter_version": "0.1.0",
        "schema_version": "1.0.0",
        "funding_rate_native": None,
        "funding_rate_8h_equivalent": 0.0001,
    }
    with pytest.raises(ValidationError):
        MechanicalFunding.model_validate(payload)


# ---------------------------------------------------------------------------
# B1-T15 — book source-depth semantics
# ---------------------------------------------------------------------------


def test_t15_book_snapshot_requires_depth_definition(load_model, load_fixture):
    payload = load_fixture("book_snapshot_l2.json")
    payload["source_depth_definition"] = ""
    with pytest.raises(ValidationError):
        MechanicalBookSnapshot.model_validate(payload)


def test_t15_book_snapshot_valid_with_depth_definition(load_model):
    book = load_model(MechanicalBookSnapshot, "book_snapshot_l2.json")
    assert book.source_depth_definition == "L2_TOP_50_LEVELS"
    assert book.bids[0].price == 61230.0


# ---------------------------------------------------------------------------
# B1-T16 — book metrics require methodology
# ---------------------------------------------------------------------------


def test_t16_book_metric_requires_methodology_id(load_fixture):
    payload = load_fixture("book_metric_provider.json")
    payload["methodology_id"] = ""
    with pytest.raises(ValidationError):
        MechanicalBookMetric.model_validate(payload)


def test_t16_book_metric_validates_with_methodology(load_model):
    metric = load_model(MechanicalBookMetric, "book_metric_provider.json")
    assert metric.methodology_id == "PROVIDER_ANALYTICS_PASSTHROUGH_V1"
    recon = load_model(MechanicalBookMetric, "book_metric_reconstructed.json")
    assert recon.methodology_id == "DEPTH_BPS_RECONSTRUCTION_V1"
    assert recon.methodology_id != metric.methodology_id


# ---------------------------------------------------------------------------
# B1-T17 — positioning population
# ---------------------------------------------------------------------------


def test_t17_positioning_requires_population(load_fixture):
    payload = load_fixture("positioning_top_trader.json")
    payload["population_definition"] = ""
    with pytest.raises(ValidationError):
        MechanicalPositioning.model_validate(payload)


def test_t17_positioning_valid_with_population(load_model):
    positioning = load_model(MechanicalPositioning, "positioning_top_trader.json")
    assert positioning.population_definition == "TOP_100_ACCOUNTS_BY_POSITION"


# ---------------------------------------------------------------------------
# Fixture integrity sweep — every committed fixture validates, and the pinned
# sensor family survives validation even if the payload disagrees.
# ---------------------------------------------------------------------------

FIXTURE_MODEL_MAP = {
    "trade_valid.json": MechanicalTrade,
    "trade_unknown_side.json": MechanicalTrade,
    "liquidation_trade_level.json": MechanicalLiquidation,
    "liquidation_interval_aggregate.json": MechanicalLiquidation,
    "oi_contracts_native.json": MechanicalOpenInterest,
    "oi_usd_native.json": MechanicalOpenInterest,
    "oi_unresolved_units.json": MechanicalOpenInterest,
    "funding_8h_native.json": MechanicalFunding,
    "funding_non8h_native.json": MechanicalFunding,
    "book_snapshot_l2.json": MechanicalBookSnapshot,
    "book_metric_provider.json": MechanicalBookMetric,
    "book_metric_reconstructed.json": MechanicalBookMetric,
    "positioning_top_trader.json": MechanicalPositioning,
    "basis_valid.json": MechanicalBasis,
    "identity_unresolved.json": MechanicalLiquidation,
}


@pytest.mark.parametrize("fixture", sorted(FIXTURE_MODEL_MAP))
def test_fixtures_all_validate(fixture, load_model):
    model_cls = FIXTURE_MODEL_MAP[fixture]
    model = load_model(model_cls, fixture)
    assert model.observation_id.startswith("fixture-")


def test_sensor_family_pinned_to_concrete_schema(load_model):
    """A MechanicalTrade cannot validate as another family (B1 failure rule 1)."""
    trade = load_model(MechanicalTrade, "trade_valid.json")
    assert trade.sensor_family.value == "MECHANICAL_TRADE"
    liq = load_model(MechanicalLiquidation, "liquidation_trade_level.json")
    assert liq.sensor_family.value == "MECHANICAL_LIQUIDATION"


# ---------------------------------------------------------------------------
# SENSOR-B1-R04 (optional hardening) — explicit family mismatch fails closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture, wrong_family",
    [
        ("trade_valid.json", "MECHANICAL_FUNDING"),
        ("liquidation_trade_level.json", "MECHANICAL_TRADE"),
        ("oi_contracts_native.json", "MECHANICAL_BOOK_METRIC"),
        ("funding_8h_native.json", "MECHANICAL_LIQUIDATION"),
        ("book_snapshot_l2.json", "MECHANICAL_BASIS"),
        ("book_metric_provider.json", "MECHANICAL_POSITIONING"),
        ("positioning_top_trader.json", "MECHANICAL_OPEN_INTEREST"),
        ("basis_valid.json", "MECHANICAL_TRADE"),
    ],
)
def test_r04_explicit_sensor_family_mismatch_fails(fixture, wrong_family, load_fixture):
    """An explicitly supplied wrong sensor_family fails validation instead of
    being silently replaced by the subclass's pinned family."""
    payload = load_fixture(fixture)
    payload["sensor_family"] = wrong_family
    model_cls = FIXTURE_MODEL_MAP[fixture]
    with pytest.raises(ValidationError, match="does not match"):
        model_cls.model_validate(payload)
