import pandas as pd
import numpy as np
import os

# Check for duplicates in normalized data
sym = 'EURGBP'
path = f'data/normalized/h1/{sym}_H1.parquet'
df = pd.read_parquet(path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
df = df.sort_values('timestamp_utc')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()

print(f"Total rows: {len(df_common)}")
print(f"Unique timestamps: {df_common['timestamp_utc'].nunique()}")
print(f"Duplicates: {len(df_common) - df_common['timestamp_utc'].nunique()}")

# Check duplicates
dupes = df_common[df_common.duplicated(subset=['timestamp_utc'], keep=False)]
if len(dupes) > 0:
    print(f"\nDuplicate timestamps:")
    print(dupes[['timestamp_utc', 'open', 'high', 'low', 'close']].head(20))
    print(f"\nDuplicate timestamp values:")
    for ts in dupes['timestamp_utc'].unique()[:10]:
        rows = dupes[dupes['timestamp_utc'] == ts]
        print(f"  {ts}: {len(rows)} rows")
        print(f"    OHLC: {rows[['open','high','low','close']].values}")