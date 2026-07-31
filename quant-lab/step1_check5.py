import json

# The max_accuracy sweep only has triggers 12-27
# The floor data (7,134 trades) must be from a different sweep
# Let me check ALL json files for EURUSD with ~7134 trades

import os
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
            if 7000 <= t <= 7300:
                print(f'{fname}: trigger={e.get("t1_trigger")} trades={t} wr={e.get("wr",0):.1f}% td={e.get("tr_per_day",0):.2f}')
            elif t >= 5000:
                print(f'{fname} [5k+]: trigger={e.get("t1_trigger")} trades={t} wr={e.get("wr",0):.1f}% td={e.get("tr_per_day",0):.2f}')
    elif isinstance(eurusd, dict):
        # Check nested
        for k, v in eurusd.items():
            if isinstance(v, dict) and 'trades' in v:
                t = v.get('trades', 0)
                if t >= 5000:
                    print(f'{fname}[{k}]: trades={t} wr={v.get("wr",0):.1f}%')
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and 'trades' in e:
                        t = e.get('trades', 0)
                        if t >= 5000:
                            print(f'{fname}[{k}]: trigger={e.get("t1_trigger")} trades={t} wr={e.get("wr",0):.1f}%')
