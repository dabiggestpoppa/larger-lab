"""Debug EURGBP vs EURUSD — why does more data = fewer trades?"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

# Compare configs
print("=== CONFIG COMPARISON ===")
for key in ["EURUSD", "EURGBP"]:
    cfg = ASSET_CONFIGS[key]
    print("\n{}:".format(key))
    print("  pip_value: {}".format(cfg["pip_value"]))
    print("  tiers:")
    for tier_name, tier_cfg in cfg["tiers"].items():
        print("    {}: ar_max={:.2f}, trigger={:.2f}, au={:.2f}".format(
            tier_name, tier_cfg.get("ar_max", 0), tier_cfg.get("trigger", 0), tier_cfg.get("au", 0)))

# Run EURGBP with EURUSD's config to see if it's the config causing low trades
print("\n\n=== EURGBP WITH EURUSD CONFIG (test) ===")
cfg_eurusd = ASSET_CONFIGS["EURUSD"]
csv_eurgbp = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

bt = SymmetryTrapBacktest(
    pip_size=cfg_eurusd["pip_value"],
    tier_config=cfg_eurusd["tiers"],
    symbol="EURGBP_TEST",
    config=cfg_eurusd,
)
result = bt.run_from_csv(csv_eurgbp)
print("EURGBP with EURUSD config:")
print("  data_days: {}".format(result.data_days))
print("  total_trades: {}".format(result.total_trades))
print("  trades/day: {:.3f}".format(result.total_trades / result.data_days if result.data_days else 0))
print("  win_rate: {:.1f}%".format(result.win_rate))
print("  loop_stats: {}".format(result.loop_stats))
