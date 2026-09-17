"""Deribit capability probe tests (bloc_02/02 §10, 04 §7 fixture minimums).

Offline only.  Focus: trade-level liquidation anatomy (T2-SEM-06), has_more
sequence pagination, include_old historical traversal, the deliberately
narrower asset universe, JSON-RPC error envelopes, funding and book
characterization.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    Granularity,
    ProbeFailureClass,
    QueryMode,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import CapabilityProbeRequest
from crypto_sensor_fabric.probes.payload import fingerprint_payload
from crypto_sensor_fabric.providers.deribit import (
    NATIVE_INSTRUMENTS,
    DeribitCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "deribit"
)

PROBE = DeribitCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTC-PERPETUAL",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "DERIBIT",
            "sensor_family": sensor,
            "venue_market": "DERIBIT",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.SEQUENCE,
            "probe_run_id": "run_deribit_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# narrow universe (02 §10.7)
# ---------------------------------------------------------------------------


def test_universe_is_btc_eth_heavy():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTC-PERPETUAL"
    assert NATIVE_INSTRUMENTS["ETH"] == "ETH-PERPETUAL"
    assert NATIVE_INSTRUMENTS["SOL"] == "SOL-PERPETUAL"


def test_mid_tail_control_not_mapped_narrower_universe():
    # Deribit's universe is deliberately narrower; MID_TAIL_CONTROL is not
    # silently mapped — the limitation is explicit.
    with pytest.raises(ValueError):
        PROBE.native_instrument("MID_TAIL_CONTROL")


# ---------------------------------------------------------------------------
# query construction — include_old is required for history
# ---------------------------------------------------------------------------


def test_build_probe_request_trades_uses_timestamp_window_and_include_old():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_TRADE))
    assert query["url"].endswith("/get_last_trades_by_instrument")
    params = query["params"]
    assert params["instrument_name"] == "BTC-PERPETUAL"
    assert params["start_timestamp"] == 1655251200000
    assert params["end_timestamp"] == 1655337600000
    assert params["include_old"] is True
    assert params["count"] == 1000


# ---------------------------------------------------------------------------
# liquidation semantics — TRADE_LEVEL anatomy (T2-SEM-06)
# ---------------------------------------------------------------------------


def test_liquidation_is_trade_level_flag_semantics():
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION)
    attempt = PROBE.characterize(request, 200, _body("trades_liquidation_semantics.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    units = attempt.native_units_summary
    # the flag marks forced-liquidation trades; never merged with interval totals
    assert "TRADE_LEVEL anatomy" in units["shape"]
    assert "never numerically merged with interval totals" in units["shape"]
    assert "liquidation" in units["liquidation"]


def test_liquidation_rows_have_aggressor_direction():
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION)
    attempt = PROBE.characterize(request, 200, _body("trades_liquidation_semantics.json"))
    assert attempt.rows_returned == 3
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)
    assert "direction" in attempt.native_units_summary


# ---------------------------------------------------------------------------
# characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_trades_success():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "direction" in attempt.native_units_summary
    assert "timestamp" in attempt.native_timestamp_fields


def test_characterize_funding_history():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    units = attempt.native_units_summary
    assert "funding_8h" in units
    assert "funding_1h" in units
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)


def test_characterize_orderbook_snapshot():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("orderbook_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6
    # Deribit book levels are [price, amount] pairs — snapshot ts at result level
    assert attempt.last_timestamp_returned is None


def test_characterize_empty_trades_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_empty.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID
    assert attempt.pagination_complete is True


# ---------------------------------------------------------------------------
# JSON-RPC error envelopes
# ---------------------------------------------------------------------------


def test_characterize_invalid_instrument_error():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("error_invalid_instrument.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert attempt.error_detail_redacted == "invalid instrument name"


def test_characterize_rate_limit_error():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("error_rate_limit.json"))
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_RATE_LIMIT


# ---------------------------------------------------------------------------
# sequence pagination (has_more) + schema drift
# ---------------------------------------------------------------------------


def test_sequence_pagination_more_pages_when_has_more():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_success.json"))
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is False  # has_more=true


def test_sequence_pagination_terminal_when_has_more_absent():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_liquidation_semantics.json"))
    assert attempt.pagination_complete is True


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("trades_success.json"))
    drifted = fingerprint_payload(_body("trades_schema_changed.json"))
    assert success != drifted


def test_characterize_is_offline_and_deterministic():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    a = PROBE.characterize(request, 200, _body("funding_history_success.json"))
    b = PROBE.characterize(request, 200, _body("funding_history_success.json"))
    assert a.model_dump() == b.model_dump()
