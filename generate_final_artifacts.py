import pandas as pd
import numpy as np
import os
import json
import hashlib
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

# Generate expected FX H1 timestamps (weekdays only, excluding late Friday hours)
def get_expected_fx_timestamps(start, end):
    """Generate expected FX H1 timestamps excluding weekends and late Friday hours."""
    timestamps = pd.date_range(
        start=start.floor('h'),
        end=end.ceil('h'),
        freq='h',
        tz='UTC'
    )
    # Filter out weekends (Saturday=5, Sunday=6)
    timestamps = timestamps[timestamps.weekday < 5]
    # Filter out late Friday hours (21:00, 22:00, 23:00 UTC) - FX market closes ~21:00 UTC Friday
    friday_late_mask = (timestamps.weekday == 4) & (timestamps.hour >= 21)
    timestamps = timestamps[~friday_late_mask]
    return timestamps

expected_target = get_expected_fx_timestamps(TARGET_START, TARGET_END)
expected_common = get_expected_fx_timestamps(COMMON_START, COMMON_END)

# Known FX holidays
FX_HOLIDAYS = [
    '2022-01-01', '2022-04-15', '2022-04-18', '2022-05-30', '2022-07-04', '2022-09-05', '2022-11-24', '2022-12-26',
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
expected_target_no_holiday = expected_target[~expected_target.isin(holiday_timestamps)]
expected_common_no_holiday = expected_common[~expected_common.isin(holiday_timestamps)]

print(f"Target window expected hours (no weekends, no late Friday, no holidays): {len(expected_target_no_holiday)}")
print(f"Common window expected hours (no weekends, no late Friday, no holidays): {len(expected_common_no_holiday)}")

# Calculate per-symbol metrics
results = {}
for sym in symbols:
    df = all_dfs[sym].copy()
    df = df.sort_values('timestamp_utc')
    
    # Filter to target window
    df_target = df[(df['timestamp_utc'] >= TARGET_START) & (df['timestamp_utc'] <= TARGET_END)].copy()
    actual_ts = set(df_target['timestamp_utc'].values)
    expected_ts = set(expected_target_no_holiday.values)
    
    target_expected_hours = len(expected_ts)
    actual_valid_hours = len(actual_ts & expected_ts)
    missing_hours = target_expected_hours - actual_valid_hours
    coverage_pct = (actual_valid_hours / target_expected_hours * 100) if target_expected_hours > 0 else 0
    
    # Common window
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)].copy()
    actual_common_ts = set(df_common['timestamp_utc'].values)
    expected_common_ts = set(expected_common_no_holiday.values)
    
    common_expected_hours = len(expected_common_ts)
    common_actual_hours = len(actual_common_ts & expected_common_ts)
    common_missing_hours = common_expected_hours - common_actual_hours
    common_coverage_pct = (common_actual_hours / common_expected_hours * 100) if common_expected_hours > 0 else 0
    
    # Gap analysis for unexplained gaps
    missing_ts = expected_ts - actual_ts
    missing_classified = []
    for ts in sorted(missing_ts):
        ts_pd = pd.Timestamp(ts)
        if ts_pd.weekday() >= 5:
            category = 'weekend_closure'
        elif ts_pd in holiday_timestamps:
            category = 'market_holiday'
        elif ts_pd.weekday() == 4 and ts_pd.hour >= 21:
            category = 'friday_late_close'
        else:
            category = 'unexplained'
        missing_classified.append({'timestamp': ts_pd, 'category': category})
    
    # Group unexplained gaps
    unexplained_gaps = []
    if missing_classified:
        mc_df = pd.DataFrame(missing_classified)
        mc_df = mc_df[mc_df['category'] == 'unexplained']
        if len(mc_df) > 0:
            mc_df['time_diff'] = mc_df['timestamp'].diff().dt.total_seconds() / 3600
            mc_df['gap_group'] = (mc_df['time_diff'] != 1).cumsum()
            
            for group_id, group in mc_df.groupby('gap_group'):
                gap_start = group['timestamp'].min()
                gap_end = group['timestamp'].max()
                gap_hours = len(group)
                unexplained_gaps.append({
                    'start': gap_start.isoformat(),
                    'end': gap_end.isoformat(),
                    'hours': int(gap_hours)
                })
    
    gaps_gt_2h = len([g for g in unexplained_gaps if g['hours'] > 2])
    gaps_gt_6h = len([g for g in unexplained_gaps if g['hours'] > 6])
    gaps_gt_24h = len([g for g in unexplained_gaps if g['hours'] > 24])
    
    # Quality metrics
    duplicate_count = df_target.duplicated(subset=['timestamp_utc']).sum()
    
    malformed = 0
    for _, row in df_target.iterrows():
        if row['high'] < row['low'] or row['open'] > row['high'] or row['open'] < row['low'] or row['close'] > row['high'] or row['close'] < row['low']:
            malformed += 1
    
    stale = df_target.duplicated(subset=['open', 'high', 'low', 'close'], keep=False).sum()
    
    # Raw file info
    raw_path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    raw_sha256 = None
    if os.path.exists(raw_path):
        sha256 = hashlib.sha256()
        with open(raw_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        raw_sha256 = sha256.hexdigest()
    
    norm_path = f'data/normalized/h1/{sym}_H1.parquet'
    norm_sha256 = None
    if os.path.exists(norm_path):
        sha256 = hashlib.sha256()
        with open(norm_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        norm_sha256 = sha256.hexdigest()
    
    results[sym] = {
        'symbol': sym,
        'first_timestamp': df['timestamp_utc'].min().isoformat(),
        'last_timestamp': df['timestamp_utc'].max().isoformat(),
        'row_count': len(df),
        'row_count_in_target': len(df_target),
        'row_count_in_common': len(df_common),
        'provider': 'mt5_pro',
        'raw_source_path': raw_path,
        'raw_sha256': raw_sha256,
        'normalized_sha256': norm_sha256,
        'target_expected_hours': int(target_expected_hours),
        'target_actual_hours': int(actual_valid_hours),
        'target_missing_hours': int(missing_hours),
        'target_coverage_pct': round(coverage_pct, 2),
        'common_expected_hours': int(common_expected_hours),
        'common_actual_hours': int(common_actual_hours),
        'common_missing_hours': int(common_missing_hours),
        'common_coverage_pct': round(common_coverage_pct, 2),
        'gaps_gt_2h': int(gaps_gt_2h),
        'gaps_gt_6h': int(gaps_gt_6h),
        'gaps_gt_24h': int(gaps_gt_24h),
        'unexplained_gaps': unexplained_gaps,
        'duplicate_count': int(duplicate_count),
        'malformed_ohlc_count': int(malformed),
        'stale_bar_count': int(stale),
        'timezone': 'UTC',
        'price_side': 'bid'
    }
    
    print(f"\n{sym}:")
    print(f"  Target coverage: {coverage_pct:.2f}% ({actual_valid_hours}/{target_expected_hours})")
    print(f"  Common coverage: {common_coverage_pct:.2f}% ({common_actual_hours}/{common_expected_hours})")
    print(f"  Gaps >2h: {gaps_gt_2h}, >6h: {gaps_gt_6h}, >24h: {gaps_gt_24h}")
    print(f"  Duplicates: {duplicate_count}, Malformed: {malformed}, Stale: {stale}")

# Common intersection
common_ts_sets = []
for sym in symbols:
    df = all_dfs[sym].copy()
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)]
    common_ts_sets.append(set(df_common['timestamp_utc'].values))

intersection_ts = set.intersection(*common_ts_sets)
intersection_ts = intersection_ts & set(expected_common_no_holiday.values)
intersection_hours = len(intersection_ts)
intersection_coverage_pct = (intersection_hours / len(expected_common_no_holiday) * 100) if len(expected_common_no_holiday) > 0 else 0

print(f"\nIntersection coverage: {intersection_coverage_pct:.2f}% ({intersection_hours}/{len(expected_common_no_holiday)})")

# Per-symbol coverage in common window
per_symbol_coverage = {}
for sym in symbols:
    df = all_dfs[sym].copy()
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df_common = df[(df['timestamp_utc'] >= COMMON_START) & (df['timestamp_utc'] <= COMMON_END)]
    actual_in_common = set(df_common['timestamp_utc'].values) & set(expected_common_no_holiday.values)
    cov = len(actual_in_common) / len(expected_common_no_holiday) * 100 if len(expected_common_no_holiday) > 0 else 0
    per_symbol_coverage[sym] = round(cov, 2)

# Save batch_a_coverage_v3.json
coverage_v3 = {
    'target_window': {
        'start': TARGET_START.isoformat(),
        'end': TARGET_END.isoformat(),
        'expected_hours_no_weekends_late_friday_holidays': len(expected_target_no_holiday)
    },
    'common_window': {
        'start': COMMON_START.isoformat(),
        'end': COMMON_END.isoformat(),
        'expected_hours_no_weekends_late_friday_holidays': len(expected_common_no_holiday),
        'intersection_hours': int(intersection_hours),
        'intersection_coverage_pct': round(intersection_coverage_pct, 2),
        'per_symbol_coverage': per_symbol_coverage
    },
    'symbols': results
}

os.makedirs('data/manifests', exist_ok=True)
with open('data/manifests/batch_a_coverage_v3.json', 'w') as f:
    json.dump(coverage_v3, f, indent=2)

# Save batch_a_common_window_v2.json
common_window_v2 = {
    'common_start': COMMON_START.isoformat(),
    'common_end': COMMON_END.isoformat(),
    'symbols': symbols,
    'expected_common_hours': len(expected_common_no_holiday),
    'intersection_hours': int(intersection_hours),
    'intersection_coverage_pct': round(intersection_coverage_pct, 2),
    'per_symbol_coverage': per_symbol_coverage
}

with open('data/manifests/batch_a_common_window_v2.json', 'w') as f:
    json.dump(common_window_v2, f, indent=2)

# Save p2_data_quality_by_symbol_v3.csv
quality_rows = []
for sym in symbols:
    r = results[sym]
    quality_rows.append({
        'symbol': sym,
        'target_coverage_pct': r['target_coverage_pct'],
        'common_coverage_pct': r['common_coverage_pct'],
        'target_expected_hours': r['target_expected_hours'],
        'target_actual_hours': r['target_actual_hours'],
        'common_expected_hours': r['common_expected_hours'],
        'common_actual_hours': r['common_actual_hours'],
        'gaps_gt_2h': r['gaps_gt_2h'],
        'gaps_gt_6h': r['gaps_gt_6h'],
        'gaps_gt_24h': r['gaps_gt_24h'],
        'duplicate_count': r['duplicate_count'],
        'malformed_ohlc_count': r['malformed_ohlc_count'],
        'stale_bar_count': r['stale_bar_count'],
        'raw_sha256': r['raw_sha256'],
        'normalized_sha256': r['normalized_sha256']
    })

quality_df = pd.DataFrame(quality_rows)
quality_df.to_csv('artifacts/audits/p2_data_quality_by_symbol_v3.csv', index=False)

print("\nFiles saved:")
print("  data/manifests/batch_a_coverage_v3.json")
print("  data/manifests/batch_a_common_window_v2.json")
print("  artifacts/audits/p2_data_quality_by_symbol_v3.csv")