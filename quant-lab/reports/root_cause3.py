import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

# The sweep does:
#   pip_value = get_pip_val(pair)  -> 0.07 for JPY pairs
#   bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
#   bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=scaled_config)
#   result = bt.run(bars)

# The backtest __init__:
#   if config is not None:
#     self.pip_size = config.get("pip_value", pip_size)  -> 0.01 (from config!)
#     self.tier_config = tier_config if tier_config is not None else config.get("tiers", ...)
#   self.config = config

# Then in run():
#   engine = SymmetryTrapEngine(pip_size=self.pip_size, tier_config=self.tier_config, symbol=self.symbol, config=self.config)

# The engine __init__:
#   if config is not None:
#     self.pip_size = config.get("pip_value", pip_size)  -> 0.01 again

# So the ACTUAL pip_size used by the engine is 0.01 (from ASSET_CONFIGS)
# NOT 0.07 (what the sweep intended)

# For CHFJPY:
# Price ~150-200, 1 pip = 0.01
# trigger = 17 pips = 17 * 0.01 = 0.17 price units (CORRECT)

# If pip_size were 0.07:
# trigger = 17 pips = 17 * 0.07 = 1.19 price units (WRONG - 7x too large)

# So the engine is using pip_size=0.01, which IS correct for CHFJPY
# The sweep's get_pip_val() returning 0.07 is the WRONG value
# But it doesn't matter because the engine overrides it with config's pip_value=0.01

# So pip_size is NOT the issue for CHFJPY

# Let me check: what pip_size does the BASELINE sweep use?
# The baseline was likely run with a different script
# Let me check if there's a pattern in the baseline data

import json
base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))

# Check EURUSD baseline
# EURUSD in ASSET_CONFIGS has pip_value=0.0001
# If baseline used pip_size=0.0001 correctly:
#   trigger=12 pips = 12 * 0.0001 = 0.0012 price units
# If baseline used pip_size=0.1 (wrong for EURUSD):
#   trigger=12 pips = 12 * 0.1 = 1.2 price units (way too large)

# The baseline EURUSD at t1=12 gives 5593 trades
# This is a reasonable number, suggesting pip_size was correct

# Let me check the new sweep's result for EURUSD
# It's not in the new sweep output (only 7 JPY pairs)
# But the question is: would EURUSD also show fewer trades?

# The answer depends on whether the baseline used a DIFFERENT engine version
# Let me check the engine version that was used for the baseline

# The baseline was generated on June 4th
# The engine has been modified since then (we have a .bak file)
# The .bak file represents the OLD engine

# Key differences between OLD and NEW engine:
# 1. DEFAULT_TIER_CONFIG: OLD had ar_max=20/30/45, NEW has ar_max=60/60/60
#    But this only matters when ASSET_CONFIGS tiers aren't provided
#    Since we pass asset configs, this shouldn't matter

# 2. classify_tier vs classify_tier_by_ar + classify_tier_by_impulse
#    OLD: Session init classifies tier and sets trigger
#    NEW: Session init only gates, impulse detection uses T1 trigger

# 3. Kill switch: OLD had it, NEW doesn't
#    This should INCREASE trades in NEW

# 4. DZ zone: OLD had 32% floor for loop 1, NEW has 20% for all
#    This should INCREASE trades in NEW

# 5. 4h timeout: OLD had it, NEW doesn't
#    This should INCREASE trades in NEW

# All changes should INCREASE trades, but we see 44x FEWER
# So there must be something else...

# WAIT. Let me re-read the backtest run() method more carefully
# Maybe the issue is in how signals are processed, not generated

print("=== SIGNAL PROCESSING IN BACKTEST ===")
print("Let me check if the backtest handles the ENTRY signal correctly")
print("")

# Actually, let me just run a quick test:
# Load CHFJPY data, run with OLD engine (.bak) vs NEW engine, compare

# First, let me check if the .bak engine can even be imported
import importlib.util
spec = importlib.util.spec_from_file_location("symmetry_trap_old", r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak")
if spec and spec.loader:
    print("Can load .bak engine")
else:
    print("Cannot load .bak engine")

# Try a different approach: run the new engine on a small data sample
# and count how many signals it generates

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\CHFJPY_M5.csv'
pip_value = 0.01  # from ASSET_CONFIGS
bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
print(f"\nLoaded {len(bars)} bars for CHFJPY")

# Run with a small subset
subset = bars[:50000]  # ~2 days of M5 data
cfg = ASSET_CONFIGS['CHFJPY']

bt = SymmetryTrapBacktest(pip_size=pip_value, symbol='CHFJPY', config=cfg)
result = bt.run(subset)

print(f"\nResult on {len(subset)} bars ({subset[0].timestamp} to {subset[-1].timestamp}):")
print(f"  Total trades: {result.total_trades}")
print(f"  Win rate: {result.win_rate:.1f}%")
print(f"  Days: {result.data_days}")

# Now the question: does the baseline sweep script use the SAME backtest class?
# Or does it use a different simulation approach?

# The baseline trigger_sweep_max_accuracy.json was generated on June 4th
# by a different script (not sweep_forex_full.py)
# That script might have used a different backtest engine or different parameters

# Let me check: is there a script that was used for the baseline?
print("\n=== CHECKING FOR BASELINE SCRIPT ===")
import os
scripts_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts'
for f in os.listdir(scripts_dir):
    if 'sweep' in f.lower() or 'accuracy' in f.lower():
        print(f"  {f}")
