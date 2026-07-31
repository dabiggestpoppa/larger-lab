import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_usdchf_trades.json") as f:
    trades = json.load(f)

pnls = [t["pnl"] for t in trades]
n = len(pnls)
gross = sum(pnls)
wins = [p for p in pnls if p > 0]
losses = [p for p in pnls if p < 0]

spread = 0.7
comm_per_lot = 7.0
lot_size = 0.01
pip_value = 0.10

spread_cost = spread * n * lot_size
comm_dollars = comm_per_lot * lot_size * n
comm_pips = comm_dollars / pip_value
net_pips = gross - spread_cost - comm_pips

print("=" * 60)
print("USDCHF DMR REAL COST ANALYSIS")
print("=" * 60)
print(f"Spread: {spread}p | Commission: ${comm_per_lot}/lot RT")
print(f"Lot size: {lot_size} | Pip value: ${pip_value}/pip")
print()
print(f"Gross PnL:       {gross:+.1f} pips  (${gross * pip_value:+.2f})")
print(f"Spread cost:     -{spread_cost:.1f} pips  (${spread_cost * pip_value:.2f})")
print(f"Commission:      -{comm_pips:.1f} pips  (${comm_dollars:.2f})")
print(f"Net PnL:         {net_pips:+.1f} pips  (${net_pips * pip_value:+.2f})")
print()
print(f"Avg trade gross: {gross / n:+.2f} pips")
print(f"Avg trade net:   {net_pips / n:+.2f} pips")
print()

wins_below_spread = len([p for p in pnls if 0 < p <= spread])
print(f"WR gross:        {len(wins) / n * 100:.1f}%")
print(f"WR with spread:  {(len(wins) - wins_below_spread) / n * 100:.1f}%")
print(f"Wins <= {spread}p: {wins_below_spread} trades flip to losses")
print()

monthly = defaultdict(list)
for t in trades:
    monthly[t["date"][:7]].append(t["pnl"])

negatives = []
print("=== MONTHLY WITH REAL COSTS ===")
print(f"{'Month':<10} {'Trades':>6} {'Gross p':>10} {'Net p':>10} {'Net $':>10} {'WR g':>7} {'WR n':>7}")
print("-" * 65)
for mo in sorted(monthly.keys()):
    mp = monthly[mo]
    mg = sum(mp)
    mn = mg - spread * len(mp) * lot_size - comm_per_lot * lot_size * len(mp) / pip_value
    wrg = sum(1 for p in mp if p > 0) / len(mp) * 100
    wrn = sum(1 for p in mp if p - spread > 0) / len(mp) * 100
    marker = " ***" if mn < 0 else ""
    if mn < 0:
        negatives.append((mo, mn))
    print(f"{mo:<10} {len(mp):>6} {mg:>+10.1f} {mn:>+10.1f} {mn * pip_value:>+10.2f} {wrg:>6.1f}% {wrn:>6.1f}%{marker}")

print()
if negatives:
    print(f"NEGATIVE MONTHS WITH REAL COSTS: {len(negatives)}")
    for m, mn in negatives:
        print(f"    {m}: {mn:+.1f} pips (${mn * pip_value:+.2f})")
else:
    print("ALL MONTHS STILL PROFITABLE WITH REAL COSTS")

print()
max_cl = max_cw = cl = cw = 0
for p in pnls:
    adj = p - spread
    if adj > 0:
        cw += 1; cl = 0; max_cw = max(max_cw, cw)
    elif adj < 0:
        cl += 1; cw = 0; max_cl = max(max_cl, cl)
    else:
        cw = cl = 0
print(f"Max consecutive wins (with spread):   {max_cw}")
print(f"Max consecutive losses (with spread): {max_cl}")
print()

daily = defaultdict(float)
for t in trades:
    daily[t["date"]] += t["pnl"] - spread * lot_size - (comm_per_lot * lot_size) / pip_value

daily_dates = sorted(daily.keys())
cum = 0
peak = 289.17
max_dd = 0
equity_list = []
for d in daily_dates:
    cum += daily[d] * pip_value
    eq = 289.17 + cum
    equity_list.append(eq)
    if eq > peak:
        peak = eq
    dd = peak - eq
    if dd > max_dd:
        max_dd = dd

print(f"Max DD with real costs: ${max_dd:.2f} ({max_dd / 289.17 * 100:.2f}%)")
print(f"Final equity (from $289.17): ${equity_list[-1]:.2f}")
print("=" * 60)
