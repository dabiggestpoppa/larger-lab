import pandas as pd
import numpy as np
import os

# Check raw M5 data for weekend/holiday bars
sym = 'EURGBP'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)

# Parse timestamps
df['timestamp'] = pd.to_datetime(df['time'], utc=True)
df = df.sort_values('timestamp')

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

df_common = df[(df['timestamp'] >= COMMON_START) & (df['timestamp'] <= COMMON_END)].copy()

print(f"Raw M5 rows in common window: {len(df_common)}")

# Check for weekend bars
weekend_bars = df_common[df_common['timestamp'].dt.weekday >= 5]
print(f"Weekend M5 bars: {len(weekend_bars)}")

# Check for holiday bars
FX_HOLIDAYS = [
    '2023-01-02', '2023-04-07', '2023-04-10', '2023-05-29', '2023-07-04', '2023-09-04', '2023-11-23', '2023-12-25',
    '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-27', '2024-07-04', '2024-09-02', '2024-11-28', '2024-12-25',
    '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-26', '2025-07-04', '2025-09-01', '2025-11-27', '2025-12-25',
    '2026-01-01', '2026-04-03', '2026-04-06', '2026-05-25',
]

holiday_timestamps = set()
for h in FX_HOLIDAYS:
    day_ts = pd.date_range(h, h + ' 23:55', freq='5min', tz='UTC')
    holiday_timestamps.update(day_ts)

holiday_bars = df_common[df_common['timestamp'].isin(holiday_timestamps)]
print(f"Holiday M5 bars: {len(holiday_bars)}")

# Now check what happens when we resample M5 to H1
# The resampling will aggregate weekend/holiday M5 bars into H1 bars
# This creates extra H1 bars that shouldn't exist in trading hours

# Let's simulate the resampling
df_resample = df_common.set_index('timestamp')
ohlc_dict = {
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}

df_h1 = df_resample.resample('1H').agg(ohlc_dict).dropna()
df_h1 = df_h1.reset_index()

print(f"\nResampled H1 bars: {len(df_h1)}")

# Check which H1 bars are weekend/holiday
weekend_h1 = df_h1[df_h1['timestamp'].dt.weekday >= 5]
print(f"Weekend H1 bars: {len(weekend_h1)}")

holiday_h1 = df_h1[df_h1['timestamp'].isin(holiday_timestamps)]
print(f"Holiday H1 bars: {len(holiday_h1)}")

# Expected trading H1 bars (no weekends, no holidays)
expected_h1 = pd.date_range(
    start=COMMON_START.floor('h'),
    end=COMMON_END.ceil('h'),
    freq='h',
    tz='UTC'
)
expected_h1 = expected_h1[expected_h1.weekday < 5]
expected_h1 = expected_h1[~expected_h1.isin(holiday_timestamps)]

print(f"\nExpected trading H1 bars: {len(expected_h1)}")
print(f"Actual H1 bars (all): {len(df_h1)}")
print(f"Extra H1 bars: {len(df_h1) - len(expected_h1)}")