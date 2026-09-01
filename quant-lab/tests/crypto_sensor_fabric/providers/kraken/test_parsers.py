"""SENSOR-B3-I05 — Kraken Market Analytics parser tests.

Parser doctrine: providers emit native fields/units only; never canonical OI USD,
cross-venue CVD, LiquidationState/FundingState/PositioningState or research
features.  KNOWN/ADDITIVE produce rows; BREAKING/UNKNOWN block (no zero
coercion).  Empty-valid stays a first-class state.
"""

from __future__ import annotations

from typing import Any

import pytest

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
        # funding bucket timestamps are RAW native INTs on the current live
        # Market Analytics funding surface (I13R1 fingerprint pins int only);
        # adapter-side convenience conversion treats funding as epoch ms
        # (I10R1 adjudication) — the parser preserves the raw int verbatim.
        assert parsed.rows[0]["timestamp"] == 1755000000000

    def test_funding_known_schema_with_known_metrics(self) -> None:
        # {rate, relativeRate} is the full evidence-backed funding set (I10R1:
        # both keys pinned in the 09 fingerprint, live reproduction exact) —
        # its presence is KNOWN, never ADDITIVE.
        parsed = parse_kraken_analytics(FX.HAPPY["funding"][1], SensorFamily.MECHANICAL_FUNDING)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA

    def test_funding_genuinely_new_key_stays_additive(self) -> None:
        # A NEW unknown metric key beyond {rate, relativeRate} stays
        # ADDITIVE (preserved raw + flagged) and is NOT silently promoted
        # into a KNOWN semantic projection (I10R1 §14 firewall).
        body = {
            "errors": [],
            "result": {
                "timestamp": [1755000000000],
                "data": {
                    "rate": [["0.0001"]],
                    "relativeRate": [["0.0001"]],
                    "brandNewMetric": [["x"]],
                },
                "more": False,
            },
        }
        parsed = parse_kraken_analytics(body, SensorFamily.MECHANICAL_FUNDING)
        assert parsed.schema_state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert parsed.semantic_output_allowed is True
        # native field preserved in the native row view (raw payload also
        # preserved upstream); semantic promotion is gated by schema state.
        assert parsed.rows[0]["brandNewMetric"] == ["x"]

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
        # rate + relativeRate are both evidence-backed known metrics (I10R1) so
        # the observed set == required set -> KNOWN; still parses, zero rows
        assert parsed.schema_state in (SchemaState.KNOWN_SCHEMA, SchemaState.ADDITIVE_SCHEMA_CHANGE)
        assert parsed.semantic_output_allowed is True
        assert parsed.rows == ()

    def test_basis_empty(self) -> None:
        parsed = parse_kraken_analytics(FX.EMPTY["basis"][1], SensorFamily.MECHANICAL_BASIS)
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows == ()


class TestCardinalityFailClosed:
    """SENSOR-B3-I05R1 — structural list/dict cardinality mismatch is BREAKING."""

    LIST_SENSORS = {
        "open_interest": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "positioning": SensorFamily.MECHANICAL_POSITIONING,
        "liquidation": SensorFamily.MECHANICAL_LIQUIDATION,
    }

    def _list_body(self, timestamps: list, data: list) -> dict:
        return {"errors": [], "result": {"timestamp": timestamps, "data": data, "more": False}}

    def test_list_data_shorter_than_timestamps_breaking(self) -> None:
        for sensor in self.LIST_SENSORS.values():
            parsed = parse_kraken_analytics(
                self._list_body([1755000000, 1755003600], [["1"]]), sensor
            )
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
            assert parsed.rows == ()
            assert parsed.semantic_output_allowed is False

    def test_list_data_longer_than_timestamps_breaking(self) -> None:
        for sensor in self.LIST_SENSORS.values():
            parsed = parse_kraken_analytics(
                self._list_body([1755000000], [["1"], ["2"]]), sensor
            )
            assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
            assert parsed.rows == ()

    def test_list_equal_length_still_known(self) -> None:
        parsed = parse_kraken_analytics(
            self._list_body([1755000000], [["725.3"]]),
            SensorFamily.MECHANICAL_OPEN_INTEREST,
        )
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows[0]["value"] == ["725.3"]

    def test_dict_metric_column_longer_than_timestamps_breaking(self) -> None:
        body = {
            "errors": [],
            "result": {"timestamp": [1755000000], "data": {"basis": ["0.001", "0.002"]}, "more": False},
        }
        parsed = parse_kraken_analytics(body, SensorFamily.MECHANICAL_BASIS)
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert parsed.rows == ()

    def test_provider_declared_null_not_a_mismatch(self) -> None:
        # a correctly-sized column with a legitimate provider null value stays
        # native data (book_metric slippage1m: [None]) — structural absence
        # != provider-declared null
        parsed = parse_kraken_analytics(
            FX.HAPPY["book_metric"][1], SensorFamily.MECHANICAL_BOOK_METRIC
        )
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        # row cells are per-bucket values; the provider-declared null survives
        assert parsed.rows[0]["ask"]["slippage1m"] is None


class TestTimestampSchema:
    """SENSOR-B3-I05R2 Repair 3 — bucket timestamps fail closed to int epoch secs.

    The committed Market Analytics fingerprint pins `timestamp` as `list[int]` in
    epoch seconds.  Every non-empty member must be exactly an int (`type(ts) is
    int` — bool excluded).  String/float/bool/None/mixed elements are BREAKING
    (parsed output blocked, raw preserved upstream); an empty list stays a valid
    EMPTY_VALID observation.  No silent coercion.
    """

    def _list_body(self, timestamps: list[Any]) -> dict[str, Any]:
        # open-interest list shape with an equal-length data column
        n = len(timestamps)
        return {
            "errors": [],
            "result": {
                "timestamp": timestamps,
                "data": [["725.3"]] * n,
                "more": False,
            },
        }

    def _dict_body(self, timestamps: list[Any]) -> dict[str, Any]:
        # basis dict shape with an equal-length basis column
        n = len(timestamps)
        return {
            "errors": [],
            "result": {
                "timestamp": timestamps,
                "data": {"basis": ["0.001"] * n},
                "more": False,
            },
        }

    INVALID: list[tuple[list[Any], str]] = [
        (["1755000000"], "string"),
        ([1755000000.0], "float"),
        ([True], "bool"),
        ([None], "null"),
        ([1755000000, "1755003600"], "mixed"),
    ]

    def test_empty_list_stays_valid_empty_valid(self) -> None:
        for body, sensor in (
            (self._list_body([]), SensorFamily.MECHANICAL_OPEN_INTEREST),
            (self._dict_body([]), SensorFamily.MECHANICAL_BASIS),
        ):
            parsed = parse_kraken_analytics(body, sensor)
            assert parsed.schema_state in (
                SchemaState.KNOWN_SCHEMA,
                SchemaState.ADDITIVE_SCHEMA_CHANGE,
            )
            assert parsed.semantic_output_allowed is True
            assert parsed.rows == ()

    def test_valid_int_timestamp_parses(self) -> None:
        parsed = parse_kraken_analytics(
            self._dict_body([1755000000]), SensorFamily.MECHANICAL_BASIS
        )
        assert parsed.schema_state is SchemaState.KNOWN_SCHEMA
        assert parsed.rows[0]["timestamp"] == 1755000000

    @pytest.mark.parametrize("bad,label", INVALID)
    def test_invalid_timestamp_breaks_list_shape(self, bad: list[Any], label: str) -> None:
        parsed = parse_kraken_analytics(
            self._list_body(bad), SensorFamily.MECHANICAL_OPEN_INTEREST
        )
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE, label
        assert parsed.semantic_output_allowed is False, label
        assert parsed.rows == (), label

    @pytest.mark.parametrize("bad,label", INVALID)
    def test_invalid_timestamp_breaks_dict_shape(self, bad: list[Any], label: str) -> None:
        parsed = parse_kraken_analytics(
            self._dict_body(bad), SensorFamily.MECHANICAL_BASIS
        )
        assert parsed.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE, label
        assert parsed.semantic_output_allowed is False, label
        assert parsed.rows == (), label

    def test_no_silent_coercion(self) -> None:
        # a string timestamp is never rescued to int; a bool never becomes 1
        assert parse_kraken_analytics(
            self._list_body(["1755000000"]), SensorFamily.MECHANICAL_OPEN_INTEREST
        ).rows == ()
        assert parse_kraken_analytics(
            self._list_body([True]), SensorFamily.MECHANICAL_OPEN_INTEREST
        ).rows == ()


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