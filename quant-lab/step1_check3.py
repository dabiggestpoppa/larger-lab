import json, os

reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'
for fname in os.listdir(reports_dir):
    if not fname.endswith('.json'):
        continue
    path = os.path.join(reports_dir, fname)
    with open(path) as f:
        d = json.load(f)
    if 'EURUSD' in d:
        eurusd = d['EURUSD']
        if isinstance(eurusd, list):
            for e in eurusd:
                if e.get('trades', 0) > 6000:
                    print(f'{fname}: trigger={e.get("t1_trigger")} trades={e.get("trades")} wr={e.get("wr",0):.1f}% td={e.get("tr_per_day",0):.2f}')
        elif isinstance(eurusd, dict):
            print(f'{fname}: dict with keys {list(eurusd.keys())[:10]}')
