"""
FULL TRIGGER SWEEP — All 36 pairs, FLOOR/CEILING/KNEE.
Uses FIXED engine (trigger stays at T1 value across loops).
Sweeps trigger multiplier from 0.3x to 3.0x of base T1 trigger.
"""
import sys, json, os, time
from pathlib import Path

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

DATA_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

# All pairs
ALL_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "NZDJPY", "AUDNZD",
    "AUDCAD", "AUDCHF", "CADJPY", "CHFJPY", "CADCHF", "EURNZD", "EURAUD",
    "EURCAD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", "NZDCAD", "NZDCHF",
    "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD",
    "US500", "DE30", "FR40", "HK50",
]

# Trigger multipliers for sweep
MULTIPLIERS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0]

# Pip values
PIP_VALUES = {
    "BTCUSD": 1.0, "ETHUSD": 1.0,
    "XAUUSD": 0.10, "XAGUSD": 0.10,
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
}

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        p = os.path.join(DATA_DIR, pair + suffix)
        if os.path.exists(p):
            return p
    return None

results = {}
errors = []

for pair in ALL_PAIRS:
    csv_path = find_csv(pair)
    if not csv_path:
        print('%-10s | NO CSV' % pair, flush=True)
        errors.append(pair)
        continue
    
    cfg_base = ASSET_CONFIGS.get(pair, {})
    pip_val = PIP_VALUES.get(pair, 0.01 if 'JPY' in pair else 0.0001)
    
    pair_results = []
    
    for mult in MULTIPLIERS:
        # Scale ONLY the trigger, keep AU and ar_max at base values
        # This is the correct FLOOR/CEILING/KNEE sweep
        t1 = cfg_base.get('tiers', {}).get('T1', {})
        t2 = cfg_base.get('tiers', {}).get('T2', {})
        t3 = cfg_base.get('tiers', {}).get('T3', {})
        
        scaled_cfg = {
            'T1': {'ar_max': 999.0, 'au': t1.get('au', 10.0), 'trigger': round(t1.get('trigger', 12.0) * mult, 1)},
            'T2': {'ar_max': 999.0, 'au': t2.get('au', 12.0), 'trigger': round(t2.get('trigger', 15.0) * mult, 1)},
            'T3': {'ar_max': 999.0, 'au': t3.get('au', 15.0), 'trigger': round(t3.get('trigger', 19.0) * mult, 1)},
        }
        
        run_cfg = dict(cfg_base)
        run_cfg['tiers'] = scaled_cfg
        
        try:
            bars, _ = load_m5_csv(csv_path, pip_size=pip_val)
            bt = SymmetryTrapBacktest(pip_size=pip_val, symbol=pair, config=run_cfg)
            result = bt.run(bars)
            
            pair_results.append({
                'mult': mult,
                't1_trigger': scaled_cfg['T1']['trigger'],
                'trades': result.total_trades,
                'wr': round(result.win_rate, 1),
                'pf': round(result.profit_factor, 2),
                'pnl_pips': round(result.total_pnl_pips, 1),
                'max_dd': round(result.max_drawdown_pips, 1),
                'tr_per_day': round(result.total_trades / max(result.data_days, 1), 3),
            })
        except Exception as e:
            print('  ERROR mult=%.1f: %s' % (mult, str(e)[:50]), flush=True)
    
    results[pair] = pair_results
    
    # Print summary for this pair
    if pair_results:
        floor = max(pair_results, key=lambda x: x['trades'])
        ceiling = max(pair_results, key=lambda x: x['wr'])
        # Knee = best PF
        knee = max(pair_results, key=lambda x: x['pf'])
        print('%-10s | FLOOR: t1=%-5s %5d tr %5.1f%% %5.1f | KNEE: t1=%-5s %5d tr %5.1f%% %5.1f | CEIL: t1=%-5s %5d tr %5.1f%% %5.1f' % (
            pair,
            floor['t1_trigger'], floor['trades'], floor['wr'], floor['pf'],
            knee['t1_trigger'], knee['trades'], knee['wr'], knee['pf'],
            ceiling['t1_trigger'], ceiling['trades'], ceiling['wr'], ceiling['pf'],
        ), flush=True)
    else:
        print('%-10s | NO RESULTS' % pair, flush=True)

print()
print('Completed: %d pairs, %d errors' % (len(results), len(errors)))

# Save
out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_floor_ceiling_knee.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)
print('Saved to:', out_path)
