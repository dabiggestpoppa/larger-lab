"""
PORTFOLIO CONFIG MATRIX GENERATOR
==================================
For all assets with per_trade_pnl MC data, generate:
- All 2-asset combos with MC
- All 3-asset combos with MC
- All 4-asset combos with MC
- Greedy expansion 5-14 assets
- Summary markdown report
"""
import sys, json, random, math
from pathlib import Path
from itertools import combinations
from datetime import datetime

QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
sys.path.insert(0, str(QUANT_LAB / "configs"))
from asset_configs import ASSET_CONFIGS

OUT_DIR = QUANT_LAB / "backtest" / "portfolio_matrix"
OUT_DIR.mkdir(exist_ok=True)
MC_DIR = QUANT_LAB / "reports" / "per-asset"
N_SIMS = 5000
random.seed(42)

# ─── Load per-asset MC trade P&Ls ───
print("Loading per-asset MC data...")
ASSETS = []
ASSET_PNL = {}
ASSET_STATS = {}

for sym in sorted(ASSET_CONFIGS.keys()):
    mc_file = MC_DIR / (sym + "_mc_results.json")
    if not mc_file.exists():
        continue
    d = json.load(open(mc_file))
    pnls = d.get("per_trade_pnl", [])
    if len(pnls) < 10:
        print(f"  SKIP {sym}: only {len(pnls)} trades")
        continue
    ASSETS.append(sym)
    ASSET_PNL[sym] = pnls
    wins = sum(1 for p in pnls if p > 0)
    gross_win = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    ASSET_STATS[sym] = {
        "trades": len(pnls),
        "wr": round(wins / len(pnls) * 100, 1),
        "pnl": round(sum(pnls), 1),
        "pf": round(pf, 2),
        "avg_pnl": round(sum(pnls) / len(pnls), 2),
    }

n = len(ASSETS)
print(f"Loaded {n} assets with trade data: {ASSETS}")

# ─── Portfolio MC function ───
def run_portfolio_mc(asset_list):
    pooled = []
    for sym in asset_list:
        pooled.extend(ASSET_PNL[sym])
    if not pooled:
        return None
    n_trades = len(pooled)
    wins_list = [p for p in pooled if p > 0]
    losses_list = [p for p in pooled if p <= 0]
    total_wr = len(wins_list) / n_trades * 100
    total_pnl = sum(pooled)
    gross_profit = sum(wins_list)
    gross_loss = abs(sum(losses_list)) if losses_list else 0.01
    pf = gross_profit / gross_loss

    terminal_pnls = []
    max_dds = []
    for _ in range(N_SIMS):
        shuffled = random.sample(pooled, n_trades)
        terminal_pnls.append(sum(shuffled))
        cumulative = 0; peak = 0; max_dd = 0
        for p in shuffled:
            cumulative += p
            if cumulative > peak: peak = cumulative
            dd = peak - cumulative
            if dd > max_dd: max_dd = dd
        max_dds.append(max_dd)

    terminal_pnls.sort()
    max_dds.sort()
    nt = len(terminal_pnls)

    return {
        "n_assets": len(asset_list),
        "assets": list(asset_list),
        "total_trades": n_trades,
        "win_rate": round(total_wr, 1),
        "total_pnl": round(total_pnl, 1),
        "profit_factor": round(pf, 2),
        "avg_pnl_per_trade": round(total_pnl / n_trades, 2),
        "terminal_pnl_median": round(terminal_pnls[nt // 2], 1),
        "terminal_pnl_5th": round(terminal_pnls[int(nt * 0.05)], 1),
        "terminal_pnl_95th": round(terminal_pnls[int(nt * 0.95)], 1),
        "max_dd_median": round(max_dds[nt // 2], 1),
        "max_dd_95th": round(max_dds[int(nt * 0.95)], 1),
        "max_dd_99th": round(max_dds[int(nt * 0.99)], 1),
        "max_dd_worst": round(max_dds[-1], 1),
    }

# ─── Count combos ───
print(f"\n=== COMBINATORICS ({n} assets) ===")
total = 0
for k in range(2, min(n + 1, 6)):
    c = math.comb(n, k)
    total += c
    print(f"  {k}-asset: C({n},{k}) = {c:,}")
print(f"  Total (2-5 asset): {total:,}")
print(f"  6+ asset: greedy expansion only")

# ─── Exhaustive for sizes 2-4 ───
all_results = {}

for size in range(2, 5):
    combos = list(combinations(ASSETS, size))
    print(f"\n--- {size}-asset combos ({len(combos)}) ---")
    results = []
    for i, combo in enumerate(combos):
        mc = run_portfolio_mc(combo)
        if mc:
            results.append(mc)
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(combos)}")
    results.sort(key=lambda x: x["profit_factor"], reverse=True)
    all_results[f"{size}_asset"] = results
    if results:
        top = results[0]
        print(f"  Best: {top['assets']} | PF={top['profit_factor']} | WR={top['win_rate']}% | MaxDD95={top['max_dd_95th']}p")

# ─── Size 5 exhaustive ───
combos5 = list(combinations(ASSETS, 5))
print(f"\n--- 5-asset combos ({len(combos5)}) ---")
results5 = []
for i, combo in enumerate(combos5):
    mc = run_portfolio_mc(combo)
    if mc:
        results5.append(mc)
    if (i + 1) % 100 == 0:
        print(f"  Progress: {i+1}/{len(combos5)}")
results5.sort(key=lambda x: x["profit_factor"], reverse=True)
all_results["5_asset"] = results5
if results5:
    top = results5[0]
    print(f"  Best: {top['assets']} | PF={top['profit_factor']} | WR={top['win_rate']}% | MaxDD95={top['max_dd_95th']}p")

# ─── Greedy expansion for sizes 6-{n} ───
print(f"\n--- Greedy expansion (6 to {n} assets) ---")

# Start from best 5, try each remaining asset
best_prev = results5[0] if results5 else None
for size in range(6, n + 1):
    if best_prev is None:
        break
    current_assets = list(best_prev["assets"])
    remaining = [a for a in ASSETS if a not in current_assets]
    if not remaining:
        break
    best_next = None
    for r in remaining:
        combo = tuple(sorted(current_assets + [r]))
        mc = run_portfolio_mc(combo)
        if mc and (best_next is None or mc["profit_factor"] > best_next["profit_factor"]):
            best_next = mc
    if best_next:
        all_results[f"{size}_asset_greedy"] = best_next
        new_assets = [a for a in best_next['assets'] if a not in current_assets]
        added = new_assets[0] if new_assets else '?'
        print(f"  {size}-asset: PF={best_next['profit_factor']} WR={best_next['win_rate']}% MaxDD95={best_next['max_dd_95th']}p | +{added}")
        best_prev = best_next

# ─── All assets ───
print(f"\n--- Full {n}-asset portfolio ---")
mc_all = run_portfolio_mc(ASSETS)
all_results["all_assets"] = mc_all
print(f"  PF={mc_all['profit_factor']} WR={mc_all['win_rate']}% MaxDD95={mc_all['max_dd_95th']}p")

# ─── Save raw ───
print("\nSaving raw results...")
json.dump(all_results, open(OUT_DIR / "matrix_raw.json", "w"), indent=2, default=str)

# ─── Generate Markdown ───
print("Generating markdown...")
md = []
md.append("# PORTFOLIO CONFIG MATRIX — CEREBUS LAB BIBLE\n")
md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M EDT')}")
md.append(f"Assets with trade data: {n} | Simulations: {N_SIMS}")
md.append(f"\n⚠️ EURUSD + USDCHF flagged (WR discrepancy under Arch investigation)")
md.append("\n---\n")

# Per-asset table
md.append("## PER-ASSET SUMMARY\n")
md.append("| # | Asset | Trades | WR | PnL (pips) | PF | Avg/trade |")
md.append("|---|-------|--------|-----|------------|-----|-----------|")
for i, sym in enumerate(sorted(ASSETS, key=lambda s: ASSET_STATS[s]["pf"], reverse=True), 1):
    s = ASSET_STATS[sym]
    flag = " ⚠️" if s["pf"] < 2 else ""
    md.append(f"| {i} | {sym}{flag} | {s['trades']} | {s['wr']}% | {s['pnl']:+,.1f} | {s['pf']} | {s['avg_pnl']:+.2f} |")

# Combo tables
for size in range(2, 6):
    key = f"{size}_asset"
    if key not in all_results:
        continue
    results = all_results[key]
    md.append(f"\n## {size}-ASSET PORTFOLIOS ({len(results)} combos)\n")
    md.append("### Top 15 by Profit Factor\n")
    md.append("| Rank | Assets | Trades | WR | PnL | PF | MaxDD 95th | Avg/trade |")
    md.append("|------|--------|--------|-----|------|-----|------------|-----------|")
    for i, r in enumerate(results[:15], 1):
        md.append(f"| {i} | {', '.join(r['assets'])} | {r['total_trades']} | {r['win_rate']}% | {r['total_pnl']:+,.1f} | {r['profit_factor']} | {r['max_dd_95th']}p | {r['avg_pnl_per_trade']:+.2f} |")

# Greedy expansion
md.append(f"\n## GREEDY EXPANSION (6 to {n} assets)\n")
md.append("| Size | New Asset Added | WR | PF | MaxDD 95th | MaxDD 99th | Total PnL |")
md.append("|------|-----------------|-----|-----|------------|------------|-----------|")
for key in sorted(all_results.keys()):
    if "_greedy" in key or key == "all_assets":
        r = all_results[key]
        size = r["n_assets"]
        md.append(f"| {size} | [{', '.join(r['assets'][:4])}...] | {r['win_rate']}% | {r['profit_factor']} | {r['max_dd_95th']}p | {r['max_dd_99th']}p | {r['total_pnl']:+,.1f}p |")

md.append(f"\n---\n")
md.append(f"*Matrix generated with {N_SIMS} MC simulations per portfolio combo*")

md_path = OUT_DIR / "PORTFOLIO_MATRIX.md"
md_path.write_text("\n".join(md), encoding="utf-8")
print(f"\nSaved: {md_path}")
print("=" * 60)
print("DONE.")
