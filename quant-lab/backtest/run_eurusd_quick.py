"""Quick EURUSD backtest with detailed output to debug WR discrepancy."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv, BacktestResult
from symmetry_trap import EngineState

EST = __import__('pytz').timezone('US/Eastern')
from datetime import timedelta
import pytz

asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
pip_size = config["pip_value"]
tier_config = config["tiers"]

print(f"Config: k={config['k_factor']}, pip={pip_size}")
print(f"Tiers: {json.dumps(tier_config, indent=2)}")

bt = SymmetryTrapBacktest(pip_size=pip_size, tier_config=tier_config, symbol=asset_key, config=config)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
result = bt.run_from_csv(str(csv_path))

print(f"\nResults:")
print(f"  Trades: {result.total_trades}")
print(f"  Wins: {result.wins}, Losses: {result.losses}")
print(f"  WR: {result.win_rate:.1f}%")
print(f"  PnL: {result.total_pnl_pips:+.1f}p")
print(f"  PF: {result.profit_factor:.2f}")
print(f"  AvgWin: {result.avg_win_pips:.1f}p, AvgLoss: {result.avg_loss_pips:.1f}p")
print(f"  MaxDD: {result.max_drawdown_pips:.1f}p")

if result.tier_stats:
    print(f"\n  Tier breakdown:")
    for tn, ts in result.tier_stats.items():
        print(f"    {tn}: {ts['trades']} tr, {ts['wr']:.1f}% WR, {ts['pnl']:+.1f}p")

if result.loop_stats:
    print(f"\n  Loop breakdown:")
    for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        ls = result.loop_stats[lk]
        print(f"    Loop {lk}: {ls['trades']} tr, {ls['wr']:.1f}% WR, {ls['pnl']:+.1f}p")

if result.hourly_stats:
    print(f"\n  Hourly breakdown:")
    for h in sorted(result.hourly_stats.keys(), key=int):
        hs = result.hourly_stats[h]
        print(f"    {int(h):02d}:00 EST: {hs['trades']} tr, {hs['wr']:.1f}% WR, {hs['pnl']:+.1f}p")

# Exit type distribution
from collections import Counter
exit_types = Counter(t.result for t in result.trades)
print(f"\n  Exit types:")
for et, cnt in exit_types.most_common():
    pnl_sum = sum(t.pnl_pips for t in result.trades if t.result == et)
    print(f"    {et}: {cnt} ({cnt/result.total_trades*100:.1f}%), pnl={pnl_sum:+.1f}p")
