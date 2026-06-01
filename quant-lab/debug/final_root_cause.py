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

# The ROOT CAUSE:
# 1. Data has gaps - missing 12AM-3AM EST bars for many days
# 2. Python runner groups by EST date, so it misses the 7PM-11PM EST portion
#    which is in the PREVIOUS EST date's bars
# 3. Nautilus processes sequentially, so it accumulates Asian range across days

# Let's verify by simulating both methods

# METHOD A: Python runner (group by EST date, fresh engine per day)
print("=== METHOD A: Python runner ===")
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

# Count sessions with complete Asian range (has both 7PM and 3AM bars)
complete_sessions = 0
incomplete_sessions = 0
for dk, day_bars in est_days.items():
    has_7pm = any((b.timestamp.hour - 5) % 24 == 19 for b in day_bars)
    has_3am = any((b.timestamp.hour - 5) % 24 == 3 for b in day_bars)
    
    if has_7pm and has_3am:
        complete_sessions += 1
    elif has_7pm or has_3am:
        incomplete_sessions += 1

print(f"Complete Asian sessions (has 7PM and 3AM): {complete_sessions}")
print(f"Incomplete Asian sessions (missing 7PM or 3AM): {incomplete_sessions}")

# METHOD B: Nautilus-style (sequential, accumulate Asian range across day boundaries)
print("\n=== METHOD B: Nautilus-style ===")
# This is what the Nautilus strategy does:
# - It tracks Asian range on-the-fly
# - When a new EST day arrives, it resets the Asian range
# - But the 7PM-11PM EST bars come BEFORE the EST day change

# Let's trace the first few days
current_date = None
asian_high = 0.0
asian_low = 99999.0
sessions = []

for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_hour = est.hour
    est_date = est.strftime('%Y-%m-%d')
    
    # New day detection
    if est_date != current_date:
        # Session init happens at 3AM EST
        if current_date is not None and asian_high > 0 and asian_low < 99999:
            ar_pips = (asian_high - asian_low) / 0.1
            tier = "NO_GO"
            for t in ['T1', 'T2', 'T3']:
                if ar_pips <= xau_tiers[t]['ar_max']:
                    tier = t
                    break
            sessions.append((current_date, ar_pips, tier))
        
        current_date = est_date
        asian_high = 0.0
        asian_low = 99999.0
    
    # Asian tracking (7PM-3AM EST)
    if est_hour >= 19 or est_hour < 3:
        asian_high = max(asian_high, bar.high)
        asian_low = min(asian_low, bar.low)

# Don't forget the last day
if asian_high > 0 and asian_low < 99999:
    ar_pips = (asian_high - asian_low) / 0.1
    tier = "NO_GO"
    for t in ['T1', 'T2', 'T3']:
        if ar_pips <= xau_tiers[t]['ar_max']:
            tier = t
            break
    sessions.append((current_date, ar_pips, tier))

print(f"Total sessions: {len(sessions)}")
active = sum(1 for s in sessions if s[2] != "NO_GO")
nogo = sum(1 for s in sessions if s[2] == "NO_GO")
print(f"Active sessions: {active}, NO-GO sessions: {nogo}")

# Check tier distribution
tiers = {'T1': 0, 'T2': 0, 'T3': 0, 'NO_GO': 0}
for s in sessions:
    tiers[s[2]] += 1
print(f"Tier distribution: {tiers}")

# Now let's check the actual difference in session counts
# Python runner: 316 active, 1046 NO-GO
# Nautilus-style: 735 active, 384 NO-GO

# The difference is because:
# - Python runner misses the 7PM-11PM EST portion for incomplete days
# - This leads to smaller Asian ranges -> more NO-GO

# Let's verify by checking the average Asian range for each method
print("\n=== Average Asian Range Comparison ===")

# Python runner: only bars within the EST date
py_ar_sum = 0
py_ar_count = 0
for dk, day_bars in est_days.items():
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah > 0 and al < 99999:
        py_ar_sum += (ah - al) / 0.1
        py_ar_count += 1

print(f"Python runner avg AR: {py_ar_sum / py_ar_count:.1f} pips ({py_ar_count} sessions)")

# Nautilus-style: accumulated across day boundaries
nt_ar_sum = sum(s[1] for s in sessions)
nt_ar_count = len(sessions)
print(f"Nautilus-style avg AR: {nt_ar_sum / nt_ar_count:.1f} pips ({nt_ar_count} sessions)")

# The key insight: Nautilus-style gets LARGER Asian ranges because it accumulates
# across the day boundary, while Python runner only gets the portion within the EST date