"""Synthetic OKX Swap offline response fixtures (SENSOR-B3-I07).

Each payload is labeled **SYNTHETIC_SCHEMA_FIXTURE** and reconstructed exactly
from the committed Bloc 2 schema fingerprints (09_SCHEMA_FINGERPRINTS.jsonl),
the corrected live_probe_contracts.yaml, and the committed Bloc 2 probe fixture
shapes (`tests/.../probe_payloads/okx/*.json`):

- FUNDING: `{code, msg, data:[{formulaType, fundingRate, fundingTime, instId,
  instType, method, realizedRate}]}` — `fundingTime` is a millisecond-epoch
  STRING.  This is the closed SEVEN-field runtime fingerprint; `markPrice` is
  probe-fixture-only and modeled as an optional/unverified ADDITIVE field
  (`FUNDING_MARKPRICE_ADDITIVE`), never a required evidence-backed field.
- TRADE:   `{code, msg, data:[{instId, px, side, source, sz, tradeId, ts}]}` —
  `ts` is a millisecond-epoch STRING; `side` is the native aggressor side.
- BOOK:    `{code, msg, data:[{asks, bids, seqId, ts}]}` — bids/asks are
  `list[list[str]]`, `seqId` int, `ts` millisecond-epoch STRING.

Envelope success is `code == "0"`.  Nonzero provider codes (e.g. 51001 invalid
instrument, 50011 rate limit, 50113 auth) are provider errors, NEVER
EMPTY_VALID.  These are offline test inputs only — no live network calls.
"""

from __future__ import annotations

from typing import Any

#: Every fixture is synthetic; surfaced in the evidence manifest.
FIXTURE_LABEL = "SYNTHETIC_SCHEMA_FIXTURE"

SYMBOL = "BTC-USDT-SWAP"


def _ok(data: Any) -> dict[str, Any]:
    return {"code": "0", "msg": "", "data": data}


def funding_row(ts_ms: int = 1755000000000) -> dict[str, Any]:
    # EXACTLY the closed SEVEN-field funding record of the committed
    # 09_SCHEMA_FINGERPRINTS.jsonl fingerprint.  markPrice is NOT part of the
    # runtime fingerprint (probe fixture only) and lives in
    # FUNDING_MARKPRICE_ADDITIVE as an optional/unverified additive field.
    return {
        "instId": SYMBOL,
        "fundingRate": "0.000075",
        "realizedRate": "0.000075",
        "fundingTime": str(ts_ms),
        "formulaType": "A",
        "instType": "SWAP",
        "method": "ma",
    }


# --------------------------------------------------------------------------- #
# FUNDING
# --------------------------------------------------------------------------- #
FUNDING_HAPPY = _ok(
    [funding_row(), funding_row(1755000000300), funding_row(1755000000600)]
)
FUNDING_EMPTY = _ok([])
FUNDING_ADDITIVE = _ok(
    [{**funding_row(), "extraProviderField": "x"}]
)
#: markPrice is a probe-fixture-only field (NOT in the 09 runtime fingerprint):
#: it must be modeled as an OPTIONAL/UNVERIFIED additive field — preserved when
#: present, flagged ADDITIVE, NEVER required (SENSOR-B3-I07R1 Repair 5).
FUNDING_MARKPRICE_ADDITIVE = _ok(
    [{**funding_row(), "markPrice": "29510.5"}]
)
#: malformed fundingTime (float-like string) -> BREAKING.
FUNDING_BAD_TIMESTAMP = _ok([{**funding_row(), "fundingTime": "1755000000.0"}])
#: fundingTime None -> BREAKING.
FUNDING_NONE_TIMESTAMP = _ok([{**funding_row(), "fundingTime": None}])
FUNDING_BOOL_TIMESTAMP = _ok([{**funding_row(), "fundingTime": True}])
FUNDING_MISSING_REQUIRED = _ok([
    {k: v for k, v in funding_row().items() if k != "realizedRate"}
])
FUNDING_DRIFT = {"not": "an", "envelope": ["x"]}

# --------------------------------------------------------------------------- #
# TRADE
# --------------------------------------------------------------------------- #
TRADE_HAPPY = _ok(
    [
        {"instId": SYMBOL, "tradeId": "500003", "px": "29512.0", "sz": "0.5",
         "side": "sell", "ts": "1755000000000", "source": "a"},
        {"instId": SYMBOL, "tradeId": "500002", "px": "29511.5", "sz": "0.2",
         "side": "buy", "ts": "1754999400000", "source": "b"},
        {"instId": SYMBOL, "tradeId": "500001", "px": "29510.0", "sz": "1.1",
         "side": "sell", "ts": "1754998800000", "source": "a"},
    ]
)
TRADE_EMPTY = _ok([])
TRADE_ADDITIVE = _ok(
    [{"instId": SYMBOL, "tradeId": "500001", "px": "29510.0", "sz": "1.1",
     "side": "sell", "ts": "1754998800000", "source": "a", "extra": "z"}]
)
TRADE_BAD_TIMESTAMP = _ok([
    {"instId": SYMBOL, "tradeId": "500001", "px": "29510.0", "sz": "1.1",
     "side": "sell", "ts": 1754998800000}  # int, not str -> BREAKING
])
TRADE_MISSING_SIDE = _ok([
    {"instId": SYMBOL, "tradeId": "500001", "px": "29510.0", "sz": "1.1",
     "ts": "1754998800000"}
])
TRADE_DRIFT = {"label": "INVALID", "message": "not data"}

#: descending-order trade page (newest first): OKX history can be returned in
#: descending time order, so PARTIAL/GAP classification must NOT depend on
#: first/last row ordering (SENSOR-B3-I07R2).  t3 newest, t2, t1 oldest.
TRADE_T3 = 1755000000000  # 2025-08-12T22:40:00Z
TRADE_T2 = 1754999400000  # 2025-08-12T22:30:00Z
TRADE_T1 = 1754998800000  # 2025-08-12T22:20:00Z


def trade_row(ts_ms: int, trade_id: str = "500001", side: str = "sell") -> dict[str, Any]:
    return {
        "instId": SYMBOL,
        "tradeId": trade_id,
        "px": "29510.0",
        "sz": "1.1",
        "side": side,
        "ts": str(ts_ms),
        "source": "a",
    }


TRADE_DESCENDING = _ok(
    [
        trade_row(TRADE_T3, trade_id="500003"),
        trade_row(TRADE_T2, trade_id="500002", side="buy"),
        trade_row(TRADE_T1, trade_id="500001"),
    ]
)
#: scrambled (non-monotonic) trade page: still contains a valid in-window row.
TRADE_SCRAMBLED = _ok(
    [
        trade_row(TRADE_T2, trade_id="500002", side="buy"),
        trade_row(TRADE_T3, trade_id="500003"),
        trade_row(TRADE_T1, trade_id="500001"),
    ]
)

# --------------------------------------------------------------------------- #
# BOOK (CURRENT_ONLY)
# --------------------------------------------------------------------------- #
def _book(ts_ms: int = 1755000000000) -> dict[str, Any]:
    return {
        "asks": [["29512.0", "0.5", "0", "2"], ["29512.5", "2.1", "0", "1"]],
        "bids": [["29498.0", "1.2", "0", "1"], ["29497.5", "3.4", "0", "4"]],
        "seqId": 1001,
        "ts": str(ts_ms),
    }


BOOK_HAPPY = _ok([_book()])
BOOK_EMPTY = _ok([])  # current snapshot returning no book row -> EMPTY_VALID
BOOK_ADDITIVE = _ok([{**_book(), "extraField": "y"}])
BOOK_BAD_TIMESTAMP = _ok([{**_book(), "ts": 1755000000000}])  # int not str
BOOK_NONE_TIMESTAMP = _ok([{**_book(), "ts": None}])
BOOK_MISSING_BIDS = _ok([{k: v for k, v in _book().items() if k != "bids"}])
BOOK_BAD_LEVEL = _ok([{**_book(), "bids": [["29498.0", 1.2]]}])  # non-str level
#: one-element price-only level (missing size) -> BREAKING (I07R1 Repair 4).
BOOK_LEVEL_ONE_ELEMENT = _ok([{**_book(), "bids": [["29498.0"]], "asks": [["29512.0"]]}])
#: zero-element level -> BREAKING.
BOOK_LEVEL_EMPTY = _ok([{**_book(), "bids": [[]]}])
#: minimal valid [price, size] two-element level -> PASS (evidence allows
#: optional trailing native fields, so 4-element rows stay valid).
BOOK_LEVEL_MINIMAL = _ok(
    [{**_book(), "bids": [["29498.0", "1.2"]], "asks": [["29512.0", "0.5"]]}]
)
#: bool must NOT pass as the int seqId (bool subclasses int) -> BREAKING.
BOOK_SEQID_BOOL_TRUE = _ok([{**_book(), "seqId": True}])
BOOK_SEQID_BOOL_FALSE = _ok([{**_book(), "seqId": False}])
BOOK_DRIFT = {"code": "0", "data": {"not": "a list"}}

# --------------------------------------------------------------------------- #
# PROVIDER ERRORS (never EMPTY_VALID)
# --------------------------------------------------------------------------- #
ERROR_INVALID_INSTRUMENT = {"code": "51001", "msg": "Instrument ID does not exist", "data": []}
ERROR_RATE_LIMIT = {"code": "50011", "msg": "Requests too frequent", "data": []}
ERROR_AUTH = {"code": "50113", "msg": "Please login", "data": []}
ERROR_OTHER = {"code": "99999", "msg": "some provider error", "data": []}
#: plain 5xx server failure WITHOUT an OKX code envelope (maps to ProviderUnavailable).
HTTP_500_BODY = {"msg": "internal server error"}

#: routing table keyed by URL fragment
ROUTES: dict[str, Any] = {
    "/funding-rate-history": FUNDING_HAPPY,
    "/history-trades": TRADE_HAPPY,
    "/books": BOOK_HAPPY,
}

SCENARIOS_TIMESTAMP: dict[str, dict[str, tuple[int, Any]]] = {
    "funding": {
        "happy": (200, FUNDING_HAPPY),
        "empty": (200, FUNDING_EMPTY),
        "additive": (200, FUNDING_ADDITIVE),
        "bad_timestamp": (200, FUNDING_BAD_TIMESTAMP),
        "none_timestamp": (200, FUNDING_NONE_TIMESTAMP),
        "bool_timestamp": (200, FUNDING_BOOL_TIMESTAMP),
        "missing_field": (200, FUNDING_MISSING_REQUIRED),
        "drift": (200, FUNDING_DRIFT),
        "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
        "rate_limit": (429, ERROR_RATE_LIMIT),
        "provider_error": (500, HTTP_500_BODY),
    },
    "trade": {
        "happy": (200, TRADE_HAPPY),
        "empty": (200, TRADE_EMPTY),
        "additive": (200, TRADE_ADDITIVE),
        "bad_timestamp": (200, TRADE_BAD_TIMESTAMP),
        "missing_field": (200, TRADE_MISSING_SIDE),
        "drift": (200, TRADE_DRIFT),
        "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
        "rate_limit": (429, ERROR_RATE_LIMIT),
        "provider_error": (500, ERROR_OTHER),
    },
    "book": {
        "happy": (200, BOOK_HAPPY),
        "empty": (200, BOOK_EMPTY),
        "additive": (200, BOOK_ADDITIVE),
        "bad_timestamp": (200, BOOK_BAD_TIMESTAMP),
        "none_timestamp": (200, BOOK_NONE_TIMESTAMP),
        "missing_field": (200, BOOK_MISSING_BIDS),
        "bad_level": (200, BOOK_BAD_LEVEL),
        "drift": (200, BOOK_DRIFT),
        "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
        "rate_limit": (429, ERROR_RATE_LIMIT),
        "provider_error": (500, HTTP_500_BODY),
    },
}