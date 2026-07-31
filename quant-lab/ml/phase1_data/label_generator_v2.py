"""
Phase 1D: Label Generator v2 — Forward-Looking Labels (Vectorized)
====================================================================
For each M15 candle, looks ahead in time (NO future leakage) and assigns labels:

1. label_25_delivery: 1 (clean hit), -1 (rekey first), 0 (chop/miss)
2. label_50_delivery: same for -50% target
3. rekey_triggered: 1 if 132% breached before any target hit
4. time_to_25_min: minutes to -25% target hit (NaN if not hit)
5. time_to_50_min: minutes to -50% target hit (NaN if not hit)
6. regime_at_time: CONFIRMED/CAUTION/FAILED/NO-GO at this candle

CRITICAL: Order of events matters. If 132% is breached BEFORE the target,
the label is -1 (rekey), even if the target was eventually hit later.

GATE: All labels use strictly forward-looking windows. No data leakage.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

MACRO_FEATURES_DIR = Path(__file__).parent.parent / "data" / "macro_features"
LABELS_DIR = Path(__file__).parent.parent / "data" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Lookahead windows (in M15 bars)
LOOKAHEAD_25 = 96     # 24 hours
LOOKAHEAD_50 = 192    # 48 hours


# ============================================================
# VECTORIZED DELIVERY LABEL COMPUTATION
# ============================================================

def compute_delivery_labels(
    df: pd.DataFrame,
    target_col: str,
    lookahead: int,
) -> tuple[pd.Series, pd.Series]:
    """
    Compute delivery labels for all bars using chunked processing.
    For each bar, looks ahead `lookahead` bars to determine if target
    or kill-switch is hit first.

    Returns: (label_series, time_to_hit_minutes_series)
    label: 1 = clean hit, -1 = rekey first, 0 = miss/chop
    """
    n = len(df)
    labels = np.full(n, np.nan)
    times = np.full(n, np.nan)

    if target_col not in df.columns or "kill_switch_132" not in df.columns:
        return pd.Series(labels, index=df.index), pd.Series(times, index=df.index)

    target = df[target_col].values
    kill_switch = df["kill_switch_132"].values
    high = df["high"].values
    low = df["low"].values
    bias = df["bias"].values if "bias" in df.columns else np.full(n, "BULLISH")

    for i in range(n):
        end = min(i + 1 + lookahead, n)
        if end <= i + 1:
            continue

        tgt = target[i]
        ks = kill_switch[i]
        if np.isnan(tgt) or np.isnan(ks):
            continue

        fh = high[i + 1: end]
        fl = low[i + 1: end]

        if bias[i] == "BULLISH":
            ht = np.where(fh >= tgt)[0]
            hk = np.where(fl <= ks)[0]
        else:
            ht = np.where(fl <= tgt)[0]
            hk = np.where(fh >= ks)[0]

        ft = ht[0] if len(ht) > 0 else None
        fk = hk[0] if len(hk) > 0 else None

        if ft is None and fk is None:
            labels[i] = 0
        elif ft is not None and fk is None:
            labels[i] = 1
            times[i] = (ft + 1) * 5  # M15 bars → minutes
        elif fk is not None and ft is None:
            labels[i] = -1
        else:
            if ft <= fk:
                labels[i] = 1
                times[i] = (ft + 1) * 5
            else:
                labels[i] = -1

    return pd.Series(labels, index=df.index), pd.Series(times, index=df.index)


def compute_regime_at_time(df: pd.DataFrame) -> pd.Series:
    """Compute regime status at each point in time."""
    if "regime_status" in df.columns:
        return df["regime_status"]
    if "regime_ratio" in df.columns:
        conditions = [df["regime_ratio"] > 1.5, df["regime_ratio"] >= 1.0]
        choices = ["CONFIRMED", "CAUTION"]
        return pd.Series(np.select(conditions, choices, default="FAILED"), index=df.index)
    return pd.Series("UNKNOWN", index=df.index)


def compute_all_labels(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Run the full label generation pipeline for a single asset."""
    print(f"\nGenerating labels for {symbol} ({len(df)} bars)...")

    # Delivery labels for -25%
    print(f"  Computing -25% delivery labels...")
    label_25, time_25 = compute_delivery_labels(df, "target_25", LOOKAHEAD_25)
    df["label_25_delivery"] = label_25
    df["time_to_25_min"] = time_25

    # Delivery labels for -50%
    print(f"  Computing -50% delivery labels...")
    label_50, time_50 = compute_delivery_labels(df, "target_50", LOOKAHEAD_50)
    df["label_50_delivery"] = label_50
    df["time_to_50_min"] = time_50

    # Rekey triggered
    df["rekey_triggered"] = (df["label_25_delivery"] == -1).astype(float)

    # Regime at time
    df["regime_at_time"] = compute_regime_at_time(df)

    # Report
    for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered", "regime_at_time"]:
        valid = df[col].dropna()
        if len(valid) > 0:
            print(f"    {col}: {dict(valid.value_counts())}")

    return df


def run_labels_for_all_assets() -> dict:
    """Run label generation for all assets with macro features."""
    print("=" * 60)
    print("PHASE 1D: LABEL GENERATOR v2")
    print("=" * 60)

    manifest = {}

    for parquet_file in sorted(MACRO_FEATURES_DIR.glob("*_macro.parquet")):
        symbol = parquet_file.stem.replace("_macro", "")
        if symbol == "TEST":
            continue

        print(f"\n{'='*40}")
        print(f"Processing: {symbol}")

        df = pd.read_parquet(parquet_file)
        print(f"Input: {len(df)} rows")

        df = compute_all_labels(df, symbol)

        out_path = LABELS_DIR / f"{symbol}_labeled.parquet"
        df.to_parquet(out_path)

        manifest[symbol] = {
            "rows": len(df),
            "columns": len(df.columns),
            "path": str(out_path),
        }
        print(f"  ✓ Saved: {out_path}")

    manifest_path = LABELS_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"PHASE 1D COMPLETE: {len(manifest)} assets labeled")
    print(f"{'='*60}")

    return manifest


if __name__ == "__main__":
    result = run_labels_for_all_assets()
    print(f"\nManifest: {json.dumps(result, indent=2, default=str)}")
