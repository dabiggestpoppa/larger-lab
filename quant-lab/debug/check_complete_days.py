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

# Group by EST date
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

# Count sessions and NO-GO for EST grouping
est_active = 0
est_nogo = 0
for dk, day_bars in est_days.items():
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.1
    # Check tier
    tier = "NO_GO"
    for t in ['T1', 'T2', 'T3']:
        if ar_pips <= xau_tiers[t]['ar_max']:
            tier = t
            break
    
    if tier == "NO_GO":
        est_nogo += 1
    else:
        est_active += 1

print(f"EST grouping: {est_active} active sessions, {est_nogo} NO-GO sessions")

# Group by UTC date
utc_days = defaultdict(list)
for bar in bars:
    dk = bar.timestamp.strftime('%Y-%m-%d')
    utc_days[dk].append(bar)

# Count sessions and NO-GO for UTC grouping
utc_active = 0
utc_nogo = 0
for dk, day_bars in utc_days.items():
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.1
    tier = "NO_GO"
    for t in ['T1', 'T2', 'T3']:
        if ar_pips <= xau_tiers[t]['ar_max']:
            tier = t
            break
    
    if tier == "NO_GO":
        utc_nogo += 1
    else:
        utc_active += 1

print(f"UTC grouping: {utc_active} active sessions, {utc_nogo} NO-GO sessions")

# Now let's check the actual Nautilus strategy behavior
# The Nautilus strategy uses EST date for day detection, but processes bars sequentially
# Let me trace what happens with the first complete day

print("\n=== Tracing first complete day (2022-01-19) ===")
dk = '2022-01-19'
day_bars = sorted(est_days[dk], key=lambda b: b.timestamp)
print(f"EST date {dk}: {len(day_bars)} bars")

# Find Asian range
ah, al = 0.0, 99999.0
for b in day_bars:
    h = (b.timestamp.hour - 5) % 24
    if h >= 19 or h < 3:
        ah = max(ah, b.high)
        al = min(al, b.low)

ar_pips = (ah - al) / 0.1
print(f"Asian range: {ar_pips:.1f} pips")

# Check tier
tier = "NO_GO"
for t in ['T1', 'T2', 'T3']:
    if ar_pips <= xau_tiers[t]['ar_max']:
        tier = t
        break
print(f"Tier: {tier}")

# Check what bars are in Asian vs trading
asian_bars = [b for b in day_bars if (b.timestamp.hour - 5) % 24 >= 19 or (b.timestamp.hour - 5) % 24 < 3]
trading_bars = [b for b in day_bars if 3 <= (b.timestamp.hour - 5) % 24 < 19]
print(f"Asian bars: {len(asian_bars)}, Trading bars: {len(trading_bars)}")

# Check if the Asian bars are in the SAME UTC day
print("\nAsian bar UTC dates:")
asian_utc_dates = set(b.timestamp.strftime('%Y-%m-%d') for b in asian_bars)
print(f"  Unique UTC dates: {asian_utc_dates}")

# The key insight: Asian session (7PM-3AM EST) spans TWO UTC days!
# UTC day N: 7PM EST day N-1 (midnight UTC = 7PM EST)
# UTC day N+1: 3AM EST day N (8AM UTC = 3AM EST)

# So when we group by EST date, we get the FULL Asian range
# But when we group by UTC date, we only get PART of the Asian range

# Let me verify this is the cause of the session count difference
print("\n=== Checking UTC day split ===")
# UTC day 2022-01-20 contains 7PM-3AM EST of day 01-19
utc_dk = '2022-01-20'
utc_day_bars = utc_days[utc_dk]
print(f"UTC date {utc_dk}: {len(utc_day_bars)} bars")

# This UTC day starts at midnight UTC = 7PM EST
# It contains bars from 7PM EST day 01-18 through 3AM EST day 01-19

# Check the EST hours in this UTC day
est_hours = set((b.timestamp.hour - 5) % 24 for b in utc_day_bars)
print(f"EST hours in this UTC day: {sorted(est_hours)}")