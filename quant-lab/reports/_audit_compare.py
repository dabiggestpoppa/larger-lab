import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    baseline = json.load(f)

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json') as f:
    new_sweep = json.load(f)

# Show EURUSD from baseline
print("=== EURUSD BASELINE (max_accuracy) ===")
eurusd = baseline.get('EURUSD', {})
print("Type:", type(eurusd).__name__)
if isinstance(eurusd, dict):
    print("Keys:", list(eurusd.keys())[:20])
    # Print all entries
    for k, v in eurusd.items():
        if isinstance(v, dict):
            print(f"  {k}: trades={v.get('trades','?')}, wr={v.get('wr','?')}, pf={v.get('pf','?')}, pnl={v.get('pnl','?')}")
        else:
            print(f"  {k}: {v}")
elif isinstance(eurusd, list):
    print("Entries:", len(eurusd))
    for e in eurusd[:5]:
        print(f"  {json.dumps(e, indent=2)[:300]}")

# Show what's in new_sweep for a JPY pair
print("\n=== EURJPY NEW SWEEP (forex_full) ===")
ej_new = new_sweep.get('EURJPY', {})
print("Type:", type(ej_new).__name__)
if isinstance(ej_new, dict):
    print("Keys:", list(ej_new.keys())[:20])
    for k, v in list(ej_new.items())[:10]:
        if isinstance(v, dict):
            print(f"  {k}: trades={v.get('trades','?')}, wr={v.get('wr','?')}, pf={v.get('pf','?')}, pnl={v.get('pnl','?')}")
        else:
            print(f"  {k}: {v}")
elif isinstance(ej_new, list):
    print("Entries:", len(ej_new))
    for e in ej_new[:5]:
        print(f"  {json.dumps(e, indent=2)[:300]}")

# Show EURJPY from baseline
print("\n=== EURJPY BASELINE (max_accuracy) ===")
ej_base = baseline.get('EURJPY', {})
print("Type:", type(ej_base).__name__)
if isinstance(ej_base, dict):
    print("Keys:", list(ej_base.keys())[:20])
    for k, v in list(ej_base.items())[:10]:
        if isinstance(v, dict):
            print(f"  {k}: trades={v.get('trades','?')}, wr={v.get('wr','?')}, pf={v.get('pf','?')}, pnl={v.get('pnl','?')}")
        else:
            print(f"  {k}: {v}")
