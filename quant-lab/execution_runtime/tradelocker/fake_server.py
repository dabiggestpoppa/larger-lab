"""QL-EXEC-R5 — FakeTradeLocker: deterministic in-memory TradeLocker provider.

Implements the ``HttpTransport`` protocol (same injection pattern as
``brokers/fake_mt5.py``) so the whole provider stack is testable with ZERO
network. Provides the full read surface and a write surface whose semantics
match official TradeLocker truth:

- JWT auth + refresh (+ expiry control)
- ``/auth/jwt/all-accounts`` (accountId vs accNum kept distinct)
- ``/trade/config`` (dynamic columns, limits, rateLimits)
- instrument discovery with INFO/TRADE routes
- orders / ordersHistory / positions / executions / account state
- quotes (INFO route) + price history
- place order: market → IOC → immediate Filled + position; limit/stop → GTC
  pending order
- close position: places a closing order; optional deferred-close mode where
  the position persists until confirmed (close request != closed truth)
- failure injection: auth fail, token expiry, 429 + Retry-After, malformed
  JSON, 5xx, rejections, partial fills, before-send / ambiguous timeouts,
  missing positions, duplicate legs

Row payloads use the value-array format aligned to ``/config`` columns, exactly
like the real API.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.parse
from typing import Optional

from .transport import (
    AmbiguousSendError,
    HttpRequest,
    HttpResponse,
    TimeoutBeforeSendError,
)

# ─── canonical /config column ids (fake truth; real provider is dynamic) ──
COLUMNS = {
    "ordersConfig": [
        "id", "tradableInstrumentId", "side", "qty", "type", "validity",
        "status", "positionId", "price", "stopPrice", "strategyId", "serverTime",
    ],
    "ordersHistoryConfig": [
        "id", "tradableInstrumentId", "side", "qty", "type", "validity",
        "status", "positionId", "price", "stopPrice", "strategyId", "serverTime",
    ],
    "filledOrdersConfig": [
        "id", "orderId", "tradableInstrumentId", "side", "qty", "price",
        "strategyId", "positionId", "serverTime",
    ],
    "executionsConfig": [
        "id", "orderId", "tradableInstrumentId", "side", "qty", "price",
        "strategyId", "positionId", "serverTime",
    ],
    "positionsConfig": [
        "id", "tradableInstrumentId", "side", "qty", "price", "currentPrice",
        "strategyId", "serverTime", "pnl", "stopLossId", "takeProfitId",
    ],
    "accountDetailsConfig": [
        "balance", "equity", "margin", "freeMargin", "currency", "mode", "buyingPower",
    ],
    "instrumentsConfig": [
        "id", "name", "tradableInstrumentId", "routes", "pricePrecision",
        "contractSize", "volumeMin", "volumeMax", "volumeStep",
    ],
    "priceHistoryConfig": ["t", "o", "h", "l", "c", "v"],
}
_LIMITS = [{"limitType": "QUOTES_HISTORY_BARS", "limit": 100000}]
_RATE_LIMITS = [
    {"rateLimitType": "QUOTES_HISTORY", "limit": 10, "seconds": 60},
    {"rateLimitType": "GET_CONFIG", "limit": 100, "seconds": 60},
    {"rateLimitType": "GET_ORDERS", "limit": 60, "seconds": 60},
    {"rateLimitType": "GET_POSITIONS", "limit": 60, "seconds": 60},
    {"rateLimitType": "PLACE_ORDER", "limit": 30, "seconds": 60},
    {"rateLimitType": "CLOSE_POSITION", "limit": 30, "seconds": 60},
]
CONFIG_D = {
    # Real /config payload: each object name sits at the top of ``d`` with its
    # own ``columns`` list (e.g. ``d.ordersConfig.columns``).
    k: {"columns": [{"id": c} for c in v]} for k, v in COLUMNS.items()
}
CONFIG_D["limits"] = _LIMITS
CONFIG_D["rateLimits"] = _RATE_LIMITS


def _row(values: list, columns: list) -> list:
    return values


class FakeTradeLocker:
    """In-memory TradeLocker provider behind the transport protocol."""

    def __init__(self, *, base_url: str = "https://demo.tradelocker.com/backend-api") -> None:
        self.base_url = base_url.rstrip("/")
        self.reset()

    # ── setup ─────────────────────────────────────────────────────────────

    def reset(self) -> None:
        self._access_token = ""
        self._refresh_token = ""
        self._token_seq = 1
        self._access_ttl_seconds: float = 3600.0  # TTL of issued access tokens
        self._force_expired = False
        self._request_count = 0
        self._refresh_calls = 0
        self._accounts = [
            {"id": 101, "accNum": 1000001, "name": "Demo USD 1", "server": "demo-server"},
            {"id": 102, "accNum": 1000002, "name": "Demo USD 2", "server": "demo-server"},
        ]
        self._credentials = {"email": "user@example.com", "password": "s3cret", "server": "demo-server"}
        self._auth_enabled = True
        self._refresh_enabled = True

        self._instruments: dict[int, list] = {}
        self._orders: dict[int, dict] = {}  # account_id -> {oid: row}
        self._positions: dict[int, dict] = {}
        self._executions: dict[int, list] = {}
        self._next_id = 5000

        self._account_state: dict[int, list] = {}
        for acc in self._accounts:
            self._seed_account(acc["id"], acc["accNum"])

        self._quotes: dict[int, dict] = {}
        self._history: dict[int, list] = {}

        # failure injection
        self._fail_auth = False
        self._fail_refresh = False
        self._reject_next_order = False
        self._reject_next_close = False
        self._partial_fill_next = 0.0
        self._defer_close = False
        self._pending_closes: set = set()
        self._timeout_mode: Optional[str] = None  # None | before_send | ambiguous
        self._malformed_json = False
        self._status_5xx = False
        self._status_403 = False
        self._rate_limit_enabled = False
        self._rate_hits: dict[str, list] = {}
        self._fixed_server_time_ms: Optional[int] = None
        self._missing_position = False

    def _seed_account(self, account_id: int, acc_num: int) -> None:
        self._orders[account_id] = {}
        self._positions[account_id] = {}
        self._executions[account_id] = []
        self._account_state[account_id] = [
            10000.0, 10000.0, 0.0, 10000.0, "USD", "demo", 10000.0,
        ]

    def add_instrument(
        self,
        account_id: int,
        *,
        name: str,
        symbol_id: int,
        info_route: str = "a",
        trade_route: str = "b",
        price_precision: int = 5,
        contract_size: float = 100000.0,
        volume_min: float = 0.01,
        volume_max: float = 100.0,
        volume_step: float = 0.01,
    ) -> int:
        self._next_id += 1
        tradable_id = self._next_id
        row = {
            "id": symbol_id,
            "name": name,
            "tradableInstrumentId": tradable_id,
            "routes": [
                {"id": info_route, "type": "INFO"},
                {"id": trade_route, "type": "TRADE"},
            ],
            "pricePrecision": price_precision,
            "contractSize": contract_size,
            "volumeMin": volume_min,
            "volumeMax": volume_max,
            "volumeStep": volume_step,
        }
        self._instruments.setdefault(account_id, []).append(row)
        self._quotes.setdefault(tradable_id, {
            "bp": 1.10000, "ap": 1.10005, "serverTime": self._now_ms(),
        })
        return tradable_id

    def set_quote(self, instrument_id: int, bid: float, ask: float) -> None:
        self._quotes[instrument_id] = {
            "bp": bid, "ap": ask, "serverTime": self._now_ms(),
        }

    def set_history(self, instrument_id: int, rows: list) -> None:
        self._history[instrument_id] = list(rows)

    def set_access_ttl(self, seconds: Optional[float]) -> None:
        self._access_ttl_seconds = float(seconds) if seconds is not None else 3600.0

    def expire_access_token(self) -> None:
        """Force the CURRENT access token to be rejected (401) and re-issue it
        with an already-expired exp claim so the client's local JWT expiry
        check also triggers a refresh."""
        self._force_expired = True
        self._access_token = self._make_jwt("access", -60.0)

    def set_credentials(self, email: str, password: str, server: str) -> None:
        self._credentials = {"email": email, "password": password, "server": server}

    def set_auth_enabled(self, enabled: bool) -> None:
        self._auth_enabled = enabled

    def set_refresh_enabled(self, enabled: bool) -> None:
        self._refresh_enabled = enabled

    def set_timeout_mode(self, mode: Optional[str]) -> None:
        self._timeout_mode = mode

    def set_malformed_json(self, flag: bool) -> None:
        self._malformed_json = flag

    def set_status_5xx(self, flag: bool) -> None:
        self._status_5xx = flag

    def set_status_403(self, flag: bool) -> None:
        self._status_403 = flag

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def refresh_calls(self) -> int:
        return self._refresh_calls

    def set_rate_limit_enabled(self, flag: bool) -> None:
        self._rate_limit_enabled = flag

    def set_defer_close(self, flag: bool) -> None:
        self._defer_close = flag

    def resolve_pending_closes(self) -> None:
        """Apply deferred closes (position truth catches up)."""
        for pid in list(self._pending_closes):
            for acc, pos in self._positions.items():
                if pid in pos:
                    del pos[pid]
            self._pending_closes.discard(pid)

    def set_missing_position(self, flag: bool) -> None:
        self._missing_position = flag

    def set_reject_next_order(self) -> None:
        self._reject_next_order = True

    def set_reject_next_close(self) -> None:
        self._reject_next_close = True

    def set_partial_fill_next(self, ratio: float) -> None:
        self._partial_fill_next = ratio

    def set_fixed_server_time_ms(self, ms: Optional[int]) -> None:
        self._fixed_server_time_ms = ms

    def set_account_state(self, account_id: int, values: list) -> None:
        self._account_state[account_id] = list(values)

    # ── inspection helpers (test assertions) ─────────────────────────────

    def open_positions(self, account_id: int) -> list:
        return list(self._positions.get(account_id, {}).values())

    def open_orders(self, account_id: int) -> list:
        return [o for o in self._orders.get(account_id, {}).values() if o["status"] != "Filled"]

    def all_orders(self, account_id: int) -> list:
        return list(self._orders.get(account_id, {}).values())

    def executions(self, account_id: int) -> list:
        return list(self._executions.get(account_id, []))

    def instrument_ids(self, account_id: int) -> dict:
        return {
            row["name"]: row["tradableInstrumentId"]
            for row in self._instruments.get(account_id, [])
        }

    def seed_foreign_position(
        self, account_id: int, *, symbol: str = "GBPUSD", qty: float = 1.0,
        side: str = "buy", strategy_id: str = "FOREIGN",
    ) -> int:
        self._next_id += 1
        pid = self._next_id
        inst = next(
            (r for r in self._instruments.get(account_id, []) if r["name"] == symbol), None
        )
        tid = inst["tradableInstrumentId"] if inst else 0
        self._positions[account_id][pid] = {
            "id": pid, "tradableInstrumentId": tid, "side": side, "qty": qty,
            "price": 1.00000, "currentPrice": 1.00005, "strategyId": strategy_id,
            "serverTime": self._now_ms(), "pnl": 0.0, "stopLossId": 0, "takeProfitId": 0,
        }
        return pid

    # ── transport protocol ────────────────────────────────────────────────

    def request(self, request: HttpRequest) -> HttpResponse:
        self._request_count += 1
        if self._timeout_mode == "before_send":
            raise TimeoutBeforeSendError("fake connect timeout")
        if self._timeout_mode == "ambiguous":
            raise AmbiguousSendError("fake read timeout after send")
        if self._status_5xx:
            return self._resp(500, {"s": "error", "desc": "internal"})
        if self._status_403:
            return self._resp(403, {"s": "error", "desc": "forbidden"})
        if self._malformed_json:
            return HttpResponse(status=200, body="not-json{{{")

        method = request.method.upper()
        path = urllib.parse.urlsplit(request.url).path
        base_path = urllib.parse.urlsplit(self.base_url).path
        if base_path and path.startswith(base_path):
            path = path[len(base_path):] or "/"
        params = dict(request.params or {})
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)
        for k, v in query.items():
            params.setdefault(k, v[0])
        body = request.json_body or {}

        if self._rate_limit_enabled:
            route = self._route_for(method, path)
            if route and not self._rate_ok(route):
                return HttpResponse(
                    status=429,
                    headers={"Retry-After": "1"},
                    body=json.dumps({"s": "error", "desc": "rate limited"}),
                )

        try:
            return self._dispatch(method, path, params, body, request.headers)
        except _FakeAuthRejected:
            return HttpResponse(
                status=401,
                body=json.dumps({"s": "error", "desc": "token expired"}),
            )

    # ── internals ─────────────────────────────────────────────────────────

    def _now_ms(self) -> int:
        if self._fixed_server_time_ms is not None:
            return self._fixed_server_time_ms
        return int(time.time() * 1000.0)

    def _resp(self, status: int, payload: dict) -> HttpResponse:
        return HttpResponse(status=status, body=json.dumps(payload))

    def _ok(self, d=None) -> HttpResponse:
        return self._resp(200, {"s": "ok", "d": d or {}})

    def _err(self, desc: str, status: int = 400) -> HttpResponse:
        return self._resp(status, {"s": "error", "desc": desc})

    def _route_for(self, method: str, path: str) -> Optional[str]:
        if path == "/auth/jwt/token":
            return None
        if path == "/auth/jwt/refresh":
            return None
        if path == "/auth/jwt/all-accounts":
            return None
        if path == "/trade/config":
            return "GET_CONFIG"
        if path == "/trade/accounts":
            return "GET_ACCOUNTS"
        if path.endswith("/state"):
            return "GET_ACCOUNT_STATE"
        if path.endswith("/instruments"):
            return "GET_INSTRUMENTS"
        if path == "/trade/quotes":
            return "QUOTES"
        if path == "/trade/history":
            return "QUOTES_HISTORY"
        if path == "/trade/accounts" and method == "GET":
            return "GET_ACCOUNTS"
        if "/executions" in path:
            return "GET_EXECUTIONS"
        if "/positions" in path:
            if method == "DELETE":
                return "CLOSE_POSITION"
            return "GET_POSITIONS"
        if "/orders" in path:
            if method == "POST":
                return "PLACE_ORDER"
            if method == "DELETE":
                return "DELETE_ORDER"
            if path.endswith("History"):
                return "GET_ORDERS_HISTORY"
            return "GET_ORDERS"
        return None

    def _rate_ok(self, route: str) -> bool:
        window = 60.0
        now = time.time()
        hits = [h for h in self._rate_hits.get(route, []) if h > now - window]
        limit = next(
            (r["limit"] for r in _RATE_LIMITS if r["rateLimitType"] == route), 10
        )
        if len(hits) >= limit:
            return False
        self._rate_hits.setdefault(route, []).append(now)
        return True

    def _dispatch(self, method: str, path: str, params: dict, body: dict, headers: dict) -> HttpResponse:
        # auth routes
        if path == "/auth/jwt/token" and method == "POST":
            return self._auth_token(body)
        if path == "/auth/jwt/refresh" and method == "POST":
            return self._auth_refresh(body)
        if path == "/auth/jwt/all-accounts" and method == "GET":
            self._require_auth(headers)
            # Real API returns accounts at the TOP level (not under d).
            return self._resp(200, {"s": "ok", "accounts": self._accounts})

        # everything below needs auth
        self._require_auth(headers)

        if path == "/trade/config" and method == "GET":
            return self._ok(CONFIG_D)
        if path == "/trade/accounts" and method == "GET":
            acc = self._account_for_headers(headers)
            return self._ok(dict(acc))

        parts = [p for p in path.split("/") if p]
        # /trade/accounts/{id}/...
        if len(parts) >= 4 and parts[0] == "trade" and parts[1] == "accounts":
            try:
                account_id = int(parts[2])
            except ValueError:
                return self._err("bad account id", 404)
            rest = parts[3:]
            if rest == ["state"] and method == "GET":
                return self._ok({"accountDetailsData": self._account_state.get(account_id, [])})
            if rest == ["instruments"] and method == "GET":
                return self._ok({"instruments": self._instruments.get(account_id, [])})
            if rest == ["positions"] and method == "GET":
                return self._ok({"positions": list(self._positions.get(account_id, {}).values())})
            if rest == ["positions"] and method == "DELETE":
                return self._close_all(account_id, params)
            if rest == ["executions"] and method == "GET":
                return self._ok({"executions": self._executions.get(account_id, [])})
            if rest == ["orders"] and method == "GET":
                return self._ok({"orders": self._nonfinal_rows(account_id)})
            if rest == ["ordersHistory"] and method == "GET":
                return self._ok({"ordersHistory": self._history_rows(account_id)})
            if rest == ["orders"] and method == "POST":
                return self._place_order(account_id, body)
            if rest == ["orders"] and method == "DELETE":
                self._orders[account_id] = {}
                return self._ok({})
            if len(rest) == 2 and rest[0] == "orders" and method == "DELETE":
                try:
                    oid = int(rest[1])
                except ValueError:
                    return self._err("bad order id", 404)
                if oid not in self._orders.get(account_id, {}):
                    return self._err("order not found", 404)
                del self._orders[account_id][oid]
                return self._ok({})
            return self._err("unknown account route", 404)

        # /trade/positions/{positionId}
        if len(parts) == 3 and parts[0] == "trade" and parts[1] == "positions" and method == "DELETE":
            try:
                pid = int(parts[2])
            except ValueError:
                return self._err("bad position id", 404)
            return self._close_position(pid, body)

        # market data (INFO route)
        if path == "/trade/quotes" and method == "GET":
            return self._quotes_endpoint(params)
        if path == "/trade/history" and method == "GET":
            return self._history_endpoint(params)
        return self._err("unknown route", 404)

    # ── auth handlers ─────────────────────────────────────────────────────

    def _issue_tokens(self) -> dict:
        """Issue a fresh JWT-shaped token pair with a decodable exp claim."""
        self._token_seq += 1
        self._force_expired = False
        self._access_token = self._make_jwt("access", self._access_ttl_seconds)
        self._refresh_token = self._make_jwt("refresh", 86400.0)
        # Real API returns tokens at the TOP level (not under d).
        return {
            "s": "ok",
            "accessToken": self._access_token,
            "refreshToken": self._refresh_token,
        }

    @staticmethod
    def _make_jwt(kind: str, ttl_seconds: float) -> str:
        def _b64(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).decode().rstrip("=")

        header = _b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
        payload = _b64(
            json.dumps({
                "exp": int(time.time() + ttl_seconds),
                "sub": f"fake-user|fake-server",
                "kind": kind,
            }).encode()
        )
        return f"{header}.{payload}.fake-signature"

    def _auth_token(self, body: dict) -> HttpResponse:
        if not self._auth_enabled:
            return self._err("auth disabled", 401)
        if (
            body.get("email") != self._credentials["email"]
            or body.get("password") != self._credentials["password"]
            or body.get("server") != self._credentials["server"]
        ):
            return self._err("invalid credentials", 401)
        return self._resp(200, self._issue_tokens())

    def _auth_refresh(self, body: dict) -> HttpResponse:
        self._refresh_calls += 1
        if not self._refresh_enabled:
            return self._err("refresh disabled", 401)
        if body.get("refreshToken") != self._refresh_token:
            return self._err("invalid refresh token", 401)
        return self._resp(200, self._issue_tokens())

    def _require_auth(self, headers: dict) -> None:
        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise _FakeAuthRejected()
        token = auth[len("Bearer "):]
        if token != self._access_token:
            raise _FakeAuthRejected()
        if self._force_expired:
            raise _FakeAuthRejected()

    def _account_for_headers(self, headers: dict) -> dict:
        acc_num = headers.get("accNum")
        for acc in self._accounts:
            if str(acc["accNum"]) == str(acc_num):
                return acc
        return self._accounts[0]

    # ── order / position handlers ─────────────────────────────────────────

    def _place_order(self, account_id: int, body: dict) -> HttpResponse:
        try:
            qty = float(body.get("qty"))
        except (TypeError, ValueError):
            return self._err("bad qty")
        side = body.get("side")
        otype = body.get("type")
        validity = body.get("validity")
        tid = int(body.get("tradableInstrumentId") or 0)
        route_id = body.get("routeId")
        strategy_id = str(body.get("strategyId") or "")

        instruments = self._instruments.get(account_id, [])
        inst = next((r for r in instruments if r["tradableInstrumentId"] == tid), None)
        if inst is None:
            return self._err("unknown tradableInstrumentId", 404)
        trade_routes = [r["id"] for r in inst["routes"] if r["type"] == "TRADE"]
        if route_id not in trade_routes:
            return self._err("invalid TRADE routeId")
        if qty <= 0:
            return self._err("qty must be positive")
        if side not in ("buy", "sell"):
            return self._err("bad side")
        if otype not in ("market", "limit", "stop"):
            return self._err("bad type")
        if (otype == "market" and validity != "IOC") or (otype != "market" and validity != "GTC"):
            return self._err(f"invalid validity {validity} for type {otype}")
        if len(strategy_id) > 32:
            return self._err("strategyId too long")

        if self._reject_next_order:
            self._reject_next_order = False
            return self._err("order rejected by provider")

        self._next_id += 1
        oid = self._next_id
        row = {
            "id": oid,
            "tradableInstrumentId": tid,
            "side": side,
            "qty": qty,
            "type": otype,
            "validity": validity,
            "status": "Pending",
            "positionId": 0,
            "price": body.get("price") or 0.0,
            "stopPrice": body.get("stopPrice") or 0.0,
            "strategyId": strategy_id,
            "serverTime": self._now_ms(),
        }

        if otype == "market":
            self._fill_order(account_id, oid, row)
        else:
            self._orders[account_id][oid] = row
        return self._ok({"orderId": oid})

    def _fill_order(self, account_id: int, oid: int, row: dict) -> None:
        ratio = self._partial_fill_next
        self._partial_fill_next = 0.0
        filled = round(row["qty"] * ratio, 6) if ratio else row["qty"]
        row["status"] = "Filled"
        self._orders[account_id][oid] = row

        self._next_id += 1
        pid = self._next_id
        quote = self._quotes.get(row["tradableInstrumentId"], {"bp": 1.0, "ap": 1.0})
        price = quote["ap"] if row["side"] == "buy" else quote["bp"]
        self._positions[account_id][pid] = {
            "id": pid,
            "tradableInstrumentId": row["tradableInstrumentId"],
            "side": row["side"],
            "qty": filled,
            "price": price,
            "currentPrice": price,
            "strategyId": row["strategyId"],
            "serverTime": self._now_ms(),
            "pnl": 0.0,
            "stopLossId": 0,
            "takeProfitId": 0,
        }
        row["positionId"] = pid
        self._next_id += 1
        ex_id = self._next_id
        self._executions[account_id].append({
            "id": ex_id,
            "orderId": oid,
            "tradableInstrumentId": row["tradableInstrumentId"],
            "side": row["side"],
            "qty": filled,
            "price": price,
            "strategyId": row["strategyId"],
            "positionId": pid,
            "serverTime": self._now_ms(),
        })

    def _close_all(self, account_id: int, params: dict) -> HttpResponse:
        tid_filter = params.get("tradableInstrumentId")
        for pid in list(self._positions.get(account_id, {})):
            pos = self._positions[account_id][pid]
            if tid_filter and str(pos["tradableInstrumentId"]) != str(tid_filter):
                continue
            self._close_position(pid, {"qty": "0"})
        return self._ok({})

    def _close_position(self, pid: int, body: dict) -> HttpResponse:
        if self._reject_next_close:
            self._reject_next_close = False
            return self._err("close rejected by provider")
        if self._missing_position:
            return self._err("position not found", 404)
        for account_id, positions in self._positions.items():
            pos = positions.get(pid)
            if pos is None:
                continue
            try:
                close_qty = float(body.get("qty", "0"))
            except (TypeError, ValueError):
                return self._err("bad qty")
            remaining = pos["qty"]
            qty_to_close = remaining if close_qty <= 0 else min(close_qty, remaining)

            self._next_id += 1
            close_oid = self._next_id
            opp_side = "sell" if pos["side"] == "buy" else "buy"
            self._orders[account_id][close_oid] = {
                "id": close_oid,
                "tradableInstrumentId": pos["tradableInstrumentId"],
                "side": opp_side,
                "qty": qty_to_close,
                "type": "market",
                "validity": "IOC",
                "status": "Filled",
                "positionId": pid,
                "price": pos["currentPrice"] or pos["price"],
                "stopPrice": 0.0,
                "strategyId": pos["strategyId"],
                "serverTime": self._now_ms(),
            }
            if self._defer_close:
                # closing ORDER placed (IOC→GTC) but position persists until
                # the provider confirms (close request != closed truth).
                self._pending_closes.add(pid)
                return self._ok({})
            new_qty = round(remaining - qty_to_close, 6)
            if new_qty <= 1e-9:
                del positions[pid]
            else:
                pos["qty"] = new_qty
            self._next_id += 1
            self._executions[account_id].append({
                "id": self._next_id,
                "orderId": close_oid,
                "tradableInstrumentId": pos["tradableInstrumentId"],
                "side": opp_side,
                "qty": -qty_to_close,
                "price": pos["currentPrice"] or pos["price"],
                "strategyId": pos["strategyId"],
                "positionId": pid,
                "serverTime": self._now_ms(),
            })
            return self._ok({})
        return self._err("position not found", 404)

    def _nonfinal_rows(self, account_id: int) -> list:
        return [
            list(o.values())
            for o in self._orders.get(account_id, {}).values()
            if o["status"] != "Filled"
        ]

    def _history_rows(self, account_id: int) -> list:
        return [list(o.values()) for o in self._orders.get(account_id, {}).values()]

    # ── market data ───────────────────────────────────────────────────────

    def _quotes_endpoint(self, params: dict) -> HttpResponse:
        try:
            tid = int(params.get("tradableInstrumentId"))
        except (TypeError, ValueError):
            return self._err("bad tradableInstrumentId")
        if tid not in self._quotes:
            return self._err("no quote", 404)
        q = dict(self._quotes[tid])
        q["serverTime"] = self._now_ms()
        return self._ok(q)

    def _history_endpoint(self, params: dict) -> HttpResponse:
        try:
            tid = int(params.get("tradableInstrumentId"))
        except (TypeError, ValueError):
            return self._err("bad tradableInstrumentId")
        if tid not in self._history:
            return self._ok({"barDetails": []})
        return self._ok({"barDetails": [list(b) for b in self._history[tid]]})


class _FakeAuthRejected(Exception):
    pass
