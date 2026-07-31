"""Cost analysis using PER-PAIR native configs from asset_configs.py.
Each pair gets its own AU, trigger — NEVER universal values.
BIBLE Rule #1: AU is ALWAYS per-pair, never universal."""
import sys, os, json, time

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from apply_costs import run_cost_analysis

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    return None

# All pairs that have BOTH a config entry AND a CSV file
all_pairs = sorted([p for p in ASSET_CONFIGS.keys() if find_csv(p)])
print('Pairs with per-pair config + CSV: %d' % len(all_pairs))
print()

results = {}
errors = []

for pair in all_pairs:
    csv_path = find_csv(pair)
    cfg = ASSET_CONFIGS[pair]
    pip_value = cfg.get('pip_value', 0.0001)
    tiers = cfg.get('tiers', {})
    
    # ── USE PER-PAIR NATIVE CONFIG ──
    # Each pair has its own AU, trigger, ar_max — NEVER universal values
    # BIBLE Rule #1: AU is ALWAYS per-pair, never universal
    native_cfg = {
        'T1': {'ar_max': tiers['T1']['ar_max'], 'au': tiers['T1']['au'], 'trigger': tiers['T1']['trigger']},
        'T2': {'ar_max': tiers['T2']['ar_max'], 'au': tiers['T2']['au'], 'trigger': tiers['T2']['trigger']},
        'T3': {'ar_max': tiers['T3']['ar_max'], 'au': tiers['T3']['au'], 'trigger': tiers['T3']['trigger']},
    }
    
    run_cfg = dict(cfg)
    run_cfg['tiers'] = native_cfg
    
    t0 = time.time()
    try:
        bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=run_cfg)
        result = bt.run(bars)
        analysis = run_cost_analysis(result.trades, pair, pip_value, lot_size=0.01)
        results[pair] = analysis
        
        elapsed = time.time() - t0
        t1 = tiers['T1']
        print('%-10s | au=%-5s trig=%-5s | %5d tr | r_wr=%5.1f%% r_pf=%4.1f | a_wr=%5.1f%% a_pf=%4.1f | c=%4.2fp | pnl=%+5.1f%% | %.1fs' % (
            pair, t1['au'], t1['trigger'],
            analysis['raw']['trades'],
            analysis['raw']['wr'], analysis['raw']['pf'],
            analysis['adjusted']['wr'], analysis['adjusted']['pf'],
            analysis['costs']['total_cost_pips_per_trade'],
            analysis['delta']['pnl_change_pct'], elapsed), flush=True)
    except Exception as e:
        elapsed = time.time() - t0
        print('%-10s | ERROR: %s (%.1fs)' % (pair, str(e)[:60], elapsed), flush=True)
        errors.append(pair)

print()
print('Completed: %d pairs, %d errors' % (len(results), len(errors)), flush=True)

out_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print('Saved to:', out_path, flush=True)
