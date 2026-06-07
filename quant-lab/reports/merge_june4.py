import json, os, sys
from datetime import datetime

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS

base_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Load ALL the June 4th individual sweep files
sweep_files = [
    'trigger_sweep_aud.json', 'trigger_sweep_cad.json', 'trigger_sweep_chf.json',
    'trigger_sweep_gbp.json', 'trigger_sweep_nzd.json', 'trigger_sweep_usd.json',
    'trigger_sweep_remaining_eur.json', 'trigger_sweep_crypto.json',
]

# Also load the max_accuracy as reference
max_acc = json.load(open(os.path.join(base_dir, 'trigger_sweep_max_accuracy.json')))

print("=== JUNE 4TH INDIVIDUAL SWEEP FILES ===")
all_june4 = {}
for f in sweep_files:
    path = os.path.join(base_dir, f)
    if os.path.exists(path):
        data = json.load(open(path))
        for pair, entries in data.items():
            if pair not in all_june4:
                all_june4[pair] = []
            if isinstance(entries, list):
                all_june4[pair].extend(entries)
            else:
                all_june4[pair].append(entries)
        print(f'{f:40s} | {len(data)} pairs')

print(f'\nTotal pairs from individual files: {len(all_june4)}')
print(f'Total pairs in max_accuracy: {len(max_acc)}')

# Compare: for each pair, do the individual files match max_accuracy?
print("\n=== COMPARING INDIVIDUAL vs MAX_ACCURACY ===")
mismatches = []
missing_in_individual = []
missing_in_maxacc = []

for pair in sorted(max_acc.keys()):
    if pair not in all_june4:
        missing_in_individual.append(pair)
        continue
    
    ma_entries = max_acc[pair] if isinstance(max_acc[pair], list) else [max_acc[pair]]
    ind_entries = all_june4[pair]
    
    # Compare trigger values
    ma_triggers = sorted(set(e['t1_trigger'] for e in ma_entries))
    ind_triggers = sorted(set(e['t1_trigger'] for e in ind_entries))
    
    if ma_triggers != ind_triggers:
        mismatches.append((pair, ma_triggers, ind_triggers))

for pair in sorted(all_june4.keys()):
    if pair not in max_acc:
        missing_in_maxacc.append(pair)

if mismatches:
    print(f"\nTrigger mismatches: {len(mismatches)}")
    for pair, ma_t, ind_t in mismatches[:5]:
        print(f"  {pair}: max_acc={ma_t[:3]}... | individual={ind_t[:3]}...")

if missing_in_individual:
    print(f"\nMissing from individual files: {missing_in_individual}")

if missing_in_maxacc:
    print(f"\nMissing from max_accuracy: {missing_in_maxacc}")

if not mismatches and not missing_in_individual and not missing_in_maxacc:
    print("\nAll pairs match between individual files and max_accuracy!")

# Now: what script generated the individual files?
# Let me check if there's a pattern in the data that tells me the sweep method
print("\n=== SWEEP METHOD ANALYSIS ===")
for pair in ['EURUSD', 'CHFJPY', 'EURJPY', 'GBPJPY']:
    entries = all_june4.get(pair, [])
    if entries:
        triggers = sorted(set(e['t1_trigger'] for e in entries))
        days = set(e.get('days') for e in entries)
        print(f"\n{pair}:")
        print(f"  Triggers: {triggers}")
        print(f"  Days: {sorted(days)}")
        if pair in ASSET_CONFIGS:
            cfg = ASSET_CONFIGS[pair]
            cfg_t1 = cfg['tiers']['T1']['trigger']
            print(f"  Config T1 trigger: {cfg_t1}")
            # Check if triggers are multiples of config trigger
            for t in triggers:
                ratio = t / cfg_t1 if cfg_t1 > 0 else 0
                print(f"    t1={t} -> ratio to config: {ratio:.3f}")
