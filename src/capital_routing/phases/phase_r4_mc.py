"""
CR-RISK-BLOCK1 R4 — Monte Carlo frontiers + ruin probability map (R4.5, R4.6).

Dependency-aware simulation over resampled trade sequences:

- iid      individual-trade resampling (comparison baseline only)
- block    chronological stationary block bootstrap (block = 25 trades)
- episode  R1 12h-cluster block bootstrap (episode members stay together)

For every ladder fraction and scheme, n_paths simulated equity paths produce
percentile distributions of CAGR, max DD, terminal equity, minimum equity and
longest DD duration, plus explicit ruin probabilities for every definition in
R4.6 (technical ruin, capital impairment 50%, severe 40%, major 30%, and
prop-style 10/15/20% drawdown). Deterministic (fixed seed per scheme).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .phase_r2_context import assign_cluster_ranks
from .phase_r4_common import (EPISODE_INTERVAL_H, LADDER_PCT, MC_PATHS,
                              PERCENTILES, RUIN_DD_PCTS, sample_sequences,
                              span_years)

SCHEMES = ["iid", "block", "episode"]


def _longest_run_vec(mask: np.ndarray) -> np.ndarray:
    """Longest run of True per row, vectorized."""
    m = mask.astype(np.int8)
    padded = np.pad(m, ((0, 0), (1, 1)))
    d = np.diff(padded, axis=1)
    starts = np.where(d == 1)
    ends = np.where(d == -1)
    if len(starts[0]) == 0:
        return np.zeros(mask.shape[0], dtype=int)
    lengths = ends[1] - starts[1]
    out = np.zeros(mask.shape[0], dtype=int)
    np.maximum.at(out, starts[0], lengths)
    return out


def _simulate_stats(eq: np.ndarray, years: float) -> Dict[str, np.ndarray]:
    """Per-path stats from a (n_paths, n) equity matrix."""
    terminal = eq[:, -1]
    cagr = terminal ** (1.0 / years) - 1.0
    peak = np.maximum.accumulate(eq, axis=1)
    dd = (peak - eq) / peak
    max_dd = dd.max(axis=1)
    min_eq = eq.min(axis=1)
    dur = _longest_run_vec(dd > 1e-12)
    return {"terminal": terminal, "cagr": cagr, "max_dd": max_dd,
            "min_eq": min_eq, "dur": dur, "dd": dd}


def _pct_cols(stats: Dict[str, np.ndarray], key: str) -> Dict[str, float]:
    return {f"{key}_p{p}": float(np.percentile(stats[key], p))
            for p in PERCENTILES}


def monte_carlo_frontier(ledger: pd.DataFrame,
                         n_paths: int = MC_PATHS,
                         seed: int = 20260815) -> pd.DataFrame:
    """Percentile frontiers + ruin probabilities, one row per f x scheme."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    years = span_years(tb["entry_ts"], tb["exit_ts"])
    n = len(r_R)

    ranks = assign_cluster_ranks(ledger, EPISODE_INTERVAL_H)
    tb_idx = {eid: i for i, eid in enumerate(tb["event_id"])}
    blocks: List[np.ndarray] = []
    for _, g in ranks.groupby("cluster_id"):
        idx = np.array([tb_idx[e] for e in g["event_id"] if e in tb_idx])
        if len(idx):
            blocks.append(idx)

    rows = []
    for scheme in SCHEMES:
        seqs = sample_sequences(r_R, scheme, n_paths, n, seed,
                                blocks=blocks if scheme == "episode" else None)
        for f_pct in LADDER_PCT:
            f = f_pct / 100.0
            eq = np.cumprod(1.0 + f * seqs, axis=1)
            stats = _simulate_stats(eq, years)
            row = {"scheme": scheme, "f_pct": f_pct, "n_paths": n_paths}
            for key in ["cagr", "max_dd", "terminal", "min_eq"]:
                row.update(_pct_cols(stats, key))
            row.update({f"dur_trades_p{p}": float(np.percentile(stats["dur"], p))
                        for p in PERCENTILES})
            row["exp_cagr"] = float(np.mean(stats["cagr"]))
            row["exp_max_dd"] = float(np.mean(stats["max_dd"]))
            row["median_terminal"] = float(np.median(stats["terminal"]))
            # ruin probabilities (explicit definitions)
            dd = stats["dd"]
            for thr in RUIN_DD_PCTS:
                row[f"P_dd_ge_{int(thr)}"] = float((dd >= thr / 100.0).mean())
            row["P_technical_ruin"] = float((eq[:, -1] <= 0.0).mean())
            row["P_capital_impairment_50"] = row["P_dd_ge_50"]
            rows.append(row)
    return pd.DataFrame(rows)
