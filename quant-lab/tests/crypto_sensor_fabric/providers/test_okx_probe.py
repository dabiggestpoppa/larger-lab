"""OKX Swap capability probe tests (bloc_02/02 §9, 04 §7 fixture minimums).

Offline only.  Focus: data envelope handling, after/before cursor pagination,
string error codes, /books current-snapshot semantics with deep history
UNVERIFIED, and the traderecords daily zip archive.
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
from crypto_sensor_fabric.providers.okx import (
    NATIVE_INSTRUMENTS,
    OkxCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "okx"
)

PROBE = OkxCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTC-USDT-SWAP",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "OKX_SWAP",
            "sensor_family": sensor,
            "venue_market": "OKX_SWAP",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.CURSOR,
            "probe_run_id": "run_okx_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# instrument mapping + query construction
# ---------------------------------------------------------------------------


def test_native_instrument_mapping_swap_ids():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTC-USDT-SWAP"
    assert NATIVE_INSTRUMENTS["ETH"] == "ETH-USDT-SWAP"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"]


def test_build_probe_request_history_trades():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_TRADE))
    assert query["url"].endswith("/history-trades")
    assert query["params"] == {"instId": "BTC-USDT-SWAP", "limit": 100}


def test_build_probe_request_funding_public_route():
    # Funding-rate history is in the /public namespace, NOT under /api/v5/market.
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    assert (
        query["url"] == "https://www.okx.com/api/v5/public/funding-rate-history"
    )
    assert "public/funding-rate-history" in query["url"]
    assert query["params"] == {"instId": "BTC-USDT-SWAP", "limit": 100}


def test_no_funding_via_market_route():
    # Negative: funding must never be composed as /api/v5/market/funding-rate-history.
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    assert "/api/v5/market/funding-rate-history" not in query["url"]


def test_build_probe_request_books_is_current_snapshot():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))
    assert query["url"].endswith("/books")
    assert query["params"] == {"instId": "BTC-USDT-SWAP", "sz": 400}


# ---------------------------------------------------------------------------
# failure classification (string error codes)
# ---------------------------------------------------------------------------


def test_classify_symbol_error_code():
    assert (
        PROBE.classify_failure(400, _body("error_symbol.json"))
        is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    )


def test_classify_rate_limit_code():
    assert (
        PROBE.classify_failure(200, _body("error_rate_limit.json"))
        is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    )


def test_classify_auth_code():
    assert (
        PROBE.classify_failure(200, _body("error_auth.json"))
        is ProbeFailureClass.F_ACCESS_AUTH
    )


# ---------------------------------------------------------------------------
# characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_history_trades_success():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)
    assert "buy|sell — aggressor side directly" in attempt.native_units_summary["side"]


def test_characterize_funding_history():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_rate_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "fundingRate" in attempt.native_units_summary
    assert "realizedRate" in attempt.native_units_summary
    # funding fields preserved (PIT/revision semantics), interval not frozen to 8h
    assert "fundingTime" in attempt.native_units_summary
    assert "formulaType" in attempt.native_units_summary
    assert "method" in attempt.native_units_summary
    assert "NOT frozen to 8h" in attempt.native_units_summary["fundingRate"]
    assert "fundingTime timestamps (NOT trade ids)" in attempt.native_units_summary["pagination"]


def test_characterize_books_snapshot_current_only():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("books_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6  # 3 bids + 3 asks
    # deep book history is explicitly UNVERIFIED, never claimed
    assert "UNVERIFIED" in attempt.native_units_summary["deep_history"]


def test_characterize_empty_history_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_trades_empty.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID


def test_characterize_symbol_error():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 400, _body("error_symbol.json"))
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert attempt.error_detail_redacted == "Instrument ID does not exist"


# ---------------------------------------------------------------------------
# cursor pagination
# ---------------------------------------------------------------------------


def test_cursor_pagination_partial_page_reaches_history_start():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    assert attempt.pagination_detected is True
    # 3 rows < 100 limit -> terminal page (history start reached)
    assert attempt.pagination_complete is True


def test_book_has_no_pagination():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("books_success.json"))
    assert attempt.pagination_detected is False


# ---------------------------------------------------------------------------
# schema drift + archive
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("history_trades_success.json"))
    drifted = fingerprint_payload(_body("history_trades_schema_changed.json"))
    assert success != drifted


def test_archive_file_url_is_deterministic():
    assert PROBE.archive_file_url("BTC-USDT-SWAP", "2022-06-15") == (
        "https://www.okx.com/cdn/okex/traderecords/BTC-USDT-SWAP/20220615.zip"
    )


def test_characterize_archive_file_present():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize_archive(request, date="2022-06-15", file_status=200)
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.request_fingerprint.endswith("20220615.zip")


def test_characterize_archive_missing_file():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize_archive(request, date="2021-06-15", file_status=404)
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND
    assert "missing" in (attempt.error_detail_redacted or "")


def test_oi_not_substituted_from_current_surface():
    # OKX has no assumed official free historical OI route; the probe exposes
    # no OI endpoint so current OI can never masquerade as history
    with pytest.raises(ValueError):
        PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_OPEN_INTEREST))
