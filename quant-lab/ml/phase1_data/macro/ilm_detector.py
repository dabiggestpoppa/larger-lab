"""
ILM (Impulse Level Monitor) Detector
======================================
Computes ILM states and regime ratios from OHLCV data.

Per CEREBUS v4 Manual:
- ILM measures the alignment between Asian Range and London impulse
- Four states: DAILY_ILM, IELM (Extended), WILM (Weekly), MISALIGNED
- Regime Ratio = (3AM-9AM range) / Asian Range
  - CONFIRMED: ratio >= 1.5
  - CAUTION:   ratio 1.45-1.49
  - FAILED:    ratio < 1.45

ILM State Definitions:
- DAILY_ILM: London impulse (3AM-9AM EST) exceeds Asian Range
- IELM: London impulse exceeds 1.5x Asian Range (extended impulse)
- WILM: Weekly ILM — Monday's impulse exceeds weekly Asian Range
- MISALIGNED: London impulse contradicts MLR bias direction

RULE: ILM is computed on the M5 close — wicks are ignored for state determination.
RULE: ILM resets daily. WILM resets weekly (Monday).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from enum import IntEnum


class ILMState(IntEnum):
    """ILM alignment states."""
    MISALIGNED = 0
    DAILY_ILM = 1
    IELM = 2      # Impulse Extended Level Monitor
    WILM = 3      # Weekly ILM


# Regime ratio thresholds
CONFIRMED_THRESHOLD = 1.50
CAUTION_LOW_THRESHOLD = 1.45
CAUTION_HIGH_THRESHOLD = 1.49

# IELM extension threshold
IELM_THRESHOLD = 1.50


def compute_ilm_state(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
) -> pd.DataFrame:
    """
    Compute ILM (Impulse Level Monitor) state for each trading day.

    The ILM measures whether the London session impulse (03:00-09:00 EST)
    aligns with and exceeds the Asian Range (19:00-03:00 EST).

    Adds columns:
        - asian_high: Asian session high
        - asian_low: Asian session low
        - asian_range: Asian session range in price units
        - asian_range_pips: Asian session range in pips
        - london_high: London session (3AM-9AM EST) high
        - london_low: London session low
        - london_range: London session range in price units
        - london_range_pips: London session range in pips
        - ilm_state: ILMState value
        - ilm_state_label: Human-readable ILM state
        - impulse_direction: 1 (bullish), -1 (bearish), 0 (none)

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.
    pip_size : float
        Pip size for the asset (e.g., 0.0001 for EURUSD).

    Returns
    -------
    pd.DataFrame
        DataFrame with ILM columns added.
    """
    df = df.copy()

    # Initialize columns
    for col in ['asian_high', 'asian_low', 'asian_range', 'asian_range_pips',
                'london_high', 'london_low', 'london_range', 'london_range_pips',
                'ilm_state', 'ilm_state_label', 'impulse_direction']:
        if col in ['ilm_state_label']:
            df[col] = 'UNKNOWN'
        elif col == 'impulse_direction':
            df[col] = 0
        else:
            df[col] = np.nan

    # Convert to EST for session detection
    if df.index.tz is None:
        df_utc = df.tz_localize('UTC')
    else:
        df_utc = df.copy()

    df_est = df_utc.tz_convert('America/New_York')

    # Assign each bar to its trading day
    session_dates = []
    for ts in df_est.index:
        if ts.hour >= 19:
            session_dates.append(ts.date())
        else:
            session_dates.append((ts - pd.Timedelta(days=1)).date())

    df_est['_session'] = session_dates
    df_est['_orig_idx'] = df_est.index

    # Compute Asian and London ranges per trading day
    daily_ilm = {}
    for day, group in df_est.groupby('_session'):
        # Asian session: 19:00-03:00 EST
        asian = group[(group.index.hour >= 19) | (group.index.hour < 3)]
        # London session: 03:00-09:00 EST
        london = group[(group.index.hour >= 3) & (group.index.hour < 9)]

        if len(asian) == 0 or len(london) == 0:
            continue

        asian_high = asian['high'].max()
        asian_low = asian['low'].min()
        asian_range = asian_high - asian_low

        london_high = london['high'].max()
        london_low = london['low'].min()
        london_range = london_high - london_low

        # Impulse direction: bullish if London close > Asian midpoint
        london_close = london['close'].iloc[-1] if len(london) > 0 else np.nan
        asian_mid = asian_low + (asian_range / 2) if asian_range > 0 else np.nan

        if not np.isnan(london_close) and not np.isnan(asian_mid):
            impulse_dir = 1 if london_close > asian_mid else (-1 if london_close < asian_mid else 0)
        else:
            impulse_dir = 0

        # ILM state determination
        if asian_range > 0 and london_range > 0:
            extension_ratio = london_range / asian_range

            if extension_ratio >= IELM_THRESHOLD:
                state = ILMState.IELM
            elif extension_ratio >= 1.0:
                state = ILMState.DAILY_ILM
            else:
                state = ILMState.MISALIGNED
        else:
            state = ILMState.MISALIGNED
            extension_ratio = np.nan

        daily_ilm[day] = {
            'asian_high': asian_high,
            'asian_low': asian_low,
            'asian_range': asian_range,
            'asian_range_pips': asian_range / pip_size if pip_size > 0 else np.nan,
            'london_high': london_high,
            'london_low': london_low,
            'london_range': london_range,
            'london_range_pips': london_range / pip_size if pip_size > 0 else np.nan,
            'ilm_state': state,
            'ilm_state_label': state.name,
            'impulse_direction': impulse_dir,
        }

    # Map daily ILM data back to each bar in the DataFrame
    for ts in df.index:
        # Convert to EST to find session date
        ts_est = ts.tz_convert('America/New_York') if ts.tz is not None else ts
        if ts_est.hour >= 19:
            day = ts_est.date()
        else:
            day = (ts_est - pd.Timedelta(days=1)).date()

        if day in daily_ilm:
            data = daily_ilm[day]
            for key, val in data.items():
                df.at[ts, key] = val

    # Compute WILM: Monday's ILM state applies to the whole week
    # WILM = Monday is IELM or DAILY_ILM and the weekly range exceeds threshold
    df['is_wilm'] = 0
    is_monday = df.index.dayofweek == 0
    monday_ilm = df.loc[is_monday, 'ilm_state']

    for monday_ts, state in monday_ilm.items():
        if state in [ILMState.DAILY_ILM, ILMState.IELM]:
            # Apply WILM to all bars in this week (Mon-Fri)
            week_end = monday_ts + pd.Timedelta(days=4, hours=23, minutes=59)
            week_mask = (df.index >= monday_ts) & (df.index <= week_end)
            df.loc[week_mask, 'ilm_state'] = ILMState.WILM
            df.loc[week_mask, 'ilm_state_label'] = 'WILM'
            df.loc[week_mask, 'is_wilm'] = 1

    return df


def compute_regime_ratio(
    df: pd.DataFrame,
    pip_size: float = 0.0001,
) -> pd.DataFrame:
    """
    Compute the 9AM checkpoint regime ratio.

    Regime Ratio = (03:00-09:00 EST range) / Asian Range

    This is the PRIMARY regime classifier in CEREBUS:
    - CONFIRMED: ratio >= 1.50 (strong impulse)
    - CAUTION:   ratio 1.45-1.49 (weak impulse)
    - FAILED:    ratio < 1.45 (no impulse)

    Adds columns:
        - regime_ratio: Raw ratio value
        - regime_label: CONFIRMED / CAUTION / FAILED
        - regime_encoded: 0 (CONFIRMED), 1 (CAUTION), 2 (FAILED)
        - is_confirmed: Binary flag
        - is_caution: Binary flag
        - is_failed: Binary flag

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.
    pip_size : float
        Pip size for the asset.

    Returns
    -------
    pd.DataFrame
        DataFrame with regime ratio columns added.
    """
    df = df.copy()

    # Initialize columns
    df['regime_ratio'] = np.nan
    df['regime_label'] = 'UNKNOWN'
    df['regime_encoded'] = np.nan
    df['is_confirmed'] = 0
    df['is_caution'] = 0
    df['is_failed'] = 0

    # Convert to EST
    if df.index.tz is None:
        df_utc = df.tz_localize('UTC')
    else:
        df_utc = df.copy()

    df_est = df_utc.tz_convert('America/New_York')

    # Assign trading day
    session_dates = []
    for ts in df_est.index:
        if ts.hour >= 19:
            session_dates.append(ts.date())
        else:
            session_dates.append((ts - pd.Timedelta(days=1)).date())

    df_est['_session'] = session_dates

    # Compute regime ratio per trading day
    daily_regime = {}
    for day, group in df_est.groupby('_session'):
        # Asian session: 19:00-03:00 EST
        asian = group[(group.index.hour >= 19) | (group.index.hour < 3)]
        # London impulse: 03:00-09:00 EST
        london = group[(group.index.hour >= 3) & (group.index.hour < 9)]

        if len(asian) == 0 or len(london) == 0:
            continue

        asian_range = asian['high'].max() - asian['low'].min()
        london_range = london['high'].max() - london['low'].min()

        if asian_range > 0:
            ratio = london_range / asian_range
        else:
            ratio = np.nan

        if not np.isnan(ratio):
            if ratio >= CONFIRMED_THRESHOLD:
                label = 'CONFIRMED'
                encoded = 0
            elif ratio >= CAUTION_LOW_THRESHOLD:
                label = 'CAUTION'
                encoded = 1
            else:
                label = 'FAILED'
                encoded = 2
        else:
            label = 'UNKNOWN'
            encoded = np.nan

        daily_regime[day] = {
            'regime_ratio': ratio,
            'regime_label': label,
            'regime_encoded': encoded,
        }

    # Map back to DataFrame
    for ts in df.index:
        ts_est = ts.tz_convert('America/New_York') if ts.tz is not None else ts
        if ts_est.hour >= 19:
            day = ts_est.date()
        else:
            day = (ts_est - pd.Timedelta(days=1)).date()

        if day in daily_regime:
            data = daily_regime[day]
            df.at[ts, 'regime_ratio'] = data['regime_ratio']
            df.at[ts, 'regime_label'] = data['regime_label']
            df.at[ts, 'regime_encoded'] = data['regime_encoded']

    # Binary flags
    df['is_confirmed'] = (df['regime_label'] == 'CONFIRMED').astype(int)
    df['is_caution'] = (df['regime_label'] == 'CAUTION').astype(int)
    df['is_failed'] = (df['regime_label'] == 'FAILED').astype(int)

    return df
