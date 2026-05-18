import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_202833.json') as f:
    data = json.load(f)

print("=" * 80)
print("V4 R6 FINAL RESULTS — GOALS.md COMPLIANCE CHECK")
print("=" * 80)

profitable = 0
dd_fail = 0
for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        pf = r['profit_factor']
        dd = abs(r['max_dd'])
        is_prof = pf > 1.0
        dd_ok = dd < 12.0
        if is_prof:
            profitable += 1
        if not dd_ok:
            dd_fail += 1
        prof_str = "PROFITABLE" if is_prof else "LOSING"
        dd_str = "OK" if dd_ok else "EXCEEDS 12%"
        print(f"{name}:")
        print(f"  Trades: {r['total_trades']} | WR: {r['win_rate']}% | PF: {pf} | MaxDD: {r['max_dd']}p | PnL: {r['total_pnl']}p")
        print(f"  Status: {prof_str} | MaxDD: {dd_str}")
        print()

print(f"Profitable: {profitable}/10 = {profitable*10}%")
print(f"MaxDD violations: {dd_fail}")
print()

# Check Goal 4: 80% WR strategy with ~2 trades/day
print("=" * 80)
print("GOAL 4 CHECK: 80% WR + ~2 trades/day")
print("=" * 80)
total_days = 1190  # ~3.26 years of M5 data
for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        wr = r['win_rate']
        tpd = r['total_trades'] / total_days
        if wr >= 80:
            print(f"  {name}: WR {wr}% | {tpd:.1f} trades/day | MEETS 80% WR TARGET")
        elif wr >= 70:
            print(f"  {name}: WR {wr}% | {tpd:.1f} trades/day | CLOSE to 80% WR target")
