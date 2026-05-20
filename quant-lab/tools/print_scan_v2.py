import json
import sys

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research\excel_scan_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

out_lines = []

for key in sorted(data.keys()):
    sheet = data[key]
    if 'error' in sheet:
        out_lines.append(f'{key}: ERROR - {sheet["error"]}')
        continue
    headers = sheet.get('headers', [])
    sample = sheet.get('sample_rows', [])
    out_lines.append(f'=== {key} ===')
    out_lines.append(f'  Max Row: {sheet["max_row"]} | Max Col: {sheet["max_col"]} | Scanned: {sheet["scanned_rows"]}')
    out_lines.append(f'  Headers ({len(headers)}):')
    for coord, val in headers[:50]:
        out_lines.append(f'    {coord}: {val}')
    if len(headers) > 50:
        out_lines.append(f'    ... and {len(headers)-50} more columns')
    out_lines.append(f'  Sample rows: {len(sample)}')
    for ri, row in enumerate(sample[:5]):
        out_lines.append(f'    Row {ri+2}: {[(c, str(v)[:80]) for c,v in row[:25]]}')
    out_lines.append('')

output = '\n'.join(out_lines)
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\research\excel_structure_summary.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print(f"Written {len(out_lines)} lines")
