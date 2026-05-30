"""Convert MAD's USDCHF CSV to the format p90_backtest.py expects."""
import csv, os
from datetime import datetime

INFILE = r"C:\Users\wifik\Downloads\USDCHF.PRO_M5_202301020000_202605221455.csv"
OUTFILE = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv"

count = 0
with open(INFILE, 'r') as fin, open(OUTFILE, 'w', newline='') as fout:
    reader = csv.reader(fin, delimiter='\t')
    header = next(reader)  # skip <DATE> <TIME> <OPEN> ...
    
    writer = csv.writer(fout)
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume', 'spread', 'real_volume'])
    
    for row in reader:
        if len(row) < 6:
            continue
        try:
            # Parse date: 2023.01.02  and time: 00:00:00
            dt_str = f"{row[0]} {row[1]}"
            dt = datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
            dt_fmt = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            o, h, l, c = float(row[2]), float(row[3]), float(row[4]), float(row[5])
            vol = int(row[6]) if len(row) > 6 else 0
            spread = int(row[8]) if len(row) > 8 else 0
            
            writer.writerow([dt_fmt, o, h, l, c, vol, spread, 0])
            count += 1
        except (ValueError, IndexError) as e:
            print(f"Skip row {count}: {e} -> {row}")
            continue

size_mb = os.path.getsize(OUTFILE) / 1024 / 1024
print(f"Converted {count} bars -> {OUTFILE} ({size_mb:.1f}MB)")

# Verify last bar
with open(OUTFILE, 'r') as f:
    lines = f.readlines()
print(f"First: {lines[1].strip()}")
print(f"Last:  {lines[-1].strip()}")
