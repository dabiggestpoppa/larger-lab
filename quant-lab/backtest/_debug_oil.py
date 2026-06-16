"""Debug OILUSD Asian Range calculation"""
import csv
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

def load_bars(csv_path):
    bars = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get('time') or row.get('timestamp')
                ts = datetime.strptime(ts_raw.strip(), '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
                o = float(row['open']); h = float(row['high']); lo = float(row['low']); cl = float(row['close'])
                bars.append((ts, o, h, lo, cl))
            except: continue
    bars.sort(key=lambda b: b[0])
    return bars

bars = load_bars('quant-lab/data/OILUSDPRO_M5.csv')
print(f'Total bars: {len(bars)}')
print(f'Range: {bars[0][0]} to {bars[-1][0]}')

# Check March 2026 bars
march_bars = [(ts, o, h, lo, cl) for ts, o, h, lo, cl in bars if ts.year == 2026 and ts.month >= 3]
print(f'March+ bars: {len(march_bars)}')

# Check Asian session bars for a specific day
from datetime import date
test_date = date(2026, 3, 3)
asian = [(ts, o, h, lo, cl) for ts, o, h, lo, cl in bars if ts.date() == test_date and ts.hour >= 0 and ts.hour < 8]
print(f'Asian bars on {test_date}: {len(asian)}')
if asian:
    ah = max(b[2] for b in asian)
    al = min(b[3] for b in asian)
    print(f'  AR: ${ah-al:.2f} (high={ah}, low={al})')
    print(f'  First: {asian[0]}')
    print(f'  Last: {asian[-1]}')

# Count bars per hour for March
hour_counts = {}
for ts, o, h, lo, cl in march_bars:
    hour = ts.hour
    hour_counts[hour] = hour_counts.get(hour, 0) + 1
print(f'\nHour distribution (March):')
for h in sorted(hour_counts.keys()):
    print(f'  {h:02d}:00 UTC: {hour_counts[h]} bars')

# Check how many days have Asian data
march_dates = sorted(set(ts.date() for ts, _, _, _, _ in march_bars))
print(f'\nUnique March+ dates: {len(march_dates)}')
asian_days = 0
for d in march_dates:
    asian_count = sum(1 for ts, _, _, _, _ in bars if ts.date() == d and ts.hour >= 0 and ts.hour < 8)
    if asian_count > 0:
        asian_days += 1
print(f'Days with Asian bars: {asian_days}')

# Sample a few days
print(f'\nSample Asian Ranges:')
for d in march_dates[:10]:
    asian = [(ts, o, h, lo, cl) for ts, o, h, lo, cl in bars if ts.date() == d and ts.hour >= 0 and ts.hour < 8]
    if asian:
        ah = max(b[2] for b in asian)
        al = min(b[3] for b in asian)
        ar = ah - al
        print(f'  {d}: AR=${ar:.2f} ({len(asian)} bars, high={ah}, low={al})')
    else:
        print(f'  {d}: NO Asian bars')
