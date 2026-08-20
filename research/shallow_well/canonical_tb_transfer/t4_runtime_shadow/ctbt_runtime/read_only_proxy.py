"""
CTBT T4 — Fail-closed read-only MT5 proxy.

The CTBT shadow runtime is only ever allowed READ-ONLY market-data access.
This proxy exposes a strict allowlist of MetaTrader5 methods and raises
AttributeError for EVERYTHING else — including all order/position/write
capabilities (order_send, order_calc_margin, positions_get, orders_get,
history_deals_get, deal_send, trade_*).

The runtime package imports MetaTrader5 ONLY through this proxy.  The
order-prevention test statically verifies the runtime package never touches
the write-capable API surface, and dynamically verifies the proxy blocks it.
"""
from __future__ import annotations

import types
from typing import Any

# The ONLY MetaTrader5 entry points the shadow runtime may call.
ALLOWED_MT5_ATTRS = frozenset({
    # lifecycle
    "initialize", "shutdown", "terminal_info", "last_error",
    "version", "package_info",
    # account / read-only info
    "account_info",
    # market data (read-only)
    "symbol_info", "symbol_info_tick", "symbols_get", "symbol_select",
    "copy_rates_from_pos", "copy_rates_from", "copy_rates_range",
    "copy_ticks_from", "copy_ticks_range",
})

# Read-only module CONSTANTS (data-format enums, not capabilities).  These are
# plain integers describing bar/tick formats and are safe to expose.
ALLOWED_CONSTANT_PREFIXES = ("TIMEFRAME_", "COPY_TICKS_", "COPY_RATES_")

# Explicit denylist documented for the audit (never allowed through the proxy).
WRITE_CAPABLE_ATTRS = frozenset({
    "order_send", "order_calc_margin", "order_calc_profit",
    "positions_get", "positions_total", "orders_get", "orders_total",
    "history_deals_get", "history_orders_get", "history_deals_total",
    "history_orders_total",
})


class ReadOnlyViolation(AttributeError):
    """Raised when any non-allowlisted MT5 capability is accessed."""


class ReadOnlyMT5Proxy:
    """Fail-closed facade over the MetaTrader5 module.

    Only ALLOWED_MT5_ATTRS are forwarded.  Any other attribute access raises
    ReadOnlyViolation — write/order/position capabilities are unreachable by
    construction, not by convention.
    """

    def __init__(self, mt5_module: Any):
        self._m = mt5_module

    def __getattr__(self, name: str) -> Any:
        if name in ALLOWED_MT5_ATTRS:
            return getattr(self._m, name)
        if name.startswith(ALLOWED_CONSTANT_PREFIXES):
            return getattr(self._m, name)
        if name in WRITE_CAPABLE_ATTRS:
            raise ReadOnlyViolation(
                f"BLOCKED: {name} is a broker write/order capability and is "
                f"unreachable from the CTBT shadow runtime.")
        raise ReadOnlyViolation(
            f"BLOCKED: attribute '{name}' is not on the CTBT read-only allowlist.")


def wrap_read_only() -> ReadOnlyMT5Proxy:
    """Import MetaTrader5 and wrap it in the read-only proxy (fail closed)."""
    import MetaTrader5 as mt5  # noqa: PLC0415 — only import path in the runtime
    return ReadOnlyMT5Proxy(mt5)
