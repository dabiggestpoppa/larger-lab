"""
Macro Feature Builder
======================
Combines all macro features into a single feature matrix.

Per CEREBUS v4 Manual:
- Macro features complement micro features (Asian Range, tier, AU, DZ)
- Macro and Micro lenses must remain ISOLATED in the feature store
- Bridging state variables connect them, NOT direct mapping

This module builds the COMPLETE macro feature matrix by combining:
1. MLR features (from mlr_engine)
2. Fibonacci targets (from mlr_engine)
3. 132% kill-switch proximity (from kill_switch)
4. ILM states (from ilm_detector)
5. Regime ratios (from ilm_detector)
6. Pattern recognition (from pattern_recognizer) — ALL patterns
7. Time block features (computed here)

Total macro features per candle: ~50+
Combined with micro features: ~60+ total

RULE: All features are computed on M5 closes unless otherwise specified.
RULE: No future leakage — all features use only past/current data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .mlr_engine import compute_mlr_features, compute_fib_targets
from .kill_switch import compute_132_proximity, compute_rekey_state
from .ilm_detector import compute_ilm_state, compute_regime_ratio
from .pattern_recognizer import (
    detect_alpha_leg, detect_beta_leg, detect_abcd,
    detect_ny_sweep, detect_gamma, detect_rekey_132, detect_rekey_sequence,
    detect_occ_extreme, detect_ilm_zone, detect_density_zone,
    detect_wednesday_bifurcation, detect_hard_exit, detect_gear_shift,
    detect_fib_retrace_levels, detect_fib_extension_levels,
    detect_micro_macro_phase, detect_all_patterns,
)


# Session boundaries (UTC)
# Asian session: 00:00-08:00 UTC = 7pm-3am EST (per CEREBUS v4 Manual)
SESSION_ASIAN_START = 0     # 00:00 UTC = 19:00 EST (Asian session start)
SESSION_ASIAN_END = 8       # 08:00 UTC = 03:00 EST (Asian session end)
SESSION_LONDON_START = 8    # 08:00 UTC = 03:00 EST (London open)
SESSION_LONDON_END = 12     # 12:00 UTC = 07:00 EST (London morning)
SESSION_NY_START = 12       # 12:00 UTC = 07:00 EST (NY open)
SESSION_NY_END = 17         # 17:00 UTC = 12:00 EST (NY afternoon)
BLACK_ZONE_START = 17       # 17:00 UTC = 12:00 EST
BLACK_ZONE_END = 20         # 20:00 UTC = 15:00 EST


def _compute_time_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute time block features for each candle.

    Adds columns:
        - day_of_week: 0=Monday, 4=Friday
        - hour_utc: Hour of day in UTC
        - session: 'ASIAN', 'LONDON', 'NY', 'BLACK_ZONE'
        - is_monday, is_friday, is_wednesday: Binary flags
        - is_asian, is_london, is_ny, is_black_zone: Binary flags
    """
    df = df.copy()

    df['day_of_week'] = df.index.dayofweek
    df['hour_utc'] = df.index.hour
    df['is_monday'] = (df.index.dayofweek == 0).astype(int)
    df['is_friday'] = (df.index.dayofweek == 4).astype(int)
    df['is_wednesday'] = (df.index.dayofweek == 2).astype(int)

    # Session classification
    hours = df.index.hour
    conditions = [
        (hours >= SESSION_ASIAN_START) & (hours < SESSION_ASIAN_END),
        (hours >= SESSION_LONDON_START) & (hours < SESSION_LONDON_END),
        (hours >= SESSION_NY_START) & (hours < SESSION_NY_END),
        (hours >= BLACK_ZONE_START) & (hours < BLACK_ZONE_END),
    ]
    choices = ['ASIAN', 'LONDON', 'NY', 'BLACK_ZONE']
    df['session'] = np.select(conditions, choices, default='OFF_HOURS')

    for sess in ['ASIAN', 'LONDON', 'NY', 'BLACK_ZONE']:
        df[f'is_{sess.lower()}'] = (df['session'] == sess).astype(int)

    return df


def build_macro_feature_matrix(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
    include_patterns: bool = True,
    include_time_blocks: bool = True,
    symbol: str = "",
) -> pd.DataFrame:
    """
    Build the complete macro feature matrix.

    Pipeline:
    1. MLR features
    2. Fibonacci targets
    3. 132% proximity
    4. Rekey state
    5. ILM state
    6. Regime ratio
    7. ALL pattern recognition (optional)
    8. Time blocks (optional)

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.
    pip_size : float
        Pip size for the asset.
    include_patterns : bool
        Whether to include ALL pattern recognition features.
    include_time_blocks : bool
        Whether to include time block features.
    symbol : str
        Asset symbol (e.g., 'EURUSD', 'BTCUSD').

    Returns
    -------
    pd.DataFrame
        Original DataFrame with all macro feature columns added.
    """
    df = df.copy()

    # Step 1: MLR features
    df = compute_mlr_features(df)

    # Step 2: Fibonacci targets
    df = compute_fib_targets(df)

    # Step 3: 132% kill-switch proximity
    df = compute_132_proximity(df, pip_size=pip_size)

    # Step 4: Rekey state machine
    df = compute_rekey_state(df, pip_size=pip_size)

    # Step 5: ILM state
    df = compute_ilm_state(df, pip_size=pip_size)

    # Step 6: Regime ratio
    df = compute_regime_ratio(df, pip_size=pip_size)

    # Step 7: ALL pattern recognition
    if include_patterns:
        df = detect_all_patterns(df, pip_size=pip_size)

    # Step 8: Time blocks
    if include_time_blocks:
        df = _compute_time_blocks(df)

    return df


def get_macro_feature_names() -> list[str]:
    """
    Return the list of macro feature column names.
    """
    return [
        # MLR features
        'mlr_high', 'mlr_low', 'mlr_close', 'mlr_range', 'mlr_mid',
        'bias', 'hours_since_mlr',
        # Fib targets
        'target_minus_25', 'target_minus_50', 'target_minus_100', 'target_minus_168',
        'kill_switch_132',
        'dist_to_25_pct', 'dist_to_50_pct', 'dist_to_132_pct',
        # Kill-switch proximity
        'dist_to_132_pips', 'pct_to_132', 'is_near_132', 'is_critical_132',
        # Rekey state
        'rekey_state', 'rekey_state_label', 'bars_in_current_state', 'wednesday_pm_flag',
        # ILM state
        'asian_high', 'asian_low', 'asian_range', 'asian_range_pips',
        'london_high', 'london_low', 'london_range', 'london_range_pips',
        'ilm_state', 'ilm_state_label', 'impulse_direction', 'is_wilm',
        # Regime ratio
        'regime_ratio', 'regime_label', 'regime_encoded',
        'is_confirmed', 'is_caution', 'is_failed',
        # Pattern recognition — 3-Leg
        'alpha_pattern', 'alpha_direction',
        'beta_pattern', 'beta_direction',
        # Pattern recognition — AB-CD
        'abcd_pattern', 'abcd_direction', 'abcd_extension',
        # Pattern recognition — NY Sweep
        'ny_sweep_pattern', 'ny_sweep_direction',
        # Pattern recognition — Gamma
        'gamma_zone', 'gamma_level', 'gamma_direction',
        # Pattern recognition — Rekey 132
        'rekey_132_triggered', 'rekey_132_breach_idx',
        # Pattern recognition — Rekey Sequence
        'rekey_sequence_active', 'rekey_sequence_bar_count',
        # Pattern recognition — OCC
        'occ_extreme_high', 'occ_extreme_low', 'occ_direction', 'is_at_occ_extreme',
        # Pattern recognition — ILM Zone
        'ilm_zone_state', 'ilm_zone_extension_ratio',
        # Pattern recognition — Density Zone
        'density_zone_high', 'density_zone_low', 'density_zone_range',
        'density_zone_position', 'is_in_density_zone',
        # Pattern recognition — Wednesday Bifurcation
        'wednesday_bifurcation_flag', 'wednesday_bifurcation_stress',
        # Pattern recognition — Hard Exit
        'hard_exit_flag', 'minutes_to_hard_exit',
        # Pattern recognition — Gear Shift
        'gear_shift_active', 'gear_shift_target_modifier',
        # Pattern recognition — Fib Levels
        'fib_retrace_382', 'fib_retrace_500', 'fib_retrace_618', 'fib_retrace_786',
        'closest_fib_retrace', 'dist_to_closest_fib_retrace',
        'fib_extension_1272', 'fib_extension_1618', 'fib_extension_2000', 'fib_extension_2618',
        'closest_fib_extension', 'dist_to_closest_fib_extension',
        # Pattern recognition — Micro-Macro Phase
        'micro_macro_phase', 'micro_macro_alignment', 'micro_macro_phase_encoded',
        # Combined
        'any_pattern',
        # Time blocks
        'day_of_week', 'hour_utc', 'session',
        'is_monday', 'is_friday', 'is_wednesday',
        'is_asian', 'is_london', 'is_ny', 'is_black_zone',
    ]
