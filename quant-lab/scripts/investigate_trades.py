"""Investigate trade count issues: data bars, days, loops, PRO vs non-PRO."""
import json, os, csv
from datetime import datetime

# 1. Check data_bars and data_days from basket results
print("=" * 80)
print("ISSUE 1: DATA COVERAGE (bars, days, trades per pair)")
print("=" * 80)

baskets_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\baskets'
for f in sorted(os.listdir(baskets_dir)):
    if not f.endswith('_results.json'):
        continue
    fp = os.path.join(baskets_dir, f)
    with open(fp) as fh:
        data = json.load(fh)
    basket = data.get('basket', f)
    results = data.get('results', {})
    print("\n--- {} ---".format(basket))
    print("  {:<12} {:>8} {:>8} {:>10} {:>8}".format("Pair", "Trades", "Days", "Bars", "Tr/Day"))
    if isinstance(results, dict):
        for sym, res in sorted(results.items()):
            if isinstance(res, dict):
                trades = res.get('total_trades', 0)
                days = res.get('data_days', 0)
                bars = res.get('data_bars', 0)
                tr_per_day = round(trades / days, 2) if days else 0
                print("  {:<12} {:>8} {:>8} {:>10} {:>8}".format(sym, trades, days, bars, tr_per_day))

# 2. Check loop distribution from the detailed reports
print("\n" + "=" * 80)
print("ISSUE 2: LOOP DISTRIBUTION (are loops 2-5 producing trades?)")
print("=" * 80)

# Read from the USD basket report which has detailed module breakdown
usd_report = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\baskets\usd_basket_report.md'
with open(usd_report) as f:
    content = f.read()
print("\nUSD Basket - checking for loop info in report...")
if 'loop' in content.lower() or 'Loop' in content:
    for line in content.split('\n'):
        if 'loop' in line.lower():
            print("  " + line)
else:
    print("  NO LOOP DATA in report (not being tracked/reported)")

# 3. Compare PRO vs non-PRO file trade efficiency
print("\n" + "=" * 80)
print("ISSUE 3: PRO vs NON-PRO COMPARISON")
print("=" * 80)

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'
print("\n  {:<30} {:>10} {:>10} {:<6}".format("File", "Rows", "PRO?", "First Date"))
print("  " + "-" * 60)

for f in sorted(os.listdir(data_dir)):
    if not f.endswith('_M5.csv'):
        continue
    fp = os.path.join(data_dir, f)
    is_pro = '.PRO' in f
    
    with open(fp, 'r') as fh:
        header = fh.readline().strip()
        second = fh.readline().strip()
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(max(0, size - 4096))
        last_lines = fh.read().strip().split('\n')
        last = last_lines[-1].strip()
    
    def parse_dt(line):
        cells = line.replace('\t', ',').split(',')
        for c in cells[:3]:
            c = c.strip()
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y.%m.%d %H:%M:%S']:
                try:
                    return datetime.strptime(c, fmt)
                except ValueError:
                    continue
        return None
    
    d1 = parse_dt(second)
    d2 = parse_dt(last)
    
    with open(fp, 'r') as fh:
        row_count = sum(1 for _ in fh) - 1
    
    first_date = d1.strftime('%Y-%m-%d') if d1 else 'PARSE_FAIL'
    last_date = d2.strftime('%Y-%m-%d') if d2 else 'PARSE_FAIL'
    
    print("  {:<30} {:>10,} {:>10} {} - {}".format(f[:30], row_count, 'PRO' if is_pro else 'ORIG', first_date, last_date))
