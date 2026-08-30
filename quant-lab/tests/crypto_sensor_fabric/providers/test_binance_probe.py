"""Binance USD-M capability probe tests (bloc_02/02 §7, 04 §7 fixture minimums).

Offline only.  Covers the ratified isBuyerMaker aggressor contract, REST
characterization (aggTrades / fundingRate / openInterestHist / depth),
code-based failure classification (-1121 / -1003 / 451), valid-empty, schema
drift, and deterministic archive file naming + checksums.  Historical
liquidation stays UNVERIFIED_OR_UNAVAILABLE by design.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.contracts.enums import AggressorSide, SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    Granularity,
    ProbeFailureClass,
    QueryMode,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import CapabilityProbeRequest
from crypto_sensor_fabric.probes.payload import fingerprint_payload
from crypto_sensor_fabric.providers.binance import (
    NATIVE_INSTRUMENTS,
    BinanceCapabilityProbe,
    aggressor_side_from_is_buyer_maker,
)
from crypto_sensor_fabric.testing import load_fixture_json

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "binance"
)

PROBE = BinanceCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTCUSDT",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "BINANCE_USDM",
            "sensor_family": sensor,
            "venue_market": "BINANCE_USDM",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "probe_run_id": "run_binance_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# R01 aggressor contract — direction must never invert
# ---------------------------------------------------------------------------


def test_aggressor_contract_true_maps_to_sell():
    assert aggressor_side_from_is_buyer_maker(True) is AggressorSide.SELL


def test_aggressor_contract_false_maps_to_buy():
    assert aggressor_side_from_is_buyer_maker(False) is AggressorSide.BUY


def test_aggressor_contract_matches_frozen_fixture():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    for case in contract["cases"]:
        expected = AggressorSide(case["expected_aggressor_side"])
        assert aggressor_side_from_is_buyer_maker(case["isBuyerMaker"]) is expected


def test_probe_documents_aggressor_contract_in_units():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("aggtrades_success.json"))
    assert "SELL aggressor" in attempt.native_units_summary["isBuyerMaker"]
    assert "BUY aggressor" in attempt.native_units_summary["isBuyerMaker"]


# ---------------------------------------------------------------------------
# instrument mapping + query construction
# ---------------------------------------------------------------------------


def test_native_instrument_mapping_uppercase_symbols():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTCUSDT"
    assert NATIVE_INSTRUMENTS["ETH"] == "ETHUSDT"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"]


def test_build_probe_request_aggtrades_uses_start_end_time():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_TRADE))
    assert query["url"].endswith("/aggTrades")
    assert query["params"]["symbol"] == "BTCUSDT"
    assert query["params"]["startTime"] == 1655251200000
    assert query["params"]["endTime"] == 1655337600000
    assert query["params"]["limit"] == 1000


def test_build_probe_request_depth_is_current_snapshot():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))
    assert query["url"].endswith("/depth")
    assert query["params"] == {"symbol": "BTCUSDT", "limit": 100}


# ---------------------------------------------------------------------------
# failure classification (code-based)
# ---------------------------------------------------------------------------


def test_classify_invalid_symbol_code():
    assert (
        PROBE.classify_failure(400, _body("error_invalid_symbol.json"))
        is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    )


def test_classify_rate_limit_code():
    assert (
        PROBE.classify_failure(400, _body("error_rate_limit.json"))
        is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    )


def test_classify_geo_451():
    assert (
        PROBE.classify_failure(451, _body("error_geo_451.json"))
        is ProbeFailureClass.F_ACCESS_GEO
    )


def test_characterize_geo_451_marks_geo_block():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 451, _body("error_geo_451.json"))
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_GEO
    assert attempt.geo_block_detected is True


# ---------------------------------------------------------------------------
# REST characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_aggtrades_success():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("aggtrades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "time" in attempt.native_timestamp_fields
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)


def test_characterize_funding_success():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_rate_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "fundingRate" in attempt.native_units_summary
    assert "fundingTime" in attempt.native_timestamp_fields


def test_characterize_oi_history_success():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("open_interest_hist_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    units = attempt.native_units_summary
    assert units["sumOpenInterest"] == "contracts"
    assert units["sumOpenInterestValue"] == "USD notional"


def test_characterize_depth_flattens_levels():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("depth_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6


def test_characterize_empty_aggtrades_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("aggtrades_empty.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID
    assert attempt.error_class is None


def test_liquidation_not_assumed_for_binance():
    # Binance has no public historical liquidation surface (02 §7 §8);
    # the probe exposes no liquidation endpoint and the registry keeps
    # liquidations claimed=false.  This test pins the absence.
    with pytest.raises(ValueError):
        PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_LIQUIDATION))


# ---------------------------------------------------------------------------
# schema drift + pagination
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("aggtrades_success.json"))
    drifted = fingerprint_payload(_body("aggtrades_schema_changed.json"))
    assert success != drifted


def test_window_pagination_characterized():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("aggtrades_success.json"))
    assert attempt.pagination_detected is True
    assert attempt.pagination_complete is False  # rows do not reach window end


# ---------------------------------------------------------------------------
# archive characterization (deterministic naming + checksums)
# ---------------------------------------------------------------------------


def test_archive_file_url_is_deterministic():
    url = PROBE.archive_file_url("BTCUSDT", "2022-06-15", "trades")
    assert url == (
        "https://data.binance.vision/data/futures/um/daily/trades/"
        "BTCUSDT/BTCUSDT-trades-2022-06-15.zip"
    )


def test_archive_checksum_url_sibling():
    checksum = PROBE.archive_checksum_url("BTCUSDT", "2022-06-15", "aggTrades")
    assert checksum.endswith("BTCUSDT-aggTrades-2022-06-15.zip.CHECKSUM")


def test_characterize_archive_file_present_with_checksum():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    checksum_line = (FIXTURES / "archive_checksum.txt").read_text(encoding="utf-8")
    attempt = PROBE.characterize_archive(
        request,
        kind="trades",
        date="2022-06-15",
        file_status=200,
        checksum_status="present",
        checksum_line=checksum_line,
    )
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.request_fingerprint.endswith("BTCUSDT-trades-2022-06-15.zip")
    assert attempt.payload_hash_sample == checksum_line[:100]
    assert attempt.native_units_summary["checksum"] == "present"


def test_characterize_archive_missing_file_is_hole_not_zero():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize_archive(
        request,
        kind="bookDepth",
        date="2022-06-15",
        file_status=404,
        checksum_status="missing",
    )
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND
    assert attempt.error_detail_redacted == (
        "archive file missing: BTCUSDT-bookDepth-2022-06-15.zip"
    )


def test_archive_kinds_cover_research_surfaces():
    from crypto_sensor_fabric.providers.binance import ARCHIVE_KINDS

    assert "trades" in ARCHIVE_KINDS
    assert "aggTrades" in ARCHIVE_KINDS
    assert "bookDepth" in ARCHIVE_KINDS
    assert "metrics" in ARCHIVE_KINDS
    assert "fundingRate" in ARCHIVE_KINDS
