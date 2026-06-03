"""Get all assets and their valid engine assignments from asset_configs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))
from asset_configs import ASSET_CONFIGS

print(f"Total assets in ASSET_CONFIGS: {len(ASSET_CONFIGS)}")
print()
for sym, cfg in sorted(ASSET_CONFIGS.items()):
    engines = []
    # Check if P90 config exists
    if cfg.get("p90_threshold") is not None:
        engines.append("P90")
    # ST config — all assets have tiers, but check if it's a valid ST
    if cfg.get("tiers"):
        engines.append("ST")
    print(f"{sym:10s}: engines={engines} | pip={cfg['pip_value']} | k={cfg.get('k_factor','N/A')} | thresholds={cfg.get('p90_threshold','N/A')} | fixed_tp={cfg.get('fixed_tp','N/A')}")

# Check what assets have backtested data
import glob
data_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")
mc_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset")
data_files = set(f.stem.replace("_M5", "") for f in data_dir.glob("*_M5.csv"))
mc_files = set(f.stem.replace("_mc_results", "") for f in mc_dir.glob("*_mc_results.json"))

print(f"\nData files: {len(data_files)} assets")
print(f"MC results: {len(mc_files)} assets")
print(f"\nAssets WITH MC results: {sorted(mc_files)}")
print(f"Assets WITHOUT MC results: {sorted(data_files - mc_files)}")
print(f"Assets with data but no config: {sorted(data_files - set(ASSET_CONFIGS.keys()))}")
