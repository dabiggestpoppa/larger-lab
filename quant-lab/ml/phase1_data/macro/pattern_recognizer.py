"""
Pattern Recognition Engine
===========================
Detects CEREBUS-specific price patterns from OHLCV data.

Per CEREBUS v4 Manual + Holy Grail extracted patterns:

3-Leg Patterns:
- Alpha 3-Leg: B-leg retraces 72% of A-leg
- Beta 3-Leg: B-leg retraces 61.8% of A-leg (golden ratio)

Fibonacci Patterns:
- AB-CD Sequence: Fibonacci extension (CD = 1.272-1.618x AB)
- Fibonacci retracements: 23.6%, 38.2%, 50%, 61.8%, 72%, 78.6%, 88.6%
- Fibonacci extensions: 100%, 127.2%, 132%, 161.8%, 168%

Session Patterns:
- 7-8 AM NY Sweep: Price sweep during 7:00-8:00 AM EST (NY session open)
- NY Session Sweep: Broader NY session sweep detection

Rekey Patterns (132% Kill-Switch):
- Rekey at 132%: Price touches/crosses 132% MLR level
- Rekey Sequence: Post-breach state tracking
- 78.6% Rekey Retest: Post-breach retracement to 78.6% level

ILM Patterns:
- ILM Zone: Impulse Level Monitor zone detection
- ILM State: DAILY_ILM, IELM, WILM, MISALIGNED

OCC (Order Close Confirmation):
- OCC Extreme: Close-only impulse extreme (zero-buffer)
- OCC Body: Close-only body measurement

Micro-Macro Phase Patterns:
- Phase 3: Temporal delivery system patterns
- Phase 4: Integration/continuity patterns
- Micro lens: Asian Range, AU, Density Zone
- Macro lens: MLR, Fib targets, ILM, Regime

Gamma Patterns:
- Gamma levels: Key Fibonacci-based gamma zones
- Gamma zone detection: Price interaction with gamma levels

Density & Atomic:
- Density Zone: Price concentration zone detection
- Atomic Unit (AU): Base measurement unit from Asian Range
- Tier Classification: K-Means tier assignment

Time Patterns:
- Wednesday PM Bifurcation: 12:00-16:00 UTC Wednesday stress window
- 12PM EST Hard Exit: End-of-day exit signal
- Session blocks: Asian/London/NY/Black Zone

Gear Shift:
- Target modification signals (SL never changes, only target)

RULE: All patterns computed on M5 closes unless otherwise specified.
RULE: No future leakage — all features use only past/current data.
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
    NY_SWEEP = 4
    GAMMA = 5
    REKEY_132 = 6
    REKEY_SEQUENCE = 7
    OCC_EXTREME = 8
    ILM_ZONE = 9
    DENSITY_ZONE = 10
    WEDNESDAY_BIFURCATION = 11
    HARD_EXIT = 12
    GEAR_SHIFT = 13


# Fibonacci levels
FIB_RETRACE_LEVELS = [0.236, 0.382, 0.50, 0.618, 0.72, 0.786, 0.886]
FIB_EXTENSION_LEVELS = [1.0, 1.272, 1.32, 1.618, 1.68, 2.0, 2.618]
FIB_LEVEL_TOLERANCE = 0.02

# Pattern parameters
ALPHA_RETRACE_RATIO = 0.72
BETA_RETRACE_RATIO = 0.618
AB_CD_EXTENSION_LOW = 1.272
AB_CD_EXTENSION_HIGH = 1.618
RETRACE_TOLERANCE = 0.05
MIN_LEG_BARS = 3
MAX_LEG_BARS = 50

# Session times (EST)
NY_SWEEP_START_HOUR = 7
NY_SWEEP_END_HOUR = 8
WEDNESDAY_BIFURCATION_START_HOUR_UTC = 12
WEDNESDAY_BIFURCATION_END_HOUR_UTC = 16
HARD_EXIT_HOUR_EST = 12


def _find_swing_points(closes, highs, lows, order=5):
    """Find swing highs and swing lows using vectorized rolling max/min."""
    n = len(closes)
    if n < 2 * order + 1:
        return np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)

    h = pd.Series(highs)
    l = pd.Series(lows)

    roll_max = h.rolling(window=2 * order + 1, center=True, min_periods=1).max()
    roll_min = l.rolling(window=2 * order + 1, center=True, min_periods=1).min()

    swing_highs = (h == roll_max).values
    swing_lows = (l == roll_min).values

    swing_highs[:order] = False
    swing_highs[n - order:] = False
    swing_lows[:order] = False
    swing_lows[n - order:] = False

    return swing_highs, swing_lows


def _detect_3leg_pattern(closes, highs, lows, retrace_ratio, tolerance=RETRACE_TOLERANCE):
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


def detect_alpha_leg(df, tolerance=RETRACE_TOLERANCE):
    """
    Detect Alpha 3-Leg patterns (72% retrace).
    B-leg retraces 72% of A-leg (±tolerance).
    Adds: alpha_pattern, alpha_direction
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


def detect_beta_leg(df, tolerance=RETRACE_TOLERANCE):
    """
    Detect Beta 3-Leg patterns (61.8% retrace — golden ratio).
    B-leg retraces 61.8% of A-leg (±tolerance).
    Adds: beta_pattern, beta_direction
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


def detect_abcd(df):
    """
    Detect AB-CD Fibonacci extension patterns.
    A→B impulse, B→C retrace (38.2%-88.6%), C→D extension (1.272-1.618x AB).
    Adds: abcd_pattern, abcd_direction, abcd_extension
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


def detect_ny_sweep(df):
    """
    Detect 7-8 AM NY Sweep pattern.
    Price sweep during 7:00-8:00 AM EST (NY session open).
    Looks for: price makes a new high/low during the sweep window,
    then reverses — indicating a sweep of liquidity.
    Adds: ny_sweep_pattern, ny_sweep_direction
    """
    df = df.copy()
    df['ny_sweep_pattern'] = 0
    df['ny_sweep_direction'] = 0

    if df.index.tz is None:
        idx_est = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        idx_est = df.index.tz_convert('America/New_York')

    hours_est = idx_est.hour
    is_sweep_window = (hours_est >= NY_SWEEP_START_HOUR) & (hours_est < NY_SWEEP_END_HOUR)

    if not is_sweep_window.any():
        return df

    # For each trading day, check if the 7-8 AM window made an extreme
    # that was subsequently reversed
    bar_dates = idx_est.date
    unique_dates = np.unique(bar_dates)

    for date in unique_dates:
        day_mask = bar_dates == date
        sweep_mask = day_mask & is_sweep_window

        if sweep_mask.sum() < 2:
            continue

        sweep_high = df.loc[sweep_mask, 'high'].max()
        sweep_low = df.loc[sweep_mask, 'low'].min()
        sweep_range = sweep_high - sweep_low

        if sweep_range <= 0:
            continue

        # Check bars after the sweep window on the same day
        after_sweep = day_mask & ~is_sweep_window
        if after_sweep.sum() < 1:
            continue

        after_high = df.loc[after_sweep, 'high'].max()
        after_low = df.loc[after_sweep, 'low'].min()

        # Bullish sweep: sweep made a low, then price moved up
        if after_low > sweep_low + sweep_range * 0.5:
            sweep_idx = df.index[sweep_mask]
            if len(sweep_idx) > 0:
                last_sweep_idx = sweep_idx[-1]
                df.loc[last_sweep_idx, 'ny_sweep_pattern'] = 1
                df.loc[last_sweep_idx, 'ny_sweep_direction'] = 1

        # Bearish sweep: sweep made a high, then price moved down
        if after_high < sweep_high - sweep_range * 0.5:
            sweep_idx = df.index[sweep_mask]
            if len(sweep_idx) > 0:
                last_sweep_idx = sweep_idx[-1]
                df.loc[last_sweep_idx, 'ny_sweep_pattern'] = 1
                df.loc[last_sweep_idx, 'ny_sweep_direction'] = -1

    return df


def detect_gamma(df, fib_levels=None):
    """
    Detect Gamma levels — key Fibonacci-based gamma zones.
    Gamma levels are derived from the Asian Range and Fibonacci extensions.
    Detects when price interacts with gamma zones.
    Adds: gamma_level, gamma_zone, gamma_interaction
    """
    df = df.copy()

    if fib_levels is None:
        fib_levels = [0.5, 0.618, 0.72, 0.786, 1.0, 1.272, 1.32, 1.618]

    df['gamma_level'] = np.nan
    df['gamma_zone'] = 0
    df['gamma_interaction'] = 0

    if 'asian_range' not in df.columns or 'asian_range_pips' not in df.columns:
        return df

    # Gamma levels = Asian Range × Fibonacci multipliers
    valid = df['asian_range'].notna()
    if not valid.any():
        return df

    for fib in fib_levels:
        gamma_price = df.loc[valid, 'low'] + df.loc[valid, 'asian_range'] * fib
        # Check if price is near this gamma level (within 5% of AR)
        tolerance = df.loc[valid, 'asian_range'] * 0.05
        near_gamma = np.abs(df.loc[valid, 'close'] - gamma_price) <= tolerance

        if near_gamma.any():
            df.loc[valid & near_gamma.reindex(df.index, fill_value=False), 'gamma_level'] = fib
            df.loc[valid & near_gamma.reindex(df.index, fill_value=False), 'gamma_zone'] = 1
            df.loc[valid & near_gamma.reindex(df.index, fill_value=False), 'gamma_interaction'] = 1

    return df


def detect_rekey_132(df):
    """
    Detect Rekey at 132% — price touches/crosses the 132% MLR kill-switch level.
    Per CEREBUS v4 Manual: 98% of bifurcated days trigger a 132% violation.
    Adds: rekey_132_triggered, rekey_132_direction
    """
    df = df.copy()
    df['rekey_132_triggered'] = 0
    df['rekey_132_direction'] = 0

    if 'kill_switch_132' not in df.columns:
        return df

    is_bullish = df['bias'] == 'BULLISH'
    is_bearish = df['bias'] == 'BEARISH'

    # Bullish: breach = low <= kill_switch_132
    # Bearish: breach = high >= kill_switch_132
    bull_breach = is_bullish & (df['low'] <= df['kill_switch_132'])
    bear_breach = is_bearish & (df['high'] >= df['kill_switch_132'])

    df.loc[bull_breach | bear_breach, 'rekey_132_triggered'] = 1
    df.loc[bull_breach, 'rekey_132_direction'] = -1  # Bullish breach = bearish signal
    df.loc[bear_breach, 'rekey_132_direction'] = 1   # Bearish breach = bullish signal

    return df


def detect_rekey_sequence(df):
    """
    Detect Rekey Sequence — post-132% breach sequence tracking.
    Once 132% is breached, tracks the subsequent price action:
    - 78.6% rekey retest
    - Continuation vs reversal
    Adds: rekey_sequence_state, rekey_sequence_bar
    """
    df = df.copy()
    df['rekey_sequence_state'] = 0  # 0=none, 1=breach, 2=retest, 3=continuation, 4=reversal
    df['rekey_sequence_bar'] = 0

    if 'rekey_132_triggered' not in df.columns:
        return df

    breach_mask = df['rekey_132_triggered'] == 1
    if not breach_mask.any():
        return df

    df.loc[breach_mask, 'rekey_sequence_state'] = 1

    # For each breach, look forward for 78.6% retest
    breach_indices = np.where(breach_mask)[0]
    n = len(df)

    for bi in breach_indices:
        # Look ahead up to 96 bars (24h on M5)
        end = min(bi + 96, n)
        if end - bi < 2:
            continue

        # Get the MLR range for this bar
        if 'mlr_range' in df.columns and 'mlr_high' in df.columns:
            mlr_range = df.iloc[bi]['mlr_range']
            mlr_high = df.iloc[bi]['mlr_high']
            mlr_low = df.iloc[bi]['mlr_low']

            if pd.notna(mlr_range) and mlr_range > 0:
                # 78.6% rekey level
                is_bullish = df.iloc[bi]['bias'] == 'BULLISH'
                if is_bullish:
                    rekey_level = mlr_high - mlr_range * 0.786
                else:
                    rekey_level = mlr_low + mlr_range * 0.786

                # Check if price retested the 78.6% level
                for j in range(bi + 1, end):
                    if is_bullish:
                        if df.iloc[j]['low'] <= rekey_level:
                            df.iloc[j, df.columns.get_loc('rekey_sequence_state')] = 2
                            df.iloc[j, df.columns.get_loc('rekey_sequence_bar')] = j - bi
                            break
                    else:
                        if df.iloc[j]['high'] >= rekey_level:
                            df.iloc[j, df.columns.get_loc('rekey_sequence_state')] = 2
                            df.iloc[j, df.columns.get_loc('rekey_sequence_bar')] = j - bi
                            break

    return df


def detect_occ_extreme(df, lookback=20):
    """
    Detect OCC (Order Close Confirmation) Extreme.
    Close-only impulse extreme (zero-buffer).
    The highest close (bullish) or lowest close (bearish) in the lookback window.
    Adds: occ_extreme_high, occ_extreme_low, occ_direction, is_at_occ_extreme
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


def detect_ilm_zone(df, pip_size=0.0001):
    """
    Detect ILM (Impulse Level Monitor) Zone.
    ILM zone = Asian Range ± Fibonacci extensions.
    Adds: ilm_zone_high, ilm_zone_low, ilm_zone_width, price_in_ilm_zone
    """
    df = df.copy()
    df['ilm_zone_high'] = np.nan
    df['ilm_zone_low'] = np.nan
    df['ilm_zone_width'] = np.nan
    df['price_in_ilm_zone'] = 0

    if 'asian_range' not in df.columns:
        return df

    valid = df['asian_range'].notna()
    if not valid.any():
        return df

    # ILM zone = Asian Range + 61.8% extension on each side
    ilm_ext = 0.618
    df.loc[valid, 'ilm_zone_high'] = df.loc[valid, 'high'] + df.loc[valid, 'asian_range'] * ilm_ext
    df.loc[valid, 'ilm_zone_low'] = df.loc[valid, 'low'] - df.loc[valid, 'asian_range'] * ilm_ext
    df.loc[valid, 'ilm_zone_width'] = df.loc[valid, 'ilm_zone_high'] - df.loc[valid, 'ilm_zone_low']

    in_zone = valid & (df['close'] >= df['ilm_zone_low']) & (df['close'] <= df['ilm_zone_high'])
    df.loc[in_zone, 'price_in_ilm_zone'] = 1

    return df


def detect_density_zone(df, lookback=20):
    """
    Detect Density Zone — price concentration zone.
    Uses rolling standard deviation to identify low-volatility consolidation.
    Adds: density_zone_high, density_zone_low, density_zone_compression
    """
    df = df.copy()

    rolling_std = df['close'].rolling(window=lookback, min_periods=5).std()
    rolling_mean = df['close'].rolling(window=lookback, min_periods=5).mean()

    # Density zone = mean ± 1 standard deviation
    df['density_zone_high'] = rolling_mean + rolling_std
    df['density_zone_low'] = rolling_mean - rolling_std

    # Compression ratio: how tight is the zone relative to recent range
    recent_range = df['high'].rolling(window=lookback, min_periods=5).max() - df['low'].rolling(window=lookback, min_periods=5).min()
    df['density_zone_compression'] = np.where(
        recent_range > 0,
        1 - (rolling_std * 2) / recent_range,
        0
    )

    return df


def detect_wednesday_bifurcation(df):
    """
    Detect Wednesday PM Bifurcation window.
    Per CEREBUS v4 Manual: Wednesday = HIGH ALERT (35% of all 132% violations).
    Wednesday PM = 12:00-16:00 UTC bifurcation window.
    Adds: wednesday_bifurcation_flag, wednesday_pm_volatility
    """
    df = df.copy()
    df['wednesday_bifurcation_flag'] = 0
    df['wednesday_pm_volatility'] = np.nan

    is_wednesday = df.index.dayofweek == 2
    is_pm = (df.index.hour >= WEDNESDAY_BIFURCATION_START_HOUR_UTC) & \
            (df.index.hour < WEDNESDAY_BIFURCATION_END_HOUR_UTC)

    bifurcation_window = is_wednesday & is_pm
    df.loc[bifurcation_window, 'wednesday_bifurcation_flag'] = 1

    # Wednesday PM volatility (range during bifurcation window)
    if bifurcation_window.any():
        df.loc[bifurcation_window, 'wednesday_pm_volatility'] = df.loc[bifurcation_window, 'high'] - df.loc[bifurcation_window, 'low']

    return df


def detect_hard_exit(df):
    """
    Detect 12PM EST Hard Exit signal.
    Per CEREBUS Ironclad Rule: 12PM EST Hard Exit — no exceptions.
    Adds: minutes_to_hard_exit, hard_exit_imminent
    """
    df = df.copy()
    df['minutes_to_hard_exit'] = np.nan
    df['hard_exit_imminent'] = 0

    if df.index.tz is None:
        idx_est = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        idx_est = df.index.tz_convert('America/New_York')

    # Minutes until 12:00 PM EST
    hard_exit_time = idx_est.normalize() + pd.Timedelta(hours=HARD_EXIT_HOUR_EST)
    minutes_to_exit = (hard_exit_time - idx_est).total_seconds() / 60

    # Only for bars before 12PM
    before_noon = idx_est.hour < HARD_EXIT_HOUR_EST
    df.loc[before_noon, 'minutes_to_hard_exit'] = minutes_to_exit[before_noon]

    # Hard exit imminent = within 30 minutes
    imminent = before_noon & (minutes_to_exit <= 30) & (minutes_to_exit >= 0)
    df.loc[imminent, 'hard_exit_imminent'] = 1

    return df


def detect_gear_shift(df):
    """
    Detect Gear Shift — target modification signal.
    Per CEREBUS Ironclad Rule: Gear Shift modifies TARGET ONLY, SL never changes.
    Gear shift occurs when regime changes but price hasn't hit SL.
    Adds: gear_shift_signal, gear_shift_direction
    """
    df = df.copy()
    df['gear_shift_signal'] = 0
    df['gear_shift_direction'] = 0

    if 'regime_ratio' not in df.columns or 'bias' not in df.columns:
        return df

    # Gear shift: regime ratio crosses 1.5 threshold while price is still in valid range
    if 'dist_to_132_pips' in df.columns:
        valid_sl = df['dist_to_132_pips'] > 15  # Not near kill-switch
    else:
        valid_sl = True

    # Regime improvement: ratio crosses above 1.5
    if 'regime_ratio' in df.columns:
        regime_improving = (df['regime_ratio'] >= 1.5) & (df['regime_ratio'].shift(1) < 1.5)
        gear_up = regime_improving & valid_sl

        # Regime deterioration: ratio crosses below 1.45
        regime_worsening = (df['regime_ratio'] < 1.45) & (df['regime_ratio'].shift(1) >= 1.45)
        gear_down = regime_worsening & valid_sl

        df.loc[gear_up, 'gear_shift_signal'] = 1
        df.loc[gear_up, 'gear_shift_direction'] = 1
        df.loc[gear_down, 'gear_shift_signal'] = 1
        df.loc[gear_down, 'gear_shift_direction'] = -1

    return df


def detect_fib_retrace_levels(df, lookback=20):
    """
    Detect Fibonacci retracement levels from recent swing.
    Standard Fib levels: 23.6%, 38.2%, 50%, 61.8%, 72%, 78.6%, 88.6%.
    Adds: fib_retrace_236, fib_retrace_382, fib_retrace_50, fib_retrace_618,
          fib_retrace_72, fib_retrace_786, fib_retrace_886, nearest_fib_level
    """
    df = df.copy()

    for level in FIB_RETRACE_LEVELS:
        col = f'fib_retrace_{int(level * 1000):03d}'
        df[col] = np.nan

    df['nearest_fib_level'] = np.nan
    df['dist_to_nearest_fib'] = np.nan

    # Rolling swing high/low
    swing_high = df['high'].rolling(window=lookback, min_periods=5).max()
    swing_low = df['low'].rolling(window=lookback, min_periods=5).min()
    swing_range = swing_high - swing_low

    valid = swing_range > 0
    if not valid.any():
        return df

    for level in FIB_RETRACE_LEVELS:
        col = f'fib_retrace_{int(level * 1000):03d}'
        df.loc[valid, col] = df.loc[valid, 'low'] + swing_range[valid] * level

    # Find nearest fib level to current close
    if valid.any():
        fib_cols = [f'fib_retrace_{int(l * 1000):03d}' for l in FIB_RETRACE_LEVELS]
        fib_values = df.loc[valid, fib_cols].values
        close_values = df.loc[valid, 'close'].values.reshape(-1, 1)

        dists = np.abs(close_values - fib_values)
        nearest_idx = np.argmin(dists, axis=1)
        nearest_level = np.array(FIB_RETRACE_LEVELS)[nearest_idx]
        min_dist = np.min(dists, axis=1)

        df.loc[valid, 'nearest_fib_level'] = nearest_level
        df.loc[valid, 'dist_to_nearest_fib'] = min_dist

    return df


def detect_fib_extension_levels(df, lookback=20):
    """
    Detect Fibonacci extension levels from recent swing.
    Extension levels: 100%, 127.2%, 132%, 161.8%, 168%.
    Adds: fib_ext_100, fib_ext_1272, fib_ext_132, fib_ext_1618, fib_ext_168
    """
    df = df.copy()

    for level in [1.0, 1.272, 1.32, 1.618, 1.68]:
        col = f'fib_ext_{int(level * 1000):04d}'
        df[col] = np.nan

    swing_high = df['high'].rolling(window=lookback, min_periods=5).max()
    swing_low = df['low'].rolling(window=lookback, min_periods=5).min()
    swing_range = swing_high - swing_low

    valid = swing_range > 0
    if not valid.any():
        return df

    is_bullish = df['bias'] == 'BULLISH'
    is_bearish = df['bias'] == 'BEARISH'

    for level in [1.0, 1.272, 1.32, 1.618, 1.68]:
        col = f'fib_ext_{int(level * 1000):04d}'
        # Bullish: extend up from swing high
        # Bearish: extend down from swing low
        df.loc[valid & is_bullish, col] = df.loc[valid & is_bullish, 'high'] + swing_range[valid & is_bullish] * (level - 1)
        df.loc[valid & is_bearish, col] = df.loc[valid & is_bearish, 'low'] - swing_range[valid & is_bearish] * (level - 1)

    return df


def detect_micro_macro_phase(df):
    """
    Detect Micro-Macro Phase patterns.
    Micro lens: Asian Range, AU, Density Zone (short-term)
    Macro lens: MLR, Fib targets, ILM, Regime (long-term)
    Phase 3: Temporal delivery system
    Phase 4: Integration/continuity
    Adds: micro_phase, macro_phase, phase_alignment
    """
    df = df.copy()
    df['micro_phase'] = 0
    df['macro_phase'] = 0
    df['phase_alignment'] = 0

    # Micro phase: based on Asian Range position
    if 'asian_range_pips' in df.columns:
        ar = df['asian_range_pips']
        ar_median = ar.rolling(window=96, min_periods=24).median()  # 8h median

        # Micro phase 1: AR expanding (volatility increasing)
        # Micro phase 2: AR contracting (consolidation)
        # Micro phase 3: AR breakout (impulse)
        ar_expanding = ar > ar_median * 1.2
        ar_contracting = ar < ar_median * 0.8

        df.loc[ar_expanding, 'micro_phase'] = 1
        df.loc[ar_contracting, 'micro_phase'] = 2
        df.loc[~ar_expanding & ~ar_contracting, 'micro_phase'] = 3

    # Macro phase: based on MLR bias + regime
    if 'bias' in df.columns and 'regime_ratio' in df.columns:
        is_bullish = df['bias'] == 'BULLISH'
        is_bearish = df['bias'] == 'BEARISH'
        regime_confirmed = df['regime_ratio'] >= 1.5
        regime_failed = df['regime_ratio'] < 1.45

        # Macro phase 1: Bullish confirmed
        # Macro phase 2: Bearish confirmed
        # Macro phase 3: Transition/uncertain
        df.loc[is_bullish & regime_confirmed, 'macro_phase'] = 1
        df.loc[is_bearish & regime_confirmed, 'macro_phase'] = 2
        df.loc[regime_failed, 'macro_phase'] = 3

    # Phase alignment: micro and macro agree
    micro_bull = df['micro_phase'] == 1  # Expanding = bullish micro
    micro_bear = df['micro_phase'] == 2  # Contracting = bearish micro
    macro_bull = df['macro_phase'] == 1
    macro_bear = df['macro_phase'] == 2

    df.loc[(micro_bull & macro_bull) | (micro_bear & macro_bear), 'phase_alignment'] = 1
    df.loc[(micro_bull & macro_bear) | (micro_bear & macro_bull), 'phase_alignment'] = -1

    return df


def detect_all_patterns(df, pip_size=0.0001):
    """
    Run all pattern detection functions.
    Returns DataFrame with all pattern columns added.
    """
    df = df.copy()

    # 3-Leg patterns
    df = detect_alpha_leg(df)
    df = detect_beta_leg(df)
    df = detect_abcd(df)

    # Session patterns
    df = detect_ny_sweep(df)

    # Gamma
    df = detect_gamma(df)

    # Rekey patterns
    df = detect_rekey_132(df)
    df = detect_rekey_sequence(df)

    # OCC
    df = detect_occ_extreme(df)

    # ILM Zone
    df = detect_ilm_zone(df, pip_size)

    # Density Zone
    df = detect_density_zone(df)

    # Time patterns
    df = detect_wednesday_bifurcation(df)
    df = detect_hard_exit(df)

    # Gear Shift
    df = detect_gear_shift(df)

    # Fibonacci levels
    df = detect_fib_retrace_levels(df)
    df = detect_fib_extension_levels(df)

    # Micro-Macro phase
    df = detect_micro_macro_phase(df)

    # Combined pattern flag: 1 if any pattern detected
    df['any_pattern'] = (
        (df['alpha_pattern'] == 1) |
        (df['beta_pattern'] == 1) |
        (df['abcd_pattern'] == 1) |
        (df['ny_sweep_pattern'] == 1) |
        (df['gamma_zone'] > 0) |
        (df['rekey_132_triggered'] == 1) |
        (df['rekey_sequence_state'] == 1) |
        (df['is_at_occ_extreme'] == 1) |
        (df['price_in_ilm_zone'] == 1) |
        (df['wednesday_bifurcation_flag'] == 1) |
        (df['hard_exit_imminent'] == 1) |
        (df['gear_shift_signal'] == 1) |
        (df['phase_alignment'] != 0)
    ).astype(int)

    return df
