#!/usr/bin/env python3
"""Execution drag analysis — Low Cost Hex"""
import json

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json") as f:
    acc = json.load(f)

hex_pairs = ["EURJPY", "EURNZD", "GBPNZD", "EURAUD", "GBPAUD", "GBPCAD"]

print("=" * 100)
print("LOW COST HEX — EXECUTION DRAG ANALYSIS")
print("Commission: $0.07/trade flat | Lot: 0.01 | $10/pip for all forex")
print("=" * 100)

grand_trades = 0
grand_wins = 0
grand_pnl = 0.0

for pair in hex_pairs:
    if pair not in acc:
        print(f"{pair}: NOT FOUND")
        continue
    entries = acc[pair]
    floor = max(entries, key=lambda e: e.get("trades", 0))
    t = floor["trades"]
    wr = floor["wr"]
    aw = floor["avg_w"]
    al = floor["avg_l"]
    rr = abs(aw / al) if al != 0 else 0
    exp = floor["exp"]
    pf = floor["pf"]
    pnl = floor["pnl"]
    nw = int(t * wr / 100)
    nl = t - nw
    # Net USD: pips * 0.01 lot * $10/pip = pips * 0.1
    net_usd = pnl * 0.1 - t * 0.07
    grand_trades += t
    grand_wins += nw
    grand_pnl += pnl

    print(f"\n{pair}: WR={wr:.1f}% | PF={pf:.1f} | AvgW={aw:.1f}p | AvgL={al:.1f}p | RR={rr:.2f} | Exp={exp:.2f}p")
    print(f"  {t} trades | {nw}W/{nl}L | Net=${net_usd:.0f} (after $0.07/trade comm)")
    for bp in [10, 15, 20, 25, 30]:
        bad = int(nw * bp / 100)
        nnw = nw - bad
        nnl = nl + bad
        nwr = nnw / t * 100
        npnl = nnw * aw + nnl * al
        nexp = npnl / t
        npf = (nnw * aw) / abs(nnl * al) if nnl * al != 0 else 999
        net = npnl * 0.1 - t * 0.07
        stat = "PROFITABLE" if nexp > 0 else "DEAD"
        print(f"  Bad {bp:2d}%: WR={nwr:.1f}% | PF={npf:.1f} | Exp={nexp:.2f}p | Net=${net:.0f} | {stat}")

# Combined basket
print("\n" + "=" * 100)
print("COMBINED BASKET (all 6 pairs)")
print("=" * 100)
bwr = grand_wins / grand_trades * 100
gl = grand_trades - grand_wins
baw = grand_pnl / grand_wins if grand_wins > 0 else 0
bal = grand_pnl / gl if gl > 0 else 0
brr = abs(baw / bal) if bal != 0 else 0
bexp = grand_pnl / grand_trades
bnet = grand_pnl * 0.1 - grand_trades * 0.07
print(f"WR={bwr:.1f}% | {grand_trades} trades | AvgW={baw:.1f}p | AvgL={bal:.1f}p | RR={brr:.2f} | Exp={bexp:.2f}p")
print(f"Net=${bnet:.0f} (after comm)")

for bp in [10, 15, 20, 25, 30]:
    bad = int(grand_wins * bp / 100)
    nnw = grand_wins - bad
    nnl = gl + bad
    nwr = nnw / grand_trades * 100
    npnl = nnw * baw + nnl * bal
    nexp = npnl / grand_trades
    npf = (nnw * baw) / abs(nnl * bal) if nnl * bal != 0 else 999
    net = npnl * 0.1 - grand_trades * 0.07
    stat = "PROFITABLE" if nexp > 0 else "DEAD"
    print(f"  Bad {bp:2d}%: WR={nwr:.1f}% | PF={npf:.1f} | Exp={nexp:.2f}p | Net=${net:.0f} | {stat}")

# Per day stats
days = 1600  # approx backtest period
grand_tpd = grand_trades / days
grand_net_pd = bnet / days
print(f"\nPer day: {grand_tpd:.1f} tr/day | ${grand_net_pd:.2f}/day | ${grand_net_pd*365:.0f}/yr (after comm)")

# Key insight: what WR do we need to break even?
# Exp = WR * AvgW + (1-WR) * AvgL = 0
# WR * AvgW = (1-WR) * |AvgL|
# WR = |AvgL| / (AvgW + |AvgL|)
breakeven_wr = abs(bal) / (baw + abs(bal)) * 100 if (baw + abs(bal)) > 0 else 0
print(f"\nBreakeven WR: {breakeven_wr:.1f}% (below this = losing money)")
print(f"Current WR: {bwr:.1f}% — Margin: {bwr - breakeven_wr:.1f} percentage points")
print(f"Max bad fill tolerance: can lose {int(grand_wins * (bwr - breakeven_wr) / bwr)} more trades before break-even")
