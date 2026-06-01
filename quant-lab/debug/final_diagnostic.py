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

# The issue: Python runner groups by EST date, but Asian session (7PM-3AM EST) spans TWO EST dates
# When we group by EST date, we miss the 7PM-11PM EST portion which is in the PREVIOUS EST date

# Let's count how many EST days have incomplete Asian ranges
# (missing the 7PM-11PM portion)

est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

# For each EST day, check if it has bars at 7PM EST (midnight UTC)
# If not, it's missing the first part of the Asian session
missing_7pm = 0
has_7pm = 0
for dk, day_bars in est_days.items():
    has_7pm_est = any((b.timestamp.hour - 5) % 24 == 19 for b in day_bars)
    if has_7pm_est:
        has_7pm += 1
    else:
        missing_7pm += 1

print(f"EST days with 7PM EST bar (complete Asian start): {has_7pm}")
print(f"EST days missing 7PM EST bar (incomplete Asian start): {missing_7pm}")

# Now let's check the actual session count difference
# Python runner: 316 active sessions, 1046 NO-GO
# Nautilus-style: 735 active sessions, 384 NO-GO

# The difference is because:
# 1. Python runner misses the 7PM-11PM portion of Asian session for many days
# 2. This leads to incomplete Asian ranges
# 3. Incomplete Asian ranges are smaller, so more days are NO-GO

# Let's verify by computing Asian ranges with and without the 7PM portion
complete_ar_sum = 0
complete_ar_count = 0
incomplete_ar_sum = 0
incomplete_ar_count = 0

for dk, day_bars in est_days.items():
    ah, al = 0.0, 99999.0
    has_7pm_est = False
    
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
            if h == 19:
                has_7pm_est = True
    
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.1
    
    if has_7pm_est:
        complete_ar_sum += ar_pips
        complete_ar_count += 1
    else:
        incomplete_ar_sum += ar_pips
        incomplete_ar_count += 1

print(f"\nComplete Asian ranges (has 7PM): avg {complete_ar_sum / complete_ar_count:.1f} pips ({complete_ar_count} days)")
print(f"Incomplete Asian ranges (no 7PM): avg {incomplete_ar_sum / incomplete_ar_count:.1f} pips ({incomplete_ar_count} days)")

# Check tier distribution for complete vs incomplete
complete_tiers = {'T1': 0, 'T2': 0, 'T3': 0, 'NO_GO': 0}
incomplete_tiers = {'T1': 0, 'T2': 0, 'T3': 0, 'NO_GO': 0}

for dk, day_bars in est_days.items():
    ah, al = 0.0, 99999.0
    has_7pm_est = False
    
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
            if h == 19:
                has_7pm_est = True
    
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.1
    tier = "NO_GO"
    for t in ['T1', 'T2', 'T3']:
        if ar_pips <= xau_tiers[t]['ar_max']:
            tier = t
            break
    
    if has_7pm_est:
        complete_tiers[tier] += 1
    else:
        incomplete_tiers[tier] += 1

print(f"\nComplete Asian ranges tier distribution: {complete_tiers}")
print(f"Incomplete Asian ranges tier distribution: {incomplete_tiers}")

# The key insight: incomplete Asian ranges are smaller, so more are NO-GO
# This explains why Python runner has 1046 NO-GO vs Nautilus 384 NO-GO

# But wait, the Nautilus strategy uses EST date for day detection!
# Let me check if there's something else going on...

# Actually, looking at the Nautilus on_bar code:
# bar_date = self._ts_to_date(bar.ts_event, est_offset=-5)  # EST date
# This correctly uses EST date, so it should get the full Asian range

# The issue must be in how the Python runner processes bars
# Let me check the run() method again