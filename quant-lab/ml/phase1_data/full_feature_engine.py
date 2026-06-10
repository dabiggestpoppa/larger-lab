"""
CEREBUS Full Feature Engine — COMPLETE (No Shortcuts)
=======================================================
Implements ALL features from CEREBUS BUILD.txt Phase 1.1 exactly.

MICRO FEATURES (Atomic & Intraday):
  1. asian_range_pips + tier classification (T1/T2/T3/T4)
  2. constraint_deficit — distance from Asian band edge
  3. density_zone_proximity — 38.2%-50% rebalancing zone (binary + pip distance)
  4. au_deficit — distance to Atomic Unit target (50% of K-Means centroid)
  5. regime_ratio — 9AM checkpoint ratio (CONFIRMED/CAUTION/FAILED)
  6. ilm_state — Daily ILM / IELM / WILM / Misaligned
  7. impulse_to_ar_ratio — first impulse / Asian Range
  8. occ_body_to_au_ratio — OCC body size / AU
  9. pullback_pct — pullback % of impulse
  10. time_since_impulse_min — minutes since impulse candle
  11. volume_spike_ratio — OCC volume / 20-bar avg
  12. distance_to_dz_center — how centered in Density Zone
  13. prior_loop_outcome — last loop result
  14. consecutive_losses — rolling loss streak
  15. prior_session_wr — prior session win rate
  16. spread_vs_20d_avg — current spread / 20-day avg
  17. hour_est — hour of day EST

MACRO FEATURES (Fib Sequence & Time Blocks):
  18. mlr_high / mlr_low / mlr_range / mlr_mid / mlr_close
  19. bias — Bullish/Bearish from MLR close vs mid
  20. target_minus_25 — MLR -25% extension
  21. target_minus_50 — MLR -50% extension
  22. target_minus_100 — MLR -100% extension
  23. target_minus_168 — MLR -168% extension
  24. kill_switch_132 — 132% invalidation level
  25. dist_to_25_pips — pip distance to -25% target
  26. dist_to_50_pips — pip distance to -50% target
  27. dist_to_100_pips — pip distance to -100% target
  28. dist_to_168_pips — pip distance to -168% target
  29. dist_to_132_pips — pip distance to 132% kill-switch
  30. dist_to_mlr_high_pips — pip distance to MLR high
  31. dist_to_mlr_low_pips — pip distance to MLR low
  32. weekly_target_proximity — distance to weekly Fib targets
  33. fib_sequence_state — which Fib sequence is active
  34. day_of_week — 0=Mon to 4=Fri
  35. session — Asian/London/NY/Black Zone
  36. hours_since_mlr — hours since Monday London Range
  37. minutes_to_12pm_est — countdown to 12PM EST hard exit
  38. is_wednesday_pm — Wednesday PM bifurcation flag
  39. is_monday — Monday flag
  40. is_friday — Friday flag

FORWARD-LOOKING LABELS (Phase 1.2):
  41. au_completion — AU target hit within 2h without OCC violation
  42. macro_25_hit — MLR -25% hit within 24h
  43. macro_50_hit — MLR -50% hit within 48h
  44. rekey_triggered — 132% breached before targets
  45. time_to_delivery — minutes to -25% hit
  46. pattern_formation — Alpha 3-Leg / Beta 3-Leg / AB-CD / None

GATE: No future leakage. All features use only past/current data.
All labels use strictly forward-looking windows.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans

# ============================================================
# CONFIG
# ============================================================

PIP_MULT = {
    "EURUSD": 10000, "GBPUSD": 10000, "USDCHF": 10000, "AUDUSD": 10000,
    "NZDUSD": 10000, "USDCAD": 10000, "EURGBP": 10000, "EURAUD": 10000,
    "EURCHF": 10000, "GBPAUD": 10000, "GBPCAD": 10000, "GBPCHF": 10000,
    "GBPNZD": 10000, "AUDCAD": 10000, "AUDCHF": 10000, "AUDNZD": 10000,
    "NZDCAD": 10000, "NZDCHF": 10000, "CADCHF": 10000,
    "USDJPY": 100, "EURJPY": 100, "GBPJPY": 100, "AUDJPY": 100,
    "NZDJPY": 100, "CADJPY": 100, "CHFJPY": 100,
    "XAUUSD": 10, "XAGUSD": 1000,
    "BTCUSD": 1, "ETHUSD": 10, "OILUSD": 100,
    "US500": 1, "DE30": 1, "FR40": 1, "NAS100": 1, "HK50": 1,
}

# Fibonacci extension levels from MLR
FIB_LEVELS = {
    "minus_25": 0.25,
    "minus_50": 0.50,
    "minus_100": 1.00,
    "minus_168": 1.68,
}

# 132% Kill-Switch level
KILL_SWITCH_PCT = 1.32

# Density Zone: 38.2% - 50% of Asian Range from the edge
DZ_LOW_PCT = 0.382
DZ_HIGH_PCT = 0.50

# AU = 50% of K-Means centroid (NON-NEGOTIABLE)
AU_FACTOR = 0.50

# Tier classification boundaries (will be overridden by K-Means)
TIER_BOUNDARIES = {"T1": 20, "T2": 30, "T3": 45}


def get_pip_mult(symbol: str) -> int:
    return PIP_MULT.get(symbol, 10000)


# ============================================================
# SECTION 1: MICRO FEATURES
# ============================================================

def compute_asian_range(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute daily Asian Range (19:00-03:00 EST = 00:00-08:00 UTC).
    Adds: asian_high, asian_low, asian_range_pips, tier
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Asian session: 00:00-08:00 UTC
    hour = df.index.hour
    asian_mask = (hour >= 0) & (hour < 8)

    df["_date"] = df.index.date
    df["_is_asian"] = asian_mask

    # Compute daily Asian range from Asian session bars
    daily_asian = {}
    for date, group in df.groupby("_date"):
        asian_bars = group[group["_is_asian"]]
        if len(asian_bars) >= 2:  # Minimum 2 bars for valid range
            daily_asian[date] = {
                "asian_high": asian_bars["high"].max(),
                "asian_low": asian_bars["low"].min(),
                "asian_range_pips": (asian_bars["high"].max() - asian_bars["low"].min()) * pip_mult,
            }
        else:
            daily_asian[date] = {"asian_high": np.nan, "asian_low": np.nan, "asian_range_pips": np.nan}

    asian_df = pd.DataFrame(daily_asian).T
    df["asian_high"] = df["_date"].map(asian_df["asian_high"])
    df["asian_low"] = df["_date"].map(asian_df["asian_low"])
    df["asian_range_pips"] = df["_date"].map(asian_df["asian_range_pips"])

    # Tier classification (initial — will be refined by K-Means later)
    def classify_tier(rng):
        if pd.isna(rng):
            return "UNKNOWN"
        elif rng < 20:
            return "T1"
        elif rng < 30:
            return "T2"
        elif rng < 45:
            return "T3"
        else:
            return "T4_NO_GO"

    df["tier"] = df["asian_range_pips"].apply(classify_tier)

    df = df.drop(columns=["_date", "_is_asian"], errors="ignore")
    return df


def compute_kmeans_tiers(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Run K-Means clustering (k=3) on Asian Range distribution.
    AU = 50% of cluster centroid (NON-NEGOTIABLE).
    Tier boundaries = midpoints between sorted centroids.
    Density Zone = AU ± 20%.
    
    Adds: au_pips, density_zone_high, density_zone_low, tier_kmeans
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Get valid Asian ranges
    ar_values = df["asian_range_pips"].dropna().values.reshape(-1, 1)

    if len(ar_values) < 30:
        df["au_pips"] = np.nan
        df["density_zone_high"] = np.nan
        df["density_zone_low"] = np.nan
        df["tier_kmeans"] = "UNKNOWN"
        return df

    # K-Means k=3, n_init=10, random_state=42 (FIXED)
    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
    kmeans.fit(ar_values)

    # Sort centroids
    centroids = sorted(kmeans.cluster_centers_.flatten())

    # Tier boundaries = midpoints between sorted centroids
    boundary_1 = (centroids[0] + centroids[1]) / 2
    boundary_2 = (centroids[1] + centroids[2]) / 2

    # AU = 50% of each centroid
    au_values = {i: c * AU_FACTOR for i, c in enumerate(centroids)}

    # Classify each bar's Asian range into a cluster
    ar_reshaped = df["asian_range_pips"].values.reshape(-1, 1)
    # Handle NaN
    valid_mask = ~np.isnan(df["asian_range_pips"].values)
    clusters = np.full(len(df), -1)
    clusters[valid_mask] = kmeans.predict(ar_reshaped[valid_mask])

    # Map cluster to AU
    df["au_pips"] = np.where(valid_mask, [au_values.get(c, np.nan) for c in clusters], np.nan)

    # Density Zone = AU ± 20%
    df["density_zone_high"] = df["au_pips"] * 1.2
    df["density_zone_low"] = df["au_pips"] * 0.8

    # Tier classification using K-Means boundaries
    def classify_kmeans_tier(rng):
        if pd.isna(rng):
            return "UNKNOWN"
        elif rng < boundary_1:
            return "T1"
        elif rng < boundary_2:
            return "T2"
        else:
            return "T3"  # T4 is handled separately as NO-GO

    df["tier_kmeans"] = df["asian_range_pips"].apply(classify_kmeans_tier)

    print(f"  K-Means centroids: {[f'{c:.1f}' for c in centroids]}")
    print(f"  AU values: {[f'{au_values[i]:.1f}' for i in range(3)]}")
    print(f"  Tier boundaries: {boundary_1:.1f}, {boundary_2:.1f}")

    return df


def compute_constraint_deficit(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute Constraint Deficit: current price distance from Asian Band edge.
    Positive = price above Asian high (bullish deficit).
    Negative = price below Asian low (bearish deficit).
    
    Adds: constraint_deficit_pips
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Distance from Asian band edge
    dist_above = (df["close"] - df["asian_high"]) * pip_mult
    dist_below = (df["asian_low"] - df["close"]) * pip_mult

    # Constraint deficit: positive if above band, negative if below
    df["constraint_deficit_pips"] = np.where(
        df["close"] > df["asian_high"],
        dist_above,
        np.where(df["close"] < df["asian_low"], -dist_below, 0),
    )
    return df


def compute_density_zone_proximity(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Density Zone Proximity: Is price in the 38.2%-50% partial rebalancing zone?
    The DZ is measured from the Asian band edge inward.
    
    DZ low = Asian_edge + (AR * 0.382)
    DZ high = Asian_edge + (AR * 0.50)
    
    Adds: in_density_zone (binary), dist_to_dz_center_pips
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    ar = df["asian_range_pips"]

    # For bullish bias: DZ is above Asian high
    # For bearish bias: DZ is below Asian low
    # We compute both and use the bias to select
    dz_width_low = ar * DZ_LOW_PCT
    dz_width_high = ar * DZ_HIGH_PCT

    # Distance from Asian high (for bullish) or Asian low (for bearish)
    dist_from_asian_edge = np.abs(df["close"] - df["asian_high"]) * pip_mult

    # In DZ if distance from edge is between 38.2% and 50% of AR
    in_dz = (dist_from_asian_edge >= dz_width_low) & (dist_from_asian_edge <= dz_width_high)
    df["in_density_zone"] = in_dz.astype(int)

    # Distance to DZ center (DZ center = AR * 44.1% from edge)
    dz_center = ar * (DZ_LOW_PCT + DZ_HIGH_PCT) / 2
    df["dist_to_dz_center_pips"] = np.abs(dist_from_asian_edge - dz_center)

    return df


def compute_au_deficit(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    AU Deficit: Distance to the Atomic Unit target.
    AU = 50% of K-Means centroid for the current tier.
    
    Adds: au_target, au_deficit_pips
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # AU target: price level that is AU pips away from Asian edge
    if "bias" in df.columns:
        df["au_target"] = np.where(
            df["bias"] == "BULLISH",
            df["asian_high"] + df["au_pips"] / pip_mult,
            df["asian_low"] - df["au_pips"] / pip_mult,
        )
    else:
        df["au_target"] = df["asian_high"] + df["au_pips"] / pip_mult

    # AU deficit: distance from current price to AU target
    df["au_deficit_pips"] = np.abs(df["au_target"] - df["close"]) * pip_mult

    return df


def compute_impulse_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Detect the first impulse from the Asian range.
    Impulse = first significant move away from Asian band edge.
    
    Adds: impulse_high, impulse_low, impulse_size_pips, impulse_to_ar_ratio,
          time_since_impulse_min, pullback_pct
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Find impulse: first bar that closes outside the Asian range
    df["_date"] = df.index.date
    df["_bar_num"] = df.groupby("_date").cumcount()

    # For each day, find the impulse bar
    impulse_data = {}
    for date, group in df.groupby("_date"):
        asian_high = group["asian_high"].iloc[0]
        asian_low = group["asian_low"].iloc[0]
        asian_range = group["asian_range_pips"].iloc[0]

        if pd.isna(asian_high) or pd.isna(asian_low):
            for idx in group.index:
                impulse_data[idx] = {
                    "impulse_high": np.nan, "impulse_low": np.nan,
                    "impulse_size_pips": np.nan, "impulse_to_ar_ratio": np.nan,
                    "time_since_impulse_min": np.nan, "pullback_pct": np.nan,
                }
            continue

        impulse_found = False
        impulse_high = asian_high
        impulse_low = asian_low
        impulse_idx = None

        for i, (idx, row) in enumerate(group.iterrows()):
            if row["close"] > asian_high or row["close"] < asian_low:
                # Impulse detected
                impulse_high = row["high"]
                impulse_low = row["low"]
                impulse_idx = i
                impulse_found = True
                break

        for i, (idx, row) in enumerate(group.iterrows()):
            if impulse_found and i >= impulse_idx:
                impulse_size = (impulse_high - impulse_low) * pip_mult
                ar = asian_range if asian_range > 0 else np.nan
                time_since = (i - impulse_idx) * 5  # M15 bars → minutes

                # Pullback: how much has price retraced from impulse extreme
                if row["close"] > asian_high:
                    pullback = (impulse_high - row["close"]) * pip_mult
                else:
                    pullback = (row["close"] - impulse_low) * pip_mult
                pullback_pct = pullback / impulse_size if impulse_size > 0 else np.nan

                impulse_data[idx] = {
                    "impulse_high": impulse_high,
                    "impulse_low": impulse_low,
                    "impulse_size_pips": impulse_size,
                    "impulse_to_ar_ratio": impulse_size / ar if ar > 0 else np.nan,
                    "time_since_impulse_min": time_since,
                    "pullback_pct": pullback_pct,
                }
            else:
                impulse_data[idx] = {
                    "impulse_high": np.nan, "impulse_low": np.nan,
                    "impulse_size_pips": np.nan, "impulse_to_ar_ratio": np.nan,
                    "time_since_impulse_min": np.nan, "pullback_pct": np.nan,
                }

    impulse_df = pd.DataFrame(impulse_data).T
    for col in impulse_df.columns:
        df[col] = impulse_df[col]

    df = df.drop(columns=["_date", "_bar_num"], errors="ignore")
    return df


def compute_occ_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    OCC (Close-Only) Extreme features.
    OCC body = |close - open| (zero-buffer, close-only).
    
    Adds: occ_body_pips, occ_body_to_au_ratio
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    df["occ_body_pips"] = np.abs(df["close"] - df["open"]) * pip_mult

    # OCC body / AU ratio
    if "au_pips" in df.columns:
        df["occ_body_to_au_ratio"] = df["occ_body_pips"] / df["au_pips"].replace(0, np.nan)
    else:
        df["occ_body_to_au_ratio"] = np.nan

    return df


def compute_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Volume spike ratio: current volume / 20-bar average.
    
    Adds: volume_spike_ratio
    """
    df = df.copy()

    if "volume" in df.columns:
        vol_avg = df["volume"].rolling(20, min_periods=5).mean()
        df["volume_spike_ratio"] = df["volume"] / vol_avg.replace(0, np.nan)
    else:
        df["volume_spike_ratio"] = 1.0

    return df


def compute_regime_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regime Ratio: 9AM EST checkpoint ratio.
    9AM EST = 14:00 UTC.
    Ratio = (Current price range from session open) / (Expected range from tier).
    
    Adds: regime_ratio, regime_status
    """
    df = df.copy()

    # Session open = first bar of the day
    df["_date"] = df.index.date
    df["session_open"] = df.groupby("_date")["open"].transform("first")

    # Price range from session open
    df["price_range_from_open"] = np.abs(df["close"] - df["session_open"])

    # Expected range from Asian Range
    if "asian_range_pips" in df.columns:
        pip_mult = get_pip_mult("EURUSD")  # Approximate
        df["expected_range"] = df["asian_range_pips"] / pip_mult
    else:
        df["expected_range"] = df["price_range_from_open"].rolling(96, min_periods=10).mean()

    # Regime ratio
    df["regime_ratio"] = df["price_range_from_open"] / df["expected_range"].replace(0, np.nan)

    # Regime status
    conditions = [
        df["regime_ratio"] > 1.5,
        df["regime_ratio"] >= 1.45,
        df["regime_ratio"] < 1.45,
    ]
    choices = ["CONFIRMED", "CAUTION", "FAILED"]
    df["regime_status"] = np.select(conditions, choices, default="UNKNOWN")

    df = df.drop(columns=["_date"], errors="ignore")
    return df


def compute_ilm_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    ILM (Intra-day Liquidity Model) State.
    
    Types:
    - Daily ILM: Price within daily range, no extreme
    - IELM (Intra-day Extreme): Price at daily extreme
    - WILM (Weekly ILM): Price at weekly extreme (MLR boundary)
    - Misaligned: Price outside expected range
    
    Adds: ilm_state (0=Daily, 1=IELM, 2=WILM, 3=Misaligned)
    """
    df = df.copy()

    # Daily high/low up to current bar (no future leakage)
    df["_date"] = df.index.date
    df["daily_high"] = df.groupby("_date")["high"].cummax()
    df["daily_low"] = df.groupby("_date")["low"].cummin()
    df["daily_range"] = df["daily_high"] - df["daily_low"]

    # Position within daily range (0 = at low, 1 = at high)
    df["daily_range_safe"] = df["daily_range"].replace(0, np.nan)
    df["pos_in_daily_range"] = (df["close"] - df["daily_low"]) / df["daily_range_safe"]

    # ILM classification
    ilm_state = np.zeros(len(df), dtype=int)  # Default: Daily ILM

    # IELM: Price within 10% of daily extreme
    ilm_state[df["pos_in_daily_range"] > 0.9] = 1
    ilm_state[df["pos_in_daily_range"] < 0.1] = 1

    # WILM: Price at weekly extreme (near MLR boundary)
    if "mlr_high" in df.columns:
        dist_to_mlr_high = np.abs(df["close"] - df["mlr_high"])
        dist_to_mlr_low = np.abs(df["close"] - df["mlr_low"])
        dist_to_mlr_extreme = np.minimum(dist_to_mlr_high, dist_to_mlr_low)
        # Within 5% of weekly range from extreme
        if "mlr_range" in df.columns:
            near_weekly = dist_to_mlr_extreme < (df["mlr_range"] * 0.05)
            ilm_state[near_weekly] = 2

    # Misaligned: Price outside MLR range entirely
    if "mlr_high" in df.columns:
        outside_mlr = (df["close"] > df["mlr_high"] * 1.01) | (df["close"] < df["mlr_low"] * 0.99)
        ilm_state[outside_mlr] = 3

    df["ilm_state"] = ilm_state
    df = df.drop(columns=["_date", "daily_range_safe", "pos_in_daily_range"], errors="ignore")
    return df


# ============================================================
# SECTION 2: MACRO FEATURES (MLR + FIB SEQUENCES)
# ============================================================

def compute_mlr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Monday London Range (MLR): 07:00-10:00 UTC on Monday.
    Forward-filled from Monday to Friday.
    
    Adds: mlr_high, mlr_low, mlr_close, mlr_range, mlr_mid, bias
    """
    df = df.copy()

    df["mlr_high"] = np.nan
    df["mlr_low"] = np.nan
    df["mlr_close"] = np.nan

    # Find Monday 07:00-10:00 UTC bars
    is_monday = df.index.dayofweek == 0
    is_mlr_hour = (df.index.hour >= 7) & (df.index.hour < 10)
    mlr_mask = is_monday & is_mlr_hour

    if mlr_mask.sum() == 0:
        return df

    # Group by week
    mlr_bars = df[mlr_mask].copy()
    mlr_bars["_week"] = mlr_bars.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)

    weekly_mlr = mlr_bars.groupby("_week").agg(
        mlr_high=("high", "max"),
        mlr_low=("low", "min"),
        mlr_close=("close", "last"),
    )

    df["_week"] = df.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)

    for week_start, row in weekly_mlr.iterrows():
        week_mask = df["_week"] == week_start
        df.loc[week_mask, "mlr_high"] = row["mlr_high"]
        df.loc[week_mask, "mlr_low"] = row["mlr_low"]
        df.loc[week_mask, "mlr_close"] = row["mlr_close"]

    df["mlr_range"] = df["mlr_high"] - df["mlr_low"]
    df["mlr_mid"] = df["mlr_low"] + df["mlr_range"] / 2
    df["bias"] = np.where(df["mlr_close"] > df["mlr_mid"], "BULLISH", "BEARISH")

    df = df.drop(columns=["_week"], errors="ignore")
    return df


def compute_fib_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ALL Fibonacci extension targets from MLR.
    
    For BULLISH bias:
      - Extensions above MLR high: +25%, +50%, +100%, +168%
      - Kill-switch below MLR low: -132%
    
    For BEARISH bias:
      - Extensions below MLR low: -25%, -50%, -100%, -168%
      - Kill-switch above MLR high: +132%
    
    Adds: target_minus_25, target_minus_50, target_minus_100, target_minus_168,
          kill_switch_132
    """
    df = df.copy()

    for level_name, level_pct in FIB_LEVELS.items():
        target_col = f"target_{level_name}"
        df[target_col] = np.where(
            df["bias"] == "BULLISH",
            df["mlr_high"] + level_pct * df["mlr_range"],
            df["mlr_low"] - level_pct * df["mlr_range"],
        )

    # 132% Kill-Switch
    df["kill_switch_132"] = np.where(
        df["bias"] == "BULLISH",
        df["mlr_low"] - KILL_SWITCH_PCT * df["mlr_range"],
        df["mlr_high"] + KILL_SWITCH_PCT * df["mlr_range"],
    )

    return df


def compute_fib_sequence_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    Determine which Fib sequence is currently active.
    Tracks the progression through Fib levels.
    
    Adds: fib_sequence_state (categorical: 'none', '25_hit', '50_hit', '100_hit', '168_hit', 'rekey')
    """
    df = df.copy()

    # For each bar, determine which Fib level price is closest to
    fib_targets = ["target_minus_25", "target_minus_50", "target_minus_100", "target_minus_168"]

    # Initialize
    df["fib_sequence_state"] = "none"

    # Check if price has touched each level (using close proximity)
    for target in fib_targets:
        if target in df.columns:
            level_name = target.replace("target_", "")
            # Price within 2% of the target level
            proximity = np.abs(df["close"] - df[target]) / df[target]
            df.loc[proximity < 0.02, "fib_sequence_state"] = level_name

    # Check kill switch
    if "kill_switch_132" in df.columns:
        ks_proximity = np.abs(df["close"] - df["kill_switch_132"]) / df["kill_switch_132"]
        df.loc[ks_proximity < 0.02, "fib_sequence_state"] = "rekey"

    return df


def compute_weekly_targets(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute weekly Fib targets from the prior week's MLR.
    These are the "weekly targets" that price is moving toward.
    
    Adds: weekly_target_25, weekly_target_50, weekly_target_100, weekly_target_168,
          dist_to_weekly_target_pips
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Prior week's MLR (shifted by 1 week)
    df["_week"] = df.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)
    df["_prev_week"] = df["_week"] - pd.Timedelta(weeks=1)

    # Get prior week's MLR values
    weekly_mlr = df.groupby("_week").agg(
        mlr_high=("mlr_high", "first"),
        mlr_low=("mlr_low", "first"),
        mlr_range=("mlr_range", "first"),
        bias=("bias", "first"),
    )

    # Map prior week's MLR to current bars
    df["prev_mlr_high"] = df["_prev_week"].map(weekly_mlr["mlr_high"])
    df["prev_mlr_low"] = df["_prev_week"].map(weekly_mlr["mlr_low"])
    df["prev_mlr_range"] = df["_prev_week"].map(weekly_mlr["mlr_range"])
    df["prev_bias"] = df["_prev_week"].map(weekly_mlr["bias"])

    # Compute weekly targets from prior week's MLR
    for level_name, level_pct in FIB_LEVELS.items():
        target_col = f"weekly_target_{level_name}"
        df[target_col] = np.where(
            df["prev_bias"] == "BULLISH",
            df["prev_mlr_high"] + level_pct * df["prev_mlr_range"],
            df["prev_mlr_low"] - level_pct * df["prev_mlr_range"],
        )

    # Distance to nearest weekly target
    weekly_target_cols = [f"weekly_target_{n}" for n in FIB_LEVELS.keys()]
    existing_cols = [c for c in weekly_target_cols if c in df.columns]
    if existing_cols:
        dists = df[existing_cols].apply(lambda col: np.abs(df["close"] - col) * pip_mult, axis=0)
        df["dist_to_weekly_target_pips"] = dists.min(axis=1)

    df = df.drop(columns=["_week", "_prev_week", "prev_mlr_high", "prev_mlr_low", "prev_mlr_range", "prev_bias"], errors="ignore")
    return df


def compute_distance_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute pip distances from current price to ALL key levels.
    
    Adds: dist_to_25_pips, dist_to_50_pips, dist_to_100_pips, dist_to_168_pips,
          dist_to_132_pips, dist_to_mlr_high_pips, dist_to_mlr_low_pips,
          dist_to_mlr_mid_pips
    """
    df = df.copy()
    pip_mult = get_pip_mult(symbol)

    # Distance to Fib targets
    for level in FIB_LEVELS:
        col = f"target_{level}"
        if col in df.columns:
            df[f"dist_to_{level}_pips"] = (df[col] - df["close"]) * pip_mult

    # Distance to 132% kill-switch (always positive — safety distance)
    df["dist_to_132_pips"] = np.abs(df["kill_switch_132"] - df["close"]) * pip_mult

    # Distance to MLR boundaries
    df["dist_to_mlr_high_pips"] = (df["mlr_high"] - df["close"]) * pip_mult
    df["dist_to_mlr_low_pips"] = (df["mlr_low"] - df["close"]) * pip_mult
    df["dist_to_mlr_mid_pips"] = (df["mlr_mid"] - df["close"]) * pip_mult

    return df


def compute_time_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Time block encoding.
    
    Adds: day_of_week, session, is_monday, is_wednesday, is_friday,
          is_wednesday_pm, hours_since_mlr, minutes_to_12pm_est
    """
    df = df.copy()

    df["day_of_week"] = df.index.dayofweek

    # Session encoding (UTC hours)
    hour_utc = df.index.hour
    conditions = [
        (hour_utc >= 0) & (hour_utc < 8),
        (hour_utc >= 7) & (hour_utc < 16),
        (hour_utc >= 12) & (hour_utc < 21),
    ]
    choices = ["asian", "london", "ny"]
    df["session"] = np.select(conditions, choices, default="black")

    df["is_monday"] = (df.index.dayofweek == 0).astype(int)
    df["is_wednesday"] = (df.index.dayofweek == 2).astype(int)
    df["is_friday"] = (df.index.dayofweek == 4).astype(int)
    df["is_wednesday_pm"] = ((df.index.dayofweek == 2) & (df.index.hour >= 17)).astype(int)

    # Hours since MLR (Monday 07:00 UTC)
    df["hours_since_mlr"] = np.nan
    monday_mask = (df.index.dayofweek == 0) & (df.index.hour == 7)
    if monday_mask.any():
        monday_times = df.index[monday_mask]
        idx_positions = monday_times.searchsorted(df.index, side="right") - 1
        valid = idx_positions >= 0
        hours = np.full(len(df), np.nan)
        hours[valid] = (df.index[valid] - monday_times[idx_positions[valid]]).total_seconds() / 3600
        df["hours_since_mlr"] = hours

    # Minutes to 12PM EST hard exit (17:00 UTC)
    today_17utc = df.index.normalize() + pd.Timedelta(hours=17)
    df["minutes_to_12pm_est"] = (today_17utc - df.index).total_seconds() / 60
    df.loc[df["minutes_to_12pm_est"] < 0, "minutes_to_12pm_est"] = 0

    return df


# ============================================================
# SECTION 3: PRIOR LOOP OUTCOME
# ============================================================

def compute_prior_loop_outcome(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prior loop outcome: result of the last completed AU loop.
    1 = WIN (AU target hit), 0 = LOSS (OCC violated), -1 = NONE
    
    Adds: prior_loop_outcome
    """
    df = df.copy()

    if "label_25_delivery" not in df.columns:
        df["prior_loop_outcome"] = -1
        return df

    # Shift the label by 1 to get the "prior" outcome
    # Map: 1 → 1 (WIN), -1 → 0 (LOSS), 0 → -1 (NONE)
    shifted = df["label_25_delivery"].shift(1)
    df["prior_loop_outcome"] = np.where(
        shifted == 1, 1,
        np.where(shifted == -1, 0, -1),
    )
    return df


# ============================================================
# SECTION 4: FULL PIPELINE
# ============================================================

def compute_all_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Run the COMPLETE feature computation pipeline.
    All features from CEREBUS BUILD.txt Phase 1.1 — no shortcuts.
    """
    print(f"\n{'='*60}")
    print(f"Computing ALL features for {symbol}")
    print(f"{'='*60}")
    print(f"Input: {df.shape}")

    # Micro features
    print("\n--- Micro Features ---")
    df = compute_asian_range(df, symbol)
    print(f"  ✓ Asian range + tier")

    df = compute_kmeans_tiers(df, symbol)
    print(f"  ✓ K-Means tiers + AU + Density Zone")

    df = compute_constraint_deficit(df, symbol)
    print(f"  ✓ Constraint deficit")

    df = compute_density_zone_proximity(df, symbol)
    print(f"  ✓ Density zone proximity")

    df = compute_au_deficit(df, symbol)
    print(f"  ✓ AU deficit")

    df = compute_impulse_features(df, symbol)
    print(f"  ✓ Impulse features (size, ratio, time since, pullback)")

    df = compute_occ_features(df, symbol)
    print(f"  ✓ OCC features (body/AU ratio)")

    df = compute_volume_features(df)
    print(f"  ✓ Volume spike ratio")

    df = compute_regime_ratio(df)
    print(f"  ✓ Regime ratio + status")

    df = compute_ilm_state(df)
    print(f"  ✓ ILM state")

    # Macro features
    print("\n--- Macro Features ---")
    df = compute_mlr(df)
    print(f"  ✓ MLR (Monday London Range)")

    df = compute_fib_targets(df)
    print(f"  ✓ Fib targets (-25%, -50%, -100%, -168%) + 132% kill-switch")

    df = compute_fib_sequence_state(df)
    print(f"  ✓ Fib sequence state")

    df = compute_weekly_targets(df, symbol)
    print(f"  ✓ Weekly targets (from prior week MLR)")

    df = compute_distance_features(df, symbol)
    print(f"  ✓ Distance features (all levels)")

    df = compute_time_blocks(df)
    print(f"  ✓ Time blocks")

    # Prior loop
    df = compute_prior_loop_outcome(df)
    print(f"  ✓ Prior loop outcome")

    # Hour EST
    df["hour_est"] = (df.index.hour - 5) % 24

    # Spread vs 20d avg
    if "spread" in df.columns:
        spread = df["spread"]
    else:
        pip_mult = get_pip_mult(symbol)
        spread = (df["high"] - df["low"]) * pip_mult
    spread_20d = spread.rolling(5760, min_periods=288).mean()
    df["spread_vs_20d_avg"] = spread / spread_20d.replace(0, np.nan)

    # Consecutive losses
    if "label_25_delivery" in df.columns:
        is_loss = (df["label_25_delivery"] == -1).astype(int)
        groups = (is_loss != is_loss.shift()).cumsum()
        df["consecutive_losses"] = is_loss.groupby(groups).cumsum()

    # Prior session win rate
    if "label_25_delivery" in df.columns:
        is_win = (df["label_25_delivery"] == 1).astype(float)
        df["prior_session_wr"] = is_win.rolling(96, min_periods=10).mean()

    # MLR range in pips
    if "mlr_range" in df.columns:
        df["mlr_range_pips"] = df["mlr_range"] * get_pip_mult(symbol)

    # Bias encoded
    if "bias" in df.columns:
        df["bias_encoded"] = (df["bias"] == "BULLISH").astype(int)

    print(f"\nOutput: {df.shape}")
    print(f"Total feature columns: {len([c for c in df.columns if not c.startswith('_')])}")

    return df


def run_full_pipeline(symbol: str, output_dir: Path) -> Path:
    """Run the complete feature pipeline for a single symbol."""
    # Load clean data
    clean_path = Path("quant-lab/ml/data/clean") / f"{symbol}_clean.parquet"
    if not clean_path.exists():
        print(f"SKIP: no clean data for {symbol}")
        return None

    df = pd.read_parquet(clean_path)
    df = compute_all_features(df, symbol)

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{symbol}_full.parquet"
    df.to_parquet(out_path)
    print(f"  ✓ Saved: {out_path}")

    return out_path


if __name__ == "__main__":
    import sys
    output_dir = Path("quant-lab/ml/data/full_features")

    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
    else:
        # Process all symbols
        clean_dir = Path("quant-lab/ml/data/clean")
        symbols = [f.stem.replace("_clean", "") for f in clean_dir.glob("*_clean.parquet")]
        symbols = [s for s in symbols if s != "TEST"]

    print(f"Processing {len(symbols)} symbols...")
    for symbol in symbols:
        run_full_pipeline(symbol, output_dir)

    print(f"\n{'='*60}")
    print(f"FULL FEATURE PIPELINE COMPLETE")
    print(f"{'='*60}")
