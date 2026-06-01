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

# Check the first complete day
dk = '2022-01-19'
day_bars = sorted(est_days[dk], key=lambda b: b.timestamp)

print(f"EST date {dk}: {len(day_bars)} bars")

# Find Asian range using Python runner logic
ah, al = 0.0, 99999.0
for b in day_bars:
    h = (b.timestamp.hour - 5) % 24
    if h >= 19 or h < 3:
        ah = max(ah, b.high)
        al = min(al, b.low)

ar_pips = (ah - al) / 0.1
print(f"Asian range (Python runner): {ar_pips:.1f} pips")

# Check tier
tier = "NO_GO"
for t in ['T1', 'T2', 'T3']:
    if ar_pips <= xau_tiers[t]['ar_max']:
        tier = t
        break
print(f"Tier: {tier}")

# Now check: what if we use the Nautilus logic?
# Nautilus tracks Asian range on-the-fly, bar by bar
# Let's simulate this

asian_high = 0.0
asian_low = 99999.0
asian_locked = False

# Process bars in order, tracking Asian range
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_hour = est.hour
    est_date = est.strftime('%Y-%m-%d')
    
    # Track Asian range
    if est_hour >= 19 or est_hour < 3:
        asian_high = max(asian_high, bar.high)
        asian_low = min(asian_low, bar.low)
    
    # At 3AM EST, lock the Asian range
    if not asian_locked and est_hour >= 3 and est_date == dk:
        asian_locked = True
        print(f"\nNautilus-style Asian range for {dk}: {(asian_high - asian_low) / 0.1:.1f} pips")
        break

# Now let's check what happens with the Python runner
# The issue might be that the Python runner is NOT skipping Asian bars correctly
# Let me check the run() method more carefully

print("\n=== Checking Python runner Asian skip logic ===")
# In run(), the code is:
# if bar_est_h >= 19 or bar_est_h < 3:
#     continue

# This should skip Asian bars. But let me verify the hour calculation
for bar in day_bars[:5]:
    bar_est_h = (bar.timestamp.hour - 5) % 24
    print(f"  UTC: {bar.timestamp} -> EST hour: {bar_est_h}")

# Wait! The hour calculation is WRONG!
# (bar.timestamp.hour - 5) % 24 gives the wrong result
# For UTC 00:00 (midnight), hour=0, (0-5)%24 = -5%24 = 19 (correct)
# For UTC 08:00 (8AM), hour=8, (8-5)%24 = 3 (correct)
# For UTC 23:00 (11PM), hour=23, (23-5)%24 = 18 (WRONG! Should be 18 for EST)

# Actually wait, let me check:
# EST = UTC - 5 hours
# UTC 00:00 -> EST 19:00 (previous day) -> hour 19
# UTC 08:00 -> EST 03:00 -> hour 3
# UTC 23:00 -> EST 18:00 -> hour 18

# So (hour - 5) % 24 is correct for converting UTC to EST hour
# Let me verify:
print("\n=== Verifying hour conversion ===")
for utc_hour in [0, 8, 19, 23]:
    est_hour = (utc_hour - 5) % 24
    print(f"UTC {utc_hour:02d}:00 -> EST {est_hour:02d}:00")