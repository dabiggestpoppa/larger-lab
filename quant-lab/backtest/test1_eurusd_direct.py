"""Test 1: Run EURUSD using the EXACT same code path as the multi-asset runner."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
pip_size = config["pip_value"]
tier_config = config["tiers"]

# EXACT same call as multi-asset runner line 270
bt = SymmetryTrapBacktest(
    pip_size=pip_size,
    tier_config=tier_config,
    symbol=asset_key,
    config=config,
)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
result = bt.run_from_csv(str(csv_path))

print(f"EURUSD: trades={result.total_trades}, wr={result.win_rate:.1f}%, pnl={result.total_pnl_pips:+.1f}p, pf={result.profit_factor:.2f}")
print(f"  Long: {result.long_trades} tr, {result.long_wr:.1f}% WR, {result.long_pnl:+.1f}p")
print(f"  Short: {result.short_trades} tr, {result.short_wr:.1f}% WR, {result.short_pnl:+.1f}p")
print(f"  MaxDD: {result.max_drawdown_pips:.1f}p")

from collections import Counter
exit_types = Counter(t.result for t in result.trades)
for et, cnt in exit_types.most_common():
    print(f"  {et}: {cnt} ({cnt/result.total_trades*100:.1f}%)")

if result.tier_stats:
    for tn, ts in result.tier_stats.items():
        print(f"  {tn}: {ts['trades']} tr, {ts['wr']:.1f}% WR, {ts['pnl']:+.1f}p")
