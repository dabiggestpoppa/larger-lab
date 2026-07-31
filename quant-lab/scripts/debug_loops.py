"""Debug: run a single pair and check loop stats directly."""
import sys, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

# Run EURUSD
asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

bt = SymmetryTrapBacktest(
    pip_size=config["pip_value"],
    tier_config=config["tiers"],
    symbol=asset_key,
    config=config,
)
result = bt.run_from_csv(csv_path)

print("=== EURUSD LOOP STATS ===")
print("loop_stats:", result.loop_stats)
print("total_trades:", result.total_trades)
print("data_days:", result.data_days)
print("data_bars:", result.data_bars)

# Count trades by loop
if result.loop_stats:
    for loop_key in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        ls = result.loop_stats[loop_key]
        print("  Loop {}: {} tr, {:.1f}% WR, {:.1f}p".format(loop_key, ls['trades'], ls['wr'], ls['pnl']))
else:
    print("  NO LOOP STATS - loops 2-5 never fired")

# Also check: how many trades have loop_count > 1?
if result.trades:
    loop_counts = {}
    for t in result.trades:
        lc = getattr(t, 'loop_count', 1)
        loop_counts[lc] = loop_counts.get(lc, 0) + 1
    print("\nTrade loop distribution from trade records:")
    for lc in sorted(loop_counts.keys()):
        print("  Loop {}: {} trades".format(lc, loop_counts[lc]))
