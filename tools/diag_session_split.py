"""
XAUUSD Session Split Diagnostic
==============================
Analyzes how UTC vs EST day boundaries split the Asian session (19:00-03:00 EST)
and how this affects trade counts.
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load XAUUSD data
DATA_DIR = Path("quant-lab/data")
csv_path = DATA_DIR / "XAUUSD_M5.csv"

if not csv_path.exists():
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

# XAUUSD config
pip_divisor = 10.0
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

# Group by EST date (correct method)
est_days = {}
for ts, row in df.iterrows():
    est_dt = ts + timedelta(hours=-5)
    est_date = est_dt.date()
    if est_date not in est_days:
        est_days[est_date] = []
    est_days[est_date].append(row)

# Group by UTC date (Nautilus method)
utc_days = {}
for ts, row in df.iterrows():
    utc_date = ts.date()
    if utc_date not in utc_days:
        utc_days[utc_date] = []
    utc_days[utc_date].append(row)

# Analyze Asian session splitting
print("\n=== Asian Session Splitting Analysis ===")

# For each EST day, check how many UTC days its Asian session spans
split_count = 0
single_day_count = 0
for est_date, bars in est_days.items():
    ar_pips, ah, al = calc_asian_range_pips(bars)
    if ar_pips == 0:
        continue
    
    # Find which UTC days these bars belong to
    utc_dates_in_est_day = set()
    for item in bars:
        ts = item.name
        utc_dates_in_est_day.add(ts.date())
    
    # Check if Asian bars span multiple UTC days
    asian_bars_utc_dates = set()
    for item in bars:
        ts = item.name
        est_hour = (ts.hour - 5) % 24
        if est_hour >= 19 or est_hour < 3:
            asian_bars_utc_dates.add(ts.date())
    
    if len(asian_bars_utc_dates) > 1:
        split_count += 1
    else:
        single_day_count += 1

print(f"EST days with Asian session spanning multiple UTC days: {split_count}")
print(f"EST days with Asian session on single UTC day: {single_day_count}")

# Now simulate what happens with UTC grouping
# Each UTC day gets its own session, but Asian range may be incomplete
print("\n=== UTC Day Session Analysis ===")

# For each UTC day, calculate what Asian range it would see
utc_asian_complete = 0
utc_asian_partial = 0
utc_asian_none = 0

for utc_date, bars in utc_days.items():
    ar_pips, ah, al = calc_asian_range_pips(bars)
    if ar_pips == 0:
        utc_asian_none += 1
    else:
        # Check if this UTC day has full Asian session (both 19:00-24:00 AND 00:00-03:00 EST)
        has_evening_asian = False
        has_morning_asian = False
        for item in bars:
            ts = item.name
            est_hour = (ts.hour - 5) % 24
            if est_hour >= 19:
                has_evening_asian = True
            elif est_hour < 3:
                has_morning_asian = True
        
        if has_evening_asian and has_morning_asian:
            utc_asian_complete += 1
        else:
            utc_asian_partial += 1

print(f"UTC days with complete Asian session (both evening and morning): {utc_asian_complete}")
print(f"UTC days with partial Asian session: {utc_asian_partial}")
print(f"UTC days with no Asian session: {utc_asian_none}")

# Count active sessions
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

print(f"\n=== Active Session Counts ===")
print(f"Active EST sessions: {active_est}")
print(f"Active UTC sessions: {active_utc}")
print(f"Ratio (UTC/EST): {active_utc / active_est:.2f}x")

# The key insight: UTC days with partial Asian sessions may still be active
# but they're missing part of the Asian range, which could lead to different tier classification
print("\n=== Tier Distribution Comparison ===")

est_tiers = {"T1": 0, "T2": 0, "T3": 0, "NO_GO": 0}
utc_tiers = {"T1": 0, "T2": 0, "T3": 0, "NO_GO": 0}

for est_date, bars in est_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    tier = classify_tier(ar_pips)
    est_tiers[tier] += 1

for utc_date, bars in utc_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    tier = classify_tier(ar_pips)
    utc_tiers[tier] += 1

print("EST tier distribution:")
for t, c in est_tiers.items():
    print(f"  {t}: {c}")

print("UTC tier distribution:")
for t, c in utc_tiers.items():
    print(f"  {t}: {c}")