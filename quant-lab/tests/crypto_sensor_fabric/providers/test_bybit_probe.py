"""Bybit Linear capability probe tests (bloc_02/02 §8, 04 §7 fixture minimums).

Offline only.  Focus: nextPageCursor pagination state, numeric-string
timestamps, OI units by contract type, retCode failure classification, direct
aggressor side on recent-trade, and the public csv.gz trade archive.
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
from crypto_sensor_fabric.providers.bybit import (
    NATIVE_INSTRUMENTS,
    BybitCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "bybit"
)

PROBE = BybitCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTCUSDT",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "BYBIT_LINEAR",
            "sensor_family": sensor,
            "venue_market": "BYBIT_LINEAR",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.CURSOR,
            "probe_run_id": "run_bybit_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# query construction
# ---------------------------------------------------------------------------


def test_native_instrument_mapping():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTCUSDT"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"]


def test_build_probe_request_oi_uses_category_window_and_interval():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_OPEN_INTEREST))
    assert query["url"].endswith("/open-interest")
    params = query["params"]
    assert params["category"] == "linear"
    assert params["symbol"] == "BTCUSDT"
    assert params["startTime"] == 1655251200000
    assert params["endTime"] == 1655337600000
    assert params["intervalTime"] == "1h"


def test_build_probe_request_recent_trade_is_latest_only():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_TRADE))
    assert query["url"].endswith("/recent-trade")
    assert "startTime" not in query["params"]


# ---------------------------------------------------------------------------
# failure classification (retCode-based)
# ---------------------------------------------------------------------------


def test_classify_unknown_symbol_retcode():
    assert (
        PROBE.classify_failure(200, _body("error_symbol_not_found.json"))
        is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    )


def test_classify_rate_limit_retcode():
    assert (
        PROBE.classify_failure(200, _body("error_rate_limit.json"))
        is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    )


def test_classify_auth_retcode():
    assert (
        PROBE.classify_failure(200, _body("error_auth.json"))
        is ProbeFailureClass.F_ACCESS_AUTH
    )


# ---------------------------------------------------------------------------
# characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_oi_history_numeric_string_timestamps():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("open_interest_hist_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    # ms-epoch strings must parse to real datetimes
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)
    assert "openInterest" in attempt.native_units_summary
    assert "contracts (linear)" in attempt.native_units_summary["openInterest"]


def test_characterize_funding_history():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "fundingRate" in attempt.native_units_summary


def test_characterize_recent_trade_aggressor_side():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("recent_trade_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert "Buy|Sell — aggressor side directly" in attempt.native_units_summary["side"]


def test_characterize_orderbook_flattens_levels():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("orderbook_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6
    # Bybit book levels are [price, size] pairs — a single snapshot-level ts,
    # no per-level timestamps
    assert attempt.last_timestamp_returned is None


def test_characterize_empty_oi_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("open_interest_empty.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID


def test_characterize_symbol_error():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("error_symbol_not_found.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert attempt.error_detail_redacted == "Unknown symbol"


# ---------------------------------------------------------------------------
# cursor pagination (T2-PAGE-01/02)
# ---------------------------------------------------------------------------


def test_cursor_pagination_more_pages_when_cursor_present():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("open_interest_hist_success.json"))
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is False  # nextPageCursor present


def test_cursor_pagination_terminal_when_cursor_absent():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_history_success.json"))
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is True


def test_recent_trade_has_no_pagination():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("recent_trade_success.json"))
    assert attempt.pagination_detected is False


# ---------------------------------------------------------------------------
# schema drift + archive
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("open_interest_hist_success.json"))
    drifted = fingerprint_payload(_body("open_interest_schema_changed.json"))
    assert success != drifted


def test_archive_file_url_is_deterministic():
    assert PROBE.archive_file_url("BTCUSDT", "2022-06-15") == (
        "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2022-06-15.csv.gz"
    )


def test_characterize_archive_file_present():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize_archive(request, date="2022-06-15", file_status=200)
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.request_fingerprint.endswith("BTCUSDT2022-06-15.csv.gz")
    assert attempt.native_units_summary["checksum"] == "not_published"


def test_characterize_archive_missing_file():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize_archive(request, date="2021-06-15", file_status=404)
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND
    assert "missing" in (attempt.error_detail_redacted or "")


def test_no_public_historical_liquidation_surface():
    # Bybit exposes no public historical liquidation API; do not infer one
    with pytest.raises(ValueError):
        PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_LIQUIDATION))
