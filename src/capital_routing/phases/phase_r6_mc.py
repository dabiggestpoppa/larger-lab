"""
CR-RISK-BLOCK2 R6 — Dependency-aware heat-policy Monte Carlo (XVIII) and
edge-degradation stress under heat policies (XIX).

Resampling (identical spirit to Block-I/R5, deterministic seeds):

- block:    chronological stationary block bootstrap over the merged A+B book
            (block = 25 events), blocks placed back-to-back; intra-block
            timing exact, cross-block overlap occurs naturally (as in the
            original data).
- episode:  R1 12h-cluster block bootstrap; within-cluster timing exact and
            clusters placed with their original quiet gaps (>= 12h), so
            cross-cluster overlap stays ~zero - episode structure preserved.
- iid:      reference only (H0 at 50/50).

Per path the causal admission engine decides admitted heat from the block-
internal hourly timing model; PnL aggregation follows the Block-I/R5
resampled-sequence convention (each admitted event contributes its final R at
its sequence position, equity = cumprod(1 + f * admitted_f * r)).

KEY INVARIANTS exploited for cost control:
- admission decisions are invariant to base_f (caps and requested heat both
  scale linearly with base_f) -> one admission pass per (policy, alloc, path)
  serves every f level.
- admission never reads returns -> the same admitted weights serve every edge
  scenario (XIX): only the positive-return scaling differs.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r4_common import BLOCK_SIZE, EPISODE_INTERVAL_H, span_years
from .phase_r4_mc import _longest_run_vec, _simulate_stats
from .phase_r5_common import joint_indices
from .phase_r6_common import (MC_70_30, MC_CORE, MC_F, MC_SEED,
                              _admit_sweep, book_arrays)

# PERCENTILES for MC outputs
_PCTS = [5, 25, 50, 75, 90, 95, 99]


def _book_hour_layout(load: Dict) -> Dict:
    """Merged chronological book with hour-based timing (block layout base)."""
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    t0 = entry.min()
    entry_h = (entry - t0).dt.total_seconds() / 3600.0
    exit_h = entry_h + 6.0
    return {
        "entry_h": entry_h.to_numpy(dtype=float),
        "exit_h": exit_h.to_numpy(dtype=float),
        "fam": ba["fam"], "dir": ba["dir"], "r_R": ba["r_R"],
        "n": len(tb),
    }


def _episode_block_indices(load: Dict) -> List[np.ndarray]:
    tb = load["ba"]["tb"]
    ranks = load["episode_ranks"]
    idx_of = {eid: i for i, eid in enumerate(tb["event_id"])}
    blocks: List[np.ndarray] = []
    for _, g in ranks.groupby("cluster_id"):
        idx = np.array([idx_of[e] for e in g["event_id"] if e in idx_of])
        if len(idx):
            blocks.append(idx)
    return blocks


def _path_layouts(load: Dict, scheme: str, n_paths: int, n: int,
                  seed: int) -> Tuple[List[Dict], Dict]:
    """Per-path event layouts (vectorized; block constants precomputed once).

    block scheme: 25-event stationary blocks placed back-to-back; intra-block
    timing exact (hour offsets), cross-block overlap arises naturally - an
    overlap STRESS vs the historical rate.
    episode scheme: R1 12h clusters placed with their original quiet gaps
    (>= 12h), so cross-cluster overlap stays ~zero - faithful episode
    structure (primary comparison to historical).
    """
    lay = _book_hour_layout(load)
    rng = np.random.default_rng(seed)
    n_events = lay["n"]
    entry_h = lay["entry_h"]
    fam = lay["fam"]
    direc = lay["dir"]
    r_R = lay["r_R"]
    clus_book = load["ba"]["clus"]
    if scheme == "block":
        n_blocks = int(np.ceil(n / BLOCK_SIZE))
        starts = rng.integers(0, n_events, size=(n_paths, n_blocks))
        book_span = float((entry_h[-1] + 6.0) - entry_h[0])
        pos = np.arange(BLOCK_SIZE)
        out = []
        for p in range(n_paths):
            s = starts[p]
            pos_mat = (s[:, None] + pos[None, :]) % n_events
            rel = (entry_h[pos_mat] - entry_h[s][:, None]) % book_span
            span = rel[:, -1] + 6.0
            b_start = np.concatenate([[0.0], np.cumsum(span)[:-1]])
            idx = pos_mat.ravel()[:n]
            path_entry = (b_start[:, None] + rel).ravel()[:n]
            out.append({"idx": idx, "entry": path_entry,
                        "exit": path_entry + 6.0,
                        "fam": fam[idx], "dir": direc[idx]})
        return out, lay
    if scheme == "episode":
        blocks = _episode_block_indices(load)
        b_sizes = np.array([len(b) for b in blocks], dtype=np.int64)
        b_first = np.array([entry_h[b].min() for b in blocks])
        b_span = np.array([(entry_h[b].max() + 6.0) - entry_h[b].min()
                           for b in blocks])
        rel_book = entry_h - b_first[clus_book]
        # expected blocks to reach n events (~1.85 events/cluster)
        n_draw = max(600, int(np.ceil(n / (b_sizes.mean() or 1.0))) + 8)
        out = []
        for p in range(n_paths):
            pick = rng.integers(0, len(blocks), size=n_draw)
            sizes = b_sizes[pick]
            cum = np.cumsum(sizes)
            keep = int(np.searchsorted(cum, n)) + 1
            pick = pick[:keep]
            b_start = np.concatenate([[0.0],
                                      np.cumsum(b_span[pick] + 12.0)[:-1]])
            idx = np.concatenate([blocks[b] for b in pick])[:n]
            ev_start = b_start.repeat(sizes[:keep])[:n]
            path_entry = ev_start + rel_book[idx]
            out.append({"idx": idx, "entry": path_entry,
                        "exit": path_entry + 6.0,
                        "fam": fam[idx], "dir": direc[idx]})
        return out, lay
    if scheme == "iid":
        idx_all = rng.integers(0, n_events, size=(n_paths, n))
        return [{"idx": idx_all[p], "entry": np.zeros(n), "exit": np.zeros(n),
                 "fam": fam[idx_all[p]], "dir": direc[idx_all[p]]}
                for p in range(n_paths)], lay
    raise ValueError(scheme)


def _path_episode_ids(load: Dict, layouts: List[Dict],
                      scheme: str) -> List[np.ndarray]:
    """H4 episode-budget unit per path: episode scheme -> placement id (each
    placement is a fresh R1 episode); block/iid -> 12h windows in path time."""
    clus_book = load["ba"]["clus"]
    out = []
    for lay_ in layouts:
        idx = lay_["idx"]
        if scheme == "episode":
            ep = np.zeros(len(idx), dtype=np.int64)
            k = 0
            bi = 0
            while k < len(idx):
                c0 = int(clus_book[idx[k]])
                j = k
                while j < len(idx) and int(clus_book[idx[j]]) == c0:
                    j += 1
                ep[k:j] = bi
                k = j
                bi += 1
        else:
            ep = np.zeros(len(idx), dtype=np.int64)
            e_id = 0
            w_start = lay_["entry"][0]
            for k in range(len(idx)):
                if lay_["entry"][k] - w_start > 12.0:
                    e_id += 1
                    w_start = lay_["entry"][k]
                ep[k] = e_id
        out.append(ep)
    return out


def _admit_paths(layouts: List[Dict], w_A: float, w_B: float,
                 policy: Dict, base_f: float = 1.0,
                 ep_ids: Optional[List[np.ndarray]] = None) -> List[np.ndarray]:
    """Admission per path for one policy (invariant to base_f and returns)."""
    out = []
    for k, lay in enumerate(layouts):
        req_mult = np.where(lay["fam"] == "A", w_A, w_B)
        clus = ep_ids[k] if ep_ids is not None else np.zeros(len(lay["entry"]))
        f_ = _admit_sweep(lay["entry"], lay["exit"], lay["fam"], lay["dir"],
                          clus, req_mult, policy, base_f)
        out.append(f_)
    return out


def _path_stats_matrix(eq: np.ndarray, years: float) -> Dict[str, np.ndarray]:
    stats = _simulate_stats(eq, years)
    dd = stats["dd"]
    rows: Dict[str, np.ndarray] = {
        "max_dd": stats["max_dd"], "terminal": stats["terminal"],
        "cagr": stats["cagr"], "min_eq": stats["min_eq"],
        "dur": stats["dur"],
    }
    for thr in [10.0, 15.0, 20.0, 30.0, 40.0, 50.0]:
        rows[f"P_dd_ge_{int(thr)}"] = (stats["max_dd"] >= thr / 100.0)
    rows["P_technical_ruin"] = stats["terminal"] <= 0.0
    return rows


def heat_policy_mc(load: Dict, policies: List[Dict],
                   w_A: float, w_B: float,
                   n_block: int, n_episode: int,
                   f_grid: List[float], seed: int = MC_SEED) -> pd.DataFrame:
    """Monte Carlo for every policy x f x scheme (block/episode). Rows carry
    percentile distributions + DD-threshold probabilities + ruin."""
    years = load["years"]
    ba = load["ba"]
    n = len(ba["tb"])
    rows = []
    need_h4 = any(p["kind"] == "H4" for p in policies)
    for scheme, n_paths in [("block", n_block), ("episode", n_episode)]:
        layouts, lay = _path_layouts(load, scheme, n_paths, n, seed)
        r_mat = np.stack([lay["r_R"][l["idx"]] for l in layouts])
        ep_ids = _path_episode_ids(load, layouts, scheme) if need_h4 else None
        for pol in policies:
            pid = pol["policy_id"]
            admits = _admit_paths(layouts, w_A, w_B, pol, ep_ids=ep_ids)
            w_mat = np.stack(admits)
            for f in f_grid:
                eq = np.cumprod(1.0 + (f / 100.0) * w_mat * r_mat, axis=1)
                st = _path_stats_matrix(eq, years)
                row = {"policy_id": pid, "kind": pol["kind"],
                       "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                       "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                       "scheme": scheme, "f_pct": f, "n_paths": n_paths}
                for key in ["max_dd", "terminal", "cagr", "min_eq"]:
                    for p in _PCTS:
                        row[f"{key}_p{p}"] = float(np.percentile(st[key], p))
                row["exp_cagr"] = float(np.mean(st["cagr"]))
                row["median_cagr"] = float(np.median(st["cagr"]))
                row["exp_max_dd"] = float(np.mean(st["max_dd"]))
                row["median_terminal"] = float(np.median(st["terminal"]))
                row["dur_trades_p95"] = float(np.percentile(st["dur"], 95))
                for k, v in st.items():
                    if k.startswith("P_"):
                        row[k] = float(v.mean())
                rows.append(row)
    return pd.DataFrame(rows)


def heat_edge_mc(load: Dict, policies: List[Dict], w_A: float, w_B: float,
                 scenarios: List[Tuple[float, float]], n_paths: int,
                 f_pct: float, seed: int = MC_SEED) -> pd.DataFrame:
    """Edge degradation under heat policies (XIX): admission identical across
    scenarios (it never reads returns); positive returns scaled per family."""
    years = load["years"]
    ba = load["ba"]
    n = len(ba["tb"])
    layouts, lay = _path_layouts(load, "block", n_paths, n, seed)
    fam_mat = np.stack([lay["fam"][l["idx"]] for l in layouts])
    r_base = np.stack([lay["r_R"][l["idx"]] for l in layouts])
    rows = []
    for pol in policies:
        admits = _admit_paths(layouts, w_A, w_B, pol)
        w_mat = np.stack(admits)
        for edge_A, edge_B in scenarios:
            pos = r_base > 0
            r_e = r_base.copy()
            r_e[pos & (fam_mat == "A")] *= edge_A
            r_e[pos & (fam_mat == "B")] *= edge_B
            eq = np.cumprod(1.0 + (f_pct / 100.0) * w_mat * r_e, axis=1)
            st = _path_stats_matrix(eq, years)
            row = {"policy_id": pol["policy_id"], "kind": pol["kind"],
                   "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                   "w_A_pct": w_A * 100.0, "w_B_pct": w_B * 100.0,
                   "edge_A": edge_A, "edge_B": edge_B,
                   "f_pct": f_pct, "n_paths": n_paths,
                   "exp_cagr": float(np.mean(st["cagr"])),
                   "median_cagr": float(np.median(st["cagr"])),
                   "max_dd_p50": float(np.median(st["max_dd"])),
                   "max_dd_p95": float(np.percentile(st["max_dd"], 95)),
                   "max_dd_p99": float(np.percentile(st["max_dd"], 99))}
            for thr in [10.0, 20.0, 30.0, 40.0, 50.0]:
                row[f"P_dd_ge_{int(thr)}"] = float(
                    (st["max_dd"] >= thr / 100.0).mean())
            row["P_technical_ruin"] = float(st["P_technical_ruin"].mean())
            rows.append(row)
    return pd.DataFrame(rows)


def _mc_policy_set(policy_ids: List[str], core: bool) -> List[Dict]:
    from .phase_r6_common import POLICY_GRID
    return [p for p in POLICY_GRID if p["policy_id"] in policy_ids]
