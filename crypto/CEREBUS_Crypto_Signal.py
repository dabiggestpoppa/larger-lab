"""
CEREBUS FX v4.0 — Crypto Signal Generator
==========================================
Generates live ST + P90 signals for crypto assets.
Outputs signals to data/signals/crypto_signals.json.
ccxt is optional — runs in signal-only mode if not installed.
"""
import sys, os, json, csv, time
from pathlib import Path
from datetime import datetime

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab"))
sys.path.insert(0, str(LAB / "quant-lab/engines"))

DATA_DIR = LAB / "quant-lab/data"
SIGNAL_DIR = LAB / "data/signals"
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("ccxt not installed — running in signal-only mode (no exchange connection)")

CRYPTO_ASSETS = {
    "BTCUSD": {"csv": "BTCUSD_M5.csv", "pip": 1.0},
    "ETHUSD": {"csv": "ETHUSD_M5.csv", "pip": 1.0},
}


def load_recent_bars(filepath, num_bars=500, max_rows=300000):
    from symmetry_trap import Bar
    bars = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            try:
                ts_str = row.get('datetime', row.get('time', ''))
                try:
                    ts = datetime.fromisoformat(ts_str)
                except Exception:
                    ts = datetime(2020, 1, 1)
                bar = Bar(timestamp=ts, open=float(row['open']), high=float(row['high']),
                          low=float(row['low']), close=float(row['close']))
                bars.append(bar)
            except (KeyError, ValueError):
                continue
    return bars[-num_bars:] if len(bars) > num_bars else bars


def generate_signals(csv_path, pip_size, symbol):
    """Generate ST + P90 signals from recent bars."""
    from symmetry_trap import SymmetryTrapEngine
    signals = {"symbol": symbol, "timestamp": datetime.now().isoformat(), "st": None, "p90": None}
    try:
        engine = SymmetryTrapEngine(pip_size=pip_size)
        bars = load_recent_bars(str(csv_path), num_bars=500)
        last_signal = None
        for bar in bars:
            sig = engine.process_bar(bar)
            if sig is not None:
                last_signal = {
                    "event": sig.event,
                    "direction": sig.direction.value if sig.direction else None,
                    "entry_price": sig.entry_price,
                    "sl": sig.sl_price,
                    "tp": sig.tp_price,
                    "reason": sig.reason,
                    "bar_time": str(bar.timestamp),
                }
        signals["st"] = last_signal
    except Exception as e:
        signals["st"] = {"error": str(e)}
    return signals


def main():
    print("=" * 60)
    print("CEREBUS CRYPTO SIGNAL GENERATOR")
    print(f"ccxt available: {CCXT_AVAILABLE}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    all_signals = []
    for symbol, cfg in CRYPTO_ASSETS.items():
        csv_path = DATA_DIR / cfg["csv"]
        if not csv_path.exists():
            print(f"SKIP {symbol}: data file not found")
            continue
        print(f"Generating signals for {symbol}...")
        sig = generate_signals(str(csv_path), cfg["pip"], symbol)
        all_signals.append(sig)
        st_sig = sig.get("st")
        if st_sig and "event" in st_sig:
            print(f"  ST: {st_sig.get('event')} {st_sig.get('direction')} @ {st_sig.get('entry_price')}")
        elif st_sig and "error" in st_sig:
            print(f"  ST ERROR: {st_sig['error']}")
        else:
            print(f"  ST: No signal")
    out_path = SIGNAL_DIR / "crypto_signals.json"
    with open(out_path, 'w') as f:
        json.dump({"timestamp": datetime.now().isoformat(), "signals": all_signals}, f, indent=2)
    print(f"\nSignals saved: {out_path}")
    return all_signals

if __name__ == "__main__":
    main()
