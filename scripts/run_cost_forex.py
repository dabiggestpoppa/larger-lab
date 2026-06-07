"""Run cost analysis — forex pairs only first."""
import sys, os, json, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest')

import importlib
import symmetry_trap
import symmetry_trap_backtest
import apply_costs
importlib.reload(symmetry_trap)
importlib.reload(symmetry_trap_backtest)
importlib.reload(apply_costs)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from apply_costs import run_cost_analysis
from copy import deepcopy

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    return None

# Forex pairs only (28 pairs)
forex_pairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
    'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
    'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
    'NZDJPY', 'NZDCHF', 'NZDCAD',
    'CADJPY', 'CADCHF', 'CHFJPY',
]

available = [(p, find_csv(p)) for p in forex_pairs if find_csv(p)]
print('Forex pairs available: %d of %d' % (len(available), len(forex_pairs)))
print()

results = {}
for pair, csv_path in available:
    if not csv_path:
        continue
    cfg = deepcopy(ASSET_CONFIGS.get(pair, {'pip_value': 0.0001}))
    cfg['tiers'] = {
        'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
    }
    pip_value = cfg.get('pip_value', 0.0001)
    
    t0 = time.time()
    try:
        bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
        result = bt.run(bars)
        analysis = run_cost_analysis(result.trades, pair, pip_value, lot_size=0.01)
        results[pair] = analysis
        
        elapsed = time.time() - t0
        print('%-10s | %5d tr | raw wr=%5.1f%% pf=%5.1f | adj wr=%5.1f%% pf=%5.1f | cost=%4.2fp | pnl_cost=%+5.1f%% | %.1fs' % (
            pair, analysis['raw']['trades'],
            analysis['raw']['wr'], analysis['raw']['pf'],
            analysis['adjusted']['wr'], analysis['adjusted']['pf'],
            analysis['costs']['total_cost_pips_per_trade'],
            analysis['delta']['pnl_change_pct'], elapsed))
    except Exception as e:
        print('%-10s | ERROR: %s' % (pair, str(e)[:60]))

# Summary
print()
print('=' * 90)
print('SUMMARY: Cost Impact on Forex Pairs')
print('=' * 90)
print('%-10s | %-6s | %-8s %-8s | %-8s %-8s | %-6s | %s' % (
    'Pair', 'Trades', 'Raw_WR', 'Adj_WR', 'Raw_PF', 'Adj_PF', 'Cost/t', 'PnL_Cost'))
print('-' * 90)
for pair in sorted(results.keys()):
    r = results[pair]
    print('%-10s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %+.1f%%' % (
        pair, r['raw']['trades'],
        r['raw']['wr'], r['adjusted']['wr'],
        r['raw']['pf'], r['adjusted']['pf'],
        r['costs']['total_cost_pips_per_trade'],
        r['delta']['pnl_change_pct']))

# Save
out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_forex.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print()
print('Saved to:', out_path)
