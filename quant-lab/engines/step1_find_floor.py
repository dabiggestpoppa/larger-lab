import json, os

reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'
for fname in os.listdir(reports_dir):
    if not fname.endswith('.json'):
        continue
    path = os.path.join(reports_dir, fname)
    with open(path) as f:
        d = json.load(f)
    if 'EURUSD' not in d:
        continue
    eurusd = d['EURUSD']
    if isinstance(eurusd, list):
        for e in eurusd:
            t = e.get('trades', 0)
            if t > 4000:
                t1 = e.get('t1_trigger', '?')
                wr = e.get('wr', 0)
                td = e.get('tr_per_day', 0)
                print(f'{fname}: trigger={t1} trades={t} wr={wr:.1f}% td={td:.2f}')
    elif isinstance(eurusd, dict):
        for k, v in eurusd.items():
            if isinstance(v, dict) and 'trades' in v and v.get('trades', 0) > 4000:
                print(f'{fname}[{k}]: trades={v["trades"]} wr={v.get("wr",0):.1f}%')
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and e.get('trades', 0) > 4000:
                        t1 = e.get('t1_trigger', '?')
                        wr = e.get('wr', 0)
                        td = e.get('tr_per_day', 0)
                        print(f'{fname}[{k}]: trigger={t1} trades={e["trades"]} wr={wr:.1f}% td={td:.2f}')
