"""
CR-RISK-BLOCK1 R1.2 — Concurrency Map.

From the exact chronological trade book (P0: every qualifying event), identify:
  - number of open trades at every (hourly) timestamp
  - max / mean / median concurrency
  - hours with 2 / 3 positions
  - same-direction overlaps, opposite-direction overlaps
  - A+A, B+B, A+B overlap
  - gross and net directional exposure through time

Positions are hour-aligned (entries/exits on hour boundaries by construction),
so an hourly timeline is exact — no state change is missed.

Note: opposite positions do NOT cancel economically; gross and net exposure are
tracked separately (gross = sum of |pos|, net = sum of dir*pos).
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def _pair_count(n: int) -> int:
    return max(n * (n - 1) // 2, 0)


def build_concurrency(ledger: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Hourly open-position book + summary statistics."""
    entry = pd.to_datetime(ledger["entry_ts"], utc=True)
    exit_ = pd.to_datetime(ledger["exit_ts"], utc=True)
    ts_min = entry.min().floor("h")
    ts_max = exit_.max().ceil("h")
    idx = pd.date_range(ts_min, ts_max, freq="h")

    rows = []
    for t in idx:
        active = ledger[(entry <= t) & (exit_ > t)]
        nl = int((active["dir"] > 0).sum())
        ns = int((active["dir"] < 0).sum())
        nA = int((active["family"] == "A").sum())
        nB = int((active["family"] == "B").sum())
        n = len(active)
        if n == 0:
            rows.append({"ts": t, "n_active": 0, "n_long": 0, "n_short": 0,
                         "n_A": 0, "n_B": 0,
                         "same_dir_overlap_pairs": 0, "opp_dir_overlap_pairs": 0,
                         "A_A_overlap_pairs": 0, "B_B_overlap_pairs": 0,
                         "A_B_overlap_pairs": 0, "gross_exposure": 0.0,
                         "net_exposure": 0.0, "abs_net_exposure": 0.0})
            continue
        rows.append({
            "ts": t, "n_active": n, "n_long": nl, "n_short": ns,
            "n_A": nA, "n_B": nB,
            "same_dir_overlap_pairs": _pair_count(nl) + _pair_count(ns),
            "opp_dir_overlap_pairs": nl * ns,
            "A_A_overlap_pairs": _pair_count(nA), "B_B_overlap_pairs": _pair_count(nB),
            "A_B_overlap_pairs": nA * nB,
            "gross_exposure": float(active["pos"].sum()),
            "net_exposure": float((active["dir"] * active["pos"]).sum()),
            "abs_net_exposure": float(abs((active["dir"] * active["pos"]).sum())),
        })
    tl = pd.DataFrame(rows)
    if len(tl) == 0:
        return tl, pd.DataFrame()

    n_active = tl["n_active"].to_numpy(dtype=float)
    in_market = tl[tl["n_active"] > 0]
    summary = pd.DataFrame([{
        "n_raw_events": int(len(ledger)),
        "n_executed_trades": int(len(ledger)),
        "timeline_hours": int(len(tl)),
        "in_market_hours": int(len(in_market)),
        "max_concurrent_positions": int(tl["n_active"].max()),
        "mean_concurrency_all_hours": float(n_active.mean()),
        "mean_concurrency_in_market": float(in_market["n_active"].mean()) if len(in_market) else np.nan,
        "median_concurrency_in_market": float(in_market["n_active"].median()) if len(in_market) else np.nan,
        "p90_concurrency_in_market": float(in_market["n_active"].quantile(0.90)) if len(in_market) else np.nan,
        "p99_concurrency_in_market": float(in_market["n_active"].quantile(0.99)) if len(in_market) else np.nan,
        "hours_with_2_positions": int((tl["n_active"] == 2).sum()),
        "hours_with_3_positions": int((tl["n_active"] == 3).sum()),
        "hours_with_4plus_positions": int((tl["n_active"] >= 4).sum()),
        "same_direction_overlap_hours": int((tl["same_dir_overlap_pairs"] > 0).sum()),
        "opposite_direction_overlap_hours": int((tl["opp_dir_overlap_pairs"] > 0).sum()),
        "A_A_overlap_hours": int((tl["A_A_overlap_pairs"] > 0).sum()),
        "B_B_overlap_hours": int((tl["B_B_overlap_pairs"] > 0).sum()),
        "A_B_overlap_hours": int((tl["A_B_overlap_pairs"] > 0).sum()),
        "max_gross_exposure": float(tl["gross_exposure"].max()),
        "max_abs_net_exposure": float(tl["abs_net_exposure"].max()),
        "gross_exposure_p90": float(tl["gross_exposure"].quantile(0.90)),
        "gross_exposure_p99": float(tl["gross_exposure"].quantile(0.99)),
        "note": "gross = sum|pos|; net = sum(dir*pos); opposite positions do NOT cancel economically",
    }])
    return tl, summary
