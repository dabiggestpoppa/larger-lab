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
6. Pattern recognition (from pattern_recognizer)
7. Time block features (computed here)

Total macro features per candle: ~20
Combined with micro features: ~30 total

RULE: All features are computed on M5 closes unless otherwise specified.
RULE: No future leakage — all features use only past/current data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .mlr_engine import compute_mlr_features, compute_fib_targets
from .kill_switch import compute_132_proximity, compute_rekey_state
from .ilm_detector import compute_ilm_state, compute_regime_ratio
from .pattern_recognizer import detect_alpha_leg, detect_beta_leg, detect_abcd, detect_occ_extreme


# Session boundaries (UTC)
SESSION_ASIAN_START = 20    # 20:00 UTC = 15:00 EST (Asian afternoon)
SESSION_ASIAN_END = 2       # 02:00 UTC = 21:00 EST (Asian evening)
SESSION_LONDON_START = 7    # 07:00 UTC = 03:00 EST (London open)
SESSION_LONDON_END = 12     # 12:00 UTC = 08:00 EST (London morning)
SESSION_NY_START = 12       # 12:00 UTC = 08:00 EST (NY open)
SESSION_NY_END = 17         # 17:00 UTC = 13:00 EST (NY afternoon)
BLACK_ZONE_START = 17       # 17:00 UTC = 13:00 EST
BLACK_ZONE_END = 20         # 20:00 UTC = 15:00 EST


def _compute_time_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute time block features for each candle.

    Adds columns:
        - day_of_week: 0=Monday, 4=Friday
        - hour_utc: Hour of day in UTC
        - session: 'ASIAN', 'LONDON', 'NY', 'BLACK_ZONE'
        - is_monday: Binary flag
        - is_friday: Binary flag
        - is_wednesday: Binary flag
        - hours_since_mlr: Hours since MLR formation (filled from MLR engine)

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone.

    Returns
    -------
    pd.DataFrame
        DataFrame with time block columns added.
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
        (hours >= SESSION_ASIAN_START) | (hours < SESSION_ASIAN_END),
        (hours >= SESSION_LONDON_START) & (hours < SESSION_LONDON_END),
        (hours >= SESSION_NY_START) & (hours < SESSION_NY_END),
        (hours >= BLACK_ZONE_START) & (hours < BLACK_ZONE_START + 3),
    ]
    choices = ['ASIAN', 'LONDON', 'NY', 'BLACK_ZONE']
    df['session'] = np.select(conditions, choices, default='OFF_HOURS')

    # One-hot encode session
    for sess in ['ASIAN', 'LONDON', 'NY', 'BLACK_ZONE']:
        df[f'is_{sess.lower()}'] = (df['session'] == sess).astype(int)

    return df


def build_macro_feature_matrix(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
    include_patterns: bool = True,
    include_time_blocks: bool = True,
) -> pd.DataFrame:
    """
    Build the complete macro feature matrix.

    This is the MAIN ENTRY POINT for macro feature computation.
    It chains all macro feature modules in the correct order.

    Pipeline:
    1. MLR features → mlr_engine.compute_mlr_features
    2. Fib targets → mlr_engine.compute_fib_targets
    3. 132% proximity → kill_switch.compute_132_proximity
    4. Rekey state → kill_switch.compute_rekey_state
    5. ILM state → ilm_detector.compute_ilm_state
    6. Regime ratio → ilm_detector.compute_regime_ratio
    7. Pattern recognition → pattern_recognizer (optional)
    8. Time blocks → _compute_time_blocks (optional)

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.
    pip_size : float
        Pip size for the asset (e.g., 0.0001 for EURUSD, 0.01 for USDJPY).
    include_patterns : bool
        Whether to include pattern recognition features (slower).
    include_time_blocks : bool
        Whether to include time block features.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with all macro feature columns added.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.read_parquet('EURUSD_M5.parquet')
    >>> df_macro = build_macro_feature_matrix(df, pip_size=0.0001)
    >>> print([c for c in df_macro.columns if c not in ['open','high','low','close','volume']])
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

    # Step 7: Pattern recognition (optional — computationally expensive)
    if include_patterns:
        df = detect_alpha_leg(df)
        df = detect_beta_leg(df)
        df = detect_abcd(df)
        df = detect_occ_extreme(df)

        # Combined pattern flag
        df['any_pattern'] = (
            (df['alpha_pattern'] == 1) |
            (df['beta_pattern'] == 1) |
            (df['abcd_pattern'] == 1)
        ).astype(int)

    # Step 8: Time blocks
    if include_time_blocks:
        df = _compute_time_blocks(df)

    return df


def get_macro_feature_names() -> list[str]:
    """
    Return the list of macro feature column names.

    Returns
    -------
    list[str]
        List of feature names that build_macro_feature_matrix adds.
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
        # Pattern recognition
        'alpha_pattern', 'alpha_direction',
        'beta_pattern', 'beta_direction',
        'abcd_pattern', 'abcd_direction', 'abcd_extension',
        'occ_extreme_high', 'occ_extreme_low', 'occ_direction', 'is_at_occ_extreme',
        'any_pattern',
        # Time blocks
        'day_of_week', 'hour_utc', 'session',
        'is_monday', 'is_friday', 'is_wednesday',
        'is_asian', 'is_london', 'is_ny', 'is_black_zone',
    ]
