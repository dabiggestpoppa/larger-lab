"""
Phase 1.3: Asian Range Extraction
===================================
Extract Asian Range (19:00-03:00 EST) for each trading day.
This is the foundational structural measurement for CEREBUS.

The Asian Range represents the overnight consolidation zone.
All tier classification, AU derivation, and regime detection
flows from this single measurement.

Window: 19:00 EST → 03:00 EST (next day) = 8 hours
Minimum 10 bars per session for valid range calculation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def extract_asian_ranges(
    df: pd.DataFrame,
    pip_size: float = 1.0,
    min_bars: int = 10,
) -> list[dict]:
    """
    Extract Asian Range for each trading day.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex (UTC).
    pip_size : float
        Pip/point size for the asset (e.g., 0.0001 for EURUSD, 0.01 for USDJPY, 1.0 for BTC).
    min_bars : int
        Minimum bars required for a valid Asian session.

    Returns
    -------
    list[dict]
        Each dict: {"date": date, "ar_pips": float, "high": float, "low": float, "bars": int}
    """
    # Convert to EST
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df_est = df.tz_convert("America/New_York")

    # Assign each bar to its trading day (session = date of the Asian range)
    # Asian session starts at 19:00 EST, so bars from 19:00-23:59 belong to that day's session
    # Bars from 00:00-02:59 belong to the previous day's session
    session_dates = []
    for ts in df_est.index:
        if ts.hour >= 19:
            session_dates.append(ts.date())
        else:
            session_dates.append((ts - pd.Timedelta(days=1)).date())

    df_est["session"] = session_dates

    results = []
    for day, group in df_est.groupby("session"):
        # Asian window: 19:00 - 03:00 EST
        asian = group[(group.index.hour >= 19) | (group.index.hour < 3)]

        if len(asian) < min_bars:
            continue

        high = asian["high"].max()
        low = asian["low"].min()
        ar_native = high - low
        ar_pips = ar_native / pip_size

        results.append({
            "date": str(day),
            "ar_pips": round(ar_pips, 2),
            "ar_native": round(ar_native, 6),
            "high": round(high, 6),
            "low": round(low, 6),
            "bars": len(asian),
        })

    return results


def extract_asian_ranges_from_parquet(
    symbol: str,
    parquet_dir: Path,
    pip_size: float = 1.0,
) -> pd.DataFrame:
    """
    Load a Parquet file and extract Asian Ranges.
    Returns DataFrame with columns: date, ar_pips, ar_native, high, low, bars
    """
    parquet_path = parquet_dir / f"{symbol}_M5.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"No Parquet for {symbol}: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)

    records = extract_asian_ranges(df, pip_size=pip_size)
    return pd.DataFrame(records)


def get_ar_statistics(ar_df: pd.DataFrame) -> dict:
    """
    Summary statistics for Asian Range distribution.
    Used for validation and tier discovery input.
    """
    if ar_df.empty:
        return {"error": "No Asian Range data"}

    ar_values = ar_df["ar_pips"].values
    return {
        "count": len(ar_values),
        "mean": round(float(np.mean(ar_values)), 2),
        "median": round(float(np.median(ar_values)), 2),
        "std": round(float(np.std(ar_values)), 2),
        "min": round(float(np.min(ar_values)), 2),
        "max": round(float(np.max(ar_values)), 2),
        "p25": round(float(np.percentile(ar_values, 25)), 2),
        "p75": round(float(np.percentile(ar_values, 75)), 2),
        "p90": round(float(np.percentile(ar_values, 90)), 2),
    }


if __name__ == "__main__":
    # Demo with EURUSD
    parquet_dir = Path(__file__).resolve().parent.parent / "features" / "parquet"

    if (parquet_dir / "EURUSD_M5.parquet").exists():
        ar_df = extract_asian_ranges_from_parquet("EURUSD", parquet_dir, pip_size=0.0001)
        stats = get_ar_statistics(ar_df)
        print(f"EURUSD Asian Range Stats ({stats['count']} sessions):")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("Run data_pipeline.py first to generate Parquet files")
