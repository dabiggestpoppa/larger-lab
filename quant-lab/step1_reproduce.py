"""
Step 1: Reproduce EURUSD floor baseline.
Floor config: t1_trigger=12.0 (from deployment_configs.json)
Target: 5,593 trades, 82.9% WR (from trigger_sweep_max_accuracy.json entry [0])
"""
import sys, json, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from engines.symmetry_trap_backtest import SymmetryTrapBacktest, format_report

# EURUSD floor config: trigger=12.0
tier_config = {
    "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 12.0},
    "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
    "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 12.0},
}

CSV_PATH = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
ENGINES_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines'
REPORTS_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

print("=== Step 1: EURUSD Floor Baseline Reproduction ===")
print(f"Config: trigger=12.0, CSV={CSV_PATH}")
print()

start = time.time()
bt = SymmetryTrapBacktest(pip_size=0.0001, tier_config=tier_config, symbol="EURUSD")
result = bt.run_from_csv(CSV_PATH)
elapsed = time.time() - start

print(format_report(result))
print(f"\nElapsed: {elapsed:.1f}s")

# Save raw result for step 2
output = {
    "step": 1,
    "symbol": "EURUSD",
    "config": tier_config,
    "total_trades": result.total_trades,
    "wins": result.wins,
    "losses": result.losses,
    "win_rate": result.win_rate,
    "total_pnl_pips": result.total_pnl_pips,
    "profit_factor": result.profit_factor,
    "avg_win_pips": result.avg_win_pips,
    "avg_loss_pips": result.avg_loss_pips,
    "expectancy_pips": result.expectancy_pips,
    "sharpe_ratio": result.sharpe_ratio,
    "max_drawdown_pips": result.max_drawdown_pips,
    "max_consec_wins": result.max_consec_wins,
    "max_consec_losses": result.max_consec_losses,
    "tier_stats": result.tier_stats,
    "loop_stats": result.loop_stats,
    "data_bars": result.data_bars,
    "data_days": result.data_days,
    "elapsed_seconds": elapsed,
    "raw_trades": [
        {
            "entry_time": t.entry_time.isoformat(),
            "exit_time": t.exit_time.isoformat(),
            "direction": t.direction,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "pnl_pips": t.pnl_pips,
            "result": t.result,
            "tier": t.tier,
            "loop_count": t.loop_count,
        }
        for t in result.trades
    ],
}

out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\step1_eurusd_baseline.json'
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nRaw trades saved to {out_path}")
print(f"Trade count: {result.total_trades}")
