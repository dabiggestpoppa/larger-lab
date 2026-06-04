"""
ISOLATED TEST: New Percentile Config vs Old Config
Tests whether the percentile-based tier thresholds produce more trades.
"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

# Old config (current in asset_configs.py)
old_config = ASSET_CONFIGS["EURGBP"]
print("=== OLD CONFIG (K-Means + percentile capping) ===")
print("T1: ar_max={}, trigger={}, au={}".format(
    old_config["tiers"]["T1"]["ar_max"], old_config["tiers"]["T1"]["trigger"], old_config["tiers"]["T1"]["au"]))
print("T2: ar_max={}, trigger={}, au={}".format(
    old_config["tiers"]["T2"]["ar_max"], old_config["tiers"]["T2"]["trigger"], old_config["tiers"]["T2"]["au"]))
print("T3: ar_max={}, trigger={}, au={}".format(
    old_config["tiers"]["T3"]["ar_max"], old_config["tiers"]["T3"]["trigger"], old_config["tiers"]["T3"]["au"]))

bt_old = SymmetryTrapBacktest(
    pip_size=old_config["pip_value"],
    tier_config=old_config["tiers"],
    symbol="EURGBP_OLD",
    config=old_config,
)
result_old = bt_old.run_from_csv(csv_path)
print("Results: {} trades | {} days | {:.3f} tr/day | WR: {:.1f}%".format(
    result_old.total_trades, result_old.data_days,
    result_old.total_trades / result_old.data_days if result_old.data_days else 0,
    result_old.win_rate))
print("Tier distribution: {}".format(
    {t: sum(1 for tr in result_old.trades if getattr(tr, 'tier', '') == t) for t in ['T1', 'T2', 'T3']}))
print("Loop stats: {}".format(result_old.loop_stats))

# New config (percentile-based from tier_discovery_all.json)
import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\tier_discovery_all.json') as f:
    new_configs = json.load(f)

new_tiers = new_configs["EURGBP"]
print("\n=== NEW CONFIG (Percentile boundaries) ===")
print("T1: ar_max={}, trigger={}, au={}".format(
    new_tiers["T1"]["range_max"], new_tiers["T1"]["trig"], new_tiers["T1"]["au"]))
print("T2: ar_max={}, trigger={}, au={}".format(
    new_tiers["T2"]["range_max"], new_tiers["T2"]["trig"], new_tiers["T2"]["au"]))
print("T3: ar_max={}, trigger={}, au={}".format(
    new_tiers["T3"]["range_min"], new_tiers["T3"]["trig"], new_tiers["T3"]["au"]))

# Build config in the format the engine expects
new_config = {
    "pip_value": 0.0001,
    "tiers": {
        "T1": {"ar_max": new_tiers["T1"]["range_max"], "trigger": new_tiers["T1"]["trig"], "au": new_tiers["T1"]["au"]},
        "T2": {"ar_max": new_tiers["T2"]["range_max"], "trigger": new_tiers["T2"]["trig"], "au": new_tiers["T2"]["au"]},
        "T3": {"ar_max": new_tiers["T3"]["range_min"], "trigger": new_tiers["T3"]["trig"], "au": new_tiers["T3"]["au"]},
    }
}

bt_new = SymmetryTrapBacktest(
    pip_size=0.0001,
    tier_config=new_config["tiers"],
    symbol="EURGBP_NEW",
    config=new_config,
)
result_new = bt_new.run_from_csv(csv_path)
print("Results: {} trades | {} days | {:.3f} tr/day | WR: {:.1f}%".format(
    result_new.total_trades, result_new.data_days,
    result_new.total_trades / result_new.data_days if result_new.data_days else 0,
    result_new.win_rate))
print("Tier distribution: {}".format(
    {t: sum(1 for tr in result_new.trades if getattr(tr, 'tier', '') == t) for t in ['T1', 'T2', 'T3']}))
print("Loop stats: {}".format(result_new.loop_stats))

print("\n=== COMPARISON ===")
print("OLD: {} trades | {:.3f} tr/day".format(result_old.total_trades, result_old.total_trades / result_old.data_days if result_old.data_days else 0))
print("NEW: {} trades | {:.3f} tr/day".format(result_new.total_trades, result_new.total_trades / result_new.data_days if result_new.data_days else 0))
if result_new.total_trades > result_old.total_trades:
    print(">>> NEW CONFIG WINS: +{} trades ({:+.1f}%)".format(
        result_new.total_trades - result_old.total_trades,
        (result_new.total_trades / result_old.total_trades - 1) * 100))
else:
    print(">>> NEW CONFIG LOSES: {} trades ({:+.1f}%)".format(
        result_new.total_trades - result_old.total_trades,
        (result_new.total_trades / result_old.total_trades - 1) * 100))
