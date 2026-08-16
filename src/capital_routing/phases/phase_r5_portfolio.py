"""
CR-RISK-BLOCK2 R5 — Portfolio allocation machinery (IX, X, XI, XIV).

- IX  R5_MARGINAL_PORTFOLIO_CONTRIBUTION  A-only / B-only / pooled / 50-50
      contributions at the f=1% reference, historical + block-MC risk
- X   R5_ALLOCATION_FRONTIER             predefined 11-ratio grid x 7 total-f
      values, hourly overlap-exact, merged with block-MC tail stats
- XI  R5_ALLOCATION_MC                   dependency-aware joint resampling
      (block + episode primary, iid reference), 10k paths, deterministic
- XIV R5_NONDOMINATED_FRONTIER           DOMINATED / NON-DOMINATED under
      historical, block-MC, and 75%/50% edge-degraded regimes

The allocation grid and f grid are FIXED before results. No weight is ever
selected as "best". No alpha / entry / exit / management change.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r4_common import PERCENTILES, span_years
from .phase_r4_mc import _simulate_stats
from .phase_r5_common import (ALLOC_GRID, F_GRID, MC_PATHS, MC_SEED,
                              joint_indices, joint_sequences,
                              weighted_cumprod, weighted_metrics)

SCHEMES = ["block", "episode", "iid"]


def _mc_stats(r_mat: np.ndarray, w_mat: np.ndarray, f: float,
              years: float) -> Dict[str, float]:
    eq = weighted_cumprod(r_mat, w_mat, f)
    stats = _simulate_stats(eq, years)
    out: Dict[str, float] = {}
    for key in ["cagr", "max_dd", "terminal", "min_eq"]:
        for p in PERCENTILES:
            out[f"{key}_p{p}"] = float(np.percentile(stats[key], p))
    dd = stats["dd"]
    for thr in [10.0, 15.0, 20.0, 30.0, 40.0, 50.0]:
        out[f"P_dd_ge_{int(thr)}"] = float((dd >= thr / 100.0).mean())
    out["P_technical_ruin"] = float((eq[:, -1] <= 0.0).mean())
    out["exp_cagr"] = float(np.mean(stats["cagr"]))
    out["median_terminal"] = float(np.median(stats["terminal"]))
    return out


def allocation_mc(ledger: pd.DataFrame, years: float,
                  n_paths: int = MC_PATHS, seed: int = MC_SEED) -> pd.DataFrame:
    """Pre-sample joint sequences once per scheme; reuse across alloc x f."""
    r_R, fam = _joint_book(ledger)
    blocks = _episode_blocks(ledger)
    pre: Dict[str, np.ndarray] = {}
    for scheme in SCHEMES:
        pre[scheme] = joint_indices(r_R, scheme, n_paths, len(r_R), seed,
                                    blocks=blocks if scheme == "episode" else None)
    rows = []
    for a_share, b_share in ALLOC_GRID:
        wA, wB = a_share / 100.0, b_share / 100.0
        for f in F_GRID:
            for scheme in SCHEMES:
                idx = pre[scheme]
                r_mat = r_R[idx]
                w_mat = np.where(fam[idx] == "A", wA, wB).astype(float)
                st = _mc_stats(r_mat, w_mat, f / 100.0, years)
                rows.append({"w_A_pct": a_share, "w_B_pct": b_share,
                             "f_total_pct": f, "scheme": scheme,
                             "n_paths": n_paths, **st})
    return pd.DataFrame(rows)


def _joint_book(ledger: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    return r, tb["family"].to_numpy()


def _episode_blocks(ledger: pd.DataFrame) -> List[np.ndarray]:
    from .phase_r2_context import assign_cluster_ranks
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    ranks = assign_cluster_ranks(tb, 12.0)
    idx_of = {eid: i for i, eid in enumerate(tb["event_id"])}
    blocks: List[np.ndarray] = []
    for _, g in ranks.groupby("cluster_id"):
        idx = np.array([idx_of[e] for e in g["event_id"] if e in idx_of])
        if len(idx):
            blocks.append(idx)
    return blocks


# ---------------------------------------------------------------------------
# X. Allocation frontier (historical hourly + merged block-MC tail stats)
# ---------------------------------------------------------------------------

def allocation_frontier(load: Dict, mc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a_share, b_share in ALLOC_GRID:
        wA, wB = a_share / 100.0, b_share / 100.0
        for f in F_GRID:
            m = weighted_metrics(load["fam_grid"], load["years"], wA, wB,
                                 f / 100.0, ledger=load["ledger"],
                                 fam_heat=load["fam_heat"])
            row = {"w_A_pct": a_share, "w_B_pct": b_share,
                   "f_total_pct": f, "total_heat_pct": (wA + wB) * f}
            for k in ["cagr", "total_return", "max_dd", "calmar", "worst_day_pct",
                      "worst_24h_pct", "worst_48h_pct", "sortino", "ulcer_index",
                      "recovery_factor", "worst_cluster_pct",
                      "worst_weighted_cae_pct", "max_gross_R_weighted"]:
                row[k] = float(m[k])
            # merge block-MC tail stats
            mc_b = mc[(mc.scheme == "block") & (mc.w_A_pct == a_share)
                      & (mc.f_total_pct == f)].iloc[0]
            for k in ["max_dd_p95", "max_dd_p99", "P_dd_ge_10", "P_dd_ge_15",
                      "P_dd_ge_20", "P_dd_ge_30", "P_dd_ge_40", "P_dd_ge_50",
                      "P_technical_ruin", "exp_cagr", "median_terminal",
                      "cagr_p5", "cagr_p95", "terminal_p5", "terminal_p95"]:
                row[f"mc_{k}"] = float(mc_b[k])
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# IX. Marginal portfolio contribution at the f=1% reference
# ---------------------------------------------------------------------------

def marginal_contribution(load: Dict, mc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    refs = [
        ("A_only_f1", 1.0, 0.0, 1.0),
        ("B_only_f1", 0.0, 1.0, 1.0),
        ("Pooled_AB_f1_each_trade_sealed", 1.0, 1.0, 1.0),
        ("AB_5050_total_f1_equal_heat", 0.5, 0.5, 1.0),
    ]
    for label, wA, wB, f_pct in refs:
        m = weighted_metrics(load["fam_grid"], load["years"], wA, wB,
                             f_pct / 100.0, ledger=load["ledger"],
                             fam_heat=load["fam_heat"])
        mc_b = mc[(mc.scheme == "block") & (mc.w_A_pct == wA * 100.0)
                  & (mc.w_B_pct == wB * 100.0) & (mc.f_total_pct == f_pct)]
        row = {"config": label, "w_A_pct": wA * 100.0, "w_B_pct": wB * 100.0,
               "f_total_pct": f_pct,
               "cagr": float(m["cagr"]), "total_return": float(m["total_return"]),
               "max_dd": float(m["max_dd"]), "calmar": float(m["calmar"]),
               "worst_day_pct": float(m["worst_day_pct"]),
               "worst_24h_pct": float(m["worst_24h_pct"]),
               "worst_cluster_pct": float(m["worst_cluster_pct"]),
               "worst_weighted_cae_pct": float(m["worst_weighted_cae_pct"]),
               "max_gross_R_weighted": float(m["max_gross_R_weighted"])}
        if len(mc_b):
            b = mc_b.iloc[0]
            row.update({"mc_p95_max_dd": float(b["max_dd_p95"]),
                        "mc_P_dd_ge_10": float(b["P_dd_ge_10"]),
                        "mc_P_dd_ge_15": float(b["P_dd_ge_15"]),
                        "mc_P_dd_ge_20": float(b["P_dd_ge_20"]),
                        "mc_median_cagr": float(b["cagr_p50"])})
        else:
            # pooled config (w=1/1) is not on the allocation grid - run block MC
            # directly (joint sequences keep A/B co-occurrence)
            r_R, fam = _joint_book(load["ledger"])
            idx = joint_indices(r_R, "block", MC_PATHS, len(r_R), MC_SEED)
            r_mat, w_mat = joint_sequences(
                r_R, fam, "block", MC_PATHS, len(r_R), MC_SEED,
                family_weight={"A": wA, "B": wB}, idx=idx)
            st = _mc_stats(r_mat, w_mat, f_pct / 100.0, load["years"])
            row.update({"mc_p95_max_dd": st["max_dd_p95"],
                        "mc_P_dd_ge_10": st["P_dd_ge_10"],
                        "mc_P_dd_ge_15": st["P_dd_ge_15"],
                        "mc_P_dd_ge_20": st["P_dd_ge_20"],
                        "mc_median_cagr": st["cagr_p50"]})
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# XIV. Non-dominated classification
# ---------------------------------------------------------------------------

def nondominated_frontier(frontier: pd.DataFrame, edge_tbl: pd.DataFrame) -> pd.DataFrame:
    """Per-regime DOMINATED/NON-DOMINATED flags over all (alloc, f) points.

    Regimes (return, risk) pairs:
      historical       CAGR        vs historical max DD
      historical_wd    CAGR        vs worst day
      block_mc         exp CAGR    vs block-MC p95 max DD
      edge75           exp CAGR    vs p95 max DD @ (0.75, 0.75) edge
      edge50           exp CAGR    vs p95 max DD @ (0.50, 0.50) edge
    """
    fr = frontier.copy()
    fr["label"] = fr["w_A_pct"].astype(int).astype(str) + "/" + \
        fr["w_B_pct"].astype(int).astype(str) + "@" + fr["f_total_pct"].astype(str)
    rows = []
    regimes = [
        ("historical", "cagr", "max_dd"),
        ("historical_worst_day", "cagr", "worst_day_pct"),
        ("block_mc", "mc_exp_cagr", "mc_max_dd_p95"),
    ]
    for rname, ret_col, risk_col in regimes:
        points = fr[["label", ret_col, risk_col]].dropna()
        rows += _dominance(points, rname, ret_col, risk_col)
    # edge regimes from the stress table
    for edge, rname in [(0.75, "edge75"), (0.50, "edge50")]:
        e = edge_tbl[(edge_tbl.edge_A == edge) & (edge_tbl.edge_B == edge)
                     & (edge_tbl.f_total_pct == 1.0)]
        merged = fr.merge(e[["w_A_pct", "w_B_pct", "exp_cagr", "max_dd_p95"]],
                          on=["w_A_pct", "w_B_pct"], how="inner")
        points = merged[["label", "exp_cagr", "max_dd_p95"]].dropna()
        rows += _dominance(points, rname, "exp_cagr", "max_dd_p95")
    return pd.DataFrame(rows)


def _dominance(points: pd.DataFrame, rname: str, ret_col: str,
               risk_col: str) -> List[Dict]:
    """A point is DOMINATED if another point has >= return and <= risk (one
    strict), evaluated pairwise on the same metric pair."""
    out = []
    pts = points.reset_index(drop=True)
    for i, r in pts.iterrows():
        dominated_by = []
        for j, s in pts.iterrows():
            if i == j:
                continue
            ret_ok = s[ret_col] >= r[ret_col] - 1e-12
            risk_ok = s[risk_col] <= r[risk_col] + 1e-12
            strict = s[ret_col] > r[ret_col] + 1e-12 or \
                s[risk_col] < r[risk_col] - 1e-12
            if ret_ok and risk_ok and strict:
                dominated_by.append(s["label"])
        out.append({"regime": rname, "label": r["label"],
                    "return": float(r[ret_col]), "risk": float(r[risk_col]),
                    "status": "DOMINATED" if dominated_by else "NON_DOMINATED",
                    "dominated_by": ";".join(dominated_by[:3])})
    return out
