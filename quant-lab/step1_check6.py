import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_usd.json') as f:
    d = json.load(f)

print("Keys:", list(d.keys()))
if 'EURUSD' in d:
    eurusd = d['EURUSD']
    print(f"\nEURUSD type: {type(eurusd)}, len: {len(eurusd) if isinstance(eurusd, list) else 'N/A'}")
    if isinstance(eurusd, list):
        for i, e in enumerate(eurusd):
            t1 = e.get('t1_trigger', '?')
            trades = e.get('trades', '?')
            wr = e.get('wr', 0)
            td = e.get('tr_per_day', 0)
            print(f'  [{i}] trigger={t1} trades={trades} wr={wr:.1f}% td={td:.2f}')
    else:
        print(json.dumps(eurusd, indent=2)[:2000])
