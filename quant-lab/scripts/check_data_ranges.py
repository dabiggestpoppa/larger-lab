"""Check date ranges and row counts for all CSV data files."""
import os
from datetime import datetime

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
files = sorted([f for f in os.listdir(data_dir) if f.endswith('_M5.csv')])

print("{:<30} {:<22} {:<22} {:>10}".format("File", "First Date", "Last Date", "Rows"))
print("-" * 90)

for f in files:
    fp = os.path.join(data_dir, f)
    with open(fp, 'r') as fh:
        first = fh.readline().strip()
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(max(0, size - 4096))
        last_lines = fh.read().strip().split('\n')
        last = last_lines[-1].strip()

    def parse_dt(line):
        cells = line.replace('\t', ',').split(',')
        for c in cells:
            c = c.strip()
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y.%m.%d %H:%M:%S']:
                try:
                    return datetime.strptime(c, fmt)
                except ValueError:
                    continue
        return None

    d1 = parse_dt(first)
    d2 = parse_dt(last)

    with open(fp, 'r') as fh:
        row_count = sum(1 for _ in fh) - 1

    fdate = d1.strftime('%Y-%m-%d') if d1 else '???'
    ldate = d2.strftime('%Y-%m-%d') if d2 else '???'
    print("{:<30} {:<22} {:<22} {:>10,}".format(f, fdate, ldate, row_count))
