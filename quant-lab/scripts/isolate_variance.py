"""
ISOLATION TEST: Find the source of EURUSD trade count variance.
Original June 4th: t1=12.0 -> 5,593 trades
Current engine:    t1=12.0 -> 3,186 trades
"""
import sys, time
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from symmetry_trap import SymmetryTrapEngine

pair = "EURUSD"
cfg = ASSET_CONFIGS[pair]
csv_path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv"

pip_from_config = cfg.get("pip_value", 0.0001)

bars_config_pip, _ = load_m5_csv(csv_path, pip_size=pip_from_config)
bars_norm_pip, _ = load_m5_csv(csv_path, pip_size=0.10)

print("=" * 70)
print("ISOLATION TEST EURUSD Trade Count Variance")
print("=" * 70)
print("Config pip_value: %s" % pip_from_config)
print("Normalized pip:   0.10")
print("Bars (config pip): %d" % len(bars_config_pip))
print("Bars (norm pip):   %d" % len(bars_norm_pip))

orig_tiers = cfg["tiers"]
print("\nOriginal tiers: T1 trigger=%s ar_max=%s au=%s" % (orig_tiers["T1"]["trigger"], orig_tiers["T1"]["ar_max"], orig_tiers["T1"]["au"]))
print("                T2 trigger=%s ar_max=%s au=%s" % (orig_tiers["T2"]["trigger"], orig_tiers["T2"]["ar_max"], orig_tiers["T2"]["au"]))
print("                T3 trigger=%s ar_max=%s au=%s" % (orig_tiers["T3"]["trigger"], orig_tiers["T3"]["ar_max"], orig_tiers["T3"]["au"]))

# TEST 1: Original method config=cfg tier_config=None
print("\n" + "-" * 70)
print("TEST 1: config=cfg (original June 4th method)")
print("-" * 70)
t0 = time.time()
bt1 = SymmetryTrapBacktest(pip_size=pip_from_config, config=cfg, symbol=pair)
r1 = bt1.run(bars_config_pip)
t1 = time.time() - t0
print("  Trades=%d | WR=%.1f%% | PF=%.2f | PnL=%.1f | %.1fs" % (r1.total_trades, r1.win_rate, r1.profit_factor, r1.total_pnl_pips, t1))
print("  Engine pip_size: %s" % bt1.pip_size)
print("  Engine tier_config T1: %s" % str(bt1.tier_config.get("T1")))

# TEST 2: config=None, tier_config=orig_tiers, pip_size=raw
print("\n" + "-" * 70)
print("TEST 2: config=None, tier_config=orig_tiers, pip_size=%s" % pip_from_config)
print("-" * 70)
t0 = time.time()
bt2 = SymmetryTrapBacktest(pip_size=pip_from_config, tier_config=orig_tiers, symbol=pair, config=None)
r2 = bt2.run(bars_config_pip)
t2 = time.time() - t0
print("  Trades=%d | WR=%.1f%% | PF=%.2f | PnL=%.1f | %.1fs" % (r2.total_trades, r2.win_rate, r2.profit_factor, r2.total_pnl_pips, t2))

# TEST 3: config=None, tier_config=orig_tiers, pip_size=0.10
print("\n" + "-" * 70)
print("TEST 3: config=None, tier_config=orig_tiers, pip_size=0.10")
print("-" * 70)
t0 = time.time()
bt3 = SymmetryTrapBacktest(pip_size=0.10, tier_config=orig_tiers, symbol=pair, config=None)
r3 = bt3.run(bars_norm_pip)
t3 = time.time() - t0
print("  Trades=%d | WR=%.1f%% | PF=%.2f | PnL=%.1f | %.1fs" % (r3.total_trades, r3.win_rate, r3.profit_factor, r3.total_pnl_pips, t3))

# TEST 4: DEFAULT tiers, no config
print("\n" + "-" * 70)
print("TEST 4: DEFAULT tier config, pip_size=%s" % pip_from_config)
print("-" * 70)
t0 = time.time()
bt4 = SymmetryTrapBacktest(pip_size=pip_from_config, symbol=pair, config=None)
r4 = bt4.run(bars_config_pip)
t4 = time.time() - t0
print("  Trades=%d | WR=%.1f%% | PF=%.2f | PnL=%.1f | %.1fs" % (r4.total_trades, r4.win_rate, r4.profit_factor, r4.total_pnl_pips, t4))
print("  DEFAULT tiers: %s" % str(bt4.tier_config))

# BAR COMPARISON
print("\n" + "-" * 70)
print("BAR COMPARISON First and Last")
print("-" * 70)
bc0 = bars_config_pip[0]
bn0 = bars_norm_pip[0]
print("  First config_pip: ts=%s O=%s H=%s L=%s C=%s" % (bc0.timestamp, bc0.open, bc0.high, bc0.low, bc0.close))
print("  First norm_pip:   ts=%s O=%s H=%s L=%s C=%s" % (bn0.timestamp, bn0.open, bn0.high, bn0.low, bn0.close))
if bc0.open != bn0.open:
    print("  *** BARS DIFFER from first bar ***")

bcN = bars_config_pip[-1]
bnN = bars_norm_pip[-1]
print("  Last config_pip: ts=%s O=%s H=%s L=%s C=%s" % (bcN.timestamp, bcN.open, bcN.high, bcN.low, bcN.close))
print("  Last norm_pip:   ts=%s O=%s H=%s L=%s C=%s" % (bnN.timestamp, bnN.open, bnN.high, bnN.low, bnN.close))

# Check load_m5_csv with different pip_size values
print("\n" + "-" * 70)
print("LOAD_M5_CSV behavior at different pip_size values")
print("-" * 70)
for ps in [0.0001, 0.001, 0.01, 0.10, 1.0]:
    b, s = load_m5_csv(csv_path, pip_size=ps)
    print("  pip_size=%s -> bars=%d symbol=%s first_open=%s" % (ps, len(b), s, b[0].open if b else "N/a"))

# Check what fields engine reads from config
print("\n" + "-" * 70)
print("ENGINE SymmetryTrapEngine config field usage")
print("-" * 70)
eng_full = SymmetryTrapEngine(pip_size=pip_from_config, tier_config=None, symbol=pair, config=cfg)
eng_none = SymmetryTrapEngine(pip_size=pip_from_config, tier_config=orig_tiers, symbol=pair, config=None)
print("  With config:    pip_size=%s" % eng_full.pip_size)
print("  Without config: pip_size=%s" % eng_none.pip_size)
print("  Config k_factor=%s p90=%s fixed_tp=%s gear_shifts=%s" % (cfg.get("k_factor"), cfg.get("p90_threshold"), cfg.get("fixed_tp"), cfg.get("gear_shifts")))
