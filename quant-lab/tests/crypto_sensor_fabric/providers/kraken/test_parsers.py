"""SENSOR-B3-I05 — Kraken Market Analytics parser tests.

Parser doctrine: providers emit native fields/units only; never canonical OI USD,
cross-venue CVD, LiquidationState/FundingState/PositioningState or research
features.  KNOWN/ADDITIVE produce rows; BREAKING/UNKNOWN block (no zero
coercion).  Empty-valid stays a first-class state.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import SchemaState
from crypto_sensor_fabric.providers.kraken.parsers import parse_kraken_analytics

from .fixtures import analytics as FX


class TestListShape:
    def test_open_interest_happy(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["open_interest"][1], SensorFamily.MECHANICAL_OPEN_INTEREST)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 2
        assert parsed.rows[0]["timestamp"] == 1755000000
        assert parsed.rows[0]["value"] == ["725.3"]
        assert parsed.more is False

    def test_positioning_happy(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["positioning"][1], SensorFamily.MECHANICAL_POSITIONING)
        assert parsed.rows[0]["value"] == "1.245"

    def test_liquidation_happy(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["liquidation"][1], SensorFamily.MECHANICAL_LIQUIDATION)
        assert parsed.rows[0]["value"] == "150000.0"

    def test_continuation_flag(self) -> None:
        parsed = parse_kraken_analytics(FX.CONTINUE["open_interest"][1], SensorFamily.MECHANICAL_OPEN_INTEREST)
        assert parsed.more is True


class TestDictShape:
    def test_funding_happy_preserves_native_metrics(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["funding"][1], SensorFamily.MECHANICAL_FUNDING)
        assert parsed.rows[0]["rate"] == ["0.0001"]
        assert parsed.rows[0]["relativeRate"] == ["0.0001"]
        # funding bucket timestamps are epoch seconds per committed probe
        # fixture + live probe contract (I13R1 fingerprint pins int only)
        assert parsed.rows[0]["timestamp"] == 1755000000

    def test_basis_happy(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["basis"][1], SensorFamily.MECHANICAL_BASIS)
        assert parsed.rows[0]["basis"] == "0.001"

    def test_book_metric_happy(self) -> None:
        parsed = parse_kraken_analytics(FX.HAPPY["book_metric"][1], SensorFamily.MECHANICAL_BOOK_METRIC)
        assert parsed.rows[0]["ask"]["bestPrice"] == "1000.0"
        assert parsed.rows[0]["bid"]["bestPrice"] == "1000.0"


class TestEmptyValid:
    def test_open_interest_empty(self) -> None:
        parsed = parse_kraken_analytics(FX.EMPTY["open_interest"][1], SensorFamily.MECHANICAL_OPEN_INTEREST)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_funding_empty(self) -> None:
        parsed = parse_kraken_analytics(FX.EMPTY["funding"][1], SensorFamily.MECHANICAL_FUNDING)
        # rate present -> ADDITIVE (relativeRate extra); still parses, zero rows
        assert parsed.schema_state in (SchemaState.KNOWN_SCHEMA, SchemaState.ADDITIVE_SCHEMA_CHANGE)
        assert parsed.semantic_output_allowed is True
        assert parsed.rows == ()

    def test_basis_empty(self) -> None:
        parsed = parse_kraken_analytics(FX.EMPTY["basis"][1], SensorFamily.MECHANICAL_BASIS)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()


class TestSchemaDriftFailClosed:
    def test_open_interest_wrong_data_type_unknown(self) -> None:
        parsed = parse_kraken_analytics(FX.DRIFT["open_interest"][1], SensorFamily.MECHANICAL_OPEN_INTEREST)
        assert parsed.schema_state is SchemaState.UNKNOWN_SCHEMA
        assert parsed.rows == ()

    def test_funding_missing_rate_breaking(self) -> None:
        parsed = parse_kraken_analytics(FX.DRIFT["funding"][1], SensorFamily.MECHANICAL_FUNDING)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_basis_missing_basis_breaking(self) -> None:
        parsed = parse_kraken_analytics(FX.DRIFT["basis"][1], SensorFamily.MECHANICAL_BASIS)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_book_metric_missing_bid_breaking(self) -> None:
        parsed = parse_kraken_analytics(FX.DRIFT["book_metric"][1], SensorFamily.MECHANICAL_BOOK_METRIC)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_unknown_envelope(self) -> None:
        parsed = parse_kraken_analytics({"unexpected": 1}, SensorFamily.MECHANICAL_BASIS)
        assert parsed.schema_state is SchemaState.UNKNOWN_SCHEMA


class TestParserNeverCanonicalizes:
    def test_no_canonical_or_research_fields_emitted(self) -> None:
        for key, body in ((k, FX.HAPPY[k][1]) for k in ("open_interest", "funding", "basis", "book_metric", "positioning", "liquidation")):
            sensor = {
                "open_interest": SensorFamily.MECHANICAL_OPEN_INTEREST,
                "funding": SensorFamily.MECHANICAL_FUNDING,
                "basis": SensorFamily.MECHANICAL_BASIS,
                "book_metric": SensorFamily.MECHANICAL_BOOK_METRIC,
                "positioning": SensorFamily.MECHANICAL_POSITIONING,
                "liquidation": SensorFamily.MECHANICAL_LIQUIDATION,
            }[key]
            parsed = parse_kraken_analytics(body, sensor)
            for row in parsed.rows:
                assert "oiUsd" not in row and "openInterestUsd" not in row
                assert "cvd" not in row and "aggressorImbalance" not in row
                assert "liquidationState" not in row and "fundingState" not in row
                assert "signAsymmetry" not in row
                # only legitimately native keys expected
                assert set(row) <= {"timestamp", "value", "rate", "relativeRate", "basis", "ask", "bid"}