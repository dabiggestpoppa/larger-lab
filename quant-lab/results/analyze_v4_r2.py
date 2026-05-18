import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_200148.json') as f:
    data = json.load(f)

print("=" * 80)
print("V4 ROUND 2 RESULTS")
print("=" * 80)

profitable = 0
for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        pf = r['profit_factor']
        status = "PROFITABLE" if pf > 1.0 else "LOSING"
        if pf > 1.0:
            profitable += 1
        print(f"{name}:")
        print(f"  Trades: {r['total_trades']} | WR: {r['win_rate']}% | PF: {pf} | MaxDD: {r['max_dd']}p | P&L: {r['total_pnl']}p")
        print(f"  Exits: {r.get('by_exit', {})}")
        print(f"  Status: {status}")
        print()

print(f"Profitable: {profitable}/10 = {profitable*10}%")
print()

# V3 -> V4r1 -> V4r2 comparison for the 3 problem strategies
print("=" * 80)
print("V3 -> V4 Round 1 -> V4 Round 2 (PROBLEM STRATEGIES)")
print("=" * 80)

comparison = {
    'Two_Plays':        {'v3': (38.0, 0.84, -379.6), 'v4r1': (57.4, 0.94, -144.8), 'v4r2': (36.4, 0.92, -256.7)},
    'Dual_Engine':      {'v3': (32.4, 0.87, -287.7), 'v4r1': (57.3, 0.97, -73.4),  'v4r2': (36.7, 0.94, -191.4)},
    'Alpha_Combination':{'v3': (31.9, 0.92, -68.2),  'v4r1': (57.3, 0.97, -31.5),  'v4r2': (37.6, 1.04, 46.6)},
}

for name, v in comparison.items():
    print(f"{name}:")
    print(f"  V3:      WR {v['v3'][0]}% | PF {v['v3'][1]} | PnL {v['v3'][2]}p")
    print(f"  V4 R1:   WR {v['v4r1'][0]}% | PF {v['v4r1'][1]} | PnL {v['v4r1'][2]}p")
    print(f"  V4 R2:   WR {v['v4r2'][0]}% | PF {v['v4r2'][1]} | PnL {v['v4r2'][2]}p")
    print()
