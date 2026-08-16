"""
CR-RISK-BLOCK1 R1.3 — Portfolio Heat.

Heat = aggregate live account-risk commitment through time. For every open
position the per-position heat at time t is the one-sigma adverse move over the
REMAINING hold:

    heat_i(t) = pos_i * rv_eff_i * sqrt(remaining_hours_i(t)) = TARGET_VOL * sqrt(rem)

(pos*rv_eff = TARGET_VOL by construction, so heat is a deterministic function of
remaining time — 24.49 bps at entry, decaying to 0 at exit.)

Per timestamp (hourly, exact state book):
  - gross_heat        = sum of per-position heat
  - net_heat          = sum of dir * per-position heat (signed)
  - same_dir_heat     = heat on the side of net exposure (longs if net >= 0)
  - opposing_heat     = gross - same_dir_heat
  - unrealized_pnl_bps= mark-to-market of open positions (frozen H1 panel)
  - portfolio_cae_bps = sum of each open position's cumulative adverse excursion
  - max_simul_cae     = running maximum of portfolio_cae

Heat distributions are reported for the instantaneous hourly series and for
rolling 1/3/6/12/24h windows (median, p75, p90, p95, p99, max).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .phase_7_execution import _window
from .phase_r1_ledger import TARGET_VOL, PAIR

ROLLING_WINDOWS_H = [1, 3, 6, 12, 24]
HEAT_METRICS = ["gross_heat", "abs_net_heat", "same_dir_heat", "opposing_heat",
                "unrealized_pnl_bps", "portfolio_cae_bps", "max_simul_cae"]
# in-market scope only applies to risk-commitment metrics
RISK_METRICS = ["gross_heat", "abs_net_heat", "same_dir_heat", "opposing_heat"]


def build_marks(ledger: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Per-trade hourly marked PnL path from the frozen H1 panel.

    Uses the identical window logic as the execution grid, so
    max(mark_bps / pos) == dir_mfe_bps to float tolerance.
    """
    grid_ns = panel.index.values.astype("int64")
    closes = panel[f"{PAIR}_close"].to_numpy(dtype=float)
    closes_log = np.log(closes)
    rows = []
    entry_ts = pd.to_datetime(ledger["entry_ts"], utc=True).to_numpy()
    ts = pd.to_datetime(ledger["event_start"], utc=True)
    for i in range(len(ledger)):
        row = ledger.iloc[i]
        cfg = _cfg(row["family"])
        t0 = int(ts.iloc[i].value)
        entry, exit_i = _window(grid_ns, t0, cfg["delay_h"], cfg["hold_h"])
        if exit_i < entry:
            continue
        seg = closes_log[entry:exit_i + 1]
        base = seg[0]
        pos = float(row["pos"])
        d = float(row["dir"])
        for k in range(len(seg)):
            mark = d * (seg[k] - base) * 1e4 * pos
            rows.append({"event_id": row["event_id"], "mark_time": panel.index[entry + k],
                         "entry_ts": entry_ts[i], "h_since_entry": k, "mark_bps": float(mark)})
    marks = pd.DataFrame(rows)
    if len(marks) == 0:
        return marks
    marks = marks.sort_values(["event_id", "h_since_entry"]).reset_index(drop=True)
    marks["cum_min_bps"] = marks.groupby("event_id")["mark_bps"].cummin()
    marks["cae_bps"] = (-marks["cum_min_bps"]).clip(lower=0.0)
    return marks


def _cfg(family: str):
    from .phase_7_5_audit import FROZEN_CONFIGS
    return FROZEN_CONFIGS[family]


def build_heat(ledger: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """Hourly portfolio-heat frame (one row per timestamp)."""
    entry = pd.to_datetime(ledger["entry_ts"], utc=True)
    exit_ = pd.to_datetime(ledger["exit_ts"], utc=True)
    ts_min = entry.min().floor("h")
    ts_max = exit_.max().ceil("h")
    idx = pd.date_range(ts_min, ts_max, freq="h")
    dir_arr = ledger["dir"].to_numpy(dtype=float)
    pos_arr = ledger["pos"].to_numpy(dtype=float)
    # rv_eff such that pos*rv_eff = TARGET_VOL (matches sizing convention)
    rv_eff = TARGET_VOL / np.where(pos_arr > 0, pos_arr, 1.0)
    entry_ns = entry.to_numpy(dtype="int64")
    exit_ns = exit_.to_numpy(dtype="int64")
    HOUR_NS = int(3600 * 1e9)

    marks_sorted = marks.sort_values("mark_time") if len(marks) else marks

    rows = []
    max_cae = 0.0
    for t in idx:
        t_ns = int(t.value)
        active_mask = (entry_ns <= t_ns) & (exit_ns > t_ns)
        if not active_mask.any():
            rows.append({"ts": t, "n_open": 0, "gross_heat": 0.0, "net_heat": 0.0,
                         "abs_net_heat": 0.0, "long_heat": 0.0, "short_heat": 0.0,
                         "same_dir_heat": 0.0, "opposing_heat": 0.0,
                         "unrealized_pnl_bps": 0.0, "portfolio_cae_bps": 0.0,
                         "max_simul_cae": 0.0})
            continue
        rem_h = np.maximum((exit_ns[active_mask] - t_ns) / HOUR_NS, 0.0)
        heat = TARGET_VOL * np.sqrt(rem_h)
        d = dir_arr[active_mask]
        gross = float(heat.sum())
        net = float((d * heat).sum())
        long_heat = float(heat[d > 0].sum()) if (d > 0).any() else 0.0
        short_heat = float(heat[d < 0].sum()) if (d < 0).any() else 0.0
        same_dir = long_heat if net >= 0 else short_heat
        eids = set(ledger.loc[active_mask, "event_id"].tolist())
        sub = marks_sorted[marks_sorted["event_id"].isin(eids) & (marks_sorted["mark_time"] <= t)]
        unreal = 0.0
        cae = 0.0
        if len(sub):
            last = sub.groupby("event_id").last()
            unreal = float(last["mark_bps"].sum())
            cae = float(last["cae_bps"].sum())
        max_cae = max(max_cae, cae)
        rows.append({"ts": t, "n_open": int(active_mask.sum()), "gross_heat": gross,
                     "net_heat": net, "abs_net_heat": abs(net),
                     "long_heat": long_heat, "short_heat": short_heat,
                     "same_dir_heat": same_dir, "opposing_heat": gross - same_dir,
                     "unrealized_pnl_bps": unreal, "portfolio_cae_bps": cae,
                     "max_simul_cae": max_cae})
    return pd.DataFrame(rows)


def heat_distributions(heat: pd.DataFrame) -> pd.DataFrame:
    """Quantile profile of each heat metric, instantaneous + rolling windows."""
    rows = []
    for metric in HEAT_METRICS:
        scopes = ["all_hours"] if metric not in RISK_METRICS else ["all_hours", "in_market"]
        for scope in scopes:
            series = heat[metric].copy()
            if scope == "in_market":
                series = series[heat["n_open"] > 0]
            for w in ROLLING_WINDOWS_H:
                s = series.rolling(w, min_periods=1).mean()
                rows.append({
                    "metric": metric, "scope": scope, "window_h": w,
                    "median": float(s.median()), "p75": float(s.quantile(0.75)),
                    "p90": float(s.quantile(0.90)), "p95": float(s.quantile(0.95)),
                    "p99": float(s.quantile(0.99)), "max": float(s.max()),
                    "mean": float(s.mean()),
                })
    return pd.DataFrame(rows)
