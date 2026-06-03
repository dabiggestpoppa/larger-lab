"""
PORTFOLIO CONFIG MATRIX GENERATOR
==================================
For N assets (each can be: off, P90-only, ST-only, both), generate:
1. All 2-asset combos
2. All 3-asset combos
3. Top-K combos for sizes 4-7 (by best pooled PF from per-asset MC)
4. Full matrix document

Uses per-asset per_trade_pnl from MC results for fast portfolio MC.
"""
import sys, json, random, math
from pathlib import Path
from itertools import combinations, product
from datetime import datetime

# Setup paths
QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
sys.path.insert(0, str(QUANT_LAB / "configs"))
from asset_configs import ASSET_CONFIGS

OUT_DIR = QUANT_LAB / "backtest" / "portfolio_matrix"
OUT_DIR.mkdir(exist_ok=True)
MC_DIR = QUANT_LAB / "reports" / "per-asset"
N_SIMULATIONS = 5000
random.seed(42)

# ─── Load per-asset MC trade P&Ls ───
print("Loading per-asset MC data...")
ASSETS = []
ASSET_PNL = {}   # sym -> list of per-trade PnL
ASSET_STATS = {} # sym -> {trades, wr, pnl, pf, avg_pnl}

for sym in sorted(ASSET_CONFIGS.keys()):
    mc_file = MC_DIR / (sym + "_mc_results.json")
    if not mc_file.exists():
        continue
    d = json.load(open(mc_file))
    pnls = d.get("per_trade_pnl", [])
    if not pnls:
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

print(f"Loaded {len(ASSETS)} assets: {ASSETS}")

# ─── Portfolio MC function ───
def run_portfolio_mc(asset_list, engines_per_asset=None):
    """Run portfolio MC for a list of assets. Returns MC stats dict."""
    pooled = []
    for sym in asset_list:
        if sym in ASSET_PNL:
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
    
    # MC simulations
    terminal_pnls = []
    max_dds = []
    for _ in range(N_SIMULATIONS):
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
    n = len(terminal_pnls)
    
    return {
        "n_assets": len(asset_list),
        "assets": list(asset_list),
        "total_trades": n_trades,
        "win_rate": round(total_wr, 1),
        "total_pnl": round(total_pnl, 1),
        "profit_factor": round(pf, 2),
        "avg_pnl_per_trade": round(total_pnl / n_trades, 2),
        "terminal_pnl_median": round(terminal_pnls[n // 2], 1),
        "terminal_pnl_5th": round(terminal_pnls[int(n * 0.05)], 1),
        "terminal_pnl_95th": round(terminal_pnls[int(n * 0.95)], 1),
        "max_dd_median": round(max_dds[n // 2], 1),
        "max_dd_95th": round(max_dds[int(n * 0.95)], 1),
        "max_dd_99th": round(max_dds[int(n * 0.99)], 1),
        "max_dd_worst": round(max_dds[-1], 1),
    }

# ─── ENU: Count total combos ───
print("\n=== COMBINATORICS ===")
n = len(ASSETS)
total_combos = 0
for k in range(2, n + 1):
    c = math.comb(n, k)
    total_combos += c
    print(f"  {k}-asset combos: C({n},{k}) = {c:,}")
print(f"  TOTAL combos (2 to {n} assets): {total_combos:,}")

# ─── Generate all combos for sizes 2-3, top-K for sizes 4+ ───
print("\n=== RUNNING PORTFOLIO MC FOR ALL COMBOS ===")

all_results = {}

# Size 2: all combos
print(f"\n--- 2-asset combos ({math.comb(n, 2)} combos) ---")
results_2 = []
for combo in combinations(ASSETS, 2):
    mc = run_portfolio_mc(combo)
    if mc:
        results_2.append(mc)
results_2.sort(key=lambda x: x["profit_factor"], reverse=True)
all_results["2_asset"] = results_2
print(f"  Done. Top: {results_2[0]['assets']} PF={results_2[0]['profit_factor']}")

# Size 3: all combos
print(f"\n--- 3-asset combos ({math.comb(n, 3)} combos) ---")
results_3 = []
for combo in combinations(ASSETS, 3):
    mc = run_portfolio_mc(combo)
    if mc:
        results_3.append(mc)
results_3.sort(key=lambda x: x["profit_factor"], reverse=True)
all_results["3_asset"] = results_3
print(f"  Done. Top: {results_3[0]['assets']} PF={results_3[0]['profit_factor']}")

# Size 4: all combos (might be slow — 3876 combos)
print(f"\n--- 4-asset combos ({math.comb(n, 4)} combos) ---")
results_4 = []
for combo in combinations(ASSETS, 4):
    mc = run_portfolio_mc(combo)
    if mc:
        results_4.append(mc)
results_4.sort(key=lambda x: x["profit_factor"], reverse=True)
all_results["4_asset"] = results_4
print(f"  Done. Top: {results_4[0]['assets']} PF={results_4[0]['profit_factor']}")

# Size 5-7: Too many combos for exhaustive. Use greedy + top-seeded approach
# Seed with best 4-asset combo, add best remaining asset
print(f"\n--- 5-asset combos (greedy from best 4) ---")
best_4 = results_4[0]["assets"]
remaining = [a for a in ASSETS if a not in best_4]
best_5 = None
for r in remaining:
    combo = tuple(sorted(best_4 + [r]))
    mc = run_portfolio_mc(combo)
    if mc and (best_5 is None or mc["profit_factor"] > best_5["profit_factor"]):
        best_5 = mc
if best_5:
    all_results["5_asset_greedy"] = best_5
    print(f"  Best 5: {best_5['assets']} PF={best_5['profit_factor']}")

# Size 6-12: Greedy expansion
print(f"\n--- 6 to 12-asset greedy expansion ---")
prev_best = best_5
for size in range(6, 13):
    if prev_best is None:
        break
    current_assets = prev_best["assets"]
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
        print(f"  Best {size}: PF={best_next['profit_factor']} WR={best_next['win_rate']}% MaxDD95={best_next['max_dd_95th']}p Assets={len(best_next['assets'])}")
        prev_best = best_next

# All 19 assets
print(f"\n--- Full 19-asset portfolio ---")
mc_all = run_portfolio_mc(ASSETS)
all_results["19_asset_all"] = mc_all
print(f"  PF={mc_all['profit_factor']} WR={mc_all['win_rate']}% MaxDD95={mc_all['max_dd_95th']}p")

# ─── Save raw results ───
print("\nSaving results...")
json.dump(all_results, open(OUT_DIR / "matrix_raw.json", "w"), indent=2, default=str)

# ─── Generate Markdown report ───
print("Generating markdown report...")
lines = []
lines.append("# PORTFOLIO CONFIG MATRIX — CEREBUS LAB BIBLE")
lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M EDT')}")
lines.append(f"Assets: {len(ASSETS)} | Simulations per combo: {N_SIMULATIONS}")
lines.append(f"\n⚠️ EURUSD and USDCHF included but flagged — WR discrepancy under investigation by Arch")
lines.append("\n---\n")

# Per-asset summary table
lines.append("## PER-ASSET SUMMARY\n")
lines.append("| Asset | Trades | WR | PnL (pips) | PF | Avg PnL/trade |")
lines.append("|-------|--------|-----|------------|-----|---------------|")
for sym in sorted(ASSETS, key=lambda s: ASSET_STATS[s]["pf"], reverse=True):
    s = ASSET_STATS[sym]
    flag = " ⚠️" if s["pf"] < 2 else ""
    lines.append(f"| {sym}{flag} | {s['trades']} | {s['wr']}% | {s['pnl']:+,.1f} | {s['pf']} | {s['avg_pnl']:+.2f} |")

# 2-asset combos
lines.append(f"\n## 2-ASSET PORTFOLIOS ({len(results_2)} combos)\n")
lines.append("### Top 20 by Profit Factor\n")
lines.append("| Rank | Assets | Trades | WR | PnL | PF | MaxDD 95th |")
lines.append("|------|--------|--------|-----|------|-----|------------|")
for i, r in enumerate(results_2[:20], 1):
    lines.append(f"| {i} | {', '.join(r['assets'])} | {r['total_trades']} | {r['win_rate']}% | {r['total_pnl']:+,.1f} | {r['profit_factor']} | {r['max_dd_95th']}p |")

lines.append(f"\n### Bottom 10 by Profit Factor\n")
lines.append("| Rank | Assets | Trades | WR | PnL | PF | MaxDD 95th |")
lines.append("|------|--------|--------|-----|------|-----|------------|")
for i, r in enumerate(results_2[-10:], len(results_2) - 9):
    lines.append(f"| {i} | {', '.join(r['assets'])} | {r['total_trades']} | {r['win_rate']}% | {r['total_pnl']:+,.1f} | {r['profit_factor']} | {r['max_dd_95th']}p |")

# 3-asset combos
lines.append(f"\n## 3-ASSET PORTFOLIOS ({len(results_3)} combos)\n")
lines.append("### Top 20 by Profit Factor\n")
lines.append("| Rank | Assets | Trades | WR | PnL | PF | MaxDD 95th |")
lines.append("|------|--------|--------|-----|------|-----|------------|")
for i, r in enumerate(results_3[:20], 1):
    lines.append(f"| {i} | {', '.join(r['assets'])} | {r['total_trades']} | {r['win_rate']}% | {r['total_pnl']:+,.1f} | {r['profit_factor']} | {r['max_dd_95th']}p |")

# 4-asset combos
lines.append(f"\n## 4-ASSET PORTFOLIOS ({len(results_4)} combos)\n")
lines.append("### Top 20 by Profit Factor\n")
lines.append("| Rank | Assets | Trades | WR | PnL | PF | MaxDD 95th |")
lines.append("|------|--------|--------|-----|------|-----|------------|")
for i, r in enumerate(results_4[:20], 1):
    lines.append(f"| {i} | {', '.join(r['assets'])} | {r['total_trades']} | {r['win_rate']}% | {r['total_pnl']:+,.1f} | {r['profit_factor']} | {r['max_dd_95th']}p |")

# Greedy expansion
lines.append(f"\n## GREEDY EXPANSION (5-12 assets)\n")
lines.append("| Size | Assets | WR | PF | MaxDD 95th | MaxDD 99th |")
lines.append("|------|--------|-----|-----|------------|------------|")
for key in sorted(all_results.keys()):
    if "_greedy" in key or key == "19_asset_all":
        r = all_results[key]
        size = r['n_assets']
        assets_str = ', '.join(r['assets'][:5]) + ('...' if len(r['assets']) > 5 else '')
        lines.append(f"| {size} | {assets_str} | {r['win_rate']}% | {r['profit_factor']} | {r['max_dd_95th']}p | {r['max_dd_99th']}p |")

# Full 19-asset
lines.append(f"\n## FULL 19-ASSET PORTFOLIO\n")
r = all_results["19_asset_all"]
lines.append(f"- **Assets**: {', '.join(r['assets'])}")
lines.append(f"- **Trades**: {r['total_trades']}")
lines.append(f"- **WR**: {r['win_rate']}%")
lines.append(f"- **PF**: {r['profit_factor']}")
lines.append(f"- **Total PnL**: {r['total_pnl']:+.1f}p")
lines.append(f"- **MaxDD 95th**: {r['max_dd_95th']}p")
lines.append(f"- **MaxDD 99th**: {r['max_dd_99th']}p")
lines.append(f"- **MaxDD worst**: {r['max_dd_worst']}p")

# Save markdown
md_path = OUT_DIR / "PORTFOLIO_MATRIX.md"
md_path.write_text("\n".join(lines), encoding="utf-8")
print(f"\nSaved: {md_path}")
print("=" * 60)
print("DONE. Full portfolio config matrix complete.")
