"""
Phase 1.6: Label Generation
=============================
Generate ML training labels from backtest outcomes.

Label Types:
  1. REGIME (4-class): CONFIRMED / CAUTION / FAILED / NO-GO
     Derived from: WIN/LOSS + R-multiple + vol_ratio
  2. ENTRY_QUALITY (regression 0-1): Normalized R-multiple
     Derived from: Actual R-multiple of each trade

Label Definitions (from CEREBUS ML Constitution):
  CONFIRMED = WIN and R >= 1.0 and vol_ratio >= 1.5
  CAUTION   = WIN and R >= 0.5 and vol_ratio 1.45-1.49
  FAILED    = LOSS or vol_ratio < 1.45
  NO-GO     = AR > NO-GO threshold OR spread > 3x avg

Training labels come from BACKTEST OUTCOMES, not raw price.
The model learns WHEN your strategy works, not price patterns.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# Regime label encoding
REGIME_MAP = {"CONFIRMED": 0, "CAUTION": 1, "FAILED": 2, "NO-GO": 3}
REGIME_REVERSE = {v: k for k, v in REGIME_MAP.items()}


def label_regime(row: pd.Series) -> str:
    """
    Label a single session/bar with regime class.

    Rules:
      NO-GO:    AR > threshold OR spread > 3x avg
      FAILED:   LOSS or vol_ratio < 1.45
      CAUTION:  WIN and R >= 0.5 and vol_ratio 1.45-1.49
      CONFIRMED: WIN and R >= 1.0 and vol_ratio >= 1.5
    """
    ar = row.get("asian_range_pips", 0)
    vol_ratio = row.get("vol_ratio_3am_9am", 1.0)
    spread_ratio = row.get("spread_vs_20d_avg", 1.0)
    outcome = row.get("outcome", None)  # "WIN" or "LOSS" from backtest
    r_multiple = row.get("r_multiple", 0.0)

    # NO-GO check
    if spread_ratio > 3.0:
        return "NO-GO"

    # FAILED check
    if outcome == "LOSS" or vol_ratio < 1.45:
        return "FAILED"

    # CAUTION check
    if outcome == "WIN" and r_multiple >= 0.5 and 1.45 <= vol_ratio < 1.5:
        return "CAUTION"

    # CONFIRMED check
    if outcome == "WIN" and r_multiple >= 1.0 and vol_ratio >= 1.5:
        return "CONFIRMED"

    # Default: FAILED (conservative)
    return "FAILED"


def label_entry_quality(r_multiple: float, max_r: float = 5.0) -> float:
    """
    Convert R-multiple to normalized entry quality score (0-1).
    1.0 = best observed R, 0.0 = worst (loss).
    """
    if max_r <= 0:
        return 0.0
    quality = r_multiple / max_r
    return float(np.clip(quality, 0.0, 1.0))


def generate_labels_from_trades(
    trades: list[dict],
    feature_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate labels from backtest trade results.

    Parameters
    ----------
    trades : list[dict]
        Each trade: {"entry_time": str, "exit_time": str, "outcome": "WIN"/"LOSS",
                     "r_multiple": float, "session_date": str, "vol_ratio": float}
    feature_df : pd.DataFrame
        Feature matrix from feature_matrix.py

    Returns
    -------
    pd.DataFrame
        Feature matrix with added label columns.
    """
    df = feature_df.copy()

    # Initialize label columns
    df["regime_label"] = "FAILED"
    df["regime_class"] = REGIME_MAP["FAILED"]
    df["entry_quality"] = 0.0
    df["r_multiple"] = 0.0
    df["outcome"] = None

    # Create trade lookup by session date
    trade_by_date = {}
    for t in trades:
        trade_by_date[t.get("session_date", "")] = t

    # Apply labels
    for idx, row in df.iterrows():
        session_date = row.get("session_date", "")
        if session_date in trade_by_date:
            trade = trade_by_date[session_date]
            df.at[idx, "outcome"] = trade.get("outcome")
            df.at[idx, "r_multiple"] = trade.get("r_multiple", 0.0)
            df.at[idx, "vol_ratio_3am_9am"] = trade.get("vol_ratio", row.get("vol_ratio_3am_9am", 1.0))

            regime = label_regime(df.loc[idx])
            df.at[idx, "regime_label"] = regime
            df.at[idx, "regime_class"] = REGIME_MAP[regime]

            quality = label_entry_quality(trade.get("r_multiple", 0.0))
            df.at[idx, "entry_quality"] = quality

    return df


def generate_synthetic_labels(feature_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic labels for initial model training.
    Used when backtest trade results are not yet available.

    Uses heuristic rules based on feature distributions.
    Replace with real backtest labels when available.
    """
    df = feature_df.copy()

    df["regime_label"] = "FAILED"
    df["regime_class"] = REGIME_MAP["FAILED"]
    df["entry_quality"] = 0.0

    for idx, row in df.iterrows():
        vol_ratio = row.get("vol_ratio_3am_9am", 1.0)
        spread_ratio = row.get("spread_vs_20d_avg", 1.0)
        ar = row.get("asian_range_pips", 0)

        # Synthetic regime labeling
        if spread_ratio > 3.0:
            regime = "NO-GO"
        elif vol_ratio >= 1.5:
            regime = "CONFIRMED"
        elif vol_ratio >= 1.45:
            regime = "CAUTION"
        else:
            regime = "FAILED"

        df.at[idx, "regime_label"] = regime
        df.at[idx, "regime_class"] = REGIME_MAP[regime]

        # Synthetic quality (based on vol_ratio as proxy)
        quality = min(1.0, max(0.0, (vol_ratio - 1.0) / 1.0))
        df.at[idx, "entry_quality"] = round(quality, 3)

    return df


def validate_label_distribution(df: pd.DataFrame) -> dict:
    """
    Validate label distribution matches expected patterns.
    Expected: ~62% CONFIRMED, ~8% NO-GO (from manual benchmarks).
    """
    total = len(df)
    if total == 0:
        return {"error": "Empty DataFrame"}

    dist = df["regime_label"].value_counts(normalize=True).to_dict()
    counts = df["regime_label"].value_counts().to_dict()

    result = {
        "total_rows": total,
        "distribution": {k: f"{v:.1%}" for k, v in dist.items()},
        "counts": counts,
        "warnings": [],
    }

    # Check expected ranges
    confirmed_pct = dist.get("CONFIRMED", 0)
    if confirmed_pct < 0.4:
        result["warnings"].append(f"CONFIRMED {confirmed_pct:.1%} below expected ~62%")
    if confirmed_pct > 0.85:
        result["warnings"].append(f"CONFIRMED {confirmed_pct:.1%} above expected ~62%")

    no_go_pct = dist.get("NO-GO", 0)
    if no_go_pct > 0.2:
        result["warnings"].append(f"NO-GO {no_go_pct:.1%} above expected ~8%")

    return result


def save_labeled_data(df: pd.DataFrame, symbol: str, output_dir: Path) -> Path:
    """Save labeled feature matrix as Parquet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{symbol}_labeled.parquet"
    df.to_parquet(out_path, engine="pyarrow", compression="zstd")
    return out_path


if __name__ == "__main__":
    print("Label generator ready. Use generate_labels_from_trades() with backtest results")
    print("or generate_synthetic_labels() for initial training.")
