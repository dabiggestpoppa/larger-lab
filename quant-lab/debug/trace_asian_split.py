import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# The issue: Asian session (7PM-3AM EST) spans TWO UTC days
# When we group by EST date, we only get bars from ONE UTC day
# We're missing the 7PM-8AM portion which is in the PREVIOUS UTC day

# Let's trace the bars for EST date 2022-01-19
# The Asian session for this day is 7PM EST 01-18 through 3AM EST 01-19

# Find all bars that belong to the Asian session of EST date 2022-01-19
asian_for_0119 = []
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_hour = est.hour
    est_date = est.strftime('%Y-%m-%d')
    
    # Asian session for EST date 2022-01-19:
    # - 7PM-11PM EST 01-18 (UTC 00:00-05:00 on 01-19)
    # - 12AM-3AM EST 01-19 (UTC 05:00-08:00 on 01-19)
    
    if (est_date == '2022-01-18' and est_hour >= 19) or (est_date == '2022-01-19' and est_hour < 3):
        asian_for_0119.append(bar)

print(f"Bars in Asian session for EST 2022-01-19: {len(asian_for_0119)}")

# Compute Asian range
ah, al = 0.0, 99999.0
for bar in asian_for_0119:
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
print(f"This is because Python runner misses the 7PM-11PM EST portion (25 bars)")

# Count bars in each portion
portion1 = [b for b in asian_for_0119 if b.timestamp.strftime('%Y-%m-%d') == '2022-01-19' and (b.timestamp.hour - 5) % 24 >= 19]
portion2 = [b for b in asian_for_0119 if b.timestamp.strftime('%Y-%m-%d') == '2022-01-19' and (b.timestamp.hour - 5) % 24 < 3]
print(f"\nBars in 7PM-11PM EST 01-18 (UTC 01-19): {len(portion1)}")
print(f"Bars in 12AM-3AM EST 01-19 (UTC 01-19): {len(portion2)}")