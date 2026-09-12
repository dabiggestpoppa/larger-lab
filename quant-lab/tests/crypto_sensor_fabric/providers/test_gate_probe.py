"""Gate Futures capability probe tests (bloc_02/02 §6, 04 §7 fixture minimums).

All offline: fixtures only.  Focus: contract_stats long/short liquidation and
OI fields, taker_side aggressor semantics, from/to window pagination,
label-based failure classification (UNAUTHORIZED / FORBIDDEN / RATE_LIMIT /
NOT_FOUND / INVALID_PARAM_VALUE).
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
from crypto_sensor_fabric.providers.gate import (
    NATIVE_INSTRUMENTS,
    GateCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "gate"
)

PROBE = GateCapabilityProbe()


def _request(
    sensor: SensorFamily,
    *,
    era: str = "2022",
    instrument: str = "BTC_USDT",
    asset: str = "BTC",
) -> CapabilityProbeRequest:
    start = datetime(2022, 6, 15, tzinfo=UTC)
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": "GATE_FUTURES",
            "sensor_family": sensor,
            "venue_market": "GATE_FUTURES",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": start,
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "probe_run_id": "run_gate_001",
            "provider_hints": {"era": era},
        }
    )


def _body(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# instrument mapping + query construction
# ---------------------------------------------------------------------------


def test_native_instrument_mapping_covers_playbook_basket():
    assert NATIVE_INSTRUMENTS["BTC"] == "BTC_USDT"
    assert NATIVE_INSTRUMENTS["ETH"] == "ETH_USDT"
    assert NATIVE_INSTRUMENTS["SOL"] == "SOL_USDT"
    assert NATIVE_INSTRUMENTS["MID_TAIL_CONTROL"]


def test_native_instrument_unknown_asset_raises():
    with pytest.raises(ValueError):
        PROBE.native_instrument("NOPE")


def test_build_probe_request_contract_stats_seconds_from_interval_limit():
    # contract_stats contract: `from` is Unix SECONDS (not ms), `interval` in
    # seconds, `limit` caps records, and `to` is NOT invented.
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_OPEN_INTEREST))
    assert (
        "https://api.gateio.ws/api/v4/futures/usdt/contract_stats" == query["url"]
    )
    assert query["params"]["contract"] == "BTC_USDT"
    assert query["params"]["from"] == 1655251200  # 10-digit-ish epoch seconds
    assert query["params"]["from"] < 10_000_000_000  # never 13-digit ms
    # LIVE OBSERVED (I13): interval is a STRING bucket, not seconds
    assert query["params"]["interval"] == "1h"
    assert "limit" in query["params"]
    assert "to" not in query["params"]


def test_build_probe_request_positions_via_public_contract_stats():
    # Market-wide positioning MUST come from PUBLIC /contract_stats, never user
    # /positions (private account data, OUT_OF_SCOPE).
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_POSITIONING))
    assert query["url"].endswith("/contract_stats")
    assert "/positions" not in query["url"]
    assert query["params"]["contract"] == "BTC_USDT"
    assert query["params"]["from"] < 10_000_000_000


def test_no_market_positioning_via_authenticated_positions():
    # Negative: the canonical market positioning candidate must not route to
    # the auth-gated user /positions surface.
    build = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_POSITIONING))
    assert "/positions" not in build["url"]
    assert "contract_stats" in build["url"]


def test_funding_uses_single_contract_get_funding_rate():
    # I13R1: funding MUST be the single-contract GET /funding_rate?contract=...
    # (no auth) — never the plural batch POST /funding_rates probed under a
    # GET-style model (that produced INVALID_CREDENTIALS = REQUEST_CONTRACT_INVALID).
    query = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    assert query["url"].endswith("/funding_rate")
    assert "/funding_rates" not in query["url"]
    assert query["params"]["contract"] == "BTC_USDT"
    assert "from" in query["params"] and "to" in query["params"]


def test_funding_get_route_has_no_auth():
    # The single-contract GET funding_rate route requires NO authentication;
    # a 401 on this route is REQUEST_CONTRACT_INVALID evidence, not provider
    # capability truth (I13R1 §10).
    url = PROBE.funding_rate_url()
    assert url.endswith("/funding_rate")
    assert PROBE.access_mode is AccessMode.PUBLIC_REST
    assert PROBE.classify_failure(401, _body("error_unauthorized.json")) is ProbeFailureClass.F_ACCESS_AUTH  # classifier maps the status


def test_batch_funding_rates_modeled_separately():
    # The plural batch route is POST /funding_rates — modeled SEPARATELY and
    # never confused with the single-contract GET funding_rate route.
    batch = PROBE.batch_funding_rates_url()
    assert batch.endswith("/funding_rates")
    single = PROBE.funding_rate_url()
    assert single.endswith("/funding_rate")
    assert single != batch


def test_build_probe_request_is_deterministic():
    a = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    b = PROBE.build_probe_request(_request(SensorFamily.MECHANICAL_FUNDING))
    assert a == b


# ---------------------------------------------------------------------------
# label-based failure classification
# ---------------------------------------------------------------------------


def test_classify_unauthorized_is_auth():
    assert (
        PROBE.classify_failure(401, _body("error_unauthorized.json"))
        is ProbeFailureClass.F_ACCESS_AUTH
    )


def test_classify_forbidden_is_geo_evidence():
    assert (
        PROBE.classify_failure(403, _body("error_forbidden_geo.json"))
        is ProbeFailureClass.F_ACCESS_GEO
    )


def test_classify_rate_limit_label():
    assert (
        PROBE.classify_failure(429, _body("error_429_label.json"))
        is ProbeFailureClass.F_ACCESS_RATE_LIMIT
    )


def test_classify_not_found_label():
    assert (
        PROBE.classify_failure(404, _body("error_404_label.json"))
        is ProbeFailureClass.F_ENDPOINT_REMOVED
    )


def test_classify_invalid_contract_is_symbol_level():
    assert (
        PROBE.classify_failure(400, _body("error_invalid_contract.json"))
        is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# characterization — success paths
# ---------------------------------------------------------------------------


def test_characterize_contract_stats_long_short_liquidation_and_oi():
    request = _request(SensorFamily.MECHANICAL_LIQUIDATION)
    attempt = PROBE.characterize(request, 200, _body("contract_stats_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 2
    units = attempt.native_units_summary
    assert "long_liq_size" in units
    assert "short_liq_size" in units
    assert "long_liq_usd" in units
    assert "short_liq_usd" in units
    assert attempt.first_timestamp_returned == datetime(2022, 6, 15, tzinfo=UTC)


def test_characterize_oi_from_contract_stats_has_usd_notional():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("contract_stats_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    units = attempt.native_units_summary
    assert "open_interest" in units
    assert "open_interest_usd" in units
    assert units["open_interest_usd"] == "USD notional"


def test_characterize_funding_success():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 200, _body("funding_rates_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert "funding_rate" in attempt.native_units_summary


def test_characterize_trades_taker_side_is_aggressor_semantics():
    # order-flow probing rides on MECHANICAL_TRADE (order flow is T2-derived,
    # not a frozen T1 SensorFamily member)
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    # Gate's taker_side IS the aggressor side — documented, no maker inversion
    assert "no maker inversion" in attempt.native_units_summary["taker_side"]


def test_characterize_orderbook_flattens_levels():
    request = _request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    attempt = PROBE.characterize(request, 200, _body("order_book_success.json"))
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 6  # 3 bids + 3 asks


def test_characterize_empty_contract_stats_is_valid_empty():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 200, _body("contract_stats_empty.json"))
    assert attempt.response_status_class is ResponseStatusClass.EMPTY_VALID
    assert attempt.error_class is None


# ---------------------------------------------------------------------------
# characterization — failure paths
# ---------------------------------------------------------------------------


def test_characterize_positions_unauthorized():
    request = _request(SensorFamily.MECHANICAL_POSITIONING)
    attempt = PROBE.characterize(request, 401, _body("error_unauthorized.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_AUTH
    assert attempt.requires_auth is True


def test_characterize_geo_forbidden():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 403, _body("error_forbidden_geo.json"))
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_GEO
    assert attempt.geo_block_detected is True


def test_characterize_rate_limit():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 429, _body("error_429_label.json"))
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_RATE_LIMIT


def test_characterize_not_found():
    request = _request(SensorFamily.MECHANICAL_FUNDING)
    attempt = PROBE.characterize(request, 404, _body("error_404_label.json"))
    assert attempt.error_class is ProbeFailureClass.F_ENDPOINT_REMOVED


def test_characterize_invalid_contract_symbol_error():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    attempt = PROBE.characterize(request, 400, _body("error_invalid_contract.json"))
    assert attempt.error_class is ProbeFailureClass.F_SYMBOL_NOT_FOUND
    assert "INVALID_PARAM_VALUE" in (attempt.error_detail_redacted or "")


# ---------------------------------------------------------------------------
# schema drift + pagination
# ---------------------------------------------------------------------------


def test_schema_drift_changes_fingerprint():
    success = fingerprint_payload(_body("trades_success.json"))
    drifted = fingerprint_payload(_body("trades_schema_changed.json"))
    assert success != drifted


def test_window_pagination_characterized():
    request = _request(SensorFamily.MECHANICAL_TRADE)
    attempt = PROBE.characterize(request, 200, _body("trades_success.json"))
    assert attempt.pagination_detected is True
    # last row (1655251330000) is before the requested end (1655280000000):
    # the window is not fully covered, so more pages exist
    assert attempt.pagination_complete is False


def test_characterize_is_offline_and_deterministic():
    request = _request(SensorFamily.MECHANICAL_OPEN_INTEREST)
    a = PROBE.characterize(request, 200, _body("contract_stats_success.json"))
    b = PROBE.characterize(request, 200, _body("contract_stats_success.json"))
    assert a.model_dump() == b.model_dump()
