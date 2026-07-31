"""Full validation: ar_max=999, t1=12 vs sweep baseline for EURUSD."""
import sys, time, json
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

# Load baseline
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    sweep = json.load(f)

baseline = None
for e in sweep['EURUSD']:
    if abs(e['t1_trigger'] - 12.0) < 0.1:
        baseline = e
        break

# Run my engine
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
cfg = deepcopy(ASSET_CONFIGS['EURUSD'])
cfg['tiers'] = {
    'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
}
pip_value = 0.0001
bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol='EURUSD', config=cfg)
r = bt.run(bars)

# Compute detailed stats
wins = [t for t in r.trades if t.pnl_pips > 0]
losses = [t for t in r.trades if t.pnl_pips <= 0]
avg_w = sum(t.pnl_pips for t in wins) / len(wins) if wins else 0
avg_l = sum(t.pnl_pips for t in losses) / len(losses) if losses else 0
total_pnl = sum(t.pnl_pips for t in r.trades)
exp = total_pnl / r.total_trades if r.total_trades > 0 else 0

# Max consecutive wins/losses
max_cw = 0
max_cl = 0
cw = 0
cl = 0
for t in r.trades:
    if t.pnl_pips > 0:
        cw += 1
        cl = 0
        max_cw = max(max_cw, cw)
    else:
        cl += 1
        cw = 0
        max_cl = max(max_cl, cl)

print('=' * 60)
print('EURUSD VALIDATION: ar_max=999, t1=12 vs Sweep Baseline')
print('=' * 60)
print()
print('%-20s %-12s %-12s %-10s' % ('Metric', 'My Engine', 'Baseline', 'Delta'))
print('-' * 60)
print('%-20s %-12d %-12d %+.1f%%' % ('Trades', r.total_trades, baseline['trades'], (r.total_trades - baseline['trades'])/baseline['trades']*100))
print('%-20s %-12.1f %-12.1f %+.1f%%' % ('WR%', r.win_rate, baseline['wr'], r.win_rate - baseline['wr']))
print('%-20s %-12.2f %-12.2f %+.2f' % ('PF', r.profit_factor, baseline['pf'], r.profit_factor - baseline['pf']))
print('%-20s %-12.1f %-12.1f %+.1f' % ('PnL (pips)', total_pnl, baseline['pnl'], total_pnl - baseline['pnl']))
print('%-20s %-12.2f %-12.2f %+.2f' % ('Avg Win', avg_w, baseline['avg_w'], avg_w - baseline['avg_w']))
print('%-20s %-12.2f %-12.2f %+.2f' % ('Avg Loss', avg_l, baseline['avg_l'], avg_l - baseline['avg_l']))
print('%-20s %-12.2f %-12.2f %+.2f' % ('Expectancy', exp, baseline['exp'], exp - baseline['exp']))
print('%-20s %-12d %-12d' % ('Max Cons Wins', max_cw, baseline['max_cw']))
print('%-20s %-12d %-12d' % ('Max Cons Losses', max_cl, baseline['max_cl']))
print('%-20s %-12d %-12d' % ('Days', r.data_days, baseline['days']))
print('%-20s %-12.2f %-12.2f' % ('Tr/Day', r.total_trades/baseline['days'], baseline['tr_per_day']))

print()
trade_delta = abs(r.total_trades - baseline['trades']) / baseline['trades'] * 100
if trade_delta <= 2:
    print('VERDICT: EXACT MATCH (%.1f%% deviation)' % trade_delta)
elif trade_delta <= 5:
    print('VERDICT: MATCH (%.1f%% deviation)' % trade_delta)
else:
    print('VERDICT: OFF (%.1f%% deviation)' % trade_delta)

# Tier distribution
tier_counts = {}
for t in r.trades:
    tier_counts[t.tier] = tier_counts.get(t.tier, 0) + 1
print()
print('Tier distribution:', dict(sorted(tier_counts.items())))

# Loop distribution
loop_counts = {}
for t in r.trades:
    lc = t.loop_count
    loop_counts[lc] = loop_counts.get(lc, 0) + 1
print('Loop distribution:', dict(sorted(loop_counts.items())))

# Direction
long_count = sum(1 for t in r.trades if t.direction == 'LONG')
short_count = sum(1 for t in r.trades if t.direction == 'SHORT')
print('Direction: LONG=%d SHORT=%d' % (long_count, short_count))
