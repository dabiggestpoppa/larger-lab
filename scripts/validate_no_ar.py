"""Validate ar_max=999 across multiple pairs against sweep baseline."""
import sys, time, json, os
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

# Load sweep baseline
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    sweep = json.load(f)

# Check top pairs from sweep
data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

print('%-12s | %-8s %-8s | %-8s %-8s | %-8s %-8s | %s' % (
    'Pair', 'MyTr', 'BaseTr', 'MyWR', 'BaseWR', 'MyPF', 'BasePF', 'Verdict'))
print('-' * 100)

for pair in sorted(sweep.keys())[:15]:
    entries = sweep[pair]
    if not entries:
        continue
    
    # Find the t1=12 entry in baseline
    base_entry = None
    for e in entries:
        if abs(e['t1_trigger'] - 12.0) < 0.1:
            base_entry = e
            break
    
    if base_entry is None:
        continue
    
    csv_path = os.path.join(data_dir, '%s_M5.csv' % pair)
    if not os.path.exists(csv_path):
        continue
    
    cfg = deepcopy(ASSET_CONFIGS.get(pair, {
        'pip_value': 0.0001,
        'tiers': {'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
                  'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
                  'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0}},
    }))
    cfg['tiers'] = {
        'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
    }
    
    pip_value = ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001)
    try:
        bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
        r = bt.run(bars)
        
        delta_pct = (r.total_trades - base_entry['trades']) / base_entry['trades'] * 100
        
        if abs(delta_pct) <= 5:
            verdict = 'MATCH'
        elif abs(delta_pct) <= 15:
            verdict = 'CLOSE'
        else:
            verdict = 'OFF %.1f%%' % delta_pct
        
        print('%-12s | %-8d %-8d | %-8.1f %-8.1f | %-8.2f %-8.2f | %s' % (
            pair, r.total_trades, base_entry['trades'],
            r.win_rate, base_entry['wr'],
            r.profit_factor, base_entry['pf'],
            verdict))
    except Exception as e:
        print('%-12s | ERROR: %s' % (pair, str(e)[:50]))
