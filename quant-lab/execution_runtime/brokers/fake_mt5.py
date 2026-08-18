"""QL-EXEC-R2 — deterministic FakeMT5 for offline broker-session tests.

Mimics the field-access patterns of the real MetaTrader5 Python module:
attribute-style named-tuple/record objects, dict-like records, and raw numpy
structured bars can all be injected. No MetaTrader5 dependency is required to
import or use this module.
"""  # noqa: E501
from __future__ import annotations

from typing import Any, Callable, Optional


class _Rec:
    """Attribute + mapping access, mimicking MT5's returned named tuples.

    Supports ``r.field``, ``r["field"]``, ``r.get("field")``, and
    ``"field" in r`` so adapter normalization can be tested against both the
    real attribute API and dict-like fixtures.
    """

    def __init__(self, **kwargs: Any) -> None:
        object.__setattr__(self, "_d", dict(kwargs))
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)

    def __getitem__(self, key: str) -> Any:
        return self._d[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._d.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._d

    def to_dict(self) -> dict:
        return dict(self._d)

    def __repr__(self) -> str:
        return f"_Rec({self._d!r})"


class FakeMT5:
    """Scriptable stand-in for the ``MetaTrader5`` module.

    Every broker call is recorded; results are fully injectable. Standard MT5
    enum constants are exposed so the adapter can reference them exactly like
    the real module.
    """

    # Standard MetaTrader5 enum constants (values as in the real package).
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_INVALID_FILL = 10030
    TRADE_RETCODE_REQUOTE = 10004
    TRADE_RETCODE_BUSY = 10027
    TIMEFRAME_M5 = 5

    def __init__(self) -> None:
        self.initialize_result: bool = True
        self.initialize_calls: list[dict] = []
        self.shutdown_calls: int = 0

        self._terminal_info: Optional[_Rec] = None
        self._account_info: Optional[_Rec] = None
        self.symbol_infos: dict[str, _Rec] = {}
        self.symbol_select_results: dict[str, bool] = {}
        self.symbol_select_calls: list[tuple[str, bool]] = []
        self.ticks: dict[str, _Rec] = {}
        self.bars: dict[str, list] = {}
        self._positions: list[_Rec] = []
        self._orders: list[_Rec] = []
        self._deals: list[_Rec] = []

        self.order_check_calls: list[dict] = []
        self.order_send_calls: list[dict] = []
        self._order_check_fn: Callable[[dict], Optional[_Rec]] = (
            lambda req: _Rec(retcode=0, comment="ok")
        )
        self._order_send_fn: Callable[[dict], Optional[_Rec]] = (
            lambda req: _Rec(retcode=self.TRADE_RETCODE_DONE, comment="done", order=100001)
        )

        self._last_error: str = ""

    # ── configuration helpers ─────────────────────────────────────────────

    def set_terminal_info(self, **kwargs: Any) -> None:
        self._terminal_info = _Rec(**kwargs)

    def set_account_info(self, **kwargs: Any) -> None:
        self._account_info = _Rec(**kwargs)

    def clear_terminal_info(self) -> None:
        self._terminal_info = None

    def clear_account_info(self) -> None:
        self._account_info = None

    def set_symbol_info(self, symbol: str, **kwargs: Any) -> None:
        self.symbol_infos[symbol] = _Rec(**kwargs)

    def set_tick(self, symbol: str, **kwargs: Any) -> None:
        self.ticks[symbol] = _Rec(**kwargs)

    def set_positions(self, records: list) -> None:
        self._positions = [_Rec(**r) if isinstance(r, dict) else r for r in records]

    def set_orders(self, records: list) -> None:
        self._orders = [_Rec(**r) if isinstance(r, dict) else r for r in records]

    def set_deals(self, records: list) -> None:
        self._deals = [_Rec(**r) if isinstance(r, dict) else r for r in records]

    def set_order_check(self, fn: Callable[[dict], Optional[_Rec]]) -> None:
        self._order_check_fn = fn

    def set_order_send(self, fn: Callable[[dict], Optional[_Rec]]) -> None:
        self._order_send_fn = fn

    def set_last_error(self, text: str) -> None:
        self._last_error = text

    # ── MT5 module surface ────────────────────────────────────────────────

    def initialize(self, **kwargs: Any) -> bool:
        self.initialize_calls.append(dict(kwargs))
        return self.initialize_result

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def terminal_info(self) -> Optional[_Rec]:
        return self._terminal_info

    def account_info(self) -> Optional[_Rec]:
        return self._account_info

    def symbol_info(self, symbol: str) -> Optional[_Rec]:
        return self.symbol_infos.get(symbol)

    def symbol_select(self, symbol: str, enable: bool) -> bool:
        self.symbol_select_calls.append((symbol, enable))
        return self.symbol_select_results.get(symbol, False)

    def symbol_info_tick(self, symbol: str) -> Optional[_Rec]:
        return self.ticks.get(symbol)

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start: int, count: int):
        bars = self.bars.get(symbol)
        if bars is None:
            return None
        if start == 0:
            return list(bars[-count:])
        return list(bars[start : start + count])

    def positions_get(self, symbol: Optional[str] = None) -> Optional[list]:
        if not self._positions:
            return None
        if symbol is None:
            return list(self._positions)
        return [p for p in self._positions if getattr(p, "symbol", None) == symbol]

    def orders_get(self, symbol: Optional[str] = None) -> Optional[list]:
        if not self._orders:
            return None
        if symbol is None:
            return list(self._orders)
        return [o for o in self._orders if getattr(o, "symbol", None) == symbol]

    def history_deals_get(self, start, end) -> Optional[list]:
        if not self._deals:
            return None
        return list(self._deals)

    def order_check(self, req: dict) -> Optional[_Rec]:
        self.order_check_calls.append(dict(req))
        return self._order_check_fn(req)

    def order_send(self, req: dict) -> Optional[_Rec]:
        self.order_send_calls.append(dict(req))
        return self._order_send_fn(req)

    def last_error(self) -> str:
        return self._last_error

    # ── fixture factory ───────────────────────────────────────────────────

    @classmethod
    def ox_demo(cls) -> "FakeMT5":
        """A preconfigured Ox Securities demo environment (pure fixture)."""
        fake = cls()
        fake.set_terminal_info(
            company="Ox Securities",
            trade_allowed=True,
            tradeapi_disabled=False,
        )
        fake.set_account_info(
            login=12345678,
            server="OxSecurities-Demo",
            trade_mode=0,
            currency="USD",
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            free_margin=10000.0,
            leverage=100,
            trade_allowed=True,
        )
        return fake
