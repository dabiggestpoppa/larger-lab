import pickle, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'
with open(os.path.join(reports, '_matrix_data.pkl'), 'rb') as f:
    data = pickle.load(f)

low_cost_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']
for p in low_cost_pairs:
    d = data.get(p, {})
    floor = d.get('FLOOR', {})
    if floor:
        print(f'{p}: FLOOR trades={floor.get("trades",0)}, wr={floor.get("wr",0):.1f}%, pf={floor.get("pf",0):.1f}, net=${floor.get("net_usd",0):.0f}, cost={floor.get("cost_pct",0):.1f}%')
        print(f'  trigger={floor.get("t1_trigger",0)}, au={floor.get("au_used",0)}, tr_per_day={floor.get("tr_per_day",0):.2f}')
    else:
        print(f'{p}: NO FLOOR DATA')
