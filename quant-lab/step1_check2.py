import json

# Check EURUSD floor data in the main sweep files
for fname in ['trigger_sweep_usd.json', 'trigger_sweep_remaining_eur.json']:
    path = fr'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\{fname}'
    with open(path) as f:
        d = json.load(f)
    if 'EURUSD' in d:
        eurusd = d['EURUSD']
        print(f'\n=== {fname} ===')
        print(f'Entries: {len(eurusd) if isinstance(eurusd, list) else "dict"}')
        if isinstance(eurusd, list):
            for i, e in enumerate(eurusd):
                t1 = e.get('t1_trigger', '?')
                trades = e.get('trades', '?')
                wr = e.get('wr', 0)
                td = e.get('tr_per_day', 0)
                print(f'  [{i}] trigger={t1} trades={trades} wr={wr:.1f}% td={td:.2f}')
        elif isinstance(eurusd, dict):
            print(json.dumps(eurusd, indent=2)[:2000])
