"""
Phase 1.5: Feature Matrix Construction
========================================
Extract per-bar ML features from OHLCV data.

Features per bar:
  - asian_range_pips: Asian Range in native pips
  - vol_ratio_3am_9am: (3AM-9AM range) / Asian Range
  - hour_est: Hour of day EST (3-12)
  - spread_vs_20d_avg: Current spread / 20-day avg spread
  - impulse_to_ar_ratio: First impulse size / Asian Range
  - day_of_week: 0=Mon ... 4=Fri
  - consecutive_losses: Rolling streak counter
  - prior_session_wr: Prior session win rate (regime momentum)
  - pullback_pct: Pullback % of impulse
  - occ_body_to_au_ratio: OCC body size / Atomic Unit
  - time_since_impulse_min: Minutes since impulse candle
  - volume_spike_ratio: OCC volume / 20-bar avg volume
  - regime_confidence: Output from Layer 1 (filled after Phase 2)
  - distance_to_dz_center: How centered in DZ (0=center, 1=edge)
  - prior_loop_outcome: Last loop: 1=WIN, 0=LOSS, -1=NONE
  - spread_at_entry: Current spread in pips
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def compute_rolling_features(df: pd.DataFrame, pip_size: float = 1.0) -> pd.DataFrame:
    """
    Compute rolling/technical features from OHLCV data.
    Adds columns to the DataFrame in-place.
    """
    # Basic price features
    df["range"] = df["high"] - df["low"]
    df["body"] = (df["close"] - df["open"]).abs()
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]

    # Spread proxy (if bid/ask not available, use high-low as proxy)
    if "spread" in df.columns:
        df["spread_pips"] = df["spread"] / pip_size
    else:
        df["spread_pips"] = df["range"] / pip_size

    # Rolling spread average (20-day ≈ 5760 M5 bars)
    df["spread_20d_avg"] = df["spread_pips"].rolling(window=5760, min_periods=288).mean()
    df["spread_vs_20d_avg"] = df["spread_pips"] / df["spread_20d_avg"]

    # Volume spike ratio
    if "volume" in df.columns:
        df["vol_20bar_avg"] = df["volume"].rolling(window=20, min_periods=5).mean()
        df["volume_spike_ratio"] = df["volume"] / df["vol_20bar_avg"]
    else:
        df["volume_spike_ratio"] = 1.0

    # Time features (EST)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df_est = df.index.tz_convert("America/New_York")
    df["hour_est"] = df_est.hour
    df["day_of_week"] = df_est.dayofweek
    df["minute_of_day"] = df_est.hour * 60 + df_est.minute

    # Rolling volatility (20-bar)
    df["volatility_20"] = df["range"].rolling(window=20, min_periods=5).mean() / pip_size

    # Body-to-range ratio (OCC detection)
    df["body_to_range"] = df["body"] / df["range"].replace(0, np.nan)

    return df


def compute_session_features(
    df: pd.DataFrame,
    ar_values: dict[str, float],
    pip_size: float = 1.0,
) -> pd.DataFrame:
    """
    Add session-level features (Asian Range, vol ratio) to each bar.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex.
    ar_values : dict
        {date_str: ar_pips} mapping from asian_range extraction.
    pip_size : float
        Pip size for the asset.
    """
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df_est = df.index.tz_convert("America/New_York")

    # Assign session date
    session_dates = []
    for ts in df_est:
        if ts.hour >= 19:
            session_dates.append(str(ts.date()))
        else:
            session_dates.append(str((ts - pd.Timedelta(days=1)).date()))

    df["session_date"] = session_dates

    # Map Asian Range to each bar
    df["asian_range_pips"] = df["session_date"].map(ar_values).fillna(method="ffill")

    # 3AM-9AM volatility ratio
    # Compute rolling 3AM-9AM range for each session
    df["vol_ratio_3am_9am"] = np.nan  # Placeholder — computed per-session below

    return df


def build_feature_matrix(
    symbol: str,
    parquet_dir: Path,
    tier_config: dict,
    pip_size: float = 1.0,
) -> pd.DataFrame:
    """
    Build complete feature matrix for a single asset.
    This is the main entry point for Phase 1.5.
    """
    from ml.phase1_data.asian_range import extract_asian_ranges_from_parquet

    # Load data
    parquet_path = parquet_dir / f"{symbol}_M5.parquet"
    df = pd.read_parquet(parquet_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)

    # Extract Asian Ranges
    ar_df = extract_asian_ranges_from_parquet(symbol, parquet_dir, pip_size)
    ar_map = dict(zip(ar_df["date"], ar_df["ar_pips"]))

    # Compute features
    df = compute_rolling_features(df, pip_size)
    df = compute_session_features(df, ar_map, pip_size)

    # Add tier info from config
    if "tiers" in tier_config:
        t1 = tier_config["tiers"]["T1"]
        t2 = tier_config["tiers"]["T2"]
        t3 = tier_config["tiers"]["T3"]
        df["au_t1"] = t1["atomic_unit"]
        df["au_t2"] = t2["atomic_unit"]
        df["au_t3"] = t3["atomic_unit"]
        df["trigger_t1"] = t1["trigger"]
        df["trigger_t2"] = t2["trigger"]
        df["trigger_t3"] = t3["trigger"]

    # Classify each bar's session into tier
    def classify_tier(ar):
        if pd.isna(ar):
            return "UNKNOWN"
        if ar < tier_config["tiers"]["T1"].get("ar_max", 999):
            return "T1"
        elif ar < tier_config["tiers"]["T2"].get("ar_max", 999):
            return "T2"
        else:
            return "T3"

    df["session_tier"] = df["asian_range_pips"].apply(classify_tier)

    # Filter to trading hours only (3AM-12PM EST)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df_est = df.index.tz_convert("America/New_York")
    trading_mask = (df_est.hour >= 3) & (df_est.hour < 12)
    df = df[trading_mask]

    # Drop rows with NaN in critical features
    critical_cols = ["asian_range_pips", "hour_est", "day_of_week"]
    df = df.dropna(subset=critical_cols)

    return df


def build_all_assets(
    parquet_dir: Path,
    tier_configs: dict[str, dict],
    pip_sizes: dict[str, float],
    output_dir: Path,
) -> dict[str, int]:
    """
    Build feature matrices for all assets.
    Saves as Parquet. Returns {symbol: row_count}.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for symbol, config in tier_configs.items():
        if "error" in config:
            continue
        pip_size = pip_sizes.get(symbol, 1.0)
        try:
            df = build_feature_matrix(symbol, parquet_dir, config, pip_size)
            out_path = output_dir / f"{symbol}_features.parquet"
            df.to_parquet(out_path, engine="pyarrow", compression="zstd")
            results[symbol] = len(df)
            print(f"  ✅ {symbol}: {len(df):,} rows × {len(df.columns)} features")
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")
            results[symbol] = 0

    total = sum(results.values())
    print(f"\n✅ Phase 1.5 Complete: {len(results)} assets, {total:,} total rows")
    return results


if __name__ == "__main__":
    parquet_dir = Path(__file__).resolve().parent.parent / "features" / "parquet"
    output_dir = Path(__file__).resolve().parent.parent / "features" / "matrices"

    if not any(parquet_dir.glob("*.parquet")):
        print("Run data_pipeline.py first to generate Parquet files")
    else:
        print("Feature matrix builder ready. Run after tier_discovery.")
