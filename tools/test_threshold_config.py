import json, os

# Simulate what DMR does
cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
print(f"Config path: {cfg_path}")
print(f"Exists: {os.path.exists(cfg_path)}")

with open(cfg_path) as f:
    cfg = json.load(f)

pair_thresholds = cfg.get('p90_thresholds', {})
print(f"Keys in p90_thresholds: {list(pair_thresholds.keys())}")

for sym in ["EURUSD.PRO", "USDCHF.PRO", "CHFJPY.PRO"]:
    thresholds = pair_thresholds.get(sym)
    if thresholds is None:
        # Try case-insensitive
        for k, v in pair_thresholds.items():
            if k.upper() == sym.upper():
                thresholds = v
                break
    print(f"{sym}: {thresholds}")
