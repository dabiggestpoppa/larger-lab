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
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional, Tuple


# Fibonacci extension levels (multiplier of MLR range)
FIB_LEVELS = {
    'minus_25': 0.25,
    'minus_50': 0.50,
    'minus_100': 1.00,
    'minus_168': 1.68,
}

# 132% Kill-Switch multiplier
KILL_SWITCH_132 = 1.32


def compute_mlr_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Monday London Range (MLR) for each trading week.
    
    MLR Window: Monday 07:00-10:00 UTC
    Forward-filled: Tuesday through Friday (or until next Monday)
    
    Adds columns:
        - mlr_high: MLR high for the week
        - mlr_low: MLR low for the week
        - mlr_range: MLR range in price units
        - mlr_mid: MLR midpoint
        - mlr_close: Last candle close within MLR window
        - bias: 'BULLISH' or 'BEARISH'
        - hours_since_mlr: Hours since MLR formation
    
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
    
    # Initialize MLR columns
    df['mlr_high'] = np.nan
    df['mlr_low'] = np.nan
    df['mlr_close'] = np.nan
    
    # Find Monday 07:00-10:00 UTC windows
    is_monday = df.index.dayofweek == 0
    is_mlr_hour = (df.index.hour >= 7) & (df.index.hour < 10)
    mlr_mask = is_monday & is_mlr_hour
    
    if mlr_mask.sum() == 0:
        # No MLR windows found — return with NaN columns
        df['mlr_range'] = np.nan
        df['mlr_mid'] = np.nan
        df['bias'] = 'UNKNOWN'
        df['hours_since_mlr'] = np.nan
        return df
    
    # Group MLR candles by week
    mlr_candles = df[mlr_mask].copy()
    
    # Resample to weekly — each week's MLR = Mon 07:00-10:00 UTC high/low
    # Use 'W-MON' anchor so weeks start on Monday
    weekly_groups = mlr_candles.groupby(pd.Grouper(freq='W-MON'))
    
    mlr_data = {}
    for week_start, group in weekly_groups:
        if len(group) == 0:
            continue
        week_key = week_start.normalize()
        mlr_data[week_key] = {
            'high': group['high'].max(),
            'low': group['low'].min(),
            'close': group['close'].iloc[-1] if len(group) > 0 else np.nan,
        }
    
    # Forward-fill MLR values to all candles in the week
    # Each candle gets the MLR from its week's Monday
    for ts in df.index:
        # Find the Monday of this candle's week
        day_of_week = ts.dayofweek
        monday_of_week = ts.normalize() - pd.Timedelta(days=day_of_week)
        
        if monday_of_week in mlr_data:
            df.at[ts, 'mlr_high'] = mlr_data[monday_of_week]['high']
            df.at[ts, 'mlr_low'] = mlr_data[monday_of_week]['low']
            df.at[ts, 'mlr_close'] = mlr_data[monday_of_week]['close']
            
            # Hours since MLR formation (Monday 10:00 UTC = end of MLR window)
            mlr_end = monday_of_week + pd.Timedelta(hours=10)
            if ts >= mlr_end:
                df.at[ts, 'hours_since_mlr'] = (ts - mlr_end).total_seconds() / 3600
            else:
                df.at[ts, 'hours_since_mlr'] = 0.0
    
    # Derived MLR features
    df['mlr_range'] = df['mlr_high'] - df['mlr_low']
    df['mlr_mid'] = df['mlr_low'] + (df['mlr_range'] / 2)
    
    # Bias: Bullish if MLR close > midpoint, Bearish otherwise
    df['bias'] = np.where(
        df['mlr_close'] > df['mlr_mid'],
        'BULLISH',
        np.where(df['mlr_close'] < df['mlr_mid'], 'BEARISH', 'NEUTRAL')
    )
    
    return df


def compute_fib_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Fibonacci extension targets based on MLR.
    
    For BULLISH bias:
        - Targets extend UP from MLR high
        - Kill-switch extends DOWN from MLR low
    
    For BEARISH bias:
        - Targets extend DOWN from MLR low
        - Kill-switch extends UP from MLR high
    
    Adds columns:
        - target_minus_25: -25% Fib extension
        - target_minus_50: -50% Fib extension
        - target_minus_100: -100% Fib extension
        - target_minus_168: -168% Fib extension
        - kill_switch_132: 132% invalidation level
        - dist_to_25_pct: Absolute distance to -25% target (pips)
        - dist_to_50_pct: Absolute distance to -50% target (pips)
        - dist_to_132_pct: Absolute distance to 132% kill-switch (pips)
    
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
        col_name = f'target_{level_name}'
        
        # Bullish: target = MLR_high + (multiplier * MLR_range)
        # Bearish: target = MLR_low - (multiplier * MLR_range)
        df[col_name] = np.where(
            is_bullish,
            df['mlr_high'] + (multiplier * df['mlr_range']),
            np.where(
                is_bearish,
                df['mlr_low'] - (multiplier * df['mlr_range']),
                np.nan
            )
        )
    
    # 132% Kill-Switch
    # Bullish: kill_switch = MLR_low - (1.32 * MLR_range)
    # Bearish: kill_switch = MLR_high + (1.32 * MLR_range)
    df['kill_switch_132'] = np.where(
        is_bullish,
        df['mlr_low'] - (KILL_SWITCH_132 * df['mlr_range']),
        np.where(
            is_bearish,
            df['mlr_high'] + (KILL_SWITCH_132 * df['mlr_range']),
            np.nan
        )
    )
    
    # Distance features (in price units — convert to pips at call site)
    df['dist_to_25_pct'] = (df['close'] - df['target_minus_25']).abs()
    df['dist_to_50_pct'] = (df['close'] - df['target_minus_50']).abs()
    df['dist_to_132_pct'] = (df['close'] - df['kill_switch_132']).abs()
    
    return df


def get_mlr_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a weekly summary of MLR data.
    
    Returns
    -------
    pd.DataFrame
        Weekly MLR summary with columns: mlr_high, mlr_low, mlr_range, bias
    """
    has_mlr = df['mlr_high'].notna()
    if has_mlr.sum() == 0:
        return pd.DataFrame(columns=['mlr_high', 'mlr_low', 'mlr_range', 'bias', 'week_start'])
    
    weekly = df[has_mlr].groupby(pd.Grouper(freq='W-MON')).agg({
        'mlr_high': 'first',
        'mlr_low': 'first',
        'mlr_range': 'first',
        'bias': 'first',
    }).dropna()
    
    return weekly
