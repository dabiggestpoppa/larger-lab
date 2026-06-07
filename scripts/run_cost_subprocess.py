"""Run cost analysis across all pairs — with per-pair timeout via subprocess."""
import sys, os, json, time, subprocess

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    return None

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

available = [(p, find_csv(p)) for p in all_pairs if find_csv(p)]
print('Available: %d of %d pairs' % (len(available), len(all_pairs)))

# Generate per-pair runner script
runner_script = '''
import sys, os, json, time
sys.path.insert(0, r'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\configs')
sys.path.insert(0, r'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\engines')
sys.path.insert(0, r'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\backtest')
os.environ['PYTHONIOENCODING'] = 'utf-8'

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

pair = sys.argv[1]
csv_path = sys.argv[2]

cfg = deepcopy(ASSET_CONFIGS.get(pair, {'pip_value': 0.0001}))
cfg['tiers'] = {
    'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
}
pip_value = cfg.get('pip_value', 0.0001)

try:
    bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
    bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
    result = bt.run(bars)
    analysis = run_cost_analysis(result.trades, pair, pip_value, lot_size=0.01)
    
    # Output as JSON to stdout
    print(json.dumps(analysis, default=str))
except Exception as e:
    print(json.dumps({'error': str(e)}))
'''

runner_path = r'C:\Users\wifik\Desktop\projects\larger-lab\scripts\_cost_runner.py'
with open(runner_path, 'w') as f:
    f.write(runner_script)

results = {}
errors = []
t_total = time.time()

for pair, csv_path in available:
    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, runner_path, pair, csv_path],
            capture_output=True, text=True, timeout=300,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        elapsed = time.time() - t0
        
        if result.returncode == 0 and result.stdout.strip():
            analysis = json.loads(result.stdout.strip())
            if 'error' in analysis:
                print('%-10s | ERROR: %s' % (pair, analysis['error'][:60]))
                errors.append(pair)
            else:
                results[pair] = analysis
                print('%-10s | %5d tr | raw wr=%5.1f%% pf=%4.1f | adj wr=%5.1f%% pf=%4.1f | cost=%4.2fp | pnl=%+5.1f%% | %.1fs' % (
                    pair, analysis['raw']['trades'],
                    analysis['raw']['wr'], analysis['raw']['pf'],
                    analysis['adjusted']['wr'], analysis['adjusted']['pf'],
                    analysis['costs']['total_cost_pips_per_trade'],
                    analysis['delta']['pnl_change_pct'], elapsed))
        else:
            err_msg = result.stderr[:100] if result.stderr else 'no output'
            print('%-10s | FAIL: %s' % (pair, err_msg[:60]))
            errors.append(pair)
    except subprocess.TimeoutExpired:
        print('%-10s | TIMEOUT (>300s)' % pair)
        errors.append(pair)
    except Exception as e:
        print('%-10s | ERROR: %s' % (pair, str(e)[:60]))
        errors.append(pair)

total_elapsed = time.time() - t_total
print()
print('Completed: %d pairs in %.1fs, %d errors' % (len(results), total_elapsed, len(errors)))
if errors:
    print('Errors:', errors)

# Save
out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_all.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)
print('Saved to:', out_path)
