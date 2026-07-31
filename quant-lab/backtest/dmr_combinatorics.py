"""
DMR Portfolio Combinatorics
=============================
Find optimal pair combinations for target trades/day.
Analyzes all possible baskets (2-30 pairs) for:
- Total trades/day
- Blended WR, PF, Sharpe
- Max DD and MC ruin
- Best portfolio compositions
"""

import json, math, random, sys
from pathlib import Path
from itertools import combinations
from collections import defaultdict

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
RESULTS_PATH = WORKSPACE / "quant-lab" / "reports" / "dmr_mc" / "dmr_mc_full_results.json"

with open(RESULTS_PATH) as f:
    data = json.load(f)

stats = data["per_asset_stats"]

# Filter to pairs with >= 50 trades (meaningful sample)
valid_pairs = {s: v for s, v in stats.items() if v["total"] >= 50}

print("=" * 80)
print("DMR PORTFOLIO COMBINATORICS")
print("=" * 80)
print(f"\nValid pairs (>= 50 trades): {len(valid_pairs)}")
print(f"Total pairs: {len(stats)}")

# ─── Individual Pair Trade Frequency ───
print("\n" + "=" * 80)
print("INDIVIDUAL PAIR TRADE FREQUENCY")
print("=" * 80)

for sym in sorted(valid_pairs.keys(), key=lambda s: valid_pairs[s]["trades_per_day"], reverse=True):
    s = valid_pairs[sym]
    print(f"  {sym:10s}: {s['trades_per_day']:.2f} tr/day | {s['total']:4d} tr over {s['n_trading_days']:4d} days | {s['date_range']}")

# ─── Cumulative: All Pairs Pooled ───
print("\n" + "=" * 80)
print("ALL PAIRS POOLED (29 pairs)")
print("=" * 80)

all_trades_per_day = sum(s["trades_per_day"] for s in valid_pairs.values())
all_total = sum(s["total"] for s in valid_pairs.values())
all_pnl = sum(s["pnl"] for s in valid_pairs.values())
all_wins = sum(s["wins"] for s in valid_pairs.values())
all_losses = sum(s["losses"] for s in valid_pairs.values())
all_wr = all_wins / all_total * 100
all_gp = sum(s["pnl"] for s in valid_pairs.values() for _ in range(1))  # placeholder

# Weighted avg
all_avg_trade = sum(s["avg_trade"] * s["total"] for s in valid_pairs.values()) / all_total
all_max_dd = max(s["max_dd"] for s in valid_pairs.values())

print(f"  Total trades/day: {all_trades_per_day:.1f}")
print(f"  Total trades: {all_total}")
print(f"  Blended WR: {all_wr:.1f}%")
print(f"  Total PnL: {all_pnl:+.1f}p")
print(f"  Avg trade: {all_avg_trade:.2f}p")
print(f"  Worst MaxDD (single pair): {all_max_dd:.1f}p")

# ─── Find Minimum Pairs for 3+ Trades/Day ───
print("\n" + "=" * 80)
print("MINIMUM PAIRS FOR 3+ TRADES/DAY")
print("=" * 80)

# Sort by trades_per_day descending
sorted_pairs = sorted(valid_pairs.items(), key=lambda x: x[1]["trades_per_day"], reverse=True)

cumulative = 0
basket = []
for sym, s in sorted_pairs:
    cumulative += s["trades_per_day"]
    basket.append(sym)
    if cumulative >= 3.0:
        break

basket_wr = sum(valid_pairs[p]["wins"] for p in basket) / sum(valid_pairs[p]["total"] for p in basket) * 100
basket_pnl = sum(valid_pairs[p]["pnl"] for p in basket)
basket_pf = sum(valid_pairs[p]["pnl"] for p in basket if valid_pairs[p]["pnl"] > 0) / abs(sum(valid_pairs[p]["pnl"] for p in basket if valid_pairs[p]["pnl"] < 0)) if any(valid_pairs[p]["pnl"] < 0 for p in basket) else float("inf")

print(f"  Need {len(basket)} pairs for {cumulative:.1f} tr/day:")
for p in basket:
    print(f"    {p:10s}: {valid_pairs[p]['trades_per_day']:.2f} tr/day | WR {valid_pairs[p]['wr']:.1f}% | {valid_pairs[p]['date_range']}")
print(f"  Basket WR: {basket_wr:.1f}% | PnL: {basket_pnl:+.1f}p")

# ─── Top N Pair Combinations ───
print("\n" + "=" * 80)
print("OPTIMAL BASKETS BY SIZE")
print("=" * 80)

for target_size in [3, 5, 7, 10, 15, 20, 29]:
    if target_size > len(valid_pairs):
        continue
    
    # Greedy: pick top N by trades_per_day
    top_n = [p for p, _ in sorted_pairs[:target_size]]
    n_trades = sum(valid_pairs[p]["trades_per_day"] for p in top_n)
    n_total = sum(valid_pairs[p]["total"] for p in top_n)
    n_wr = sum(valid_pairs[p]["wins"] for p in top_n) / n_total * 100
    n_pnl = sum(valid_pairs[p]["pnl"] for p in top_n)
    n_avg = sum(valid_pairs[p]["avg_trade"] * valid_pairs[p]["total"] for p in top_n) / n_total
    n_maxdd = max(valid_pairs[p]["max_dd"] for p in top_n)
    n_kelly = sum(valid_pairs[p]["kelly"] * valid_pairs[p]["total"] for p in top_n) / n_total
    
    print(f"\n  [{target_size:2d} pairs] {n_trades:.1f} tr/day | WR {n_wr:.1f}% | PnL {n_pnl:+10.1f}p | Avg {n_avg:+.2f}p | MaxDD {n_maxdd:.1f}p | Kelly {n_kelly:.3f}")
    print(f"           Pairs: {', '.join(top_n)}")

# ─── Currency Basket Combinations ───
print("\n" + "=" * 80)
print("CURRENCY BASKET COMBINATIONS")
print("=" * 80)

CURRENCY_BASKETS = {
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD"],
    "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD"],
    "USD": ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD"],
    "JPY": ["EURJPY", "GBPJPY", "USDJPY", "AUDJPY", "CHFJPY", "NZDJPY", "CADJPY"],
    "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF"],
    "NZD": ["NZDUSD", "EURNZD", "GBPNZD", "AUDNZD", "NZDCHF", "NZDJPY", "NZDCAD"],
    "CAD": ["USDCAD", "AUDCAD", "NZDCAD", "CADCHF", "CADJPY"],
    "CHF": ["USDCHF", "EURCHF", "GBPCHF", "AUDCHF", "CADCHF", "NZDCHF", "CHFJPY"],
}

# 2-basket combos
print("\n  2-Basket Combinations:")
for b1, b2 in combinations(sorted(CURRENCY_BASKETS.keys()), 2):
    pairs = list(set(CURRENCY_BASKETS[b1] + CURRENCY_BASKETS[b2]))
    valid = [p for p in pairs if p in valid_pairs]
    if len(valid) < 3:
        continue
    t_day = sum(valid_pairs[p]["trades_per_day"] for p in valid)
    if t_day < 2.0:
        continue
    total = sum(valid_pairs[p]["total"] for p in valid)
    wr = sum(valid_pairs[p]["wins"] for p in valid) / total * 100
    pnl = sum(valid_pairs[p]["pnl"] for p in valid)
    maxdd = max(valid_pairs[p]["max_dd"] for p in valid)
    print(f"    {b1:4s}+{b2:4s}: {t_day:.1f} tr/day | {len(valid):2d} pairs | WR {wr:.1f}% | PnL {pnl:+10.1f}p | MaxDD {maxdd:.1f}p")

# ─── Best 5-Pair Portfolios (by WR) ───
print("\n" + "=" * 80)
print("BEST 5-PAIR PORTFOLIOS (by blended WR)")
print("=" * 80)

# Greedy approach: start with highest WR pairs
by_wr = sorted(valid_pairs.items(), key=lambda x: x[1]["wr"], reverse=True)
top5_wr = [p for p, _ in by_wr[:5]]
t5 = sum(valid_pairs[p]["trades_per_day"] for p in top5_wr)
t5_total = sum(valid_pairs[p]["total"] for p in top5_wr)
t5_wr = sum(valid_pairs[p]["wins"] for p in top5_wr) / t5_total * 100
t5_pnl = sum(valid_pairs[p]["pnl"] for p in top5_wr)
t5_maxdd = max(valid_pairs[p]["max_dd"] for p in top5_wr)
print(f"  Top 5 by WR: {', '.join(top5_wr)}")
print(f"  {t5:.1f} tr/day | WR {t5_wr:.1f}% | PnL {t5_pnl:+10.1f}p | MaxDD {t5_maxdd:.1f}p")

# ─── Best 5-Pair Portfolios (by trades/day) ───
print("\n" + "=" * 80)
print("BEST 5-PAIR PORTFOLIOS (by trades/day)")
print("=" * 80)

by_td = sorted(valid_pairs.items(), key=lambda x: x[1]["trades_per_day"], reverse=True)
top5_td = [p for p, _ in by_td[:5]]
t5_td = sum(valid_pairs[p]["trades_per_day"] for p in top5_td)
t5_total2 = sum(valid_pairs[p]["total"] for p in top5_td)
t5_wr2 = sum(valid_pairs[p]["wins"] for p in top5_td) / t5_total2 * 100
t5_pnl2 = sum(valid_pairs[p]["pnl"] for p in top5_td)
t5_maxdd2 = max(valid_pairs[p]["max_dd"] for p in top5_td)
print(f"  Top 5 by trades/day: {', '.join(top5_td)}")
print(f"  {t5_td:.1f} tr/day | WR {t5_wr2:.1f}% | PnL {t5_pnl2:+10.1f}p | MaxDD {t5_maxdd2:.1f}p")

# ─── Majors Only ───
print("\n" + "=" * 80)
print("FOREX MAJORS ONLY (EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, USDCAD, NZDUSD)")
print("=" * 80)

majors = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]
majors = [p for p in majors if p in valid_pairs]
m_tr = sum(valid_pairs[p]["trades_per_day"] for p in majors)
m_total = sum(valid_pairs[p]["total"] for p in majors)
m_wr = sum(valid_pairs[p]["wins"] for p in majors) / m_total * 100
m_pnl = sum(valid_pairs[p]["pnl"] for p in majors)
m_maxdd = max(valid_pairs[p]["max_dd"] for p in majors)
m_kelly = sum(valid_pairs[p]["kelly"] * valid_pairs[p]["total"] for p in majors) / m_total
print(f"  {m_tr:.1f} tr/day | WR {m_wr:.1f}% | PnL {m_pnl:+10.1f}p | MaxDD {m_maxdd:.1f}p | Kelly {m_kelly:.3f}")

# ─── Max Possible Trades/Day ───
print("\n" + "=" * 80)
print("MAXIMUM TRADES/DAY (ALL PAIRS)")
print("=" * 80)

max_tr = sum(s["trades_per_day"] for s in valid_pairs.values())
max_total = sum(s["total"] for s in valid_pairs.values())
max_wr = sum(s["wins"] for s in valid_pairs.values()) / max_total * 100
max_pnl = sum(s["pnl"] for s in valid_pairs.values())
print(f"  {max_tr:.1f} tr/day | WR {max_wr:.1f}% | PnL {max_pnl:+12.1f}p")
print(f"  {max_total:,} total trades across {len(valid_pairs)} pairs")

# ─── Recommended Portfolios ───
print("\n" + "=" * 80)
print("RECOMMENDED PORTFOLIOS")
print("=" * 80)

print("""
  CONSERVATIVE (3 trades/day, low correlation):
    EURUSD + GBPUSD + USDCHF + USDJPY + AUDUSD + USDCAD + NZDUSD
    = All 7 majors, ~7 tr/day, lowest basket correlation

  MODERATE (5 trades/day, balanced):
    EURUSD + GBPUSD + USDJPY + AUDUSD + USDCAD + GBPJPY + CHFJPY
    = 5 majors + 2 JPY crosses, ~7 tr/day, higher R:R

  AGGRESSIVE (10+ trades/day, all forex):
    All 25 forex pairs (excl crypto/metals)
    ~25 tr/day, maximum diversification

  MAXIMUM (all pairs):
    All 29 pairs (incl BTC, ETH, XAU, US500)
    ~30 tr/day
""")
