"""Debug: check if older EURGBP data has Asian bars."""
import csv
from datetime import datetime
from collections import defaultdict

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

# Count bars by UTC hour for different time periods
hourly_counts = defaultdict(lambda: defaultdict(int))
yearly_day_count = defaultdict(int)

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts_str = row.get('time', '')
        try:
            dt = datetime.fromisoformat(ts_str.split('.')[0])
        except:
            continue
        
        year = dt.year
        utc_h = dt.hour
        period = '2015-2021' if year <= 2021 else '2022-2026'
        hourly_counts[period][utc_h] += 1
        
        if utc_h == 0:  # Count days
            yearly_day_count[year] += 1

print("=== BAR COUNT BY UTC HOUR ===")
print("  Hour | 2015-2021  | 2022-2026")
print("  " + "-" * 40)
for h in range(24):
    old = hourly_counts['2015-2021'].get(h, 0)
    new = hourly_counts['2022-2026'].get(h, 0)
    if old > 0 or new > 0:
        print("  {:02d}:00 | {:>10,} | {:>10,}".format(h, old, new))

print("\n=== DAY COUNT BY YEAR (UTC midnight bars) ===")
for year in sorted(yearly_day_count.keys()):
    print("  {}: {} days".format(year, yearly_day_count[year]))

# Check: does 2015-2021 data have bars in Asian hours (UTC 00:00-08:00)?
print("\n=== ASIAN HOUR COVERAGE (UTC 00:00-08:00) ===")
for period in ['2015-2021', '2022-2026']:
    asian_bars = sum(hourly_counts[period].get(h, 0) for h in range(8))
    total_bars = sum(hourly_counts[period].values())
    print("  {}: {} asian bars / {} total ({:.1f}%)".format(
        period, asian_bars, total_bars, asian_bars/total_bars*100 if total_bars else 0))
