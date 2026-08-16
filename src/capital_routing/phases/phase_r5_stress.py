"""
CR-RISK-BLOCK2 R5 — Family-specific stress (XII, XIII).

XII  R5_FAMILY_EDGE_DEGRADATION: edge retention applied PER FAMILY (method A:
     positive returns scaled, losses preserved - same semantics as R4) across
     explicit (edge_A, edge_B) scenarios x allocation ratios x total f.
     Joint block bootstrap (5,000 paths, deterministic) preserves A/B
     co-occurrence inside blocks.

XIII R5_FAMILY_TAIL_STRESS: deterministic weighted sequential shocks - amplify
     the worst 5% of ONE family's losses (other untouched), insert worst
     trades, inject p99-loss clusters - at allocation subset x f=1%.

No winners are ever invented; losses are preserved in edge shrink. No
allocation is selected here.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r4_mc import _simulate_stats
from .phase_r5_common import (ALLOC_SUBSET, EDGE_SCENARIOS, MC_PATHS_STRESS,
                              MC_SEED, joint_indices, joint_sequences,
                              span_years)
from .phase_r5_portfolio import _joint_book

F_GRID_STRESS = [0.50, 1.00, 2.00]


def _edge_shrink_family(r_R: np.ndarray, fam: np.ndarray, edge_A: float,
                        edge_B: float) -> np.ndarray:
    out = r_R.copy()
    pos = out > 0
    out[(fam == "A") & pos] *= edge_A
    out[(fam == "B") & pos] *= edge_B
    return out


# ---------------------------------------------------------------------------
# XII. Edge degradation by family
# ---------------------------------------------------------------------------

def family_edge_degradation(ledger: pd.DataFrame,
                            n_paths: int = MC_PATHS_STRESS,
                            seed: int = MC_SEED) -> pd.DataFrame:
    r_R, fam = _joint_book(ledger)
    years = span_years(ledger["entry_ts"], ledger["exit_ts"])
    n = len(r_R)
    idx = joint_indices(r_R, "block", n_paths, n, seed)
    rows = []
    for edge_A, edge_B in EDGE_SCENARIOS:
        r_e = _edge_shrink_family(r_R, fam, edge_A, edge_B)
        r_mat = r_e[idx]
        for a_share, b_share in ALLOC_SUBSET:
            wA, wB = a_share / 100.0, b_share / 100.0
            w_mat = np.where(fam[idx] == "A", wA, wB).astype(float)
            for f in F_GRID_STRESS:
                eq = np.cumprod(1.0 + (f / 100.0) * w_mat * r_mat, axis=1)
                stats = _simulate_stats(eq, years)
                dd = stats["dd"]
                rows.append({
                    "edge_A": edge_A, "edge_B": edge_B,
                    "w_A_pct": a_share, "w_B_pct": b_share,
                    "f_total_pct": f, "n_paths": n_paths,
                    "exp_cagr": float(np.mean(stats["cagr"])),
                    "median_cagr": float(np.median(stats["cagr"])),
                    "max_dd_p50": float(np.median(stats["max_dd"])),
                    "max_dd_p95": float(np.percentile(stats["max_dd"], 95)),
                    "P_dd_ge_10": float((dd >= 0.10).mean()),
                    "P_dd_ge_20": float((dd >= 0.20).mean()),
                    "P_dd_ge_30": float((dd >= 0.30).mean()),
                    "P_dd_ge_40": float((dd >= 0.40).mean()),
                    "P_dd_ge_50": float((dd >= 0.50).mean()),
                    "P_technical_ruin": float((eq[:, -1] <= 0.0).mean()),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# XIII. Family-specific tail stress (deterministic weighted sequential path)
# ---------------------------------------------------------------------------

def _worst5_mask(r: np.ndarray) -> np.ndarray:
    losses = r[r < 0]
    if len(losses) == 0:
        return np.zeros_like(r, dtype=bool)
    thr = np.quantile(losses, 0.05)
    return r <= thr


def _weighted_path_stats(r_seq: np.ndarray, w_seq: np.ndarray,
                         f: float) -> Tuple[float, float]:
    assert len(r_seq) == len(w_seq), f"len mismatch {len(r_seq)} vs {len(w_seq)}"
    eq = np.concatenate([[1.0], np.cumprod(1.0 + f * w_seq * r_seq)])
    peak = np.maximum.accumulate(eq)
    max_dd = float(((peak - eq) / peak).max())
    return max_dd, float(eq[-1])


def family_tail_stress(ledger: pd.DataFrame) -> pd.DataFrame:
    """Deterministic weighted sequential shocks. Each variant is a (seq,
    ins_pos, ins_tag) triple: inserted trades (at ins_pos) carry the inserted
    family's weight; amplification variants have no insertion."""
    r_R, fam = _joint_book(ledger)
    m5A = _worst5_mask(r_R[fam == "A"])
    m5B = _worst5_mask(r_R[fam == "B"])
    variants: Dict[str, Tuple[np.ndarray, Optional[int], Optional[str]]] = {
        "historical": (r_R, None, None)}
    for mult in [1.50, 2.00]:
        vA, vB = r_R.copy(), r_R.copy()
        vA[fam == "A"] = np.where(m5A, r_R[fam == "A"] * mult, r_R[fam == "A"])
        vB[fam == "B"] = np.where(m5B, r_R[fam == "B"] * mult, r_R[fam == "B"])
        both = vA.copy()
        both[fam == "B"] = vB[fam == "B"]
        for tag, v in [("A", vA), ("B", vB), ("both", both)]:
            variants[f"{tag}_worst5_x{mult:.2f}".replace(".", "_")] = (v, None, None)
    # worst-trade insertion per family (inserted trade keeps its family's weight)
    iA = int(np.argmin(np.where(fam == "A", r_R, np.inf)))
    iB = int(np.argmin(np.where(fam == "B", r_R, np.inf)))
    for tag, pos in [("A", iA), ("B", iB)]:
        variants[f"{tag}_insert_worst_1"] = (np.insert(r_R, pos, r_R[pos]), pos, tag)
    # p99-loss cluster per family (5 consecutive at family p99 loss)
    for tag in ["A", "B"]:
        fam_losses = r_R[(fam == tag) & (r_R < 0)]
        p99 = float(np.quantile(fam_losses, 0.01))
        pos = iA if tag == "A" else iB
        variants[f"{tag}_p99_loss_cluster"] = (np.insert(r_R, pos, np.full(5, p99)),
                                                pos, tag)

    rows = []
    for a_share, b_share in ALLOC_SUBSET:
        wA, wB = a_share / 100.0, b_share / 100.0
        w_seq = np.where(fam == "A", wA, wB).astype(float)
        for name, (seq, ins_pos, ins_tag) in variants.items():
            if ins_pos is None:
                w_s = w_seq
            else:
                ins_w = wA if ins_tag == "A" else wB
                n_add = len(seq) - len(r_R)
                w_s = np.insert(w_seq, ins_pos, np.full(n_add, ins_w))
            for f in [0.50, 1.00, 2.00]:
                max_dd, term = _weighted_path_stats(seq, w_s, f / 100.0)
                rows.append({"variant": name, "w_A_pct": a_share, "w_B_pct": b_share,
                             "f_total_pct": f, "max_dd": max_dd,
                             "terminal_equity": term})
    return pd.DataFrame(rows)
