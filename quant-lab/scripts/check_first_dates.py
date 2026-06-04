"""Check first dates for all CSV data files."""
import os
from datetime import datetime

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
files = sorted([f for f in os.listdir(data_dir) if f.endswith('_M5.csv')])

for f in files:
    fp = os.path.join(data_dir, f)
    with open(fp, 'r') as fh:
        header = fh.readline().strip()
        second = fh.readline().strip()  # first data row

    cells = second.replace('\t', ',').split(',')
    # Try to find a date-like cell
    first_date = '???'
    for c in cells[:3]:
        c = c.strip()
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y.%m.%d %H:%M:%S', '%Y-%m-%d']:
            try:
                d = datetime.strptime(c, fmt)
                first_date = d.strftime('%Y-%m-%d')
                break
            except ValueError:
                continue
        if first_date != '???':
            break

    print("{:<30} {}".format(f, first_date))
