"""
CR-RISK-BLOCK1 R4 — Stress studies (R4.7 edge degradation, R4.8 tail stress,
R4.9 loss-streak stress).

R4.7 Edge degradation (method A, documented): positive excess returns are
scaled by the edge state; losses are preserved exactly.
    r'_R = min(r_R, 0) + edge * max(r_R, 0)
Re-simulated with dependency-aware block bootstrap at reduced path count.

R4.8 Tail shock stress (deterministic, on the historical trade sequence):
    - worst 5% losses amplified 1.25x / 1.5x / 2.0x
    - one historical worst trade inserted (duplicated at its position)
    - the two worst trades inserted consecutively
    - a p99-loss cluster (5 consecutive trades at the historical p99 loss)
Winners are never altered.

R4.9 Loss-streak stress: explicit consecutive losing streaks of length
5/8/10/11/13/15 at the loser median / p75 / p90 return, compounded
multiplicatively at each fraction -> account drawdown.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .phase_r4_common import (EDGE_STATES, LADDER_PCT, MC_PATHS_STRESS,
                              RUIN_DD_PCTS, sample_sequences, sequential_equity,
                              span_years)
from .phase_r4_mc import _simulate_stats

STREAK_LENGTHS = [5, 8, 10, 11, 13, 15]
LOSER_QUANTILES = [0.50, 0.75, 0.90]


def _edge_shrink(r_R: np.ndarray, edge: float) -> np.ndarray:
    """Method A: scale positive returns only; losses untouched."""
    return np.minimum(r_R, 0.0) + edge * np.maximum(r_R, 0.0)


def edge_degradation(ledger: pd.DataFrame, n_paths: int = MC_PATHS_STRESS,
                     seed: int = 20260815) -> pd.DataFrame:
    """Per f x edge state: expected/median CAGR, p95 max DD, P(DD>=20..50%),
    technical ruin. Block bootstrap (chronological blocks) at reduced paths."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    years = span_years(tb["entry_ts"], tb["exit_ts"])
    n = len(r_R)
    rows = []
    for edge in EDGE_STATES:
        r_e = _edge_shrink(r_R, edge)
        seqs = sample_sequences(r_e, "block", n_paths, n, seed + int(edge * 100))
        for f_pct in LADDER_PCT:
            f = f_pct / 100.0
            eq = np.cumprod(1.0 + f * seqs, axis=1)
            stats = _simulate_stats(eq, years)
            dd = stats["dd"]
            row = {"edge_pct": int(edge * 100), "f_pct": f_pct,
                   "exp_cagr": float(np.mean(stats["cagr"])),
                   "median_cagr": float(np.median(stats["cagr"])),
                   "p95_max_dd": float(np.percentile(stats["max_dd"], 95))}
            for thr in [10.0, 20.0, 30.0, 40.0, 50.0]:
                row[f"P_dd_ge_{int(thr)}"] = float((dd >= thr / 100.0).mean())
            row["P_technical_ruin"] = float((eq[:, -1] <= 0.0).mean())
            rows.append(row)
    return pd.DataFrame(rows)


def _worst5_mask(r_R: np.ndarray) -> np.ndarray:
    losses = r_R[r_R < 0]
    if len(losses) == 0:
        return np.zeros_like(r_R, dtype=bool)
    thr = np.quantile(losses, 0.05)  # 5th percentile of losses = deep loss
    return r_R <= thr


def tail_stress(ledger: pd.DataFrame) -> pd.DataFrame:
    """Deterministic historical-sequence shocks; winners untouched."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    years = span_years(tb["entry_ts"], tb["exit_ts"])
    variants: Dict[str, np.ndarray] = {"historical": r_R}
    mask5 = _worst5_mask(r_R)
    n5 = max(1, int(mask5.sum()))
    for mult in [1.25, 1.5, 2.0]:
        v = r_R.copy()
        v[mask5] = r_R[mask5] * mult
        variants[f"worst5_x{mult:.2f}".replace(".", "_")] = v
    # insert worst trades (duplicated at their historical position)
    worst_idx = int(np.argmin(r_R))
    order = np.argsort(r_R)
    two_worst = order[:2]
    v = np.insert(r_R, worst_idx, r_R[worst_idx])
    variants["insert_worst_1"] = v
    v2 = np.insert(r_R, worst_idx, np.sort(r_R[order[:2]])[::-1])
    variants["insert_worst_2_consec"] = v2
    # p99 loss cluster: 5 consecutive trades at the historical p99 loss
    p99 = np.quantile(r_R[r_R < 0], 0.01)
    v3 = np.insert(r_R, worst_idx, np.full(5, p99))
    variants["insert_p99_loss_cluster"] = v3

    rows = []
    for name, seq in variants.items():
        for f_pct in LADDER_PCT:
            f = f_pct / 100.0
            eq = sequential_equity(seq, f)
            peak = np.maximum.accumulate(eq)
            max_dd = float(((peak - eq) / peak).max())
            rows.append({
                "variant": name, "f_pct": f_pct,
                "terminal_equity": float(eq[-1]),
                "max_dd": max_dd,
            })
    return pd.DataFrame(rows)


def loss_streak_stress(ledger: pd.DataFrame) -> pd.DataFrame:
    """Explicit streak survival table at each f."""
    r_R = (ledger["pnl_bps"] / ledger["risk_unit_bps"]).to_numpy(dtype=float)
    losers = r_R[r_R < 0]
    quants = {q: float(np.quantile(losers, q)) for q in LOSER_QUANTILES}
    rows = []
    for f_pct in LADDER_PCT:
        f = f_pct / 100.0
        for length in STREAK_LENGTHS:
            for q, loss in quants.items():
                eq_after = (1.0 + f * loss) ** length
                rows.append({
                    "f_pct": f_pct, "streak_len": length,
                    "loser_quantile": q, "loser_R": loss,
                    "equity_after_streak": float(eq_after),
                    "drawdown_pct": float(1.0 - eq_after),
                })
    return pd.DataFrame(rows)
