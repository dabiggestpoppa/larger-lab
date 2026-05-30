"""Fetch USDCHF.PRO historical data from MT5 in chunks."""
import sys, os, csv
from datetime import datetime
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONPATH'] = 'quant-lab'
sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 failed"); exit(1)

all_rates = []
chunk_starts = [
    datetime(2026, 5, 1),
    datetime(2026, 1, 1),
    datetime(2025, 7, 1),
    datetime(2025, 1, 1),
    datetime(2024, 7, 1),
    datetime(2024, 1, 1),
    datetime(2023, 7, 1),
]

for i, start_dt in enumerate(chunk_starts):
    end_dt = chunk_starts[i-1] if i > 0 else datetime.now()
    rates = mt5.copy_rates_range('USDCHF.PRO', mt5.TIMEFRAME_M5, start_dt, end_dt)
    if rates is not None and len(rates) > 0:
        df = datetime.fromtimestamp(rates[0][0])
        dl = datetime.fromtimestamp(rates[-1][0])
        print(f"Chunk {i}: {start_dt.date()} -> {end_dt.date()}: {len(rates)} bars ({df} to {dl})")
        all_rates.extend(rates)
    else:
        print(f"Chunk {i}: {start_dt.date()} -> {end_dt.date()}: NO DATA")

print(f"\nTotal raw bars: {len(all_rates)}")
if all_rates:
    all_rates.sort(key=lambda x: x[0])
    seen = set()
    deduped = []
    for r in all_rates:
        if r[0] not in seen:
            seen.add(r[0])
            deduped.append(r)
    print(f"After dedup: {len(deduped)} bars")
    print(f"Range: {datetime.fromtimestamp(deduped[0][0])} to {datetime.fromtimestamp(deduped[-1][0])}")

    out = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5.csv'
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['timestamp','open','high','low','close','volume','spread','real_volume'])
        for r in deduped:
            w.writerow([int(r[0]), round(r[1],5), round(r[2],5), round(r[3],5), round(r[4],5), int(r[5]), int(r[6]), int(r[7])])
    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f"Saved: {out} ({size_mb:.1f}MB)")

mt5.shutdown()
