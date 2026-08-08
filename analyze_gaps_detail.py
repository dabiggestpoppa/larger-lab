import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta

# Load all normalized files
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

all_dfs = {}
for sym in symbols:
    path = f'data/normalized/h1/{sym}_H1.parquet'
    df = pd.read_parquet(path)
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    all_dfs[sym] = df

# Target window
TARGET_START = pd.Timestamp('2022-01-01 00:00:00', tz='UTC')
TARGET_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

# Common window
COMMON_START = pd.Timestamp('2023-07-03 00:00:00', tz='UTC')
COMMON_END = pd.Timestamp('2026-05-21 18:00:00', tz='UTC')

# Generate expected FX H1 timestamps (weekdays only)
def get_expected_fx_timestamps(start, end):
    """Generate expected FX H1 timestamps excluding weekends."""
    timestamps = pd.date_range(
        start=start.floor('h'),
        end=end.ceil('h'),
        freq='h',
        tz='UTC'
    )
    # Filter out weekends (Saturday=5, Sunday=6)
    return timestamps[timestamps.weekday < 5]

expected_target = get_expected_fx_timestamps(TARGET_START, TARGET_END)
expected_common = get_expected_fx_timestamps(COMMON_START, COMMON_END)

print(f"Target window expected hours: {len(expected_target)}")
print(f"Common window expected hours: {len(expected_common)}")

# Known FX holidays (major ones that affect all pairs)
FX_HOLIDAYS = [
    # 2022
    '2022-01-01', '2022-04-15', '2022-04-18', '2022-05-30', '2022-07-04', '2022-09-05', '2022-11-24', '2022-12-26',
    # 2023
    '2023-01-02', '2023-04-07', '2023-04-10', '2023-05-29', '2023-07-04', '2023-09-04', '2023-11-23', '2023-12-25',
    # 2024
    '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-27', '2024-07-04', '2024-09-02', '2024-11-28', '2024-12-25',
    # 2025
    '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-26', '2025-07-04', '2025-09-01', '2025-11-27', '2025-12-25',
    # 2026
    '2026-01-01', '2026-04-03', '2026-04-06', '2026-05-25',
]

holiday_timestamps = set()
for h in FX_HOLIDAYS:
    day_ts = pd.date_range(h, h + ' 23:00', freq='h', tz='UTC')
    holiday_timestamps.update(day_ts)

print(f"Holiday hours to exclude: {len(holiday_timestamps)}")

# For each symbol, analyze missing intervals in detail
for sym in symbols:
    df = all_dfs[sym].copy()
    df = df.sort_values('timestamp_utc')
    
    # Filter to target window
    df_target = df[(df['timestamp_utc'] >= TARGET_START) & (df['timestamp_utc'] <= TARGET_END)].copy()
    actual_ts = set(df_target['timestamp_utc'].values)
    expected_ts = set(expected_target.values)
    
    # Find missing timestamps
    missing_ts = expected_ts - actual_ts
    
    # Classify each missing timestamp
    missing_classified = []
    for ts in sorted(missing_ts):
        ts_pd = pd.Timestamp(ts)
        
        # Check if weekend
        if ts_pd.weekday() >= 5:
            category = 'weekend_closure'
        # Check if holiday
        elif ts_pd in holiday_timestamps:
            category = 'market_holiday'
        else:
            category = 'unexplained'
        
        missing_classified.append({
            'timestamp': ts_pd,
            'category': category
        })
    
    # Group consecutive missing by category
    if missing_classified:
        mc_df = pd.DataFrame(missing_classified)
        mc_df['category_change'] = (mc_df['category'] != mc_df['category'].shift()).cumsum()
        
        for cat, group in mc_df.groupby('category_change'):
            cat_name = group['category'].iloc[0]
            start_ts = group['timestamp'].min()
            end_ts = group['timestamp'].max()
            hours = len(group)
            
            if cat_name == 'unexplained' and hours > 0:
                print(f"{sym}: {cat_name} gap {start_ts} to {end_ts} ({hours}h)")

print("\n--- Detailed analysis for EURGBP, EURJPY, EURCHF in common window ---")
for sym in ['EURGBP', 'EURJPY', 'EURCHF']:
    df = all_dfs[sym].copy()
    df = df.sort_values('timestamp_utc')
    
    # Filter to common window
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()
    actual_ts = set(df_common['timestamp_utc'].values)
    expected_ts = set(expected_common.values)
    
    missing_ts = expected_ts - actual_ts
    
    missing_classified = []
    for ts in sorted(missing_ts):
        ts_pd = pd.Timestamp(ts)
        
        if ts_pd.weekday() >= 5:
            category = 'weekend_closure'
        elif ts_pd in holiday_timestamps:
            category = 'market_holiday'
        else:
            category = 'unexplained'
        
        missing_classified.append({
            'timestamp': ts_pd,
            'category': category
        })
    
    if missing_classified:
        mc_df = pd.DataFrame(missing_classified)
        mc_df['category_change'] = (mc_df['category'] != mc_df['category'].shift()).cumsum()
        
        for cat, group in mc_df.groupby('category_change'):
            cat_name = group['category'].iloc[0]
            start_ts = group['timestamp'].min()
            end_ts = group['timestamp'].max()
            hours = len(group)
            
            if cat_name == 'unexplained' and hours > 0:
                print(f"{sym} COMMON: {cat_name} gap {start_ts} to {end_ts} ({hours}h)")