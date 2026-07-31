"""Check Asian Range distribution for EURGBP across years."""
import sys, csv
from datetime import datetime
from collections import defaultdict

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

# Parse CSV and compute AR per day
print("Parsing EURGBP data...")
days = {}
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts_str = row.get('timestamp', row.get('time', row.get('date', '')))
        try:
            # Handle both formats
            if 'T' in ts_str:
                dt = datetime.fromisoformat(ts_str.split('.')[0])
            else:
                dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        except:
            continue
        
        dk = dt.strftime('%Y-%m-%d')
        if dk not in days:
            days[dk] = []
        try:
            h = float(row.get('high', 0))
            l = float(row.get('low', 0))
            days[dk].append((dt, h, l))
        except:
            pass

print("Total days: {}".format(len(days)))

# Compute AR per day (19:00-03:00 EST = 00:00-08:00 UTC)
# est_offset = -5, so UTC hour = EST hour + 5
# Asian: EST 19:00-03:00 = UTC 00:00-08:00
yearly_stats = defaultdict(lambda: {'days': 0, 'total_ar': 0, 'ars': []})

for dk, bars in days.items():
    year = dk[:4]
    ah, al = 0.0, 99999.0
    has_asian = False
    for dt, h, l in bars:
        utc_h = dt.hour
        # Asian: UTC 00:00-08:00 (EST 19:00-03:00)
        if utc_h < 8:
            ah = max(ah, h)
            al = min(al, l)
            has_asian = True
    
    if has_asian and ah > 0 and al < 99999:
        ar = (ah - al) * 10000  # in pips
        yearly_stats[year]['days'] += 1
        yearly_stats[year]['total_ar'] += ar
        yearly_stats[year]['ars'].append(ar)

print("\n=== EURGBP YEARLY ASIAN RANGE STATS ===")
print("  {:<6} {:>6} {:>10} {:>10} {:>10}".format("Year", "Days", "Avg AR", "Med AR", "P75 AR"))
for year in sorted(yearly_stats.keys()):
    s = yearly_stats[year]
    ars = sorted(s['ars'])
    avg_ar = s['total_ar'] / s['days']
    med_ar = ars[len(ars) // 2]
    p75_ar = ars[int(len(ars) * 0.75)]
    print("  {:<6} {:>6} {:>10.1f} {:>10.1f} {:>10.1f}".format(year, s['days'], avg_ar, med_ar, p75_ar))

# Now check: how many days pass the T1 filter per year?
# EURGBP T1: ar_max=20.98, trigger=8.0
print("\n=== EURGBP DAYS PASSING T1 FILTER (ar_max=20.98) ===")
for year in sorted(yearly_stats.keys()):
    s = yearly_stats[year]
    ars = s['ars']
    t1_pass = sum(1 for ar in ars if ar <= 20.98)
    t1_pct = t1_pass / len(ars) * 100 if ars else 0
    print("  {}: {}/{} days ({:.1f}%) pass T1".format(year, t1_pass, len(ars), t1_pct))

# Compare with EURUSD
print("\n\n=== EURUSD YEARLY ASIAN RANGE STATS ===")
csv_path2 = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
days2 = {}
with open(csv_path2, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts_str = row.get('timestamp', row.get('time', row.get('date', '')))
        try:
            if 'T' in ts_str:
                dt = datetime.fromisoformat(ts_str.split('.')[0])
            else:
                dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        except:
            continue
        dk = dt.strftime('%Y-%m-%d')
        if dk not in days2:
            days2[dk] = []
        try:
            h = float(row.get('high', 0))
            l = float(row.get('low', 0))
            days2[dk].append((dt, h, l))
        except:
            pass

yearly_stats2 = defaultdict(lambda: {'days': 0, 'total_ar': 0, 'ars': []})
for dk, bars in days2.items():
    year = dk[:4]
    ah, al = 0.0, 99999.0
    has_asian = False
    for dt, h, l in bars:
        utc_h = dt.hour
        if utc_h < 8:
            ah = max(ah, h)
            al = min(al, l)
            has_asian = True
    if has_asian and ah > 0 and al < 99999:
        ar = (ah - al) * 10000
        yearly_stats2[year]['days'] += 1
        yearly_stats2[year]['total_ar'] += ar
        yearly_stats2[year]['ars'].append(ar)

print("  {:<6} {:>6} {:>10} {:>10} {:>10}".format("Year", "Days", "Avg AR", "Med AR", "P75 AR"))
for year in sorted(yearly_stats2.keys()):
    s = yearly_stats2[year]
    ars = sorted(s['ars'])
    avg_ar = s['total_ar'] / s['days']
    med_ar = ars[len(ars) // 2]
    p75_ar = ars[int(len(ars) * 0.75)]
    print("  {:<6} {:>6} {:>10.1f} {:>10.1f} {:>10.1f}".format(year, s['days'], avg_ar, med_ar, p75_ar))

# EURUSD T1: ar_max=20.00
print("\n=== EURUSD DAYS PASSING T1 FILTER (ar_max=20.00) ===")
for year in sorted(yearly_stats2.keys()):
    s = yearly_stats2[year]
    ars = s['ars']
    t1_pass = sum(1 for ar in ars if ar <= 20.00)
    t1_pct = t1_pass / len(ars) * 100 if ars else 0
    print("  {}: {}/{} days ({:.1f}%) pass T1".format(year, t1_pass, len(ars), t1_pct))
