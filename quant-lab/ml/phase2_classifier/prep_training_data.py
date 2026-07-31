"""
Prep Training Data for CEREBUS ML
==================================
Combines all features + labels into unified training matrices.
Handles missing features, creates DMR features, and outputs clean parquet files.

Usage:
    python prep_training_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

FULL_DIR = Path("quant-lab/ml/data/full_features_v2")
LABELS_DIR = Path("quant-lab/ml/data/labels")
OUT_DIR = Path("quant-lab/ml/data/training")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Feature columns to use ────────────────────────────────────────────────
# From full_features_v2 (80 cols), select the ML-relevant ones
FEATURE_COLS = [
    # Micro features (from full_features_v2)
    "asian_range_pips",
    "vol_ratio_3am_9am",
    "hour_est",
    "spread_vs_20d_avg",
    "impulse_to_ar_ratio",
    "day_of_week",
    "consecutive_losses",
    "prior_session_wr",
    "pullback_pct",
    "occ_body_pips",
    "occ_body_to_au_ratio",
    "volume_spike_ratio",
    "spread_at_entry",
    "distance_to_dz_center",
    "in_density_zone",
    "time_since_impulse_min",
    "price_range_from_open",
    "expected_range",
    "fib_sequence_state",
    "tier",
    "session",
    
    # Macro features (from full_features_v2)
    "dist_to_25_pips",
    "dist_to_50_pips",
    "dist_to_100_pips",
    "dist_to_132_pips",
    "dist_to_168_pips",
    "dist_to_mlr_high_pips",
    "dist_to_mlr_low_pips",
    "dist_to_mlr_mid_pips",
    "dist_to_weekly_target_pips",
    "regime_ratio",
    "ilm_state",
    "is_wednesday_pm",
    "hours_since_mlr",
    "minutes_to_12pm_est",
    "mlr_range_pips",
    "bias_encoded",
    "kill_switch_132",
    "weekly_kill_switch_132",
    "regime_status",
    "is_monday",
    "is_wednesday",
    "is_friday",
    "au_deficit_pips",
    "constraint_deficit_pips",
    "impulse_size_pips",
    "daily_range",
    "weekly_range",
]

# ── Label columns ─────────────────────────────────────────────────────────
LABEL_COLS = [
    "label_25_delivery",   # -1/0/1 (FAILED/CHOP/CONFIRMED)
    "label_50_delivery",   # -1/0/1
    "rekey_triggered",     # 0/1
    "regime_at_time",      # FAILED/CHOP/CONFIRMED/NO-GO
]


def prep_asset(name: str) -> dict:
    """Prep training data for a single asset."""
    full_path = FULL_DIR / f"{name}_full.parquet"
    labels_path = LABELS_DIR / f"{name}_labeled.parquet"
    
    if not full_path.exists():
        print(f"  SKIP {name}: no full features")
        return None
    if not labels_path.exists():
        print(f"  SKIP {name}: no labels")
        return None
    
    df = pd.read_parquet(full_path)
    labels = pd.read_parquet(labels_path)
    
    # Join on index (timestamp)
    df = df.join(labels[LABEL_COLS], how="inner")
    
    # Select available feature columns
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    
    if missing:
        print(f"  {name}: missing {len(missing)} features: {missing[:5]}...")
    
    # Drop rows with NaN in features or labels
    subset = available + LABEL_COLS
    df_clean = df.dropna(subset=subset)
    
    if len(df_clean) < 1000:
        print(f"  SKIP {name}: only {len(df_clean)} valid rows")
        return None
    
    # Save
    out_path = OUT_DIR / f"{name}_training.parquet"
    df_clean[available + LABEL_COLS].to_parquet(out_path)
    
    # Compute label distributions
    label_dist = {}
    for col in LABEL_COLS:
        if col in df_clean.columns:
            label_dist[col] = df_clean[col].value_counts().to_dict()
    
    return {
        "name": name,
        "rows": len(df_clean),
        "features": len(available),
        "missing": missing,
        "label_dist": label_dist,
        "path": str(out_path),
    }


def main():
    print("=" * 60)
    print("PREP TRAINING DATA")
    print("=" * 60)
    
    # Get all available assets
    assets = []
    for f in sorted(FULL_DIR.glob("*_full.parquet")):
        name = f.stem.replace("_full", "")
        assets.append(name)
    
    print(f"\nFound {len(assets)} assets: {', '.join(assets)}\n")
    
    results = {}
    total_rows = 0
    
    for asset in assets:
        print(f"Processing {asset}...")
        r = prep_asset(asset)
        if r:
            results[asset] = r
            total_rows += r["rows"]
            print(f"  OK: {r['rows']:,} rows x {r['features']} features")
    
    # Save manifest
    manifest = {
        "assets": list(results.keys()),
        "total_rows": total_rows,
        "feature_count": len(FEATURE_COLS),
        "available_features": len(FEATURE_COLS),
        "label_cols": LABEL_COLS,
        "per_asset": {k: {"rows": v["rows"], "features": v["features"], "missing": v["missing"]} for k, v in results.items()},
    }
    
    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"  Assets: {len(results)}")
    print(f"  Total rows: {total_rows:,}")
    print(f"  Features: {len(FEATURE_COLS)}")
    print(f"  Output: {OUT_DIR}")
    print(f"  Manifest: {manifest_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
