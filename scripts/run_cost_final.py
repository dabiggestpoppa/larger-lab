"""Full cost analysis — all 28 forex pairs in one process."""
import sys, os, json, time

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest')

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
t_total = time.time()

for pair in forex_pairs:
    csv_path = find_csv(pair)
    if not csv_path:
        print('%-10s | NO CSV' % pair, flush=True)
        continue
    
    t0 = time.time()
    try:
        pip_value = ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001)
        bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
        
        cfg = deepcopy(ASSET_CONFIGS.get(pair, {'pip_value': 0.0001}))
        cfg['tiers'] = {
            'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
            'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
            'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
        }
        
        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
        result = bt.run(bars)
        analysis = run_cost_analysis(result.trades, pair, pip_value, lot_size=0.01)
        results[pair] = analysis
        
        elapsed = time.time() - t0
        print('%-10s | %5d tr | r_wr=%5.1f%% r_pf=%4.1f | a_wr=%5.1f%% a_pf=%4.1f | c=%4.2fp | pnl=%+5.1f%% | %.1fs' % (
            pair, analysis['raw']['trades'],
            analysis['raw']['wr'], analysis['raw']['pf'],
            analysis['adjusted']['wr'], analysis['adjusted']['pf'],
            analysis['costs']['total_cost_pips_per_trade'],
            analysis['delta']['pnl_change_pct'], elapsed), flush=True)
    except Exception as e:
        elapsed = time.time() - t0
        print('%-10s | ERROR: %s (%.1fs)' % (pair, str(e)[:60], elapsed), flush=True)
        errors.append(pair)

total_elapsed = time.time() - t_total
print()
print('Completed: %d pairs in %.1fs, %d errors' % (len(results), total_elapsed, len(errors)), flush=True)

out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_forex.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print('Saved to:', out_path, flush=True)
