import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

xau_tiers = {
    'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
    'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
    'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0},
}

# ROOT CAUSE ANALYSIS
# ===================
# The Asian session (7PM-3AM EST) spans TWO EST dates:
# - 7PM-11PM EST on day N (belongs to EST date N)
# - 12AM-3AM EST on day N+1 (belongs to EST date N+1)
#
# Python runner groups by EST date, so it misses the 7PM-11PM portion
# when computing the Asian range for day N+1.
#
# Nautilus processes sequentially, so it accumulates the full Asian range
# across the day boundary.

# Let's verify by computing the Asian range for EST date 2022-01-19
# using both methods

# Method 1: Python runner (only bars with EST date 2022-01-19)
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

day_bars = est_days['2022-01-19']
ah1, al1 = 0.0, 99999.0
for b in day_bars:
    h = (b.timestamp.hour - 5) % 24
    if h >= 19 or h < 3:
        ah1 = max(ah1, b.high)
        al1 = min(al1, b.low)

ar1 = (ah1 - al1) / 0.1 if ah1 > 0 and al1 < 99999 else 0
print(f"Python runner Asian range for EST 2022-01-19: {ar1:.1f} pips")
print(f"  (Only has bars at 12AM-3AM EST, missing 7PM-11PM EST from 01-18)")

# Method 2: Nautilus-style (accumulated across day boundary)
# Find all bars that belong to the Asian session for EST date 2022-01-19
asian_bars = []
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_date = est.strftime('%Y-%m-%d')
    est_hour = est.hour
    
    # Asian session for EST date 2022-01-19:
    # - Bars with EST date 2022-01-18 and hour >= 19 (7PM-11PM)
    # - Bars with EST date 2022-01-19 and hour < 3 (12AM-3AM)
    if (est_date == '2022-01-18' and est_hour >= 19) or (est_date == '2022-01-19' and est_hour < 3):
        asian_bars.append(bar)

ah2, al2 = 0.0, 99999.0
for bar in asian_bars:
    ah2 = max(ah2, bar.high)
    al2 = min(al2, bar.low)

ar2 = (ah2 - al2) / 0.1 if ah2 > 0 and al2 < 99999 else 0
print(f"\nNautilus-style Asian range for EST 2022-01-19: {ar2:.1f} pips")
print(f"  (Has bars at both 7PM-11PM EST 01-18 and 12AM-3AM EST 01-19)")

# The difference
print(f"\nDifference: {ar2 - ar1:.1f} pips")

# Now let's count how many days are affected
print("\n=== Days affected by this issue ===")

# Count days where the Python runner's Asian range differs from Nautilus-style
diff_count = 0
same_count = 0
for dk in sorted(est_days.keys())[1:]:  # Skip first day (no previous day to accumulate)
    day_bars = est_days[dk]
    
    # Python runner's Asian range
    ah1, al1 = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah1 = max(ah1, b.high)
            al1 = min(al1, b.low)
    ar1 = (ah1 - al1) / 0.1 if ah1 > 0 and al1 < 99999 else 0
    
    # Nautilus-style Asian range (accumulated from previous day)
    # This requires checking bars from the previous EST date
    prev_dk = (day_bars[0].timestamp + timedelta(hours=-5)).replace(hour=0, minute=0, second=0)
    prev_dk = prev_dk - timedelta(days=1)
    prev_dk_str = prev_dk.strftime('%Y-%m-%d')
    
    # Find Asian bars from previous day (7PM-11PM EST)
    prev_asian_bars = []
    for b in bars:
        est = b.timestamp + timedelta(hours=-5)
        if est.strftime('%Y-%m-%d') == prev_dk_str and est.hour >= 19:
            prev_asian_bars.append(b)
    
    # Combine with current day's Asian bars (12AM-3AM EST)
    ah2, al2 = ah1, al1
    for b in prev_asian_bars:
        ah2 = max(ah2, b.high)
        al2 = min(al2, b.low)
    ar2 = (ah2 - al2) / 0.1 if ah2 > 0 and al2 < 99999 else 0
    
    if abs(ar2 - ar1) > 1:  # Significant difference
        diff_count += 1
    else:
        same_count += 1

print(f"Days with different Asian ranges: {diff_count}")
print(f"Days with same Asian ranges: {same_count}")

# The fix: The Python runner should accumulate Asian range across day boundaries
# OR use a different grouping method that accounts for the Asian session spanning days