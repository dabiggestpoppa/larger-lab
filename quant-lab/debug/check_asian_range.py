import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# Group by EST date (Python runner method) - CORRECT
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

# Group by UTC date (Nautilus method) - INCORRECT for Asian session
utc_days = defaultdict(list)
for bar in bars:
    dk = bar.timestamp.strftime('%Y-%m-%d')
    utc_days[dk].append(bar)

# Compute Asian range for EST day 2022-01-19
dk = '2022-01-19'
day_bars = est_days.get(dk, [])
ah, al = 0.0, 99999.0
for bar in day_bars:
    est_h = (bar.timestamp.hour - 5) % 24
    if est_h >= 19 or est_h < 3:
        ah = max(ah, bar.high)
        al = min(al, bar.low)
print(f'EST day {dk}:')
print(f'  Asian range: {ah} - {al} = {(ah-al)/0.1:.1f} pips')

# Compute Asian range for UTC day 2022-01-20 (which contains 7PM-3AM EST of day 01-19)
dk = '2022-01-20'
day_bars = utc_days.get(dk, [])
ah, al = 0.0, 99999.0
for bar in day_bars:
    est_h = (bar.timestamp.hour - 5) % 24
    if est_h >= 19 or est_h < 3:
        ah = max(ah, bar.high)
        al = min(al, bar.low)
print(f'\\nUTC day {dk} (contains 7PM-3AM EST of day 01-19):')
print(f'  Asian range: {ah} - {al} = {(ah-al)/0.1:.1f} pips')

# Now let's count how many UTC days have incomplete Asian ranges
# (missing the 7PM-8AM portion because it's in the previous UTC day)
incomplete_asian_count = 0
complete_asian_count = 0
for dk, day_bars in utc_days.items():
    ah, al = 0.0, 99999.0
    for bar in day_bars:
        est_h = (bar.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, bar.high)
            al = min(al, bar.low)
    
    # Check if this UTC day has bars at 7PM EST (midnight UTC)
    has_7pm_est = any((bar.timestamp.hour - 5) % 24 == 19 for bar in day_bars)
    
    if ah > 0 and al < 99999:
        if has_7pm_est:
            complete_asian_count += 1
        else:
            incomplete_asian_count += 1

print(f'\\nUTC days with Asian range (starting at midnight UTC = 7PM EST): {complete_asian_count}')
print(f'UTC days with Asian range (starting at 8AM UTC = 3AM EST): {incomplete_asian_count}')

# The key insight: UTC days that start at 7PM EST have incomplete Asian range
# They're missing the 7PM-8AM portion which is in the PREVIOUS UTC day

# Let's verify by checking the actual session count difference
# Python: 316 active sessions, 1046 NO-GO
# Nautilus-style: 735 active sessions, 384 NO-GO

# This suggests that UTC grouping creates MORE active sessions because
# incomplete Asian ranges are smaller, so fewer exceed tier thresholds

# Let's compute the average Asian range for each method
est_ar_sum = 0
est_ar_count = 0
for dk, day_bars in est_days.items():
    ah, al = 0.0, 99999.0
    for bar in day_bars:
        est_h = (bar.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, bar.high)
            al = min(al, bar.low)
    if ah > 0 and al < 99999:
        est_ar_sum += (ah - al) / 0.1
        est_ar_count += 1

utc_ar_sum = 0
utc_ar_count = 0
for dk, day_bars in utc_days.items():
    ah, al = 0.0, 99999.0
    for bar in day_bars:
        est_h = (bar.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, bar.high)
            al = min(al, bar.low)
    if ah > 0 and al < 99999:
        utc_ar_sum += (ah - al) / 0.1
        utc_ar_count += 1

print(f'\\nAverage Asian range (EST grouping): {est_ar_sum / est_ar_count:.1f} pips ({est_ar_count} sessions)')
print(f'Average Asian range (UTC grouping): {utc_ar_sum / utc_ar_count:.1f} pips ({utc_ar_count} sessions)')