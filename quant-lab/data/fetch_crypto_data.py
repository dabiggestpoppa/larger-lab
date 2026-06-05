"""
Fetch crypto M5 data from MT5 → CSV files
Majors only, spread < 1%:
  BTCUSD, ETHUSD, BNBUSD, SOLUSD, LTCUSD, BCHUSD, XLMUSD
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent
START = datetime(2022, 1, 1)

CRYPTO_SYMBOLS = {
    'BTCUSD': 'BTCUSD',
    'ETHUSD': 'ETHUSD',
    'BNBUSD': 'BNBUSD',
    'SOLUSD': 'SOLUSD',
    'LTCUSD': 'LTCUSD',
    'BCHUSD': 'BCHUSD',
    'XLMUSD': 'XLMUSD',
}

def main():
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return

    account = mt5.account_info()
    print(f"Connected: {account.login} @ {account.server} | Balance: {account.balance} {account.currency}")
    print(f"Fetching M5 data from {START.date()} to now...")
    print("=" * 70)

    now = datetime.now()
    results = {}

    for sym, name in CRYPTO_SYMBOLS.items():
        print(f"\nFetching {sym}...")

        # Check symbol exists and is visible
        info = mt5.symbol_info(sym)
        if info is None:
            print(f"  {sym} not found. Skipping.")
            continue
        if not info.visible:
            mt5.symbol_select(sym, True)
            import time; time.sleep(1)
            info = mt5.symbol_info(sym)
            if info is None:
                print(f"  {sym} still not available. Skipping.")
                continue

        # Get spread info
        tick = mt5.symbol_info_tick(sym)
        if tick:
            spread = tick.ask - tick.bid
            spread_pct = (spread / tick.bid) * 100 if tick.bid > 0 else 0
            print(f"  Spread: ${spread:.2f} ({spread_pct:.2f}%)")

        # Pull M5 bars
        rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, START, now)
        if rates is None or len(rates) == 0:
            print(f"  No data returned. Error: {mt5.last_error()}")
            continue

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'time': 'timestamp', 'tick_volume': 'volume', 'real_volume': 'real_volume'})

        # Filter weekends (crypto trades 24/7 but we want consistency)
        # Actually for crypto we keep all bars — no weekend filter

        out_path = DATA_DIR / f"{name}_M5.csv"
        df.to_csv(out_path, index=False)
        size_mb = out_path.stat().st_size / 1024 / 1024

        print(f"  OK: {len(df):,} bars | {size_mb:.1f} MB | {df['timestamp'].min()} → {df['timestamp'].max()}")
        results[name] = (len(df), size_mb)

    print(f"\n{'=' * 70}")
    print("  RESULTS SUMMARY")
    print(f"{'=' * 70}")
    total_bars = 0
    total_mb = 0
    for name, (bars, mb) in results.items():
        total_bars += bars
        total_mb += mb
        print(f"  {name:10}: {bars:>8,} bars | {mb:.1f} MB")
    print(f"\n  TOTAL: {total_bars:,} bars | {total_mb:.1f} MB across {len(results)} symbols")
    print(f"  Files saved to: {DATA_DIR}")

    mt5.shutdown()
    print(f"\n  COMPLETE")

if __name__ == '__main__':
    main()
