"""Portfolio MC — 5 assets only (excluding EURUSD + USDCHF pending WR fix)."""
import json
import random
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "reports"
PORTFOLIO_MC_DIR = REPORTS_DIR / "portfolio_mc"
PORTFOLIO_MC_DIR.mkdir(parents=True, exist_ok=True)

LIVE_ASSETS = ["GBPJPY", "CHFJPY", "GBPAUD", "GBPNZD", "NZDUSD"]
N_SIMULATIONS = 10000
random.seed(42)

print("=" * 60)
print("PORTFOLIO MC — 5 ASSETS (EURUSD+USDCHF EXCLUDED)")
print("=" * 60)

all_trades = {}
for sym in LIVE_ASSETS:
    mc_path = REPORTS_DIR / "per-asset" / f"{sym}_mc_results.json"
    if not mc_path.exists():
        print(f"  SKIP {sym}: no MC results")
        continue
    data = json.loads(mc_path.read_text())
    pnls = data.get("per_trade_pnl", [])
    if not pnls:
        print(f"  SKIP {sym}: empty per_trade_pnl")
        continue
    all_trades[sym] = pnls
    wins = sum(1 for p in pnls if p > 0)
    wr = wins / len(pnls) * 100
    print(f"  {sym}: {len(pnls)} trades | WR {wr:.1f}% | sum={sum(pnls):.1f}p")

print(f"\nLoaded {len(all_trades)}/{len(LIVE_ASSETS)} assets")

pooled = []
for sym, trades in all_trades.items():
    pooled.extend(trades)

n_trades = len(pooled)
wins = [p for p in pooled if p > 0]
losses = [p for p in pooled if p < 0]
total_wr = len(wins) / n_trades * 100
total_pnl = sum(pooled)
gross_profit = sum(wins)
gross_loss = abs(sum(losses)) if losses else 0.01
pf = gross_profit / gross_loss

print(f"\nPooled: {n_trades} trades | WR {total_wr:.1f}% | P&L {total_pnl:.1f}p | PF {pf:.2f}")
print(f"Running {N_SIMULATIONS} simulations...")

terminal_pnls = []
max_dds = []
max_streaks = []

for i in range(N_SIMULATIONS):
    shuffled = random.sample(pooled, n_trades)
    terminal_pnls.append(sum(shuffled))

    cumulative = 0; peak = 0; max_dd = 0
    for p in shuffled:
        cumulative += p
        if cumulative > peak: peak = cumulative
        dd = peak - cumulative
        if dd > max_dd: max_dd = dd
    max_dds.append(max_dd)

    max_streak = current = 0
    for p in shuffled:
        if p <= 0: current += 1
        else: current = 0
        if current > max_streak: max_streak = current
    max_streaks.append(max_streak)

terminal_pnls.sort(); max_dds.sort(); max_streaks.sort()
n = len(terminal_pnls)

mc = {
    "terminal_pnl_median": round(terminal_pnls[n // 2], 1),
    "terminal_pnl_mean": round(sum(terminal_pnls) / n, 1),
    "terminal_pnl_5th": round(terminal_pnls[int(n * 0.05)], 1),
    "terminal_pnl_25th": round(terminal_pnls[int(n * 0.25)], 1),
    "terminal_pnl_75th": round(terminal_pnls[int(n * 0.75)], 1),
    "terminal_pnl_95th": round(terminal_pnls[int(n * 0.95)], 1),
    "max_dd_median": round(max_dds[n // 2], 1),
    "max_dd_95th": round(max_dds[int(n * 0.95)], 1),
    "max_dd_99th": round(max_dds[int(n * 0.99)], 1),
    "max_dd_worst": round(max_dds[-1], 1),
    "max_loss_streak_median": max_streaks[n // 2],
    "max_loss_streak_95th": max_streaks[int(n * 0.95)],
    "max_loss_streak_99th": max_streaks[int(n * 0.99)],
    "max_loss_streak_worst": max_streaks[-1],
}

print(f"\n{'='*60}")
print(f"PORTFOLIO MC RESULTS ({N_SIMULATIONS} sims, 5 assets)")
print(f"{'='*60}")
print(f"  Terminal PnL median:  {mc['terminal_pnl_median']}p")
print(f"  Terminal PnL mean:    {mc['terminal_pnl_mean']}p")
print(f"  Terminal PnL 5th:     {mc['terminal_pnl_5th']}p")
print(f"  Terminal PnL 95th:    {mc['terminal_pnl_95th']}p")
print(f"  Max DD median:        {mc['max_dd_median']}p")
print(f"  Max DD 95th:          {mc['max_dd_95th']}p")
print(f"  Max DD 99th:          {mc['max_dd_99th']}p")
print(f"  Max DD worst:         {mc['max_dd_worst']}p")
print(f"  Loss streak median:   {mc['max_loss_streak_median']}")
print(f"  Loss streak 95th:     {mc['max_loss_streak_95th']}")
print(f"  Loss streak worst:    {mc['max_loss_streak_worst']}")

per_asset = {}
for sym in all_trades:
    trades = all_trades[sym]
    aw = sum(1 for t in trades if t > 0)
    per_asset[sym] = {
        "trades": len(trades),
        "wins": aw,
        "losses": len(trades) - aw,
        "win_rate": round(aw / len(trades) * 100, 1),
        "total_pnl": round(sum(trades), 1),
    }

result = {
    "portfolio": list(all_trades.keys()),
    "excluded": ["EURUSD", "USDCHF"],
    "timestamp": datetime.now().isoformat(),
    "n_simulations": N_SIMULATIONS,
    "pooled_stats": {
        "total_trades": n_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(total_wr, 1),
        "total_pnl_pips": round(total_pnl, 1),
        "profit_factor": round(pf, 2),
    },
    "per_asset": per_asset,
    "monte_carlo": mc,
}

out_path = PORTFOLIO_MC_DIR / "portfolio_mc_5assets.json"
with open(out_path, "w") as f:
    json.dump(result, f, indent=2, default=str)

print(f"\nSaved: {out_path}")
print("=" * 60)
