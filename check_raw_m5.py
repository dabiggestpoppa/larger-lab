import pandas as pd
import numpy as np
import os

# Check raw M5 data for EURGBP, EURJPY, EURCHF in common window
symbols = ['EURGBP', 'EURJPY', 'EURCHF']

for sym in symbols:
    path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"\n{sym} raw M5:")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Rows: {len(df)}")
        
        # Parse timestamps
        if 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'], utc=True)
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        df = df.sort_values('timestamp')
        
        COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
        COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')
        
        df_common = df[(df['timestamp'] >= COMMON_START) & (df['timestamp'] <= COMMON_END)].copy()
        
        print(f"  Rows in common window: {len(df_common)}")
        print(f"  First: {df_common['timestamp'].min()}")
        print(f"  Last: {df_common['timestamp'].max()}")
        
        if len(df_common) > 1:
            diffs = df_common['timestamp'].diff().dropna()
            unique_diffs = diffs.unique()
            print(f"  Time diffs (minutes): {sorted([d.total_seconds()/60 for d in unique_diffs])[:10]}")
    else:
        print(f"\n{sym}: FILE NOT FOUND")