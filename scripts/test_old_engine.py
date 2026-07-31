"""Test with OLD engine to confirm it matches baseline"""
import sys, time, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')

# Load OLD engine from .bak
import importlib.util
spec = importlib.util.spec_from_file_location(
    "symmetry_trap_old",
    r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak"
)
old_engine_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_engine_mod)

# Also need the old backtest
spec2 = importlib.util.spec_from_file_location(
    "symmetry_trap_backtest_old",
    r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap_backtest.py"
)
# The backtest imports from symmetry_trap, so we need to patch it
import symmetry_trap_backtest
# Replace the engine class
symmetry_trap_backtest.SymmetryTrapEngine = old_engine_mod.SymmetryTrapEngine
# Re-import
import importlib
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS

pair = 'EURUSD'
data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'
csv_path = os.path.join(data_dir, pair + '_M5.csv')
cfg = ASSET_CONFIGS[pair]

pip_value = cfg.get('pip_value', 0.0001)

bars, _ = symmetry_trap_backtest.load_m5_csv(csv_path, pip_size=pip_value)
n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
print("Bars: %d, Days: %d" % (len(bars), n_days))

bt = symmetry_trap_backtest.SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)

t0 = time.time()
result = bt.run(bars)
elapsed = time.time() - t0

print("\n=== OLD ENGINE RESULTS ===")
print("Baseline: 5593 trades, 82.9%% WR, PF 12.5")
print("Old engine: %d trades, %.1f%% WR, PF %.1f, %d days" % (
    result.total_trades, result.win_rate, result.profit_factor, result.data_days))

delta = result.total_trades - 5593
pct = (delta / 5593.0) * 100
print("Delta: %+d trades (%+.1f%%)" % (delta, pct))
print("Time: %.1fs" % elapsed)

if abs(pct) <= 10:
    print("\nOLD ENGINE MATCHES BASELINE - confirms regression in new engine")
else:
    print("\nOld engine also doesn't match - data or config issue")
