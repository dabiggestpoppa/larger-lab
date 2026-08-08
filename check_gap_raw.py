import pandas as pd
import numpy as np
import os

# Check raw M5 data for EURGBP around the gap period
sym = 'EURGBP'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)
df['timestamp'] = pd.to_datetime(df['time'], utc=True)
df = df.sort_values('timestamp')

# Check around the gap start: 2023-07-07 20:00
gap_start = pd.Timestamp('2023-07-07 20:00:00', tz='UTC')
gap_end = pd.Timestamp('2026-05-15 23:00:00', tz='UTC')

# Check a window around gap start
window_start = gap_start - pd.Timedelta(days=7)
window_end = gap_start + pd.Timedelta(days=7)

df_window = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= window_end)].copy()
print(f"Raw M5 rows around gap start: {len(df_window)}")
print(f"First: {df_window['timestamp'].min()}")
print(f"Last: {df_window['timestamp'].max()}")

if len(df_window) > 1:
    diffs = df_window['timestamp'].diff().dropna()
    unique_diffs = diffs.unique()
    print(f"Time diffs (minutes): {sorted([d.total_seconds()/60 for d in unique_diffs])[:20]}")

# Check if there are missing M5 bars
expected_m5 = pd.date_range(
    start=window_start.floor('5min'),
    end=window_end.ceil('5min'),
    freq='5min',
    tz='UTC'
)
expected_m5 = expected_m5[expected_m5.weekday < 5]

actual_m5 = set(df_window['timestamp'].values)
missing_m5 = set(expected_m5) - actual_m5
print(f"\nExpected M5 bars: {len(expected_m5)}")
print(f"Actual M5 bars: {len(actual_m5)}")
print(f"Missing M5 bars: {len(missing_m5)}")

# Check the gap end area
window_start2 = gap_end - pd.Timedelta(days=7)
window_end2 = gap_end + pd.Timedelta(days=7)

df_window2 = df[(df['timestamp'] >= window_start2) & (df['timestamp'] <= window_end2)].copy()
print(f"\nRaw M5 rows around gap end: {len(df_window2)}")
print(f"First: {df_window2['timestamp'].min()}")
print(f"Last: {df_window2['timestamp'].max()}")