"""Synthetic Gate Futures offline response fixtures (SENSOR-B3-I06).

Each payload is a **SYNTHETIC_SCHEMA_FIXTURE** reconstructed exactly from the
committed Bloc 2 schema fingerprints (09_SCHEMA_FINGERPRINTS.jsonl + the
corrected live_probe_contracts.yaml):

- contract_stats (OI / LIQUIDATION / POSITIONING): a TOP-LEVEL LIST of provider
  dicts carrying one physical `dict{last_funding_rate, long_liq_*, short_liq_*,
  lsr_*, mark_price, open_interest, open_interest_usd, time, top_*}` row.  The
  union allows int/float NUMERIC SEMANTIC FAMILY variation; `time` is strict
  int native epoch MILLISECONDS.
- funding_rate: a TOP-LEVEL LIST of `dict{r: str, t: int}` (t = epoch SECONDS).

Retention (older `from`) returns `dict{label, message}` with
"from time exceeds 180-day limit" (the committed 2022-era error shape).  These
are offline test inputs only — NO live network calls in I06.
"""

from __future__ import annotations

from typing import Any

# Every fixture is synthetic; this tag is surfaced in the evidence manifest.
FIXTURE_LABEL = "SYNTHETIC_SCHEMA_FIXTURE"

#: One canonical physical contract_stats row matching the union fingerprint.
#: `time` is native epoch MILLISECONDS (1755000000000 ms = 2025-08-12T20:00:00Z).
def contract_stats_row(time_ms: int = 1755000000000) -> dict[str, Any]:
    return {
        "last_funding_rate": "0.000100",
        "long_liq_amount": 10.5,
        "long_liq_size": 5,
        "long_liq_usd": 500000.5,
        "long_liq_usd_new": 500000.25,
        "long_taker_size": 100,
        "long_users": 120,
        "lsr_account": 1.25,
        "lsr_taker": 1.15,
        "mark_price": 65000.0,
        "open_interest": 12500,
        "open_interest_usd": 812500000.5,
        "short_liq_amount": 8.0,
        "short_liq_size": 4,
        "short_liq_usd": 400000.0,
        "short_liq_usd_new": 400000.1,
        "short_taker_size": 80,
        "short_users": 95,
        "time": time_ms,
        "top_long_account": 8,
        "top_long_size": 3000,
        "top_lsr_account": 1.4,
        "top_lsr_size": 4000.0,
        "top_short_account": 6,
        "top_short_size": 2500,
    }


#: Shared physical /contract_stats happy payload (OI / LIQUIDATION / POSITIONING).
CONTRACT_STATS_HAPPY: list[dict[str, Any]] = [
    contract_stats_row(1755000000000),
    contract_stats_row(1755003600000),
]

#: Valid empty top-level list (EMPTY_VALID observation for the surface).
CONTRACT_STATS_EMPTY: list[dict[str, Any]] = []

#: A row with an extra (additive) provider field — required semantics intact.
_CONTRACT_STATS_ADDITIVE_ROW = contract_stats_row(1755000000000)
_CONTRACT_STATS_ADDITIVE_ROW["funding_interval"] = 3600
CONTRACT_STATS_ADDITIVE: list[dict[str, Any]] = [_CONTRACT_STATS_ADDITIVE_ROW]

#: Schema drift: top-level OBJECT (e.g. a provider error masquerading as data).
CONTRACT_STATS_DRIFT: dict[str, Any] = {"unexpected_envelope": 1}
#: Schema drift: row missing a required semantic field (OI open_interest).
CONTRACT_STATS_MISSING_FIELD: list[dict[str, Any]] = [
    {k: v for k, v in contract_stats_row().items() if k != "open_interest"}
]
#: Malformed timestamp: `time` is a STRING (must fail closed; no int coercion).
CONTRACT_STATS_BAD_TIME: list[dict[str, Any]] = [
    {**contract_stats_row(), "time": "1755000000000"}
]
#: Malformed timestamp: `time` is None (must fail closed).
CONTRACT_STATS_NONE_TIME: list[dict[str, Any]] = [
    {**contract_stats_row(), "time": None}
]

#: Provider error envelope: symbol / contract not found.
INVALID_CONTRACT: dict[str, Any] = {
    "label": "INVALID_PARAM_VALUE",
    "message": "contract ETH_USDT not found",
}
#: Provider error envelope: 180-day rolling retention boundary.
RETENTION_ERROR: dict[str, Any] = {
    "label": "INVALID_PARAM_VALUE",
    "message": "from time exceeds 180-day limit",
}
#: Provider rate-limit error envelope.
RATE_LIMIT_ERROR: dict[str, Any] = {
    "label": "RATE_LIMIT_CONTROL",
    "message": "Too many requests. Retry later",
}
#: Provider error envelope: generic provider message.
PROVIDER_ERROR: dict[str, Any] = {
    "label": "INTERNAL",
    "message": "internal server error",
}


def _scenario(body: Any, status: int = 200) -> tuple[int, Any]:
    return (status, body)


#: contract_stats virtual-expression body builders keyed by sensor.
CONTRACT_STATS_SCENARIOS: dict[str, dict[str, tuple[int, Any]]] = {
    "open_interest": {
        "happy": _scenario(CONTRACT_STATS_HAPPY),
        "empty": _scenario(CONTRACT_STATS_EMPTY),
        "additive": _scenario(CONTRACT_STATS_ADDITIVE),
        "drift": _scenario(CONTRACT_STATS_DRIFT),
        "missing_field": _scenario(CONTRACT_STATS_MISSING_FIELD),
        "bad_time": _scenario(CONTRACT_STATS_BAD_TIME),
        "none_time": _scenario(CONTRACT_STATS_NONE_TIME),
        "invalid_contract": _scenario(INVALID_CONTRACT, status=400),
        "retention": _scenario(RETENTION_ERROR, status=400),
        "rate_limit": _scenario(RATE_LIMIT_ERROR, status=429),
        "provider_error": _scenario(PROVIDER_ERROR, status=500),
    },
    "liquidation": {
        "happy": _scenario(CONTRACT_STATS_HAPPY),
        "empty": _scenario(CONTRACT_STATS_EMPTY),
        "additive": _scenario(CONTRACT_STATS_ADDITIVE),
        "drift": _scenario(CONTRACT_STATS_DRIFT),
        "missing_field": _scenario(CONTRACT_STATS_MISSING_FIELD),
        "bad_time": _scenario(CONTRACT_STATS_BAD_TIME),
        "none_time": _scenario(CONTRACT_STATS_NONE_TIME),
        "invalid_contract": _scenario(INVALID_CONTRACT, status=400),
        "retention": _scenario(RETENTION_ERROR, status=400),
        "rate_limit": _scenario(RATE_LIMIT_ERROR, status=429),
        "provider_error": _scenario(PROVIDER_ERROR, status=500),
    },
    "positioning": {
        "happy": _scenario(CONTRACT_STATS_HAPPY),
        "empty": _scenario(CONTRACT_STATS_EMPTY),
        "additive": _scenario(CONTRACT_STATS_ADDITIVE),
        "drift": _scenario(CONTRACT_STATS_DRIFT),
        "missing_field": _scenario(CONTRACT_STATS_MISSING_FIELD),
        "bad_time": _scenario(CONTRACT_STATS_BAD_TIME),
        "none_time": _scenario(CONTRACT_STATS_NONE_TIME),
        "invalid_contract": _scenario(INVALID_CONTRACT, status=400),
        "retention": _scenario(RETENTION_ERROR, status=400),
        "rate_limit": _scenario(RATE_LIMIT_ERROR, status=429),
        "provider_error": _scenario(PROVIDER_ERROR, status=500),
    },
}

#: funding -> `list[dict{r:str, t:int}]`.
FUNDING_HAPPY: list[dict[str, Any]] = [{"r": "0.000100", "t": 1755000000}]
FUNDING_EMPTY: list[dict[str, Any]] = []
FUNDING_BAD_T: list[dict[str, Any]] = [{"r": "0.000100", "t": "1755000000"}]
FUNDING_NONE_T: list[dict[str, Any]] = [{"r": "0.000100", "t": None}]
FUNDING_BOOL_T: list[dict[str, Any]] = [{"r": "0.000100", "t": True}]
FUNDING_MISSING_T: list[dict[str, Any]] = [{"r": "0.000100"}]
FUNDING_DRIFT: dict[str, Any] = 7

FUNDING_SCENARIOS: dict[str, tuple[int, Any]] = {
    "happy": _scenario(FUNDING_HAPPY),
    "empty": _scenario(FUNDING_EMPTY),
    "bad_t": _scenario(FUNDING_BAD_T),
    "none_t": _scenario(FUNDING_NONE_T),
    "bool_t": _scenario(FUNDING_BOOL_T),
    "missing_t": _scenario(FUNDING_MISSING_T),
    "drift": _scenario(FUNDING_DRIFT),
    "invalid_contract": _scenario(INVALID_CONTRACT, status=400),
    "retention": _scenario(RETENTION_ERROR, status=400),
    "rate_limit": _scenario(RATE_LIMIT_ERROR, status=429),
    "provider_error": _scenario(PROVIDER_ERROR, status=500),
}