import json

with open('reports/cost_analysis_all.json', 'r') as f:
    data = json.load(f)

print('Pair         Spread  Comm    Total   WR_raw  WR_adj  PF_raw  PF_adj')
print('-' * 80)

for sym in sorted(data.keys()):
    c = data[sym]['costs']
    r = data[sym]['raw']
    a = data[sym]['adjusted']
    spread = c.get('spread_pips_per_trade', 0)
    comm = c.get('commission_pips_per_trade', 0)
    total = c.get('total_cost_pips_per_trade', 0)
    wr_raw = r.get('wr', 0)
    wr_adj = a.get('wr', 0)
    pf_raw = r.get('pf', 0)
    pf_adj = a.get('pf', 0)
    print(f'{sym:12s} {spread:6.3f}  {comm:6.3f}  {total:6.3f}  {wr_raw:6.1f}  {wr_adj:6.1f}  {pf_raw:6.1f}  {pf_adj:6.1f}')

# Check JPY pip_value
print('\n--- JPY pip_value check ---')
for sym in ['USDJPY', 'EURJPY', 'GBPJPY', 'CHFJPY', 'CADJPY', 'AUDJPY', 'NZDJPY']:
    if sym in data:
        pv = data[sym]['costs'].get('pip_value_per_lot', 0)
        print(f'{sym}: pip_value_per_lot={pv}')
