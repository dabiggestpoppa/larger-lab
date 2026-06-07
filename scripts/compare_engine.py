"""Compare engine output with baseline for EURUSD t1=12."""
import sys, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import importlib
import symmetry_trap
import symmetry_trap_backtest
importlib.reload(symmetry_trap)
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from copy import deepcopy

pair = 'EURUSD'
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

cfg = deepcopy(ASSET_CONFIGS[pair])
cfg['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 19.0},
}
pip_value = 0.0001

bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)

t0 = time.time()
result = bt.run(bars)
elapsed = time.time() - t0

wins = [t for t in result.trades if t.pnl_pips > 0]
losses = [t for t in result.trades if t.pnl_pips <= 0]
avg_w = sum(t.pnl_pips for t in wins) / len(wins) if wins else 0
avg_l = sum(t.pnl_pips for t in losses) / len(losses) if losses else 0
total_pnl = sum(t.pnl_pips for t in result.trades)

print('My engine (t1=12, ar_max=60, 4PM):')
print('  trades=%d (baseline: 5593)' % result.total_trades)
print('  wr=%.1f%% (baseline: 82.9%%)' % result.win_rate)
print('  pf=%.2f (baseline: 12.5)' % result.profit_factor)
print('  pnl=%.1f (baseline: 33421)' % total_pnl)
print('  avg_w=%.2f (baseline: 7.84)' % avg_w)
print('  avg_l=%.2f (baseline: -3.11)' % avg_l)
print('  days=%d' % result.data_days)
print('  time=%.1fs' % elapsed)

# Loop distribution
loop_counts = {}
for t in result.trades:
    lc = t.loop_count
    loop_counts[lc] = loop_counts.get(lc, 0) + 1
print('  Loop distribution:', dict(sorted(loop_counts.items())))

# Tier distribution
tier_counts = {}
for t in result.trades:
    tier = t.tier
    tier_counts[tier] = tier_counts.get(tier, 0) + 1
print('  Tier distribution:', dict(sorted(tier_counts.items())))

# Direction distribution
long_count = sum(1 for t in result.trades if t.direction == 'LONG')
short_count = sum(1 for t in result.trades if t.direction == 'SHORT')
print('  LONG: %d, SHORT: %d' % (long_count, short_count))
