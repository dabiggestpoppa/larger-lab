import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_195504.json') as f:
    data = json.load(f)

print("=" * 80)
print("V4 RESULTS ANALYSIS")
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

# V3 vs V4 comparison
print("=" * 80)
print("V3 -> V4 CHANGES")
print("=" * 80)
v3_data = {
    'Blind_Structural_Chain': {'wr': 25.6, 'pf': 1.10, 'pnl': 596.5},
    'Two_Plays': {'wr': 38.0, 'pf': 0.84, 'pnl': -379.6},
    'Dual_Engine': {'wr': 32.4, 'pf': 0.87, 'pnl': -287.7},
    'Fractal_Resolution': {'wr': 41.3, 'pf': 1.00, 'pnl': 11.4},
    'Alpha_Combination': {'wr': 31.9, 'pf': 0.92, 'pnl': -68.2},
}

v4_data = {
    'Blind_Structural_Chain': {'wr': 37.2, 'pf': 1.02, 'pnl': 153.2},
    'Two_Plays': {'wr': 57.4, 'pf': 0.94, 'pnl': -144.8},
    'Dual_Engine': {'wr': 57.3, 'pf': 0.97, 'pnl': -73.4},
    'Fractal_Resolution': {'wr': 49.4, 'pf': 1.04, 'pnl': 147.2},
    'Alpha_Combination': {'wr': 57.3, 'pf': 0.97, 'pnl': -31.5},
}

for name in v3_data:
    v3 = v3_data[name]
    v4 = v4_data[name]
    wr_delta = v4['wr'] - v3['wr']
    pf_delta = v4['pf'] - v3['pf']
    pnl_delta = v4['pnl'] - v3['pnl']
    print(f"{name}:")
    print(f"  WR: {v3['wr']}% -> {v4['wr']}% ({wr_delta:+.1f}%)")
    print(f"  PF: {v3['pf']} -> {v4['pf']} ({pf_delta:+.2f})")
    print(f"  PnL: {v3['pnl']}p -> {v4['pnl']}p ({pnl_delta:+.1f}p)")
    print()
