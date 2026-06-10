"""
Micro Feature Computation
==========================
Computes micro-level features from raw OHLCV data.
These are the MISSING features that the old pipeline had but weren't carried over.

Features computed:
- asian_range_pips: Asian session range (19:00-03:00 EST = 00:00-08:00 UTC)
- vol_ratio_3am_9am: (3AM-9AM EST range) / Asian Range
- spread_vs_20d_avg: Current spread / 20-day average spread
- impulse_to_ar_ratio: First impulse size / Asian Range
- consecutive_losses: Rolling streak counter (computed from labels)
- prior_session_wr: Prior session win rate (computed from labels)
- mlr_range_pips: MLR range in pips
- bias_encoded: 1 = Bullish, 0 = Bearish
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

PIP_MULT = {
    "EURUSD": 10000, "GBPUSD": 10000, "USDCHF": 10000, "AUDUSD": 10000,
    "NZDUSD": 10000, "USDCAD": 10000, "EURGBP": 10000, "EURAUD": 10000,
    "EURCHF": 10000, "GBPAUD": 10000, "GBPCAD": 10000, "GBPCHF": 10000,
    "GBPNZD": 10000, "AUDCAD": 10000, "AUDCHF": 10000, "AUDNZD": 10000,
    "NZDCAD": 10000, "NZDCHF": 10000, "CADCHF": 10000,
    "USDJPY": 100, "EURJPY": 100, "GBPJPY": 100, "AUDJPY": 100,
    "NZDJPY": 100, "CADJPY": 100, "CHFJPY": 100,
    "XAUUSD": 10, "XAGUSD": 1000,
    "BTCUSD": 1, "ETHUSD": 10, "LTCUSD": 1, "BCHUSD": 1, "BNBUSD": 1,
    "SOLUSD": 1, "XLMUSD": 1,
    "OILUSD": 100, "US500": 1, "DE30": 1, "FR40": 1, "NAS100": 1, "HK50": 1,
}


def get_pip_mult(symbol: str) -> int:
    return PIP_MULT.get(symbol, 10000)


def compute_asian_range(df: pd.DataFrame, symbol: str) -> pd.Series:
    """
    Compute Asian Range (00:00-08:00 UTC = 19:00-03:00 EST) for each day.
    Forward-filled to all bars in the day.
    """
    pip_mult = get_pip_mult(symbol)
    df = df.copy()

    # Asian session: 00:00-08:00 UTC
    hour = df.index.hour
    asian_mask = (hour >= 0) & (hour < 8)

    # Group by date and compute Asian range
    df["_date"] = df.index.date
    df["_is_asian"] = asian_mask

    # For each day, compute Asian high/low from Asian session bars
    asian_ranges = {}
    for date, group in df.groupby("_date"):
        asian_bars = group[group["_is_asian"]]
        if len(asian_bars) > 0:
            asian_high = asian_bars["high"].max()
            asian_low = asian_bars["low"].min()
            asian_ranges[date] = (asian_high - asian_low) * pip_mult
        else:
            asian_ranges[date] = np.nan

    # Map to all bars
    df["asian_range_pips"] = df["_date"].map(asian_ranges)

    df = df.drop(columns=["_date", "_is_asian"], errors="ignore")
    return df["asian_range_pips"]


def compute_vol_ratio(df: pd.DataFrame) -> pd.Series:
    """
    Compute vol_ratio_3am_9am: (3AM-9AM EST range) / Asian Range.
    3AM-9AM EST = 08:00-14:00 UTC.
    """
    df = df.copy()
    hour = df.index.hour

    # 3AM-9AM EST = 08:00-14:00 UTC
    activation_mask = (hour >= 8) & (hour < 14)

    df["_date"] = df.index.date
    df["_is_activation"] = activation_mask

    # Compute activation range per day
    vol_ratios = {}
    for date, group in df.groupby("_date"):
        act_bars = group[group["_is_activation"]]
        asian_range = group["asian_range_pips"].iloc[0] if "asian_range_pips" in group.columns else np.nan

        if len(act_bars) > 0 and not np.isnan(asian_range) and asian_range > 0:
            act_range = (act_bars["high"].max() - act_bars["low"].min()) * 10000  # Approximate
            vol_ratios[date] = act_range / asian_range
        else:
            vol_ratios[date] = np.nan

    df["vol_ratio_3am_9am"] = df["_date"].map(vol_ratios)
    df = df.drop(columns=["_date", "_is_activation"], errors="ignore")
    return df["vol_ratio_3am_9am"]


def compute_micro_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute all micro features and add them to the DataFrame.
    """
    df = df.copy()

    # Asian Range
    if "asian_range_pips" not in df.columns:
        df["asian_range_pips"] = compute_asian_range(df, symbol)

    # Vol Ratio
    if "vol_ratio_3am_9am" not in df.columns:
        df["vol_ratio_3am_9am"] = compute_vol_ratio(df)

    # Hour EST (UTC - 5)
    if "hour_est" not in df.columns:
        df["hour_est"] = (df.index.hour - 5) % 24

    # Spread vs 20d avg (use high-low as spread proxy if no spread column)
    if "spread_vs_20d_avg" not in df.columns:
        if "spread" in df.columns:
            spread = df["spread"]
        else:
            pip_mult = get_pip_mult(symbol)
            spread = (df["high"] - df["low"]) * pip_mult
        spread_20d = spread.rolling(5760, min_periods=288).mean()  # 20 days of M15
        df["spread_vs_20d_avg"] = spread / spread_20d

    # Impulse to AR ratio (first impulse of the day / Asian Range)
    if "impulse_to_ar_ratio" not in df.columns:
        df["_date"] = df.index.date
        # First impulse = first bar's range
        first_bar_range = df.groupby("_date")["high"].transform("first") - df.groupby("_date")["low"].transform("first")
        ar = df["asian_range_pips"].replace(0, np.nan)
        df["impulse_to_ar_ratio"] = first_bar_range * get_pip_mult(symbol) / ar
        df = df.drop(columns=["_date"], errors="ignore")

    # MLR range in pips
    if "mlr_range_pips" not in df.columns and "mlr_range" in df.columns:
        df["mlr_range_pips"] = df["mlr_range"] * get_pip_mult(symbol)

    # Bias encoded
    if "bias_encoded" not in df.columns and "bias" in df.columns:
        df["bias_encoded"] = (df["bias"] == "BULLISH").astype(int)

    # Consecutive losses (computed from labels if available)
    if "consecutive_losses" not in df.columns and "label_25_delivery" in df.columns:
        # Count consecutive -1 labels
        is_loss = (df["label_25_delivery"] == -1).astype(int)
        # Group consecutive losses
        groups = (is_loss != is_loss.shift()).cumsum()
        df["consecutive_losses"] = is_loss.groupby(groups).cumsum()

    # Prior session win rate (computed from labels if available)
    if "prior_session_wr" not in df.columns and "label_25_delivery" in df.columns:
        # Rolling win rate over last 96 bars (1 session)
        is_win = (df["label_25_delivery"] == 1).astype(float)
        df["prior_session_wr"] = is_win.rolling(96, min_periods=10).mean()

    return df
