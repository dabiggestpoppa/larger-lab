"""
132% Kill-Switch Engine
========================
Per CEREBUS v4 Manual:
- 98% of bifurcated days trigger a 132% violation
- Wednesday = HIGH ALERT (35% of all 132% violations)
- If 132% breached -> EXIT immediately, wait for 78.6% rekey retest
- The distance to 132% MUST be a top-5 SHAP feature (Ironclad Rule #3)

This module computes:
- Proximity to 132% kill-switch
- Rekey state machine (normal -> approaching -> breached -> rekey_sequence)
- Wednesday PM bifurcation flag
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from enum import IntEnum


class RekeyState(IntEnum):
    """State machine for 132% kill-switch monitoring."""
    NORMAL = 0
    APPROACHING = 1
    CRITICAL = 2
    BREACHED = 3
    REKEY_SEQUENCE = 4


APPROACH_THRESHOLD_PIPS = 30.0
CRITICAL_THRESHOLD_PIPS = 15.0


def compute_132_proximity(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
    approach_threshold: float = APPROACH_THRESHOLD_PIPS,
    critical_threshold: float = CRITICAL_THRESHOLD_PIPS,
) -> pd.DataFrame:
    """
    Compute 132% kill-switch proximity features.

    Adds columns:
        - dist_to_132_pips: Distance to 132% level in pips
        - pct_to_132: Distance as % of MLR range
        - is_near_132: Binary flag (1 if < approach_threshold pips)
        - is_critical_132: Binary flag (1 if < critical_threshold pips)
    """
    df = df.copy()

    df['dist_to_132_pips'] = df['dist_to_132_pct'] / pip_size

    df['pct_to_132'] = np.where(
        df['mlr_range'] > 0,
        df['dist_to_132_pct'] / df['mlr_range'],
        np.nan
    )

    df['is_near_132'] = (df['dist_to_132_pips'] < approach_threshold).astype(int)
    df['is_critical_132'] = (df['dist_to_132_pips'] < critical_threshold).astype(int)

    return df


def compute_rekey_state(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
) -> pd.DataFrame:
    """
    Compute the rekey state machine for each bar.

    Tracks the progression: NORMAL -> APPROACHING -> CRITICAL -> BREACHED -> REKEY_SEQUENCE

    REKEY_SEQUENCE logic: Once a 132% breach occurs on a given trading day,
    all subsequent bars on that same day transition to REKEY_SEQUENCE.
    The breached bar itself remains BREACHED.

    Adds columns:
        - rekey_state: Current RekeyState value
        - rekey_state_label: Human-readable label
        - bars_in_current_state: How many bars since state changed
        - wednesday_pm_flag: 1 if Wednesday 12:00-16:00 UTC (bifurcation window)
    """
    df = df.copy()

    # Determine raw state per bar based on distance to 132%
    conditions = [
        df['dist_to_132_pips'] < CRITICAL_THRESHOLD_PIPS,
        df['dist_to_132_pips'] < APPROACH_THRESHOLD_PIPS,
    ]
    choices = [RekeyState.CRITICAL, RekeyState.APPROACHING]
    df['rekey_state'] = np.select(conditions, choices, default=RekeyState.NORMAL)

    # Check if price actually breached the 132% level
    is_bullish = df['bias'] == 'BULLISH'
    is_bearish = df['bias'] == 'BEARISH'

    # Bullish: breach = low <= kill_switch_132
    # Bearish: breach = high >= kill_switch_132
    breach = np.where(
        is_bullish,
        df['low'] <= df['kill_switch_132'],
        np.where(
            is_bearish,
            df['high'] >= df['kill_switch_132'],
            False
        )
    )
    df.loc[breach, 'rekey_state'] = RekeyState.BREACHED

    # REKEY_SEQUENCE: vectorized approach
    # For each trading day that has at least one breach, all bars AFTER
    # the first breach on that day become REKEY_SEQUENCE.
    breached_mask = df['rekey_state'] == RekeyState.BREACHED
    if breached_mask.any():
        # Assign trading day to each bar
        bar_dates = df.index.date

        # Build a DataFrame of breach events with their dates
        breach_df = pd.DataFrame({
            'date': bar_dates[breached_mask.values],
            'idx': np.where(breached_mask)[0]
        })

        # For each date, find the index of the first breach
        first_breach_by_date = breach_df.groupby('date')['idx'].min()

        # For each bar, check if its date has a first breach that occurred before it
        # Vectorized: create a Series mapping date -> first_breach_idx
        date_to_first_breach = first_breach_by_date

        # Build rekey_sequence mask: bar's date has a first breach, and bar is after it
        rekey_seq = np.zeros(len(df), dtype=bool)
        for date_val, first_idx in date_to_first_breach.items():
            date_mask = bar_dates == date_val
            after_mask = np.arange(len(df)) > first_idx
            rekey_seq |= (date_mask & after_mask)

        df.loc[rekey_seq, 'rekey_state'] = RekeyState.REKEY_SEQUENCE

        # Ensure breached bars remain BREACHED (not overwritten by REKEY_SEQUENCE)
        df.loc[breached_mask, 'rekey_state'] = RekeyState.BREACHED

    # Human-readable labels
    state_labels = {s.value: s.name for s in RekeyState}
    df['rekey_state_label'] = df['rekey_state'].map(state_labels)

    # Bars in current state (consecutive count)
    state_changes = df['rekey_state'] != df['rekey_state'].shift(1)
    state_groups = state_changes.cumsum()
    df['bars_in_current_state'] = state_groups.groupby(state_groups).cumcount()

    # Wednesday PM bifurcation flag
    # Wednesday = dayofweek 2, PM = 12:00-16:00 UTC
    is_wednesday = df.index.dayofweek == 2
    is_pm = (df.index.hour >= 12) & (df.index.hour < 16)
    df['wednesday_pm_flag'] = (is_wednesday & is_pm).astype(int)

    return df


def get_rekey_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all 132% breach events from the DataFrame.

    Returns
    -------
    pd.DataFrame
        Table of breach events with timestamp, price, and context.
    """
    breached = df[df['rekey_state'] == RekeyState.BREACHED].copy()
    if len(breached) == 0:
        return pd.DataFrame(columns=['timestamp', 'breach_price', 'bias', 'wednesday_pm'])

    return breached[['close', 'bias', 'wednesday_pm_flag', 'dist_to_132_pips']].rename(
        columns={'close': 'breach_price', 'wednesday_pm_flag': 'wednesday_pm'}
    )
