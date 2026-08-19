"""QL-EXEC-R5 — TradeLocker REST client (provider-native, transport-injected).

Policy truth:

- 401 → refresh token once → retry once. A 401 means the request was NOT
  executed by the provider, so one retry is safe.
- 429 → honor ``Retry-After`` with a bounded number of attempts (max 3 total),
  then raise ``TradeLockerRateLimitExceeded``. Never infinite retry.
- Transport failures on READ requests → one bounded backoff retry.
- Transport failures on WRITE requests (POST/DELETE order paths) → NEVER
  retried: the send may have reached the provider. Raise/propagate and let the
  caller reconcile broker truth first (duplicate-order protection).

Column mappings are resolved by id from the ``/config`` snapshot — never
hardcoded indexes. Provider-native fields (``accountId``, ``accNum``,
``tradableInstrumentId``, ``routeId``) pass through untouched.
"""
from __future__ import annotations

import time
from typing import Optional

from .auth import TradeLockerAuthProvider
from .config import TradeLockerConfigParser
from .ratelimit import TradeLockerRateLimiter
from .transport import (
    AmbiguousSendError,
    HttpRequest,
    HttpTransport,
    HttpResponse,
    TimeoutBeforeSendError,
    TransportError,
)
from .types import (
    TradeLockerAccount,
    TradeLockerConfigSnapshot,
    TradeLockerInstrument,
    TradeLockerQuote,
    TradeLockerRateLimit,
    TradeLockerRoute,
)

# Route names used as rate-limiter keys (mirror /config rateLimits names).
R_GET_CONFIG = "GET_CONFIG"
R_GET_ACCOUNTS = "GET_ACCOUNTS"
R_GET_INSTRUMENTS = "GET_INSTRUMENTS"
R_GET_ORDERS = "GET_ORDERS"
R_GET_ORDERS_HISTORY = "GET_ORDERS_HISTORY"
R_GET_POSITIONS = "GET_POSITIONS"
R_GET_EXECUTIONS = "GET_EXECUTIONS"
R_GET_ACCOUNT_STATE = "GET_ACCOUNT_STATE"
R_PLACE_ORDER = "PLACE_ORDER"
R_DELETE_ORDER = "DELETE_ORDER"
R_CLOSE_POSITION = "CLOSE_POSITION"
R_QUOTES = "QUOTES"
R_QUOTES_HISTORY = "QUOTES_HISTORY"

_MAX_ATTEMPTS = 3  # bounded retry budget (429 / read-transport retries)
_MAX_RETRY_AFTER_SECONDS = 30.0
_WRITE_METHODS = {"POST", "DELETE", "PATCH", "PUT"}


class TradeLockerApiError(Exception):
    """Provider-level API error (HTTP status / malformed response / drift)."""

    def __init__(self, message: str, *, status: Optional[int] = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class TradeLockerRateLimitExceeded(TradeLockerApiError):
    """Bounded rate-limit retries exhausted."""


class TradeLockerClient:
    def __init__(
        self,
        *,
        auth: TradeLockerAuthProvider,
        transport: HttpTransport,
        rate_limiter: Optional[TradeLockerRateLimiter] = None,
        acc_num: Optional[int] = None,
        clock=None,
    ) -> None:
        self._auth = auth
        self._transport = transport
        self._rate_limiter = rate_limiter or TradeLockerRateLimiter()
        self._acc_num = acc_num
        self._clock = clock or time.time
        self._config: Optional[TradeLockerConfigSnapshot] = None
        self._config_parser = TradeLockerConfigParser()

    # ── auth helpers (thin, public) ──────────────────────────────────────

    def authenticated(self) -> bool:
        return self._auth.tokens_present()

    def authenticate(self) -> None:
        self._auth.authenticate()

    def token_expiry_seconds(self):
        return self._auth.access_token_expiry_seconds()

    def refresh_count(self) -> int:
        return self._auth.refresh_count()

    # ── config ────────────────────────────────────────────────────────────

    def get_config(self, force: bool = False) -> TradeLockerConfigSnapshot:
        if self._config is not None and not force:
            return self._config
        resp = self._request("GET", "/trade/config", route=R_GET_CONFIG)
        payload = self._expect_ok(resp, R_GET_CONFIG)
        d = payload.get("d") if isinstance(payload, dict) else None
        if not isinstance(d, dict):
            raise TradeLockerApiError("config payload missing 'd'", status=resp.status)
        self._config = self._config_parser.parse(d)
        self._rate_limiter.update_from_config(self._config.rate_limits)
        return self._config

    @property
    def config_snapshot(self) -> Optional[TradeLockerConfigSnapshot]:
        return self._config

    # ── discovery ─────────────────────────────────────────────────────────

    def get_all_accounts(self) -> list:
        return self._auth.get_all_accounts()

    def get_instruments(self, account_id: int) -> list:
        resp = self._request(
            "GET", f"/trade/accounts/{account_id}/instruments", route=R_GET_INSTRUMENTS
        )
        payload = self._expect_ok(resp, R_GET_INSTRUMENTS)
        d = payload.get("d") or {}
        rows = d.get("instruments") or []
        out = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            routes = tuple(
                TradeLockerRoute(route_id=str(r.get("id")), route_type=str(r.get("type", "")))
                for r in (row.get("routes") or [])
                if isinstance(r, dict) and r.get("id") is not None
            )
            out.append(
                TradeLockerInstrument(
                    tradable_instrument_id=int(row["tradableInstrumentId"]),
                    name=str(row.get("name", "")),
                    symbol_id=int(row.get("id", 0) or 0),
                    routes=routes,
                    raw=dict(row),
                )
            )
        return out

    def get_trade_accounts(self) -> dict:
        """``/trade/accounts`` detail for the session's accNum."""
        resp = self._request("GET", "/trade/accounts", route=R_GET_ACCOUNTS)
        payload = self._expect_ok(resp, R_GET_ACCOUNTS)
        d = payload.get("d") or {}
        return dict(d)

    # ── state / positions / orders / fills ────────────────────────────────

    def get_account_state(self, account_id: int) -> dict:
        resp = self._request(
            "GET", f"/trade/accounts/{account_id}/state", route=R_GET_ACCOUNT_STATE
        )
        payload = self._expect_ok(resp, R_GET_ACCOUNT_STATE)
        d = payload.get("d") or {}
        values = d.get("accountDetailsData")
        if isinstance(values, list):
            columns = self.get_config().columns.get("accountDetailsConfig", ())
            return dict(zip(columns, values))
        return dict(values or {})

    def get_positions(self, account_id: int) -> list:
        resp = self._request(
            "GET", f"/trade/accounts/{account_id}/positions", route=R_GET_POSITIONS
        )
        payload = self._expect_ok(resp, R_GET_POSITIONS)
        d = payload.get("d") or {}
        rows = d.get("positions") or []
        columns = self.get_config().columns.get("positionsConfig", ())
        return self._resolve_rows(rows, columns)

    def get_orders(self, account_id: int, history: bool = False) -> list:
        endpoint = "ordersHistory" if history else "orders"
        route = R_GET_ORDERS_HISTORY if history else R_GET_ORDERS
        resp = self._request(
            "GET", f"/trade/accounts/{account_id}/{endpoint}", route=route
        )
        payload = self._expect_ok(resp, route)
        d = payload.get("d") or {}
        rows = d.get(endpoint) or []
        columns = self.get_config().columns.get(endpoint + "Config", ())
        return self._resolve_rows(rows, columns)

    def get_executions(self, account_id: int) -> list:
        resp = self._request(
            "GET", f"/trade/accounts/{account_id}/executions", route=R_GET_EXECUTIONS
        )
        payload = self._expect_ok(resp, R_GET_EXECUTIONS)
        d = payload.get("d") or {}
        rows = d.get("executions") or []
        columns = self.get_config().columns.get("filledOrdersConfig", ())
        return self._resolve_rows(rows, columns)

    # ── writes ────────────────────────────────────────────────────────────

    def place_order(
        self,
        *,
        account_id: int,
        instrument_id: int,
        qty: float,
        side: str,
        order_type: str,
        validity: str,
        route_id: str,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        strategy_id: Optional[str] = None,
        stop_loss: Optional[float] = None,
        stop_loss_type: Optional[str] = None,
        take_profit: Optional[float] = None,
        take_profit_type: Optional[str] = None,
    ) -> int:
        body = {
            "price": price,
            "qty": str(qty),
            "routeId": str(route_id),
            "side": side,
            "validity": validity,
            "tradableInstrumentId": str(instrument_id),
            "type": order_type,
            "stopPrice": stop_price,
            "strategyId": strategy_id,
            "stopLoss": stop_loss,
            "stopLossType": stop_loss_type,
            "takeProfit": take_profit,
            "takeProfitType": take_profit_type,
        }
        resp = self._request(
            "POST",
            f"/trade/accounts/{account_id}/orders",
            route=R_PLACE_ORDER,
            json_body=body,
            write=True,
        )
        payload = self._expect_ok(resp, R_PLACE_ORDER)
        d = payload.get("d") or {}
        order_id = d.get("orderId")
        if order_id is None:
            raise TradeLockerApiError("place_order response missing d.orderId", status=resp.status)
        return int(order_id)

    def cancel_order(self, account_id: int, order_id: int) -> bool:
        resp = self._request(
            "DELETE",
            f"/trade/accounts/{account_id}/orders/{order_id}",
            route=R_DELETE_ORDER,
            write=True,
        )
        payload = self._expect_ok(resp, R_DELETE_ORDER)
        return payload.get("s") == "ok"

    def delete_all_orders(self, account_id: int) -> bool:
        resp = self._request(
            "DELETE",
            f"/trade/accounts/{account_id}/orders",
            route=R_DELETE_ORDER,
            write=True,
        )
        payload = self._expect_ok(resp, R_DELETE_ORDER)
        return payload.get("s") == "ok"

    def close_position(self, position_id: int, qty: float = 0.0) -> bool:
        """Place a closing order for a position. ``qty=0`` closes fully.

        IMPORTANT: a successful response means the closing ORDER was placed
        (IOC then GTC), NOT that the position is gone. Confirm via
        ``get_positions`` truth.
        """
        resp = self._request(
            "DELETE",
            f"/trade/positions/{position_id}",
            route=R_CLOSE_POSITION,
            json_body={"qty": str(qty)},
            write=True,
        )
        payload = self._expect_ok(resp, R_CLOSE_POSITION)
        return payload.get("s") == "ok"

    def close_all_positions(self, account_id: int, instrument_id: Optional[int] = None) -> bool:
        params = {}
        if instrument_id is not None:
            params["tradableInstrumentId"] = str(instrument_id)
        resp = self._request(
            "DELETE",
            f"/trade/accounts/{account_id}/positions",
            route=R_CLOSE_POSITION,
            params=params,
            write=True,
        )
        payload = self._expect_ok(resp, R_CLOSE_POSITION)
        return payload.get("s") == "ok"

    # ── market data (INFO route) ──────────────────────────────────────────

    def get_quotes(self, instrument_id: int, route_id: str) -> TradeLockerQuote:
        resp = self._request(
            "GET",
            "/trade/quotes",
            route=R_QUOTES,
            params={"tradableInstrumentId": instrument_id, "routeId": route_id},
        )
        payload = self._expect_ok(resp, R_QUOTES)
        d = payload.get("d") or {}
        try:
            bid = float(d.get("bp", 0.0))
            ask = float(d.get("ap", 0.0))
        except (TypeError, ValueError) as err:
            raise TradeLockerApiError(f"malformed quote: {err}", status=resp.status) from err
        return TradeLockerQuote(
            instrument_id=instrument_id,
            bid=bid,
            ask=ask,
            server_time_ms=int(d.get("serverTime", 0) or 0),
            raw=dict(d),
        )

    def get_price_history(
        self,
        instrument_id: int,
        route_id: str,
        resolution: str,
        from_ms: int,
        to_ms: int,
    ) -> list:
        resp = self._request(
            "GET",
            "/trade/history",
            route=R_QUOTES_HISTORY,
            params={
                "tradableInstrumentId": instrument_id,
                "routeId": route_id,
                "resolution": resolution,
                "from": from_ms,
                "to": to_ms,
            },
        )
        payload = self._expect_ok(resp, R_QUOTES_HISTORY)
        d = payload.get("d") or {}
        bars = d.get("barDetails") or []
        out = []
        for row in bars:
            if not isinstance(row, (list, dict)):
                continue
            if isinstance(row, list):
                cols = ("t", "o", "h", "l", "c", "v")
                row = dict(zip(cols, row))
            out.append(dict(row))
        return out

    # ── internals ─────────────────────────────────────────────────────────

    def _resolve_rows(self, rows: list, columns: tuple) -> list:
        """Rows arrive as value-arrays aligned to /config columns, or dicts."""
        out = []
        for row in rows:
            if isinstance(row, dict):
                out.append(dict(row))
            elif isinstance(row, (list, tuple)):
                out.append(dict(zip(columns, row)))
        return out

    def _expect_ok(self, resp: HttpResponse, route: str) -> dict:
        if resp.status != 200:
            raise TradeLockerApiError(
                f"{route}: HTTP {resp.status}", status=resp.status, body=resp.body
            )
        try:
            payload = resp.json()
        except ValueError as err:
            raise TradeLockerApiError(f"{route}: {err}", status=resp.status, body=resp.body) from err
        if payload.get("s") not in (None, "ok"):
            raise TradeLockerApiError(
                f"{route}: provider error: {payload.get('s')} {payload.get('desc', '')}",
                status=resp.status,
                body=resp.body,
            )
        return payload

    def _headers(self, include_acc_num: bool = True) -> dict:
        headers = {"Authorization": f"Bearer {self._auth.get_access_token()}"}
        if include_acc_num and self._acc_num is not None:
            headers["accNum"] = str(self._acc_num)
        dev_key = self._auth.developer_api_key()
        if dev_key:
            headers["developer-api-key"] = dev_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        route: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
        write: bool = False,
    ) -> HttpResponse:
        url = f"{self._auth.base_url}{path}"
        attempts = 0
        while True:
            attempts += 1
            wait = self._rate_limiter.wait_seconds(route)
            if wait > 0:
                if attempts >= _MAX_ATTEMPTS:
                    raise TradeLockerRateLimitExceeded(
                        f"{route}: rate limit not cleared after {_MAX_ATTEMPTS} waits",
                        status=429,
                    )
                time.sleep(min(wait, _MAX_RETRY_AFTER_SECONDS))
            req = HttpRequest(
                method=method,
                url=url,
                headers=self._headers(),
                params=params or {},
                json_body=json_body,
            )
            try:
                resp = self._transport.request(req)
            except AmbiguousSendError as err:
                if write:
                    # The request MAY have reached the provider. Do not retry.
                    self._rate_limiter.note_failure(route)
                    raise err
                self._rate_limiter.note_failure(route)
                if attempts >= _MAX_ATTEMPTS:
                    raise err
                continue
            except TimeoutBeforeSendError as err:
                self._rate_limiter.note_failure(route)
                if write:
                    raise err  # nothing reached provider, but stay conservative
                if attempts >= _MAX_ATTEMPTS:
                    raise err
                continue
            except TransportError as err:
                self._rate_limiter.note_failure(route)
                if write:
                    raise err
                if attempts >= _MAX_ATTEMPTS:
                    raise err
                continue

            self._rate_limiter.reset_failure(route)
            self._rate_limiter.consume(route)

            if resp.status == 401:
                # Not executed by provider → refresh once and retry once.
                # force=True: the SERVER rejected the token, which is the only
                # authoritative expiry signal (local JWT exp may look valid).
                if attempts >= _MAX_ATTEMPTS:
                    raise TradeLockerApiError(
                        f"{route}: auth rejected after retries", status=401, body=resp.body
                    )
                self._auth.refresh_access_token(force=True)
                continue
            if resp.status == 429:
                retry_after = _parse_retry_after(resp.headers)
                if retry_after:
                    self._rate_limiter.note_retry_after(route, retry_after)
                if attempts >= _MAX_ATTEMPTS:
                    raise TradeLockerRateLimitExceeded(
                        f"{route}: rate limited after {_MAX_ATTEMPTS} attempts",
                        status=429,
                        body=resp.body,
                    )
                continue
            return resp


def _parse_retry_after(headers: dict) -> Optional[float]:
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(float(raw), 0.0)
    except (TypeError, ValueError):
        return None
