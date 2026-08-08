import pandas as pd
import numpy as np
import os

# Check what hours are present in raw M5 data for EURGBP
sym = 'EURGBP'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)
df['timestamp'] = pd.to_datetime(df['time'], utc=True)
df = df.sort_values('timestamp')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

df_common = df[(df['timestamp'] >= COMMON_START) & (df['timestamp'] <= COMMON_END)].copy()

# Check hours present
hours_present = df_common['timestamp'].dt.hour.value_counts().sort_index()
print(f"Hours present in raw M5 data:")
for h, count in hours_present.items():
    print(f"  Hour {h:2d}: {count} bars")

# Check if it's a specific hour range missing
print(f"\nMissing hours (0-23):")
for h in range(24):
    if h not in hours_present.index:
        print(f"  Hour {h:2d}: MISSING")

# Check the gap period specifically
gap_start = pd.Timestamp('2023-07-07 20:00:00', tz='UTC')
gap_end = pd.Timestamp('2026-05-15 23:00:00', tz='UTC')

df_gap = df[(df['timestamp'] >= gap_start) & (df['timestamp'] <= gap_end)].copy()
print(f"\nRaw M5 rows in gap period: {len(df_gap)}")
if len(df_gap) > 0:
    print(f"First: {df_gap['timestamp'].min()}")
    print(f"Last: {df_gap['timestamp'].max()}")
    hours_in_gap = df_gap['timestamp'].dt.hour.value_counts().sort_index()
    print(f"Hours in gap period:")
    for h, count in hours_in_gap.items():
        print(f"  Hour {h:2d}: {count} bars")