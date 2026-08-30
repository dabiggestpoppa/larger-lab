"""Kraken capability probe tests (bloc_02/02 §5, 04 §7 fixture minimums).

All offline: fixtures only, no network.  Cover success, empty, 404, 429,
domain-error, pre-listing-style symbol error, schema change and pagination.
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
from crypto_sensor_fabric.providers.kraken import (
    NATIVE_INSTRUMENTS,
    KrakenCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "kraken"
)

PROBE = KrakenCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "PI_XBTUSD",
    asset: str = "BTC",
    start: datetime | None = None,
) -> CapabilityProbeRequest:
    start = start or datetime(2022, 6, 15, tzinfo=UTC)
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": sensor,
            "venue_market": "KRAKEN_FUTURES",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": start,
            "requested_end": start,
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "probe_run_id": "run_kraken_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# instrument mapping (02 §4)
# ---------------------------------------------------------------------------


def test_native_instrument_mapping_covers_playbook_basket():
    assert NATIVE_INSTRUMENTS["BTC"] == "PI_XBTUSD"
    assert NATIVE_INSTRUMENTS["ETH"] == "PI_ETHUSD"
    assert NATIVE_INSTRUMENTS["SOL"] == "PI_SOLUSD"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"]


def test_native_instrument_unknown_asset_raises():
    with pytest.raises(ValueError):
        PROBE.native_instrument("NOPE")


# ---------------------------------------------------------------------------
# query construction
# ---------------------------------------------------------------------------


def test_build_probe_request_funding_analytics_seconds_units():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    query = PROBE.build_probe_request(request)
    assert query["url"].endswith("/api/charts/v1/analytics/PI_XBTUSD/funding")
    assert query["params"]["since"] == 1655251200  # epoch seconds, NOT ms
    assert query["params"]["to"] == 1655251200
    assert query["params"]["interval"] == 3600


def test_build_probe_request_trades_uses_since_cursor():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    query = PROBE.build_probe_request(request)
    assert query["url"].endswith("/history")
    assert query["params"]["type"] == "all"
    assert query["params"]["since"] == 1655251200000


def test_build_probe_request_oi_analytics_open_interest():
    # Historical OI MUST target Market Analytics open-interest, not /tickers.
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST, era="2022")
    query = PROBE.build_probe_request(request)
    assert (
        "https://futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/open-interest"
        == query["url"]
    )
    assert "open-interest" in query["url"]
    assert "/tickers" not in query["url"]
    assert query["params"]["since"] == 1655251200  # seconds
    assert query["params"]["to"] == 1655251200
    assert query["params"]["interval"] == 3600


def test_build_probe_request_oi_analytics_since_to_in_seconds():
    start = datetime(2022, 6, 15, tzinfo=UTC)
    end = datetime(2022, 6, 16, tzinfo=UTC)
    request = _request(
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        era="2022",
        start=start,
    )
    request = CapabilityProbeRequest.model_validate(
        {
            **request.model_dump(),
            "requested_end": end,
            "probe_run_id": "run_kraken_001",
        }
    )
    query = PROBE.build_probe_request(request)
    assert query["params"]["since"] == 1655251200
    assert query["params"]["to"] == 1655337600
    # 13-digit ms must never appear
    assert query["params"]["since"] < 10_000_000_000
    assert query["params"]["to"] < 10_000_000_000


def test_historical_oi_not_via_current_tickers_only():
    # Negative: historical OI must not be characterized through current /tickers.
    query = PROBE.build_probe_request(
        _request(SensorFamily.MECHANICAL_OPEN_INTEREST, era="2021")
    )
    assert "open-interest" in query["url"]
    assert "/tickers" not in query["url"]


def test_build_probe_request_positioning_analytics_long_short_ratio():
    query = PROBE.build_probe_request(
        _request(SensorFamily.MECHANICAL_POSITIONING, era="2024")
    )
    assert (
        "https://futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/long-short-ratio"
        == query["url"]
    )
    assert query["params"]["since"] == 1655251200


def test_build_probe_request_book_metric_analytics_orderbook():
    query = PROBE.build_probe_request(
        _request(SensorFamily.MECHANICAL_BOOK_METRIC, era="2024")
    )
    assert query["url"].endswith("/analytics/PI_XBTUSD/orderbook")
    assert query["params"]["interval"] == 3600


def test_build_probe_request_is_deterministic():
    a = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    b = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    assert a == b


# ---------------------------------------------------------------------------
# failure classification
# ---------------------------------------------------------------------------


def test_classify_http_404_is_endpoint_removed():
    assert (
        PROBE.classify_failure(404, _body("error_404.json"))
        is ProbeFailureClass.F_ENDPOINT_REMOVED
    )


def test_classify_http_429_is_rate_limit():
    assert (
        PROBE.classify_failure(429, _body("error_429.json"))
        is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    )


def test_classify_domain_error_invalid_symbol():
    # HTTP 200 + {"error": "invalidSymbol"} -> symbol-level, never a provider
    # verdict.  Historical PRE_LISTING is decided at the era layer, not here.
    assert (
        PROBE.classify_failure(200, _body("error_invalid_symbol.json"))
        is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    )


def test_classify_5xx_and_auth():
    assert PROBE.classify_failure(500, {}) is ProbeFailureClass.F_SERVER_5XX
    assert PROBE.classify_failure(403, {}) is ProbeFailureClass.F_ACCESS_AUTH


# ---------------------------------------------------------------------------
# payload characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_trades_success():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert attempt.era_hint == "2022"
    assert "time" in attempt.native_timestamp_fields
    assert attempt.native_units_summary["price"] == "USD"
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)
    assert attempt.payload_schema_fingerprint


def test_characterize_liquidation_uses_trade_history_with_type_flag():
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION)
    attempt = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    # liquidation semantics live in the `type` field of trade rows
    assert "type" in attempt.native_units_summary
    assert "liquidation" in attempt.native_units_summary["type"]


def test_characterize_liquidation_via_analytics_hint():
    # I13R1: the live runner can stamp an analytics_type hint so liquidation
    # probes the bucketed `liquidation-volume` Market Analytics surface while
    # the offline default stays trade-level /history anatomy (both preserved).
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION, era="2022")
    request = request.model_copy(update={"provider_hints": {"analytics_type": "liquidation-volume"}})
    query = PROBE.build_probe_request(request)
    assert query["url"].endswith("/liquidation-volume")
    assert query["params"]["since"] < 10_000_000_000  # epoch seconds
    attempt = PROBE.characterize(request, 200, _body("liquidation_volume_analytics_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert "liquidation-volume" in attempt.native_units_summary["source"]
    assert attempt.pagination_detected is True


def test_characterize_funding_analytics_success():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_analytics_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "fundingRate" in attempt.native_units_summary
    assert attempt.last_timestamp_returned == datetime(2022, 6, 15, 2, 0, tzinfo=UTC)
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is True  # more=false -> terminal page


def test_characterize_oi_analytics_success():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST, era="2022")
    attempt = PROBE.characterize(request, 200, _body("open_interest_analytics_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "openInterest" in attempt.native_units_summary
    assert "not assumed" in attempt.native_units_summary["exact_equivalent"]
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)
    # analytics envelope carries a `more` flag -> pagination detected, not complete
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is False


def test_characterize_positioning_analytics_long_short_ratio():
    request = _request(SensorFamily.MECHANICAL_POSITIONING, era="2024")
    attempt = PROBE.characterize(
        request, 200, _body("long_short_ratio_analytics_success.json")
    )
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "long-short-ratio" in attempt.native_units_summary["source"]


def test_characterize_orderbook_flattens_levels():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("orderbook_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6  # 3 bids + 3 asks
    assert attempt.first_timestamp_returned is not None
    assert attempt.last_timestamp_returned is not None


def test_characterize_valid_empty_is_not_failure():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_empty_valid.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID
    assert attempt.error_class is None


# ---------------------------------------------------------------------------
# failure paths
# ---------------------------------------------------------------------------


def test_characterize_404_fails_endpoint_removed():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 404, _body("error_404.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ENDPOINT_REMOVED


def test_characterize_429_fails_rate_limit():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 429, _body("error_429.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_RATE_LIMIT


def test_characterize_domain_error_symbol_not_found():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("error_invalid_symbol.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert attempt.error_detail_redacted == "invalidSymbol"


def test_characterize_missing_result_key_is_schema_changed():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, {"result": {}})
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_SCHEMA_CHANGED


# ---------------------------------------------------------------------------
# schema drift + pagination
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("history_trades_success.json"))
    drifted = fingerprint_payload(_body("history_schema_changed.json"))
    assert success != drifted


def test_pagination_detected_with_more_pages():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("history_pagination.json"))
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is False  # oldest row still newer than window start


def test_characterize_is_offline_and_deterministic():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    a = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    b = PROBE.characterize(request, 200, _body("history_trades_success.json"))
    assert a.model_dump() == b.model_dump()
