"""Coinalyze capability probe tests (bloc_02/02 §11, 04 §7 fixture minimums).

Offline only.  Focus: THIRD_PARTY_AGGREGATOR semantics (never independent
venue truth), venue-attributed symbols, free-key requirement, rate-limit and
auth classification, aggregated-history characterization.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

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
from crypto_sensor_fabric.providers.coinalyze import (
    NATIVE_INSTRUMENTS,
    CoinalyzeCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "coinalyze"
)

PROBE = CoinalyzeCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTCUSDT_PERP.BINANCE",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "COINALYZE",
            "sensor_family": sensor,
            "venue_market": "COINALYZE",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.FREE_API_KEY,
            "query_mode": QueryMode.TIME_RANGE,
            "probe_run_id": "run_coinalyze_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# venue-attributed symbols + free-key access
# ---------------------------------------------------------------------------


def test_native_instruments_are_venue_attributed():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTCUSDT_PERP.BINANCE"
    assert NATIVE_INSTRUMENTS["ETH"] == "ETHUSDT_PERP.BINANCE"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"].endswith(".BINANCE")


def test_probe_is_free_api_key_mode():
    assert PROBE.access_mode is AccessMode.FREE_API_KEY


def test_build_probe_request_never_embeds_apikey():
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_OPEN_INTEREST))
    assert "apikey" not in query["params"]
    assert query["params"]["symbols"] == "BTCUSDT_PERP.BINANCE"
    assert query["params"]["interval"] == "1h"
    # from/to are UNIX seconds (coinalyze convention)
    assert query["params"]["from"] == 1655251200
    assert query["params"]["to"] == 1655337600


# ---------------------------------------------------------------------------
# aggregation semantics — never independent venue truth
# ---------------------------------------------------------------------------


def test_characterize_oi_history_documents_aggregation():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("oi_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    units = attempt.native_units_summary
    assert "vendor-aggregated, opaque" in units["methodology"]
    assert "venue-attributed" in units["symbols"]
    assert "corroboration" in units["methodology"]
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)


def test_characterize_liquidations_history():
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION)
    attempt = PROBE.characterize(request, 200, _body("liquidations_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "aggregated USD liquidations" in attempt.native_units_summary["value"]


def test_characterize_funding_and_ratio_history():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_rate_history_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert "funding rate" in attempt.native_units_summary["value"]

    ratio = PROBE.characterize(
        _request(SensorFamily.MECHANICAL_POSITIONING),
        200,
        _body("long_short_ratio_history_success.json"),
    )
    assert ratio.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert "long/short ratio" in ratio.native_units_summary["value"]


def test_characterize_empty_history_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("empty_history.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID


# ---------------------------------------------------------------------------
# auth / rate-limit / symbol errors
# ---------------------------------------------------------------------------


def test_characterize_invalid_key():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 401, _body("error_401.json"))
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_AUTH
    assert attempt.requires_auth is True


def test_characterize_rate_limit():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 429, _body("error_429.json"))
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_RATE_LIMIT


def test_characterize_symbol_error():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 404, _body("error_symbol.json"))
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert "not found" in (attempt.error_detail_redacted or "")


# ---------------------------------------------------------------------------
# schema drift + determinism
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("oi_history_success.json"))
    drifted = fingerprint_payload(_body("schema_changed.json"))
    assert success != drifted


def test_characterize_is_offline_and_deterministic():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    a = PROBE.characterize(request, 200, _body("oi_history_success.json"))
    b = PROBE.characterize(request, 200, _body("oi_history_success.json"))
    assert a.model_dump() == b.model_dump()
