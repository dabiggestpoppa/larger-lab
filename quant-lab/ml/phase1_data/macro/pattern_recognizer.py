"""
Pattern Recognition Engine
===========================
Detects CEREBUS-specific price patterns from OHLCV data.

Per CEREBUS v4 Manual:
- Alpha 3-Leg: B-leg retraces 72% of A-leg (72% retrace pattern)
- Beta 3-Leg: B-leg retraces 61.8% of A-leg (Fibonacci golden ratio)
- AB-CD Sequence: Fibonacci extension pattern where CD = 1.272-1.618x AB
- OCC Extreme: Close-only impulse extreme (zero-buffer)

Pattern Definitions:
- Alpha 3-Leg: A-leg (impulse), B-leg (72% retrace), C-leg (continuation)
- Beta 3-Leg: A-leg (impulse), B-leg (61.8% retrace), C-leg (continuation)
- AB-CD: A→B impulse, B→C retrace, C→D extension (1.272-1.618x AB)

RULE: Patterns are detected on M5 closes — wicks are ignored.
RULE: Minimum 3 bars per leg, maximum 50 bars per leg.
RULE: Retrace tolerance = ±5% of target ratio.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from enum import IntEnum


class PatternType(IntEnum):
    """Detected pattern types."""
    NONE = 0
    ALPHA_3LEG = 1
    BETA_3LEG = 2
    AB_CD = 3


# Pattern parameters
ALPHA_RETRACE_RATIO = 0.72
BETA_RETRACE_RATIO = 0.618
AB_CD_EXTENSION_LOW = 1.272
AB_CD_EXTENSION_HIGH = 1.618
RETRACE_TOLERANCE = 0.05  # ±5% tolerance
MIN_LEG_BARS = 3
MAX_LEG_BARS = 50


def _find_swing_points(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    order: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Find swing highs and swing lows in price data.

    Parameters
    ----------
    closes : np.ndarray
        Close prices.
    highs : np.ndarray
        High prices.
    lows : np.ndarray
        Low prices.
    order : int
        Number of bars on each side for swing detection.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (swing_highs, swing_lows) — boolean arrays.
    """
    n = len(closes)
    swing_highs = np.zeros(n, dtype=bool)
    swing_lows = np.zeros(n, dtype=bool)

    for i in range(order, n - order):
        # Swing high: highs[i] is the highest in [i-order, i+order]
        if highs[i] == max(highs[i - order:i + order + 1]):
            swing_highs[i] = True
        # Swing low: lows[i] is the lowest in [i-order, i+order]
        if lows[i] == min(lows[i - order:i + order + 1]):
            swing_lows[i] = True

    return swing_highs, swing_lows


def _detect_3leg_pattern(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    retrace_ratio: float,
    tolerance: float = RETRACE_TOLERANCE,
) -> np.ndarray:
    """
    Detect a 3-leg pattern (Alpha or Beta) in price data.

    Pattern structure:
    - Leg A: Impulse move (up or down)
    - Leg B: Retrace of Leg A by `retrace_ratio` (±tolerance)
    - Leg C: Continuation in Leg A direction

    Parameters
    ----------
    closes : np.ndarray
        Close prices.
    highs : np.ndarray
        High prices.
    lows : np.ndarray
        Low prices.
    retrace_ratio : float
        Target retrace ratio (0.72 for Alpha, 0.618 for Beta).
    tolerance : float
        Acceptable deviation from target ratio.

    Returns
    -------
    np.ndarray
        Boolean array — True where pattern completes (at C-leg end).
    """
    n = len(closes)
    pattern_detected = np.zeros(n, dtype=bool)

    swing_highs, swing_lows = _find_swing_points(closes, highs, lows)

    swing_high_idx = np.where(swing_highs)[0]
    swing_low_idx = np.where(swing_lows)[0]

    if len(swing_high_idx) < 2 or len(swing_low_idx) < 2:
        return pattern_detected

    # Combine and sort swing points
    all_swings = []
    for idx in swing_high_idx:
        all_swings.append((idx, 'high', highs[idx]))
    for idx in swing_low_idx:
        all_swings.append((idx, 'low', lows[idx]))
    all_swings.sort(key=lambda x: x[0])

    if len(all_swings) < 3:
        return pattern_detected

    # Look for 3-leg patterns in swing sequences
    for i in range(len(all_swings) - 2):
        pt1 = all_swings[i]
        pt2 = all_swings[i + 1]
        pt3 = all_swings[i + 2]

        # Check bar constraints
        leg1_bars = pt2[0] - pt1[0]
        leg2_bars = pt3[0] - pt2[0]

        if not (MIN_LEG_BARS <= leg1_bars <= MAX_LEG_BARS):
            continue
        if not (MIN_LEG_BARS <= leg2_bars <= MAX_LEG_BARS):
            continue

        # Leg A direction
        if pt1[1] == 'low' and pt2[1] == 'high':
            # Leg A: up (low -> high)
            leg_a_size = pt2[2] - pt1[2]
            leg_b_size = pt2[2] - pt3[2]  # retrace down
        elif pt1[1] == 'high' and pt2[1] == 'low':
            # Leg A: down (high -> low)
            leg_a_size = pt1[2] - pt2[2]
            leg_b_size = pt3[2] - pt2[2]  # retrace up
        else:
            continue

        if leg_a_size <= 0:
            continue

        # Check retrace ratio
        actual_ratio = leg_b_size / leg_a_size
        if abs(actual_ratio - retrace_ratio) <= tolerance:
            # Leg C should continue in Leg A direction
            if pt1[1] == 'low' and pt3[1] == 'low':
                # Bullish: C-leg ends at a low (before continuation up)
                pattern_detected[pt3[0]] = True
            elif pt1[1] == 'high' and pt3[1] == 'high':
                # Bearish: C-leg ends at a high (before continuation down)
                pattern_detected[pt3[0]] = True

    return pattern_detected


def detect_alpha_leg(
    df: pd.DataFrame,
    tolerance: float = RETRACE_TOLERANCE,
) -> pd.DataFrame:
    """
    Detect Alpha 3-Leg patterns (72% retrace).

    B-leg retraces 72% of A-leg (±tolerance).

    Adds columns:
        - alpha_pattern: 1 where Alpha 3-Leg completes, 0 otherwise
        - alpha_direction: 1 (bullish), -1 (bearish), 0 (none)

    Parameters
    ----------
    df : pd.DataFrame
        Must have OHLC columns with DatetimeIndex.
    tolerance : float
        Acceptable deviation from 72% ratio.

    Returns
    -------
    pd.DataFrame
        DataFrame with Alpha pattern columns added.
    """
    df = df.copy()

    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values

    pattern = _detect_3leg_pattern(closes, highs, lows, ALPHA_RETRACE_RATIO, tolerance)

    df['alpha_pattern'] = pattern.astype(int)
    df['alpha_direction'] = 0

    # Determine direction for detected patterns
    pattern_idx = np.where(pattern)[0]
    for idx in pattern_idx:
        # Look at the surrounding context to determine direction
        start = max(0, idx - MAX_LEG_BARS * 2)
        if idx > start:
            if closes[idx] > closes[start]:
                df.iloc[idx, df.columns.get_loc('alpha_direction')] = 1
            else:
                df.iloc[idx, df.columns.get_loc('alpha_direction')] = -1

    return df


def detect_beta_leg(
    df: pd.DataFrame,
    tolerance: float = RETRACE_TOLERANCE,
) -> pd.DataFrame:
    """
    Detect Beta 3-Leg patterns (61.8% retrace — golden ratio).

    B-leg retraces 61.8% of A-leg (±tolerance).

    Adds columns:
        - beta_pattern: 1 where Beta 3-Leg completes, 0 otherwise
        - beta_direction: 1 (bullish), -1 (bearish), 0 (none)

    Parameters
    ----------
    df : pd.DataFrame
        Must have OHLC columns with DatetimeIndex.
    tolerance : float
        Acceptable deviation from 61.8% ratio.

    Returns
    -------
    pd.DataFrame
        DataFrame with Beta pattern columns added.
    """
    df = df.copy()

    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values

    pattern = _detect_3leg_pattern(closes, highs, lows, BETA_RETRACE_RATIO, tolerance)

    df['beta_pattern'] = pattern.astype(int)
    df['beta_direction'] = 0

    pattern_idx = np.where(pattern)[0]
    for idx in pattern_idx:
        start = max(0, idx - MAX_LEG_BARS * 2)
        if idx > start:
            if closes[idx] > closes[start]:
                df.iloc[idx, df.columns.get_loc('beta_direction')] = 1
            else:
                df.iloc[idx, df.columns.get_loc('beta_direction')] = -1

    return df


def detect_abcd(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect AB-CD Fibonacci extension patterns.

    Pattern structure:
    - A→B: Impulse leg
    - B→C: Retrace (38.2%-88.6% of A→B)
    - C→D: Extension (1.272-1.618x A→B)

    Adds columns:
        - abcd_pattern: 1 where AB-CD completes, 0 otherwise
        - abcd_direction: 1 (bullish), -1 (bearish), 0 (none)
        - abcd_extension: Actual extension ratio at D point

    Parameters
    ----------
    df : pd.DataFrame
        Must have OHLC columns with DatetimeIndex.

    Returns
    -------
    pd.DataFrame
        DataFrame with AB-CD pattern columns added.
    """
    df = df.copy()

    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    n = len(closes)

    df['abcd_pattern'] = 0
    df['abcd_direction'] = 0
    df['abcd_extension'] = np.nan

    swing_highs, swing_lows = _find_swing_points(closes, highs, lows)

    swing_high_idx = np.where(swing_highs)[0]
    swing_low_idx = np.where(swing_lows)[0]

    # Combine and sort swing points
    all_swings = []
    for idx in swing_high_idx:
        all_swings.append((idx, 'high', highs[idx]))
    for idx in swing_low_idx:
        all_swings.append((idx, 'low', lows[idx]))
    all_swings.sort(key=lambda x: x[0])

    if len(all_swings) < 4:
        return df

    # Look for AB-CD patterns in swing sequences
    for i in range(len(all_swings) - 3):
        pt_a = all_swings[i]
        pt_b = all_swings[i + 1]
        pt_c = all_swings[i + 2]
        pt_d = all_swings[i + 3]

        # Check bar constraints
        ab_bars = pt_b[0] - pt_a[0]
        bc_bars = pt_c[0] - pt_b[0]
        cd_bars = pt_d[0] - pt_c[0]

        if not all(MIN_LEG_BARS <= b <= MAX_LEG_BARS for b in [ab_bars, bc_bars, cd_bars]):
            continue

        # AB direction and size
        if pt_a[1] == 'low' and pt_b[1] == 'high':
            ab_size = pt_b[2] - pt_a[2]  # Bullish AB
            bc_retrace = pt_b[2] - pt_c[2]
            cd_extension = pt_d[2] - pt_c[2] if pt_d[1] == 'high' else 0
        elif pt_a[1] == 'high' and pt_b[1] == 'low':
            ab_size = pt_a[2] - pt_b[2]  # Bearish AB
            bc_retrace = pt_c[2] - pt_b[2]
            cd_extension = pt_c[2] - pt_d[2] if pt_d[1] == 'low' else 0
        else:
            continue

        if ab_size <= 0:
            continue

        # BC retrace should be 38.2%-88.6% of AB
        bc_ratio = bc_retrace / ab_size
        if not (0.382 - RETRACE_TOLERANCE <= bc_ratio <= 0.886 + RETRACE_TOLERANCE):
            continue

        # CD extension should be 1.272-1.618x AB
        cd_ratio = cd_extension / ab_size
        if AB_CD_EXTENSION_LOW - RETRACE_TOLERANCE <= cd_ratio <= AB_CD_EXTENSION_HIGH + RETRACE_TOLERANCE:
            df.iloc[pt_d[0], df.columns.get_loc('abcd_pattern')] = 1
            df.iloc[pt_d[0], df.columns.get_loc('abcd_extension')] = cd_ratio

            if pt_a[1] == 'low':
                df.iloc[pt_d[0], df.columns.get_loc('abcd_direction')] = 1
            else:
                df.iloc[pt_d[0], df.columns.get_loc('abcd_direction')] = -1

    return df


def detect_occ_extreme(
    df: pd.DataFrame,
    lookback: int = 20,
) -> pd.DataFrame:
    """
    Detect OCC (Order Close Confirmation) Extreme.

    OCC Extreme = Close-only impulse extreme (zero-buffer).
    The highest close (bullish) or lowest close (bearish) in the lookback window.

    Adds columns:
        - occ_extreme_high: Rolling highest close in lookback
        - occ_extreme_low: Rolling lowest close in lookback
        - occ_direction: 1 (bullish extreme), -1 (bearish extreme), 0 (none)
        - is_at_occ_extreme: 1 if current close equals the extreme

    Parameters
    ----------
    df : pd.DataFrame
        Must have 'close' column with DatetimeIndex.
    lookback : int
        Number of bars to look back for extreme detection.

    Returns
    -------
    pd.DataFrame
        DataFrame with OCC extreme columns added.
    """
    df = df.copy()

    df['occ_extreme_high'] = df['close'].rolling(window=lookback, min_periods=5).max()
    df['occ_extreme_low'] = df['close'].rolling(window=lookback, min_periods=5).min()

    df['occ_direction'] = 0
    df['is_at_occ_extreme'] = 0

    # Bullish extreme: close == rolling max
    is_bull_extreme = df['close'] >= df['occ_extreme_high']
    # Bearish extreme: close == rolling min
    is_bear_extreme = df['close'] <= df['occ_extreme_low']

    df.loc[is_bull_extreme, 'occ_direction'] = 1
    df.loc[is_bear_extreme, 'occ_direction'] = -1
    df.loc[is_bull_extreme | is_bear_extreme, 'is_at_occ_extreme'] = 1

    return df
