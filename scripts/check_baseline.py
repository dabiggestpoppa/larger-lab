import json

fpath = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'
with open(fpath) as f:
    data = json.load(f)

eurusd = data['EURUSD']
for e in eurusd:
    if e['trades'] == 5593:
        print('Baseline 5593 trades (t1=12):')
        print('  pnl=%.1f' % e['pnl'])
        print('  avg_w=%.2f' % e['avg_w'])
        print('  avg_l=%.2f' % e['avg_l'])
        print('  exp=%.2f' % e['exp'])
        print('  max_dd=%.1f' % e['max_dd'])
        print('  max_cw=%d' % e['max_cw'])
        print('  max_cl=%d' % e['max_cl'])
        print('  tr_per_day=%.2f' % e['tr_per_day'])
        break

# Also show the t1=10 entry if it exists
print()
for e in eurusd:
    if e['t1_trigger'] == 10.0:
        print('Baseline t1=10 entry:')
        print('  trades=%d, wr=%.1f%%, pf=%.1f' % (e['trades'], e['wr'], e['pf']))
        break
