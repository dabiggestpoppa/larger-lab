"""
Debug: Why do some assets have fewer trades?
Compare tier thresholds across asset classes.
"""
import sys, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

import importlib.util
spec = importlib.util.spec_from_file_location("asset_configs", os.path.join(os.path.dirname(__file__), "..", "quant-lab", "configs", "asset_configs.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ASSET_CONFIGS = mod.ASSET_CONFIGS

print("=" * 80)
print("TRIGGER THRESHOLD COMPARISON (in price units)")
print("=" * 80)

for key, cfg in sorted(ASSET_CONFIGS.items()):
    pip = cfg["pip_value"]
    tiers = cfg.get("tiers", {})
    t1 = tiers.get("T1", {})
    t3 = tiers.get("T3", {})
    
    trigger_t1 = t1.get("trigger", 0)
    trigger_t3 = t3.get("trigger", 0)
    au_t1 = t1.get("au", 0)
    ar_max_t1 = t1.get("ar_max", 0)
    
    print(f"{key:12} pip={pip:>8} | T1 trigger={trigger_t1:>8} | T3 trigger={trigger_t3:>8} | T1 AU={au_t1:>8} | T1 ARmax={ar_max_t1:>8}")

print()
print("=" * 80)
print("ANALYSIS: Assets with fewer trades likely have very high trigger thresholds")
print("relative to their typical session volatility.")
print("=" * 80)

# Now let's also check: how many sessions actually get "NO_GO"?
# That would happen if Asian Range > T3 AR_max
print()
print("NO-GO THRESHOLD (Asian Range > T3 AR_max):")
for key, cfg in sorted(ASSET_CONFIGS.items()):
    t3 = cfg.get("tiers", {}).get("T3", {})
    ar_max = t3.get("ar_max", 999)
    pip = cfg["pip_value"]
    print(f"{key:12} T3 AR_max={ar_max:>8} (in pips)")
