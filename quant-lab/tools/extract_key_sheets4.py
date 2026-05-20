import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\wifik\Downloads\cerebus 3 market hoily grail.xlsx', read_only=True, data_only=True)

def get_all_data(wb, sheet_name):
    ws = wb[sheet_name]
    return list(ws.iter_rows(values_only=True))

print("=== ASIAN SESSION FAILURE ANALYSIS ===")
rows = get_all_data(wb, "ASIAN SESSION FAILURE ANALYSIS")
for i, row in enumerate(rows[:70]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== MONDAY-ASIAN SESSION CROSS-REF ===")
rows = get_all_data(wb, "MONDAY-ASIAN SESSION CROSS-REF")
for i, row in enumerate(rows[:50]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== PHASE 4 - TEMPORAL DELIVERY MAPPING ===")
rows = get_all_data(wb, "PHASE 4 - TEMPORAL DELIVERY MAPPING")
for i, row in enumerate(rows[:60]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== PHASE 5 - WILM ILM VELOCITY ANALYSIS ===")
rows = get_all_data(wb, "PHASE 5 - WILM ILM VELOCITY ANALYSIS")
for i, row in enumerate(rows[:60]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

wb.close()
