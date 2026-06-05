import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    d = json.load(f)

eurusd = d['EURUSD']
print('EURUSD entries:', len(eurusd))
for i, e in enumerate(eurusd):
    t1 = e.get('t1_trigger', '?')
    trades = e.get('trades', '?')
    wr = e.get('wr', 0)
    td = e.get('tr_per_day', 0)
    print(f'[{i}] trigger={t1} trades={trades} wr={wr:.1f}% td={td:.2f}')
