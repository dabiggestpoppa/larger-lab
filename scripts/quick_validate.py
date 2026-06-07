"""Quick validation: EURUSD at t1=12.0 should give 5593 trades"""
import sys, time, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

pair = 'EURUSD'
data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'
csv_path = os.path.join(data_dir, pair + '_M5.csv')
cfg = ASSET_CONFIGS[pair]

print("Config for %s:" % pair)
for t in ['T1', 'T2', 'T3']:
    tier = cfg['tiers'][t]
    print("  %s: ar_max=%s, au=%s, trigger=%s" % (t, tier['ar_max'], tier['au'], tier['trigger']))

pip_value = cfg.get('pip_value', 0.0001)
print("pip_value: %s" % pip_value)

bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
print("Bars: %d, Days: %d" % (len(bars), n_days))

bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)

t0 = time.time()
result = bt.run(bars)
elapsed = time.time() - t0

print("\n=== RESULTS ===")
print("Baseline: 5593 trades, 82.9%% WR, PF 12.5, 1341 days, 4.17 tr/d")
print("New:      %d trades, %.1f%% WR, PF %.1f, %d days" % (
    result.total_trades, result.win_rate, result.profit_factor, result.data_days))
if result.total_trades > 0 and result.data_days > 0:
    tr_per_day = result.total_trades / result.data_days
    print("Tr/day: %.3f" % tr_per_day)

delta = result.total_trades - 5593
pct = (delta / 5593.0) * 100
print("Delta: %+d trades (%+.1f%%)" % (delta, pct))
print("Time: %.1fs" % elapsed)

if abs(pct) <= 10:
    print("\nPASS: Within 10%% tolerance")
elif abs(pct) <= 25:
    print("\nWARN: 10-25%% deviation")
else:
    print("\nFAIL: %.0f%% deviation - engine regression detected" % abs(pct))
