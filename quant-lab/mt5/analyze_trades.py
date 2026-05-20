import json
from collections import Counter

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_mt5_trades.json") as f:
    trades = json.load(f)

losses = [t for t in trades if t["pnl_pips"] <= 0]
wins = [t for t in trades if t["pnl_pips"] > 0]

print("Total trades:", len(trades))
print("Wins:", len(wins), "Losses:", len(losses))
print()
if wins:
    print("Avg win pips:", round(sum(t["pnl_pips"] for t in wins)/len(wins), 2))
if losses:
    print("Avg loss pips:", round(sum(t["pnl_pips"] for t in losses)/len(losses), 2))
print()

reasons = Counter(t["exit_reason"] for t in trades)
print("Exit reasons:")
for r, c in reasons.most_common():
    print("  {}: {}".format(r, c))
print()

print("SL hits by tier:")
for tier in ["T1", "T2", "T3"]:
    t_trades = [t for t in trades if t["tier"] == tier]
    sl_hits = [t for t in t_trades if t["exit_reason"] == "sl"]
    if t_trades:
        print("  {}: {}/{} SL hits ({:.1f}%)".format(tier, len(sl_hits), len(t_trades), len(sl_hits)/len(t_trades)*100))
print()

sl_dists = []
for t in trades:
    sl_dist = abs(t["entry_price"] - t["sl"]) / 0.0001
    sl_dists.append(sl_dist)
if sl_dists:
    print("Avg SL distance (pips):", round(sum(sl_dists)/len(sl_dists), 1))
    print("Min SL:", round(min(sl_dists), 1), "Max SL:", round(max(sl_dists), 1))
print()

tp_dists = []
for t in trades:
    tp_dist = abs(t["tp2"] - t["entry_price"]) / 0.0001
    tp_dists.append(tp_dist)
if tp_dists:
    print("Avg TP2 distance (pips):", round(sum(tp_dists)/len(tp_dists), 1))
print()

asian_ranges = [t["asian_range"] for t in trades if t.get("asian_range")]
if asian_ranges:
    print("Avg Asian Range (pips):", round(sum(asian_ranges)/len(asian_ranges), 1))
    print("Min AR:", round(min(asian_ranges), 1), "Max AR:", round(max(asian_ranges), 1))
print()

print("Sample trades:")
for t in trades[:5]:
    print("  {} {} entry={} sl={} tp2={} pnl={}p {}".format(
        t["direction"], t["entry_time"][:16], t["entry_price"], 
        round(t["sl"], 5), round(t["tp2"], 5), t["pnl_pips"], t["exit_reason"]
    ))
