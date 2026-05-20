import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research\excel_scan_results.json', 'r') as f:
    data = json.load(f)

for key in sorted(data.keys()):
    sheet = data[key]
    if 'error' in sheet:
        err = sheet['error']
        print(f'{key}: ERROR - {err}')
        continue
    headers = sheet.get('headers', [])
    sample = sheet.get('sample_rows', [])
    print(f'=== {key} ===')
    print(f'  Dims: {sheet["dimensions"]} | Rows: {sheet["max_row"]} | Cols: {sheet["max_col"]}')
    merged = sheet.get('merged_cells', [])
    if merged:
        print(f'  Merged cells: {merged[:5]}')
    print(f'  Headers ({len(headers)}):')
    for coord, val in headers[:40]:
        print(f'    {coord}: {val}')
    if len(headers) > 40:
        print(f'    ... and {len(headers)-40} more columns')
    print(f'  Sample rows: {len(sample)}')
    for ri, row in enumerate(sample[:5]):
        print(f'    Row {ri+2}: {[(c, str(v)[:60]) for c,v in row[:20]]}')
    print()
