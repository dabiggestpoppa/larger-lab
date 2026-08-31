"""SENSOR-B3-I08C — Deribit provider-native parser tests.

Proves timestamp schema (epoch-ms INT strictness: None/bool/float/string fail
closed, no silent coercion), per-sensor native field preservation, additive vs
breaking drift, closed-record required-field strictness (trade 13 / funding 5 /
book core 4), the trade/liquidation shared-surface projection (liquidation
view = ONLY rows carrying the evidence-backed forced-liquidation flag), book
level minimum [price, amount], funding raw-list envelope (NOT {data:[...]}),
and that parsers NEVER emit canonical/aggregate/research fields.
"""

from __future__ import annotations

import pytest

from crypto_sensor_fabric.providers.base.enums import SchemaState
from crypto_sensor_fabric.providers.deribit.parsers import (
    parse_deribit_book,
    parse_deribit_funding,
    parse_deribit_liquidations,
    parse_deribit_trades,
)

from .fixtures import responses as FX

TRADE_FINGERPRINT_FIELDS = (
    "amount",
    "contracts",
    "direction",
    "index_price",
    "instrument_name",
    "mark_price",
    "price",
    "starbase_match_id",
    "starbase_timestamp",
    "tick_direction",
    "timestamp",
    "trade_id",
    "trade_seq",
)
FUNDING_FINGERPRINT_FIELDS = (
    "index_price",
    "interest_1h",
    "interest_8h",
    "prev_index_price",
    "timestamp",
)


def _drop_trade_field(field: str) -> dict:
    return FX._ok_result(
        FX._trades_result(
            [{k: v for k, v in FX.trade_row(FX.T1).items() if k != field}]
        )
    )


class TestTradeParser:
    def test_happy_preserves_native_fields(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.semantic_output_allowed is True
        assert len(parsed.rows) == 3
        row = parsed.rows[0]
        assert row["trade_id"] == "123456001"
        assert isinstance(row["timestamp"], int)
        assert row["direction"] in ("buy", "sell")  # native side preserved
        assert row["instrument_name"] == "BTC-PERPETUAL"
        assert parsed.has_more is False

    @pytest.mark.parametrize("field", TRADE_FINGERPRINT_FIELDS)
    def test_missing_each_structural_trade_field_breaks(self, field) -> None:
        # closed THIRTEEN-field record: every fingerprint field is structurally
        # required (I07R1 doctrine applied to I08).
        parsed = parse_deribit_trades(_drop_trade_field(field))
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_empty_is_empty_valid(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()
        assert parsed.has_more is False

    def test_has_more_true_parses_but_flagged(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_HAS_MORE_TRUE)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.has_more is True

    def test_missing_has_more_breaks(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_MISSING_HAS_MORE)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_non_bool_has_more_breaks(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_BAD_HAS_MORE)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_timestamp_strict_int(self) -> None:
        for fx in (FX.TRADE_BAD_TIMESTAMP_FLOAT, FX.TRADE_BAD_TIMESTAMP_BOOL,
                   FX.TRADE_BAD_TIMESTAMP_STR, FX.TRADE_NONE_TIMESTAMP):
            parsed = parse_deribit_trades(fx)
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE, fx
            assert parsed.semantic_output_allowed is False
            assert parsed.rows == ()

    def test_additive_allowed(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_ADDITIVE)
        assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is True

    def test_row_not_dict_breaks(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_BAD_LEVEL_NESTING)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_drift_unknown(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_DRIFT)
        assert parsed.schema_state in (
            SchemaState.BREAKING_SCHEMA_CHANGE,
            SchemaState.UNKNOWN_SCHEMA,
        )

    def test_direction_never_reinterpreted(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_HAPPY)
        assert {r["direction"] for r in parsed.rows} == {"buy", "sell"}
        for r in parsed.rows:
            assert not any(k.startswith(("cvd", "flow", "buy_pressure", "sell_pressure")) for k in r)

    def test_no_canonical_field_emitted(self) -> None:
        parsed = parse_deribit_trades(FX.TRADE_HAPPY)
        for row in parsed.rows:
            assert not any(k.startswith(("canonical_", "liquidation_state")) for k in row)


class TestLiquidationParser:
    def test_projects_only_forced_liquidation_rows(self) -> None:
        # mixed page: ONLY the "liquidation"-flagged row is projected.
        parsed = parse_deribit_liquidations(FX.LIQ_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 1
        assert parsed.rows[0]["trade_id"] == "9990001"
        assert parsed.rows[0]["liquidation"] == "liquidation"
        # the same payload as TRADE projects ALL rows
        trades = parse_deribit_trades(FX.LIQ_HAPPY)
        assert len(trades.rows) == 3

    def test_no_events_yields_empty_valid(self) -> None:
        # ordinary trades only -> liquidation view row_count 0 (EMPTY_VALID at
        # the adapter layer); raw payload preserved upstream.
        parsed = parse_deribit_liquidations(FX.LIQ_NO_EVENTS)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_missing_flag_rows_are_not_liquidation_events(self) -> None:
        parsed = parse_deribit_liquidations(FX.LIQ_MISSING_FLAG)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_union_combo_row_valid_and_projected(self) -> None:
        parsed = parse_deribit_liquidations(FX.LIQ_COMBO_ROW)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 1
        assert parsed.rows[0]["combo_id"] == "cb-1"

    def test_malformed_liquidation_flag_breaks(self) -> None:
        parsed = parse_deribit_liquidations(FX.LIQ_BAD_FLAG_TYPE)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_missing_structural_field_breaks(self) -> None:
        parsed = parse_deribit_liquidations(FX.LIQ_MISSING_REQUIRED)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_no_aggregation_emitted(self) -> None:
        parsed = parse_deribit_liquidations(FX.LIQ_HAPPY)
        for row in parsed.rows:
            # never a canonical/interval-total field
            assert not any(
                k in row
                for k in ("liquidation_usd", "liquidation_volume", "long_liq",
                          "short_liq", "liq_pressure")
            )
            assert row["direction"] == "sell"  # native direction preserved

    def test_shared_payload_preserved_for_both_sensors(self) -> None:
        liq = parse_deribit_liquidations(FX.LIQ_HAPPY)
        trade = parse_deribit_trades(FX.LIQ_HAPPY)
        assert liq.rows[0]["trade_id"] == trade.rows[0]["trade_id"]
        # same physical payload != same logical observation


class TestFundingParser:
    def test_happy_preserves_native_fields(self) -> None:
        parsed = parse_deribit_funding(FX.FUNDING_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 3
        row = parsed.rows[0]
        assert isinstance(row["timestamp"], int)
        assert row["index_price"] == 29508.0
        assert "interest_1h" in row
        assert "interest_8h" in row
        assert "prev_index_price" in row
        assert "funding_rate" not in row  # probe-fixture-only, not required

    @pytest.mark.parametrize("field", FUNDING_FINGERPRINT_FIELDS)
    def test_missing_each_structural_funding_field_breaks(self, field) -> None:
        body = FX._ok_result(
            [{k: v for k, v in FX.funding_row().items() if k != field}]
        )
        parsed = parse_deribit_funding(body)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_timestamp_strict_int(self) -> None:
        for fx in (FX.FUNDING_BAD_TIMESTAMP_FLOAT, FX.FUNDING_BAD_TIMESTAMP_BOOL,
                   FX.FUNDING_BAD_TIMESTAMP_STR, FX.FUNDING_NONE_TIMESTAMP):
            parsed = parse_deribit_funding(fx)
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE, fx
            assert parsed.rows == ()

    def test_dict_result_is_breaking_never_repaired(self) -> None:
        # the old wrong {data:[...]} envelope assumption is BREAKING.
        parsed = parse_deribit_funding(FX.FUNDING_DRIFT_DICT_RESULT)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_empty_is_empty_valid(self) -> None:
        parsed = parse_deribit_funding(FX.FUNDING_EMPTY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()

    def test_fixture_only_fields_are_additive_not_required(self) -> None:
        # funding_rate/funding_1h/funding_8h are probe-fixture-only: present ->
        # ADDITIVE + preserved; absent -> KNOWN (never required).
        with_additive = parse_deribit_funding(FX.FUNDING_ADDITIVE)
        assert with_additive.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert with_additive.semantic_output_allowed is True
        assert with_additive.rows[0]["funding_rate"] == 0.000075
        assert parse_deribit_funding(FX.FUNDING_HAPPY).schema_state is SchemaState.KNOWN_SCHEMA

    def test_no_canonical_field_emitted(self) -> None:
        parsed = parse_deribit_funding(FX.FUNDING_ADDITIVE)
        for row in parsed.rows:
            assert not any(k.startswith(("canonical_", "funding_state", "carry")) for k in row)

    def test_drift_unknown(self) -> None:
        parsed = parse_deribit_funding(FX.FUNDING_DRIFT)
        assert parsed.schema_state in (
            SchemaState.BREAKING_SCHEMA_CHANGE,
            SchemaState.UNKNOWN_SCHEMA,
        )


class TestBookParser:
    def test_happy_preserves_book(self) -> None:
        parsed = parse_deribit_book(FX.BOOK_HAPPY)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 1
        book = parsed.rows[0]
        assert isinstance(book["bids"], list)
        assert book["bids"][0] == [29498.0, 1.2]  # native [price, amount]
        assert isinstance(book["timestamp"], int)

    def test_minimal_core_only_is_known(self) -> None:
        # known-optional fingerprint fields may be absent for the sensor view.
        parsed = parse_deribit_book(FX.BOOK_MINIMAL)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert len(parsed.rows) == 1

    def test_missing_bids_or_asks_breaks(self) -> None:
        assert parse_deribit_book(FX.BOOK_MISSING_BIDS).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parse_deribit_book(FX.BOOK_MISSING_ASKS).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_timestamp_strict_int(self) -> None:
        for fx in (FX.BOOK_BAD_TIMESTAMP_FLOAT, FX.BOOK_BAD_TIMESTAMP_BOOL,
                   FX.BOOK_BAD_TIMESTAMP_STR):
            parsed = parse_deribit_book(fx)
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE, fx

    def test_level_requires_price_and_amount(self) -> None:
        assert parse_deribit_book(FX.BOOK_BAD_LEVEL_ONE_ELEMENT).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parse_deribit_book(FX.BOOK_BAD_LEVEL_EMPTY).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parse_deribit_book(FX.BOOK_LEVEL_MINIMAL).schema_state is SchemaState.KNOWN_SCHEMA
        assert parse_deribit_book(FX.BOOK_HAPPY).schema_state is SchemaState.KNOWN_SCHEMA

    def test_bool_in_level_breaks(self) -> None:
        assert parse_deribit_book(FX.BOOK_BAD_LEVEL_BOOL).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_string_level_breaks(self) -> None:
        assert parse_deribit_book(FX.BOOK_BAD_LEVEL_STRING).schema_state is SchemaState.BREAKING_SCHEMA_CHANGE

    def test_empty_levels_valid(self) -> None:
        parsed = parse_deribit_book(FX.BOOK_EMPTY_LEVELS)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows[0]["bids"] == []

    def test_additive_allowed(self) -> None:
        parsed = parse_deribit_book(FX.BOOK_ADDITIVE)
        assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is True

    def test_drift_unknown(self) -> None:
        parsed = parse_deribit_book(FX.BOOK_DRIFT)
        assert parsed.schema_state in (
            SchemaState.BREAKING_SCHEMA_CHANGE,
            SchemaState.UNKNOWN_SCHEMA,
        )

    def test_no_derived_signal_emitted(self) -> None:
        parsed = parse_deribit_book(FX.BOOK_HAPPY)
        for row in parsed.rows:
            assert not any(k.startswith(("imbalance", "spread", "depth_", "slippage")) for k in row)


class TestSchemaStateTaxonomy:
    def test_known_additive_breaking_covered(self) -> None:
        states = {
            parse_deribit_trades(FX.TRADE_HAPPY).schema_state,
            parse_deribit_trades(FX.TRADE_ADDITIVE).schema_state,
            parse_deribit_trades(FX.TRADE_BAD_TIMESTAMP_FLOAT).schema_state,
        }
        assert SchemaState.KNOWN_SCHEMA in states
        assert SchemaState.ADDITIVE_SCHEMA_CHANGE in states
        assert SchemaState.BREAKING_SCHEMA_CHANGE in states

    def test_no_silent_default_to_zero(self) -> None:
        assert parse_deribit_funding(FX.FUNDING_MISSING_REQUIRED).rows == ()
        assert parse_deribit_trades(FX.TRADE_MISSING_REQUIRED).rows == ()
