import pandas as pd
import numpy as np
import os

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

for sym in symbols:
    path = f'data/normalized/h1/{sym}_H1.parquet'
    df = pd.read_parquet(path)
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df = df.sort_values('timestamp_utc')
    
    # Check frequency in common window
    COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
    COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')
    
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()
    
    if len(df_common) > 1:
        diffs = df_common['timestamp_utc'].diff().dropna()
        unique_diffs = diffs.unique()
        print(f"\n{sym}:")
        print(f"  Rows in common window: {len(df_common)}")
        print(f"  Time diffs (hours): {sorted([d.total_seconds()/3600 for d in unique_diffs])[:10]}")
        print(f"  First few timestamps: {df_common['timestamp_utc'].head(3).values}")
        print(f"  Last few timestamps: {df_common['timestamp_utc'].tail(3).values}")