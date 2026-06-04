"""Check hourly distribution of trades."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

for asset_key, csv_name in [("EURUSD", "EURUSD_M5.csv"), ("EURGBP", "EURGBP_PRO_M5.csv")]:
    config = ASSET_CONFIGS[asset_key]
    csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\{}'.format(csv_name)
    
    bt = SymmetryTrapBacktest(
        pip_size=config["pip_value"],
        tier_config=config["tiers"],
        symbol=asset_key,
        config=config,
    )
    result = bt.run_from_csv(csv_path)
    
    print("=== {} HOURLY DISTRIBUTION ===".format(asset_key))
    if result.hourly_stats:
        total_trades = result.total_trades
        for h in sorted(result.hourly_stats.keys(), key=int):
            hs = result.hourly_stats[h]
            pct = hs['trades'] / total_trades * 100 if total_trades else 0
            bar = '#' * int(pct / 2)
            print("  {:02d}:00 EST | {:>5} tr ({:>5.1f}%) | {:>5.1f}% WR | {:>+8.1f}p | {}".format(
                int(h), hs['trades'], pct, hs['wr'], hs['pnl'], bar))
    print("  TOTAL    | {:>5} tr".format(result.total_trades))
    print()
