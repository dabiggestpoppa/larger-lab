import json

# Baseline file
base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))
print(f"BASELINE: {len(base)} pairs")

# New sweep
new = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json'))
print(f"NEW SWEEP: {len(new)} pairs")

# Check structure of baseline for one pair
sample_pair = 'EURUSD'
if sample_pair in base:
    s = base[sample_pair]
    print(f"\nEURUSD baseline type: {type(s).__name__}")
    if isinstance(s, list):
        print(f"  Length: {len(s)}")
        if s:
            print(f"  First entry: {s[0]}")
    elif isinstance(s, dict):
        print(f"  Keys: {list(s.keys())[:5]}")

# Check structure of new for one pair
sample_pair2 = 'EURJPY'
if sample_pair2 in new:
    s2 = new[sample_pair2]
    print(f"\nEURJPY new type: {type(s2).__name__}")
    if isinstance(s2, list):
        print(f"  Length: {len(s2)}")
        if s2:
            print(f"  First entry: {s2[0]}")
    elif isinstance(s2, dict):
        print(f"  Keys: {list(s2.keys())[:5]}")

# Compare overlapping pairs at similar triggers
overlap = set(base.keys()) & set(new.keys())
print(f"\n--- OVERLAP: {len(overlap)} pairs ---")

for pair in sorted(overlap):
    b_entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    n_entries = new[pair] if isinstance(new[pair], list) else [new[pair]]
    
    print(f"\n{pair}:")
    print(f"  Baseline entries: {len(b_entries)}")
    print(f"  New entries: {len(n_entries)}")
    
    # Show first few from each
    if b_entries:
        b0 = b_entries[0]
        print(f"  Baseline[0]: {b0}")
    if n_entries:
        n0 = n_entries[0]
        print(f"  New[0]: {n0}")
