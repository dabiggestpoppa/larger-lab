"""Debug: why is EURUSD loading 0 bars?"""
import sys, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

# Read the file directly
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

raw_lines = content.strip().split('\n')
print('Total lines:', len(raw_lines))
print('Header:', repr(raw_lines[0]))
print('First data:', repr(raw_lines[1]))

header_cells = raw_lines[0].replace('\t', ',').split(',')
header_lower = [h.strip().lower() for h in header_cells]
print('Headers:', header_lower)

col_idx = {}
for i, h in enumerate(header_lower):
    col_idx[h] = i
print('col_idx:', col_idx)

ts_col = col_idx.get('timestamp') or col_idx.get('time')
print('ts_col:', ts_col)

# Try parsing first data row
cells = raw_lines[1].replace('\t', ',').split(',')
print('Cells:', cells)
if ts_col is not None:
    ts_str = cells[ts_col].strip()
    print('ts_str:', repr(ts_str))
    
    from datetime import datetime
    formats = [
        '%Y.%m.%d %H:%M',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M',
        '%Y.%m.%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str, fmt)
            print('Matched:', fmt, '->', dt)
            break
        except ValueError:
            print('Failed:', fmt)
