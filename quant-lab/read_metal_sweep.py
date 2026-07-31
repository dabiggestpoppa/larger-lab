import json
d = json.load(open('reports/trigger_sweep_metals_indices.json'))
for pair in ['XAUUSD','XAGUSD','US500','DE30','FR40','HK50']:
    if pair in d:
        v = d[pair]
        if isinstance(v, list) and len(v) > 0:
            print(f'{pair}: {len(v)} sweep points')
            for p in v[:3]:
                if isinstance(p, dict):
                    print(f'  trig={p.get(\"t1_trigger\",0):.1f} wr={p.get(\"wr\",0):.1f}%')
        elif isinstance(v, dict):
            print(f'{pair}: {list(v.keys())}')
d2 = json.load(open('reports/trigger_sweep_crypto.json'))
for level in ['floor', 'ceiling']:
    if level in d2:
        for pair in ['BTCUSD', 'ETHUSD']:
            if pair in d2[level]:
                f = d2[level][pair]
                if isinstance(f, dict):
                    print(f'{pair} ({level}): trig={f.get(\"t1_trigger\",0):.1f} wr={f.get(\"wr\",0):.1f}%')