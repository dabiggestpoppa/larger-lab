import json, sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
from asset_configs import ASSET_CONFIGS

# Check what fields EURUSD config has
cfg = ASSET_CONFIGS["EURUSD"]
print("EURUSD config keys:", list(cfg.keys()))
print("EURUSD tiers:", json.dumps(cfg["tiers"], indent=2))
print("EURUSD full config:")
for k, v in cfg.items():
    if k != "tiers":
        print("  %s = %s" % (k, v))

# Now check what build_scaled_config produces
base = cfg.copy()
mult = 1.0
tiers = {}
for tn in ["T1", "T2", "T3"]:
    t = base["tiers"][tn]
    tiers[tn] = {
        "ar_max": round(t["ar_max"] * mult, 1),
        "au": round(t["au"] * mult, 1),
        "trigger": round(t["trigger"] * mult, 1),
    }
base["tiers"] = tiers

print("\nScaled config keys:", list(base.keys()))
print("Scaled config non-tier fields:")
for k, v in base.items():
    if k != "tiers":
        print("  %s = %s (type=%s)" % (k, v, type(v).__name__))
