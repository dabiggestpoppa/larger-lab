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

# Group by UTC date (Nautilus method)
utc_days = defaultdict(list)
for bar in bars:
    dk = bar.timestamp.strftime('%Y-%m-%d')
    utc_days[dk].append(bar)

print(f'EST days: {len(est_days)}')
print(f'UTC days: {len(utc_days)}')

# Check how many EST days have incomplete Asian session
# (missing bars from 7PM-3AM EST)
incomplete_asian = 0
complete_asian = 0
for dk, day_bars in est_days.items():
    # Count bars in Asian session (EST hours 19-23 and 0-2)
    asian_count = 0
    for bar in day_bars:
        est_h = (bar.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            asian_count += 1
    
    # Full Asian session should have ~96 bars (8 hours * 12 bars/hour)
    if asian_count < 50:  # Less than half of expected
        incomplete_asian += 1
    else:
        complete_asian += 1

print(f'\\nEST days with incomplete Asian session: {incomplete_asian}')
print(f'EST days with complete Asian session: {complete_asian}')

# Check the overlap between EST and UTC days
# Each UTC day starts at midnight, but Asian session spans 7PM-3AM EST
# So UTC day N contains: 7PM EST day N-1, 12AM EST day N, 3AM EST day N
# EST day N contains: 3AM-7PM EST day N, 7PM-11PM EST day N

# Let's trace a specific day
print('\\n=== Tracing Jan 3-4, 2022 ===')
for dk in ['2022-01-03', '2022-01-04']:
    day_bars = est_days.get(dk, [])
    if day_bars:
        print(f'\\nEST date {dk}: {len(day_bars)} bars')
        for bar in day_bars[:5]:
            est_dt = bar.timestamp + timedelta(hours=-5)
            print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')
        if len(day_bars) > 5:
            print(f'  ...')
            for bar in day_bars[-3:]:
                est_dt = bar.timestamp + timedelta(hours=-5)
                print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')

# Check UTC days
print('\\n=== UTC days Jan 3-4, 2022 ===')
for dk in ['2022-01-03', '2022-01-04']:
    day_bars = utc_days.get(dk, [])
    if day_bars:
        print(f'\\nUTC date {dk}: {len(day_bars)} bars')
        for bar in day_bars[:5]:
            est_dt = bar.timestamp + timedelta(hours=-5)
            print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')