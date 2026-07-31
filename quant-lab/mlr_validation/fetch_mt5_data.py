"""
Fetch M5 data from MT5 for all pairs.
Saves to quant-lab/data/ as CSV files.
"""

import csv
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add repo root to path for venv imports
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "quant-lab" / "data"

# Pairs to fetch — all the main forex pairs + commodities
PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD",
    "NZDJPY", "NZDCHF", "NZDCAD", "NZDAUD",
    "CADJPY", "CADCHF",
    "CHFJPY",
    "XAUUSD", "XAGUSD",
]

# MT5 symbol mapping (add .PRO suffix for some brokers)
MT5_SYMBOLS = {
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "USDJPY": "USDJPY",
    "USDCHF": "USDCHF",
    "AUDUSD": "AUDUSD",
    "NZDUSD": "NZDUSD",
    "USDCAD": "USDCAD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "EURCHF": "EURCHF",
    "EURAUD": "EURAUD",
    "EURNZD": "EURNZD",
    "EURCAD": "EURCAD",
    "GBPJPY": "GBPJPY",
    "GBPCHF": "GBPCHF",
    "GBPAUD": "GBPAUD",
    "GBPCAD": "GBPCAD",
    "GBPNZD": "GBPNZD",
    "AUDJPY": "AUDJPY",
    "AUDCHF": "AUDCHF",
    "AUDNZD": "AUDNZD",
    "AUDCAD": "AUDCAD",
    "NZDJPY": "NZDJPY",
    "NZDCHF": "NZDCHF",
    "NZDCAD": "NZDCAD",
    "NZDAUD": "NZDAUD",
    "CADJPY": "CADJPY",
    "CADCHF": "CADCHF",
    "CHFJPY": "CHFJPY",
    "XAUUSD": "XAUUSD",
    "XAGUSD": "XAGUSD",
}

# Date range for data
FROM_DATE = datetime(2020, 1, 1)
TO_DATE = datetime(2026, 6, 8)


def fetch_pair(symbol: str, mt5_symbol: str) -> list:
    """Fetch M5 data for a single pair from MT5."""
    try:
        import MetaTrader5 as mt5

        if not mt5.initialize():
            print(f"  MT5 init failed")
            return None

        # Try with suffixes if needed
        rates = None
        for suffix in ["", ".PRO", ".pro", "m", "M"]:
            sym = mt5_symbol + suffix
            rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, FROM_DATE, TO_DATE)
            if rates is not None and len(rates) > 0:
                print(f"  Found as {sym}: {len(rates)} bars")
                break

        mt5.shutdown()

        if rates is None or len(rates) == 0:
            print(f"  No data for {mt5_symbol}")
            return None

        rows = []
        for r in rates:
            dt = datetime.fromtimestamp(r["time"])
            rows.append({
                "datetime": dt,
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "date": dt.date(),
                "hour": dt.hour,
            })

        return rows

    except ImportError:
        print("  MetaTrader5 not available")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def save_csv(symbol: str, rows: list):
    """Save fetched data to CSV."""
    filepath = DATA_DIR / f"{symbol}_M5_fetched.csv"
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close"])
        for r in rows:
            writer.writerow([
                r["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                r["open"], r["high"], r["low"], r["close"]
            ])
    print(f"  Saved {len(rows)} bars to {filepath.name}")


def main():
    print(f"Fetching M5 data from MT5...")
    print(f"Date range: {FROM_DATE} to {TO_DATE}")
    print(f"Pairs: {len(PAIRS)}")
    print()

    success = 0
    failed = 0
    skipped = 0

    for pair in PAIRS:
        mt5_sym = MT5_SYMBOLS.get(pair, pair)

        # Check if we already have M5 data
        existing = list(DATA_DIR.glob(f"{pair}*M5*.csv"))
        has_real_m5 = False
        for ef in existing:
            # Quick check: if file > 5MB and not daily, skip
            if ef.stat().st_size > 5_000_000:
                # Verify it's actually M5
                with open(ef) as f:
                    reader = csv.DictReader(f)
                    r1 = next(reader, None)
                    r2 = next(reader, None)
                    if r1 and r2:
                        ts_col = None
                        for c in ["timestamp", "time"]:
                            if c in r1:
                                ts_col = c
                                break
                        if ts_col:
                            try:
                                t1 = r1[ts_col].strip()
                                t2 = r2[ts_col].strip()
                                try:
                                    dt1 = datetime.fromtimestamp(int(t1))
                                    dt2 = datetime.fromtimestamp(int(t2))
                                except:
                                    dt1 = datetime.fromisoformat(t1)
                                    dt2 = datetime.fromisoformat(t2)
                                if (dt2 - dt1).total_seconds() <= 600:
                                    has_real_m5 = True
                            except:
                                pass

        if has_real_m5:
            print(f"  {pair}: SKIP (already have M5 data)")
            skipped += 1
            continue

        print(f"Fetching {pair}...")
        rows = fetch_pair(pair, mt5_sym)
        if rows and len(rows) > 100:
            save_csv(pair, rows)
            success += 1
        else:
            failed += 1

        time.sleep(0.5)  # Rate limit

    print(f"\nDone: {success} fetched, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
