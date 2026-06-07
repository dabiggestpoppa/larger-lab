"""
VALIDATION SCRIPT — Re-run June 4th max accuracy sweep with current engine
Uses EXACT same config that produced the baseline results.
Compares output to trigger_sweep_max_accuracy.json to find discrepancies.
"""
import sys, json, os, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

REPORTS_DIR = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports')
DATA_DIR = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data')

# Load baseline for comparison
baseline = json.load(open(REPORTS_DIR / 'trigger_sweep_max_accuracy.json'))

# Focus on key pairs first
TEST_PAIRS = ['EURUSD', 'CHFJPY', 'GBPJPY', 'USDJPY', 'EURJPY']

# For each pair, get the baseline triggers and re-run
results = {}
discrepancies = []

for pair in TEST_PAIRS:
    if pair not in baseline:
        print(f"SKIP: {pair} not in baseline")
        continue
    
    base_entries = baseline[pair] if isinstance(baseline[pair], list) else [baseline[pair]]
    base_triggers = sorted(set(e['t1_trigger'] for e in base_entries))
    
    print(f"\n{'='*60}")
    print(f"{pair}: {len(base_triggers)} baseline triggers")
    print(f"  Triggers: {base_triggers}")
    
    # Load CSV
    csv_path = DATA_DIR / f"{pair}_M5.csv"
    if not csv_path.exists():
        candidates = sorted(DATA_DIR.glob(f"{pair}*.csv"))
        if candidates:
            csv_path = candidates[0]
        else:
            print(f"  ERROR: No CSV for {pair}")
            continue
    
    cfg = ASSET_CONFIGS[pair]
    pip_value = cfg.get('pip_value', 0.0001)
    
    # For JPY pairs, pip_value should be 0.01
    if 'JPY' in pair:
        pip_value = 0.01
    
    bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
    if not bars:
        print(f"  ERROR: No bars loaded")
        continue
    
    n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
    print(f"  Bars: {len(bars)}, Days: {n_days}, Pip: {pip_value}")
    print(f"  Config T1 trigger: {cfg['tiers']['T1']['trigger']}")
    
    pair_results = []
    
    # Re-run at each baseline trigger
    for target_trigger in base_triggers:
        # Build a config with this specific trigger
        test_cfg = cfg.copy()
        test_cfg['tiers'] = {}
        for tier_name in ['T1', 'T2', 'T3']:
            orig_tier = cfg['tiers'][tier_name]
            # Scale all tiers proportionally to match the target T1 trigger
            scale = target_trigger / cfg['tiers']['T1']['trigger'] if cfg['tiers']['T1']['trigger'] > 0 else 1.0
            test_cfg['tiers'][tier_name] = {
                'ar_max': round(orig_tier['ar_max'] * scale, 2),
                'au': round(orig_tier['au'] * scale, 2),
                'trigger': round(orig_tier['trigger'] * scale, 2),
            }
        
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            symbol=pair,
            config=test_cfg,
        )
        result = bt.run(bars)
        
        # Find baseline entry for this trigger
        base_entry = None
        for e in base_entries:
            if abs(e['t1_trigger'] - target_trigger) < 0.1:
                base_entry = e
                break
        
        new_trades = result.total_trades
        base_trades = base_entry['trades'] if base_entry else 0
        base_wr = base_entry['wr'] if base_entry else 0
        base_pf = base_entry['pf'] if base_entry else 0
        
        delta_pct = ((new_trades - base_trades) / base_trades * 100) if base_trades > 0 else 0
        
        entry = {
            'trigger': target_trigger,
            'baseline_trades': base_trades,
            'new_trades': new_trades,
            'delta_pct': round(delta_pct, 1),
            'baseline_wr': base_wr,
            'new_wr': round(result.win_rate, 1),
            'baseline_pf': base_pf,
            'new_pf': round(result.profit_factor, 2) if result.profit_factor != float('inf') else 999,
        }
        pair_results.append(entry)
        
        flag = " *** MISMATCH ***" if abs(delta_pct) > 15 else ""
        print(f"  t1={target_trigger:6.1f} | base={base_trades:5d} wr={base_wr:.1f}% pf={base_pf:.1f} | new={new_trades:5d} wr={result.win_rate:.1f}% pf={result.profit_factor:.1f} | delta={delta_pct:+.1f}%{flag}")
        
        if abs(delta_pct) > 15:
            discrepancies.append({
                'pair': pair,
                'trigger': target_trigger,
                'baseline_trades': base_trades,
                'new_trades': new_trades,
                'delta_pct': delta_pct,
            })
    
    results[pair] = pair_results

# Summary
print(f"\n{'='*60}")
print("VALIDATION SUMMARY")
print(f"{'='*60}")
print(f"Total pairs tested: {len(results)}")
print(f"Total trigger points: {sum(len(v) for v in results.values())}")
print(f"Discrepancies (>15% trade count diff): {len(discrepancies)}")

if discrepancies:
    print(f"\nDISCREPANCIES:")
    for d in discrepancies:
        print(f"  {d['pair']:10s} t1={d['trigger']:6.1f} | base={d['baseline_trades']:5d} | new={d['new_trades']:5d} | delta={d['delta_pct']:+.1f}%")
else:
    print("\nAll results match within 15% tolerance!")

# Save results
output_path = REPORTS_DIR / 'validation_results.json'
with open(output_path, 'w') as f:
    json.dump({'results': results, 'discrepancies': discrepancies}, f, indent=2, default=str)
print(f"\nResults saved to: {output_path}")
