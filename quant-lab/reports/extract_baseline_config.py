import json

# Load the baseline that WORKS
base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))

print("=== JUNE 4TH BASELINE — ALL PAIRS ===")
print(f"Total pairs: {len(base)}")
print()

# Show entry counts and day counts per pair
for pair in sorted(base.keys()):
    entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    days = set(e.get('days') for e in entries)
    triggers = sorted(set(e.get('t1_trigger') for e in entries))
    max_trades = max(e['trades'] for e in entries)
    max_wr = max(e['wr'] for e in entries)
    print(f"{pair:10s} | entries={len(entries):2d} | days={sorted(days)} | triggers={triggers[:3]}... | max_trades={max_trades:5d} | max_wr={max_wr:.1f}%")

# Now extract the EXACT config for the key pairs
# The baseline used ASSET_CONFIGS from June 4th
# Let me check what the current ASSET_CONFIGS has vs what the baseline results imply

import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

print("\n=== CURRENT ASSET_CONFIGS vs BASELINE RESULTS ===")
print("\nFor each pair, the baseline t1_trigger should match ASSET_CONFIGS T1 trigger:")
print(f"{'Pair':10s} | {'Baseline t1':>11s} | {'Config T1 trigger':>17s} | {'Match?':>6s}")
print("-" * 60)

mismatches = []
for pair in sorted(base.keys()):
    entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    # Get the lowest trigger (FLOOR) entry
    floor_entry = min(entries, key=lambda e: e['t1_trigger'])
    baseline_t1 = floor_entry['t1_trigger']
    
    if pair in ASSET_CONFIGS:
        config_t1 = ASSET_CONFIGS[pair]['tiers']['T1']['trigger']
        match = "YES" if abs(baseline_t1 - config_t1) < 0.5 else "NO"
        if match == "NO":
            mismatches.append((pair, baseline_t1, config_t1))
    else:
        config_t1 = "N/A"
        match = "N/A"
    
    print(f"{pair:10s} | {baseline_t1:11.1f} | {config_t1:17} | {match:>6s}")

if mismatches:
    print(f"\n*** MISMATCHES: {len(mismatches)} pairs ***")
    for pair, base_t1, cfg_t1 in mismatches:
        print(f"  {pair}: baseline={base_t1}, config={cfg_t1}")
else:
    print("\nAll baseline triggers match current ASSET_CONFIGS")

# Now check: what AR gate values were used?
# The baseline results show the AR gate was ACTIVE (ar_max=20/30/45 in old engine)
# Let me check the current ASSET_CONFIGS ar_max values
print("\n=== AR MAX VALUES IN CURRENT CONFIG ===")
for pair in sorted(base.keys())[:10]:
    if pair in ASSET_CONFIGS:
        cfg = ASSET_CONFIGS[pair]
        t1_ar = cfg['tiers']['T1']['ar_max']
        t2_ar = cfg['tiers']['T2']['ar_max']
        t3_ar = cfg['tiers']['T3']['ar_max']
        print(f"{pair:10s} | T1 ar_max={t1_ar:6.1f} | T2 ar_max={t2_ar:6.1f} | T3 ar_max={t3_ar:6.1f}")
