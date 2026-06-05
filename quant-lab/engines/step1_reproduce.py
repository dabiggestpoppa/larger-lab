"""
Step 1: Reproduce EURUSD floor baseline.
Using the EXACT native config from trigger_sweep_max_accuracy_all.py
AR expanded 3.0x, 4PM cutoff (hardcoded in engine).
"""
import sys, json, time

from symmetry_trap_backtest import SymmetryTrapBacktest

# EURUSD native config from sweep script (floor = native trigger, AR expanded 3x)
# Native: T1 ar_max=20.0 au=10.0 trigger=12.0 | T2 ar_max=30.0 au=12.0 trigger=15.0 | T3 ar_max=45.0 au=15.0 trigger=19.0
# AR expanded 3.0x: T1=60.0 T2=90.0 T3=135.0
tier_config = {
    "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 90.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 135.0, "au": 15.0, "trigger": 19.0},
}

CSV_PATH = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
OUT_PATH = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\step1_eurusd_baseline.json'

print("=== Step 1: EURUSD Floor Baseline Reproduction ===")
print(f"Config: {json.dumps(tier_config, indent=2)}")
print()

start = time.time()
bt = SymmetryTrapBacktest(pip_size=0.0001, tier_config=tier_config, symbol="EURUSD")
result = bt.run_from_csv(CSV_PATH)
elapsed = time.time() - start

print(f"Data: {result.data_bars:,} bars | {result.data_days} days")
print(f"Trades: {result.total_trades} | W: {result.wins} L: {result.losses} | WR: {result.win_rate:.1f}%")
print(f"PnL: {result.total_pnl_pips:+.1f} pips | PF: {result.profit_factor:.2f}")
print(f"Avg Win: {result.avg_win_pips:.1f}p | Avg Loss: {result.avg_loss_pips:.1f}p | Expectancy: {result.expectancy_pips:.1f}p")
print(f"MaxDD: {result.max_drawdown_pips:.1f}p | MaxCW: {result.max_consec_wins} | MaxCL: {result.max_consec_losses}")
if result.tier_stats:
    for tn, ts in result.tier_stats.items():
        print(f"  {tn}: {ts['trades']} tr, {ts['wr']:.1f}% WR, {ts['pnl']:+.1f}p")
if result.loop_stats:
    for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        ls = result.loop_stats[lk]
        print(f"  Loop {lk}: {ls['trades']} tr, {ls['wr']:.1f}% WR, {ls['pnl']:+.1f}p")
print(f"\nElapsed: {elapsed:.1f}s")

# Target from sweep JSON: trigger=12.0 -> 5593 trades, 82.9% WR, 4.17 tr/d
print(f"\n=== COMPARISON ===")
print(f"  Got:      {result.total_trades} trades, {result.win_rate:.1f}% WR, {result.total_trades/result.data_days:.2f} tr/d")
print(f"  Expected: 5593 trades, 82.9% WR, 4.17 tr/d")

# Save result
output = {
    "step": 1, "symbol": "EURUSD", "config": tier_config,
    "total_trades": result.total_trades, "wins": result.wins, "losses": result.losses,
    "win_rate": result.win_rate, "total_pnl_pips": result.total_pnl_pips,
    "profit_factor": result.profit_factor, "avg_win_pips": result.avg_win_pips,
    "avg_loss_pips": result.avg_loss_pips, "expectancy_pips": result.expectancy_pips,
    "sharpe_ratio": result.sharpe_ratio, "max_drawdown_pips": result.max_drawdown_pips,
    "max_consec_wins": result.max_consec_wins, "max_consec_losses": result.max_consec_losses,
    "tier_stats": result.tier_stats, "loop_stats": result.loop_stats,
    "data_bars": result.data_bars, "data_days": result.data_days,
    "elapsed_seconds": elapsed,
    "raw_trades": [
        {
            "entry_time": t.entry_time.isoformat(), "exit_time": t.exit_time.isoformat(),
            "direction": t.direction, "entry_price": t.entry_price,
            "exit_price": t.exit_price, "pnl_pips": t.pnl_pips,
            "result": t.result, "tier": t.tier, "loop_count": t.loop_count,
        }
        for t in result.trades
    ],
}
with open(OUT_PATH, 'w') as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nSaved to {OUT_PATH}")
