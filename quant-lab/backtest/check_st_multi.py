import json
d = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json'))
print("Top keys:", list(d.keys()))
if 'per_asset' in d:
    for sym, s in d['per_asset'].items():
        print(f"{sym}: trades={s.get('trades')}, wr={s.get('wr')}, pnl={s.get('pnl')}")
elif 'results' in d:
    for sym, s in d['results'].items():
        print(f"{sym}: trades={s.get('trades')}, wr={s.get('wr')}, pnl={s.get('pnl')}")
