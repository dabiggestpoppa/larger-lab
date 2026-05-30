import sys
sys.stdout.reconfigure(encoding='utf-8')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")

if not mt5.initialize():
    print(f"MT5 init failed: {mt5.last_error()}")
    sys.exit(1)

account = mt5.account_info()
if account:
    print(f"Connected: {account.name} | {account.server}")

symbol = "EURUSD.PRO"
tf = mt5.TIMEFRAME_M5

ranges = [
    (datetime(2023, 1, 1), datetime(2023, 12, 31, 23, 59), "2023"),
    (datetime(2024, 1, 1), datetime(2024, 12, 31, 23, 59), "2024"),
    (datetime(2025, 1, 1), datetime(2025, 12, 31, 23, 59), "2025"),
]

all_dfs = []
for start, end, label in ranges:
    print(f"\nFetching {label}...")
    rates = mt5.copy_rates_range(symbol, tf, start, end)
    if rates is None or len(rates) == 0:
        print(f"  No data for {label}: {mt5.last_error()}")
        continue
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={'time':'timestamp','open':'open','high':'high','low':'low','close':'close','tick_volume':'volume','spread':'spread','real_volume':'real_volume'})
    df = df[df['timestamp'].dt.dayofweek < 5]
    df['est_hour'] = (df['timestamp'].dt.hour - 5) % 24
    df['est_date'] = (df['timestamp'] - pd.Timedelta(hours=5)).dt.date
    print(f"  {label}: {len(df):,} bars")
    all_dfs.append(df)

mt5.shutdown()

if not all_dfs:
    print("No data fetched!")
    sys.exit(1)

combined = pd.concat(all_dfs, ignore_index=True)
combined = combined.sort_values('timestamp').reset_index(drop=True)
print(f"\nTotal: {len(combined):,} bars")
print(f"Range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")

out_path = DATA_DIR / "EURUSDPRO_M5_2023_2025.csv"
combined.to_csv(out_path, index=False)
size_mb = out_path.stat().st_size / 1024 / 1024
print(f"Saved: {out_path} ({size_mb:.1f} MB)")
