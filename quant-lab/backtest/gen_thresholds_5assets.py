"""Generate monitoring thresholds from 5-asset portfolio MC."""
import json
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "reports"
PORTFOLIO_MC_DIR = REPORTS_DIR / "portfolio_mc"

mc = json.load(open(PORTFOLIO_MC_DIR / "portfolio_mc_5assets.json"))
pooled = mc["pooled_stats"]
monte_carlo = mc["monte_carlo"]

thresholds = {
    "generated": datetime.now().isoformat(),
    "portfolio": mc["portfolio"],
    "excluded": mc.get("excluded", []),
    "n_simulations": mc["n_simulations"],
    "pooled_backtest": {
        "total_trades": pooled["total_trades"],
        "win_rate": pooled["win_rate"],
        "profit_factor": pooled["profit_factor"],
        "total_pnl_pips": pooled["total_pnl_pips"],
    },
    "monitoring_thresholds": {
        "max_drawdown_warning_pips": round(monte_carlo["max_dd_95th"], 1),
        "max_drawdown_critical_pips": round(monte_carlo["max_dd_99th"], 1),
        "max_drawdown_hard_stop_pips": round(monte_carlo["max_dd_worst"], 1),
        "max_loss_streak_warning": monte_carlo["max_loss_streak_95th"],
        "max_loss_streak_critical": monte_carlo["max_loss_streak_worst"],
    },
    "mc_distribution": {
        "terminal_pnl_median": monte_carlo["terminal_pnl_median"],
        "terminal_pnl_mean": monte_carlo["terminal_pnl_mean"],
        "terminal_pnl_5th": monte_carlo["terminal_pnl_5th"],
        "terminal_pnl_95th": monte_carlo["terminal_pnl_95th"],
        "max_dd_median": monte_carlo["max_dd_median"],
        "max_dd_95th": monte_carlo["max_dd_95th"],
        "max_dd_99th": monte_carlo["max_dd_99th"],
        "max_dd_worst": monte_carlo["max_dd_worst"],
    },
    "per_asset": mc["per_asset"],
}

out_path = PORTFOLIO_MC_DIR / "portfolio_thresholds_5assets.json"
with open(out_path, "w") as f:
    json.dump(thresholds, f, indent=2, default=str)

print("=== PORTFOLIO THRESHOLDS (5 ASSETS) ===")
print(f"Assets: {mc['portfolio']}")
print(f"Excluded: {mc.get('excluded', [])}")
print(f"Pooled: {pooled['total_trades']} trades | WR {pooled['win_rate']}% | PF {pooled['profit_factor']}")
print()
print("Monitoring Thresholds:")
print(f"  DD Warning (95th):    {thresholds['monitoring_thresholds']['max_drawdown_warning_pips']}p")
print(f"  DD Critical (99th):   {thresholds['monitoring_thresholds']['max_drawdown_critical_pips']}p")
print(f"  DD Hard Stop (worst): {thresholds['monitoring_thresholds']['max_drawdown_hard_stop_pips']}p")
print(f"  Loss Streak Warning:  {thresholds['monitoring_thresholds']['max_loss_streak_warning']}")
print(f"  Loss Streak Critical: {thresholds['monitoring_thresholds']['max_loss_streak_critical']}")
print()
print("Per-Asset:")
for sym, s in mc["per_asset"].items():
    print(f"  {sym}: {s['trades']} tr | {s['win_rate']}% WR | {s['total_pnl']:+.1f}p")
print(f"\nSaved: {out_path}")
