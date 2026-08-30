"""Synthetic Kraken Market Analytics fixture matrix (SENSOR-B3-I05).

Each payload is a **SYNTHETIC_SCHEMA_FIXTURE** reconstructed to match the
committed Bloc 2 schema fingerprint for its sensor (09_SCHEMA_FINGERPRINTS.jsonl):

- open-interest   data: list[list[str]]  (bucket value arrays parallel to ts)
- funding         data: dict{rate, relativeRate}   (each a list, parallel to ts)
- basis           data: dict{basis}                (list parallel to ts)
- positioning     data: list[str]                  (parallel to ts)
- liquidation     data: list[str]                  (parallel to ts)
- book_metric     data: dict{ask: {...}, bid: {...}} (per-side metric lists)

Empty-valid shapes reproduce the observed empty fingerprints verbatim where
available (e.g. open_interest 2022 `data:[]`, funding 2021/2024
`data:{rate:[],relativeRate:[]}`).  These are offline test inputs only.
"""

from __future__ import annotations

from typing import Any

# Every fixture is synthetic; this tag is surfaced in the manifest.
FIXTURE_LABEL = "SYNTHETIC_SCHEMA_FIXTURE"

#: HTTP status + body pairs per scenario.  Keys: happy/empty/error/drift/continue.
SCENARIOS: dict[str, tuple[int, Any]] = {}


def _register(scenario: str, body: Any, status: int = 200) -> None:
    SCENARIOS.setdefault(scenario, []).append((status, body))


# --- shared provider error envelope (symbol not found) ---------------------
ERROR_SYMBOL = {
    "errors": [{"msg": "symbol not found", "error_class": "UnknownError"}],
    "result": {},
}

# --- open-interest (data: list[list[str]]) --------------------------------
_open_interest_happy = {
    "errors": [],
    "result": {
        "timestamp": [1755000000, 1755003600],
        "data": [["725.3"], ["726.0"]],
        "more": False,
    },
}
_open_interest_empty = {
    "errors": [],
    "result": {"data": [], "more": False, "timestamp": []},
}
_open_interest_drift = {
    "errors": [],
    "result": {"data": {"unexpected": 1}, "more": False, "timestamp": []},
}
_open_interest_continue = {
    "errors": [],
    "result": {
        "timestamp": [1754870400, 1754874000],
        "data": [["700.1"], ["701.0"]],
        "more": True,
    },
}

# --- funding (data: dict{rate, relativeRate}) -----------------------------
# Bucket timestamps are EPOCH SECONDS: the committed Bloc 2 probe fixture
# (funding_analytics_success.json) and the live probe contract both use
# seconds; the I13R1 fingerprint (09_SCHEMA_FINGERPRINTS.jsonl) pins the
# timestamp type as int only.  No milliseconds claim is manufactured here.
_funding_happy = {
    "errors": [],
    "result": {
        "timestamp": [1755000000],
        "data": {"rate": [["0.0001"]], "relativeRate": [["0.0001"]]},
        "more": False,
    },
}
_funding_empty = {
    "errors": [],
    "result": {
        "data": {"rate": [], "relativeRate": []},
        "more": False,
        "timestamp": [],
    },
}
_funding_drift = {
    "errors": [],
    "result": {"data": {"otherMetric": []}, "more": False, "timestamp": []},
}

# --- basis (data: dict{basis}) -------------------------------------------
_basis_happy = {
    "errors": [],
    "result": {
        "timestamp": [1755000000],
        "data": {"basis": ["0.001"]},
        "more": False,
    },
}
_basis_empty = {
    "errors": [],
    "result": {"data": {"basis": []}, "more": False, "timestamp": []},
}
_basis_drift = {
    "errors": [],
    "result": {"data": {"notBasis": []}, "more": False, "timestamp": []},
}

# --- positioning / liquidation (data: list[str]) --------------------------
_positioning_happy = {
    "errors": [],
    "result": {"timestamp": [1755000000], "data": ["1.245"], "more": False},
}
_positioning_empty = {
    "errors": [],
    "result": {"data": [], "more": False, "timestamp": []},
}
_positioning_drift = {
    "errors": [],
    "result": {"data": 7, "more": False, "timestamp": []},
}
_liquidation_happy = {
    "errors": [],
    "result": {"timestamp": [1755000000], "data": ["150000.0"], "more": False},
}
_liquidation_empty = {
    "errors": [],
    "result": {"data": [], "more": False, "timestamp": []},
}
_liquidation_drift = {
    "errors": [],
    "result": {"data": None, "more": False, "timestamp": []},
}

# --- book_metric (data: dict{ask: {...}, bid: {...}}) ----------------------
_BOOK_SIDE = {
    "bestPrice": ["1000.0"],
    "liquidity005": ["0.1"],
    "liquidity01": ["0.2"],
    "liquidity025": ["0.3"],
    "liquidity05": ["0.4"],
    "liquidity10": ["0.5"],
    "liquidity100": ["0.6"],
    "slippage100k": ["0.003"],
    "slippage10k": ["0.002"],
    "slippage1k": ["0.001"],
    "slippage1m": [None],
}
_book_metric_happy = {
    "errors": [],
    "result": {
        "timestamp": [1755000000],
        "data": {"ask": _BOOK_SIDE, "bid": _BOOK_SIDE},
        "more": False,
    },
}
_BOOK_EMPTY_SIDE = {k: [] for k in _BOOK_SIDE}
_book_metric_empty = {
    "errors": [],
    "result": {
        "data": {"ask": _BOOK_EMPTY_SIDE, "bid": _BOOK_EMPTY_SIDE},
        "more": False,
        "timestamp": [],
    },
}
_book_metric_drift = {
    "errors": [],
    "result": {"data": {"ask": {}}, "more": False, "timestamp": []},
}
_book_metric_continue = {
    "errors": [],
    "result": {
        "timestamp": [1754870400],
        "data": {"ask": _BOOK_SIDE, "bid": _BOOK_SIDE},
        "more": True,
    },
}

SCENARIOS["open_interest"] = [
    (200, _open_interest_happy),
    (200, _open_interest_empty),
    (200, ERROR_SYMBOL),
    (200, _open_interest_drift),
    (200, _open_interest_continue),
]
SCENARIOS["funding"] = [
    (200, _funding_happy),
    (200, _funding_empty),
    (200, ERROR_SYMBOL),
    (200, _funding_drift),
]
SCENARIOS["basis"] = [
    (200, _basis_happy),
    (200, _basis_empty),
    (200, ERROR_SYMBOL),
    (200, _basis_drift),
]
SCENARIOS["positioning"] = [
    (200, _positioning_happy),
    (200, _positioning_empty),
    (200, ERROR_SYMBOL),
    (200, _positioning_drift),
]
SCENARIOS["liquidation"] = [
    (200, _liquidation_happy),
    (200, _liquidation_empty),
    (200, ERROR_SYMBOL),
    (200, _liquidation_drift),
]
SCENARIOS["book_metric"] = [
    (200, _book_metric_happy),
    (200, _book_metric_empty),
    (200, ERROR_SYMBOL),
    (200, _book_metric_drift),
    (200, _book_metric_continue),
]

#: scenario index -> (status, body) by name for convenient construction.
HAPPY = {k: v[0] for k, v in SCENARIOS.items()}
EMPTY = {k: v[1] for k, v in SCENARIOS.items()}
ERROR = {k: v[2] for k, v in SCENARIOS.items()}
DRIFT = {k: v[3] for k, v in SCENARIOS.items()}
CONTINUE = {k: v[4] for k, v in SCENARIOS.items() if len(v) > 4}