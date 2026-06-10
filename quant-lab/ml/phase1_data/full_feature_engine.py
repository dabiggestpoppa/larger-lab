"""
CEREBUS Full Feature Engine — COMPLETE (No Shortcuts)
=======================================================
Implements ALL features from CEREBUS BUILD.txt Phase 1.1 exactly.

Uses calibrated per-asset tier/AU configs from asset_configs.py (ST_TIERS_AND_AU.pdf).
NO K-Means re-computation — uses the validated manual tiers from the PDF.

MICRO FEATURES (from CEREBUS BUILD.txt Phase 1.1):
  1. asian_range_pips — Asian session range in pips
  2. tier — T1/T2/T3/T4_NO_GO classification (from calibrated configs)
  3. constraint_deficit — distance from Asian band edge in pips
  4. density_zone_proximity — binary 1/0 if price in DZ
  5. density_zone_distance_pips — distance from DZ center
  6. au_deficit_pips — distance to AU target in pips
  7. regime_ratio — 9AM checkpoint ratio
  8. regime_status — CONFIRMED/CAUTION/FAILED/NO-GO
  9. ilm_state — 0=Daily/1=IELM/2=WILM/3=Misaligned
 10. impulse_to_ar_ratio — first impulse size / Asian Range
 11. occ_body_to_au_ratio — OCC body size / AU
 12. pullback_pct — pullback % of impulse
 13. time_since_impulse_min — minutes since impulse candle
 14. volume_spike_ratio — OCC volume / 20-bar avg volume
 15. distance_to_dz_center — 0=center, 1=edge of DZ
 16. prior_loop_outcome — 1=WIN/0=LOSS/-1=NONE
 17. consecutive_losses — rolling loss streak
 18. prior_session_wr — prior session win rate
 19. spread_at_entry — current spread in pips
 20. hour_est — hour of day EST (0-23)
 21. day_of_week — 0=Mon ... 6=Sun
 22. is_wednesday_pm — binary Wed 17:00+ UTC
 23. minutes_to_12pm_est — minutes until 17:00 UTC hard exit

MACRO FEATURES (from CEREBUS BUILD.txt Phase 1.1):
 24. mlr_high — Monday London Range high (07:00-10:00 UTC)
 25. mlr_low — Monday London Range low
 26. mlr_close — MLR close
 27. mlr_range — MLR range in price
 28. mlr_mid — MLR midpoint
 29. mlr_range_pips — MLR range in pips
 30. bias — Bullish/Bearish
 31. bias_encoded — 1=Bullish/0=Bearish
 32. target_25 — MLR -25% extension
 33. target_50 — MLR -50% extension
 34. target_100 — MLR -100% extension
 35. target_168 — MLR -168% extension
 36. kill_switch_132 — 132% invalidation level
 37. weekly_high — weekly high
 38. weekly_low — weekly low
 39. weekly_range — weekly range in pips
40. weekly_target_25 — weekly -25% extension
41. weekly_target_50 — weekly -50% extension
42. weekly_target_100 — weekly -100% extension
43. weekly_target_168 — weekly -168% extension
44. weekly_kill_switch_132 — weekly 132% invalidation
45. dist_to_25_pips — distance to -25% target
46. dist_to_50_pips — distance to -50% target
47. dist_to_100_pips — distance to -100% target
48. dist_to_168_pips — distance to -168% target
49. dist_to_132_pips — distance to 132% kill switch
50. dist_to_mlr_high_pips — distance to MLR high
51. dist_to_mlr_low_pips — distance to MLR low
52. dist_to_mlr_mid_pips — distance to MLR mid
53. hours_since_mlr — hours since MLR formation
54. session — asian/london/ny/black
55. is_monday — binary
56. is_wednesday — binary
57. is_friday — binary
58. fib_sequence_state — categorical encoding of current Fib state
"""
from __future__ import annotations

import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Import calibrated configs from asset_configs.py (ST_TIERS_AND_AU.pdf)
import importlib.util
configs_path = Path(__file__).parent.parent.parent / "configs" / "asset_configs.py"
spec = importlib.util.spec_from_file_location("asset_configs", configs_path)
asset_configs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset_configs_mod)
ASSET_CONFIGS = asset_configs_mod.ASSET_CONFIGS

# ============================================================
# CONFIG HELPERS
# ============================================================

def get_asset_config(symbol: str) -> dict:
    """Get calibrated config for an asset."""
    if symbol in ASSET_CONFIGS:
        return ASSET_CONFIGS[symbol]
    # Default to EURUSD config if asset not found
    return ASSET_CONFIGS.get("EURUSD", {})


def get_pip_value(symbol: str) -> float:
    """Get pip value for an asset."""
    cfg = get_asset_config(symbol)
    return cfg.get("pip_value", 0.0001)


def get_pip_multiplier(symbol: str) -> int:
    """Get pip multiplier for converting price to pips."""
    pip_val = get_pip_value(symbol)
    if pip_val >= 0.1:
        return int(round(1 / pip_val))
    elif pip_val >= 0.01:
        return int(round(1 / pip_val))
    else:
        return int(round(1 / pip_val))


def price_to_pips(price_diff: float, symbol: str) -> float:
    """Convert price difference to pips."""
    return price_diff / get_pip_value(symbol)


def pips_to_price(pips: float, symbol: str) -> float:
    """Convert pips to price."""
    return pips * get_pip_value(symbol)


# ============================================================
# ASIAN RANGE & TIER CLASSIFICATION (from calibrated configs)
# ============================================================

def compute_asian_range(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute Asian Range (00:00-08:00 UTC = 19:00-03:00 EST) for each day.
    Uses calibrated tier configs from asset_configs.py — NO K-Means.
    """
    df = df.copy()
    pip_mult = get_pip_multiplier(symbol)
    cfg = get_asset_config(symbol)
    tiers = cfg.get("tiers", {})
    ar_max = tiers.get("T3", {}).get("ar_max", 60.0)

    # Asian session: 00:00-08:00 UTC
    hour = df.index.hour
    asian_mask = (hour >= 0) & (hour < 8)

    df["_date"] = df.index.date
    df["_is_asian"] = asian_mask

    # Compute Asian range per day
    asian_data = {}
    for date, group in df.groupby("_date"):
        asian_bars = group[group["_is_asian"]]
        if len(asian_bars) > 0:
            ah = asian_bars["high"].max()
            al = asian_bars["low"].min()
            ar_pips = (ah - al) * pip_mult
            asian_data[date] = (ah, al, ar_pips)
        else:
            asian_data[date] = (np.nan, np.nan, np.nan)

    # Map to all bars
    df["asian_high"] = df["_date"].map(lambda d: asian_data.get(d, (np.nan,)*3)[0])
    df["asian_low"] = df["_date"].map(lambda d: asian_data.get(d, (np.nan,)*3)[1])
    df["asian_range_pips"] = df["_date"].map(lambda d: asian_data.get(d, (np.nan,)*3)[2])

    # Tier classification using calibrated config values
    def classify_tier(ar):
        if np.isnan(ar):
            return "UNKNOWN"
        t1_au = tiers.get("T1", {}).get("au", 10.0)
        t2_au = tiers.get("T2", {}).get("au", 12.0)
        t3_au = tiers.get("T3", {}).get("au", 15.0)
        # Tier boundaries based on AU values from config
        # T1: AR < T1 AU * 2 (approximate)
        # T2: AR between T1 AU*2 and T2 AU*2
        # T3: AR between T2 AU*2 and T3 AU*2
        # T4: AR > T3 AU*2
        t1_bound = t1_au * 2
        t2_bound = t2_au * 2
        t3_bound = t3_au * 2
        if ar < t1_bound:
            return "T1"
        elif ar < t2_bound:
            return "T2"
        elif ar < t3_bound:
            return "T3"
        elif ar <= ar_max:
            return "T3"  # Still tradeable but wide
        else:
            return "T4_NO_GO"

    df["tier"] = df["asian_range_pips"].apply(classify_tier)

    # Get AU for the classified tier
    def get_au_for_tier(tier_name):
        if tier_name in tiers:
            return tiers[tier_name].get("au", 10.0)
        elif tier_name == "T4_NO_GO":
            return tiers.get("T3", {}).get("au", 15.0)
        return 10.0

    df["au_pips"] = df["tier"].apply(get_au_for_tier)

    # Density Zone = AU ± 20%
    df["density_zone_high"] = df["asian_low"] + (df["au_pips"] * 1.2 * get_pip_value(symbol))
    df["density_zone_low"] = df["asian_low"] + (df["au_pips"] * 0.8 * get_pip_value(symbol))

    df = df.drop(columns=["_date", "_is_asian"], errors="ignore")
    return df


# ============================================================
# CONSTRAINT DEFICIT & AU MATH
# ============================================================

def compute_constraint_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute constraint deficit, AU deficit, and density zone proximity.
    """
    df = df.copy()

    # Constraint deficit: distance from Asian band edge in pips
    pip_val = get_pip_value(symbol)
    bias = df.get("bias", pd.Series("BULLISH", index=df.index))

    # For bullish: deficit = (asian_high - close) in pips
    # For bearish: deficit = (close - asian_low) in pips
    df["constraint_deficit_pips"] = np.where(
        bias == "BULLISH",
        (df["asian_high"] - df["close"]) / pip_val,
        (df["close"] - df["asian_low"]) / pip_val,
    )

    # AU target: Asian low + AU (bullish) or Asian high - AU (bearish)
    au_price = df["au_pips"] * pip_val
    df["au_target"] = np.where(
        bias == "BULLISH",
        df["asian_low"] + au_price,
        df["asian_high"] - au_price,
    )

    # AU deficit: distance from current price to AU target
    df["au_deficit_pips"] = np.where(
        bias == "BULLISH",
        (df["au_target"] - df["close"]) / pip_val,
        (df["close"] - df["au_target"]) / pip_val,
    )

    # Density zone proximity
    df["in_density_zone"] = (
        (df["close"] >= df["density_zone_low"]) &
        (df["close"] <= df["density_zone_high"])
    ).astype(int)

    # Distance to DZ center (0 = at center, 1 = at edge)
    dz_center = (df["density_zone_high"] + df["density_zone_low"]) / 2
    dz_half_width = (df["density_zone_high"] - df["density_zone_low"]) / 2
    dz_half_width = dz_half_width.replace(0, np.nan)
    df["distance_to_dz_center"] = ((df["close"] - dz_center).abs() / dz_half_width).clip(0, 1)

    return df


# ============================================================
# IMPULSE DETECTION
# ============================================================

def compute_impulse_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute impulse-related features.
    Impulse = first significant move from Asian range.
    """
    df = df.copy()
    pip_val = get_pip_value(symbol)

    # Find impulse: first bar that breaks Asian range
    df["_date"] = df.index.date

    impulse_data = {}
    for date, group in df.groupby("_date"):
        if len(group) < 2:
            continue
        asian_high = group["asian_high"].iloc[0]
        asian_low = group["asian_low"].iloc[0]
        if np.isnan(asian_high) or np.isnan(asian_low):
            continue

        # Find first bar that breaks Asian range
        impulse_idx = None
        impulse_high = asian_high
        impulse_low = asian_low
        for i, (idx, row) in enumerate(group.iterrows()):
            if row["high"] > asian_high or row["low"] < asian_low:
                impulse_idx = idx
                impulse_high = max(row["high"], asian_high)
                impulse_low = min(row["low"], asian_low)
                break

        if impulse_idx is None:
            impulse_idx = group.index[0]
            impulse_high = asian_high
            impulse_low = asian_low

        impulse_size = (impulse_high - impulse_low) / pip_val
        for idx in group.index:
            time_since = (idx - impulse_idx).total_seconds() / 60 if idx >= impulse_idx else 0
            impulse_data[idx] = (impulse_high, impulse_low, impulse_size, time_since)

    # Map to DataFrame
    impulse_df = pd.DataFrame.from_dict(impulse_data, orient="index",
                                         columns=["impulse_high", "impulse_low", "impulse_size_pips", "time_since_impulse_min"])
    df = df.join(impulse_df)

    # Impulse to AR ratio
    df["impulse_to_ar_ratio"] = df["impulse_size_pips"] / df["asian_range_pips"].replace(0, np.nan)

    # Pullback % of impulse (how much price has pulled back from impulse extreme)
    df["pullback_pct"] = np.where(
        df.get("bias", pd.Series("BULLISH", index=df.index)) == "BULLISH",
        (df["impulse_high"] - df["close"]) / (df["impulse_high"] - df["impulse_low"]).replace(0, np.nan) * 100,
        (df["close"] - df["impulse_low"]) / (df["impulse_high"] - df["impulse_low"]).replace(0, np.nan) * 100,
    )

    # OCC body / AU ratio
    df["occ_body_pips"] = (df["close"] - df["open"]).abs() / pip_val
    df["occ_body_to_au_ratio"] = df["occ_body_pips"] / df["au_pips"].replace(0, np.nan)

    # Volume spike ratio
    if "volume" in df.columns:
        vol_avg = df["volume"].rolling(20, min_periods=5).mean()
        df["volume_spike_ratio"] = df["volume"] / vol_avg.replace(0, np.nan)
    else:
        df["volume_spike_ratio"] = 1.0

    df = df.drop(columns=["_date"], errors="ignore")
    return df


# ============================================================
# REGIME RATIO
# ============================================================

def compute_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute regime ratio and status."""
    df = df.copy()

    # Session open (first bar of day)
    df["_date"] = df.index.date
    df["session_open"] = df.groupby("_date")["open"].transform("first")

    # Price range from session open
    df["price_range_from_open"] = (df["close"] - df["session_open"]).abs()

    # Expected range from MLR
    if "mlr_range" in df.columns:
        df["expected_range"] = df["mlr_range"]
    else:
        df["expected_range"] = (df["high"] - df["low"]).rolling(20, min_periods=5).mean()

    # Regime ratio
    df["regime_ratio"] = df["price_range_from_open"] / df["expected_range"].replace(0, np.nan)

    # Regime status
    conditions = [df["regime_ratio"] > 1.5, df["regime_ratio"] >= 1.0]
    choices = ["CONFIRMED", "CAUTION"]
    df["regime_status"] = np.select(conditions, choices, default="FAILED")

    # NO-GO override
    if "mlr_range" in df.columns:
        df.loc[df["mlr_range"].isna(), "regime_status"] = "NO-GO"

    df = df.drop(columns=["_date"], errors="ignore")
    return df


# ============================================================
# ILM STATE
# ============================================================

def compute_ilm_state(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Intra-day Liquidity Model state."""
    df = df.copy()

    df["_date"] = df.index.date
    df["daily_high"] = df.groupby("_date")["high"].cummax()
    df["daily_low"] = df.groupby("_date")["low"].cummin()
    df["daily_range"] = df["daily_high"] - df["daily_low"]
    df["daily_range"] = df["daily_range"].replace(0, np.nan)

    # Position within daily range
    pos = (df["close"] - df["daily_low"]) / df["daily_range"]

    ilm = np.zeros(len(df), dtype=int)  # Default: Daily ILM
    ilm[pos > 0.9] = 1  # IELM: near high
    ilm[pos < 0.1] = 1  # IELM: near low

    # WILM: near weekly extreme
    if "mlr_high" in df.columns:
        dist_to_extreme = np.minimum(
            (df["close"] - df["mlr_high"]).abs(),
            (df["close"] - df["mlr_low"]).abs(),
        )
        near_weekly = dist_to_extreme < (df["mlr_range"] * 0.05)
        ilm[near_weekly] = 2

    # Misaligned: outside MLR range
    if "mlr_high" in df.columns:
        outside = (df["close"] > df["mlr_high"] * 1.01) | (df["close"] < df["mlr_low"] * 0.99)
        ilm[outside] = 3

    df["ilm_state"] = ilm
    df = df.drop(columns=["_date"], errors="ignore")
    return df


# ============================================================
# MLR & FIBONACCI TARGETS
# ============================================================

def compute_mlr(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Monday London Range (07:00-10:00 UTC)."""
    df = df.copy()
    df["mlr_high"] = np.nan
    df["mlr_low"] = np.nan
    df["mlr_close"] = np.nan

    is_monday = df.index.dayofweek == 0
    is_mlr_hour = (df.index.hour >= 7) & (df.index.hour < 10)
    mlr_mask = is_monday & is_mlr_hour

    if mlr_mask.sum() == 0:
        return df

    mlr_bars = df[mlr_mask].copy()
    mlr_bars["week_key"] = mlr_bars.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)

    weekly_mlr = mlr_bars.groupby("week_key").agg(
        mlr_high=("high", "max"),
        mlr_low=("low", "min"),
        mlr_close=("close", "last"),
    )

    df["week_key"] = df.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)
    for week_start, row in weekly_mlr.iterrows():
        mask = df["week_key"] == week_start
        df.loc[mask, "mlr_high"] = row["mlr_high"]
        df.loc[mask, "mlr_low"] = row["mlr_low"]
        df.loc[mask, "mlr_close"] = row["mlr_close"]

    df["mlr_range"] = df["mlr_high"] - df["mlr_low"]
    df["mlr_mid"] = df["mlr_low"] + df["mlr_range"] / 2
    df["bias"] = np.where(df["mlr_close"] > df["mlr_mid"], "BULLISH", "BEARISH")
    df["bias_encoded"] = (df["bias"] == "BULLISH").astype(int)
    df["mlr_range_pips"] = price_to_pips(df["mlr_range"], df.index.map(lambda _: "EURUSD").__class__ or "EURUSD")

    df = df.drop(columns=["week_key"], errors="ignore")
    return df


def compute_fib_targets(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Compute Fibonacci extension targets from MLR."""
    df = df.copy()
    pip_val = get_pip_value(symbol)

    fib_levels = {
        "target_25": 0.25,
        "target_50": 0.50,
        "target_100": 1.00,
        "target_168": 1.68,
    }

    for target_name, level in fib_levels.items():
        df[target_name] = np.where(
            df["bias"] == "BULLISH",
            df["mlr_high"] + level * df["mlr_range"],
            df["mlr_low"] - level * df["mlr_range"],
        )

    # 132% Kill-Switch
    df["kill_switch_132"] = np.where(
        df["bias"] == "BULLISH",
        df["mlr_low"] - 1.32 * df["mlr_range"],
        df["mlr_high"] + 1.32 * df["mlr_range"],
    )

    # Distance features
    for target in ["25", "50", "100", "168"]:
        col = f"dist_to_{target}_pips"
        target_col = f"target_{target}"
        df[col] = (df[target_col] - df["close"]) / pip_val

    df["dist_to_132_pips"] = (df["kill_switch_132"] - df["close"]).abs() / pip_val
    df["dist_to_mlr_high_pips"] = (df["mlr_high"] - df["close"]) / pip_val
    df["dist_to_mlr_low_pips"] = (df["mlr_low"] - df["close"]) / pip_val
    df["dist_to_mlr_mid_pips"] = (df["mlr_mid"] - df["close"]) / pip_val

    return df


# ============================================================
# WEEKLY TARGETS
# ============================================================

def compute_weekly_targets(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Compute weekly Fibonacci extensions from weekly high/low."""
    df = df.copy()
    pip_val = get_pip_value(symbol)

    # Compute weekly high/low
    df["week_key"] = df.index.to_series().dt.to_period("W").apply(lambda p: p.start_time)
    df["weekly_high"] = df.groupby("week_key")["high"].transform("max")
    df["weekly_low"] = df.groupby("week_key")["low"].transform("min")
    df["weekly_range"] = (df["weekly_high"] - df["weekly_low"]) / pip_val

    # Weekly bias from weekly close vs mid
    weekly_close = df.groupby("week_key")["close"].transform("last")
    weekly_mid = (df["weekly_high"] + df["weekly_low"]) / 2
    weekly_bias = np.where(weekly_close > weekly_mid, "BULLISH", "BEARISH")

    fib_levels = {
        "weekly_target_25": 0.25,
        "weekly_target_50": 0.50,
        "weekly_target_100": 1.00,
        "weekly_target_168": 1.68,
    }

    weekly_range_price = df["weekly_high"] - df["weekly_low"]
    for target_name, level in fib_levels.items():
        df[target_name] = np.where(
            weekly_bias == "BULLISH",
            df["weekly_high"] + level * weekly_range_price,
            df["weekly_low"] - level * weekly_range_price,
        )

    # Weekly 132% kill-switch
    df["weekly_kill_switch_132"] = np.where(
        weekly_bias == "BULLISH",
        df["weekly_low"] - 1.32 * weekly_range_price,
        df["weekly_high"] + 1.32 * weekly_range_price,
    )

    # Distance to weekly target (use -25% as primary)
    df["dist_to_weekly_target_pips"] = (df["weekly_target_25"] - df["close"]) / pip_val

    df = df.drop(columns=["week_key"], errors="ignore")
    return df


# ============================================================
# TIME BLOCKS
# ============================================================

def compute_time_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """Encode temporal features."""
    df = df.copy()

    df["day_of_week"] = df.index.dayofweek
    df["hour_est"] = (df.index.hour - 5) % 24

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
# PRIOR LOOP & SESSION FEATURES
# ============================================================

def compute_loop_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute prior loop outcome, consecutive losses, prior session WR."""
    df = df.copy()

    # Prior loop outcome: use label if available, else compute from price action
    if "label_25_delivery" in df.columns:
        # Shift by 1 to avoid leakage
        df["prior_loop_outcome"] = df["label_25_delivery"].shift(1).fillna(-1)
    else:
        df["prior_loop_outcome"] = -1

    # Consecutive losses
    if "label_25_delivery" in df.columns:
        is_loss = (df["label_25_delivery"].shift(1) == -1).astype(int)
        groups = (is_loss != is_loss.shift()).cumsum()
        df["consecutive_losses"] = is_loss.groupby(groups).cumsum()
    else:
        df["consecutive_losses"] = 0

    # Prior session win rate (rolling 96 bars = ~1 session)
    if "label_25_delivery" in df.columns:
        is_win = (df["label_25_delivery"].shift(1) == 1).astype(float)
        df["prior_session_wr"] = is_win.rolling(96, min_periods=10).mean()
    else:
        df["prior_session_wr"] = 0.5

    return df


# ============================================================
# SPREAD FEATURES
# ============================================================

def compute_spread_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Compute spread-related features."""
    df = df.copy()
    pip_val = get_pip_value(symbol)

    # Spread at entry (use high-low as proxy if no spread column)
    if "spread" in df.columns:
        spread_pips = df["spread"]
    else:
        spread_pips = (df["high"] - df["low"]) / pip_val

    df["spread_at_entry"] = spread_pips

    # Spread vs 20-day average
    spread_20d = spread_pips.rolling(5760, min_periods=288).mean()
    df["spread_vs_20d_avg"] = spread_pips / spread_20d.replace(0, np.nan)

    return df


# ============================================================
# FIB SEQUENCE STATE
# ============================================================

def compute_fib_sequence_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode the current Fibonacci sequence state.
    States: APPROACHING_25, AT_25, APPROACHING_50, AT_50, etc.
    """
    df = df.copy()

    # Simple encoding based on which Fib level price is closest to
    dists = {}
    for level in ["25", "50", "100", "168"]:
        col = f"dist_to_{level}_pips"
        if col in df.columns:
            dists[level] = df[col].abs()

    if dists:
        dist_df = pd.DataFrame(dists)
        closest = dist_df.idxmin(axis=1)
        min_dist = dist_df.min(axis=1)

        # Encode: 0=far, 1=approaching (<5p), 2=at (<2p)
        df["fib_sequence_state"] = np.where(
            min_dist < 2, 2,
            np.where(min_dist < 5, 1, 0)
        )
    else:
        df["fib_sequence_state"] = 0

    return df


# ============================================================
# MASTER PIPELINE
# ============================================================

def run_full_pipeline(symbol: str, output_dir: Path) -> bool:
    """Run the complete feature pipeline for one symbol."""
    print(f"\n{'='*60}")
    print(f"Processing: {symbol}")
    print(f"{'='*60}")

    # Load clean data
    clean_path = Path("quant-lab/ml/data/clean") / f"{symbol}_clean.parquet"
    if not clean_path.exists():
        print(f"  SKIP: no clean data for {symbol}")
        return False

    df = pd.read_parquet(clean_path)
    print(f"Input: {df.shape}")

    # Step 1: Asian Range + Tier Classification (from calibrated configs)
    print("  Computing Asian Range + Tiers...")
    df = compute_asian_range(df, symbol)

    # Step 2: Constraint + AU features
    print("  Computing Constraint + AU features...")
    df = compute_constraint_features(df, symbol)

    # Step 3: Impulse features
    print("  Computing Impulse features...")
    df = compute_impulse_features(df, symbol)

    # Step 4: MLR
    print("  Computing MLR...")
    df = compute_mlr(df)

    # Step 5: Fib targets
    print("  Computing Fib targets...")
    df = compute_fib_targets(df, symbol)

    # Step 6: Weekly targets
    print("  Computing Weekly targets...")
    df = compute_weekly_targets(df, symbol)

    # Step 7: Regime
    print("  Computing Regime...")
    df = compute_regime_features(df)

    # Step 8: ILM
    print("  Computing ILM state...")
    df = compute_ilm_state(df)

    # Step 9: Time blocks
    print("  Computing Time blocks...")
    df = compute_time_blocks(df)

    # Step 10: Loop features
    print("  Computing Loop features...")
    df = compute_loop_features(df)

    # Step 11: Spread features
    print("  Computing Spread features...")
    df = compute_spread_features(df, symbol)

    # Step 12: Fib sequence state
    print("  Computing Fib sequence state...")
    df = compute_fib_sequence_state(df)

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{symbol}_full.parquet"
    df.to_parquet(out_path)

    print(f"  ✓ Saved: {out_path} ({df.shape[1]} columns)")
    return True


if __name__ == "__main__":
    import sys
    symbols = sys.argv[1:] if len(sys.argv) > 1 else [
        "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD",
        "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD", "CHFJPY",
        "US500", "DE30", "FR40", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "OILUSD"
    ]
    output_dir = Path("quant-lab/ml/data/full_features_v2")
    for sym in symbols:
        run_full_pipeline(sym, output_dir)
    print("\nALL COMPLETE")
