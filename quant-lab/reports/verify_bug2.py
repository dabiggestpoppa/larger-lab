import json, sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts')

from asset_configs import ASSET_CONFIGS
from sweep_forex_full import build_scaled_config

pair = 'CHFJPY'
raw = ASSET_CONFIGS[pair]
scaled = build_scaled_config(pair, 1.0)

print("=== CHFJPY: RAW vs SCALED at mult=1.0 ===")
for tier in ['T1', 'T2', 'T3']:
    r = raw['tiers'][tier]
    s = scaled['tiers'][tier]
    print(f"\n{tier}:")
    print(f"  RAW:    ar_max={r['ar_max']}, au={r['au']}, trigger={r['trigger']}")
    print(f"  SCALED: ar_max={s['ar_max']}, au={s['au']}, trigger={s['trigger']}")
    for key in ['ar_max', 'au', 'trigger']:
        if r[key] != s[key]:
            print(f"  *** MISMATCH: {key}: {r[key]} vs {s[key]} ***")

print("\n=== OTHER CONFIG FIELDS ===")
print(f"RAW keys: {list(raw.keys())}")
print(f"SCALED keys: {list(scaled.keys())}")
for key in raw.keys():
    if key != 'tiers':
        if raw[key] != scaled[key]:
            print(f"  *** {key}: RAW={raw[key]} vs SCALED={scaled[key]} ***")

print("\n=== PIP VALUE ===")
print(f"CHFJPY pip_value = {raw.get('pip_value', 'NOT SET')}")
print(f"scaled pip_value = {scaled.get('pip_value', 'NOT SET')}")

# Check EURUSD too
pair2 = 'EURUSD'
raw2 = ASSET_CONFIGS[pair2]
scaled2 = build_scaled_config(pair2, 1.0)
print(f"\n=== EURUSD: RAW vs SCALED at mult=1.0 ===")
for tier in ['T1', 'T2', 'T3']:
    r = raw2['tiers'][tier]
    s = scaled2['tiers'][tier]
    match = "OK" if r == s else "MISMATCH"
    print(f"  {tier}: RAW={r} | SCALED={s} | {match}")
