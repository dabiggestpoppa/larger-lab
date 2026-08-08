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
        start=start.floor('H'),
        end=end.ceil('H'),
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
# These are approximate - in reality would need a proper trading calendar
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

# Classify gaps for each symbol
gap_classifications = []

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
    for ts in sorted(missing_ts):
        ts_pd = pd.Timestamp(ts)
        
        # Check if weekend
        if ts_pd.weekday() >= 5:
            category = 'weekend_closure'
        # Check if holiday
        elif ts_pd in holiday_timestamps:
            category = 'market_holiday'
        else:
            # Check if it's a weekday gap - need to see if it's part of a larger gap
            category = 'unexplained'
        
        gap_classifications.append({
            'symbol': sym,
            'missing_timestamp': ts_pd.isoformat(),
            'category': category,
            'weekday': ts_pd.weekday(),
            'hour': ts_pd.hour
        })

# Convert to DataFrame
gap_df = pd.DataFrame(gap_classifications)

# Now group consecutive unexplained gaps to find gap lengths
unexplained_gaps = gap_df[gap_df['category'] == 'unexplained'].copy()
unexplained_gaps['missing_timestamp'] = pd.to_datetime(unexplained_gaps['missing_timestamp'])

# For each symbol, find consecutive unexplained gaps
gap_summary = []

for sym in symbols:
    sym_gaps = unexplained_gaps[unexplained_gaps['symbol'] == sym].sort_values('missing_timestamp')
    
    if len(sym_gaps) == 0:
        continue
    
    # Group consecutive hours
    sym_gaps['time_diff'] = sym_gaps['missing_timestamp'].diff().dt.total_seconds() / 3600
    sym_gaps['gap_group'] = (sym_gaps['time_diff'] != 1).cumsum()
    
    for group_id, group in sym_gaps.groupby('gap_group'):
        gap_start = group['missing_timestamp'].min()
        gap_end = group['missing_timestamp'].max()
        gap_hours = len(group)
        
        gap_summary.append({
            'symbol': sym,
            'gap_start': gap_start.isoformat(),
            'gap_end': gap_end.isoformat(),
            'gap_hours': int(gap_hours),
            'category': 'unexplained'
        })

gap_summary_df = pd.DataFrame(gap_summary)

# Count gaps by size
for sym in symbols:
    sym_gaps = gap_summary_df[gap_summary_df['symbol'] == sym]
    gt_2h = len(sym_gaps[sym_gaps['gap_hours'] > 2])
    gt_6h = len(sym_gaps[sym_gaps['gap_hours'] > 6])
    gt_24h = len(sym_gaps[sym_gaps['gap_hours'] > 24])
    print(f"{sym}: gaps>2h={gt_2h}, gaps>6h={gt_6h}, gaps>24h={gt_24h}")

# Save gap classification
os.makedirs('artifacts/audits', exist_ok=True)
gap_df.to_csv('artifacts/audits/p2_gap_classification.csv', index=False)

# Save summary
summary = {
    'target_window': {
        'start': TARGET_START.isoformat(),
        'end': TARGET_END.isoformat(),
        'expected_hours': len(expected_target)
    },
    'common_window': {
        'start': COMMON_START.isoformat(),
        'end': COMMON_END.isoformat(),
        'expected_hours': len(expected_common)
    },
    'holiday_hours_excluded': len(holiday_timestamps),
    'gap_categories': gap_df['category'].value_counts().to_dict(),
    'unexplained_gaps_by_symbol': gap_summary_df.groupby('symbol').agg(
        total_gaps=('gap_hours', 'count'),
        total_missing_hours=('gap_hours', 'sum'),
        gaps_gt_2h=('gap_hours', lambda x: (x > 2).sum()),
        gaps_gt_6h=('gap_hours', lambda x: (x > 6).sum()),
        gaps_gt_24h=('gap_hours', lambda x: (x > 24).sum()),
        max_gap_hours=('gap_hours', 'max')
    ).to_dict('index')
}

with open('artifacts/audits/p2_gap_classification_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nGap classification saved:")
print("  artifacts/audits/p2_gap_classification.csv")
print("  artifacts/audits/p2_gap_classification_summary.json")