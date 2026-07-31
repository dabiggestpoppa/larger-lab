"""
CEREBUS FX v4.0 — Crypto Trade Copier
=======================================
Reads trade signals from data/signals/crypto_signats.json
and formats them for exchange API execution.
ccxt is optional — prints formatted orders if not installed.
"""
import sys, os, json
from pathlib import Path
from datetime import datetime

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
SIGNAL_DIR = LAB / "data/signals"

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False


def load_signals():
    signal_path = SIGNAL_DIR / "crypto_signals.json"
    if not signal_path.exists():
        print("No signals file found. Run CEREBUS_Crypto_Signal.py first.")
        return None
    with open(signal_path, 'r') as f:
        return json.load(f)


def format_order(signal):
    """Format a signal into an exchange order dict."""
    if signal is None or "event" not in signal:
        return None
    if signal["event"] != "ENTRY":
        return None
    direction = signal.get("direction", "BUY")
    return {
        "side": "buy" if direction == "BUY" else "sell",
        "type": "limit",
        "price": signal.get("entry_price"),
        "stop_loss": signal.get("sl"),
        "take_profit": signal.get("tp"),
        "reason": signal.get("reason", ""),
    }


def execute_orders(orders, exchange_id="binance"):
    """Execute orders via ccxt exchange."""
    if not CCXT_AVAILABLE:
        print("ccxt not installed — printing orders only (dry run)")
        for order in orders:
            print(f"  DRY RUN: {order}")
        return []
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        results = []
        for order in orders:
            print(f"  EXECUTING: {order}")
            result = exchange.create_order(
                symbol=order.get("symbol", "BTC/USDT"),
                type=order["type"],
                side=order["side"],
                amount=order.get("amount", 0.001),
                price=order.get("price"),
            )
            results.append(result)
        return results
    except Exception as e:
        print(f"Exchange error: {e}")
        return []


def main():
    print("=" * 60)
    print("CEREBUS CRYPTO TRADE COPIER")
    print(f"ccxt available: {CCXT_AVAILABLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    data = load_signals()
    if data is None:
        return
    signals = data.get("signals", [])
    all_orders = []
    for sig in signals:
        symbol = sig.get("symbol", "UNKNOWN")
        st_signal = sig.get("st")
        order = format_order(st_signal)
        if order:
            order["symbol"] = symbol
            all_orders.append(order)
            print(f"  {symbol}: {order['side'].upper()} @ {order['price']} | SL={order.get('stop_loss')} TP={order.get('take_profit')}")
    if all_orders:
        print(f"\nExecuting {len(all_orders)} order(s)...")
        execute_orders(all_orders)
    else:
        print("No actionable signals found.")

if __name__ == "__main__":
    main()
