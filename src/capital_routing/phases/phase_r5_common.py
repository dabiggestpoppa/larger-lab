"""
CR-RISK-BLOCK2 R5 — Family Quality / Allocation Anatomy (shared primitives).

Rebuilds the sealed A/B book from the SAME frozen inputs as Block I (phase_03
panel, phase_05 events, P7_5_TRADES), cross-checks against the sealed R1
ledger, and provides the allocation machinery:

- weighted hourly paths:  r_h = w_A * f * r_h_A + w_B * f * r_h_B
  (total portfolio f held constant; 50/50 at f=1% = 0.5% per family per R;
  real intra- and inter-family overlap preserved exactly)
- joint dependency-preserving samplers over the MERGED chronological book
  (iid reference / chronological block / R1 12h-episode block) that keep A/B
  co-occurrence inside resampled units
- weighted cluster / CAE helpers

No alpha, entry, exit, trade-management, or 1R changes. Only the allocation
surface is measured. No "best weight" is ever selected here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_6_events import load_frozen_phase3_panel, load_frozen_phase5
from .phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL
from .phase_7_execution import build_execution_grid, orient_trade
from .phase_7_families import FAMILIES
from .phase_r1_heat import build_heat, build_marks
from .phase_r1_ledger import build_ledger
from .phase_r2_common import build_net_paths
from .phase_r2_context import assign_cluster_ranks
from .phase_r4_common import (BLOCK_SIZE, RISK_UNIT_BPS, equity_metrics,
                              hourly_grid, span_years)

# Predefined allocation grid (A_share %, B_share %): fixed BEFORE results.
ALLOC_GRID: List[Tuple[int, int]] = [
    (0, 100), (10, 90), (20, 80), (30, 70), (40, 60), (50, 50),
    (60, 40), (70, 30), (80, 20), (90, 10), (100, 0)]
ALLOC_SUBSET: List[Tuple[int, int]] = [(0, 100), (30, 70), (50, 50),
                                       (70, 30), (100, 0)]
# Total portfolio f grid (fixed before results; 0.25/5.0 included - cheap)
F_GRID: List[float] = [0.25, 0.50, 1.00, 1.50, 2.00, 3.00, 5.00]
F_GRID_CORE: List[float] = [0.50, 1.00, 1.50, 2.00, 3.00]

MC_PATHS = 10_000
MC_PATHS_STRESS = 5_000
MC_SEED = 20260815
EDGE_STATES = [1.0, 0.75, 0.50, 0.25]

# Edge-degradation scenarios (edge_A, edge_B) - XII
EDGE_SCENARIOS: List[Tuple[float, float]] = [
    (1.00, 1.00), (0.75, 1.00), (1.00, 0.75), (0.75, 0.75),
    (0.50, 1.00), (1.00, 0.50), (0.50, 0.75), (0.75, 0.50),
    (0.50, 0.50), (0.25, 0.25), (0.25, 1.00), (1.00, 0.25)]


# ---------------------------------------------------------------------------
# Frozen-input rebuild (identical chain to R4; cross-checked vs sealed ledger)
# ---------------------------------------------------------------------------

def load_r5_inputs(root: Path) -> Dict:
    """Rebuild ledger/marks/paths/heat from frozen inputs and verify against
    the sealed Block-I artifacts."""
    phase3 = root / "artifacts" / "phase_03"
    phase5 = root / "artifacts" / "phase_05"
    p75 = root / "artifacts" / "phase_07_5"
    risk1 = root / "artifacts" / "risk_block1"

    ev = load_frozen_phase5(phase5)["routing_events.parquet"]
    panel = load_frozen_phase3_panel(phase3)
    trades = pd.read_csv(p75 / "P7_5_TRADES.csv")
    trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
    trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
    trades["split"] = trades["split"].replace("untouched", OOS_LABEL)

    grids: Dict[str, pd.DataFrame] = {}
    for fid in ["A", "B"]:
        fam = FAMILIES[fid]
        fam_events = ev[(ev["origin_currency"] == fam["origin"])
                        & (ev["direction"] == fam["direction"])]
        cfg = FROZEN_CONFIGS[fid]
        g = build_execution_grid(fam_events, panel, [cfg["pair"]],
                                 [cfg["delay_h"]], [cfg["hold_h"]])
        grids[fid] = orient_trade(g, fam)

    ledger = build_ledger(trades, grids, panel)
    marks = build_marks(ledger, panel)
    paths = build_net_paths(ledger, marks)
    heat = build_heat(ledger, marks)

    # cross-check against the sealed R1 ledger
    sealed = pd.read_csv(risk1 / "R1_EVENT_RISK_LEDGER.csv")
    assert len(ledger) == len(sealed) == 890, "ledger size mismatch"
    assert int((ledger.family == "A").sum()) == int((sealed.family == "A").sum())
    assert int((ledger.family == "B").sum()) == int((sealed.family == "B").sum())
    assert abs(float(ledger["pnl_bps"].sum()) - float(sealed["pnl_bps"].sum())) < 1e-6

    # per-family hourly grids + heat (for weighted allocation paths)
    fam_grid: Dict[str, pd.DataFrame] = {}
    fam_heat: Dict[str, pd.DataFrame] = {}
    for fid in ["A", "B"]:
        sub = ledger[ledger["family"] == fid].reset_index(drop=True)
        sub_paths = paths[paths["event_id"].isin(set(sub["event_id"]))]
        fam_grid[fid] = hourly_grid(sub, sub_paths)
        fam_heat[fid] = build_heat(sub, marks[marks["event_id"].isin(set(sub["event_id"]))])

    years = span_years(ledger["entry_ts"], ledger["exit_ts"])
    return {"ledger": ledger, "marks": marks, "paths": paths, "heat": heat,
            "fam_grid": fam_grid, "fam_heat": fam_heat, "years": years,
            "sealed_ledger": sealed,
            "risk1_dir": risk1,
            "inputs": {"trades": trades, "ev": ev, "panel": panel}}


# ---------------------------------------------------------------------------
# Weighted allocation paths (hourly, overlap-exact)
# ---------------------------------------------------------------------------

def allocation_hourly_r(fam_grid: Dict[str, pd.DataFrame],
                        w_A: float, w_B: float, f_total: float) -> np.ndarray:
    """Weighted portfolio hourly return vector (start-of-book to end-of-book)."""
    rA = fam_grid["A"]["r_h"].to_numpy(dtype=float)
    rB = fam_grid["B"]["r_h"].to_numpy(dtype=float)
    n = max(len(rA), len(rB))
    if len(rA) != len(rB):
        idx = pd.date_range(fam_grid["A"].index.min(),
                            max(fam_grid["A"].index.max(), fam_grid["B"].index.max()),
                            freq="h")
        rA = fam_grid["A"]["r_h"].reindex(idx, fill_value=0.0).to_numpy()
        rB = fam_grid["B"]["r_h"].reindex(idx, fill_value=0.0).to_numpy()
    return w_A * f_total * rA + w_B * f_total * rB


def weighted_metrics(fam_grid: Dict[str, pd.DataFrame], years: float,
                     w_A: float, w_B: float, f_total: float,
                     ledger: Optional[pd.DataFrame] = None,
                     fam_heat: Optional[Dict[str, pd.DataFrame]] = None) -> Dict:
    """Full account metric set for an allocation at total f (hourly path)."""
    r_h = allocation_hourly_r(fam_grid, w_A, w_B, f_total)
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r_h)])
    m = equity_metrics(eq, years, hourly=True)
    m["f_total_pct"] = f_total
    m["w_A_pct"] = w_A * 100.0
    m["w_B_pct"] = w_B * 100.0
    if ledger is not None:
        m["worst_cluster_pct"] = weighted_cluster_worst(ledger, w_A, w_B, f_total)
    if fam_heat is not None:
        m["worst_weighted_cae_pct"] = weighted_cae(fam_heat, w_A, w_B, f_total)
        m["max_gross_R_weighted"] = weighted_gross_R(ledger, w_A, w_B)
    return m


def weighted_cluster_worst(ledger: pd.DataFrame, w_A: float, w_B: float,
                           f_total: float) -> float:
    """Worst 12h-cluster account impact: within each R1 cluster, compound the
    weighted per-trade returns sequentially; report the deepest dip."""
    ranks = assign_cluster_ranks(ledger, 12.0)
    fam = ledger["family"].to_numpy()
    r_R = (ledger["pnl_bps"] / ledger["risk_unit_bps"]).to_numpy(dtype=float)
    w_map = {"A": w_A, "B": w_B}
    w = np.array([w_map[f_] for f_ in fam], dtype=float) * f_total
    df = pd.DataFrame({"cluster": ranks["cluster_id"].to_numpy(), "r": r_R * w})
    worst = 0.0
    for _, g in df.groupby("cluster"):
        eq = np.concatenate([[1.0], np.cumprod(1.0 + g["r"].to_numpy(dtype=float))])
        worst = min(worst, float(np.min(eq) - 1.0))
    return worst


def weighted_cae(fam_heat: Dict[str, pd.DataFrame], w_A: float, w_B: float,
                 f_total: float) -> float:
    """Worst weighted portfolio adverse excursion (account %): each family's
    hourly CAE (bps) scaled by its weight x f, then worst hour."""
    hA = fam_heat["A"]["portfolio_cae_bps"].copy()
    hB = fam_heat["B"]["portfolio_cae_bps"].copy()
    idx = hA.index.union(hB.index)
    hA = hA.reindex(idx, fill_value=0.0)
    hB = hB.reindex(idx, fill_value=0.0)
    w_cae = (w_A * f_total * hA + w_B * f_total * hB) / RISK_UNIT_BPS
    return float(-w_cae.max())  # negative = adverse


def weighted_gross_R(ledger: pd.DataFrame, w_A: float, w_B: float) -> float:
    """Max weighted gross R commitment (each open position commits 1R x w)."""
    fam = ledger["family"].to_numpy()
    w = np.where(fam == "A", w_A, w_B)
    ts = pd.to_datetime(ledger["entry_ts"], utc=True)
    ex = pd.to_datetime(ledger["exit_ts"], utc=True)
    events = []
    for t0, t1, wi in zip(ts, ex, w):
        events.append((t0, wi))
        events.append((t1, -wi))
    events.sort(key=lambda x: x[0])
    cur = best = 0.0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


# ---------------------------------------------------------------------------
# Joint dependency-preserving samplers (merged A+B book)
# ---------------------------------------------------------------------------

def joint_book(ledger: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Chronological merged book: (r_R array, family-weight-of-1 array)."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    r = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    fam = tb["family"].to_numpy()
    return r, fam


def episode_blocks(ledger: pd.DataFrame) -> List[np.ndarray]:
    """R1 12h-cluster index blocks over the merged chronological book."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    ranks = assign_cluster_ranks(tb, 12.0)
    idx_of = {eid: i for i, eid in enumerate(tb["event_id"])}
    blocks: List[np.ndarray] = []
    for _, g in ranks.groupby("cluster_id"):
        idx = np.array([idx_of[e] for e in g["event_id"] if e in idx_of])
        if len(idx):
            blocks.append(idx)
    return blocks


def joint_indices(r_R: np.ndarray, scheme: str, n_paths: int, n: int,
                  seed: int,
                  blocks: Optional[List[np.ndarray]] = None) -> np.ndarray:
    """Sample the (n_paths, n) index matrix for a scheme (deterministic)."""
    rng = np.random.default_rng(seed)
    if scheme == "iid":
        return rng.integers(0, len(r_R), size=(n_paths, n))
    if scheme == "block":
        n_blocks = int(np.ceil(n / BLOCK_SIZE))
        starts = rng.integers(0, len(r_R), size=(n_paths, n_blocks))
        idx = np.empty((n_paths, n), dtype=np.int64)
        for p in range(n_paths):
            pieces = [np.arange(s, s + BLOCK_SIZE) % len(r_R) for s in starts[p]]
            idx[p] = np.concatenate(pieces)[:n]
        return idx
    if scheme == "episode":
        assert blocks is not None, "episode scheme requires cluster blocks"
        idx = np.empty((n_paths, n), dtype=np.int64)
        for p in range(n_paths):
            picked: List[np.ndarray] = []
            total = 0
            while total < n:
                b = blocks[int(rng.integers(0, len(blocks)))]
                picked.append(b)
                total += len(b)
            idx[p] = np.concatenate(picked)[:n]
        return idx
    raise ValueError(f"unknown scheme {scheme}")


def joint_sequences(r_R: np.ndarray, fam: np.ndarray, scheme: str,
                    n_paths: int, n: int, seed: int,
                    blocks: Optional[List[np.ndarray]] = None,
                    family_weight: Optional[Dict[str, float]] = None,
                    family_edge: Optional[Dict[str, float]] = None,
                    idx: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Draw (r, w) matrices: r = resampled returns, w = per-trade family weight
    (default 1.0 each; pass family_weight to bake in allocation splits and
    family_edge to shrink positive returns of a family - method A). If `idx` is
    provided (see joint_indices), it is reused - the sampled index structure is
    identical for a given (scheme, seed) regardless of weights/edges."""
    if family_weight is None:
        family_weight = {"A": 1.0, "B": 1.0}
    w_1 = np.array([family_weight[f_] for f_ in fam], dtype=float)
    r_adj = r_R.copy()
    if family_edge is not None:
        pos = r_adj > 0
        for f_ in ["A", "B"]:
            mask = (fam == f_) & pos
            r_adj[mask] = r_adj[mask] * family_edge[f_]
    if idx is None:
        idx = joint_indices(r_R, scheme, n_paths, n, seed, blocks=blocks)
    return r_adj[idx], w_1[idx]


def weighted_cumprod(r_mat: np.ndarray, w_mat: np.ndarray, f: float) -> np.ndarray:
    """Equity matrix from (n_paths, n) weighted returns: prod(1 + f*w*r)."""
    return np.cumprod(1.0 + f * w_mat * r_mat, axis=1)
