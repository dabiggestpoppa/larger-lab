"""
Phase 7.5 - portfolio-level A+B simulation (brief section 4).

One chronological strategy:
  A: EUR accumulation event -> delay 2h -> LONG USDJPY  -> fixed 6h hold
  B: EUR liquidation event -> delay 1h -> SHORT USDJPY -> fixed 6h hold

Models actual signal overlap, concurrency, and four execution policies.
Policy selection uses development only (inner_sel + inner_val); the
RELATIONSHIP_CONFIRMED_OOS segment is evaluated only after policy freeze.

Policies:
  P0 = allow every qualifying event (unconstrained)
  P1 = one position at a time (skip new signal while any position open)
  P2 = same-direction events merge/refresh; opposite event closes and reverses
  P3 = cooldown after entry (no new entry within cooldown_h of last entry)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL, metric_units


def build_trades(g_a: pd.DataFrame, g_b: pd.DataFrame,
                 target_vol: float = 10.0) -> pd.DataFrame:
    """
    Build the per-event trade frame for A and B at their frozen configs,
    with vol-normalized PnL (bps), entry/exit timestamps.
    """
    frames = []
    for fid in ["A", "B"]:
        cfg = FROZEN_CONFIGS[fid]
        g = g_a if fid == "A" else g_b
        sub = g[(g["pair"] == cfg["pair"])
                & (g["delay_h"] == cfg["delay_h"])
                & (g["hold_h"] == cfg["hold_h"])].copy()
        ts = pd.to_datetime(sub["event_start"], utc=True)
        sub["entry_ts"] = ts + pd.Timedelta(hours=cfg["delay_h"])
        sub["exit_ts"] = ts + pd.Timedelta(hours=cfg["delay_h"] + cfg["hold_h"])
        sub["family"] = fid
        sub["dir"] = 1.0 if cfg["trade"] == "long" else -1.0
        # vol-normalized position
        rv = sub["rv_bps_per_h"].to_numpy(dtype=float)
        pos = np.where(np.isfinite(rv) & (rv > 0), target_vol / rv, 1.0)
        sub["pos"] = pos
        sub["pnl_bps"] = sub["dir_net_bps"].to_numpy(dtype=float) * pos
        sub["gross_pnl_bps"] = sub["dir_return_bps"].to_numpy(dtype=float) * pos
        sub["cost_pnl_bps"] = sub["cost_bps"].to_numpy(dtype=float) * pos
        sub["split"] = sub["split"].replace("untouched", OOS_LABEL)
        frames.append(sub[["event_id", "event_start", "family", "dir", "pos",
                           "entry_ts", "exit_ts", "pnl_bps", "gross_pnl_bps",
                           "cost_pnl_bps", "split", "hold_h"]])
    out = pd.concat(frames, ignore_index=True).sort_values("entry_ts").reset_index(drop=True)
    return out


def concurrency_analysis(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Hourly position book: for each hour, count active positions, same/opposite
    direction overlaps, gross/net exposure (units of normalized position).
    """
    rows = []
    ts_min = trades["entry_ts"].min().floor("h")
    ts_max = trades["exit_ts"].max().ceil("h")
    idx = pd.date_range(ts_min, ts_max, freq="h")
    for t in idx:
        active = trades[(trades["entry_ts"] <= t) & (trades["exit_ts"] > t)]
        n = len(active)
        if n == 0:
            rows.append({"ts": t, "n_active": 0, "long_count": 0, "short_count": 0,
                         "same_dir_overlap_pairs": 0, "opp_dir_overlap_pairs": 0,
                         "gross_exposure": 0.0, "net_exposure": 0.0})
            continue
        longs = active[active["dir"] > 0]
        shorts = active[active["dir"] < 0]
        nl, ns = len(longs), len(shorts)
        same = max(nl * (nl - 1) // 2, 0) + max(ns * (ns - 1) // 2, 0)
        opp = nl * ns
        gross = float(active["pos"].sum())
        net = float((active["dir"] * active["pos"]).sum())
        rows.append({"ts": t, "n_active": n, "long_count": nl, "short_count": ns,
                     "same_dir_overlap_pairs": same, "opp_dir_overlap_pairs": opp,
                     "gross_exposure": gross, "net_exposure": net})
    out = pd.DataFrame(rows)
    summary = {
        "n_raw_events": int(len(trades)),
        "n_executed_trades": int(len(trades)),
        "simultaneous_position_hours": int((out["n_active"] > 1).sum()),
        "same_direction_overlap_hours": int((out["same_dir_overlap_pairs"] > 0).sum()),
        "opposite_direction_overlap_hours": int((out["opp_dir_overlap_pairs"] > 0).sum()),
        "signal_conflicts": int((out["opp_dir_overlap_pairs"] > 0).sum()),
        "max_concurrent_positions": int(out["n_active"].max()),
        "max_gross_exposure": float(out["gross_exposure"].max()),
        "max_net_exposure": float(out["net_exposure"].max()),
        "max_abs_net_exposure": float(out["net_exposure"].abs().max()),
    }
    out.attrs["summary"] = summary
    return out


def run_policy(trades: pd.DataFrame, policy: str,
               cooldown_h: int = 6) -> pd.DataFrame:
    """
    Execute a policy on the chronological trade list. Returns the executed
    trades (subset/merged). Policy selection happens on development data only.

    The result always carries:
      - book_ts: timestamp at which the position's PnL is realized in equity
        (entry_ts for standalone trades; exit_ts for P2-merged positions so no
        later PnL is booked before it is actually realized).
      - n_raw_merged: number of raw signals folded into the row.
    """
    t = trades.sort_values("entry_ts").reset_index(drop=True)
    if policy == "P0":
        out = t.copy()
        out["book_ts"] = out["entry_ts"]
        out["n_raw_merged"] = 1
        return out
    if policy == "P1":
        keep = []
        last_exit = pd.Timestamp.min.tz_localize("UTC")
        for _, row in t.iterrows():
            if row["entry_ts"] >= last_exit:
                row = row.copy()
                row["book_ts"] = row["entry_ts"]
                row["n_raw_merged"] = 1
                keep.append(row)
                last_exit = row["exit_ts"]
        res = pd.DataFrame(keep) if keep else pd.DataFrame()
        return res
    if policy == "P3":
        keep = []
        last_entry = pd.Timestamp.min.tz_localize("UTC")
        for _, row in t.iterrows():
            if row["entry_ts"] >= last_entry + pd.Timedelta(hours=cooldown_h):
                row = row.copy()
                row["book_ts"] = row["entry_ts"]
                row["n_raw_merged"] = 1
                keep.append(row)
                last_entry = row["entry_ts"]
        res = pd.DataFrame(keep) if keep else pd.DataFrame()
        return res
    if policy == "P2":
        # merge/refresh same direction; opposite closes current and reverses.
        # PnL of a merged position is booked at its final exit (no look-ahead).
        out = []
        cur = None
        for _, row in t.iterrows():
            if cur is None:
                cur = row.copy()
                cur["merged_n"] = 1
                continue
            if np.sign(cur["dir"]) == np.sign(row["dir"]):
                cur = cur.copy()
                cur["exit_ts"] = max(cur["exit_ts"], row["exit_ts"])
                cur["pnl_bps"] = cur["pnl_bps"] + row["pnl_bps"]
                cur["gross_pnl_bps"] = cur["gross_pnl_bps"] + row["gross_pnl_bps"]
                cur["cost_pnl_bps"] = cur["cost_pnl_bps"] + row["cost_pnl_bps"]
                cur["merged_n"] = cur.get("merged_n", 1) + 1
                cur["merged_events"] = cur.get("merged_events", [cur["event_id"]])
                cur["merged_events"] = cur["merged_events"] + [row["event_id"]]
            else:
                out.append(cur)
                cur = row.copy()
                cur["merged_n"] = 1
        if cur is not None:
            out.append(cur)
        res = pd.DataFrame(out) if out else pd.DataFrame()
        if len(res):
            res["book_ts"] = res["exit_ts"]
            res["n_raw_merged"] = res.get("merged_n", 1)
            res["merged_events"] = res.get("merged_events", res["event_id"])
        return res
    raise ValueError(f"unknown policy {policy}")


def policy_comparison(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Compare P0-P3 on development data (inner_sel + inner_val only).

    Because P2 folds multiple raw signals into one position row, per-row mean
    PnL is NOT comparable across policies. The selection criterion is therefore
    per-RAW-EVENT expectancy (total PnL / number of qualifying raw signals) and
    total return; per-row stats are reported but labelled as per-position.
    """
    dev = trades[trades["split"].isin(["inner_sel", "inner_val"])]
    n_raw = int(len(dev))
    rows = []
    for pol in ["P0", "P1", "P2", "P3"]:
        exec_t = run_policy(dev, pol)
        n = len(exec_t)
        if n == 0:
            rows.append({"policy": pol, "n_trades": 0})
            continue
        pnl = exec_t["pnl_bps"].to_numpy(dtype=float)
        ts = pd.to_datetime(exec_t["book_ts"]).to_numpy()
        span_y = max((pd.to_datetime(ts).max() - pd.to_datetime(ts).min()).total_seconds()
                     / (365.25 * 86400), 1 / 365.25)
        tpy = n / span_y
        eq = chronological_equity(pnl, ts)
        mu = metric_units(eq, tpy)
        total = float(pnl.sum())
        rows.append({
            "policy": pol,
            "n_raw_events": n_raw,
            "n_positions": n,
            "total_return_bps": total,
            "expectancy_per_raw_event_bps": total / n_raw if n_raw else np.nan,
            "expectancy_per_position_bps": float(pnl.mean()),
            "win_rate_per_position": float((pnl > 0).mean()),
            "profit_factor": float(pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()))
            if (pnl < 0).any() and pnl[pnl < 0].sum() != 0 else np.nan,
            "cumulative_return_bps": mu["cumulative_return_bps"],
            "max_drawdown_ratio": mu["max_drawdown_ratio"],
            "calmar": mu["calmar"],
            "sharpe_annualized": float(pnl.mean() / pnl.std(ddof=1)) * np.sqrt(tpy)
            if len(pnl) > 1 and pnl.std(ddof=1) > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def chronological_equity(pnl_bps, ts):
    from .phase_7_5_audit import chronological_equity as _ce
    return _ce(pnl_bps, ts)
