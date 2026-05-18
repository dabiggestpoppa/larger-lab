import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_201129.json') as f:
    data = json.load(f)

print("=" * 80)
print("V4 ROUND 3 RESULTS (Partial Profit Taking)")
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

# Full comparison V3 -> V4 R1 -> V4 R2 -> V4 R3
print("=" * 80)
print("FULL EVOLUTION: V3 -> V4 R1 -> V4 R2 -> V4 R3")
print("=" * 80)

# V3 results
v3 = {
    'Two_Plays':         (38.0, 0.84, -379.6),
    'Dual_Engine':       (32.4, 0.87, -287.7),
    'Alpha_Combination': (31.9, 0.92, -68.2),
}
# V4 R1 (SL/TP balance)
v4r1 = {
    'Two_Plays':         (57.4, 0.94, -144.8),
    'Dual_Engine':       (57.3, 0.97, -73.4),
    'Alpha_Combination': (57.3, 0.97, -31.5),
}
# V4 R2 (min R:R)
v4r2 = {
    'Two_Plays':         (36.4, 0.92, -256.7),
    'Dual_Engine':       (36.7, 0.94, -191.4),
    'Alpha_Combination': (37.6, 1.04, 46.6),
}
# V4 R3 (partial profit)
v4r3 = {
    'Two_Plays':         (71.3, 0.92, -118.1),
    'Dual_Engine':       (72.4, 0.96, -68.5),
    'Alpha_Combination': (57.3, 0.97, -31.5),
}

for name in v3:
    print(f"{name}:")
    print(f"  V3:    WR {v3[name][0]}% | PF {v3[name][1]} | PnL {v3[name][2]}p")
    print(f"  V4 R1: WR {v4r1[name][0]}% | PF {v4r1[name][1]} | PnL {v4r1[name][2]}p")
    print(f"  V4 R2: WR {v4r2[name][0]}% | PF {v4r2[name][1]} | PnL {v4r2[name][2]}p")
    print(f"  V4 R3: WR {v4r3[name][0]}% | PF {v4r3[name][1]} | PnL {v4r3[name][2]}p")
    print()

# Key insight
print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("Two_Plays and Dual_Engine have WR > 70% with partial profit but PF < 1.0.")
print("This means the avg loss (full SL hit before TP1) is much larger than avg win.")
print("The SL at 1.5x body is too wide. Need to either:")
print("  1. Tighten SL to 1.0x body (accept lower WR but better R:R)")
print("  2. Or use a tighter initial SL that only applies before TP1")
print()
print("Alpha_Combination: PF 0.97 with WR 57%. Close to 1.0.")
print("The SL at 1.5x body is the issue. Try 1.0x body.")
