"""Collect per-asset MC stats for portfolio matrix."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))
from asset_configs import ASSET_CONFIGS

mc_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset")
assets = []
for s in sorted(ASSET_CONFIGS.keys()):
    mc_file = mc_dir / (s + "_mc_results.json")
    if mc_file.exists():
        assets.append(s)

stats = {}
for sym in assets:
    mc_file = mc_dir / (sym + "_mc_results.json")
    d = json.load(open(mc_file))
    bt = d.get("backtest", {})
    pnls = d.get("per_trade_pnl", [])
    if pnls:
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / len(pnls) * 100
        gross_win = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        pf = gross_win / gross_loss if gross_loss > 0 else 999
        stats[sym] = {
            "trades": len(pnls),
            "wr": round(wr, 1),
            "pnl": round(sum(pnls), 1),
            "pf": round(pf, 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2),
        }

# Save for other scripts
out = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest\portfolio_matrix")
out.mkdir(exist_ok=True)
json.dump({"assets": assets, "stats": stats}, open(out / "asset_stats.json", "w"), indent=2)

# Print sorted by PF
print(f"{'ASSET':10s} {'TR':>4s} {'WR':>6s} {'PNL':>9s} {'PF':>6s} {'AVG':>8s}")
print("-" * 50)
for sym in sorted(stats.keys(), key=lambda s: stats[s]["pf"], reverse=True):
    s = stats[sym]
    print(f"{sym:10s} {s['trades']:4d} {s['wr']:5.1f}% {s['pnl']:+9.1f} {s['pf']:6.2f} {s['avg_pnl']:+8.2f}")
print(f"\nTotal: {len(assets)} assets")
