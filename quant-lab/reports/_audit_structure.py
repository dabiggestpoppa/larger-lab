import json

# Load the baseline (June 4)
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    baseline = json.load(f)

# Load the new sweep (June 7)
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json') as f:
    new_sweep = json.load(f)

# Inspect structure
print("=== BASELINE (max_accuracy) ===")
print("Type:", type(baseline).__name__)
if isinstance(baseline, dict):
    print("Top keys:", list(baseline.keys())[:15])
elif isinstance(baseline, list):
    print("Length:", len(baseline))
    if baseline:
        print("First entry keys:", list(baseline[0].keys())[:15])
        print("First entry:", json.dumps(baseline[0], indent=2)[:500])

print("\n=== NEW SWEEP (forex_full) ===")
print("Type:", type(new_sweep).__name__)
if isinstance(new_sweep, dict):
    print("Top keys:", list(new_sweep.keys())[:15])
elif isinstance(new_sweep, list):
    print("Length:", len(new_sweep))
    if new_sweep:
        print("First entry keys:", list(new_sweep[0].keys())[:15])
        print("First entry:", json.dumps(new_sweep[0], indent=2)[:500])
