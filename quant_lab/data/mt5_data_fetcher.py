"""
MT5 Data Fetcher — Pull historical bars from OxSecurities demo
Outputs: CSV files in quant-lab/data/
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent
SYMBOLS = {
    'EURUSD.PRO': 'EURUSD',
    'USDCHF.PRO': 'USDCHF',
    'CHFJPY.PRO': 'CHFJPY',
    'XAUUSD.PRO': 'XAUUSD',
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
        print(f"Connected: {account.name} | {account.server} | Balance: {account.balance} {account.currency}")
    return True

def fetch_symbol(symbol_name, csv_name):
    print(f"\nFetching {symbol_name}...")
    
    # Make sure symbol is selected
    symbol_info = mt5.symbol_info(symbol_name)
    if symbol_info is None:
        print(f"  {symbol_name} not found, trying alternatives...")
        # Try without .PRO suffix
        alt = symbol_name.replace('.PRO', '')
        symbol_info = mt5.symbol_info(alt)
        if symbol_info is None:
            print(f"  Neither {symbol_name} nor {alt} found. Skipping.")
            return None
        symbol_name = alt
    
    if not symbol_info.visible:
        mt5.symbol_select(symbol_name, True)
    
    # Pull all M5 bars from START to END
    rates = mt5.copy_rates_range(symbol_name, TIMEFRAME, START_DATE, END_DATE)
    
    if rates is None or len(rates) == 0:
        print(f"  No data returned. Error: {mt5.last_error()}")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={
        'time': 'timestamp',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'tick_volume': 'volume',
        'spread': 'spread',
        'real_volume': 'real_volume'
    })
    
    # Filter to EST trading hours (remove weekends)
    df['est_hour'] = (df['timestamp'].dt.hour - 5) % 24
    df = df[df['timestamp'].dt.dayofweek < 5]  # Mon-Fri only
    
    out_path = DATA_DIR / f"{csv_name}_M5.csv"
    df.to_csv(out_path, index=False)
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  Saved: {out_path} ({len(df):,} bars, {size_mb:.1f} MB)")
    print(f"  Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def main():
    print("="*60)
    print("MT5 DATA FETCHER — Quant Lab")
    print("="*60)
    
    if not connect():
        return
    
    results = {}
    for symbol, name in SYMBOLS.items():
        df = fetch_symbol(symbol, name)
        if df is not None:
            results[name] = df
    
    mt5.shutdown()
    
    print(f"\n{'='*60}")
    print(f"DONE: {len(results)}/{len(SYMBOLS)} symbols fetched")
    for name, df in results.items():
        print(f"  {name}: {len(df):,} bars")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
