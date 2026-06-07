"""Quick check — just EURUSD and GBPUSD, minimal output."""
import sys, time
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")
from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
import os

DATA_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data"

for pair in ["EURUSD", "GBPUSD", "EURJPY"]:
    cfg = ASSET_CONFIGS[pair]
    csv_path = os.path.join(DATA_DIR, pair + "_M5.csv")
    if not os.path.exists(csv_path):
        print("%s: NO CSV" % pair)
        continue

    pip = cfg.get("pip_value", 0.0001)
    bars, _ = load_m5_csv(csv_path, pip_size=pip)
    if not bars:
        print("%s: NO BARS" % pair)
        continue

    print("\n%s: %d bars, pip=%s" % (pair, len(bars), pip))
    print("Asset config T1: %s" % str(cfg["tiers"]["T1"]))

    # With asset config
    bt1 = SymmetryTrapBacktest(pip_size=pip, config=cfg, symbol=pair)
    r1 = bt1.run(bars)
    print("  ASSET CONFIG:  trades=%d WR=%.1f%% PF=%.2f pnl=%.1f" % (r1.total_trades, r1.win_rate, r1.profit_factor, r1.total_pnl_pips))

    # With default config
    bt2 = SymmetryTrapBacktest(pip_size=pip, symbol=pair, config=None)
    r2 = bt2.run(bars)
    print("  DEFAULT CONFIG: trades=%d WR=%.1f%% PF=%.2f pnl=%.1f" % (r2.total_trades, r2.win_rate, r2.profit_factor, r2.total_pnl_pips))
    print("  DEFAULT T1: %s" % str(bt2.tier_config["T1"]))

    delta = ((r2.total_trades - r1.total_trades) / max(r1.total_trades, 1)) * 100
    print("  DELTA: %.0f%%" % delta)
