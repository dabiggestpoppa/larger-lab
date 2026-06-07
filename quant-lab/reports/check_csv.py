import csv
from datetime import datetime

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\CHFJPY_M5.csv'

# Read first and last timestamps
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"Header: {header}")
    
    first_row = next(reader)
    print(f"First row: {first_row}")
    
    # Read last row
    last_row = None
    count = 1
    for row in reader:
        last_row = row
        count += 1

print(f"Last row: {last_row}")
print(f"Total bars: {count}")

# Parse dates
ts_col = 0  # timestamp column
first_ts = datetime.strptime(first_row[ts_col].strip(), "%Y-%m-%d %H:%M:%S")
last_ts = datetime.strptime(last_row[ts_col].strip(), "%Y-%m-%d %H:%M:%S")
days = (last_ts.date() - first_ts.date()).days

print(f"\nDate range: {first_ts} to {last_ts}")
print(f"Total days: {days}")
print(f"Baseline days: 1336")
print(f"New sweep days: 1599")

if days != 1599:
    print(f"\n*** MISMATCH: CSV has {days} days but new sweep reports 1599 ***")
if days != 1336:
    print(f"*** MISMATCH: CSV has {days} days but baseline reports 1336 ***")

# Check: does the CSV have the format the new sweep expects?
# The new sweep uses load_m5_csv with pip_size=0.07 (JPY pair)
# Let's check a few rows
print("\n=== SAMPLE ROWS ===")
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for i, row in enumerate(reader):
        if i < 3 or i >= count-3:
            print(f"  Row {i}: {row}")
        if i > 5:
            break
