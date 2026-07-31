import sys, json
from pathlib import Path

QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
sys.path.insert(0, str(QUANT_LAB / "configs"))
from asset_configs import ASSET_CONFIGS

MC_DIR = QUANT_LAB / "reports" / "per-asset"

print("Assets in ASSET_CONFIGS:")
for sym in sorted(ASSET_CONFIGS.keys()):
    mc_file = MC_DIR / (sym + "_mc_results.json")
    has_mc = mc_file.exists()
    d = json.load(open(mc_file)) if has_mc else {}
    pnls = d.get("per_trade_pnl", [])
    print(f"  {sym:10s}: MC={has_mc} pnls={len(pnls)}")
