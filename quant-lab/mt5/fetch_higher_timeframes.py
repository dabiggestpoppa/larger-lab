"""
Fetch Daily, Weekly, and Monthly data from MT5.
Higher timeframes = more historical data available (years instead of months).
This gives the Macro DTB model much more training data.
"""
import MetaTrader5 as mt5
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Symbols to fetch (use .PRO suffix for consistency)
SYMBOLS = [
    "EURUSD.PRO", "GBPUSD.PRO", "USDJPY.PRO", "USDCHF.PRO",
    "USDCAD.PRO", "AUDUSD.PRO", "NZDUSD.PRO",
    "EURGBP.PRO", "EURJPY.PRO", "EURCHF.PRO", "EURAUD.PRO",
    "GBPJPY.PRO", "GBPCHF.PRO", "GBPAUD.PRO",
    "AUDJPY.PRO", "AUDCHF.PRO", "AUDCAD.PRO",
    "NZDJPY.PRO", "NZDCHF.PRO", "NZDCAD.PRO",
    "CADJPY.PRO", "CADCHF.PRO", "CHFJPY.PRO",
    "BTCUSD", "ETHUSD",
]

# Timeframes to fetch
TIMEFRAMES = {
    "D1": (mt5.TIMEFRAME_D1, "_D1.csv", "Daily"),
    "W1": (mt5.TIMEFRAME_W1, "_W1.csv", "Weekly"),
    "MN1": (mt5.TIMEFRAME_MN1, "_MN1.csv", "Monthly"),
}


def fetch_and_save(symbol: str, timeframe: int, suffix: str, label: str):
    """Fetch data from MT5 and save as CSV."""
    output_name = symbol.replace(".", "_") + suffix
    output_path = DATA_DIR / output_name

    # Check if already exists and has data
    if output_path.exists() and output_path.stat().st_size > 10000:
        print(f"  SKIP {symbol} {label}: {output_name} already exists ({output_path.stat().st_size // 1024}KB)")
        return True

    # Make sure symbol is visible
    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(1)

    # Fetch bars — get as many as possible
    print(f"  Fetching {symbol} {label} bars...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 500000)

    if rates is None or len(rates) == 0:
        print(f"  FAIL {symbol} {label}: no data returned ({mt5.last_error()})")
        return False

    print(f"  Got {len(rates)} bars for {symbol} {label}")

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "volume"])
        for r in rates:
            t = datetime.fromtimestamp(int(r["time"])).strftime("%Y-%m-%dT%H:%M:%S")
            vol = 0
            if isinstance(r, dict):
                vol = r.get("tick_volume", r.get("volume", 0))
            else:
                # numpy void — access by index
                try:
                    vol = r[6] if len(r) > 6 else 0
                except (IndexError, KeyError):
                    vol = 0
            writer.writerow([
                t,
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                vol,
            ])

    print(f"  Saved: {output_path.name} ({len(rates)} bars)")
    return True


def main():
    print("=" * 60)
    print("Fetch Higher Timeframe Data from MT5")
    print("=" * 60)

    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return

    print(f"MT5 connected: {mt5.account_info()}")
    print(f"Symbols: {len(SYMBOLS)}")
    print(f"Timeframes: {list(TIMEFRAMES.keys())}")
    print()

    results = {"ok": 0, "skip": 0, "fail": 0}

    for symbol in SYMBOLS:
        for tf_name, (tf_const, suffix, label) in TIMEFRAMES.items():
            try:
                success = fetch_and_save(symbol, tf_const, suffix, label)
                if success:
                    # Check if it was a skip
                    output_path = DATA_DIR / (symbol.replace(".", "_") + suffix)
                    if output_path.exists() and output_path.stat().st_size > 10000:
                        results["ok"] += 1
                    else:
                        results["skip"] += 1
                else:
                    results["fail"] += 1
            except Exception as e:
                print(f"  ERROR {symbol} {label}: {e}")
                results["fail"] += 1

    mt5.shutdown()

    print(f"\n{'='*60}")
    print(f"Results: {results['ok']} fetched, {results['skip']} skipped, {results['fail']} failed")
    print(f"Data saved to: {DATA_DIR}")


if __name__ == "__main__":
    main()
