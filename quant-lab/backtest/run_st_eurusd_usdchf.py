"""
ST BACKTEST + MC for EURUSD and USDCHF — Exact Live Configs
Outputs per_trade_pnl in same format as existing P90 per-asset results.
"""
import json
import random
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))

from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv, compute_stats
from symmetry_trap import TradeRecord

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "per-asset"

EXACT_CONFIGS = {
    "EURUSD": {
        "csv": "EURUSD_M5.csv",
        "pip_value": 0.0001,
        "tiers": {
            "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
            "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
        },
    },
    "USDCHF": {
        "csv": "USDCHF_M5.csv",
        "pip_value": 0.0001,
        "tiers": {
            "T1": {"ar_max": 19.0, "au": 11.0, "trigger": 11.0},
            "T2": {"ar_max": 29.0, "au": 15.0, "trigger": 15.0},
            "T3": {"ar_max": 50.0, "au": 20.0, "trigger": 20.0},
        },
    },
}

N_SIMULATIONS = 10000
random.seed(42)


def run_mc_on_pnls(pnls, n_sims=N_SIMULATIONS):
    n_trades = len(pnls)
    terminal_pnls, max_dds, max_streaks = [], [], []

    for _ in range(n_sims):
        shuffled = random.sample(pnls, n_trades)
        terminal_pnls.append(sum(shuffled))

        cumulative = 0; peak = 0; max_dd = 0
        for p in shuffled:
            cumulative += p
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
        max_dds.append(max_dd)

        max_streak = current = 0
        for p in shuffled:
            if p <= 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        max_streaks.append(max_streak)

    terminal_pnls.sort()
    max_dds.sort()
    max_streaks.sort()
    n = len(terminal_pnls)

    return {
        "n_simulations": n_sims,
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


def main():
    print("=" * 60)
    print("ST BACKTEST + MC — EURUSD, USDCHF (EXACT LIVE CONFIGS)")
    print("=" * 60)

    for symbol, cfg in EXACT_CONFIGS.items():
        csv_path = DATA_DIR / cfg["csv"]
        print(f"\n{symbol}: {csv_path.name}")

        config = {"name": symbol, "pip_value": cfg["pip_value"], "tiers": cfg["tiers"]}
        bt = SymmetryTrapBacktest(config=config)
        result = bt.run_from_csv(str(csv_path))

        print(f"  Data: {result.data_bars:,} bars | {result.data_days} days")
        print(f"  Trades: {result.total_trades} | W: {result.wins} L: {result.losses} | WR: {result.win_rate:.1f}%")
        print(f"  PnL: {result.total_pnl_pips:+.1f}p | PF: {result.profit_factor:.2f}")
        print(f"  MaxDD: {result.max_drawdown_pips:.1f}p")

        if result.loop_stats:
            print(f"  Loop dist:", end="")
            for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
                ls = result.loop_stats[lk]
                print(f" L{lk}={ls['trades']}({ls['wr']:.0f}%)", end="")
            print()

        if result.total_trades == 0:
            print(f"  SKIP: 0 trades")
            continue

        # Extract per-trade PnL
        pnls = [t.pnl_pips for t in result.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        gp = sum(wins) if wins else 0
        gl = abs(sum(losses)) if losses else 0.01

        print(f"  Sharpe: {result.sharpe_ratio:.2f} | AvgWin: {result.avg_win_pips:.1f}p | AvgLoss: {result.avg_loss_pips:.1f}p")

        # MC
        print(f"  Running {N_SIMULATIONS} MC sims...")
        mc = run_mc_on_pnls(pnls)

        # Build output in same format as existing P90 results
        output = {
            "asset": symbol,
            "timestamp": datetime.now().isoformat(),
            "backtest": {
                "trades": result.total_trades,
                "wins": result.wins,
                "losses": result.losses,
                "win_rate": round(result.win_rate / 100, 4),
                "total_pnl_pips": round(result.total_pnl_pips, 1),
                "profit_factor": round(result.profit_factor, 2),
                "sharpe": round(result.sharpe_ratio, 2),
                "max_dd_pips": round(result.max_drawdown_pips, 1),
                "max_dd_pct": round(result.max_drawdown_pct, 4),
                "expectancy": round(result.expectancy_pips, 2),
                "tier_stats": result.tier_stats,
                "hourly_stats": result.hourly_stats,
                "loop_stats": result.loop_stats,
                "long": {"trades": result.long_trades, "wr": result.long_wr, "pnl": round(result.long_pnl, 1)},
                "short": {"trades": result.short_trades, "wr": result.short_wr, "pnl": round(result.short_pnl, 1)},
            },
            "monte_carlo": mc,
            "per_trade_pnl": [round(p, 1) for p in pnls],
        }

        out_path = REPORTS_DIR / f"{symbol}_mc_results.json"
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"  Saved: {out_path}")
        print(f"  MC: PnL median={mc['terminal_pnl_median']}p | MaxDD 95th={mc['max_dd_95th']}p | MaxDD worst={mc['max_dd_worst']}p")

    print(f"\nDone.")
    print("=" * 60)


if __name__ == "__main__":
    main()
