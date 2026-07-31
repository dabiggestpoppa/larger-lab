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
    IELM = 2
    WILM = 3


CONFIRMED_THRESHOLD = 1.50
CAUTION_LOW_THRESHOLD = 1.45
IELM_THRESHOLD = 1.50


def _get_session_series(idx: pd.DatetimeIndex) -> pd.Series:
    """Return a Series mapping each bar to its trading session date."""
    if idx.tz is None:
        idx = idx.tz_localize('UTC')
    est = idx.tz_convert('America/New_York')
    hours = est.hour
    dates = est.date
    session = np.where(hours >= 19, dates,
                       (est - pd.Timedelta(days=1)).date)
    return pd.Series(session, index=idx, name='session')


def _compute_daily_df(df: pd.DataFrame, pip_size: float) -> pd.DataFrame:
    """Compute per-day Asian/London session ranges. Returns DataFrame indexed by session date."""
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize('UTC')
    est = idx.tz_convert('America/New_York')

    hours = est.hour
    session = np.where(hours >= 19, est.date,
                       (est - pd.Timedelta(days=1)).date)

    work = pd.DataFrame({
        'high': df['high'].values,
        'low': df['low'].values,
        'close': df['close'].values,
        'session': session,
        'hour_est': hours,
    })

    # Asian session: 19:00-03:00 EST
    asian = work[(work['hour_est'] >= 19) | (work['hour_est'] < 3)]
    # London session: 03:00-09:00 EST
    london = work[(work['hour_est'] >= 3) & (work['hour_est'] < 9)]

    ag = asian.groupby('session').agg(ah=('high', 'max'), al=('low', 'min'))
    ag['ar'] = ag['ah'] - ag['al']
    ag['ar_pips'] = ag['ar'] / pip_size

    lg = london.groupby('session').agg(lh=('high', 'max'), ll=('low', 'min'))
    lg['lr'] = lg['lh'] - lg['ll']
    lg['lr_pips'] = lg['lr'] / pip_size
    lg['lc'] = london.groupby('session')['close'].last()

    daily = ag.join(lg, how='inner')
    daily['amid'] = daily['al'] + daily['ar'] / 2

    # ILM state from extension ratio
    ext = daily['lr'] / daily['ar'].replace(0, np.nan)
    cond = [ext >= IELM_THRESHOLD, ext >= 1.0]
    daily['ilm_state'] = np.select(cond, [ILMState.IELM, ILMState.DAILY_ILM],
                                    default=ILMState.MISALIGNED)
    label_map = {s.value: s.name for s in ILMState}
    daily['ilm_state_label'] = daily['ilm_state'].map(label_map)

    # Impulse direction: bullish if London close > Asian midpoint
    daily['impulse_direction'] = np.where(
        daily['lc'] > daily['amid'], 1,
        np.where(daily['lc'] < daily['amid'], -1, 0))

    # Regime ratio = London range / Asian range
    daily['regime_ratio'] = ext

    return daily


def _apply_wilm(daily: pd.DataFrame, session_s: pd.Series) -> pd.Series:
    """
    Compute WILM flag per bar.
    If Monday is DAILY_ILM or IELM, the entire week (Mon-Fri) is marked WILM.
    """
    wilm_dates = set()
    for day, row in daily.iterrows():
        try:
            if pd.Timestamp(day).dayofweek == 0 and row['ilm_state'] in (ILMState.DAILY_ILM, ILMState.IELM):
                for off in range(5):
                    wilm_dates.add((pd.Timestamp(day) + pd.Timedelta(days=off)).date())
        except Exception:
            continue
    return session_s.isin(wilm_dates).astype(int)


def compute_ilm_state(df: pd.DataFrame, pip_size: float = 0.0001) -> pd.DataFrame:
    """
    Compute ILM (Impulse Level Monitor) state for each bar.

    The ILM measures whether the London session impulse (03:00-09:00 EST)
    aligns with and exceeds the Asian Range (19:00-03:00 EST).

    Adds columns:
        - asian_high, asian_low: Asian session high/low
        - asian_range, asian_range_pips: Asian session range
        - london_high, london_low: London session high/low
        - london_range, london_range_pips: London session range
        - ilm_state: ILMState value (MISALIGNED/DAILY_ILM/IELM/WILM)
        - ilm_state_label: Human-readable state name
        - impulse_direction: 1 (bullish), -1 (bearish), 0 (none)
        - is_wilm: 1 if bar is in a WILM week

    Parameters
    ----------
    df : pd.DataFrame
        Must have DatetimeIndex with UTC timezone and OHLC columns.
    pip_size : float
        Pip size for the asset.

    Returns
    -------
    pd.DataFrame
        DataFrame with ILM columns added.
    """
    df = df.copy()
    session_s = _get_session_series(df.index)
    daily = _compute_daily_df(df, pip_size)

    # Map daily values to bars using pd.Series.map() for C-speed lookup
    df['asian_high'] = session_s.map(daily['ah']).values
    df['asian_low'] = session_s.map(daily['al']).values
    df['asian_range'] = session_s.map(daily['ar']).values
    df['asian_range_pips'] = session_s.map(daily['ar_pips']).values
    df['london_high'] = session_s.map(daily['lh']).values
    df['london_low'] = session_s.map(daily['ll']).values
    df['london_range'] = session_s.map(daily['lr']).values
    df['london_range_pips'] = session_s.map(daily['lr_pips']).values
    df['ilm_state'] = session_s.map(daily['ilm_state']).values
    df['ilm_state_label'] = session_s.map(daily['ilm_state_label']).values
    df['impulse_direction'] = session_s.map(daily['impulse_direction']).values

    # WILM: Monday IELM/DAILY_ILM -> whole week = WILM
    is_wilm = _apply_wilm(daily, session_s)
    df['is_wilm'] = is_wilm.values
    wilm_mask = is_wilm.astype(bool)
    if wilm_mask.any():
        df.loc[wilm_mask, 'ilm_state'] = ILMState.WILM
        df.loc[wilm_mask, 'ilm_state_label'] = 'WILM'

    return df


def compute_regime_ratio(df: pd.DataFrame, pip_size: float = 0.0001) -> pd.DataFrame:
    """
    Compute the 9AM checkpoint regime ratio for each bar.

    Regime Ratio = (03:00-09:00 EST range) / Asian Range

    Classification:
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
    session_s = _get_session_series(df.index)
    daily = _compute_daily_df(df, pip_size)

    rr = session_s.map(daily['regime_ratio'])

    conditions = [
        rr >= CONFIRMED_THRESHOLD,
        rr >= CAUTION_LOW_THRESHOLD,
    ]
    rlab = np.select(conditions, ['CONFIRMED', 'CAUTION'], default='FAILED')
    renc = np.select(conditions, [0.0, 1.0], default=2.0)

    df['regime_ratio'] = rr.values
    df['regime_label'] = rlab
    df['regime_encoded'] = renc
    df['is_confirmed'] = (rlab == 'CONFIRMED').astype(int)
    df['is_caution'] = (rlab == 'CAUTION').astype(int)
    df['is_failed'] = (rlab == 'FAILED').astype(int)
    return df
