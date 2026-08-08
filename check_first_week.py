import pandas as pd
import numpy as np
import os

# Check the very beginning of common window for EURGBP
sym = 'EURGBP'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)
df['timestamp'] = pd.to_datetime(df['time'], utc=True)
df = df.sort_values('timestamp')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

# Check first week
week_end = COMMON_START + pd.Timedelta(days=7)
df_first_week = df[(df['timestamp'] >= COMMON_START) & (df['timestamp'] < week_end)].copy()

print(f"Raw M5 rows in first week: {len(df_first_week)}")
print(f"First: {df_first_week['timestamp'].min()}")
print(f"Last: {df_first_week['timestamp'].max()}")

if len(df_first_week) > 1:
    diffs = df_first_week['timestamp'].diff().dropna()
    unique_diffs = diffs.unique()
    print(f"Time diffs (minutes): {sorted([d.total_seconds()/60 for d in unique_diffs])[:20]}")

# Check expected M5 bars in first week
expected_m5 = pd.date_range(
    start=COMMON_START.floor('5min'),
    end=week_end.ceil('5min'),
    freq='5min',
    tz='UTC'
)
expected_m5 = expected_m5[expected_m5.weekday < 5]

actual_m5 = set(df_first_week['timestamp'].values)
missing_m5 = set(expected_m5) - actual_m5
print(f"\nExpected M5 bars in first week: {len(expected_m5)}")
print(f"Actual M5 bars in first week: {len(actual_m5)}")
print(f"Missing M5 bars in first week: {len(missing_m5)}")

# Check which hours are missing in first week
if missing_m5:
    missing_hours = pd.Series(list(missing_m5)).dt.hour.value_counts().sort_index()
    print(f"\nMissing hours in first week:")
    for h, count in missing_hours.items():
        print(f"  Hour {h:2d}: {count} missing bars")