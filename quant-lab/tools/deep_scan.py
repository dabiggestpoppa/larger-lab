"""Deep scan of critical sheets with more rows and all columns."""
import openpyxl
import json

FILE_PATH = r'C:\Users\wifik\Downloads\cerebus 3 market hoily grail.xlsx'

# Sheets to deep scan with more rows
DEEP_SHEETS = {
    '01_PHASE 2 VALIDATION RESULTS': 100,
    '02_Delivery Stats': 100,
    '03_Pattern Formations': 50,
    '04_Pattern Failures & Rekeys': 50,
    '05_ILM Zone Behaviors': 50,
    '06_Session & Timing Metrics': 50,
    '07_Fibonacci Sequences Catalog': 50,
    '09_Failure Pattern Database': 50,
    '10_Low-Freq High-Accuracy Tracker': 50,
    '12_Hit Rate Analysis Framework': 50,
    '13_monday_fibonacci_calculations': 50,
    '23_PHASE 3C - TEMPORAL DELIVERY (REVISED)': 50,
    '24_PHASE 3C - PURE SYSTEM MECHANICS SUMMARY': 50,
    '32_session_data_full_week': 50,
}

wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)

results = {}
for sheet_name, max_rows in DEEP_SHEETS.items():
    # Extract actual sheet name (after the _ separator)
    actual_name = sheet_name.split('_', 1)[1]
    print(f"Deep scanning: {actual_name} (max {max_rows} rows)")
    ws = wb[actual_name]
    
    headers = []
    sample_rows = []
    row_count = 0
    
    for row in ws.iter_rows(max_row=max_rows, values_only=False):
        row_count += 1
        vals = [(cell.coordinate, cell.value) for cell in row if cell.value is not None]
        if row_count == 1:
            headers = vals
        else:
            if vals:
                sample_rows.append(vals)
    
    results[sheet_name] = {
        'headers': [(c, v) for c, v in headers],
        'sample_rows': [[(c, str(v)[:100]) for c, v in row] for row in sample_rows[:10]],
        'total_rows_scanned': row_count,
    }

wb.close()

out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research\deep_scan_results.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)

print(f"\nDeep scan saved to {out_path}")
