"""
Phase 7.5 - confidence / bootstrap robustness (brief section 7).

For A, B, and combined A+B report:
  expectancy bootstrap CI (event-level, clustered by day for overlapping
  event dependence), PF CI, win-rate CI, median trade, worst 5%, best 5%,
  loss-streak distribution, trade-order Monte Carlo max drawdown.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

BOOTSTRAP_SEED = 20260715
BOOTSTRAP_ITERS = 500
CI_ALPHA = 0.10  # two-sided -> 90% CI


def cluster_ids(ts: np.ndarray, window_h: int = 24) -> np.ndarray:
    """Cluster events by time proximity (within window_h) for block bootstrap."""
    ts = np.sort(pd.to_datetime(ts).astype("int64").to_numpy())
    cluster = np.zeros(len(ts), dtype=int)
    cid = 0
    last = ts[0] - 1
    for i, t in enumerate(ts):
        if t - last > window_h * 3600 * 10**9:
            cid += 1
        cluster[i] = cid
        last = t
    return cluster


def _ci(x: np.ndarray) -> tuple:
    lo, hi = np.percentile(x, [100 * CI_ALPHA / 2, 100 * (1 - CI_ALPHA / 2)])
    return float(lo), float(hi)


def block_bootstrap(pnl: np.ndarray, ts: np.ndarray, iters: int = BOOTSTRAP_ITERS,
                    seed: int = BOOTSTRAP_SEED) -> Dict:
    """Block-bootstrap over time clusters (dependence-aware resampling)."""
    pnl = np.asarray(pnl, dtype=float)
    ts = np.asarray(ts)
    clusters = cluster_ids(ts)
    n_clusters = int(clusters.max()) + 1
    rng = np.random.default_rng(seed)
    expect, wins, pfs = [], [], []
    for _ in range(iters):
        pick = rng.integers(0, n_clusters, size=n_clusters)
        s = np.concatenate([pnl[clusters == c] for c in pick])
        if len(s) == 0:
            continue
        expect.append(s.mean())
        wins.append((s > 0).mean())
        pos, neg = s[s > 0], s[s < 0]
        if len(neg) and neg.sum() != 0:
            pfs.append(pos.sum() / abs(neg.sum()))
        else:
            pfs.append(np.inf)
    expect = np.asarray(expect)
    wins = np.asarray(wins)
    pfs = np.asarray(pfs)
    pfs = pfs[np.isfinite(pfs)]
    elo, ehi = _ci(expect)
    wlo, whi = _ci(wins)
    if len(pfs):
        plo, phi = _ci(pfs)
    else:
        plo = phi = np.nan
    return {
        "n": int(len(pnl)),
        "expectancy_bps": float(pnl.mean()),
        "expectancy_ci_low": elo,
        "expectancy_ci_high": ehi,
        "win_rate": float((pnl > 0).mean()),
        "win_rate_ci_low": wlo,
        "win_rate_ci_high": whi,
        "pf": float(pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()))
        if (pnl < 0).any() and pnl[pnl < 0].sum() != 0 else np.nan,
        "pf_ci_low": plo,
        "pf_ci_high": phi,
        "median_trade_bps": float(np.median(pnl)),
        "worst_5pct_bps": float(np.percentile(pnl, 5)),
        "best_5pct_bps": float(np.percentile(pnl, 95)),
        "n_clusters": n_clusters,
        "method": f"block bootstrap over {n_clusters} time clusters, "
                  f"{iters} iters, seed {seed}",
    }


def loss_streaks(pnl: np.ndarray) -> Dict:
    """Distribution of consecutive losing trades."""
    pnl = np.asarray(pnl, dtype=float)
    streaks = []
    cur = 0
    for x in pnl:
        if x < 0:
            cur += 1
        else:
            if cur > 0:
                streaks.append(cur)
            cur = 0
    if cur > 0:
        streaks.append(cur)
    streaks = np.asarray(streaks, dtype=int) if streaks else np.zeros(0, dtype=int)
    return {
        "n_loss_streaks": int(len(streaks)),
        "max_loss_streak": int(streaks.max()) if len(streaks) else 0,
        "median_loss_streak": float(np.median(streaks)) if len(streaks) else 0.0,
        "p90_loss_streak": float(np.percentile(streaks, 90)) if len(streaks) else 0.0,
    }


def monte_carlo_drawdown(pnl: np.ndarray, n_perm: int = 1000,
                         seed: int = BOOTSTRAP_SEED) -> Dict:
    """
    Trade-order Monte Carlo: permute the trade order, build equity, record max
    drawdown ratio each time. Reports the distribution of max DD.
    """
    pnl = np.asarray(pnl, dtype=float)
    rng = np.random.default_rng(seed)
    dds = []
    for _ in range(n_perm):
        perm = rng.permutation(pnl)
        eq = np.cumsum(perm)
        peak = np.maximum.accumulate(eq)
        dd = np.where(peak > 0, (peak - eq) / peak, 0.0)
        dds.append(dd.max() if len(dd) else 0.0)
    dds = np.asarray(dds)
    return {
        "mc_max_dd_median": float(np.median(dds)),
        "mc_max_dd_p90": float(np.percentile(dds, 90)),
        "mc_max_dd_p95": float(np.percentile(dds, 95)),
        "mc_max_dd_worst": float(dds.max()),
        "n_permutations": n_perm,
    }


def bootstrap_robustness(trades: pd.DataFrame) -> pd.DataFrame:
    """Rows for A, B, A+B using the OOS-labelled frame (all splits)."""
    rows = []
    for grp_name, grp in _groups(trades).items():
        pnl = grp["pnl_bps"].to_numpy(dtype=float)
        ts = grp["entry_ts"].to_numpy()
        if len(pnl) < 10:
            rows.append({"group": grp_name, "n": int(len(pnl))})
            continue
        bb = block_bootstrap(pnl, ts)
        ls = loss_streaks(pnl)
        mc = monte_carlo_drawdown(pnl)
        row = {"group": grp_name}
        row.update(bb)
        row.update(ls)
        row.update(mc)
        rows.append(row)
    return pd.DataFrame(rows)


def _groups(trades: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    a = trades[trades["family"] == "A"]
    b = trades[trades["family"] == "B"]
    return {"A": a, "B": b, "A+B": trades}
