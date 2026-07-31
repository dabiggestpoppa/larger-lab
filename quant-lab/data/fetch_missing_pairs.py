"""
Fetch missing pairs from MT5: USDSEK, ETHUSD, BTCUSD, SOLUSD, XRPUSD
Saves as M5 CSV in quant-lab/data/
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent

# Symbols to fetch: MT5 name -> CSV name
SYMBOLS = {
    'USDSEK': 'USDSEK_M5.csv',
    'ETHUSD': 'ETHUSD_M5.csv',
    'BTCUSD': 'BTCUSD_M5.csv',
    'SOLUSD': 'SOLUSD_M5.csv',
    'XRPUSD': 'XRPUSD_M5.csv',
}

# Also try these alternatives if primary not found
ALT_SYMBOLS = {
    'USDSEK': ['USDSEK.PRO', 'USDSEK.i', 'USDSEKm'],
    'ETHUSD': ['ETHUSD.PRO', 'ETHUSD.i', 'ETHUSDM', 'ETH/USD'],
    'BTCUSD': ['BTCUSD.PRO', 'BTCUSD.i', 'BTCUSDM', 'BTC/USD'],
    'SOLUSD': ['SOLUSD.PRO', 'SOLUSD.i', 'SOLUSDM', 'SOL/USD'],
    'XRPUSD': ['XRPUSD.PRO', 'XRPUSD.i', 'XRPUSDM', 'XRP/USD'],
}

TIMEFRAME = mt5.TIMEFRAME_M5
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime.now()


def connect():
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return False
    account = mt5.account_info()
    if account:
        print(f"Connected: {account.name} | {account.server}")
    return True


def find_symbol(name):
    """Try to find the symbol on MT5."""
    # Try primary
    info = mt5.symbol_info(name)
    if info is not None:
        return name
    # Try alternatives
    for alt in ALT_SYMBOLS.get(name, []):
        info = mt5.symbol_info(alt)
        if info is not None:
            print(f"  Found as {alt}")
            return alt
    return None


def fetch_symbol(mt5_name, csv_path):
    symbol = find_symbol(mt5_name)
    if symbol is None:
        print(f"  {mt5_name} not found on MT5. Skipping.")
        return False

    if not mt5.symbol_info(symbol).visible:
        mt5.symbol_select(symbol, True)

    print(f"  Fetching {symbol} M5 from {START_DATE.date()} to {END_DATE.date()}...")
    rates = mt5.copy_rates_range(symbol, TIMEFRAME, START_DATE, END_DATE)

    if rates is None or len(rates) == 0:
        print(f"  No data. Error: {mt5.last_error()}")
        return False

    df = pd.DataFrame(rates)
    df['timestamp'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Save with standard columns
    out = df[['timestamp', 'open', 'high', 'low', 'close', 'tick_volume']].copy()
    out.to_csv(csv_path, index=False)
    print(f"  Saved {len(out)} bars to {csv_path}")
    return True


def main():
    if not connect():
        return

    results = {}
    for name, csv_name in SYMBOLS.items():
        csv_path = DATA_DIR / csv_name
        if csv_path.exists():
            print(f"\n{name}: {csv_name} already exists ({csv_path.stat().st_size//1024}KB). Skipping.")
            results[name] = "EXISTS"
            continue
        print(f"\n{name}:")
        success = fetch_symbol(name, csv_path)
        results[name] = "OK" if success else "FAILED"

    print("\n=== RESULTS ===")
    for name, status in results.items():
        print(f"  {name}: {status}")

    mt5.shutdown()


if __name__ == "__main__":
    main()
