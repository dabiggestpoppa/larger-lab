"""
Compare Python load_m5_csv vs Nautilus BarDataWrangler output for XAUUSD.
Focus on: bar count, timestamp alignment, first/last bars per day.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/strategies')

from datetime import timedelta
from collections import defaultdict
from symmetry_trap_backtest import load_m5_csv

# Load with Python loader
py_bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
print(f"Python loader: {len(py_bars)} bars")

# Check timestamp of first few bars
print("\nFirst 10 bars (Python):")
for b in py_bars[:10]:
    print(f"  {b.timestamp} | O={b.open:.2f} H={b.high:.2f} L={b.low:.2f} C={b.close:.2f}")

# Check Nautilus-style timestamps (UTC nanoseconds)
# Nautilus BarDataWrangler processes DataFrame with UTC index
# The ts_event is the bar OPEN time in UTC nanoseconds
import pandas as pd
df = pd.read_csv('quant-lab/data/XAUUSD_M5.csv')
if 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
elif 'date' in df.columns:
    if 'time' in df.columns:
        df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
    else:
        df['timestamp'] = pd.to_datetime(df['date'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)

print(f"\nNautilus loader (DataFrame): {len(df)} rows")
print("\nFirst 10 bars (Nautilus DataFrame):")
for idx, row in df.head(10).iterrows():
    print(f"  {idx} | O={row.get('open', row.get('Open', 0)):.2f} H={row.get('high', row.get('High', 0)):.2f} L={row.get('low', row.get('Low', 0)):.2f} C={row.get('close', row.get('Close', 0)):.2f}")

# CRITICAL: Compare timestamps
print("\n=== TIMESTAMP COMPARISON ===")
print(f"Python bar[0]:  {py_bars[0].timestamp}")
print(f"Nautilus bar[0]: {df.index[0]}")
print(f"Python bar[-1]:  {py_bars[-1].timestamp}")
print(f"Nautilus bar[-1]: {df.index[-1]}")

# Check if Python timestamp is UTC or local
print(f"\nPython bar[0] hour (UTC): {py_bars[0].timestamp.hour}")
print(f"Nautilus bar[0] hour (UTC): {df.index[0].hour}")

# Compare bar counts per day (EST)
py_days = defaultdict(int)
for b in py_bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    py_days[dk] += 1

naut_days = defaultdict(int)
for idx in df.index:
    est_dt = idx + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    naut_days[dk] += 1

# Find mismatches
all_days = sorted(set(list(py_days.keys()) + list(naut_days.keys())))
mismatches = []
for dk in all_days:
    py_c = py_days.get(dk, 0)
    naut_c = naut_days.get(dk, 0)
    if py_c != naut_c:
        mismatches.append((dk, py_c, naut_c))

print(f"\n=== BAR COUNT PER DAY ===")
print(f"Python total days: {len(py_days)}")
print(f"Nautilus total days: {len(naut_days)}")
print(f"Days with mismatched bar counts: {len(mismatches)}")
if mismatches:
    print("First 20 mismatches:")
    for dk, py_c, naut_c in mismatches[:20]:
        print(f"  {dk}: Python={py_c}, Nautilus={naut_c}, diff={naut_c-py_c}")

# Check: does the Nautilus BarDataWrangler change the timestamps?
# Test: convert Python bar[0] timestamp to UTC nanoseconds
from datetime import timezone
py_ts_utc = py_bars[0].timestamp.replace(tzinfo=timezone.utc)
py_ns = int(py_ts_utc.timestamp() * 1e9)
naut_ns = int(df.index[0].timestamp() * 1e9)
print(f"\n=== UTC NANOSECOND COMPARISON ===")
print(f"Python ts_event (ns):  {py_ns}")
print(f"Nautilus ts_event (ns): {naut_ns}")
print(f"Match: {py_ns == naut_ns}")
