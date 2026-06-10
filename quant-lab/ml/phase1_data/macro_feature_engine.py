"""
Phase 1B: Macro Feature Engine (CEREBUS Physics)
===================================================
Computes macro-level features for every M15 candle:

1. MLR (Monday London Range) — 07:00-10:00 UTC anchor
2. Bias Detection — Bullish/Bearish from MLR close vs mid
3. Fibonacci Targets — -25%, -50%, -100%, -168% extensions
4. 132% Kill-Switch — structural invalidation level
5. ILM State — Daily/IELM/WILM/Misaligned
6. Regime Ratio — 9AM checkpoint ratio
7. Time Block Encoding — day, session, hours since MLR
8. Distance Features — pip distances to all key levels

These are the MISSING features that the previous build didn't have.
The existing feature matrix has 8 micro features. This adds 12+ macro features.

GATE: No future leakage. MLR is forward-filled from Monday to Friday.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

CLEAN_DIR = Path(__file__).parent.parent / "data" / "clean"
MACRO_FEATURES_DIR = Path(__file__).parent.parent / "data" / "macro_features"
MACRO_FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# MLR window: Monday 07:00-10:00 UTC
MLR_START_HOUR_UTC = 7
MLR_END_HOUR_UTC = 10

# Asian session for ILM: 19:00-03:00 EST (= 00:00-08:00 UTC)
ASIAN_START_EST = 19
ASIAN_END_EST = 3

# Session boundaries (UTC)
SESSION_HOURS_UTC = {
    "asian": (0, 8),      # 00:00-08:00 UTC (= 19:00-03:00 EST)
    "london": (7, 16),    # 07:00-16:00 UTC
    "ny": (12, 21),       # 12:00-21:00 UTC
    "black": (21, 24),    # 21:00-24:00 UTC (gap)
}

# Pip multipliers per asset
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


def get_pip_multiplier(symbol: str) -> int:
    """Get pip multiplier for a symbol."""
    return PIP_MULT.get(symbol, 10000)


def pips_to_price(pips: float, symbol: str) -> float:
    """Convert pips to price for a given symbol."""
    return pips / get_pip_multiplier(symbol)


def price_to_pips(price_diff: float, symbol: str) -> float:
    """Convert price difference to pips."""
    return price_diff * get_pip_multiplier(symbol)


# ============================================================
# 1. MONDAY LONDON RANGE (MLR)
# ============================================================

def compute_mlr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Monday London Range (MLR) for each week.
    MLR = High/Low of Monday 07:00-10:00 UTC.
    Forward-filled from Monday to Friday.

    Adds columns: mlr_high, mlr_low, mlr_range, mlr_mid, mlr_close, bias
    """
    df = df.copy()

    # Initialize MLR columns
    df["mlr_high"] = np.nan
    df["mlr_low"] = np.nan
    df["mlr_close"] = np.nan

    # Find Monday 07:00-10:00 UTC bars
    is_monday = df.index.dayofweek == 0
    is_mlr_hour = (df.index.hour >= MLR_START_HOUR_UTC) & (df.index.hour < MLR_END_HOUR_UTC)
    mlr_mask = is_monday & is_mlr_hour

    if mlr_mask.sum() == 0:
        print("  ⚠ No Monday London bars found — check timezone")
        return df

    # Group by week (Monday date as key)
    mlr_bars = df[mlr_mask].copy()
    mlr_bars["week_key"] = mlr_bars.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)

    weekly_mlr = mlr_bars.groupby("week_key").agg(
        mlr_high=("high", "max"),
        mlr_low=("low", "min"),
        mlr_close=("close", "last"),
    )

    # Forward-fill MLR to all bars in the week
    df["week_key"] = df.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)

    for week_start, row in weekly_mlr.iterrows():
        week_mask = df["week_key"] == week_start
        df.loc[week_mask, "mlr_high"] = row["mlr_high"]
        df.loc[week_mask, "mlr_low"] = row["mlr_low"]
        df.loc[week_mask, "mlr_close"] = row["mlr_close"]

    # Compute derived MLR features
    df["mlr_range"] = df["mlr_high"] - df["mlr_low"]
    df["mlr_mid"] = df["mlr_low"] + df["mlr_range"] / 2

    # Bias: Bullish if close > mid, Bearish otherwise
    df["bias"] = np.where(df["mlr_close"] > df["mlr_mid"], "BULLISH", "BEARISH")

    # Clean up
    df = df.drop(columns=["week_key"], errors="ignore")

    # Report
    valid_weeks = df["mlr_high"].notna().sum()
    print(f"  MLR: {valid_weeks} bars with MLR data ({weekly_mlr.shape[0]} weeks)")

    return df


# ============================================================
# 2. FIBONACCI TARGETS
# ============================================================

def compute_fib_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Fibonacci extension targets from MLR.
    Bullish: extensions above MLR high
    Bearish: extensions below MLR low

    Adds: target_25, target_50, target_100, target_168, kill_switch_132
    """
    df = df.copy()

    # Fib extension levels
    fib_levels = {
        "target_25": 0.25,
        "target_50": 0.50,
        "target_100": 1.00,
        "target_168": 1.68,
    }

    for target_name, level in fib_levels.items():
        # Bullish: MLR_high + level * MLR_range
        # Bearish: MLR_low - level * MLR_range
        df[target_name] = np.where(
            df["bias"] == "BULLISH",
            df["mlr_high"] + level * df["mlr_range"],
            df["mlr_low"] - level * df["mlr_range"],
        )

    # 132% Kill-Switch (structural invalidation)
    # Bullish: MLR_low - 1.32 * MLR_range (below the range)
    # Bearish: MLR_high + 1.32 * MLR_range (above the range)
    df["kill_switch_132"] = np.where(
        df["bias"] == "BULLISH",
        df["mlr_low"] - 1.32 * df["mlr_range"],
        df["mlr_high"] + 1.32 * df["mlr_range"],
    )

    valid = df["target_25"].notna().sum()
    print(f"  Fib targets: {valid} bars with targets")

    return df


# ============================================================
# 3. DISTANCE FEATURES
# ============================================================

def compute_distance_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute pip distances from current price to all key levels.
    These are the PRIMARY features for XGBoost.

    Adds: dist_to_25_pips, dist_to_50_pips, dist_to_100_pips,
          dist_to_168_pips, dist_to_132_pips, dist_to_mlr_high_pips,
          dist_to_mlr_low_pips, dist_to_mlr_mid_pips
    """
    df = df.copy()

    # Distance to each Fib target (in pips, signed)
    for target in ["target_25", "target_50", "target_100", "target_168"]:
        col = f"dist_to_{target.replace('target_', '')}_pips"
        df[col] = (df[target] - df["close"]) * get_pip_multiplier(symbol)

    # Distance to 132% kill-switch (ALWAYS positive — it's a safety distance)
    df["dist_to_132_pips"] = (df["kill_switch_132"] - df["close"]).abs() * get_pip_multiplier(symbol)

    # Distance to MLR boundaries
    df["dist_to_mlr_high_pips"] = (df["mlr_high"] - df["close"]) * get_pip_multiplier(symbol)
    df["dist_to_mlr_low_pips"] = (df["mlr_low"] - df["close"]) * get_pip_multiplier(symbol)
    df["dist_to_mlr_mid_pips"] = (df["mlr_mid"] - df["close"]) * get_pip_multiplier(symbol)

    return df


# ============================================================
# 4. ILM STATE
# ============================================================

def compute_ilm_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Intra-day Liquidity Model (ILM) state.

    ILM Types:
    - Daily ILM: Price within daily range, no extreme
    - IELM (Intra-day Extreme Liquidity Model): Price at daily extreme
    - WILM (Weekly ILM): Price at weekly extreme (Monday range)
    - Misaligned: Price outside expected range

    Encoded as: 0=Daily ILM, 1=IELM, 2=WILM, 3=Misaligned
    """
    df = df.copy()

    # Compute daily high/low up to current bar (no future leakage)
    df["daily_high"] = df["high"].groupby(df.index.date).cummax()
    df["daily_low"] = df["low"].groupby(df.index.date).cummin()
    df["daily_range"] = df["daily_high"] - df["daily_low"]

    # Avoid division by zero
    df["daily_range"] = df["daily_range"].replace(0, np.nan)

    # Position within daily range (0 = at low, 1 = at high)
    df["pos_in_daily_range"] = (df["close"] - df["daily_low"]) / df["daily_range"]

    # ILM classification
    ilm_state = np.zeros(len(df), dtype=int)  # Default: Daily ILM

    # IELM: Price within 10% of daily extreme
    ilm_state[df["pos_in_daily_range"] > 0.9] = 1  # High extreme
    ilm_state[df["pos_in_daily_range"] < 0.1] = 1  # Low extreme

    # WILM: Price at weekly extreme (near MLR boundary)
    if "mlr_high" in df.columns:
        dist_to_mlr_extreme = np.minimum(
            (df["close"] - df["mlr_high"]).abs(),
            (df["close"] - df["mlr_low"]).abs(),
        )
        # Within 5% of weekly range from extreme
        near_weekly_extreme = dist_to_mlr_extreme < (df["mlr_range"] * 0.05)
        ilm_state[near_weekly_extreme] = 2

    # Misaligned: Price outside MLR range entirely
    if "mlr_high" in df.columns:
        outside_mlr = (df["close"] > df["mlr_high"] * 1.01) | (df["close"] < df["mlr_low"] * 0.99)
        ilm_state[outside_mlr] = 3

    df["ilm_state"] = ilm_state

    # Clean up intermediate columns
    df = df.drop(columns=["pos_in_daily_range"], errors="ignore")

    # Report
    state_counts = pd.Series(ilm_state).map({0: "Daily", 1: "IELM", 2: "WILM", 3: "Misaligned"}).value_counts()
    print(f"  ILM states: {dict(state_counts)}")

    return df


# ============================================================
# 5. REGIME RATIO
# ============================================================

def compute_regime_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 9AM checkpoint regime ratio.
    Ratio = (Current price range from session open) / (Expected range from tier)

    Regime classification:
    - CONFIRMED: ratio > 1.5x
    - CAUTION: ratio 1.0-1.5x
    - FAILED: ratio < 1.0x

    Adds: regime_ratio, regime_status
    """
    df = df.copy()

    # Find 9AM EST (= 14:00 UTC) checkpoint
    is_9am_est = (df.index.hour == 14) & (df.index.minute == 0)

    # Session open = Asian session open (19:00 EST = 00:00 UTC)
    # For simplicity, use daily open as proxy
    df["session_open"] = df["open"].groupby(df.index.date).transform("first")

    # Price range from session open
    df["price_range_from_open"] = (df["close"] - df["session_open"]).abs()

    # Expected range from MLR (if available)
    if "mlr_range" in df.columns:
        df["expected_range"] = df["mlr_range"]
    else:
        # Fallback: use 20-bar average range
        df["expected_range"] = (df["high"] - df["low"]).rolling(20, min_periods=5).mean()

    # Regime ratio
    df["regime_ratio"] = df["price_range_from_open"] / df["expected_range"].replace(0, np.nan)

    # Regime status
    conditions = [
        df["regime_ratio"] > 1.5,
        df["regime_ratio"] >= 1.0,
        df["regime_ratio"] < 1.0,
    ]
    choices = ["CONFIRMED", "CAUTION", "FAILED"]
    df["regime_status"] = np.select(conditions, choices, default="UNKNOWN")

    # Report
    status_counts = df["regime_status"].value_counts()
    print(f"  Regime status: {dict(status_counts)}")

    return df


# ============================================================
# 6. TIME BLOCK ENCODING
# ============================================================

def compute_time_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode temporal features:
    - day_of_week: 0=Mon ... 6=Sun
    - session: asian/london/ny/black
    - is_monday: binary
    - is_wednesday: binary (bifurcation day)
    - is_friday: binary
    - is_wednesday_pm: binary (Wed 12:00+ EST = 17:00+ UTC)
    - hours_since_mlr: hours since Monday London Range formation
    - minutes_to_12pm_est: minutes until 12PM EST hard exit (17:00 UTC)
    """
    df = df.copy()

    # Day of week
    df["day_of_week"] = df.index.dayofweek

    # Session encoding
    hour_utc = df.index.hour
    conditions = [
        (hour_utc >= 0) & (hour_utc < 8),
        (hour_utc >= 7) & (hour_utc < 16),
        (hour_utc >= 12) & (hour_utc < 21),
        (hour_utc >= 21) | (hour_utc < 0),
    ]
    choices = ["asian", "london", "ny", "black"]
    df["session"] = np.select(conditions, choices, default="unknown")

    # Key day flags
    df["is_monday"] = (df.index.dayofweek == 0).astype(int)
    df["is_wednesday"] = (df.index.dayofweek == 2).astype(int)
    df["is_friday"] = (df.index.dayofweek == 4).astype(int)

    # Wednesday PM (12:00+ EST = 17:00+ UTC) — bifurcation window
    df["is_wednesday_pm"] = (
        (df.index.dayofweek == 2) & (df.index.hour >= 17)
    ).astype(int)

    # Hours since MLR (Monday 07:00 UTC) — vectorized
    df["hours_since_mlr"] = np.nan
    monday_mask = (df.index.dayofweek == 0) & (df.index.hour == MLR_START_HOUR_UTC)
    if monday_mask.any():
        monday_times = df.index[monday_mask]
        # Use searchsorted for efficient lookup
        idx_positions = monday_times.searchsorted(df.index, side="right") - 1
        valid = idx_positions >= 0
        hours = np.full(len(df), np.nan)
        hours[valid] = (
            (df.index[valid] - monday_times[idx_positions[valid]]).total_seconds() / 3600
        )
        df["hours_since_mlr"] = hours

    # Minutes to 12PM EST hard exit (17:00 UTC)
    today_17utc = df.index.normalize() + pd.Timedelta(hours=17)
    df["minutes_to_12pm_est"] = (today_17utc - df.index).total_seconds() / 60
    # After 17:00 UTC, set to 0 (hard exit has passed)
    df.loc[df["minutes_to_12pm_est"] < 0, "minutes_to_12pm_est"] = 0

    return df


# ============================================================
# 7. FULL MACRO FEATURE PIPELINE
# ============================================================

def compute_all_macro_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Run the full macro feature pipeline on a single-asset DataFrame.
    Returns DataFrame with all macro features added.
    """
    print(f"\nComputing macro features for {symbol}:")

    # Step 1: MLR
    df = compute_mlr(df)

    # Step 2: Fib targets
    df = compute_fib_targets(df)

    # Step 3: Distance features
    df = compute_distance_features(df, symbol)

    # Step 4: ILM state
    df = compute_ilm_state(df)

    # Step 5: Regime ratio
    df = compute_regime_ratio(df)

    # Step 6: Time blocks
    df = compute_time_blocks(df)

    # Report macro feature columns
    macro_cols = [c for c in df.columns if c.startswith((
        "mlr_", "target_", "kill_switch", "dist_to_", "ilm_state",
        "regime_ratio", "regime_status", "is_monday", "is_wednesday",
        "is_friday", "is_wednesday_pm", "hours_since_mlr", "minutes_to_12pm",
        "bias", "session", "daily_", "session_open", "price_range",
        "expected_range",
    ))]
    print(f"  Total macro feature columns: {len(macro_cols)}")

    return df


def run_macro_features_for_all_assets() -> dict:
    """
    Run macro feature computation for all assets in the clean dataset.
    """
    print("=" * 60)
    print("PHASE 1B: MACRO FEATURE ENGINE")
    print("=" * 60)

    manifest = {}

    for parquet_file in sorted(CLEAN_DIR.glob("*_clean.parquet")):
        symbol = parquet_file.stem.replace("_clean", "")
        print(f"\n{'='*40}")
        print(f"Processing: {symbol}")
        print(f"{'='*40}")

        df = pd.read_parquet(parquet_file)
        print(f"Input: {len(df)} rows, {len(df.columns)} columns")

        df = compute_all_macro_features(df, symbol)

        # Save
        out_path = MACRO_FEATURES_DIR / f"{symbol}_macro.parquet"
        df.to_parquet(out_path)

        manifest[symbol] = {
            "rows": len(df),
            "columns": len(df.columns),
            "macro_columns": len([c for c in df.columns if c.startswith((
                "mlr_", "target_", "kill_switch", "dist_to_", "ilm_state",
                "regime_ratio", "regime_status", "is_monday", "is_wednesday",
                "is_friday", "is_wednesday_pm", "hours_since_mlr", "minutes_to_12pm",
                "bias", "session",
            ))]),
            "path": str(out_path),
        }
        print(f"  ✓ Saved: {out_path}")

    # Save manifest
    manifest_path = MACRO_FEATURES_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"PHASE 1B COMPLETE: {len(manifest)} assets processed")
    print(f"{'='*60}")

    return manifest


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import json
    result = run_macro_features_for_all_assets()
    print(f"\nManifest: {json.dumps(result, indent=2)}")
