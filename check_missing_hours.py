import pandas as pd
import numpy as np
import os

# Check which specific hours are missing for EURGBP
sym = 'EURGBP'
path = f'data/normalized/h1/{sym}_H1.parquet'
df = pd.read_parquet(path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
df = df.sort_values('timestamp_utc')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()

# Check hours present
hours_present = df_common['timestamp_utc'].dt.hour.value_counts().sort_index()
print(f"Hours present in data:")
for h, count in hours_present.items():
    print(f"  Hour {h:2d}: {count} bars")

# Check expected hours (0-23)
print(f"\nMissing hours (0-23):")
for h in range(24):
    if h not in hours_present.index:
        print(f"  Hour {h:2d}: MISSING")

# Check if it's a specific hour range missing
print(f"\nTotal bars: {len(df_common)}")
print(f"Expected bars (17539): {17539}")
print(f"Missing: {17539 - len(df_common)}")