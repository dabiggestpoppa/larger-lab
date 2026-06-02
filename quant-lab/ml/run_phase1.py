"""Run Phase 1 pipeline end-to-end."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / "phase1_data"))
from pipeline import run_tier_discovery, build_feature_matrix, ASSET_CONFIG
from pathlib import Path
import json

PARQUET_DIR = Path(__file__).parent / "data" / "parquet"
TIERS_DIR = Path(__file__).parent / "data" / "tiers"
FEATURES_DIR = Path(__file__).parent / "data" / "features"
TIERS_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# Build manifest from existing Parquet files
manifest = {}
for symbol, cfg in ASSET_CONFIG.items():
    p = PARQUET_DIR / f"{symbol}_M5.parquet"
    if p.exists():
        manifest[symbol] = {"status": "OK", "parquet_path": str(p)}

print(f"Found {len(manifest)} assets with Parquet files")

# Tier discovery
print("\n=== TIER DISCOVERY ===")
all_tiers = run_tier_discovery(manifest)
ok_count = len([v for v in all_tiers.values() if v.get("status") == "OK"])
print(f"\nTier discovery: {ok_count}/{len(all_tiers)} assets OK")

# Feature matrix
print("\n=== FEATURE MATRIX ===")
for symbol, tiers in all_tiers.items():
    if tiers.get("status") != "OK":
        continue
    meta = manifest.get(symbol, {})
    if meta.get("status") != "OK":
        continue
    try:
        parquet_path = Path(meta["parquet_path"])
        features_df = build_feature_matrix(parquet_path, symbol, tiers["tiers"])
        feature_path = FEATURES_DIR / f"{symbol}_features.parquet"
        features_df.to_parquet(feature_path)
        print(f"  [{symbol}] Features: {features_df.shape[0]} rows x {features_df.shape[1]} cols")
    except Exception as e:
        print(f"  [{symbol}] Error: {e}")

# Save manifest
with open(Path(__file__).parent / "data" / "phase1_manifest.json", "w") as f:
    json.dump({"tiers": all_tiers, "manifest": manifest}, f, indent=2, default=str)

print("\n=== PHASE 1 COMPLETE ===")
print(f"Parquet: {PARQUET_DIR}")
print(f"Tiers:   {TIERS_DIR}")
print(f"Features: {FEATURES_DIR}")
