"""
Fetch all MT5 data → CSV files
Runs standalone: python fetch_all.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess
import time
from datetime import datetime
from pathlib import Path

MT5_EXE = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
DATA_DIR = Path(__file__).parent
REPORTS_DIR = Path(__file__).parent.parent / 'reports'

SYMBOLS = {
    'EURUSD.PRO': 'EURUSD',
    'USDCHF.PRO': 'USDCHF',
    'CHFJPY.PRO': 'CHFJPY',
    'XAUUSD.PRO': 'XAUUSD',
}

TIMEFRAME = 7  # M5 in the constants below
START = datetime(2022, 1, 1)

def check_mt5_running():
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], capture_output=True, text=True)
    return 'terminal64' in r.stdout

def start_mt5():
    print(f"Starting MT5: {MT5_EXE}")
    subprocess.Popen([MT5_EXE], shell=True)
    for i in range(30):
        time.sleep(1)
        if check_mt5_running():
            print(f"MT5 started ({i+1}s)")
            time.sleep(5)  # Let it fully init and connect
            return True
    return False

def main():
    import MetaTrader5 as mt5
    
    print("="*60)
    print("  MT5 DATA FETCH → CSV")
    print("="*60)
    
    # Step 1: Ensure MT5 is running
    if not check_mt5_running():
        print("MT5 not running, launching...")
        if not start_mt5():
            print("FAILED to start MT5")
            return
    else:
        print("MT5 already running ✓")
    
    # Step 2: Connect
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return
    
    account = mt5.account_info()
    print(f"Connected: {account.login} @ {account.server} | Balance: {account.balance} {account.currency}")
    
    # Step 3: Pull data for each symbol
    import pandas as pd
    import pytz
    
    results = {}
    now = datetime.now()
    
    for sym, name in SYMBOLS.items():
        print(f"\nFetching {sym}...")
        rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, START, now)
        
        if rates is None or len(rates) == 0:
            print(f"  FAILED: {mt5.last_error()}")
            continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={
            'time': 'timestamp',
            'tick_volume': 'volume',
            'real_volume': 'real_volume'
        })
        
        # Filter weekends
        df = df[df['timestamp'].dt.dayofweek < 5]
        
        out_path = DATA_DIR / f"{name}_M5.csv"
        df.to_csv(out_path, index=False)
        size_mb = out_path.stat().st_size / 1024 / 1024
        
        print(f"  ✓ {len(df):,} bars | {size_mb:.1f} MB | {df['timestamp'].min()} → {df['timestamp'].max()}")
        results[name] = df
    
    # Step 4: Data quality report
    print(f"\n{'='*60}")
    print("  DATA QUALITY REPORT")
    print(f"{'='*60}")
    
    total_bars = 0
    for name, df in results.items():
        bars = len(df)
        total_bars += bars
        date_range = f"{df['timestamp'].min().date()} → {df['timestamp'].max().date()}"
        gaps = df['timestamp'].diff().dt.total_seconds().gt(300 * 3).sum()  # gaps > 15min
        print(f"  {name:12}: {bars:>8,} bars | {date_range} | {gaps} gaps")
    
    print(f"\nTOTAL: {total_bars:,} bars across {len(results)} symbols")
    print(f"Files saved to: {DATA_DIR}")
    
    # Save fetch report
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"data_fetch_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w') as f:
        f.write(f"MT5 Data Fetch Report — {now}\n")
        f.write(f"Account: {account.login} @ {account.server}\n")
        for name, df in results.items():
            f.write(f"{name}: {len(df)} bars, {df['timestamp'].min()} → {df['timestamp'].max()}\n")
    print(f"Report: {report_path}")
    
    mt5.shutdown()
    print(f"\n{'='*60}")
    print("  ✓ COMPLETE")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
