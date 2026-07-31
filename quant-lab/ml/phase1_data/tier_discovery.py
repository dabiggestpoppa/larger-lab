"""
Phase 1.4: K-Means Tier Discovery
===================================
Derive structural Tier thresholds from Asian Range distribution.

Algorithm:
  1. Cluster AR values into k=3 groups (K-Means)
  2. Sort centroids ascending → T1 (tight), T2 (standard), T3 (wide)
  3. Cutoffs = midpoints between adjacent centroids
  4. AU = 50% of centroid (NON-NEGOTIABLE)
  5. Trigger = AU × 1.2
  6. Density Zone = AU ± 20%

Parameters are FIXED:
  k=3, n_init=10, random_state=42
  Do NOT optimize k. Three tiers are structurally mandated.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def discover_tiers(
    ar_values: list[float] | np.ndarray,
    symbol: str = "UNKNOWN",
) -> dict:
    """
    K-Means clustering to derive Tier thresholds and Atomic Units.

    Parameters
    ----------
    ar_values : array-like
        Asian Range values in pips (one per trading day).
    symbol : str
        Asset symbol for labeling.

    Returns
    -------
    dict
        Complete tier configuration with centroids, cutoffs, AUs, triggers, DZ bounds.
    """
    X = np.array(ar_values).reshape(-1, 1)

    if len(X) < 60:
        raise ValueError(f"Need ≥60 sessions for reliable clustering, got {len(X)}")

    # K-Means k=3 (FIXED — do not optimize)
    km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)
    centroids = sorted(km.cluster_centers_.flatten())

    c_low, c_mid, c_high = centroids

    # Cutoffs = midpoints between centroids
    cutoff1 = (c_low + c_mid) / 2
    cutoff2 = (c_mid + c_high) / 2

    # AU = 50% of centroid (NON-NEGOTIABLE)
    au_t1 = c_low * 0.50
    au_t2 = c_mid * 0.50
    au_t3 = c_high * 0.50

    # Trigger = AU × 1.2
    trig_t1 = au_t1 * 1.2
    trig_t2 = au_t2 * 1.2
    trig_t3 = au_t3 * 1.2

    # Density Zone = AU ± 20%
    dz_t1 = [au_t1 * 0.80, au_t1 * 1.20]
    dz_t2 = [au_t2 * 0.80, au_t2 * 1.20]
    dz_t3 = [au_t3 * 0.80, au_t3 * 1.20]

    # Per-bar tier assignment from labels
    labels = km.labels_
    cluster_counts = {
        "T1": int((labels == 0).sum()),
        "T2": int((labels == 1).sum()),
        "T3": int((labels == 2).sum()),
    }

    result = {
        "symbol": symbol,
        "sessions_analyzed": len(X),
        "mean_ar": round(float(np.mean(X)), 2),
        "centroids": {
            "T1": round(c_low, 2),
            "T2": round(c_mid, 2),
            "T3": round(c_high, 2),
        },
        "cutoffs": {
            "T1_T2": round(cutoff1, 2),
            "T2_T3": round(cutoff2, 2),
        },
        "tiers": {
            "T1": {
                "ar_max": round(cutoff1, 2),
                "centroid": round(c_low, 2),
                "atomic_unit": round(au_t1, 2),
                "trigger": round(trig_t1, 2),
                "density_zone": [round(dz_t1[0], 2), round(dz_t1[1], 2)],
                "session_count": cluster_counts.get("T1", 0),
            },
            "T2": {
                "ar_min": round(cutoff1, 2),
                "ar_max": round(cutoff2, 2),
                "centroid": round(c_mid, 2),
                "atomic_unit": round(au_t2, 2),
                "trigger": round(trig_t2, 2),
                "density_zone": [round(dz_t2[0], 2), round(dz_t2[1], 2)],
                "session_count": cluster_counts.get("T2", 0),
            },
            "T3": {
                "ar_min": round(cutoff2, 2),
                "centroid": round(c_high, 2),
                "atomic_unit": round(au_t3, 2),
                "trigger": round(trig_t3, 2),
                "density_zone": [round(dz_t3[0], 2), round(dz_t3[1], 2)],
                "session_count": cluster_counts.get("T3", 0),
            },
        },
        "cluster_distribution": cluster_counts,
    }

    return result


def discover_tiers_from_parquet(
    symbol: str,
    parquet_dir: Path,
    pip_size: float = 1.0,
) -> dict:
    """
    End-to-end: load Parquet → extract AR → discover tiers.
    """
    from ml.phase1_data.asian_range import extract_asian_ranges_from_parquet

    ar_df = extract_asian_ranges_from_parquet(symbol, parquet_dir, pip_size)
    if len(ar_df) < 60:
        raise ValueError(f"{symbol}: Only {len(ar_df)} sessions (need ≥60)")

    return discover_tiers(ar_df["ar_pips"].values, symbol)


def save_tier_config(tier_config: dict, output_dir: Path) -> Path:
    """Save tier config as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    symbol = tier_config["symbol"]
    out_path = output_dir / f"{symbol}_tiers.json"
    with open(out_path, "w") as f:
        json.dump(tier_config, f, indent=2)
    return out_path


def run_all_assets(
    parquet_dir: Path,
    pip_sizes: dict[str, float],
    output_dir: Path,
) -> dict[str, dict]:
    """
    Run tier discovery on all available assets.
    Returns {symbol: tier_config} dict.
    """
    results = {}
    parquet_files = list(parquet_dir.glob("*_M5.parquet"))

    for pf in parquet_files:
        symbol = pf.stem.replace("_M5", "")
        pip_size = pip_sizes.get(symbol, 1.0)

        try:
            config = discover_tiers_from_parquet(symbol, parquet_dir, pip_size)
            save_tier_config(config, output_dir)
            results[symbol] = config
            t1 = config["tiers"]["T1"]
            t2 = config["tiers"]["T2"]
            t3 = config["tiers"]["T3"]
            print(f"  ✅ {symbol}: T1 AU={t1['atomic_unit']}p | T2 AU={t2['atomic_unit']}p | T3 AU={t3['atomic_unit']}p | n={config['sessions_analyzed']}")
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")
            results[symbol] = {"error": str(e)}

    print(f"\n✅ Phase 1.4 Complete: {len([r for r in results.values() if 'error' not in r])}/{len(parquet_files)} assets tiered")
    return results


if __name__ == "__main__":
    parquet_dir = Path(__file__).resolve().parent.parent / "features" / "parquet"
    output_dir = Path(__file__).resolve().parent.parent / "configs" / "tiers"

    # Standard pip sizes for CEREBUS assets
    PIP_SIZES = {
        "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
        "USDJPY": 0.01, "AUDUSD": 0.0001, "NZDUSD": 0.0001,
        "CHFJPY": 0.01, "GBPJPY": 0.01, "GBPAUD": 0.0001,
        "GBPNZD": 0.0001, "GBPCHF": 0.0001,
        "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
        "XAUUSD": 0.01, "XAGUSD": 0.001,
        "BTCUSD": 1.0, "ETHUSD": 0.01,
    }

    if any(parquet_dir.glob("*.parquet")):
        run_all_assets(parquet_dir, PIP_SIZES, output_dir)
    else:
        print("Run data_pipeline.py first to generate Parquet files")
