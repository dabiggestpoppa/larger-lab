import openpyxl
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\wifik\Downloads\cerebus 3 market hoily grail.xlsx', read_only=True, data_only=True)

output_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research'
os.makedirs(output_dir, exist_ok=True)

def get_all_data(wb, sheet_name):
    """Get ALL data from a sheet"""
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    return rows

# 1. Delivery Stats - full data
print("=== Delivery Stats ===")
rows = get_all_data(wb, "Delivery Stats")
for i, row in enumerate(rows[:35]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Hit Rate Analysis Framework ===")
rows = get_all_data(wb, "Hit Rate Analysis Framework")
for i, row in enumerate(rows[:70]):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== hit_rate_summary ===")
rows = get_all_data(wb, "hit_rate_summary")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Pattern Formations ===")
rows = get_all_data(wb, "Pattern Formations")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Pattern Failures & Rekeys ===")
rows = get_all_data(wb, "Pattern Failures & Rekeys")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== ILM Zone Behaviors ===")
rows = get_all_data(wb, "ILM Zone Behaviors")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Session & Timing Metrics ===")
rows = get_all_data(wb, "Session & Timing Metrics")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

print("\n\n=== Fibonacci Sequences Catalog ===")
rows = get_all_data(wb, "Fibonacci Sequences Catalog")
for i, row in enumerate(rows):
    non_empty = [str(v) for v in row if v is not None]
    if non_empty:
        print(f"Row {i}: {non_empty}")

wb.close()
