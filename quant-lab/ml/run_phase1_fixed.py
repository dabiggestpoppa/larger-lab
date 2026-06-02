"""Re-run Phase 1 pipeline with fixed Asian session grouping."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "phase1_data"))
from pipeline import extract_asian_ranges, discover_tiers, build_feature_matrix, ASSET_CONFIG

PARQUET_DIR = Path(__file__).parent / "data" / "parquet"
TIERS_DIR = Path(__file__).parent / "data" / "tiers"
FEATURES_DIR = Path(__file__).parent / "data" / "features"
TIERS_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# Build manifest from existing Parquet files
manifest = {}
for symbol, cfg in ASSET_CONFIG.items():
    csv_name = cfg.get("csv")
    if csv_name is None:
        continue
    p = PARQUET_DIR / f"{symbol}_M5.parquet"
    if p.exists():
        manifest[symbol] = {"status": "OK", "parquet_path": str(p)}

print(f"Found {len(manifest)} assets with Parquet files")

# Tier discovery with fixed grouping
print("\n=== TIER DISCOVERY (FIXED) ===")
all_tiers = {}
for symbol, meta in manifest.items():
    if meta.get("status") != "OK":
        continue
    parquet_path = Path(meta["parquet_path"])
    ranges_df = extract_asian_ranges(parquet_path, symbol)
    if len(ranges_df) == 0:
        print(f"  [{symbol}] No Asian Range data")
        all_tiers[symbol] = {"status": "NO_DATA"}
        continue
    tiers = discover_tiers(ranges_df, symbol)
    all_tiers[symbol] = tiers
    if tiers.get("status") == "OK":
        t = tiers["tiers"]
        print(f"  [{symbol}] T1 AU={t['T1']['au']:.1f}p | T2 AU={t['T2']['au']:.1f}p | T3 AU={t['T3']['au']:.1f}p")

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

# Save tiers
with open(TIERS_DIR / "all_tiers.json", "w") as f:
    json.dump(all_tiers, f, indent=2)

print("\n=== PHASE 1 COMPLETE (FIXED) ===")
