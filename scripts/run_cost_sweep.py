"""Run cost analysis across all available pairs with flexible CSV naming."""
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
from apply_costs import run_cost_analysis, COST_TABLE
from copy import deepcopy

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

def find_csv(pair):
    """Find CSV file for a pair, handling various naming conventions."""
    # Try exact match first
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    # Try lowercase
    for suffix in ['_m5.csv', '_PRO_m5.csv']:
        path = os.path.join(data_dir, pair.lower() + suffix)
        if os.path.exists(path):
            return path
    return None

# All 36 pairs
all_pairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
    'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
    'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
    'NZDJPY', 'NZDCHF', 'NZDCAD',
    'CADJPY', 'CADCHF', 'CHFJPY',
    'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD',
    'US500', 'DE30', 'FR40', 'HK50',
]

# Filter to available
available = []
for pair in all_pairs:
    csv_path = find_csv(pair)
    if csv_path:
        available.append((pair, csv_path))

print('Available pairs: %d of %d' % (len(available), len(all_pairs)))
print()

results = {}
t_total = time.time()

for pair, csv_path in available:
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
        print('%-10s | %5d tr | raw wr=%.1f%% pf=%.1f | adj wr=%.1f%% pf=%.1f | cost/tr=%.2fp | pnl_cost=%+.1f%% | %.1fs' % (
            pair,
            analysis['raw']['trades'],
            analysis['raw']['wr'], analysis['raw']['pf'],
            analysis['adjusted']['wr'], analysis['adjusted']['pf'],
            analysis['costs']['total_cost_pips_per_trade'],
            analysis['delta']['pnl_change_pct'],
            elapsed
        ))
    except Exception as e:
        elapsed = time.time() - t0
        print('%-10s | ERROR: %s (%.1fs)' % (pair, str(e)[:60], elapsed))

total_elapsed = time.time() - t_total
print()
print('Total time: %.1fs' % total_elapsed)

# Save
out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_all.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print('Saved to:', out_path)
