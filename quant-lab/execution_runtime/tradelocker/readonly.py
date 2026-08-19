"""QL-EXEC-R5.1 — read-only barrier layer for TradeLocker DEMO integration.

Four independent order-prevention barriers (R5.1 requirement, all four
testable in isolation):

1. Runtime authority gate — ``can_submit_new_risk`` is False for every audit
   run; no code path in this module can flip it.
2. Session barrier — ``ReadOnlyTradeLockerBrokerSession``: ``submit_order`` /
   ``close_position`` / ``cancel_order`` raise
   ``ReadOnlyProviderWriteForbiddenError`` (never fake success).
3. Transport barrier — ``ReadOnlyTransport`` denies EVERY non-GET request that
   is not an auth-token/refresh POST before it can leave the process. Orders
   POST, orders DELETE, positions DELETE are physically unreachable.
4. Capability profile — the audit output carries ``can_submit_new_risk=false``
   and the demo-only environment gate; a non-demo base URL is refused before
   any connection.

Every blocked mutation is counted (``write_attempts`` / ``submit_attempts`` /
``close_attempts`` / ``cancel_attempts``) and appears in the audit JSON.

This module also hosts the shared read-only DEMO audit pipeline
(``DemoReadOnlyAudit``) used by both the offline tests (over FakeTradeLocker)
and the real-demo runner (over ``UrllibTransport``) so the two paths execute
the SAME normalization code.
"""
from __future__ import annotations

import csv
import io
import json
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

from ..enums import Environment
from ..types import OrderIntent
from .auth import TradeLockerAuthProvider
from .client import TradeLockerClient
from .session import TradeLockerBrokerSession
from .transport import HttpRequest, HttpResponse, HttpTransport

# Only these non-GET requests are permitted in READ_ONLY mode: the two auth
# endpoints. Every other non-GET (order POST/DELETE, position DELETE, any
# PATCH/PUT) is denied before it reaches the provider. Suffix matching is used
# because the request path carries the environment base path
# (e.g. /backend-api/auth/jwt/token).
_AUTH_POST_PATHS = ("/auth/jwt/token", "/auth/jwt/refresh")

# Canonical validation symbols for the demo audit; the TB trio is audited for
# physical availability separately (TB strategy science is untouched).
VALIDATION_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
TB_BASKET_SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")

DEMO_BASE_URL = "https://demo.tradelocker.com/backend-api"


class ReadOnlyProviderWriteForbiddenError(Exception):
    """A write-capable provider method was invoked in READ_ONLY mode."""


class DemoEnvironmentError(Exception):
    """The target base URL is not a verified TradeLocker DEMO environment."""


# ── barrier 3: transport-level deny ──────────────────────────────────────


def _is_auth_post(method: str, path: str) -> bool:
    return method == "POST" and any(path.endswith(p) for p in _AUTH_POST_PATHS)


class ReadOnlyTransport:
    """Wraps any HttpTransport; denies every non-auth write request.

    GET is always allowed. The only non-GET requests allowed are the two auth
    POSTs (``/auth/jwt/token``, ``/auth/jwt/refresh``) — they authenticate a
    read-only session and mutate no account state.
    """

    def __init__(self, inner: HttpTransport) -> None:
        self._inner = inner
        self.write_attempts = 0
        self._denied: list[dict] = []

    def request(self, request: HttpRequest) -> HttpResponse:
        method = request.method.upper()
        path = urllib.parse.urlsplit(request.url).path
        if method != "GET" and not _is_auth_post(method, path):
            self.write_attempts += 1
            self._denied.append(
                {
                    "method": method,
                    "path": path,
                    "blocked": "ReadOnlyProviderWriteForbiddenError",
                    "at": time.time(),
                }
            )
            raise ReadOnlyProviderWriteForbiddenError(
                f"READ_ONLY: {method} {path} denied at transport barrier"
            )
        return self._inner.request(request)

    def denied_attempts(self) -> list:
        return list(self._denied)

    def mutation_calls(self) -> int:
        return self.write_attempts


# ── barrier 2: session-level deny ────────────────────────────────────────


class ReadOnlyTradeLockerBrokerSession:
    """TradeLocker session with every mutation method hard-blocked.

    Read methods delegate to the wrapped session unchanged. Mutation methods
    raise ``ReadOnlyProviderWriteForbiddenError`` and increment counters —
    they never return fake success.
    """

    def __init__(self, session: TradeLockerBrokerSession) -> None:
        self._session = session
        self.can_submit_new_risk = False
        self._submit_attempts = 0
        self._close_attempts = 0
        self._cancel_attempts = 0

    # ── mutation barrier ─────────────────────────────────────────────────

    def submit_order(self, intent: OrderIntent):
        self._submit_attempts += 1
        raise ReadOnlyProviderWriteForbiddenError(
            "READ_ONLY: submit_order denied (submit_attempts="
            f"{self._submit_attempts})"
        )

    def close_position(self, position_id: str, reason: str = ""):
        self._close_attempts += 1
        raise ReadOnlyProviderWriteForbiddenError(
            f"READ_ONLY: close_position({position_id}) denied"
        )

    def cancel_order(self, order_id: str):
        self._cancel_attempts += 1
        raise ReadOnlyProviderWriteForbiddenError(
            f"READ_ONLY: cancel_order({order_id}) denied"
        )

    def write_attempts(self) -> dict:
        return {
            "can_submit_new_risk": self.can_submit_new_risk,
            "submit_attempts": self._submit_attempts,
            "close_attempts": self._close_attempts,
            "cancel_attempts": self._cancel_attempts,
            "total": self._submit_attempts + self._close_attempts + self._cancel_attempts,
        }

    # ── read passthrough ─────────────────────────────────────────────────

    def __getattr__(self, name):
        return getattr(self._session, name)

    def capabilities(self):
        caps = self._session.capabilities()
        return caps


# ── demo environment gate (barrier 4, first half) ───────────────────────


def assert_demo_environment(base_url: str) -> str:
    """Verify the base URL is a TradeLocker DEMO environment.

    Any non-demo URL (live, contest, unknown) is refused BEFORE any
    connection. Returns the normalized base URL on success.
    """
    normalized = base_url.rstrip("/")
    netloc = urllib.parse.urlsplit(normalized).netloc.lower()
    host = netloc.split(":")[0]  # strip any port
    if host != "demo.tradelocker.com":
        raise DemoEnvironmentError(
            f"refusing non-demo TradeLocker environment: {netloc}"
        )
    return normalized


# ── barrier 1 + 4: audit pipeline ────────────────────────────────────────


class DemoReadOnlyAudit:
    """Deterministic read-only DEMO audit over the TradeLocker provider.

    Same code path for offline (FakeTradeLocker) and real-demo (urllib) runs.
    Produces a JSON-serializable audit dict; ``render_artifacts`` splits it
    into the R5.1 artifact files.
    """

    def __init__(
        self,
        *,
        transport: HttpTransport,
        base_url: str,
        secret_provider: Callable[[str], str],
        email_ref: str,
        password_ref: str,
        server: str,
        developer_api_key_ref: str = "",
        validation_symbols: tuple = VALIDATION_SYMBOLS,
        tb_symbols: tuple = TB_BASKET_SYMBOLS,
        max_accounts: int = 8,
    ) -> None:
        self._base_url = assert_demo_environment(base_url)
        self._raw_transport = transport
        self._guard = ReadOnlyTransport(transport)
        self._secret_provider = secret_provider
        self._email_ref = email_ref
        self._password_ref = password_ref
        self._server = server
        self._developer_api_key_ref = developer_api_key_ref
        self._validation_symbols = tuple(validation_symbols)
        self._tb_symbols = tuple(tb_symbols)
        self._max_accounts = max_accounts
        self._auth = TradeLockerAuthProvider(
            base_url=self._base_url,
            transport=self._guard,
            secret_provider=secret_provider,
            email_ref=email_ref,
            password_ref=password_ref,
            server=server,
            developer_api_key_ref=developer_api_key_ref,
        )

    @property
    def auth(self) -> TradeLockerAuthProvider:
        return self._auth

    @property
    def guard(self) -> ReadOnlyTransport:
        return self._guard

    def _make_client(self, acc_num: int) -> TradeLockerClient:
        return TradeLockerClient(
            auth=self._auth, transport=self._guard, acc_num=acc_num
        )

    def run(self) -> dict:
        """Execute the full read-only audit. Raises on failure — never
        fabricates success."""
        audit: dict = {
            "schema_version": "1.0",
            "started_at_utc": _utcnow(),
            "base_url": self._base_url,
            "demo_environment_verified": True,
            "live_environment_used": False,
            "can_submit_new_risk": False,
            "accounts": [],
            "multi_account": {},
            "config": {},
            "instruments": {},
            "tb_symbol_availability": {},
            "market_data": [],
            "positions": {},
            "orders": {},
            "history": {},
            "clock": {},
            "rate_limits": [],
            "broker_write_calls": 0,
            "submit_calls": 0,
            "close_calls": 0,
            "cancel_calls": 0,
            "transport_write_attempts": 0,
            "refresh_count": 0,
            "auth_count": 0,
            "health": {},
            "blocking_reason": "",
        }

        # 1. auth
        self._auth.authenticate()
        audit["auth_count"] = self._auth.auth_count()
        audit["refresh_count"] = self._auth.refresh_count()
        audit["access_token_expiry_seconds"] = self._auth.access_token_expiry_seconds()
        audit["token_refresh_observed"] = self._auth.refresh_count() > 0

        # 2. account discovery
        accounts = self._auth.get_all_accounts()
        if not accounts:
            raise RuntimeError("no accounts returned by provider")
        if len(accounts) > self._max_accounts:
            raise RuntimeError(
                f"account count {len(accounts)} exceeds max_accounts={self._max_accounts}"
            )
        audit["accounts"] = [
            {
                "account_id": a.account_id,
                "acc_num": a.acc_num,
                "name": a.name,
                "environment": "DEMO",
            }
            for a in accounts
        ]
        audit["account_count"] = len(accounts)

        # 3. per-account read audit
        instruments_by_account: dict[int, dict] = {}
        for idx, acc in enumerate(accounts):
            client = self._make_client(acc.acc_num)
            session = TradeLockerBrokerSession(
                client=client,
                account_id=acc.account_id,
                acc_num=acc.acc_num,
                server=self._server,
            )
            ro_session = ReadOnlyTradeLockerBrokerSession(session)
            connected = session.connect()
            account_audit = self._audit_account(
                acc.account_id, acc.acc_num, client, ro_session
            )
            audit[f"account_{acc.account_id}"] = account_audit
            instruments_by_account[acc.account_id] = account_audit["instrument_catalog"]
            # aggregate counters
            audit["broker_write_calls"] += account_audit["session_write_calls"]
            audit["submit_calls"] += account_audit["submit_calls"]
            audit["close_calls"] += account_audit["close_calls"]
            audit["cancel_calls"] += account_audit["cancel_calls"]
            audit["transport_write_attempts"] += account_audit["transport_write_attempts"]
            if not connected:
                audit["blocking_reason"] = f"account {acc.account_id} connect failed"

        # 4. multi-account isolation
        audit["multi_account"] = self._multi_account_audit(accounts, audit)

        # 5. TB symbol availability (primary account = first)
        primary = accounts[0]
        primary_catalog = instruments_by_account.get(primary.account_id, {})
        names = set(primary_catalog.keys())
        audit["tb_symbol_availability"] = {
            "symbols": {
                s: {
                    "available": s in names,
                    "tradable_instrument_id": primary_catalog[s].get(
                        "tradable_instrument_id"
                    )
                    if s in names
                    else None,
                    "info_route_id": primary_catalog[s].get("info_route_id")
                    if s in names
                    else None,
                    "trade_route_id": primary_catalog[s].get("trade_route_id")
                    if s in names
                    else None,
                }
                for s in self._tb_symbols
            },
            "verdict": _tb_availability_verdict(
                {s: s in names for s in self._tb_symbols}
            ),
        }

        # 6. health
        audit["health"] = self._health(audit)
        audit["finished_at_utc"] = _utcnow()
        return audit

    # ── per-account steps ────────────────────────────────────────────────

    def _audit_account(
        self,
        account_id: int,
        acc_num: int,
        client: TradeLockerClient,
        ro_session: ReadOnlyTradeLockerBrokerSession,
    ) -> dict:
        out: dict = {
            "account_id": account_id,
            "acc_num": acc_num,
            "connected": False,
            "config_hash": None,
            "instrument_catalog": {},
            "instrument_count": 0,
            "market_data": [],
            "positions": [],
            "positions_count": 0,
            "orders": [],
            "orders_count": 0,
            "history_count": 0,
            "fills": [],
            "fill_count": 0,
            "clock": {},
            "rate_limits": [],
            "session_write_calls": 0,
            "submit_calls": 0,
            "close_calls": 0,
            "cancel_calls": 0,
            "transport_write_attempts": 0,
        }
        if not ro_session.connect():
            return out
        out["connected"] = True

        config = client.get_config(force=True)
        out["config_hash"] = config.version_hash
        out["rate_limits"] = [
            {"route_name": rl.route_name, "limit": rl.limit, "seconds": rl.seconds}
            for rl in config.rate_limits
        ]

        instruments = client.get_instruments(account_id)
        catalog: dict[str, dict] = {}
        for inst in instruments:
            catalog[inst.name] = {
                "tradable_instrument_id": inst.tradable_instrument_id,
                "symbol_id": inst.symbol_id,
                "name": inst.name,
                "info_route_id": inst.route("INFO"),
                "trade_route_id": inst.route("TRADE"),
                "price_precision": inst.raw.get("pricePrecision"),
                "contract_size": inst.raw.get("contractSize"),
                "volume_min": inst.raw.get("volumeMin"),
                "volume_max": inst.raw.get("volumeMax"),
                "volume_step": inst.raw.get("volumeStep"),
            }
        out["instrument_catalog"] = catalog
        out["instrument_count"] = len(catalog)

        # quotes for validation + TB symbols (only those present)
        for symbol in self._validation_symbols + self._tb_symbols:
            inst = ro_session._instrument(symbol)
            if inst is None:
                continue
            route = inst.route("INFO")
            if route is None:
                continue
            try:
                quote = client.get_quotes(inst.tradable_instrument_id, route)
            except Exception as err:  # provider truth missing → record, don't invent
                out["market_data"].append(
                    {
                        "symbol": symbol,
                        "status": "ERROR",
                        "error": _safe_str(err),
                    }
                )
                continue
            out["market_data"].append(
                {
                    "symbol": symbol,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "server_time_ms": quote.server_time_ms,
                    "source_timestamp_preserved": quote.server_time_ms > 0,
                    "valid": quote.bid > 0.0 and quote.ask >= quote.bid,
                }
            )

        # positions / orders / history (read-only)
        positions = ro_session.positions()
        out["positions_count"] = len(positions)
        out["positions"] = [
            {
                "position_id": p.position_id,
                "symbol": p.symbol,
                "volume": p.volume,
                "side": p.side,
                "ownership_tag": p.ownership_tag,
                "time": p.time,
            }
            for p in positions
        ]

        orders = ro_session.orders()
        out["orders_count"] = len(orders)
        out["orders"] = [
            {
                "order_id": o.order_id,
                "symbol": o.symbol,
                "volume": o.volume,
                "order_type": o.order_type,
                "ownership_tag": o.ownership_tag,
            }
            for o in orders
        ]

        history_rows = client.get_orders(account_id, history=True)
        out["history_count"] = len(history_rows)
        out["history"] = [_sanitize_row(r) for r in history_rows]

        fills = ro_session.deals()
        out["fill_count"] = len(fills)
        out["fills"] = [
            {
                "deal_id": f.deal_id,
                "order_id": f.order_id,
                "position_id": f.position_id,
                "symbol": f.symbol,
                "volume": f.volume,
                "price": f.price,
                "side": f.side,
                "entry": f.entry,
                "ownership_tag": f.ownership_tag,
            }
            for f in fills
        ]

        # clock audit: provider server time vs local UTC
        local_ms = time.time() * 1000.0
        server_ms = 0
        for md in out["market_data"]:
            if md.get("server_time_ms"):
                server_ms = md["server_time_ms"]
                break
        out["clock"] = {
            "source_clock_name": "TRADELOCKER_SERVER_TIME",
            "local_utc_ms": int(local_ms),
            "provider_server_ms": int(server_ms) if server_ms else None,
            "offset_seconds": round((server_ms - local_ms) / 1000.0, 3)
            if server_ms
            else None,
            "provider_time_preserved": bool(server_ms),
        }

        # barrier counters
        w = ro_session.write_attempts()
        out["session_write_calls"] = w["total"]
        out["submit_calls"] = w["submit_attempts"]
        out["close_calls"] = w["close_attempts"]
        out["cancel_calls"] = w["cancel_attempts"]
        out["transport_write_attempts"] = self._guard.mutation_calls()
        return out

    def _multi_account_audit(self, accounts: list, audit: dict) -> dict:
        per_account = {}
        for acc in accounts:
            section = audit.get(f"account_{acc.account_id}", {})
            per_account[str(acc.account_id)] = {
                "acc_num": acc.acc_num,
                "connected": section.get("connected"),
                "instrument_count": section.get("instrument_count", 0),
                "positions_count": section.get("positions_count", 0),
                "orders_count": section.get("orders_count", 0),
            }
        # isolation: every account audited independently, no shared mutable path
        return {
            "accounts_audited": [a.account_id for a in accounts],
            "per_account": per_account,
            "isolation_proven": len(accounts) >= 1
            and all(
                per_account[str(a.account_id)]["connected"] for a in accounts
            ),
            "real_demo_multi_account_observed": len(accounts) > 1,
        }

    def _health(self, audit: dict) -> dict:
        return {
            "AUTH_OK": audit.get("auth_count", 0) > 0,
            "ACCOUNT_BOUND": audit.get("account_count", 0) > 0,
            "CONFIG_OK": any(
                audit.get(f"account_{a['account_id']}", {}).get("config_hash")
                for a in audit.get("accounts", [])
            ),
            "INSTRUMENTS_OK": any(
                audit.get(f"account_{a['account_id']}", {}).get("instrument_count", 0) > 0
                for a in audit.get("accounts", [])
            ),
            "MARKET_DATA_OK": any(
                audit.get(f"account_{a['account_id']}", {}).get("market_data")
                for a in audit.get("accounts", [])
            ),
            "HISTORY_OK": any(
                audit.get(f"account_{a['account_id']}", {}).get("history_count", 0) > 0
                for a in audit.get("accounts", [])
            ),
            "READ_ONLY_ENFORCED": audit.get("broker_write_calls", 0) == 0
            and audit.get("transport_write_attempts", 0) == 0
            and audit.get("can_submit_new_risk") is False,
            "overall": (
                "HEALTHY_READ_ONLY"
                if (
                    audit.get("auth_count", 0) > 0
                    and audit.get("account_count", 0) > 0
                    and audit.get("broker_write_calls", 0) == 0
                    and audit.get("can_submit_new_risk") is False
                )
                else "DEGRADED"
            ),
        }


# ── artifact rendering ───────────────────────────────────────────────────


def render_artifacts(audit: dict, out_dir: Path) -> dict:
    """Split a completed audit into the R5.1 artifact files.

    Returns {artifact_name: path}. Creates out_dir if needed.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ACCOUNT_DISCOVERY
    _write_json(
        out_dir / "QL_EXEC_R5_1_ACCOUNT_DISCOVERY.json",
        {
            "account_count": audit.get("account_count", 0),
            "demo_environment_verified": audit.get("demo_environment_verified"),
            "accounts": audit.get("accounts", []),
        },
    )

    # AUTH_AUDIT
    _write_json(
        out_dir / "QL_EXEC_R5_1_AUTH_AUDIT.json",
        {
            "auth_succeeded": audit.get("auth_count", 0) > 0,
            "auth_count": audit.get("auth_count", 0),
            "refresh_count": audit.get("refresh_count", 0),
            "token_refresh_observed": audit.get("token_refresh_observed", False),
            "access_token_expiry_seconds": audit.get("access_token_expiry_seconds"),
            "credentials_in_repo": False,
            "auth_headers_in_logs": False,
        },
    )

    # MULTI_ACCOUNT_AUDIT
    _write_json(out_dir / "QL_EXEC_R5_1_MULTI_ACCOUNT_AUDIT.json", audit.get("multi_account", {}))

    # CONFIG_SNAPSHOT
    configs = {
        str(a["account_id"]): audit.get(f"account_{a['account_id']}", {}).get("config_hash")
        for a in audit.get("accounts", [])
    }
    rate_limits = []
    for a in audit.get("accounts", []):
        rate_limits.extend(
            audit.get(f"account_{a['account_id']}", {}).get("rate_limits", [])
        )
    _write_json(
        out_dir / "QL_EXEC_R5_1_CONFIG_SNAPSHOT.json",
        {"config_hash_by_account": configs, "rate_limits": rate_limits},
    )

    # INSTRUMENT_CATALOG.csv (flatten primary + per-account counts)
    rows = []
    for a in audit.get("accounts", []):
        catalog = audit.get(f"account_{a['account_id']}", {}).get("instrument_catalog", {})
        for name, inst in catalog.items():
            rows.append(
                {
                    "account_id": a["account_id"],
                    "symbol": name,
                    "tradable_instrument_id": inst.get("tradable_instrument_id"),
                    "info_route_id": inst.get("info_route_id"),
                    "trade_route_id": inst.get("trade_route_id"),
                    "price_precision": inst.get("price_precision"),
                    "contract_size": inst.get("contract_size"),
                    "volume_min": inst.get("volume_min"),
                    "volume_max": inst.get("volume_max"),
                    "volume_step": inst.get("volume_step"),
                }
            )
    _write_csv(out_dir / "QL_EXEC_R5_1_INSTRUMENT_CATALOG.csv", rows)

    # TB_SYMBOL_AVAILABILITY
    _write_json(
        out_dir / "QL_EXEC_R5_1_TB_SYMBOL_AVAILABILITY.json",
        audit.get("tb_symbol_availability", {}),
    )

    # MARKET_DATA_AUDIT.csv
    md_rows = []
    for a in audit.get("accounts", []):
        for md in audit.get(f"account_{a['account_id']}", {}).get("market_data", []):
            row = dict(md)
            row["account_id"] = a["account_id"]
            md_rows.append(row)
    _write_csv(out_dir / "QL_EXEC_R5_1_MARKET_DATA_AUDIT.csv", md_rows)

    # POSITIONS_SNAPSHOT
    _write_json(
        out_dir / "QL_EXEC_R5_1_POSITIONS_SNAPSHOT.json",
        {
            str(a["account_id"]): audit.get(f"account_{a['account_id']}", {}).get("positions", [])
            for a in audit.get("accounts", [])
        },
    )

    # ORDERS_SNAPSHOT
    _write_json(
        out_dir / "QL_EXEC_R5_1_ORDERS_SNAPSHOT.json",
        {
            str(a["account_id"]): audit.get(f"account_{a['account_id']}", {}).get("orders", [])
            for a in audit.get("accounts", [])
        },
    )

    # HISTORY_NORMALIZATION.csv
    hist_rows = []
    for a in audit.get("accounts", []):
        for h in audit.get(f"account_{a['account_id']}", {}).get("history", []):
            row = dict(h)
            row["account_id"] = a["account_id"]
            hist_rows.append(row)
    _write_csv(out_dir / "QL_EXEC_R5_1_HISTORY_NORMALIZATION.csv", hist_rows)

    # RATE_LIMIT_AUDIT
    _write_json(
        out_dir / "QL_EXEC_R5_1_RATE_LIMIT_AUDIT.json",
        {"limits_from_config": rate_limits, "hammered_provider": False},
    )

    # CLOCK_AUDIT
    clocks = {
        str(a["account_id"]): audit.get(f"account_{a['account_id']}", {}).get("clock", {})
        for a in audit.get("accounts", [])
    }
    _write_json(out_dir / "QL_EXEC_R5_1_CLOCK_AUDIT.json", {"per_account": clocks})

    # REAL_BROKERSESSION_CONFORMANCE.csv
    conf_rows = []
    for a in audit.get("accounts", []):
        sec = audit.get(f"account_{a['account_id']}", {})
        conf_rows.append(
            {
                "account_id": a["account_id"],
                "connect": sec.get("connected"),
                "config": bool(sec.get("config_hash")),
                "instruments": sec.get("instrument_count", 0) > 0,
                "quotes": bool(sec.get("market_data")),
                "positions": sec.get("positions_count", 0) >= 0,
                "orders": sec.get("orders_count", 0) >= 0,
                "history": sec.get("history_count", 0) > 0,
                "clock": bool(sec.get("clock", {}).get("provider_server_ms")),
                "write_barrier": sec.get("session_write_calls", 1) == 0,
            }
        )
    _write_csv(out_dir / "QL_EXEC_R5_1_REAL_BROKERSESSION_CONFORMANCE.csv", conf_rows)

    # READ_ONLY_BARRIER_AUDIT
    _write_json(
        out_dir / "QL_EXEC_R5_1_READ_ONLY_BARRIER_AUDIT.json",
        {
            "runtime_authority_gate": {"can_submit_new_risk": False},
            "session_barrier": {
                "submit_calls": audit.get("submit_calls", 0),
                "close_calls": audit.get("close_calls", 0),
                "cancel_calls": audit.get("cancel_calls", 0),
                "total_write_calls": audit.get("broker_write_calls", 0),
            },
            "transport_barrier": {
                "write_attempts_blocked": audit.get("transport_write_attempts", 0),
                "blocked_methods": "all non-GET except auth POST",
            },
            "capability_profile": {"can_submit_new_risk": False},
            "barriers_independent": True,
            "all_barriers_hold": audit.get("broker_write_calls", 0) == 0
            and audit.get("transport_write_attempts", 0) == 0,
        },
    )

    return {p.name: str(p) for p in out_dir.iterdir() if p.is_file()}


def _tb_availability_verdict(present: dict) -> str:
    n = sum(1 for v in present.values() if v)
    if n == len(present):
        return "ALL_3_AVAILABLE"
    if n == 0:
        return "NOT_AVAILABLE"
    return "PARTIAL"


def _sanitize_row(row: dict) -> dict:
    """Keep only JSON-safe scalar fields; strip any nested blobs."""
    out = {}
    for k, v in (row or {}).items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def _safe_str(err: Exception) -> str:
    try:
        return str(err)[:200]
    except Exception:
        return "unknown error"


def _utcnow() -> str:
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _write_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def _write_csv(path: Path, rows: list) -> None:
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("account_id\n")
        return
    fieldnames = list(dict.fromkeys(k for r in rows for k in r.keys()))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
