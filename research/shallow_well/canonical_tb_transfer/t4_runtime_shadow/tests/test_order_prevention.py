"""
CTBT T4 — Order-prevention tests.

Prove broker write/order capabilities are unreachable from the CTBT runtime:
  1. static: no write-capable token anywhere in the ctbt_runtime package
  2. dynamic: the ReadOnlyMT5Proxy blocks every write-capable attribute
  3. dynamic: allowlisted read methods are the ONLY MT5 surface the runtime uses
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ctbt_runtime.config import T4_DIR  # noqa: E402
from ctbt_runtime.read_only_proxy import (ALLOWED_MT5_ATTRS, WRITE_CAPABLE_ATTRS,  # noqa: E402
                                          ReadOnlyMT5Proxy, ReadOnlyViolation,
                                          wrap_read_only)

# Every broker write / order / position / history capability token that must
# never appear in the CTBT runtime package.
FORBIDDEN_TOKENS = [
    "order_send", "order_calc_margin", "order_calc_profit",
    "positions_get", "positions_total", "orders_get", "orders_total",
    "history_deals_get", "history_orders_get",
    "deal_send", "trade_send", "modify", "order_modify", "order_cancel",
]


def test_static_no_write_tokens():
    """No write-capable token may appear in ANY runtime module except the
    barrier module itself, where they exist only as deny-list definitions
    (proven dynamically by test_proxy_blocks_write_capabilities)."""
    pkg = T4_DIR / "ctbt_runtime"
    offenders = []
    for py in sorted(pkg.rglob("*.py")):
        if py.name == "read_only_proxy.py":
            continue  # the barrier module documents the deny-list
        src = py.read_text(encoding="utf-8")
        for tok in FORBIDDEN_TOKENS:
            if re.search(rf"\b{re.escape(tok)}\b", src):
                offenders.append((py.name, tok))
    assert not offenders, f"write-capable tokens found in runtime: {offenders}"


def test_proxy_blocks_write_capabilities():
    class FakeMT5:
        order_send = staticmethod(lambda *a, **k: None)
        positions_get = staticmethod(lambda *a, **k: None)
        history_deals_get = staticmethod(lambda *a, **k: None)

    p = ReadOnlyMT5Proxy(FakeMT5())
    for attr in WRITE_CAPABLE_ATTRS:
        try:
            getattr(p, attr)
        except ReadOnlyViolation:
            continue
        raise AssertionError(f"proxy allowed write-capable attr: {attr}")
    # any non-allowlisted attr also blocked
    for attr in ["order_send", "magic", "some_other_thing"]:
        try:
            getattr(p, attr)
        except ReadOnlyViolation:
            continue
        raise AssertionError(f"proxy allowed unknown attr: {attr}")


def test_proxy_allows_read_only_constants():
    """Data-format constants (TIMEFRAME_*, COPY_TICKS_*, COPY_RATES_*) are
    read-only enums and must pass through."""
    import MetaTrader5 as mt5
    p = ReadOnlyMT5Proxy(mt5)
    assert p.TIMEFRAME_M5 is not None
    assert p.COPY_TICKS_INFO is not None
    # but the write surface stays blocked even with the module present
    for attr in WRITE_CAPABLE_ATTRS:
        try:
            getattr(p, attr)
        except ReadOnlyViolation:
            continue
        raise AssertionError(f"proxy allowed write-capable attr: {attr}")


def test_proxy_forwards_read_allowlist():
    class FakeMT5:
        def symbol_info_tick(self, s):
            return s

    p = ReadOnlyMT5Proxy(FakeMT5())
    assert p.symbol_info_tick("EURUSD.PRO") == "EURUSD.PRO"
    # the runtime may only ever touch the allowlist surface
    assert ALLOWED_MT5_ATTRS.isdisjoint(WRITE_CAPABLE_ATTRS)


def test_runtime_imports_only_via_proxy():
    """The data feed must obtain MT5 through wrap_read_only(), not directly."""
    src = (T4_DIR / "ctbt_runtime" / "data_feed.py").read_text(encoding="utf-8")
    assert "wrap_read_only()" in src or "ReadOnlyMT5Proxy" in src
    assert "import MetaTrader5" not in src.replace(
        "from .read_only_proxy import", "")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"order-prevention: {len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
