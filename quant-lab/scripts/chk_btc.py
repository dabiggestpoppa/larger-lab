import json, os
REPORTS_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Check BTC in crypto sweep
with open(os.path.join(REPORTS_DIR, 'trigger_sweep_crypto.json')) as f:
    data = json.load(f)

for section, pairs in data.items():
    if isinstance(pairs, dict):
        for sym, entries in pairs.items():
            if 'BTC' in sym:
                print(f'{section}/{sym}: {len(entries)} entries')
                for e in entries:
                    print(f'  trigger={e.get("t1_trigger")} mult={e.get("multiplier")} trades={e.get("trades")} wr={e.get("wr")} pf={e.get("pf")} pnl={e.get("pnl")} days={e.get("days")} tr/d={e.get("tr_per_day")}')

# Check BTC in forex pkl
import pickle
with open(os.path.join(REPORTS_DIR, '_matrix_data.pkl'), 'rb') as f:
    pkl = pickle.load(f)

if 'BTCUSD' in pkl:
    print('\nBTC in pkl? YES')
    print(pkl['BTCUSD'])
else:
    print('\nBTC in pkl? NO')

# So BTC only comes from crypto JSON. Check which entry becomes CEILING vs FLOOR
print('\n--- BTC CEILING entries from crypto JSON ---')
btc_ceil = data.get('ceiling', {}).get('BTCUSD.PRO', [])
for e in btc_ceil:
    print(f'  mult={e.get("multiplier")} trigger={e.get("t1_trigger")} trades={e.get("trades")} wr={e.get("wr")} pf={e.get("pf")} pnl={e.get("pnl")} days={e.get("days")} tr/d={e.get("tr_per_day")}')
