"""
CR-RISK-BLOCK1 R4 — Static risk ladder (R4.2-R4.4, R4.11).

Runs the fixed-fractional ladder (18 research fractions) over:

- A+B pooled portfolio (overlap-exact hourly compounding; the historical path)
- A-only and B-only hourly books (family frontiers, R4.11)
- sequential per-trade compounding (the brief's E*(1+f*r_R) reference)

Every row carries the full account-level metric set (CAGR, max DD, Calmar,
Sortino, ulcer, worst day/24h/48h, recovery factor, ...) plus the overlap
context (max gross R exposure, effective risk during 2/3-position overlap).

All compounding multiplicative; no additive approximation; no alpha change.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_r4_common import (LADDER_PCT, RISK_UNIT_BPS, equity_metrics,
                              hourly_equity, hourly_grid, sequential_equity,
                              span_years)


def _worst_trade_pct(r_R: np.ndarray, f: float) -> float:
    return float(np.min(r_R) * f)


def _worst_seq_pct(r_R: np.ndarray, f: float) -> float:
    """Max peak-to-trough drawdown of the sequential per-trade path."""
    eq = sequential_equity(r_R, f)
    peak = np.maximum.accumulate(eq)
    return float(((peak - eq) / peak).max())


def _worst_cluster_pct(ledger: pd.DataFrame, f: float) -> float:
    """Worst R1 12h-cluster account impact (sum of cluster R x f, compounded)."""
    from .phase_r2_context import assign_cluster_ranks
    ranks = assign_cluster_ranks(ledger, 12.0)
    r_R = (ledger["pnl_bps"] / ledger["risk_unit_bps"]).to_numpy()
    per = pd.DataFrame({"cluster": ranks["cluster_id"].to_numpy(), "r": r_R})
    worst = 0.0
    for _, g in per.groupby("cluster"):
        eq = sequential_equity(g["r"].to_numpy(dtype=float), f)
        worst = min(worst, float(np.min(eq) - 1.0))
    return worst


def run_ladder(ledger: pd.DataFrame, paths: pd.DataFrame,
               families: Optional[List[str]] = None) -> pd.DataFrame:
    """Ladder over the hourly portfolio book (pooled or single-family)."""
    tb = ledger.copy()
    if families is not None:
        tb = tb[tb["family"].isin(families)].reset_index(drop=True)
        paths_f = paths[paths["event_id"].isin(set(tb["event_id"]))]
    else:
        paths_f = paths
    grid = hourly_grid(tb, paths_f)
    r_h = grid["r_h"].to_numpy(dtype=float)
    years = span_years(tb["entry_ts"], tb["exit_ts"])
    rows = []
    for f_pct in LADDER_PCT:
        f = f_pct / 100.0
        eq = hourly_equity(r_h, f)
        m = equity_metrics(eq, years, hourly=True)
        r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
        rows.append({
            "f_pct": f_pct,
            "book": "A+B" if families is None else "+".join(families),
            **{k: v for k, v in m.items()},
            "worst_trade_pct": _worst_trade_pct(r_R, f),
            "worst_seq_pct": _worst_seq_pct(r_R, f),
            "worst_cluster_pct": _worst_cluster_pct(tb, f),
            "max_concurrent_positions": _max_concurrent(tb),
            "effective_risk_2pos_pct": 2.0 * f_pct,
            "effective_risk_3pos_pct": 3.0 * f_pct,
            "max_gross_R_exposure": _max_gross_R(paths_f, tb),
        })
    return pd.DataFrame(rows)


def run_sequential_ladder(ledger: pd.DataFrame) -> pd.DataFrame:
    """Per-trade chronological compounding reference (brief's formula)."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    years = span_years(tb["entry_ts"], tb["exit_ts"])
    rows = []
    for f_pct in LADDER_PCT:
        f = f_pct / 100.0
        eq = sequential_equity(r_R, f)
        m = equity_metrics(eq, years, hourly=False)
        rows.append({"f_pct": f_pct, "book": "A+B_sequential",
                     **{k: v for k, v in m.items()},
                     "worst_trade_pct": _worst_trade_pct(r_R, f),
                     "worst_seq_pct": _worst_seq_pct(r_R, f),
                     "worst_cluster_pct": _worst_cluster_pct(tb, f),
                     "max_concurrent_positions": _max_concurrent(tb),
                     "effective_risk_2pos_pct": 2.0 * f_pct,
                     "effective_risk_3pos_pct": 3.0 * f_pct,
                     "max_gross_R_exposure": _max_gross_R_for_book(tb)})
    return pd.DataFrame(rows)


def _max_concurrent(tb: pd.DataFrame) -> int:
    """Max simultaneous open positions across the book (chronological sweep)."""
    ts = pd.to_datetime(tb["entry_ts"], utc=True)
    ex = pd.to_datetime(tb["exit_ts"], utc=True)
    events = []
    for t0, t1 in zip(ts, ex):
        events.append((t0, 1))
        events.append((t1, -1))
    events.sort(key=lambda x: x[0])
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def _max_gross_R(paths: pd.DataFrame, tb: pd.DataFrame) -> float:
    """Max number of simultaneously open positions (gross R commitment, since
    each position = 1R at entry)."""
    p = paths[["event_id", "mark_time", "h_since_entry"]].copy()
    p["mark_time"] = pd.to_datetime(p["mark_time"], utc=True)
    hourly_count = p.groupby("mark_time")["event_id"].nunique()
    return float(hourly_count.max())


def _max_gross_R_for_book(tb: pd.DataFrame) -> float:
    ts = pd.to_datetime(tb["entry_ts"], utc=True)
    ex = pd.to_datetime(tb["exit_ts"], utc=True)
    events = []
    for t0, t1 in zip(ts, ex):
        events.append((t0, 1))
        events.append((t1, -1))
    events.sort(key=lambda x: x[0])
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return float(best)


def family_frontier(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """R4.11 — same ladder for A-only and B-only; identifies the capital-
    limiting family at each f (higher max DD / worse DD profile)."""
    a = run_ladder(ledger, paths, families=["A"])
    b = run_ladder(ledger, paths, families=["B"])
    ab = run_ladder(ledger, paths)
    merged = ab[["f_pct", "cagr", "max_dd"]].merge(
        a[["f_pct", "cagr", "max_dd"]], on="f_pct", suffixes=("_AB", ""))
    merged = merged.merge(
        b[["f_pct", "cagr", "max_dd"]], on="f_pct", suffixes=("_A", "_B"))
    merged = merged.rename(columns={
        "cagr_AB": "cagr_pooled", "max_dd_AB": "max_dd_pooled",
        "cagr": "cagr_A", "max_dd": "max_dd_A",
        "cagr_B": "cagr_B", "max_dd_B": "max_dd_B"})
    merged["capital_limiting"] = np.where(
        merged["max_dd_A"] >= merged["max_dd_B"], "A", "B")
    return merged
