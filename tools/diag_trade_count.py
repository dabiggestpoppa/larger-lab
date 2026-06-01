"""
XAUUSD Trade Count Diagnostic
==============================
Simulates the actual session logic to understand the 2.84x trade count discrepancy.
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

# Group by EST date (correct method - one session per EST day)
est_days = {}
for ts, row in df.iterrows():
    est_dt = ts + timedelta(hours=-5)
    est_date = est_dt.date()
    if est_date not in est_days:
        est_days[est_date] = []
    est_days[est_date].append(row)

# Group by UTC date (Nautilus method - multiple sessions per EST day possible)
utc_days = {}
for ts, row in df.iterrows():
    utc_date = ts.date()
    if utc_date not in utc_days:
        utc_days[utc_date] = []
    utc_days[utc_date].append(row)

# Count sessions that would be active
# EST method: one session per EST day
est_active_sessions = 0
for est_date, bars in est_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) != "NO_GO":
        est_active_sessions += 1

# UTC method: one session per UTC day, but Asian range is partial
# Each UTC day gets its own session with partial Asian range
utc_active_sessions = 0
for utc_date, bars in utc_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) != "NO_GO":
        utc_active_sessions += 1

print(f"\n=== Session Count Comparison ===")
print(f"EST active sessions: {est_active_sessions}")
print(f"UTC active sessions: {utc_active_sessions}")
print(f"Ratio (UTC/EST): {utc_active_sessions / est_active_sessions:.2f}x")

# Now let's count how many UTC days get partial Asian ranges
# that are still active (could explain the extra sessions)
print("\n=== Partial Session Analysis ===")

# For each EST day, check how many UTC days its Asian session spans
# and whether those UTC days would be active
partial_active_count = 0
for est_date, bars in est_days.items():
    ar_pips, ah, al = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) == "NO_GO":
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
        # This EST day spans multiple UTC days
        # Each UTC day would get its own partial session
        partial_active_count += len(asian_bars_utc_dates) - 1  # Extra sessions beyond the 1 EST session

print(f"Extra UTC sessions from split Asian ranges: {partial_active_count}")

# The real issue: UTC days with partial Asian ranges may still be active
# Let's count how many UTC days have partial Asian ranges that are active
utc_partial_active = 0
for utc_date, bars in utc_days.items():
    ar_pips, _, _ = calc_asian_range_pips(bars)
    if classify_tier(ar_pips) == "NO_GO":
        continue
    
    # Check if this UTC day has partial Asian session
    has_evening_asian = False
    has_morning_asian = False
    for item in bars:
        ts = item.name
        est_hour = (ts.hour - 5) % 24
        if est_hour >= 19:
            has_evening_asian = True
        elif est_hour < 3:
                has_morning_asian = True
    
    if not (has_evening_asian and has_morning_asian):
        utc_partial_active += 1

print(f"UTC days with partial Asian session that are active: {utc_partial_active}")

# Final analysis: How many total sessions does UTC method see?
print(f"\n=== Final Session Count ===")
print(f"EST method: {est_active_sessions} sessions (one per EST day)")
print(f"UTC method: {utc_active_sessions} sessions (one per UTC day)")
print(f"Difference: {utc_active_sessions - est_active_sessions} extra sessions")

# The 2.84x ratio suggests something else is happening
# Let's check if the issue is in how sessions are processed
print("\n=== Checking Session Processing Logic ===")

# In Nautilus: on_bar() initializes session at 3AM EST
# But the session is tracked per UTC day
# Let's simulate this

# Count how many times session would be initialized in Nautilus
nautilus_session_inits = 0
current_utc_date = None
asian_locked = False

for ts, row in df.iterrows():
    utc_date = ts.date()
    est_hour = (ts.hour - 5) % 24
    
    # Check for new UTC day
    if current_utc_date is None or utc_date != current_utc_date:
        current_utc_date = utc_date
        asian_locked = False
    
    # Check for 3AM EST (session init) - only first bar >= 3AM
    if not asian_locked and est_hour >= 3:
        # This would initialize a new session
        nautilus_session_inits += 1
        asian_locked = True

print(f"Nautilus session initializations (at 3AM EST): {nautilus_session_inits}")
print(f"Ratio to EST sessions: {nautilus_session_inits / est_active_sessions:.2f}x")