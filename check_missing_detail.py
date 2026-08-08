import pandas as pd
import numpy as np
import os

# Check the actual missing hours in common window for EURGBP, EURJPY, EURCHF
symbols = ['EURGBP', 'EURJPY', 'EURCHF']

COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

# Generate expected FX H1 timestamps (weekdays only)
expected_common = pd.date_range(
    start=COMMON_START.floor('h'),
    end=COMMON_END.ceil('h'),
    freq='h',
    tz='UTC'
)
expected_common = expected_common[expected_common.weekday < 5]

# Known FX holidays
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

# Exclude holidays from expected
expected_common_no_holiday = expected_common[~expected_common.isin(holiday_timestamps)]

print(f"Expected common hours (no weekends): {len(expected_common)}")
print(f"Expected common hours (no weekends, no holidays): {len(expected_common_no_holiday)}")

for sym in symbols:
    path = f'data/normalized/h1/{sym}_H1.parquet'
    df = pd.read_parquet(path)
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df = df.sort_values('timestamp_utc')
    
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()
    actual_ts = set(df_common['timestamp_utc'].values)
    expected_ts = set(expected_common_no_holiday.values)
    
    missing_ts = expected_ts - actual_ts
    
    print(f"\n{sym}:")
    print(f"  Actual rows: {len(df_common)}")
    print(f"  Expected hours: {len(expected_ts)}")
    print(f"  Missing hours: {len(missing_ts)}")
    print(f"  Coverage: {len(actual_ts & expected_ts) / len(expected_ts) * 100:.2f}%")
    
    # Classify missing
    missing_classified = []
    for ts in sorted(missing_ts):
        ts_pd = pd.Timestamp(ts)
        if ts_pd.weekday() >= 5:
            category = 'weekend_closure'
        elif ts_pd in holiday_timestamps:
            category = 'market_holiday'
        else:
            category = 'unexplained'
        missing_classified.append({'timestamp': ts_pd, 'category': category})
    
    if missing_classified:
        mc_df = pd.DataFrame(missing_classified)
        mc_df['category_change'] = (mc_df['category'] != mc_df['category'].shift()).cumsum()
        
        for cat, group in mc_df.groupby('category_change'):
            cat_name = group['category'].iloc[0]
            start_ts = group['timestamp'].min()
            end_ts = group['timestamp'].max()
            hours = len(group)
            
            if cat_name == 'unexplained' and hours > 0:
                print(f"  {cat_name} gap: {start_ts} to {end_ts} ({hours}h)")
            elif cat_name == 'market_holiday' and hours > 0:
                print(f"  {cat_name}: {start_ts} to {end_ts} ({hours}h)")