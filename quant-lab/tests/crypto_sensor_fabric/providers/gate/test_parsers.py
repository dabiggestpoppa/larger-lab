"""SENSOR-B3-I06 — Gate provider-native parser tests.

Parser doctrine: native fields/units only, no canonicalization.  OI / LIQUIDATION
/ POSITIONING project sensor-specific subsets from the shared /contract_stats
physical row.  Timestamps are strict: contract_stats `time` int epoch SECONDS
(current contract; I05-era sample was ms — I10R1 transition), funding `t`
int seconds — string/float/bool/None fail closed.  Numeric semantic family
(int|float) accepted; missing required structural fields fail.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import SchemaState
from crypto_sensor_fabric.providers.gate.parsers import (
    parse_gate_contract_stats,
    parse_gate_funding,
)

from .fixtures import responses as FX

OI = SensorFamily.MECHANICAL_OPEN_INTEREST
LIQ = SensorFamily.MECHANICAL_LIQUIDATION
POS = SensorFamily.MECHANICAL_POSITIONING
FUNDING = SensorFamily.MECHANICAL_FUNDING


class TestOpenInterestProjection:
    def test_oi_happy_known(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, OI)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.semantic_output_allowed is True
        assert len(parsed.rows) == 2
        row = parsed.rows[0]
        assert row["time"] == 1755000000  # native seconds preserved
        assert row["open_interest"] == 12500
        assert row["open_interest_usd"] == 812500000.5
        # NO cross-sensor leakage into the OI view
        assert "lsr_taker" not in row
        assert "long_liq_size" not in row

    def test_oi_empty_valid(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_EMPTY, OI)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()


class TestLiquidationProjection:
    def test_liquidation_long_short_orientation_preserved(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, LIQ)
        row = parsed.rows[0]
        # long/short NOT inverted, no taker-side reinterpretation
        assert row["long_liq_size"] == 5
        assert row["short_liq_size"] == 4
        assert row["long_liq_usd"] == 500000.5
        assert row["short_liq_usd"] == 400000.0
        # contract fields (sizes) remain distinct from USD fields
        assert row["long_liq_size"] != row["long_liq_usd"]
        assert row["short_liq_size"] != row["short_liq_usd"]
        # current contract: native `time` is epoch SECONDS
        assert row["time"] == 1755000000

    def test_liquidation_does_not_leak_other_sensor_fields(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, LIQ)
        row = parsed.rows[0]
        assert "lsr_taker" not in row
        assert "open_interest" not in row


class TestPositioningProjection:
    def test_public_lsr_fields_preserved(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, POS)
        row = parsed.rows[0]
        assert row["lsr_taker"] == 1.15
        assert row["lsr_account"] == 1.25
        assert row["top_lsr_account"] == 1.4
        assert row["top_lsr_size"] == 4000.0
        assert row["top_long_size"] == 3000
        assert row["top_short_size"] == 2500
        assert row["long_users"] == 120
        assert row["short_users"] == 95
        # no private-position semantics collapse into one score
        assert "lsr_taker" in row and "lsr_account" in row

    def test_positioning_does_not_leak_liquidation_fields(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, POS)
        row = parsed.rows[0]
        assert "long_liq_size" not in row
        assert "open_interest" not in row


class TestFundingProjection:
    def test_funding_native_r_t_preserved(self) -> None:
        parsed = parse_gate_funding(FX.FUNDING_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        row = parsed.rows[0]
        assert row["r"] == "0.000100"  # native string decimal
        assert row["t"] == 1755000000  # native epoch SECONDS

    def test_funding_empty_valid(self) -> None:
        parsed = parse_gate_funding(FX.FUNDING_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()


class TestNumericSemanticFamily:
    def test_int_vs_float_mark_price_both_valid(self) -> None:
        # int and float both belong to the same numeric family per fingerprints
        int_row = {**FX.contract_stats_row(), "mark_price": 65000}
        float_row = {**FX.contract_stats_row(), "mark_price": 65000.0}
        assert parse_gate_contract_stats([int_row], OI).schema_state is SchemaState.KNOWN_SCHEMA
        assert parse_gate_contract_stats([float_row], OI).schema_state is SchemaState.KNOWN_SCHEMA

    def test_string_mark_price_not_silently_coerced(self) -> None:
        bad = {**FX.contract_stats_row(), "mark_price": "65000"}
        # mark_price is not a required OI field, but the OI-required fields are
        # present+typed, so this stays KNOWN; a directly required field string
        # coercion is exercised below.
        assert parse_gate_contract_stats([bad], OI).schema_state is SchemaState.KNOWN_SCHEMA

    def test_string_required_numeric_fails_closed(self) -> None:
        bad = {**FX.contract_stats_row(), "open_interest_usd": "812500000.5"}
        parsed = parse_gate_contract_stats([bad], OI)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is False
        assert parsed.rows == ()


class TestStructuralFailClosed:
    def test_missing_required_field_breaks(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_MISSING_FIELD, OI)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_top_level_object_unknown(self) -> None:
        parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_DRIFT, OI)
        assert parsed.schema_state is SchemaState.UNKNOWN_SCHEMA
        assert parsed.rows == ()

    def test_funding_missing_t_breaks(self) -> None:
        parsed = parse_gate_funding(FX.FUNDING_MISSING_T)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()


class TestTimestampSchema:
    def test_contract_stats_time_strict_int_ms(self) -> None:
        # bad_time is string ms -> BREAKING; none_time -> BREAKING
        assert (
            parse_gate_contract_stats(FX.CONTRACT_STATS_BAD_TIME, OI).schema_state
            is SchemaState.BREAKING_SCHEMA_CHANGE
        )
        assert (
            parse_gate_contract_stats(FX.CONTRACT_STATS_NONE_TIME, OI).schema_state
            is SchemaState.BREAKING_SCHEMA_CHANGE
        )

    def test_funding_t_strict_int_seconds(self) -> None:
        assert parse_gate_funding(FX.FUNDING_BAD_T).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parse_gate_funding(FX.FUNDING_NONE_T).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        # bool is an int subclass in Python but NOT a valid timestamp
        assert parse_gate_funding(FX.FUNDING_BOOL_T).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE


class TestAdditive:
    def test_extra_field_is_additive_and_still_parses(self) -> None:
        for sensor in (OI, LIQ, POS):
            parsed = parse_gate_contract_stats(FX.CONTRACT_STATS_ADDITIVE, sensor)
            assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
            assert parsed.semantic_output_allowed is True
            assert parsed.rows

    def test_parser_never_canonicalizes(self) -> None:
        for sensor in (OI, LIQ, POS):
            row = parse_gate_contract_stats(FX.CONTRACT_STATS_HAPPY, sensor).rows[0]
            assert "oiUsd" not in row and "openInterestUsd" not in row
            assert "cvd" not in row and "aggressorImbalance" not in row
            assert "liquidationState" not in row and "fundingState" not in row
            assert "positioningState" not in row and "signAsymmetry" not in row