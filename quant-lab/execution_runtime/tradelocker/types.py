"""QL-EXEC-R5 — provider-native TradeLocker value objects.

These types live BELOW the generic BrokerSession boundary. The generic
``types.py`` objects are what crosses the adapter; these preserve
provider-native truth (``accountId`` vs ``accNum``, ``tradableInstrumentId``,
route ids, dynamic config columns) for the adapter to translate.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TradeLockerTokens:
    """JWT token pair. Values live only in memory of the auth provider."""

    access_token: str
    refresh_token: str
    expires_in: int = 0  # seconds until access token expiry, if the API says


@dataclass(frozen=True)
class TradeLockerAccount:
    """One account row from ``/auth/jwt/all-accounts``.

    ``account_id`` (``id``) and ``acc_num`` (``accNum``) are DIFFERENT
    provider-native identities and are never collapsed into one integer.
    """

    account_id: int
    acc_num: int
    name: str = ""
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TradeLockerRoute:
    """A route id bound to an instrument. INFO = market data, TRADE = execution."""

    route_id: str
    route_type: str  # "INFO" | "TRADE"


@dataclass(frozen=True)
class TradeLockerInstrument:
    """Normalized instrument discovery row (provider-native fields preserved)."""

    tradable_instrument_id: int
    name: str = ""
    symbol_id: int = 0
    routes: tuple = ()  # tuple[TradeLockerRoute, ...]
    raw: dict = field(default_factory=dict)

    def route(self, route_type: str) -> str | None:
        for r in self.routes:
            if r.route_type == route_type:
                return r.route_id
        return None


@dataclass(frozen=True)
class TradeLockerQuote:
    """Quote snapshot from the INFO route (``/trade/quotes``)."""

    instrument_id: int
    bid: float = 0.0
    ask: float = 0.0
    server_time_ms: int = 0  # provider/server timestamp truth, ms epoch
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TradeLockerRateLimit:
    """One entry from ``/config`` ``rateLimits`` (provider truth)."""

    route_name: str
    limit: int = 0
    seconds: int = 60


@dataclass(frozen=True)
class TradeLockerConfigSnapshot:
    """Versioned/hashed snapshot of ``/trade/config``.

    Column ids are DYNAMIC provider truth — the adapter resolves field
    positions by id, never by hardcoded index.
    """

    columns: dict = field(default_factory=dict)  # object_name -> tuple[str, ...]
    limits: tuple = ()  # tuple[dict, ...]
    rate_limits: tuple = ()  # tuple[TradeLockerRateLimit, ...]
    version_hash: str = ""
    fetched_at_utc: str = ""


@dataclass(frozen=True)
class TradeLockerOrderRecord:
    """Provider-native order/position row (column-resolved)."""

    order_id: int = 0
    instrument_id: int = 0
    qty: float = 0.0
    side: str = ""  # buy / sell
    order_type: str = ""  # market / limit / stop
    validity: str = ""  # IOC / GTC
    status: str = ""  # Filled / Rejected / Pending / ...
    position_id: int = 0
    price: float = 0.0
    stop_price: float = 0.0
    strategy_id: str = ""
    server_time_ms: int = 0
    raw: dict = field(default_factory=dict)
