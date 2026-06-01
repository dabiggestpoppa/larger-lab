"""
XAUUSD Day Boundary Diagnostic
==============================
Tests the hypothesis that UTC vs EST day boundaries cause the 2.84x trade count discrepancy.

This script:
1. Loads the same CSV data
2. Groups bars by UTC date (Nautilus method)
3. Groups bars by EST date (Python method)
4. Compares Asian range calculations and session counts
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load XAUUSD data
DATA_DIR = Path("quant-lab/data")
csv_path = DATA_DIR / "XAUUSD_M5.csv"

if not csv_path.exists():
    # Try alternate names
    for alt in ["XAUUSD.csv", "XAUUSD_MAD.csv", "XAUUSD_dt.csv"]:
        p = DATA_DIR / alt
        if p.exists():
            csv_path = p
            break

if not csv_path.exists():
    print("ERROR: No XAUUSD CSV found")
    exit(1)

print(f"Loading: {csv_path.name}")
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)

print(f"Total bars: {len(df)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")

# Method 1: UTC date grouping (Nautilus)
utc_days = {}
for ts, row in df.iterrows():
    utc_date = ts.date()  # UTC date
    if utc_date not in utc_days:
        utc_days[utc_date] = []
    utc_days[utc_date].append(row)

print(f"\n=== UTC Date Grouping (Nautilus Method) ===")
print(f"Total UTC days: {len(utc_days)}")

# Method 2: EST date grouping (Python)
est_days = {}
for ts, row in df.iterrows():
    est_dt = ts + timedelta(hours=-5)  # EST = UTC - 5
    est_date = est_dt.date()
    if est_date not in est_days:
        est_days[est_date] = []
    est_days[est_date].append(row)

print(f"\n=== EST Date Grouping (Python Method) ===")
print(f"Total EST days: {len(est_days)}")

# Compare Asian range calculations for first few days
print("\n=== Sample Day Comparison ===")

# XAUUSD config
pip_divisor = 10.0  # XAUUSD
tier_config = {
    "T1": {"ar_max": 32.0, "au": 16.0, "trigger": 19.0},
    "T2": {"ar_max": 58.0, "au": 29.0, "trigger": 35.0},
    "T3": {"ar_max": 95.0, "au": 48.0, "trigger": 58.0},
}

def classify_tier(ar_pips):
    for tier in ["T1", "T2", "T3"]:
        if ar_pips <= tier_config[tier]["ar_max"]:
            return tier
    return "NO_GO"

def calc_asian_range_pips(day_bars, est_offset=-5):
    """Calculate Asian range in pips (19:00-03:00 EST)."""
    ah, al = 0.0, 99999.0
    for item in day_bars:
        ts = item.name if hasattr(item, 'name') else item[0]
        row = item if hasattr(item, 'name') else item[1]
        est_hour = (ts.hour + est_offset) % 24
        if est_hour >= 19 or est_hour < 3:
            ah = max(ah, row['high'])
            al = min(al, row['low'])
    if ah <= 0 or al >= 99999:
        return 0.0, ah, al
    ar_pips = (ah - al) * pip_divisor
    return ar_pips, ah, al

# Compare first 5 EST days
sample_dates = sorted(est_days.keys())[:5]
for est_date in sample_dates:
    est_bars = est_days[est_date]  # Already a list
    ar_pips, ah, al = calc_asian_range_pips(est_bars)
    tier = classify_tier(ar_pips)
    
    # Find corresponding UTC day(s)
    utc_date = est_date + timedelta(days=1)  # EST day starts at 5AM UTC
    utc_bars = utc_days.get(utc_date, [])
    ar_pips_utc, ah_utc, al_utc = calc_asian_range_pips(utc_bars)
    tier_utc = classify_tier(ar_pips_utc)
    
    print(f"\nEST {est_date}:")
    print(f"  Bars: {len(est_bars)}, AR: {ar_pips:.1f}p, Tier: {tier}, AH: {ah:.5f}, AL: {al:.5f}")
    print(f"  UTC {utc_date}:")
    print(f"  Bars: {len(utc_bars)}, AR: {ar_pips_utc:.1f}p, Tier: {tier_utc}, AH: {ah_utc:.5f}, AL: {al_utc:.5f}")

# Count active sessions
print("\n=== Active Session Counts ===")
active_est = 0
active_utc = 0

for est_date, bars in est_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) != "NO_GO":
        active_est += 1

for utc_date, bars in utc_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) != "NO_GO":
        active_utc += 1

print(f"Active EST sessions: {active_est}")
print(f"Active UTC sessions: {active_utc}")
print(f"Ratio (UTC/EST): {active_utc / active_est:.2f}x")