"""
MLR (Monday London Range) Engine
==================================
Calculates the Monday London Range anchor (07:00-10:00 UTC Monday),
bias direction, and Fibonacci extension targets.

Per CEREBUS v4 Manual:
- MLR is the WEEKLY ANCHOR — defines the macro constraint field
- Bias determined by close relative to MLR midpoint
- Fib extensions: -25%, -50%, -100%, -168%
- 132% Kill-Switch: structural invalidation level

RULE: MLR is forward-filled from Monday to Friday. Weekend gaps are NaN.
RULE: MLR resets every Monday. No carry-over across weeks.

PERFORMANCE: Fully vectorized — no Python loops over rows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


FIB_LEVELS = {
    'minus_25': 0.25,
    'minus_50': 0.50,
    'minus_100': 1.00,
    'minus_168': 1.68,
}

KILL_SWITCH_132 = 1.32


def compute_mlr_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Monday London Range (MLR) for each trading week. Vectorized.

    MLR Window: Monday 07:00-10:00 UTC
    Forward-filled: Tuesday through Friday (or until next Monday)

    Adds columns:
        - mlr_high, mlr_low, mlr_close, mlr_range, mlr_mid
        - bias (BULLISH/BEARISH/NEUTRAL)
        - hours_since_mlr

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with MLR columns added.
    """
    df = df.copy()
    n = len(df)

    # Initialize
    df['mlr_high'] = np.nan
    df['mlr_low'] = np.nan
    df['mlr_close'] = np.nan

    # Find Monday 07:00-10:00 UTC bars
    dow = df.index.dayofweek
    hr = df.index.hour
    mlr_mask = (dow == 0) & (hr >= 7) & (hr < 10)

    if not mlr_mask.any():
        df['mlr_range'] = np.nan
        df['mlr_mid'] = np.nan
        df['bias'] = 'UNKNOWN'
        df['hours_since_mlr'] = np.nan
        return df

    # Compute weekly MLR from Monday bars
    mlr_bars = df[mlr_mask].copy()
    # Week label: Monday of each week
    week_starts = mlr_bars.index.to_series().apply(
        lambda x: x.normalize() - pd.Timedelta(days=x.dayofweek))

    weekly = mlr_bars.groupby(week_starts).agg(
        mlr_high=('high', 'max'),
        mlr_low=('low', 'min'),
        mlr_close=('close', 'last'),
    )

    # For each bar, find its week's Monday and look up MLR
    bar_dow = df.index.dayofweek
    bar_monday = df.index.normalize() - pd.to_timedelta(bar_dow, unit='D')

    # Map weekly MLR to bars using index alignment
    # Create a Series indexed by week_start with the MLR values
    week_high = weekly['mlr_high']
    week_low = weekly['mlr_low']
    week_close = weekly['mlr_close']

    # Use reindex for fast lookup
    mlr_h = week_high.reindex(bar_monday).values
    mlr_l = week_low.reindex(bar_monday).values
    mlr_c = week_close.reindex(bar_monday).values

    df['mlr_high'] = mlr_h
    df['mlr_low'] = mlr_l
    df['mlr_close'] = mlr_c

    # Derived
    df['mlr_range'] = df['mlr_high'] - df['mlr_low']
    df['mlr_mid'] = df['mlr_low'] + df['mlr_range'] / 2

    # Bias
    df['bias'] = np.where(
        df['mlr_close'] > df['mlr_mid'], 'BULLISH',
        np.where(df['mlr_close'] < df['mlr_mid'], 'BEARISH', 'NEUTRAL')
    )

    # Hours since MLR (Monday 10:00 UTC = end of MLR window)
    mlr_end = bar_monday + pd.Timedelta(hours=10)
    delta = df.index - mlr_end
    hours = delta.total_seconds() / 3600
    df['hours_since_mlr'] = np.where(df['mlr_high'].notna(), hours, np.nan)

    return df


def compute_fib_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Fibonacci extension targets based on MLR. Vectorized.

    For BULLISH bias: targets extend UP from MLR high, kill-switch DOWN from MLR low
    For BEARISH bias: targets extend DOWN from MLR low, kill-switch UP from MLR high

    Adds columns:
        - target_minus_25, target_minus_50, target_minus_100, target_minus_168
        - kill_switch_132
        - dist_to_25_pct, dist_to_50_pct, dist_to_132_pct

    Parameters
    ----------
    df : pd.DataFrame
        Must have mlr_high, mlr_low, mlr_range, bias columns.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with Fib target columns added.
    """
    df = df.copy()

    is_bullish = df['bias'] == 'BULLISH'
    is_bearish = df['bias'] == 'BEARISH'

    for level_name, multiplier in FIB_LEVELS.items():
        col = f'target_{level_name}'
        df[col] = np.where(
            is_bullish,
            df['mlr_high'] + multiplier * df['mlr_range'],
            np.where(
                is_bearish,
                df['mlr_low'] - multiplier * df['mlr_range'],
                np.nan
            )
        )

    # 132% Kill-Switch
    df['kill_switch_132'] = np.where(
        is_bullish,
        df['mlr_low'] - KILL_SWITCH_132 * df['mlr_range'],
        np.where(
            is_bearish,
            df['mlr_high'] + KILL_SWITCH_132 * df['mlr_range'],
            np.nan
        )
    )

    # Distance features
    df['dist_to_25_pct'] = (df['close'] - df['target_minus_25']).abs()
    df['dist_to_50_pct'] = (df['close'] - df['target_minus_50']).abs()
    df['dist_to_132_pct'] = (df['close'] - df['kill_switch_132']).abs()

    return df


def get_mlr_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return weekly MLR summary."""
    has_mlr = df['mlr_high'].notna()
    if not has_mlr.any():
        return pd.DataFrame(columns=['mlr_high', 'mlr_low', 'mlr_range', 'bias', 'week_start'])
    weekly = df[has_mlr].groupby(pd.Grouper(freq='W-MON')).agg({
        'mlr_high': 'first', 'mlr_low': 'first',
        'mlr_range': 'first', 'bias': 'first',
    }).dropna()
    return weekly
