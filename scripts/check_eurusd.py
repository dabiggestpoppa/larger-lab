import json

fpath = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'
with open(fpath) as f:
    data = json.load(f)

eurusd = data['EURUSD']
print('EURUSD max accuracy sweep entries:')
for e in eurusd:
    t1 = e['t1_trigger']
    tr = e['trades']
    wr = e['wr']
    pf = e['pf']
    print(f'  t1={t1:>5}, trades={tr:>5}, wr={wr:.1f}%, pf={pf:.1f}')

# Also check the floor sweep for EURUSD from the remaining_eur file
import os
for fname in ['trigger_sweep_remaining_eur.json', 'trigger_sweep_eur.json']:
    fpath2 = os.path.join(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports', fname)
    if os.path.exists(fpath2):
        with open(fpath2) as f:
            data2 = json.load(f)
        if isinstance(data2, dict) and 'EURUSD' in data2:
            print(f'\n{fname} EURUSD:')
            eurusd2 = data2['EURUSD']
            if isinstance(eurusd2, list):
                for e in eurusd2[:5]:
                    t1 = e.get('t1_trigger', '?')
                    tr = e.get('trades', '?')
                    print(f'  t1={t1}, trades={tr}')
