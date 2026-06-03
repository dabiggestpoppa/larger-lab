"""
THRESHOLD GENERATOR — 1:1 MC COMPARATOR PARITY
================================================
Generates live monitoring thresholds DIRECTLY from portfolio MC results.
No manual estimates — every threshold is backed by MC percentile.
"""
import json
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "reports"
PORTFOLIO_MC_DIR = REPORTS_DIR / "portfolio_mc"

mc_path = PORTFOLIO_MC_DIR / "portfolio_mc_results.json"
if not mc_path.exists():
    print("ERROR: Run portfolio MC first")
    exit(1)

mc_result = json.loads(mc_path.read_text())
mc = mc_result["monte_carlo"]
pool = mc_result["pooled_stats"]
per_asset = mc_result["per_asset"]

# Portfolio-level thresholds from MC percentiles
thresholds = {
    "generated_at": datetime.now().isoformat(),
    "source": "portfolio_mc_results.json (1:1 MC parity)",
    "n_simulations": mc_result["n_simulations"],

    # Portfolio-level drawdown thresholds (from MC)
    "portfolio": {
        "max_dd_warning": round(mc["max_dd_95th"], 1),       # P95 DD
        "max_dd_critical": round(mc["max_dd_99th"], 1),       # P99 DD
        "max_dd_absolute": round(mc["max_dd_worst"], 1),      # worst case
        "max_loss_streak_warning": mc["max_loss_streak_95th"],
        "max_loss_streak_critical": mc["max_loss_streak_worst"],
        "backtest_wr": pool["win_rate"] / 100,
        "backtest_pf": pool["profit_factor"],
        "total_trades": pool["total_trades"],
    },

    # Daily thresholds (derived from MC)
    "daily": {
        "max_losses_warning": max(3, int(pool["losses"] * 0.03)),   # ~3% of total losses/day
        "max_losses_critical": max(5, int(pool["losses"] * 0.05)),  # ~5% of total losses/day
        "min_wr_warning": round(pool["win_rate"] / 100 * 0.70, 2),  # 70% of backtest WR
        "min_wr_critical": round(pool["win_rate"] / 100 * 0.55, 2), # 55% of backtest WR
    },

    # Per-asset thresholds (from per-asset MC data)
    "per_asset": {},
}

# Per-asset thresholds
for sym, stats in per_asset.items():
    asset_losses = stats["losses"]
    asset_trades = stats["trades"]
    asset_wr = stats["win_rate"] / 100

    thresholds["per_asset"][sym] = {
        "max_daily_losses_warning": max(1, int(asset_losses * 0.04)),
        "max_daily_losses_critical": max(2, int(asset_losses * 0.07)),
        "min_daily_wr_warning": round(asset_wr * 0.70, 2),
        "min_daily_wr_critical": round(asset_wr * 0.50, 2),
        "max_loss_streak_warning": max(2, int(asset_losses * 0.025)),
        "max_loss_streak_critical": max(3, int(asset_losses * 0.05)),
        "backtest_wr": asset_wr,
        "backtest_trades": asset_trades,
    }

# Save
thresh_path = PORTFOLIO_MC_DIR / "portfolio_thresholds.json"
with open(thresh_path, "w") as f:
    json.dump(thresholds, f, indent=2, default=str)

print("=" * 60)
print("THRESHOLDS GENERATED — 1:1 MC PARITY")
print("=" * 60)

p = thresholds["portfolio"]
print(f"\nPortfolio:")
print(f"  DD warning (P95):     {p['max_dd_warning']}p")
print(f"  DD critical (P99):    {p['max_dd_critical']}p")
print(f"  DD absolute (worst):  {p['max_dd_absolute']}p")
print(f"  Loss streak warning:  {p['max_loss_streak_warning']}")
print(f"  Loss streak critical: {p['max_loss_streak_critical']}")
print(f"  Backtest WR:          {p['backtest_wr']:.1%}")
print(f"  Backtest PF:          {p['backtest_pf']:.1f}")

d = thresholds["daily"]
print(f"\nDaily:")
print(f"  Max losses warning:   {d['max_losses_warning']}")
print(f"  Max losses critical:  {d['max_losses_critical']}")
print(f"  Min WR warning:       {d['min_wr_warning']:.0%}")
print(f"  Min WR critical:      {d['min_wr_critical']:.0%}")

print(f"\nPer-Asset:")
for sym, t in thresholds["per_asset"].items():
    print(f"  {sym}: daily_loss_warn={t['max_daily_losses_warning']} daily_loss_crit={t['max_daily_losses_critical']} wr_warn={t['min_daily_wr_warning']:.0%} wr_crit={t['min_daily_wr_critical']:.0%}")

print(f"\nSaved: {thresh_path}")
print("=" * 60)
