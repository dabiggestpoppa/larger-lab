import pandas as pd
import os
import hashlib
import json
from datetime import datetime, timedelta
import numpy as np

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

# Target window: 2022-01-01 00:00 UTC through latest common timestamp
TARGET_START = pd.Timestamp('2022-01-01 00:00:00', tz='UTC')

# Load all normalized files and find common end
all_dfs = {}
for sym in symbols:
    path = f'data/normalized/h1/{sym}_H1.parquet'
    df = pd.read_parquet(path)
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    all_dfs[sym] = df

# Find latest common timestamp (minimum of all last timestamps)
last_timestamps = {sym: df['timestamp_utc'].max() for sym, df in all_dfs.items()}
TARGET_END = min(last_timestamps.values())
print(f"Target window: {TARGET_START} to {TARGET_END}")

# Generate expected FX H1 timestamps (excluding weekends)
# FX market: Sunday 22:00 UTC (Monday 00:00 Sydney) to Friday 22:00 UTC (Saturday 00:00 New York)
# But H1 bars are typically 00:00-23:00 UTC Monday-Friday
# Let's generate all hourly timestamps and filter out weekends

expected_timestamps = pd.date_range(
    start=TARGET_START.floor('H'),
    end=TARGET_END.ceil('H'),
    freq='H',
    tz='UTC'
)

# Filter out weekends (Saturday=5, Sunday=6)
weekday_mask = expected_timestamps.weekday < 5
expected_fx_timestamps = expected_timestamps[weekday_mask]

print(f"Expected FX H1 timestamps in target window: {len(expected_fx_timestamps)}")

# Calculate per-symbol metrics
results = {}
for sym in symbols:
    df = all_dfs[sym].copy()
    df = df.sort_values('timestamp_utc')
    
    # Filter to target window
    df_window = df[(df['timestamp_utc'] >= TARGET_START) & (df['timestamp_utc'] <= TARGET_END)].copy()
    
    # Get actual timestamps in window
    actual_ts = set(df_window['timestamp_utc'].values)
    expected_ts = set(expected_fx_timestamps.values)
    
    # Coverage metrics
    target_expected_hours = len(expected_ts)
    actual_valid_hours = len(actual_ts & expected_ts)
    missing_hours = target_expected_hours - actual_valid_hours
    coverage_pct = (actual_valid_hours / target_expected_hours * 100) if target_expected_hours > 0 else 0
    
    # Gap analysis
    sorted_actual = sorted(actual_ts & expected_ts)
    gaps = []
    for i in range(1, len(sorted_actual)):
        gap = sorted_actual[i] - sorted_actual[i-1]
        gap_hours = gap / np.timedelta64(1, 'h')
        if gap_hours > 1:  # More than 1 hour gap
            gaps.append(gap_hours)
    
    longest_gap_hours = max(gaps) if gaps else 0
    gaps_gt_2h = sum(1 for g in gaps if g > 2)
    gaps_gt_6h = sum(1 for g in gaps if g > 6)
    gaps_gt_24h = sum(1 for g in gaps if g > 24)
    
    # Quality metrics
    duplicate_count = df_window.duplicated(subset=['timestamp_utc']).sum()
    
    # Malformed OHLC: high < low or open/close outside high/low
    malformed = 0
    for _, row in df_window.iterrows():
        if row['high'] < row['low'] or row['open'] > row['high'] or row['open'] < row['low'] or row['close'] > row['high'] or row['close'] < row['low']:
            malformed += 1
    malformed_ohlc_count = malformed
    
    # Stale bars: identical OHLC
    stale = df_window.duplicated(subset=['open', 'high', 'low', 'close'], keep=False).sum()
    stale_bar_count = stale
    
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
        'row_count_in_window': len(df_window),
        'provider': 'mt5_pro',
        'raw_source_path': raw_path,
        'raw_sha256': raw_sha256,
        'normalized_sha256': norm_sha256,
        'target_expected_hours': int(target_expected_hours),
        'actual_valid_hours': int(actual_valid_hours),
        'missing_hours': int(missing_hours),
        'coverage_pct': round(coverage_pct, 2),
        'longest_gap_hours': round(longest_gap_hours, 2),
        'gaps_gt_2h': int(gaps_gt_2h),
        'gaps_gt_6h': int(gaps_gt_6h),
        'gaps_gt_24h': int(gaps_gt_24h),
        'duplicate_count': int(duplicate_count),
        'malformed_ohlc_count': int(malformed_ohlc_count),
        'stale_bar_count': int(stale_bar_count),
        'timezone': 'UTC',
        'price_side': 'bid'
    }
    
    print(f"\n{sym}:")
    print(f"  Coverage: {coverage_pct:.2f}% ({actual_valid_hours}/{target_expected_hours})")
    print(f"  Longest gap: {longest_gap_hours:.1f}h")
    print(f"  Gaps >2h: {gaps_gt_2h}, >6h: {gaps_gt_6h}, >24h: {gaps_gt_24h}")
    print(f"  Duplicates: {duplicate_count}, Malformed: {malformed_ohlc_count}, Stale: {stale_bar_count}")

# Common intersection
common_start = max(pd.Timestamp(r['first_timestamp']) for r in results.values())
common_end = min(pd.Timestamp(r['last_timestamp']) for r in results.values())

print(f"\nCommon window: {common_start} to {common_end}")

# Expected timestamps in common window
common_expected = pd.date_range(
    start=common_start.floor('H'),
    end=common_end.ceil('H'),
    freq='H',
    tz='UTC'
)
common_expected = common_expected[common_expected.weekday < 5]
expected_common_hours = len(common_expected)

# Intersection: timestamps present in ALL symbols
common_ts_sets = []
for sym in symbols:
    df = all_dfs[sym].copy()
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df_window = df[(df['timestamp_utc'] >= common_start) & (df['timestamp_utc'] <= common_end)]
    common_ts_sets.append(set(df_window['timestamp_utc'].values))

intersection_ts = set.intersection(*common_ts_sets)
intersection_ts = intersection_ts & set(common_expected.values)
intersection_hours = len(intersection_ts)
intersection_coverage_pct = (intersection_hours / expected_common_hours * 100) if expected_common_hours > 0 else 0

print(f"Expected common hours: {expected_common_hours}")
print(f"Intersection hours: {intersection_hours}")
print(f"Intersection coverage: {intersection_coverage_pct:.2f}%")

# Per-symbol coverage in common window
per_symbol_coverage = {}
for sym in symbols:
    df = all_dfs[sym].copy()
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    df_window = df[(df['timestamp_utc'] >= common_start) & (df['timestamp_utc'] <= common_end)]
    actual_in_common = set(df_window['timestamp_utc'].values) & set(common_expected.values)
    cov = len(actual_in_common) / expected_common_hours * 100 if expected_common_hours > 0 else 0
    per_symbol_coverage[sym] = round(cov, 2)

# Excluded timestamps (weekend bars in data)
excluded_count = 0
for sym in symbols:
    df = all_dfs[sym].copy()
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
    weekend_bars = df[df['timestamp_utc'].dt.weekday >= 5]
    excluded_count += len(weekend_bars)

# Save batch_a_common_window.json
common_window = {
    'common_start': common_start.isoformat(),
    'common_end': common_end.isoformat(),
    'symbols': symbols,
    'expected_common_hours': int(expected_common_hours),
    'intersection_hours': int(intersection_hours),
    'intersection_coverage_pct': round(intersection_coverage_pct, 2),
    'per_symbol_coverage': per_symbol_coverage,
    'excluded_timestamps_count': int(excluded_count)
}

os.makedirs('data/manifests', exist_ok=True)
with open('data/manifests/batch_a_common_window.json', 'w') as f:
    json.dump(common_window, f, indent=2)

# Save batch_a_coverage_v2.json
coverage_v2 = {
    'target_window_start': TARGET_START.isoformat(),
    'target_window_end': TARGET_END.isoformat(),
    'symbols': results
}

with open('data/manifests/batch_a_coverage_v2.json', 'w') as f:
    json.dump(coverage_v2, f, indent=2)

print("\nFiles saved:")
print("  data/manifests/batch_a_common_window.json")
print("  data/manifests/batch_a_coverage_v2.json")