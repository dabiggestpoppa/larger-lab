
import sys, os, json, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest')
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
