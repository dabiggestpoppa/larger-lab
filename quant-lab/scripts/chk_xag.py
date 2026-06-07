import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_metals_indices.json') as f:
    data = json.load(f)
print('XAGUSD sweep results:')
for e in data['XAGUSD']['floor']:
    print(f"  mult={e['multiplier']:.1f} | trigger={e['t1_trigger']:.1f} | trades={e['trades']:5d} | WR={e['wr']:.1f}% | PF={e['pf']:.2f} | pnl={e['pnl']:.1f} | tr/d={e['tr_per_day']:.3f}")

print()
print('XAUUSD sweep results:')
for e in data['XAUUSD']['floor']:
    print(f"  mult={e['multiplier']:.1f} | trigger={e['t1_trigger']:.1f} | trades={e['trades']:5d} | WR={e['wr']:.1f}% | PF={e['pf']:.2f} | pnl={e['pnl']:.1f} | tr/d={e['tr_per_day']:.3f}")

for asset in ['US500','DE30','FR40','HK50']:
    print()
    print(f'{asset} sweep results:')
    for e in data[asset]['floor']:
        print(f"  mult={e['multiplier']:.1f} | trigger={e['t1_trigger']:.1f} | trades={e['trades']:5d} | WR={e['wr']:.1f}% | PF={e['pf']:.2f} | pnl={e['pnl']:.1f} | tr/d={e['tr_per_day']:.3f}")
