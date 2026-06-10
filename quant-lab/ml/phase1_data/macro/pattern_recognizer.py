"""
Pattern Recognition Engine
===========================
Detects CEREBUS-specific price patterns from OHLCV data.

Per CEREBUS v4 Manual:
- Alpha 3-Leg: B-leg retraces 72% of A-leg (72% retrace pattern)
- Beta 3-Leg: B-leg retraces 61.8% of A-leg (Fibonacci golden ratio)
- AB-CD Sequence: Fibonacci extension pattern where CD = 1.272-1.618x AB
- OCC Extreme: Close-only impulse extreme (zero-buffer)

PERFORMANCE: Swing detection uses vectorized rolling max/min — no Python loops.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from enum import IntEnum


class PatternType(IntEnum):
    NONE = 0
    ALPHA_3LEG = 1
    BETA_3LEG = 2
    AB_CD = 3


ALPHA_RETRACE_RATIO = 0.72
BETA_RETRACE_RATIO = 0.618
AB_CD_EXTENSION_LOW = 1.272
AB_CD_EXTENSION_HIGH = 1.618
RETRACE_TOLERANCE = 0.05
MIN_LEG_BARS = 3
MAX_LEG_BARS = 50


def _find_swing_points(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    order: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Find swing highs and swing lows using vectorized rolling max/min.

    A swing high at index i means highs[i] is the maximum in [i-order, i+order].
    A swing low at index i means lows[i] is the minimum in [i-order, i+order].
    """
    n = len(closes)
    if n < 2 * order + 1:
        return np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)

    h = pd.Series(highs)
    l = pd.Series(lows)

    # Rolling max/min with window = 2*order+1, centered
    roll_max = h.rolling(window=2 * order + 1, center=True, min_periods=1).max()
    roll_min = l.rolling(window=2 * order + 1, center=True, min_periods=1).min()

    swing_highs = (h == roll_max).values
    swing_lows = (l == roll_min).values

    # Exclude edges where window is incomplete
    swing_highs[:order] = False
    swing_highs[n - order:] = False
    swing_lows[:order] = False
    swing_lows[n - order:] = False

    return swing_highs, swing_lows


def _detect_3leg_pattern(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    retrace_ratio: float,
    tolerance: float = RETRACE_TOLERANCE,
) -> np.ndarray:
    """Detect a 3-leg pattern (Alpha or Beta) in price data."""
    n = len(closes)
    pattern_detected = np.zeros(n, dtype=bool)

    swing_highs, swing_lows = _find_swing_points(closes, highs, lows)

    swing_high_idx = np.where(swing_highs)[0]
    swing_low_idx = np.where(swing_lows)[0]

    if len(swing_high_idx) < 2 or len(swing_low_idx) < 2:
        return pattern_detected

    all_swings = []
    for idx in swing_high_idx:
        all_swings.append((idx, 'high', highs[idx]))
    for idx in swing_low_idx:
        all_swings.append((idx, 'low', lows[idx]))
    all_swings.sort(key=lambda x: x[0])

    if len(all_swings) < 3:
        return pattern_detected

    for i in range(len(all_swings) - 2):
        pt1 = all_swings[i]
        pt2 = all_swings[i + 1]
        pt3 = all_swings[i + 2]

        leg1_bars = pt2[0] - pt1[0]
        leg2_bars = pt3[0] - pt2[0]

        if not (MIN_LEG_BARS <= leg1_bars <= MAX_LEG_BARS):
            continue
        if not (MIN_LEG_BARS <= leg2_bars <= MAX_LEG_BARS):
            continue

        if pt1[1] == 'low' and pt2[1] == 'high':
            leg_a_size = pt2[2] - pt1[2]
            leg_b_size = pt2[2] - pt3[2]
        elif pt1[1] == 'high' and pt2[1] == 'low':
            leg_a_size = pt1[2] - pt2[2]
            leg_b_size = pt3[2] - pt2[2]
        else:
            continue

        if leg_a_size <= 0:
            continue

        actual_ratio = leg_b_size / leg_a_size
        if abs(actual_ratio - retrace_ratio) <= tolerance:
            if pt1[1] == 'low' and pt3[1] == 'low':
                pattern_detected[pt3[0]] = True
            elif pt1[1] == 'high' and pt3[1] == 'high':
                pattern_detected[pt3[0]] = True

    return pattern_detected


def detect_alpha_leg(
    df: pd.DataFrame,
    tolerance: float = RETRACE_TOLERANCE,
) -> pd.DataFrame:
    """
    Detect Alpha 3-Leg patterns (72% retrace).

    Adds columns: alpha_pattern, alpha_direction
    """
    df = df.copy()
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values

    pattern = _detect_3leg_pattern(closes, highs, lows, ALPHA_RETRACE_RATIO, tolerance)

    df['alpha_pattern'] = pattern.astype(int)
    df['alpha_direction'] = 0

    pattern_idx = np.where(pattern)[0]
    for idx in pattern_idx:
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
    Detect Beta 3-Leg patterns (61.8% retrace).

    Adds columns: beta_pattern, beta_direction
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


def detect_abcd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect AB-CD Fibonacci extension patterns.

    Adds columns: abcd_pattern, abcd_direction, abcd_extension
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

    all_swings = []
    for idx in np.where(swing_highs)[0]:
        all_swings.append((idx, 'high', highs[idx]))
    for idx in np.where(swing_lows)[0]:
        all_swings.append((idx, 'low', lows[idx]))
    all_swings.sort(key=lambda x: x[0])

    if len(all_swings) < 4:
        return df

    for i in range(len(all_swings) - 3):
        pt_a, pt_b, pt_c, pt_d = all_swings[i], all_swings[i+1], all_swings[i+2], all_swings[i+3]

        ab_bars = pt_b[0] - pt_a[0]
        bc_bars = pt_c[0] - pt_b[0]
        cd_bars = pt_d[0] - pt_c[0]

        if not all(MIN_LEG_BARS <= b <= MAX_LEG_BARS for b in [ab_bars, bc_bars, cd_bars]):
            continue

        if pt_a[1] == 'low' and pt_b[1] == 'high':
            ab_size = pt_b[2] - pt_a[2]
            bc_retrace = pt_b[2] - pt_c[2]
            cd_extension = pt_d[2] - pt_c[2] if pt_d[1] == 'high' else 0
        elif pt_a[1] == 'high' and pt_b[1] == 'low':
            ab_size = pt_a[2] - pt_b[2]
            bc_retrace = pt_c[2] - pt_b[2]
            cd_extension = pt_c[2] - pt_d[2] if pt_d[1] == 'low' else 0
        else:
            continue

        if ab_size <= 0:
            continue

        bc_ratio = bc_retrace / ab_size
        if not (0.382 - RETRACE_TOLERANCE <= bc_ratio <= 0.886 + RETRACE_TOLERANCE):
            continue

        cd_ratio = cd_extension / ab_size
        if AB_CD_EXTENSION_LOW - RETRACE_TOLERANCE <= cd_ratio <= AB_CD_EXTENSION_HIGH + RETRACE_TOLERANCE:
            df.iloc[pt_d[0], df.columns.get_loc('abcd_pattern')] = 1
            df.iloc[pt_d[0], df.columns.get_loc('abcd_extension')] = cd_ratio
            df.iloc[pt_d[0], df.columns.get_loc('abcd_direction')] = 1 if pt_a[1] == 'low' else -1

    return df


def detect_occ_extreme(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Detect OCC (Order Close Confirmation) Extreme.

    Adds columns: occ_extreme_high, occ_extreme_low, occ_direction, is_at_occ_extreme
    """
    df = df.copy()

    df['occ_extreme_high'] = df['close'].rolling(window=lookback, min_periods=5).max()
    df['occ_extreme_low'] = df['close'].rolling(window=lookback, min_periods=5).min()

    df['occ_direction'] = 0
    df['is_at_occ_extreme'] = 0

    is_bull = df['close'] >= df['occ_extreme_high']
    is_bear = df['close'] <= df['occ_extreme_low']

    df.loc[is_bull, 'occ_direction'] = 1
    df.loc[is_bear, 'occ_direction'] = -1
    df.loc[is_bull | is_bear, 'is_at_occ_extreme'] = 1

    return df
