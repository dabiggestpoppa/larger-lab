import pandas as pd
import numpy as np
import os

# Check the actual timestamps in first week
sym = 'EURGBP'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)
df['timestamp'] = pd.to_datetime(df['time'], utc=True)
df = df.sort_values('timestamp')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
week_end = COMMON_START + pd.Timedelta(days=7)

df_first_week = df[(df['timestamp'] >= COMMON_START) & (df['timestamp'] < week_end)].copy()

print(f"Raw M5 rows in first week: {len(df_first_week)}")
print(f"First 20 timestamps:")
for ts in df_first_week['timestamp'].head(20).values:
    print(f"  {ts}")
print(f"\nLast 20 timestamps:")
for ts in df_first_week['timestamp'].tail(20).values:
    print(f"  {ts}")

# Check the gap
if len(df_first_week) > 1:
    diffs = df_first_week['timestamp'].diff().dropna()
    large_gaps = diffs[diffs > pd.Timedelta(minutes=10)]
    print(f"\nLarge gaps (>10 min): {len(large_gaps)}")
    for i, gap in large_gaps.items():
        prev_ts = df_first_week.loc[i-1, 'timestamp']
        curr_ts = df_first_week.loc[i, 'timestamp']
        print(f"  Gap: {prev_ts} -> {curr_ts} ({gap.total_seconds()/60:.0f} min)")