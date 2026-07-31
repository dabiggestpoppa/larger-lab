"""Check if PRO pairs are actually loading all their historical data."""
import sys, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

# Test a PRO pair with long data
asset_key = "EURGBP"
config = ASSET_CONFIGS[asset_key]
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

bt = SymmetryTrapBacktest(
    pip_size=config["pip_value"],
    tier_config=config["tiers"],
    symbol=asset_key,
    config=config,
)
result = bt.run_from_csv(csv_path)

print("=== EURGBP (PRO, 10.5 yrs data) ===")
print("data_bars:", result.data_bars)
print("data_days:", result.data_days)
print("total_trades:", result.total_trades)
print("win_rate:", result.win_rate)
print("trades/day:", round(result.total_trades / result.data_days, 3) if result.data_days else 0)
print()
print("loop_stats:", result.loop_stats)

# Now test an ORIG pair
asset_key2 = "EURUSD"
config2 = ASSET_CONFIGS[asset_key2]
csv_path2 = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

bt2 = SymmetryTrapBacktest(
    pip_size=config2["pip_value"],
    tier_config=config2["tiers"],
    symbol=asset_key2,
    config=config2,
)
result2 = bt2.run_from_csv(csv_path2)

print("\n=== EURUSD (ORIG, 4 yrs data) ===")
print("data_bars:", result2.data_bars)
print("data_days:", result2.data_days)
print("total_trades:", result2.total_trades)
print("win_rate:", result2.win_rate)
print("trades/day:", round(result2.total_trades / result2.data_days, 3) if result2.data_days else 0)
print()
print("loop_stats:", result2.loop_stats)

# Compare: EURGBP has ~2.5x more data days but how many more trades?
print("\n=== COMPARISON ===")
print("EURGBP: {} days, {} trades, {:.3f} tr/day".format(result.data_days, result.total_trades, result.total_trades/result.data_days if result.data_days else 0))
print("EURUSD: {} days, {} trades, {:.3f} tr/day".format(result2.data_days, result2.total_trades, result2.total_trades/result2.data_days if result2.data_days else 0))
print()
print("EURGBP has {:.1f}x more days but only {:.1f}x more trades".format(
    result.data_days / result2.data_days if result2.data_days else 0,
    result.total_trades / result2.total_trades if result2.total_trades else 0
))
