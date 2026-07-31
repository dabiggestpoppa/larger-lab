"""Convert USDCHF CSV from Unix timestamp to datetime string format."""
import csv
from datetime import datetime

INFILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5.csv'
OUTFILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_dt.csv'

with open(INFILE, 'r') as fin, open(OUTFILE, 'w', newline='') as fout:
    reader = csv.DictReader(fin)
    writer = csv.writer(fout)
    writer.writerow(['timestamp','open','high','low','close','volume','spread','real_volume'])
    count = 0
    for row in reader:
        dt = datetime.fromtimestamp(int(row['timestamp']))
        writer.writerow([
            dt.strftime('%Y-%m-%d %H:%M:%S'),
            row['open'], row['high'], row['low'], row['close'],
            row['volume'], row['spread'], row['real_volume']
        ])
        count += 1

print(f"Converted {count} bars to {OUTFILE}")
