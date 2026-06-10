"""
DMR (Deep Mean Reversion) Features & Labels
============================================
Based on CEREBUS FX v4 Manual Part 4: Stall-Harvest Trading System
and p90_engine_dmr.py implementation.

DMR is a nested sub-routine inside P90 IN_TRADE — NOT a separate strategy.
When P90 enters a trade, a conditional limit order is placed at the Deep State (DS):
  DS = activation_boundary + 2.0 * p90_body (opposite direction)

The DMR captures mean reversion when price extends too far from the Asian band.
This is the "stall harvest" — price stalls at the 168-200% zone and reverts.

Key Manual Data:
- 34.2% of P90s reach Stall Zone (168% within 35 min)
- 65.8% of P90s expand through (168% NOT hit)
- 86% of stall events result in profitable expansion or rebalancing
- DMR win rate: 94.8% (EUR/USD, 2022-2026, 671 trades, PF 205)
- True rejection rate: 64.2% (price rejects at stall zone and reverts)
- Deep violation rate: 14.4% (price continues past 200%)

Session Performance:
- 2-4 AM EST: 94.2% expansion WR, 31.1% stall rate
- 4-7 AM EST: 88.6% expansion WR, 35.4% stall rate
- 7-11 AM EST: 82.4% expansion WR, 38.2% stall rate

Target Trimming Matrix (by tier):
- T1 (<20p): TP1=-25%(~5p), TP2=-50%(~10p), TP3=Daily-50%(~36p), Runner=Daily-100%(~72p)
- T2 (20-30p): TP1=-25%(~6p), TP2=-50%(~12p), TP3=Daily-50%(~29p), Runner=Skip
- T3 (30-45p): TP1=-25%(~9p), TP2=-50%(~18p), TP3+=Skip
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# DMR FEATURE COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

def compute_dmr_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute DMR-related features for each bar.
    
    These features capture the Deep Mean Reversion state:
    - Distance to Deep State (200% of P90 body from Asian band)
    - Whether DMR zone has been reached
    - Time since DMR trigger
    - DMR tier classification
    - Stall zone proximity (168% level)
    
    Requires columns: asian_high, asian_low, asian_range, 
                      p90_body (if available), hour_est, day_of_week
    """
    df = df.copy()
    
    # ── 1. Deep State (200% level) ────────────────────────────────────────
    # DS = Asian band edge + 2.0 * Asian Range (approximation from AR)
    # For bullish: DS = asian_high + 2.0 * asian_range
    # For bearish: DS = asian_low - 2.0 * asian_range
    if "asian_range" in df.columns and "asian_high" in df.columns:
        df["deep_state_bull"] = df["asian_high"] + 2.0 * df["asian_range"]
        df["deep_state_bear"] = df["asian_low"] - 2.0 * df["asian_range"]
        
        # Distance to Deep State (in pips)
        pip_mult = _get_pip_multiplier(df)
        df["dist_to_ds_bull_pips"] = (df["deep_state_bull"] - df["close"]) * pip_mult
        df["dist_to_ds_bear_pips"] = (df["close"] - df["deep_state_bear"]) * pip_mult
        
        # Minimum distance to either DS
        df["dist_to_ds_min_pips"] = np.minimum(
            df["dist_to_ds_bull_pips"].abs(), 
            df["dist_to_ds_bear_pips"].abs()
        )
    
    # ── 2. Stall Zone (168% level) ────────────────────────────────────────
    # 168% = 1.68 * Asian Range from band edge
    if "asian_range" in df.columns and "asian_high" in df.columns:
        df["stall_zone_bull"] = df["asian_high"] + 1.68 * df["asian_range"]
        df["stall_zone_bear"] = df["asian_low"] - 1.68 * df["asian_range"]
        
        df["dist_to_stall_bull_pips"] = (df["stall_zone_bull"] - df["close"]) * pip_mult
        df["dist_to_stall_bear_pips"] = (df["close"] - df["stall_zone_bear"]) * pip_mult
        df["dist_to_stall_min_pips"] = np.minimum(
            df["dist_to_stall_bull_pips"].abs(),
            df["dist_to_stall_bear_pips"].abs()
        )
    
    # ── 3. DMR Tier Classification ───────────────────────────────────────
    # Based on Asian Range size (same as ST tiers)
    if "asian_range_pips" in df.columns:
        ar = df["asian_range_pips"]
        conditions = [ar < 20.0, ar < 30.0, ar < 45.0]
        df["dmr_tier"] = np.select(conditions, [1, 2, 3], default=0).astype(int)
    elif "asian_range" in df.columns:
        ar_pips = df["asian_range"] * pip_mult
        conditions = [ar_pips < 20.0, ar_pips < 30.0, ar_pips < 45.0]
        df["dmr_tier"] = np.select(conditions, [1, 2, 3], default=0).astype(int)
    
    # ── 4. DMR Timing Features ────────────────────────────────────────────
    if "hour_est" in df.columns:
        h = df["hour_est"]
        # Peak DMR windows (from manual)
        df["dmr_window_2_4am"] = ((h >= 2) & (h < 4)).astype(int)  # 94.2% WR
        df["dmr_window_4_7am"] = ((h >= 4) & (h < 7)).astype(int)  # 88.6% WR
        df["dmr_window_7_11am"] = ((h >= 7) & (h < 11)).astype(int)  # 82.4% WR
        df["dmr_window_post_11am"] = (h >= 11).astype(int)  # No new activations
        
        # Time-based stall rate (from manual)
        df["dmr_stall_rate"] = np.where(
            df["dmr_window_2_4am"] == 1, 0.311,
            np.where(
                df["dmr_window_4_7am"] == 1, 0.354,
                np.where(df["dmr_window_7_11am"] == 1, 0.382, 0.0)
            )
        )
        
        # Time-based expansion WR (from manual)
        df["dmr_expansion_wr"] = np.where(
            df["dmr_window_2_4am"] == 1, 0.942,
            np.where(
                df["dmr_window_4_7am"] == 1, 0.886,
                np.where(df["dmr_window_7_11am"] == 1, 0.824, 0.0)
            )
        )
    
    # ── 5. DMR Proximity Score ────────────────────────────────────────────
    # How close is price to the DMR trigger zone (0-1 scale)
    if "dist_to_ds_min_pips" in df.columns:
        # Within 10 pips = high proximity
        df["dmr_proximity_score"] = np.clip(1.0 - (df["dist_to_ds_min_pips"] / 50.0), 0.0, 1.0)
    
    if "dist_to_stall_min_pips" in df.columns:
        df["stall_proximity_score"] = np.clip(1.0 - (df["dist_to_stall_min_pips"] / 40.0), 0.0, 1.0)
    
    # ── 6. Kill Switch Proximity (132%) ───────────────────────────────────
    if "asian_range" in df.columns and "asian_high" in df.columns:
        df["kill_switch_bull"] = df["asian_high"] + 1.32 * df["asian_range"]
        df["kill_switch_bear"] = df["asian_low"] - 1.32 * df["asian_range"]
        
        df["dist_to_ks_bull_pips"] = (df["kill_switch_bull"] - df["close"]) * pip_mult
        df["dist_to_ks_bear_pips"] = (df["close"] - df["kill_switch_bear"]) * pip_mult
        df["dist_to_ks_min_pips"] = np.minimum(
            df["dist_to_ks_bull_pips"].abs(),
            df["dist_to_ks_bear_pips"].abs()
        )
    
    return df


def compute_dmr_labels(df: pd.DataFrame, forward_bars: int = 288) -> pd.DataFrame:
    """
    Compute DMR training labels for each bar.
    
    Labels capture the temporal delivery sequence:
    1. label_dmrhit_25: Did -25% AR hit within forward window? (0/1)
    2. label_dmrhit_50: Did -50% AR hit? (0/1)
    3. label_dmrhit_100: Did -100% AR hit? (0/1)
    4. label_dmr_stall: Did price reach stall zone (168%)? (0/1)
    5. label_dmr_deep: Did price reach deep state (200%)? (0/1)
    6. label_dmr_revert: Did price revert back to Asian band after stall? (0/1)
    7. label_dmr_time_to_25: Time (bars) to -25% hit (capped at forward_bars)
    8. label_dmr_time_to_50: Time (bars) to -50% hit
    9. label_dmr_time_to_100: Time (bars) to -100% hit
    10. label_dmr_outcome: 0=NO_STALL, 1=STALL_REVERT, 2=DEEP_CONTINUE, 3=FULL_EXTENSION
    
    The outcome label captures the 4 resolution paths from the manual:
    - NO_STALL (0): Price didn't reach stall zone — full extension
    - STALL_REVERT (1): Price reached stall and reverted (64.2% of stalls)
    - DEEP_CONTINUE (2): Price reached 200% but continued (14.4%)
    - FULL_EXTENSION (3): Price expanded through all targets
    """
    df = df.copy()
    
    n = len(df)
    
    # Initialize labels
    df["label_dmrhit_25"] = 0
    df["label_dmrhit_50"] = 0
    df["label_dmrhit_100"] = 0
    df["label_dmr_stall"] = 0
    df["label_dmr_deep"] = 0
    df["label_dmr_revert"] = 0
    df["label_dmr_time_to_25"] = forward_bars
    df["label_dmr_time_to_50"] = forward_bars
    df["label_dmr_time_to_100"] = forward_bars
    df["label_dmr_outcome"] = 0
    
    # Compute forward-looking labels for each bar
    # This is O(n * forward_bars) — use vectorized operations for speed
    
    if "asian_range" not in df.columns or "asian_high" not in df.columns:
        return df
    
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    ar = df["asian_range"].values
    ah = df["asian_high"].values
    al = df["asian_low"].values
    
    # Target levels (from current bar's Asian Range)
    target_25_bull = ah + 0.25 * ar  # -25% extension above
    target_25_bear = al - 0.25 * ar  # -25% extension below
    target_50_bull = ah + 0.50 * ar
    target_50_bear = al - 0.50 * ar
    target_100_bull = ah + 1.00 * ar
    target_100_bear = al - 1.00 * ar
    
    # Stall zone (168%)
    stall_bull = ah + 1.68 * ar
    stall_bear = al - 1.68 * ar
    
    # Deep state (200%)
    ds_bull = ah + 2.0 * ar
    ds_bear = al - 2.0 * ar
    
    for i in range(n):
        end = min(i + forward_bars, n)
        if end <= i:
            continue
        
        fwd_high = high[i:end]
        fwd_low = low[i:end]
        fwd_close = close[i:end]
        
        # Check if targets hit (wick reach)
        hit_25_bull = np.any(fwd_high >= target_25_bull[i])
        hit_25_bear = np.any(fwd_low <= target_25_bear[i])
        hit_50_bull = np.any(fwd_high >= target_50_bull[i])
        hit_50_bear = np.any(fwd_low <= target_50_bear[i])
        hit_100_bull = np.any(fwd_high >= target_100_bull[i])
        hit_100_bear = np.any(fwd_low <= target_100_bear[i])
        
        # Stall zone hit
        hit_stall_bull = np.any(fwd_high >= stall_bull[i])
        hit_stall_bear = np.any(fwd_low <= stall_bear[i])
        hit_stall = hit_stall_bull or hit_stall_bear
        
        # Deep state hit
        hit_ds_bull = np.any(fwd_high >= ds_bull[i])
        hit_ds_bear = np.any(fwd_low <= ds_bear[i])
        hit_ds = hit_ds_bull or hit_ds_bear
        
        # Set binary labels
        df.iloc[i, df.columns.get_loc("label_dmrhit_25")] = int(hit_25_bull or hit_25_bear)
        df.iloc[i, df.columns.get_loc("label_dmrhit_50")] = int(hit_50_bull or hit_50_bear)
        df.iloc[i, df.columns.get_loc("label_dmrhit_100")] = int(hit_100_bull or hit_100_bear)
        df.iloc[i, df.columns.get_loc("label_dmr_stall")] = int(hit_stall)
        df.iloc[i, df.columns.get_loc("label_dmr_deep")] = int(hit_ds)
        
        # Time to hit (bars)
        if hit_25_bull:
            t25 = np.argmax(fwd_high >= target_25_bull[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_25")] = t25
        if hit_25_bear:
            t25 = np.argmax(fwd_low <= target_25_bear[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_25")] = min(
                df.iloc[i, df.columns.get_loc("label_dmr_time_to_25")], t25
            )
        
        if hit_50_bull:
            t50 = np.argmax(fwd_high >= target_50_bull[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_50")] = t50
        if hit_50_bear:
            t50 = np.argmax(fwd_low <= target_50_bear[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_50")] = min(
                df.iloc[i, df.columns.get_loc("label_dmr_time_to_50")], t50
            )
        
        if hit_100_bull:
            t100 = np.argmax(fwd_high >= target_100_bull[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_100")] = t100
        if hit_100_bear:
            t100 = np.argmax(fwd_low <= target_100_bear[i])
            df.iloc[i, df.columns.get_loc("label_dmr_time_to_100")] = min(
                df.iloc[i, df.columns.get_loc("label_dmr_time_to_100")], t100
            )
        
        # Revert check: after stall hit, did price come back to Asian band?
        if hit_stall:
            stall_idx = np.argmax(fwd_high >= stall_bull[i]) if hit_stall_bull else np.argmax(fwd_low <= stall_bear[i])
            if stall_idx < end - i - 1:
                post_stall = fwd_close[stall_idx:]
                revert_bull = np.any(post_stall <= ah[i])  # Came back to Asian high
                revert_bear = np.any(post_stall >= al[i])  # Came back to Asian low
                df.iloc[i, df.columns.get_loc("label_dmr_revert")] = int(revert_bull or revert_bear)
        
        # Outcome classification
        if not hit_stall:
            df.iloc[i, df.columns.get_loc("label_dmr_outcome")] = 0  # NO_STALL
        elif hit_ds:
            df.iloc[i, df.columns.get_loc("label_dmr_outcome")] = 2  # DEEP_CONTINUE
        elif df.iloc[i, df.columns.get_loc("label_dmr_revert")] == 1:
            df.iloc[i, df.columns.get_loc("label_dmr_outcome")] = 1  # STALL_REVERT
        else:
            df.iloc[i, df.columns.get_loc("label_dmr_outcome")] = 3  # FULL_EXTENSION
    
    return df


def _get_pip_multiplier(df: pd.DataFrame) -> float:
    """Get pip multiplier from symbol or default to 10000."""
    # Try to infer from column values
    if "asian_range" in df.columns:
        ar_median = df["asian_range"].median()
        if ar_median > 0.5:
            return 100.0   # JPY pairs
        elif ar_median > 0.05:
            return 10000.0  # Standard FX
        else:
            return 10000.0
    return 10000.0
