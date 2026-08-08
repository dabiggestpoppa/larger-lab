import pandas as pd
import numpy as np
import os

# Check what extra bars exist
sym = 'EURGBP'
path = f'data/normalized/h1/{sym}_H1.parquet'
df = pd.read_parquet(path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
df = df.sort_values('timestamp_utc')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()

# Generate expected timestamps (no weekends, no holidays)
expected_common = pd.date_range(
    start=COMMON_START.floor('h'),
    end=COMMON_END.ceil('h'),
    freq='h',
    tz='UTC'
)
expected_common = expected_common[expected_common.weekday < 5]

FX_HOLIDAYS = [
    '2023-01-02', '2023-04-07', '2023-04-10', '2023-05-29', '2023-07-04', '2023-09-04', '2023-11-23', '2023-12-25',
    '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-27', '2024-07-04', '2024-09-02', '2024-11-28', '2024-12-25',
    '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-26', '2025-07-04', '2025-09-01', '2025-11-27', '2025-12-25',
    '2026-01-01', '2026-04-03', '2026-04-06', '2026-05-25',
]

holiday_timestamps = set()
for h in FX_HOLIDAYS:
    day_ts = pd.date_range(h, h + ' 23:00', freq='h', tz='UTC')
    holiday_timestamps.update(day_ts)

expected_common_no_holiday = expected_common[~expected_common.isin(holiday_timestamps)]

actual_ts = set(df_common['timestamp_utc'].values)
expected_ts = set(expected_common_no_holiday.values)

# Find extra bars (in actual but not in expected)
extra_ts = actual_ts - expected_ts
print(f"Extra timestamps: {len(extra_ts)}")

# Classify extra
for ts in sorted(extra_ts):
    ts_pd = pd.Timestamp(ts)
    if ts_pd.weekday() >= 5:
        print(f"  WEEKEND: {ts_pd}")
    elif ts_pd in holiday_timestamps:
        print(f"  HOLIDAY: {ts_pd}")
    else:
        print(f"  OTHER: {ts_pd}")

# Also check for duplicates
dupes = df_common[df_common.duplicated(subset=['timestamp_utc'], keep=False)]
print(f"\nDuplicate timestamps: {len(dupes)}")
if len(dupes) > 0:
    print(dupes[['timestamp_utc', 'open', 'high', 'low', 'close']].head(20))