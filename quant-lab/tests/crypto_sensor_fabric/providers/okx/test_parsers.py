"""SENSOR-B3-I07C — OKX provider-native parser tests.

Proves timestamp schema (ms-epoch STRING strictness: None/bool/int/float fail
closed, no silent coercion), per-sensor native field preservation, additive vs
breaking drift, and that parsers NEVER emit canonical/research fields.
"""

from __future__ import annotations

from crypto_sensor_fabric.providers.base.enums import SchemaState
from crypto_sensor_fabric.providers.okx.parsers import (
    parse_okx_book,
    parse_okx_funding,
    parse_okx_trades,
)
from crypto_sensor_fabric.contracts.enums import SensorFamily

from .fixtures import responses as FX


class TestFundingParser:
    def test_happy_preserves_native_fields(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.semantic_output_allowed is True
        assert len(parsed.rows) == 3
        row = parsed.rows[0]
        assert "fundingTime" in row and isinstance(row["fundingTime"], str)
        assert "fundingRate" in row
        assert "realizedRate" in row
        assert "formulaType" in row
        assert "method" in row

    def test_empty_is_empty_valid(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_additive_allowed(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_ADDITIVE)
        assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is True

    def test_bad_timestamp_fails_closed(self) -> None:
        for fx in (FX.FUNDING_BAD_TIMESTAMP, FX.FUNDING_NONE_TIMESTAMP, FX.FUNDING_BOOL_TIMESTAMP):
            parsed = parse_okx_funding(fx)
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
            assert parsed.semantic_output_allowed is False
            assert parsed.rows == ()

    def test_missing_required_field_breaks(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_MISSING_REQUIRED)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_drift_unknown(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_DRIFT)
        assert parsed.schema_state in (
            SchemaState.BREAKING_SCHEMA_CHANGE,
            SchemaState.UNKNOWN_SCHEMA,
        )

    def test_no_canonical_field_emitted(self) -> None:
        parsed = parse_okx_funding(FX.FUNDING_HAPPY)
        for row in parsed.rows:
            assert not any(k.startswith(("canonical_", "funding_state")) for k in row)


class TestTradeParser:
    def test_happy_preserves_native_trade_fields(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        row = parsed.rows[0]
        assert row["tradeId"] == "500003"
        assert row["px"] == "29512.0"
        assert row["sz"] == "0.5"
        assert row["side"] == "sell"  # native aggressor side preserved verbatim
        assert isinstance(row["ts"], str)
        assert "source" in row

    def test_side_never_reinterpreted(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_HAPPY)
        assert {r["side"] for r in parsed.rows} == {"buy", "sell"}
        # no flow/CVD/buy-pressure synthesis
        for r in parsed.rows:
            assert not any(k.startswith(("cvd", "flow", "buy_pressure", "sell_pressure")) for k in r)

    def test_empty_is_empty_valid(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_int_timestamp_fails_closed(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_BAD_TIMESTAMP)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is False

    def test_missing_side_breaks(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_MISSING_SIDE)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_additive_allowed(self) -> None:
        parsed = parse_okx_trades(FX.TRADE_ADDITIVE)
        assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE


class TestBookParser:
    def test_happy_preserves_book_rows(self) -> None:
        parsed = parse_okx_book(FX.BOOK_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 1
        book = parsed.rows[0]
        assert isinstance(book["asks"], list)
        assert isinstance(book["asks"][0], list)
        assert book["bids"][0][0] == "29498.0"  # native [px, sz, ...]
        assert isinstance(book["ts"], str)
        assert book["seqId"] == 1001

    def test_empty_is_empty_valid(self) -> None:
        parsed = parse_okx_book(FX.BOOK_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_int_timestamp_fails_closed(self) -> None:
        parsed = parse_okx_book(FX.BOOK_BAD_TIMESTAMP)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_none_timestamp_fails_closed(self) -> None:
        parsed = parse_okx_book(FX.BOOK_NONE_TIMESTAMP)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_missing_bids_breaks(self) -> None:
        parsed = parse_okx_book(FX.BOOK_MISSING_BIDS)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_bad_level_shape_breaks(self) -> None:
        parsed = parse_okx_book(FX.BOOK_BAD_LEVEL)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_no_derived_signal_emitted(self) -> None:
        parsed = parse_okx_book(FX.BOOK_HAPPY)
        for row in parsed.rows:
            assert not any(k.startswith(("imbalance", "spread", "depth_", "slippage")) for k in row)
            assert SensorFamily.MECHANICAL_BOOK_SNAPSHOT.value not in "".join(map(str, row.values()))


class TestSchemaStateTaxonomy:
    def test_known_additive_breaking_covered(self) -> None:
        states = {
            parse_okx_funding(FX.FUNDING_HAPPY).schema_state,
            parse_okx_funding(FX.FUNDING_ADDITIVE).schema_state,
            parse_okx_funding(FX.FUNDING_BAD_TIMESTAMP).schema_state,
        }
        assert SchemaState.KNOWN_SCHEMA in states
        assert SchemaState.ADDITIVE_SCHEMA_CHANGE in states
        assert SchemaState.BREAKING_SCHEMA_CHANGE in states

    def test_no_silent_default_to_zero(self) -> None:
        # a malformed/missing field must NOT be coerced to 0/False/''/[]
        parsed = parse_okx_funding(FX.FUNDING_MISSING_REQUIRED)
        assert parsed.rows == ()
        parsed = parse_okx_trades(FX.TRADE_MISSING_SIDE)
        assert parsed.rows == ()