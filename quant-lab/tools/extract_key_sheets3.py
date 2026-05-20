import openpyxl
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\wifik\Downloads\cerebus 3 market hoily grail.xlsx', read_only=True, data_only=True)

def get_all_data(wb, sheet_name):
    ws = wb[sheet_name]
    return list(ws.iter_rows(values_only=True))

print("=== REKEY HYPOTHESIS TEST RESULTS ===")
rows = get_all_data(wb, "REKEY HYPOTHESIS TEST RESULTS")
for i, row in enumerate(rows[:85]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Cross_Market_Comparison ===")
rows = get_all_data(wb, "Cross_Market_Comparison")
for i, row in enumerate(rows[:35]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== EURUSD_TOLERANCE_ANALYSIS ===")
rows = get_all_data(wb, "EURUSD_TOLERANCE_ANALYSIS")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Validation Checklist ===")
rows = get_all_data(wb, "Validation Checklist")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Low-Freq High-Accuracy Tracker ===")
rows = get_all_data(wb, "Low-Freq High-Accuracy Tracker")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== session_data_full_week - headers ===")
rows = get_all_data(wb, "session_data_full_week")
print(f"Total rows: {len(rows)}")
all_headers = [str(h) for h in rows[0] if h is not None]
print(f"Headers: {all_headers}")
# Sample rows
count = 0
for row in rows[1:]:
    if any(v is not None for v in row):
        print([str(v) for v in row[:25]])
        count += 1
        if count >= 5:
            break

print("\n\n=== ETH_Fib_Analysis ===")
rows = get_all_data(wb, "ETH_Fib_Analysis")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== PHASE 3 - SESSION CORRELATION MATRIX ===")
rows = get_all_data(wb, "PHASE 3 - SESSION CORRELATION MATRIX")
for i, row in enumerate(rows[:105]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

wb.close()
