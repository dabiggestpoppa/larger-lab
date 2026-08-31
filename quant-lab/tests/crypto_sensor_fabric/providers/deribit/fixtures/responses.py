"""Synthetic Deribit v2 offline response fixtures (SENSOR-B3-I08).

Each payload is labeled **SYNTHETIC_SCHEMA_FIXTURE** and reconstructed exactly
from the committed Bloc 2 schema fingerprints (09_SCHEMA_FINGERPRINTS.jsonl),
the corrected live_probe_contracts.yaml, and the committed Bloc 2 probe fixture
shapes (`tests/.../probe_payloads/deribit/*.json`):

- TRADE/LIQUIDATION: `{jsonrpc, result: {has_more: bool, trades: [<row>]},
  testnet, usDiff, usIn, usOut}` — trade rows are the closed THIRTEEN-field
  runtime record (`amount, contracts, direction, index_price,
  instrument_name, mark_price, price, starbase_match_id, starbase_timestamp,
  tick_direction, timestamp, trade_id, trade_seq`), `timestamp` an
  epoch-MILLISECOND int.  The `liquidation` flag (`"liquidation" | "taker" |
  "maker"`) is characterization-backed and KNOWN-OPTIONAL.
- FUNDING: `result` is a RAW LIST of closed FIVE-field rows (`index_price,
  interest_1h, interest_8h, prev_index_price, timestamp`) — observed LIVE;
  `funding_rate`/`funding_1h`/`funding_8h` are probe-fixture-only and modeled
  as OPTIONAL/UNVERIFIED additive fields (`FUNDING_ADDITIVE`), never required.
- BOOK: `result` dict; structural core `timestamp` (epoch-ms int),
  `instrument_name`, `bids` + `asks` (`list[list[float]]`, min `[price,
  amount]`); other fingerprint-listed fields are known-optional.

Provider errors are JSON-RPC `{"error": {"code": <int>, "message": ...}}`
bodies that may ride HTTP 200 — never EMPTY_VALID.  These are offline test
inputs only — no live network calls.
"""

from __future__ import annotations

from typing import Any

#: Every fixture is synthetic; surfaced in the evidence manifest.
FIXTURE_LABEL = "SYNTHETIC_SCHEMA_FIXTURE"

SYMBOL = "BTC-PERPETUAL"

#: Shared epoch-ms timestamps (2022-06-15 around 00:00Z for the RECENT-era
#: samples we reconstruct; tests build requested windows around these).
T1 = 1655251200000  # 2022-06-15T00:00:00Z
T2 = 1655251265000  # +65s
T3 = 1655251330000  # +130s
T4 = 1655254800000  # 2022-06-15T01:00:00Z


def _ok_result(result: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": result,
        "testnet": False,
        "usDiff": 1,
        "usIn": 1,
        "usOut": 1,
    }


def trade_row(
    ts_ms: int = T1,
    trade_id: str = "123456001",
    direction: str = "sell",
    liquidation: str | None = None,
    trade_seq: int = 1,
) -> dict[str, Any]:
    """EXACTLY the closed THIRTEEN-field runtime trade record (plus optional
    characterization `liquidation` flag when requested)."""
    row: dict[str, Any] = {
        "amount": 0.0089,
        "contracts": 0.0089,
        "direction": direction,
        "index_price": 29508.0,
        "instrument_name": SYMBOL,
        "mark_price": 29510.0,
        "price": 29510.5,
        "starbase_match_id": 123,
        "starbase_timestamp": ts_ms,
        "tick_direction": 1,
        "timestamp": ts_ms,
        "trade_id": trade_id,
        "trade_seq": trade_seq,
    }
    if liquidation is not None:
        row["liquidation"] = liquidation
    return row


def _trades_result(rows: list[dict[str, Any]], has_more: bool = False) -> dict[str, Any]:
    return {"has_more": has_more, "trades": rows}


# --------------------------------------------------------------------------- #
# TRADE
# --------------------------------------------------------------------------- #
TRADE_HAPPY = _ok_result(
    _trades_result(
        [
            trade_row(T1, trade_id="123456001", direction="sell"),
            trade_row(T2, trade_id="123456002", direction="buy", trade_seq=2),
            trade_row(T3, trade_id="123456003", direction="sell", trade_seq=3),
        ],
        has_more=False,
    )
)
TRADE_EMPTY = _ok_result(_trades_result([], has_more=False))
TRADE_HAS_MORE_TRUE = _ok_result(
    _trades_result(
        [
            trade_row(T1, trade_id="123456001", direction="sell"),
            trade_row(T2, trade_id="123456002", direction="buy", trade_seq=2),
        ],
        has_more=True,
    )
)
TRADE_ADDITIVE = _ok_result(
    _trades_result(
        [trade_row(T1, trade_id="123456001", direction="sell", liquidation="taker"),
         {**trade_row(T2, trade_id="123456002", direction="buy", trade_seq=2),
          "extraProviderField": "x"}],
        has_more=False,
    )
)
TRADE_BAD_TIMESTAMP_FLOAT = _ok_result(
    _trades_result([trade_row(float(T1), trade_id="123456001")])
)
TRADE_BAD_TIMESTAMP_BOOL = _ok_result(
    _trades_result([trade_row(True, trade_id="123456001")])
)
TRADE_BAD_TIMESTAMP_STR = _ok_result(
    _trades_result([trade_row(str(T1), trade_id="123456001")])
)
TRADE_NONE_TIMESTAMP = _ok_result(
    _trades_result([trade_row(None, trade_id="123456001")])  # type: ignore[arg-type]
)
TRADE_MISSING_REQUIRED = _ok_result(
    _trades_result(
        [{k: v for k, v in trade_row(T1).items() if k != "trade_id"}]
    )
)
TRADE_MISSING_HAS_MORE = _ok_result({"trades": [trade_row(T1)]})
TRADE_BAD_HAS_MORE = _ok_result({"has_more": "yes", "trades": [trade_row(T1)]})
TRADE_BAD_LEVEL_NESTING = _ok_result(_trades_result(["not-a-dict"]))
#: descending-order page (newest first) — PARTIAL/GAP must be order-invariant.
TRADE_DESCENDING = _ok_result(
    _trades_result(
        [
            trade_row(T3, trade_id="123456003", direction="sell", trade_seq=3),
            trade_row(T2, trade_id="123456002", direction="buy", trade_seq=2),
            trade_row(T1, trade_id="123456001", direction="sell"),
        ],
        has_more=False,
    )
)
TRADE_DRIFT = {"label": "INVALID", "message": "not data"}

# --------------------------------------------------------------------------- #
# LIQUIDATION (mechanism microscope — same physical surface, filtered view)
# --------------------------------------------------------------------------- #
#: mixed page: one forced liquidation ("liquidation"), two ordinary trades.
LIQ_HAPPY = _ok_result(
    _trades_result(
        [
            trade_row(T1, trade_id="9990001", direction="sell", liquidation="liquidation"),
            trade_row(T2, trade_id="9990002", direction="buy", liquidation="taker", trade_seq=2),
            trade_row(T3, trade_id="9990003", direction="sell", liquidation="maker", trade_seq=3),
        ],
        has_more=False,
    )
)
#: no forced-liquidation events -> LIQUIDATION view EMPTY_VALID (raw preserved).
LIQ_NO_EVENTS = _ok_result(
    _trades_result(
        [
            trade_row(T1, trade_id="9990001", direction="sell", liquidation="taker"),
            trade_row(T2, trade_id="9990002", direction="buy", liquidation="maker", trade_seq=2),
        ],
        has_more=False,
    )
)
#: rows without the flag are ordinary trades too.
LIQ_MISSING_FLAG = _ok_result(
    _trades_result(
        [trade_row(T1, trade_id="9990001", direction="sell"),
         trade_row(T2, trade_id="9990002", direction="buy", trade_seq=2)],
        has_more=False,
    )
)
#: union-shape row with combo fields (liquidation fingerprint variant) is valid.
LIQ_COMBO_ROW = _ok_result(
    _trades_result(
        [{**trade_row(T1, trade_id="9990001", direction="sell",
                     liquidation="liquidation"),
          "combo_id": "cb-1", "combo_trade_id": "9990001-c"}],
        has_more=False,
    )
)
LIQ_BAD_FLAG_TYPE = _ok_result(
    _trades_result(
        [{**trade_row(T1, trade_id="9990001", direction="sell"),
          "liquidation": True}]
    )
)
LIQ_MISSING_REQUIRED = _ok_result(
    _trades_result(
        [{k: v for k, v in trade_row(T1, liquidation="liquidation").items()
          if k != "trade_seq"}]
    )
)
LIQ_EMPTY = _ok_result(_trades_result([], has_more=False))

# --------------------------------------------------------------------------- #
# FUNDING (result is a RAW LIST — observed LIVE)
# --------------------------------------------------------------------------- #
def funding_row(ts_ms: int = T1) -> dict[str, Any]:
    """EXACTLY the closed FIVE-field funding record of the committed 09
    fingerprint.  funding_rate/funding_1h/funding_8h are probe-fixture-only and
    live in FUNDING_ADDITIVE as optional/unverified additive fields."""
    return {
        "index_price": 29508.0,
        "interest_1h": 0.0000125,
        "interest_8h": 0.0001,
        "prev_index_price": 29490.0,
        "timestamp": ts_ms,
    }


FUNDING_HAPPY = _ok_result(
    [funding_row(T1), funding_row(T2), funding_row(T3)]
)
FUNDING_EMPTY = _ok_result([])
FUNDING_ADDITIVE = _ok_result(
    [
        {**funding_row(T1), "funding_rate": 0.000075,
         "funding_1h": 0.000075, "funding_8h": 0.0006},
        funding_row(T2),
    ]
)
FUNDING_BAD_TIMESTAMP_FLOAT = _ok_result([funding_row(float(T1))])
FUNDING_BAD_TIMESTAMP_BOOL = _ok_result([funding_row(True)])  # type: ignore[arg-type]
FUNDING_BAD_TIMESTAMP_STR = _ok_result([funding_row(str(T1))])  # type: ignore[arg-type]
FUNDING_NONE_TIMESTAMP = _ok_result([funding_row(None)])  # type: ignore[arg-type]
FUNDING_MISSING_REQUIRED = _ok_result(
    [{k: v for k, v in funding_row().items() if k != "interest_8h"}]
)
FUNDING_DRIFT_DICT_RESULT = _ok_result({"data": [funding_row()]})
FUNDING_DRIFT = {"not": "an", "envelope": ["x"]}

# --------------------------------------------------------------------------- #
# BOOK (CURRENT_ONLY snapshot; result dict)
# --------------------------------------------------------------------------- #
def _book_result() -> dict[str, Any]:
    return {
        "timestamp": 1788048000000,
        "instrument_name": SYMBOL,
        "bids": [
            [29498.0, 1.2],
            [29497.5, 3.4],
            [29497.0, 0.8],
        ],
        "asks": [
            [29512.0, 0.5],
            [29512.5, 2.1],
            [29513.0, 1.7],
        ],
        "best_bid_price": 29498.0,
        "best_ask_price": 29512.0,
        "mark_price": 29510.0,
        "index_price": 29508.0,
        "open_interest": 12345,
        "change_id": 9001,
        "state": "open",
        "stats": {
            "high": 29600.0,
            "low": 29400.0,
            "price_change": -0.002,
            "volume": 1200.5,
            "volume_notional": 1200.5,
            "volume_usd": 35400000.0,
        },
    }


BOOK_HAPPY = _ok_result(_book_result())
#: minimal snapshot with ONLY the structural core (known-optional fields absent
#: are fine — they are not required for the sensor view).
BOOK_MINIMAL = _ok_result(
    {
        "timestamp": 1788048000000,
        "instrument_name": SYMBOL,
        "bids": [[29498.0, 1.2]],
        "asks": [[29512.0, 0.5]],
    }
)
BOOK_EMPTY_LEVELS = _ok_result(
    {
        "timestamp": 1788048000000,
        "instrument_name": SYMBOL,
        "bids": [],
        "asks": [],
    }
)
BOOK_ADDITIVE = _ok_result({**_book_result(), "extraResultField": "y"})
BOOK_BAD_TIMESTAMP_FLOAT = _ok_result({**_book_result(), "timestamp": 1788048000000.5})
BOOK_BAD_TIMESTAMP_BOOL = _ok_result({**_book_result(), "timestamp": True})
BOOK_BAD_TIMESTAMP_STR = _ok_result({**_book_result(), "timestamp": "1788048000000"})
BOOK_MISSING_BIDS = _ok_result(
    {k: v for k, v in _book_result().items() if k != "bids"}
)
BOOK_MISSING_ASKS = _ok_result(
    {k: v for k, v in _book_result().items() if k != "asks"}
)
BOOK_BAD_LEVEL_ONE_ELEMENT = _ok_result(
    {**_book_result(), "bids": [[29498.0]]}
)
BOOK_BAD_LEVEL_EMPTY = _ok_result({**_book_result(), "bids": [[]]})
BOOK_BAD_LEVEL_BOOL = _ok_result({**_book_result(), "bids": [[True, 1.2]]})
BOOK_BAD_LEVEL_STRING = _ok_result({**_book_result(), "bids": ["29498.0"]})
BOOK_LEVEL_MINIMAL = _ok_result(
    {**_book_result(), "bids": [[29498.0, 1.2]], "asks": [[29512.0, 0.5]]}
)
BOOK_DRIFT = _ok_result({"not": "a book"})

# --------------------------------------------------------------------------- #
# PROVIDER ERRORS (JSON-RPC; may ride HTTP 200 — never EMPTY_VALID)
# --------------------------------------------------------------------------- #
def _rpc_error(code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "error": {"code": code, "message": message}}


ERROR_INVALID_INSTRUMENT = _rpc_error(40400, "invalid instrument name")
ERROR_RATE_LIMIT = _rpc_error(10001, "rate limit reached")
ERROR_AUTH = _rpc_error(10000, "not_authorized")
ERROR_ENDPOINT_REMOVED = _rpc_error(-32601, "method not found")
ERROR_UNKNOWN = _rpc_error(-32000, "some provider error")
#: plain 5xx server failure WITHOUT a JSON-RPC error envelope.
HTTP_500_BODY = {"msg": "internal server error"}

#: routing table keyed by URL fragment
ROUTES: dict[str, Any] = {
    "/get_last_trades_by_instrument": TRADE_HAPPY,
    "/get_funding_rate_history": FUNDING_HAPPY,
    "/get_order_book": BOOK_HAPPY,
}

SCENARIOS_TRADE: dict[str, tuple[int, Any]] = {
    "happy": (200, TRADE_HAPPY),
    "empty": (200, TRADE_EMPTY),
    "has_more_true": (200, TRADE_HAS_MORE_TRUE),
    "additive": (200, TRADE_ADDITIVE),
    "bad_timestamp": (200, TRADE_BAD_TIMESTAMP_FLOAT),
    "bool_timestamp": (200, TRADE_BAD_TIMESTAMP_BOOL),
    "str_timestamp": (200, TRADE_BAD_TIMESTAMP_STR),
    "none_timestamp": (200, TRADE_NONE_TIMESTAMP),
    "missing_field": (200, TRADE_MISSING_REQUIRED),
    "missing_has_more": (200, TRADE_MISSING_HAS_MORE),
    "bad_has_more": (200, TRADE_BAD_HAS_MORE),
    "drift": (200, TRADE_DRIFT),
    "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
    "rate_limit": (429, ERROR_RATE_LIMIT),
    "provider_error": (500, HTTP_500_BODY),
}

SCENARIOS_LIQUIDATION: dict[str, tuple[int, Any]] = {
    "happy": (200, LIQ_HAPPY),
    "no_events": (200, LIQ_NO_EVENTS),
    "missing_flag": (200, LIQ_MISSING_FLAG),
    "empty": (200, LIQ_EMPTY),
    "bad_flag_type": (200, LIQ_BAD_FLAG_TYPE),
    "missing_field": (200, LIQ_MISSING_REQUIRED),
    "bad_timestamp": (200, TRADE_BAD_TIMESTAMP_FLOAT),
    "drift": (200, TRADE_DRIFT),
    "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
    "rate_limit": (429, ERROR_RATE_LIMIT),
    "provider_error": (500, HTTP_500_BODY),
}

SCENARIOS_FUNDING: dict[str, tuple[int, Any]] = {
    "happy": (200, FUNDING_HAPPY),
    "empty": (200, FUNDING_EMPTY),
    "additive": (200, FUNDING_ADDITIVE),
    "bad_timestamp": (200, FUNDING_BAD_TIMESTAMP_FLOAT),
    "bool_timestamp": (200, FUNDING_BAD_TIMESTAMP_BOOL),
    "str_timestamp": (200, FUNDING_BAD_TIMESTAMP_STR),
    "none_timestamp": (200, FUNDING_NONE_TIMESTAMP),
    "missing_field": (200, FUNDING_MISSING_REQUIRED),
    "dict_result": (200, FUNDING_DRIFT_DICT_RESULT),
    "drift": (200, FUNDING_DRIFT),
    "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
    "rate_limit": (429, ERROR_RATE_LIMIT),
    "provider_error": (500, HTTP_500_BODY),
}

SCENARIOS_BOOK: dict[str, tuple[int, Any]] = {
    "happy": (200, BOOK_HAPPY),
    "minimal": (200, BOOK_MINIMAL),
    "empty_levels": (200, BOOK_EMPTY_LEVELS),
    "additive": (200, BOOK_ADDITIVE),
    "bad_timestamp": (200, BOOK_BAD_TIMESTAMP_FLOAT),
    "bool_timestamp": (200, BOOK_BAD_TIMESTAMP_BOOL),
    "str_timestamp": (200, BOOK_BAD_TIMESTAMP_STR),
    "missing_bids": (200, BOOK_MISSING_BIDS),
    "missing_asks": (200, BOOK_MISSING_ASKS),
    "bad_level": (200, BOOK_BAD_LEVEL_ONE_ELEMENT),
    "drift": (200, BOOK_DRIFT),
    "invalid_instrument": (400, ERROR_INVALID_INSTRUMENT),
    "rate_limit": (429, ERROR_RATE_LIMIT),
    "provider_error": (500, HTTP_500_BODY),
}
