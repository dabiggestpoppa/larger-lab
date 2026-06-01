import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# Group by EST date (Python runner method)
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

# Find days with complete Asian session (need bars at 7PM EST = UTC 00:00)
# AND bars at 3AM EST = UTC 08:00
complete_days = []
for dk, day_bars in est_days.items():
    has_7pm = False
    has_3am = False
    for bar in day_bars:
        est_h = (bar.timestamp.hour - 5) % 24
        if est_h == 19:  # 7PM EST
            has_7pm = True
        if est_h == 3:   # 3AM EST
            has_3am = True
    
    if has_7pm and has_3am and len(day_bars) > 200:
        complete_days.append(dk)

print(f'Days with complete Asian session (has 7PM and 3AM): {len(complete_days)}')

# Now check: when we group by EST date, does the Asian session get split?
# The Asian session is 7PM-3AM EST, which spans TWO UTC days!
# UTC day N: 7PM EST day N-1 (midnight UTC = 7PM EST)
# UTC day N+1: 3AM EST day N (8AM UTC = 3AM EST)

# Let's trace a complete day
print('\\n=== Tracing complete day 2022-01-19 ===')
dk = '2022-01-19'
day_bars = est_days.get(dk, [])
print(f'EST date {dk}: {len(day_bars)} bars')

# Count bars by session
asian_bars = []
trading_bars = []
for bar in day_bars:
    est_h = (bar.timestamp.hour - 5) % 24
    if est_h >= 19 or est_h < 3:
        asian_bars.append(bar)
    else:
        trading_bars.append(bar)

print(f'Asian bars (7PM-3AM EST): {len(asian_bars)}')
print(f'Trading bars (3AM-7PM EST): {len(trading_bars)}')

# Check if Asian bars are in the SAME EST day
print('\\nAsian bar timestamps:')
for bar in asian_bars[:5]:
    est_dt = bar.timestamp + timedelta(hours=-5)
    print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')

# Now check: what happens with UTC grouping?
utc_days = defaultdict(list)
for bar in bars:
    dk = bar.timestamp.strftime('%Y-%m-%d')
    utc_days[dk].append(bar)

print('\\n=== UTC day 2022-01-19 (contains 7PM EST 01-18) ===')
dk = '2022-01-19'
day_bars = utc_days.get(dk, [])
print(f'UTC date {dk}: {len(day_bars)} bars')
for bar in day_bars[:5]:
    est_dt = bar.timestamp + timedelta(hours=-5)
    print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')

print('\\n=== UTC day 2022-01-20 (contains 3AM EST 01-19) ===')
dk = '2022-01-20'
day_bars = utc_days.get(dk, [])
print(f'UTC date {dk}: {len(day_bars)} bars')
for bar in day_bars[:5]:
    est_dt = bar.timestamp + timedelta(hours=-5)
    print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')