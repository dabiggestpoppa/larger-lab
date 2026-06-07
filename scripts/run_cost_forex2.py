"""Run cost analysis — one pair at a time, skip slow ones."""
import sys, os, json, time, signal
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

forex_pairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
    'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
    'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
    'NZDJPY', 'NZDCHF', 'NZDCAD',
    'CADJPY', 'CADCHF', 'CHFJPY',
]

results = {}
errors = []

for pair in forex_pairs:
    csv_path = find_csv(pair)
    if not csv_path:
        continue
    
    # Skip if file too large (>20MB)
    fsize = os.path.getsize(csv_path) / 1024 / 1024
    if fsize > 20:
        print('%-10s | SKIP (%.1f MB too large)' % (pair, fsize))
        continue
    
    t0 = time.time()
    try:
        bars, _ = load_m5_csv(csv_path, pip_size=ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001))
        load_t = time.time() - t0
        
        cfg = deepcopy(ASSET_CONFIGS.get(pair, {'pip_value': 0.0001}))
        cfg['tiers'] = {
            'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
            'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
            'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
        }
        pip_value = cfg.get('pip_value', 0.0001)
        
        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
        result = bt.run(bars)
        analysis = run_cost_analysis(result.trades, pair, pip_value, lot_size=0.01)
        results[pair] = analysis
        
        total_t = time.time() - t0
        print('%-10s | %5d tr | raw wr=%5.1f%% pf=%4.1f | adj wr=%5.1f%% pf=%4.1f | cost=%4.2fp | pnl=%+5.1f%% | load=%.1fs run=%.1fs' % (
            pair, analysis['raw']['trades'],
            analysis['raw']['wr'], analysis['raw']['pf'],
            analysis['adjusted']['wr'], analysis['adjusted']['pf'],
            analysis['costs']['total_cost_pips_per_trade'],
            analysis['delta']['pnl_change_pct'], load_t, total_t))
    except Exception as e:
        print('%-10s | ERROR: %s' % (pair, str(e)[:60]))
        errors.append(pair)

print()
print('Completed: %d pairs, %d errors' % (len(results), len(errors)))
if errors:
    print('Errors:', errors)

# Save
out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_forex.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print('Saved to:', out_path)
