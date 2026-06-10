"""
Label Generator v3 — Temporal Delivery Prediction
===================================================
Predicts WHEN each Fib target (-25%, -50%, -100%) will be hit within the MLR week,
with real-time state tracking as the week progresses.

Per CEREBUS Ontology + Holy Grail temporal delivery patterns:
- Monday: Anchor set (0% and 100% levels from London Range)
- Tuesday-Wednesday: -25% delivery window (98.22% hit rate by Wed close)
- Wednesday-Thursday: -50% delivery window (96.44% hit rate by Thu close)
- Thursday-Friday: -100% delivery window (92.17% hit rate by Fri close)
- 132% violation: 71.53% weekly rate, triggers rekey sequence

Labels are forward-looking and time-aware:
- At each bar, predict: will -25% hit today? will -50% hit this week? etc.
- Track elapsed time since MLR anchor
- Track which targets have already been hit
- Track remaining time to 12PM hard exit
- Track rekey state (normal / rekey triggered / rekey in progress)

GATE: No future leakage. Labels only use data available at prediction time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from enum import IntEnum
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPORAL DELIVERY WINDOWS (from Holy Grail)
# ═══════════════════════════════════════════════════════════════════════════════

# Hit rates by day window (from Holy Grail Hit Rate Analysis Framework)
# These are the probabilities that a given Fib level will be hit BY that day
FIB_HIT_RATES = {
    "ext_25": {"tuesday": 0.68, "wednesday": 0.85, "thursday": 0.92, "friday": 0.9822},
    "ext_50": {"wednesday": 0.70, "thursday": 0.88, "friday": 0.9644},
    "ext_100": {"thursday": 0.75, "friday": 0.9217},
    "ext_168": {"friday": 0.8719},
}

# Average time to hit (hours from Monday 07:00 UTC)
AVG_TIME_TO_HIT = {
    "ext_25": 24,   # ~24 hours from Monday open
    "ext_50": 39,   # ~39 hours
    "ext_100": 60,  # ~60 hours
    "ext_168": 84,  # ~84 hours
}

# 132% violation timing
VIOLATION_132 = {
    "weekly_rate": 0.7153,
    "peak_day": "wednesday",
    "peak_session": "london_ny_overlap",  # 14:00-18:00 UTC
    "avg_time_to_violation_hrs": 33,
    "rekey_success_rate": 1.0,  # 100% rekey after violation
    "rekey_78_6_retrace_prob": 0.92,
    "rekey_50_consolidation_prob": 0.85,
    "rekey_completion_prob": 0.78,
}


class RekeyState(IntEnum):
    """Track the rekey state machine."""
    NORMAL = 0
    VIOLATION_DETECTED = 1
    RETRACE_78_6 = 2
    CONSOLIDATION_50 = 3
    NEW_DELIVERY = 4
    COMPLETE = 5


class DeliveryTarget(IntEnum):
    """Which Fib extension target."""
    NONE = 0
    EXT_25 = 1
    EXT_50 = 2
    EXT_100 = 3
    EXT_168 = 4


# ═══════════════════════════════════════════════════════════════════════════════
# LABEL GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_temporal_labels(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute temporal delivery labels for each bar.
    
    For each bar, predicts:
    1. Will -25% be hit by end of today? (binary)
    2. Will -25% be hit by Friday close this week? (binary)
    3. Will -50% be hit by Friday close this week? (binary)
    4. Will -100% be hit by Friday close this week? (binary)
    5. Will 132% be violated this week? (binary)
    6. Hours until -25% hit (regression, -1 if won't hit)
    7. Hours until -50% hit (regression, -1 if won't hit)
    8. Hours until -100% hit (regression, -1 if won't hit)
    9. Current rekey state (categorical)
    10. Next target to hit (categorical: -25/-50/-100/132/none)
    11. Time since MLR anchor (hours)
    12. Time to 12PM hard exit (minutes)
    13. Delivery progress (% of weekly targets hit so far)
    
    All labels are forward-looking — they only use data available at prediction time.
    """
    df = df.copy()
    
    # Ensure we have the required columns
    required = ["mlr_high", "mlr_low", "mlr_close", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan
    
    # Compute Fib extension levels from MLR
    df["mlr_range"] = df["mlr_high"] - df["mlr_low"]
    
    # Bullish: extensions above high; Bearish: extensions below low
    df["bias"] = np.where(df["mlr_close"] > (df["mlr_high"] + df["mlr_low"]) / 2, "BULLISH", "BEARISH")
    
    # Fib levels depend on bias
    is_bullish = df["bias"] == "BULLISH"
    df["fib_25"] = np.where(is_bullish, df["mlr_high"] + df["mlr_range"] * 0.25, df["mlr_low"] - df["mlr_range"] * 0.25)
    df["fib_50"] = np.where(is_bullish, df["mlr_high"] + df["mlr_range"] * 0.50, df["mlr_low"] - df["mlr_range"] * 0.50)
    df["fib_100"] = np.where(is_bullish, df["mlr_high"] + df["mlr_range"] * 1.00, df["mlr_low"] - df["mlr_range"] * 1.00)
    df["fib_168"] = np.where(is_bullish, df["mlr_high"] + df["mlr_range"] * 1.68, df["mlr_low"] - df["mlr_range"] * 1.68)
    df["kill_switch_132"] = np.where(is_bullish, df["mlr_low"] - df["mlr_range"] * 1.32, df["mlr_high"] + df["mlr_range"] * 1.32)
    
    # ── Week identification ──
    # Group bars by week (Monday-Friday)
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    est = idx.tz_convert("America/New_York")
    df["day_of_week"] = est.dayofweek
    df["hour_est"] = est.hour
    
    # Week key: Monday date for each bar
    df["week_key"] = pd.Series(est.date, index=df.index)
    # Adjust: if Sunday (day 6), belongs to next week
    df.loc[df["day_of_week"] == 6, "week_key"] = pd.Series(
        (est[df["day_of_week"] == 6] + pd.Timedelta(days=1)).date,
        index=df.index[df["day_of_week"] == 6]
    )
    
    # ── Forward-looking labels (computed per week) ──
    # For each week, look at the FULL week's data to create labels
    # Then assign those labels to each bar in the week
    
    # Initialize label columns
    label_cols = [
        "label_25_today", "label_25_week", "label_50_week", "label_100_week",
        "label_132_week", "hours_to_25", "hours_to_50", "hours_to_100",
        "rekey_state", "next_target", "hours_since_mlr", "minutes_to_12pm",
        "delivery_progress_pct", "targets_hit_count", "is_rekey_week",
        "time_in_current_phase_min",
    ]
    for col in label_cols:
        df[col] = np.nan
    
    # Process each week
    for week_start, week_df in df.groupby("week_key"):
        if len(week_df) < 10:
            continue
        
        week_idx = week_df.index
        
        # Get this week's price data
        week_highs = week_df["high"].values
        week_lows = week_df["low"].values
        week_closes = week_df["close"].values
        
        # Fib levels (constant for the week, from Monday MLR)
        fib_25 = week_df["fib_25"].iloc[0]
        fib_50 = week_df["fib_50"].iloc[0]
        fib_100 = week_df["fib_100"].iloc[0]
        fib_168 = week_df["fib_168"].iloc[0]
        kill_132 = week_df["kill_switch_132"].iloc[0]
        bias = week_df["bias"].iloc[0]
        
        # Determine which targets were hit during the week
        if bias == "BULLISH":
            hit_25 = np.any(week_highs >= fib_25)
            hit_50 = np.any(week_highs >= fib_50)
            hit_100 = np.any(week_highs >= fib_100)
            hit_168 = np.any(week_highs >= fib_168)
            viol_132 = np.any(week_lows <= kill_132)
        else:
            hit_25 = np.any(week_lows <= fib_25)
            hit_50 = np.any(week_lows <= fib_50)
            hit_100 = np.any(week_lows <= fib_100)
            hit_168 = np.any(week_lows <= fib_168)
            viol_132 = np.any(week_highs >= kill_132)
        
        # Find WHEN each target was hit (bar index within week)
        if bias == "BULLISH":
            idx_25 = np.argmax(week_highs >= fib_25) if hit_25 else -1
            idx_50 = np.argmax(week_highs >= fib_50) if hit_50 else -1
            idx_100 = np.argmax(week_highs >= fib_100) if hit_100 else -1
            idx_132 = np.argmax(week_lows <= kill_132) if viol_132 else -1
        else:
            idx_25 = np.argmax(week_lows <= fib_25) if hit_25 else -1
            idx_50 = np.argmax(week_lows <= fib_50) if hit_50 else -1
            idx_100 = np.argmax(week_lows <= fib_100) if hit_100 else -1
            idx_132 = np.argmax(week_highs >= kill_132) if viol_132 else -1
        
        # Convert bar indices to hours from week start
        hours_to_25 = idx_25 * 0.25 if idx_25 >= 0 else -1  # M5 bars = 0.25 hrs
        hours_to_50 = idx_50 * 0.25 if idx_50 >= 0 else -1
        hours_to_100 = idx_100 * 0.25 if idx_100 >= 0 else -1
        
        # Rekey state
        is_rekey_week = viol_132
        rekey_state = RekeyState.VIOLATION_DETECTED if viol_132 else RekeyState.NORMAL
        
        # Targets hit count
        targets_hit = sum([hit_25, hit_50, hit_100])
        
        # ── Per-bar labels ──
        for i, bar_idx in enumerate(week_idx):
            # Time since MLR anchor (Monday 07:00 UTC)
            bar_time = bar_idx
            monday_start = week_idx[0]
            hours_since_mlr = (bar_time - monday_start).total_seconds() / 3600
            
            # Time to 12PM EST hard exit
            est_time = bar_time.tz_convert("America/New_York") if bar_time.tz else bar_time
            today_12pm = est_time.normalize() + pd.Timedelta(hours=12)
            if est_time > today_12pm:
                today_12pm += pd.Timedelta(days=1)
            minutes_to_12pm = (today_12pm - est_time).total_seconds() / 60
            
            # Labels that change as the week progresses
            # At bar i, we know what's happened so far but not what will happen
            
            # What's been hit SO FAR (up to this bar)
            if bias == "BULLISH":
                hit_25_so_far = np.any(week_highs[:i+1] >= fib_25)
                hit_50_so_far = np.any(week_highs[:i+1] >= fib_50)
                hit_100_so_far = np.any(week_highs[:i+1] >= fib_100)
                viol_132_so_far = np.any(week_lows[:i+1] <= kill_132)
            else:
                hit_25_so_far = np.any(week_lows[:i+1] <= fib_25)
                hit_50_so_far = np.any(week_lows[:i+1] <= fib_50)
                hit_100_so_far = np.any(week_lows[:i+1] <= fib_100)
                viol_132_so_far = np.any(week_highs[:i+1] >= kill_132)
            
            # Will -25% be hit by end of TODAY?
            # Look at remaining bars in today's session
            today_mask = (pd.Series(est.date, index=week_idx) == est_time.date())
            today_bars = np.where(today_mask.values)[0]
            remaining_today = today_bars[today_bars >= i] if len(today_bars) > 0 else []
            
            if hit_25_so_far:
                label_25_today = 1  # Already hit
            elif len(remaining_today) > 0:
                # Will it hit in remaining bars today?
                if bias == "BULLISH":
                    label_25_today = 1 if np.any(week_highs[remaining_today] >= fib_25) else 0
                else:
                    label_25_today = 1 if np.any(week_lows[remaining_today] <= fib_25) else 0
            else:
                label_25_today = 0
            
            # Will -25% be hit by Friday close? (full week label)
            df.loc[bar_idx, "label_25_week"] = 1 if hit_25 else 0
            df.loc[bar_idx, "label_50_week"] = 1 if hit_50 else 0
            df.loc[bar_idx, "label_100_week"] = 1 if hit_100 else 0
            df.loc[bar_idx, "label_132_week"] = 1 if viol_132 else 0
            
            # Hours to hit (only for bars BEFORE the hit)
            if not hit_25_so_far and hit_25:
                df.loc[bar_idx, "hours_to_25"] = hours_to_25 - hours_since_mlr
            elif hit_25_so_far:
                df.loc[bar_idx, "hours_to_25"] = 0  # Already hit
            else:
                df.loc[bar_idx, "hours_to_25"] = -1  # Won't hit this week
            
            if not hit_50_so_far and hit_50:
                df.loc[bar_idx, "hours_to_50"] = hours_to_50 - hours_since_mlr
            elif hit_50_so_far:
                df.loc[bar_idx, "hours_to_50"] = 0
            else:
                df.loc[bar_idx, "hours_to_50"] = -1
            
            if not hit_100_so_far and hit_100:
                df.loc[bar_idx, "hours_to_100"] = idx_100 * 0.25 - hours_since_mlr
            elif hit_100_so_far:
                df.loc[bar_idx, "hours_to_100"] = 0
            else:
                df.loc[bar_idx, "hours_to_100"] = -1
            
            # Rekey state
            if viol_132_so_far:
                df.loc[bar_idx, "rekey_state"] = RekeyState.VIOLATION_DETECTED
            else:
                df.loc[bar_idx, "rekey_state"] = RekeyState.NORMAL
            
            # Next target to hit
            if not hit_25_so_far:
                df.loc[bar_idx, "next_target"] = DeliveryTarget.EXT_25
            elif not hit_50_so_far:
                df.loc[bar_idx, "next_target"] = DeliveryTarget.EXT_50
            elif not hit_100_so_far:
                df.loc[bar_idx, "next_target"] = DeliveryTarget.EXT_100
            else:
                df.loc[bar_idx, "next_target"] = DeliveryTarget.NONE
            
            # Time features
            df.loc[bar_idx, "hours_since_mlr"] = hours_since_mlr
            df.loc[bar_idx, "minutes_to_12pm"] = minutes_to_12pm
            
            # Delivery progress
            targets_hit_so_far = sum([hit_25_so_far, hit_50_so_far, hit_100_so_far])
            df.loc[bar_idx, "targets_hit_count"] = targets_hit_so_far
            df.loc[bar_idx, "delivery_progress_pct"] = targets_hit_so_far / 3.0 * 100
            
            # Rekey week flag
            df.loc[bar_idx, "is_rekey_week"] = 1 if is_rekey_week else 0
            
            # Time in current phase (minutes since last target hit or week start)
            if hit_25_so_far and idx_25 >= 0:
                bars_since_25 = i - idx_25
            else:
                bars_since_25 = i  # Bars since week start
            df.loc[bar_idx, "time_in_current_phase_min"] = bars_since_25 * 5  # M5 bars
    
    return df


def compute_intraday_labels(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute intraday-specific labels for each bar.
    
    Per CEREBUS Ontology Section 8 (Entry/Trade Mechanics):
    - Each intraday session has its own AU target
    - Asian Range defines the daily constraint deficit
    - Activation window (03:00-12:00 EST) is when resolution is permitted
    - 12PM hard exit terminates all pathways
    
    Labels:
    1. Will today's -25% intraday target be hit before 12PM? (binary)
    2. Will today's -50% intraday target be hit before 12PM? (binary)
    3. Time to intraday -25% hit (minutes, -1 if won't hit)
    4. Intraday delivery phase (0=pre-activation, 1=activation, 2=delivery, 3=completion)
    5. Bars remaining to 12PM exit
    6. Intraday rekey triggered (binary)
    """
    df = df.copy()
    
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    est = idx.tz_convert("America/New_York")
    
    df["hour_est"] = est.hour
    df["minute_est"] = est.minute
    df["day_of_week"] = est.dayofweek
    
    # Session classification
    df["session"] = "other"
    df.loc[(df["hour_est"] >= 19) | (df["hour_est"] < 3), "session"] = "asian"
    df.loc[(df["hour_est"] >= 3) & (df["hour_est"] < 12), "session"] = "activation"
    df.loc[(df["hour_est"] >= 12) & (df["hour_est"] < 16), "session"] = "ny"
    
    # Intraday delivery phase
    df["intraday_phase"] = 0
    df.loc[df["session"] == "asian", "intraday_phase"] = 0  # Pre-activation
    df.loc[(df["session"] == "activation") & (df["hour_est"] < 7), "intraday_phase"] = 1  # Early activation
    df.loc[(df["session"] == "activation") & (df["hour_est"] >= 7), "intraday_phase"] = 2  # Delivery
    df.loc[df["session"] == "ny", "intraday_phase"] = 3  # Completion
    
    # Bars remaining to 12PM EST
    today_12pm = pd.Series(est.date, index=df.index).apply(
        lambda d: pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=12)
    )
    df["bars_to_12pm"] = ((today_12pm - pd.Series(est, index=df.index)).dt.total_seconds() / 300).astype(int)
    df.loc[df["bars_to_12pm"] < 0, "bars_to_12pm"] = 0
    
    # Intraday rekey detection
    # Per Holy Grail: rekey triggered when price violates 132% of daily range
    if "kill_switch_132" in df.columns:
        is_bullish = df.get("bias", pd.Series("BULLISH", index=df.index)) == "BULLISH"
        df["intraday_rekey"] = np.where(
            is_bullish,
            (df["low"] <= df["kill_switch_132"]).astype(int),
            (df["high"] >= df["kill_switch_132"]).astype(int)
        )
    else:
        df["intraday_rekey"] = 0
    
    return df


def generate_all_labels(symbol: str) -> pd.DataFrame | None:
    """
    Generate complete label set for a symbol.
    Combines weekly MLR labels + intraday labels.
    """
    # Load the feature matrix
    features_path = Path(__file__).parent.parent / "data" / "features" / f"{symbol}_features.parquet"
    labels_path = Path(__file__).parent.parent / "data" / "labels" / f"{symbol}_labeled.parquet"
    
    if not labels_path.exists():
        print(f"  SKIP {symbol}: no labels file")
        return None
    
    df = pd.read_parquet(labels_path)
    
    # Add temporal labels
    df = compute_temporal_labels(df, symbol)
    df = compute_intraday_labels(df, symbol)
    
    # Save
    out_path = Path(__file__).parent.parent / "data" / "labels" / f"{symbol}_labeled_v3.parquet"
    df.to_parquet(out_path)
    print(f"  {symbol}: {len(df)} rows, saved to {out_path}")
    
    return df


if __name__ == "__main__":
    symbols = [f.stem.replace("_labeled", "") for f in Path("quant-lab/ml/data/labels").glob("*_labeled.parquet")]
    symbols = [s for s in symbols if s != "TEST"]
    
    for symbol in symbols:
        generate_all_labels(symbol)
    
    print(f"\nLabel generation complete for {len(symbols)} symbols")
