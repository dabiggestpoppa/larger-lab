"""Verify actual first/last dates in CSV files."""
import csv, os
from datetime import datetime

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

for f in sorted(os.listdir(data_dir)):
    if not f.endswith('_M5.csv'):
        continue
    fp = os.path.join(data_dir, f)
    
    with open(fp, 'r') as fh:
        reader = csv.DictReader(fh)
        first_row = None
        last_row = None
        row_count = 0
        for row in reader:
            if first_row is None:
                first_row = row
            last_row = row
            row_count += 1
    
    def parse_dt(row):
        for col in ['timestamp', 'time', 'date', 'datetime']:
            val = row.get(col, '')
            if val:
                try:
                    if 'T' in val:
                        return datetime.fromisoformat(val.split('.')[0])
                    return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
        return None
    
    d1 = parse_dt(first_row) if first_row else None
    d2 = parse_dt(last_row) if last_row else None
    
    is_pro = '.PRO' in f
    print("{:<30} {:>8,} rows | {} - {} | {}".format(
        f[:30], row_count,
        d1.strftime('%Y-%m-%d') if d1 else 'FAIL',
        d2.strftime('%Y-%m-%d') if d2 else 'FAIL',
        'PRO' if is_pro else 'ORIG'
    ))
