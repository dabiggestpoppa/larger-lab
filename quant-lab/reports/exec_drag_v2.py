#!/usr/bin/env python3
"""Execution drag analysis v2 — proper weighted basket calc"""
import json

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json") as f:
    acc = json.load(f)

hex_pairs = ["EURJPY", "EURNZD", "GBPNZD", "EURAUD", "GBPAUD", "GBPCAD"]

print("=" * 110)
print("LOW COST HEX — EXECUTION DRAG ANALYSIS")
print("Commission: $0.07/trade flat | Lot: 0.01 | Value: $10/pip for forex")
print("=" * 110)

# Collect per-pair data
pair_data = {}
for pair in hex_pairs:
    if pair not in acc:
        print(f"{pair}: NOT FOUND")
        continue
    entries = acc[pair]
    floor = max(entries, key=lambda e: e.get("trades", 0))
    t = floor["trades"]
    wr = floor["wr"]
    aw = floor["avg_w"]
    al = floor["avg_l"]  # negative number
    rr = abs(aw / al) if al != 0 else 0
    exp = floor["exp"]
    pf = floor["pf"]
    pnl = floor["pnl"]
    nw = round(t * wr / 100)
    nl = t - nw
    net_usd = pnl * 0.1 - t * 0.07  # pips * 0.01 * $10/pipe - comm

    pair_data[pair] = {"t": t, "wr": wr, "aw": aw, "al": al, "rr": rr, "exp": exp,
                        "pf": pf, "pnl": pnl, "nw": nw, "nl": nl, "net_usd": net_usd}

    print(f"\n{pair}: WR={wr:.1f}% | PF={pf:.1f} | AvgW={aw:.1f}p | AvgL={al:.1f}p | RR={rr:.2f} | Exp={exp:.2f}p")
    print(f"  {t} trades ({nw}W/{nl}L) | PnL={pnl:.0f}p | Net=${net_usd:.0f} (after $0.07/trade)")

    for bp in [10, 15, 20, 25, 30]:
        bad = round(nw * bp / 100)
        nnw = nw - bad
        nnl = nl + bad
        nwr = nnw / t * 100
        npnl = nnw * aw + nnl * al
        nexp = npnl / t
        npf = (nnw * aw) / abs(nnl * al) if nnl * al != 0 else 999
        net = npnl * 0.1 - t * 0.07
        stat = "OK" if nexp > 0 else "DEAD"
        print(f"  Bad {bp:2d}%: WR={nwr:.1f}% | PF={npf:.1f} | Exp={nexp:.2f}p | Net=${net:.0f} | {stat}")

# Proper combined: weight by trade count
print("\n" + "=" * 110)
print("COMBINED BASKET — weighted by trades")
print("=" * 110)
total_t = sum(d["t"] for d in pair_data.values())
total_nw = sum(d["nw"] for d in pair_data.values())
total_nl = sum(d["nl"] for d in pair_data.values())
total_pnl = sum(d["pnl"] for d in pair_data.values())
# Weighted avg win/loss
w_aw = sum(d["aw"] * d["nw"] for d in pair_data.values()) / total_nw if total_nw > 0 else 0
w_al = sum(d["al"] * d["nl"] for d in pair_data.values()) / total_nl if total_nl > 0 else 0
bwr = total_nw / total_t * 100
brr = abs(w_aw / w_al) if w_al != 0 else 0
bexp = total_pnl / total_t
bnet = total_pnl * 0.1 - total_t * 0.07
# Breakeven: WR * AvgW + (1-WR) * AvgL = 0
# WR = |AvgL| / (AvgW + |AvgL|)
be_wr = abs(w_al) / (w_aw + abs(w_al)) * 100

print(f"WR={bwr:.1f}% | {total_t} trades ({total_nw}W/{total_nl}L)")
print(f"AvgW={w_aw:.1f}p | AvgL={w_al:.1f}p | RR={brr:.2f} | Exp={bexp:.2f}p")
print(f"Net=${bnet:.0f} (after comm) | Breakeven WR={be_wr:.1f}%")
print(f"Margin: {bwr - be_wr:.1f}pp above breakeven")
print(
    f"Max bad fills before BE: {int(total_nw * (bwr - be_wr) / bwr)} trades "
    f"({(bwr - be_wr) / bwr * 100:.1f}% of wins)"
)

for bp in [10, 15, 20, 25, 30, 40, 50]:
    bad = round(total_nw * bp / 100)
    nnw = total_nw - bad
    nnl = total_nl + bad
    nwr = nnw / total_t * 100
    npnl = nnw * w_aw + nnl * w_al
    nexp = npnl / total_t
    npf = (nnw * w_aw) / abs(nnl * w_al) if nnl * w_al != 0 else 999
    net = npnl * 0.1 - total_t * 0.07
    stat = "OK" if nexp > 0 else "DEAD"
    print(f"  Bad {bp:2d}%: WR={nwr:.1f}% | PF={npf:.1f} | Exp={nexp:.2f}p | Net=${net:.0f} | {stat}")

# Per day
days = 1600
tpd = total_t / days
npd = bnet / days
print(f"\nPer day: {tpd:.1f} tr/day | ${npd:.2f}/day | ${npd*365:.0f}/yr")

# Key R:R insight
print(f"\n--- KEY R:R / WR MATH ---")
print(f"To be profitable: WR > |AvgL| / (AvgW + |AvgL|) = |{w_al:.1f}| / ({w_aw:.1f} + |{w_al:.1f}|) = {be_wr:.1f}%")
print(f"Current WR ({bwr:.1f}%) gives edge of {bwr - be_wr:.1f}pp")
print(f"Each 1pp drop in WR costs ~${bnet * 0.01 / (bwr - be_wr) * 1:.0f} (approx)")
print(f"Risk:Reward per trade = 1:{brr:.2f} (AvgW:AvgL)")
print(f"With WR={bwr:.1f}% and RR=1:{brr:.2f}, every 100 trades nets ~{bexp * 100:.0f}p = ${bexp * 100 * 0.1:.0f}")
