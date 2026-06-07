"""
Verify: Is the asset config the source of variance across ALL pairs?
Compare DEFAULT config vs asset config trade counts for key pairs.
"""
import sys, time
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

DATA_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data"

# Key pairs to check
pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
         "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "EURNZD", "GBPNZD"]

print("=" * 90)
print("CONFIG vs DEFAULT COMPARISON — Is asset config the variance source?")
print("=" * 90)
print("\n%-10s | %6s | %5s | %5s | %5s | %6s | %5s | %5s | %5s | %6s" % (
    "Pair", "CfgTrd", "CfgWR", "CfgPF", "CfgPnL", "DefTrd", "DefWR", "DefPF", "DefPnL", "Delta%"))
print("-" * 90)

for pair in pairs:
    cfg = ASSET_CONFIGS[pair]
    csv_path = DATA_DIR + "\\" + pair + "_M5.csv"
    import os
    if not os.path.exists(csv_path):
        candidates = sorted([f for f in os.listdir(DATA_DIR) if f.startswith(pair) and f.endswith(".csv")])
        if candidates:
            csv_path = DATA_DIR + "\\" + candidates[0]
        else:
            print("%-10s | NO CSV" % pair)
            continue

    pip = cfg.get("pip_value", 0.0001)
    bars, _ = load_m5_csv(csv_path, pip_size=pip)
    if not bars:
        print("%-10s | NO BARS" % pair)
        continue

    # Test with asset config
    t0 = time.time()
    bt_cfg = SymmetryTrapBacktest(pip_size=pip, config=cfg, symbol=pair)
    r_cfg = bt_cfg.run(bars)
    t_cfg = time.time() - t0

    # Test with DEFAULT config (no config param)
    t0 = time.time()
    bt_def = SymmetryTrapBacktest(pip_size=pip, symbol=pair, config=None)
    r_def = bt_def.run(bars)
    t_def = time.time() - t0

    delta_pct = ((r_def.total_trades - r_cfg.total_trades) / r_cfg.total_trades * 100) if r_cfg.total_trades > 0 else 999

    print("%-10s | %6d | %5.1f | %5.2f | %5.0f | %6d | %5.1f | %5.2f | %5.0f | %+5.0f%%" % (
        pair, r_cfg.total_trades, r_cfg.win_rate, r_cfg.profit_factor, r_cfg.total_pnl_pips,
        r_def.total_trades, r_def.win_rate, r_def.profit_factor, r_def.total_pnl_pips,
        delta_pct))

    # Show the tier configs for context
    if r_cfg.total_trades == 0 or abs(delta_pct) > 50:
        print("  *** LARGE DELTA ***")
        print("  Asset config T1: %s" % str(cfg["tiers"]["T1"]))
        print("  DEFAULT T1:      %s" % str(bt_def.tier_config["T1"]))

print("\n" + "=" * 90)
print("CONCLUSION: If Delta% is large negative, asset config is suppressing trades")
print("vs the DEFAULT config that was used in original June 4th sweeps")
