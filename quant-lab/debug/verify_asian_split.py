import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# The Asian session for EST date 2022-01-19 is:
# - 7PM-11PM EST 01-18 (UTC 00:00-05:00 on 01-19)
# - 12AM-3AM EST 01-19 (UTC 05:00-08:00 on 01-19)

# Find all bars that belong to the Asian session of EST date 2022-01-19
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

print(f"Asian bars for EST 2022-01-19: {len(asian_bars)}")

# Compute Asian range
ah, al = 0.0, 99999.0
for bar in asian_bars:
    ah = max(ah, bar.high)
    al = min(al, bar.low)

ar_pips = (ah - al) / 0.1
print(f"Full Asian range: {ar_pips:.1f} pips ({ah} - {al})")

# Now check what the Python runner gets
# It groups by EST date, so it only gets bars with EST date 2022-01-19
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

day_bars = est_days['2022-01-19']
ah2, al2 = 0.0, 99999.0
for bar in day_bars:
    est_h = (bar.timestamp.hour - 5) % 24
    if est_h >= 19 or est_h < 3:
        ah2 = max(ah2, bar.high)
        al2 = min(al2, bar.low)

ar_pips2 = (ah2 - al2) / 0.1
print(f"\nPython runner Asian range (only EST date 2022-01-19 bars): {ar_pips2:.1f} pips ({ah2} - {al2})")

# The difference!
print(f"\nDifference: {ar_pips - ar_pips2:.1f} pips")
print(f"Python runner misses {len(asian_bars) - len([b for b in day_bars if (b.timestamp.hour - 5) % 24 >= 19 or (b.timestamp.hour - 5) % 24 < 3])} Asian bars from the previous EST date")

# Now let's check the Nautilus strategy
# It uses EST date for day detection, but processes bars sequentially
# So it should get the FULL Asian range

# Let me trace the Nautilus-style processing
print("\n=== Nautilus-style processing ===")
current_date = None
asian_high = 0.0
asian_low = 99999.0
session_init_today = False

for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_hour = est.hour
    est_date = est.strftime('%Y-%m-%d')
    
    # New day detection
    if est_date != current_date:
        if current_date == '2022-01-18':
            print(f"Day changed from {current_date} to {est_date}")
            print(f"  Asian range accumulated: {(asian_high - asian_low) / 0.1:.1f} pips")
        current_date = est_date
        asian_high = 0.0
        asian_low = 99999.0
        session_init_today = False
    
    # Asian tracking
    if est_hour >= 19 or est_hour < 3:
        asian_high = max(asian_high, bar.high)
        asian_low = min(asian_low, bar.low)

print(f"\nFinal Asian range for EST 2022-01-19: {(asian_high - asian_low) / 0.1:.1f} pips")