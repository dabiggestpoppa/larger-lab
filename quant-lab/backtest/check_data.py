from pathlib import Path
from datetime import datetime

for sym in ['EURUSD', 'USDCHF', 'GBPJPY', 'NZDUSD']:
    p = Path(f'C:/Users/wifik/Desktop/projects/larger-lab/quant-lab/data/{sym}_M5.csv')
    if not p.exists():
        print(f"{sym}: FILE NOT FOUND")
        continue
    lines = p.read_text().splitlines()
    first = lines[1].split(',')[0] if len(lines) > 1 else '?'
    last = lines[-2].split(',')[0] if len(lines) > 1 else '?'
    print(f"{sym}: {len(lines)-1} bars | {first} -> {last} | {p.stat().st_size/1024/1024:.1f}MB")
