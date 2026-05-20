import openpyxl
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\wifik\Downloads\cerebus 3 market hoily grail.xlsx', read_only=True, data_only=True)

output_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research'
os.makedirs(output_dir, exist_ok=True)

def get_all_data(wb, sheet_name):
    ws = wb[sheet_name]
    return list(ws.iter_rows(values_only=True))

# Monday Fibonacci Calculations - headers + sample
print("=== monday_fibonacci_calculations ===")
rows = get_all_data(wb, "monday_fibonacci_calculations")
print(f"Total rows: {len(rows)}")
# Print header
print(f"Headers: {[str(h) for h in rows[0] if h is not None]}")
# Print first 5 data rows
count = 0
for row in rows[1:]:
    if any(v is not None for v in row):
        print([str(v) for v in row[:20]])
        count += 1
        if count >= 5:
            break

# Get ALL column headers
all_headers = [str(h) for h in rows[0]]
print(f"\nAll headers ({len(all_headers)}): {all_headers}")

print("\n\n=== EURUSD_WEEKLY_REKEYS ===")
rows = get_all_data(wb, "EURUSD_WEEKLY_REKEYS")
print(f"Total rows: {len(rows)}")
all_headers = [str(h) for h in rows[0]]
print(f"All headers ({len(all_headers)}): {all_headers}")
count = 0
for row in rows[1:]:
    if any(v is not None for v in row):
        print([str(v) for v in row])
        count += 1
        if count >= 5:
            break

print("\n\n=== EURUSD_Asian_Hit_Rates ===")
rows = get_all_data(wb, "EURUSD_Asian_Hit_Rates")
for row in rows:
    if any(v is not None for v in row):
        print([str(v) for v in row[:15]])

print("\n\n=== previous_day_targets ===")
rows = get_all_data(wb, "previous_day_targets")
print(f"Total rows: {len(rows)}")
all_headers = [str(h) for h in rows[0]]
print(f"Headers: {all_headers}")
count = 0
for row in rows[1:]:
    if any(v is not None for v in row):
        print([str(v) for v in row])
        count += 1
        if count >= 3:
            break

print("\n\n=== PHASE 2 - OVERLAP ANALYSIS ===")
rows = get_all_data(wb, "PHASE 2 - OVERLAP ANALYSIS")
print(f"Total rows: {len(rows)}")
for i, row in enumerate(rows[:50]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== measurement_comparison ===")
rows = get_all_data(wb, "measurement_comparison")
for row in rows:
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(non_empty)

print("\n\n=== top5_claims_validation ===")
rows = get_all_data(wb, "top5_claims_validation")
for row in rows:
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(non_empty)

print("\n\n=== quarterly_analysis ===")
rows = get_all_data(wb, "quarterly_analysis")
for row in rows:
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(non_empty)

print("\n\n=== TOLERANCE_COMPARISON_0.15_0.25_0.50 ===")
rows = get_all_data(wb, "TOLERANCE_COMPARISON_0.15_0.25_0.50")
print(f"Total rows: {len(rows)}")
for i, row in enumerate(rows[:50]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

wb.close()
