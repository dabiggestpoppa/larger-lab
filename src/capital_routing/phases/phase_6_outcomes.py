"""
Phase 6 - Forward outcome engine.
CR-P6-FORWARD-ROUTING-STUDY-01

Computes, for every frozen Phase 5 event, the forward cumulative latent factor
movement and forward pair returns at the fixed horizons, plus factor/pair
MFE-MAE path statistics and destination leadership.

No-lookahead is enforced by construction: the forward window starts at the
first bar STRICTLY AFTER the event timestamp (the event bar is excluded) and
every statistic is a trailing function of data <= T at the event time.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import CURRENCIES, HORIZONS, HORIZONS_OPTIONAL, PAIRS

NS_PER_HOUR = 3600 * 10**9

FACTOR_METRICS = ["forward", "abs", "dir", "rank", "rank_change", "voladj", "mfe", "mae"]
PAIR_METRICS = ["return", "mfe", "mae", "rv"]


def _window_bounds(grid_ns: np.ndarray, ts_ns: int, horizon_h: int) -> tuple:
    """
    Forward window for an event at ts_ns: bars with grid time in
    (ts_ns, ts_ns + horizon_h]. The event bar itself is excluded.
    Returns (start, end) inclusive indices, or start > end when empty.
    """
    start = int(np.searchsorted(grid_ns, ts_ns, side="left")) + 1
    end = int(np.searchsorted(grid_ns, ts_ns + horizon_h * NS_PER_HOUR, side="right")) - 1
    return start, end


def _prefix_stats(values: np.ndarray) -> tuple:
    """(max_cumulative, min_cumulative) of the running sum along axis 0."""
    prefix = np.cumsum(values, axis=0)
    return prefix.max(axis=0), prefix.min(axis=0)


def _currency_rank(cum: np.ndarray, ci: int) -> float:
    """Rank of currency ci among the cumulative factor values (1 = strongest)."""
    v = cum[ci]
    if not np.isfinite(v):
        return np.nan
    others = np.nan_to_num(cum, nan=-np.inf)
    return 1.0 + float(np.sum(others > v))


def build_forward_outcomes(
    events: pd.DataFrame,
    comp: pd.DataFrame,
    panel: pd.DataFrame,
    horizons: Optional[List[int]] = None,
    horizons_optional: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Compute forward factor and pair outcomes for every event.

    comp: event_components frame indexed by UTC H1 timestamp.
    panel: Phase 3 strict common panel indexed by UTC H1 timestamp with
        {PAIR}_close columns.

    Returns a wide per-event DataFrame with columns:
      {CUR}_forward_{h} / _abs_ / _dir_ / _rank_ / _rank_change_ / _voladj_ /
      _mfe_ / _mae_, destination_{h}, and {PAIR}_return_{h} / _mfe_ / _mae_ / _rv_.
    Optional horizons carry only forward/abs/rank/return columns.
    """
    horizons = horizons or HORIZONS
    horizons_optional = horizons_optional or HORIZONS_OPTIONAL
    all_h = horizons + horizons_optional

    factor_cols = [f"{c}_factor" for c in CURRENCIES]
    rank_cols = [f"{c}_rank" for c in CURRENCIES]
    vol_cols = [f"{c}_volatility" for c in CURRENCIES]

    F = comp[factor_cols].to_numpy(dtype=float)
    RANK_T = comp[rank_cols].to_numpy(dtype=float)
    VOL_T = comp[vol_cols].to_numpy(dtype=float)
    grid_f = comp.index.values.astype("int64")

    closes = panel[[f"{p}_close" for p in PAIRS]].to_numpy(dtype=float)
    grid_p = panel.index.values.astype("int64")
    # per-bar log returns: log(close[t] / close[t-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        rets = np.diff(np.log(closes), axis=0)
    rets[np.isinf(rets)] = np.nan

    rows = []
    ts = pd.to_datetime(events["event_start"], utc=True)

    # Baseline rank/volatility at the EVENT BAR: the event's own comp row.
    # (Events are a subset of the comp grid, so event position != comp row.)
    event_pos = np.minimum(
        np.searchsorted(grid_f, np.array([t.value for t in ts]), side="left"),
        len(RANK_T) - 1,
    )
    RANK_EVT = RANK_T[event_pos]
    VOL_EVT = VOL_T[event_pos]

    for idx, t in enumerate(ts):
        ts_ns = int(t.value)
        row = {"event_id": events.iloc[idx]["event_id"]}

        for h in all_h:
            core = h in horizons
            s_f, e_f = _window_bounds(grid_f, ts_ns, h)
            if s_f <= e_f:
                win = F[s_f:e_f + 1]
                cum = win.sum(axis=0)
                mfe, mae = _prefix_stats(win)
            else:
                cum = np.full(len(CURRENCIES), np.nan)
                mfe = np.full(len(CURRENCIES), np.nan)
                mae = np.full(len(CURRENCIES), np.nan)

            # destination leader: strongest forward cumulative factor
            if np.isnan(cum).all():
                dest = None
            else:
                dest = CURRENCIES[int(np.argmax(np.nan_to_num(cum, nan=-np.inf)))]
            row[f"destination_{h}"] = dest

            for ci, c in enumerate(CURRENCIES):
                v = cum[ci]
                row[f"{c}_forward_{h}"] = v if np.isfinite(v) else np.nan
                row[f"{c}_abs_{h}"] = abs(v) if np.isfinite(v) else np.nan
                row[f"{c}_dir_{h}"] = (1 if v > 0 else (-1 if v < 0 else 0)) if np.isfinite(v) else np.nan
                if core:
                    r_h = _currency_rank(cum, ci)
                    r_T = RANK_EVT[idx, ci] if np.isfinite(RANK_EVT[idx, ci]) else np.nan
                    row[f"{c}_rank_{h}"] = r_h
                    row[f"{c}_rank_change_{h}"] = (r_T - r_h) if np.isfinite(r_T) else np.nan
                    vol = VOL_EVT[idx, ci]
                    row[f"{c}_voladj_{h}"] = (v / vol) if (np.isfinite(v) and vol and vol > 0) else np.nan
                    row[f"{c}_mfe_{h}"] = mfe[ci] if np.isfinite(mfe[ci]) else np.nan
                    row[f"{c}_mae_{h}"] = mae[ci] if np.isfinite(mae[ci]) else np.nan

            # pair-space outcomes
            s_p, e_p = _window_bounds(grid_p, ts_ns, h)
            if s_p >= 1 and s_p <= e_p:
                base = closes[idx_p_baseline(grid_p, ts_ns)]
                end_close = closes[e_p]
                with np.errstate(divide="ignore", invalid="ignore"):
                    fwd = np.log(end_close / base)
                fwd[np.isinf(fwd)] = np.nan
                win_rets = rets[s_p - 1:e_p]  # rets[j] is return of bar j (close[j]/close[j-1])
                if len(win_rets) >= 1:
                    prefix = np.cumsum(win_rets, axis=0)
                    mfe_p = prefix.max(axis=0)
                    mae_p = prefix.min(axis=0)
                else:
                    mfe_p = np.full(len(PAIRS), np.nan)
                    mae_p = np.full(len(PAIRS), np.nan)
                rv = np.full(len(PAIRS), np.nan)
                if len(win_rets) >= 2:
                    rv = win_rets.std(axis=0, ddof=1)
            else:
                fwd = np.full(len(PAIRS), np.nan)
                mfe_p = np.full(len(PAIRS), np.nan)
                mae_p = np.full(len(PAIRS), np.nan)
                rv = np.full(len(PAIRS), np.nan)

            for pi, p in enumerate(PAIRS):
                row[f"{p}_return_{h}"] = fwd[pi] if np.isfinite(fwd[pi]) else np.nan
                if core:
                    row[f"{p}_mfe_{h}"] = mfe_p[pi] if np.isfinite(mfe_p[pi]) else np.nan
                    row[f"{p}_mae_{h}"] = mae_p[pi] if np.isfinite(mae_p[pi]) else np.nan
                    row[f"{p}_rv_{h}"] = rv[pi] if np.isfinite(rv[pi]) else np.nan

        rows.append(row)

    out = pd.DataFrame(rows)
    out = events[["event_id"]].merge(out, on="event_id", how="left")
    return out


def idx_p_baseline(grid_ns: np.ndarray, ts_ns: int) -> int:
    """Index of the event bar (first grid bar >= ts)."""
    return int(np.searchsorted(grid_ns, ts_ns, side="left"))


def destination_at_h(outcomes: pd.DataFrame, horizons: Optional[List[int]] = None) -> pd.DataFrame:
    """Long-form destination leadership: one row per (event_id, horizon)."""
    horizons = horizons or HORIZONS
    parts = []
    for h in horizons:
        sub = outcomes[["event_id", f"destination_{h}"]].copy()
        sub.columns = ["event_id", "destination"]
        sub["horizon_h"] = h
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)
