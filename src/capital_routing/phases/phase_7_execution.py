"""
Phase 7 - execution engine (brief sections 2-4).

Builds the (pair, delay, hold) execution grid from the frozen Phase 3 panel:
causal forward returns with entry at t0+delay and exit at t0+delay+hold,
plus MFE/MAE paths, time-to-MFE/MAE, realized volatility, and transaction
costs (spread/commission + swap for multi-day holds).

Entry convention (causal): the signal is available at the event timestamp t0.
Entry price = close of the first bar strictly AFTER t0 + delay (delay >= 0).
This guarantees no look-ahead: at entry time t0+delay we only use bars that
have already closed. Exit price = close of the last bar at or before
t0 + delay + hold. The event bar itself is never part of the trade window
(the first entry bar is strictly after t0 + delay, and for delay=0 that is
the bar AFTER the event bar).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_7_families import FAMILIES, ONE_WAY_COST_BPS, SPLIT, swap_bps_per_day

NS_PER_HOUR = 3600 * 10**9

DELAYS = [0, 1, 2, 3, 4]
EUR_JPY_HOLDS = [4, 6, 8, 12]
JPY_CHF_HOLDS = [24, 36, 48, 60, 72]


def _bar_index(grid_ns: np.ndarray, ts_ns: int, side: str) -> int:
    """searchsorted helper."""
    return int(np.searchsorted(grid_ns, ts_ns, side=side))


def _window(grid_ns: np.ndarray, ts_ns: int, delay_h: int, hold_h: int) -> Tuple[int, int]:
    """
    (entry_idx, exit_idx) inclusive for an event at ts_ns with delay and hold.
    entry: first bar with time > ts_ns + delay*1h  (strictly after)
    exit:  last bar with time <= ts_ns + (delay+hold)*1h
    Returns exit < entry when the window is empty.
    """
    entry_after = ts_ns + delay_h * NS_PER_HOUR
    exit_at = ts_ns + (delay_h + hold_h) * NS_PER_HOUR
    entry = _bar_index(grid_ns, entry_after, side="right")  # first > entry_after
    exit_i = _bar_index(grid_ns, exit_at, side="right") - 1  # last <= exit_at
    return entry, exit_i


def build_execution_grid(
    events: pd.DataFrame,
    panel: pd.DataFrame,
    pairs: List[str],
    delays: List[int],
    holds: List[int],
    apply_costs: bool = True,
) -> pd.DataFrame:
    """
    For every event, every pair, every delay and hold: return (bps), MFE (bps),
    MAE (bps, signed), time-to-MFE (h), time-to-MAE (h), realized vol (bps/h),
    gross and net (cost-adjusted) values.

    Returns a long DataFrame with one row per (event, pair, delay, hold).
    """
    grid_ns = panel.index.values.astype("int64")
    closes = panel[[f"{p}_close" for p in pairs]].to_numpy(dtype=float)
    closes_log = np.log(closes)
    pair_col = {p: i for i, p in enumerate(pairs)}
    n_events = len(events)

    ts = pd.to_datetime(events["event_start"], utc=True)
    ts_ns_arr = np.array([t.value for t in ts])

    rows = []
    for idx in range(n_events):
        t0 = int(ts_ns_arr[idx])
        for d in delays:
            for h in holds:
                entry, exit_i = _window(grid_ns, t0, d, h)
                if exit_i < entry:
                    continue
                for p in pairs:
                    ci = pair_col[p]
                    entry_price = closes_log[entry, ci]
                    exit_price = closes_log[exit_i, ci]
                    if not (np.isfinite(entry_price) and np.isfinite(exit_price)):
                        continue
                    gross_bps = (exit_price - entry_price) * 1e4

                    # path within (entry, exit] for MFE/MAE
                    seg = closes_log[entry:exit_i + 1, ci]
                    seg = seg[np.isfinite(seg)]
                    if len(seg) < 2:
                        continue
                    rel = seg - seg[0]
                    mfe = float(np.max(rel)) * 1e4
                    mae = float(np.min(rel)) * 1e4
                    t_mfe = float(np.argmax(rel)) + 1  # hours from entry
                    t_mae = float(np.argmin(rel)) + 1

                    # realized volatility: hourly log-return std over the window
                    rv = float(np.std(np.diff(seg))) if len(seg) > 2 else np.nan
                    rv_bps = rv * 1e4 if np.isfinite(rv) else np.nan

                    if apply_costs:
                        one_way = ONE_WAY_COST_BPS[p]
                        # spread/commission only here; swap added with sign in
                        # orient_trade (short carry is the reverse of long carry)
                        cost = 2.0 * one_way
                    else:
                        cost = 0.0

                    rows.append({
                        "event_id": events.iloc[idx]["event_id"],
                        "pair": p, "delay_h": d, "hold_h": h,
                        "gross_return_bps": gross_bps,
                        "net_return_bps": gross_bps - cost,
                        "mfe_bps": mfe, "mae_bps": mae,
                        "time_to_mfe_h": t_mfe, "time_to_mae_h": t_mae,
                        "rv_bps_per_h": rv_bps,
                        "cost_bps": cost,
                    })
    out = pd.DataFrame(rows)
    if len(out) == 0:
        return out
    meta = events[["event_id", "event_start", "origin_currency", "direction",
                   "severity", "session"]].copy()
    out = out.merge(meta, on="event_id", how="left")
    # split assignment (nested chronological)
    ts_e = pd.to_datetime(out["event_start"], utc=True)
    sel = (ts_e >= SPLIT["inner_sel"]["start"]) & (ts_e < SPLIT["inner_sel"]["end"])
    val = (ts_e >= SPLIT["inner_val"]["start"]) & (ts_e < SPLIT["inner_val"]["end"])
    out["split"] = np.where(sel, "inner_sel",
                            np.where(val, "inner_val", "untouched"))
    return out


def orient_trade(g: pd.DataFrame, family: Dict) -> pd.DataFrame:
    """
    Apply the family trade direction. Returns a copy with directional returns:
    for 'long': +pair return; 'short': -pair return; 'long_chf':
    CHFJPY is long, CHF-quote pairs (USDCHF/EURCHF/GBPCHF) are short.
    Also adds cost_signed (costs always negative) and net directional bps.
    """
    out = g.copy()
    trade = family["trade"]
    if trade == "long":
        out["dir"] = 1.0
    elif trade == "short":
        out["dir"] = -1.0
    elif trade == "long_chf":
        out["dir"] = np.where(out["pair"] == "CHFJPY", 1.0, -1.0)
    else:
        raise ValueError(f"unknown trade type {trade}")
    out["dir_return_bps"] = out["dir"] * out["gross_return_bps"]
    out["dir_mfe_bps"] = np.where(out["dir"] > 0, out["mfe_bps"], -out["mae_bps"])
    out["dir_mae_bps"] = np.where(out["dir"] > 0, out["mae_bps"], -out["mfe_bps"])
    # signed swap: long carry = +swap; short carry = -swap
    swap_signed = out["dir"] * out["hold_h"] / 24.0 * out["pair"].map(swap_bps_per_day)
    out["cost_bps"] = out["cost_bps"] + swap_signed
    out["dir_net_bps"] = out["dir_return_bps"] - out["cost_bps"]
    return out


def equal_risk_basket(g: pd.DataFrame, basket_pairs: List[str],
                      risk_scale: float = 100.0) -> pd.DataFrame:
    """
    Equal-risk JPY/CHF basket: for each (event, delay, hold) group, weight each
    pair by inverse of its realized vol (or 1.0 when missing), normalize weights
    to sum to 1, and compute the vol-normalized basket return. risk_scale is the
    target annualized vol in bps/h applied to the basket weights.
    """
    sub = g[g["pair"].isin(basket_pairs)].copy()
    if len(sub) == 0:
        return pd.DataFrame()
    sub["inv_vol"] = np.where(sub["rv_bps_per_h"].fillna(0) > 0,
                              1.0 / sub["rv_bps_per_h"], 1.0)
    grp = sub.groupby(["event_id", "delay_h", "hold_h"])
    parts = []
    for (eid, d, h), gr in grp:
        w = gr["inv_vol"].to_numpy()
        w = w / w.sum()
        ret = (gr["dir_return_bps"].to_numpy() * w).sum()
        mfe = (gr["dir_mfe_bps"].to_numpy() * w).sum()
        mae = (gr["dir_mae_bps"].to_numpy() * w).sum()
        cost = (gr["cost_bps"].to_numpy() * w).sum()
        rv = (gr["rv_bps_per_h"].fillna(np.nan).to_numpy() * w).sum()
        parts.append({
            "event_id": eid, "pair": "BASKET", "delay_h": d, "hold_h": h,
            "gross_return_bps": ret, "dir_return_bps": ret,
            "dir_mfe_bps": mfe, "dir_mae_bps": mae,
            "cost_bps": cost, "dir_net_bps": ret - cost,
            "rv_bps_per_h": rv, "dir": 1.0,
        })
    b = pd.DataFrame(parts)
    if len(b) == 0:
        return b
    meta = g[["event_id", "event_start", "origin_currency", "direction",
              "severity", "session", "split"]].drop_duplicates("event_id")
    return b.merge(meta, on="event_id", how="left")


def routing_efficiency(row: pd.Series) -> float:
    """RoutingEfficiency = E[MFE] / (E[MAE] + transaction cost)."""
    mae = abs(row["mae_bps"]) if pd.notna(row["mae_bps"]) else 0.0
    cost = row["cost_bps"] if pd.notna(row["cost_bps"]) else 0.0
    denom = mae + cost
    if denom <= 0:
        return np.nan
    return float(row["mfe_bps"]) / denom
