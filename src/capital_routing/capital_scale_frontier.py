"""Block-III Static Scale Frontier engine.

Executes the pre-registered Block-III capital-scale surface on top of the
sealed Block-II static architecture:

    scale ladder x frozen allocations x frozen heat references x edge states
    x resampling schemes (block / episode primary, iid diagnostic).

Deterministic. Admission is routed exclusively through the sealed static
architecture semantics (R6 vectorized admission, proven equivalent to
`static_risk_architecture.admit_book`). Common random numbers: ONE canonical
path bank per scheme is generated with the frozen seed and reused across all
allocation / heat / scale / edge cells so comparisons are paired.

Admission depends on (allocation, heat policy, path layout) only -- NOT on
f_total or retained edge.  Therefore admitted-weight matrices are computed
once per (allocation, heat, scheme) and reused across every scale x edge
cell.  Edge retention is a pure stress transform on realized outcome streams
(positive returns scaled per family; negatives untouched; never feeds back
into admission).

This module holds the ENGINE. The deterministic runner / artifact writer
lives in scripts/run_risk_block3_frontier.py.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .static_risk_architecture import FamilyAllocation, StaticRiskConfig
from .phases.phase_r6_mc import _path_layouts
from .phases.phase_r6_common import (
    _admit_sweep,
    policy_metrics,
    MC_SEED,
    POLICY_GRID,
)

# ---------------------------------------------------------------------------
# Frozen surface grid (mirrors the Block-III design grid artifact)
# ---------------------------------------------------------------------------

SCALE_LADDER_PCT: List[float] = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
OUTER_STRESS_PCT: float = 3.00
ALL_SCALE_PCT: List[float] = SCALE_LADDER_PCT + [OUTER_STRESS_PCT]

EDGE_STATES: List[float] = [1.00, 0.75, 0.50, 0.25]

ALLOCATIONS: Dict[str, FamilyAllocation] = {
    "A0_50_50": FamilyAllocation({"A": 0.5, "B": 0.5}),
    "A1_70_30": FamilyAllocation({"A": 0.7, "B": 0.3}),
    "A2_100_0_A": FamilyAllocation({"A": 1.0, "B": 0.0}),
    "A3_0_100_B": FamilyAllocation({"A": 0.0, "B": 1.0}),
    # DIAGNOSTIC ONLY
}
RECOMMENDATION_ALLOCS: List[str] = ["A0_50_50", "A1_70_30", "A2_100_0_A"]

# Frozen heat references: H0 + the four R6 H1 gross caps (REJECT treatment).
HEAT_IDS: List[str] = ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H1-2.00-REJ",
                       "H1-3.00-REJ"]

# Final path counts: >= 10000 for the primary schemes (frozen requirement);
# IID is diagnostic and documented at 2000.
PATH_COUNTS: Dict[str, int] = {"block": 10000, "episode": 10000, "iid": 2000}
PRIMARY_SCHEMES: List[str] = ["block", "episode"]
MC_SCHEMES: List[str] = ["block", "episode", "iid"]

# Bootstrap (quantile CI / paired CI): frozen, deterministic.
BOOT_N: int = 200
BOOT_SEED: int = 20260817

RISK_ENVELOPES_PCT: List[float] = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
SURVIVAL_FLOORS: List[float] = [0.90, 0.80, 0.75, 0.50]
DD_LADDER_PCT: List[float] = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
CAGR_BELOW: List[float] = [0.0, 0.10, 0.25, 0.50]

# Dependency-sensitivity materiality (pre-declared; tuned BEFORE seeing the
# frontier). Block vs episode disagree "materially" if relative DD diff > 25%
# or absolute CAGR diff > 10pp or P(DD>=10) diff > 10pp.
DEP_REL_DD_TOL: float = 0.25
DEP_ABS_CAGR_TOL: float = 0.10
DEP_ABS_PDD_TOL: float = 0.10

# Region classification thresholds (pre-declared in the frontier protocol).
# "survives_*" = median CAGR > 0 AND P(technical ruin) below tolerance under
# BOTH primary schemes (IID never used for survival classification).
SURVIVE_MEDIAN_CAGR: float = 0.0
SURVIVE_RUIN_TOL: float = 1e-6
KNEE_MIN_GAIN_PP: float = 3.0       # min median-CAGR gain to call growth
KNEE_TAIL_ACCEL: float = 1.3        # p95-DD marginal ratio considered accel.
OUTER_STRESS_LABEL: float = 3.00


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def layout_hash(layouts: List[Dict], scheme: str, seed: int) -> str:
    """Deterministic hash over the full path-bank layout (index order)."""
    h = hashlib.sha256()
    h.update(f"{scheme}:{seed}:{len(layouts)}".encode())
    for lay in layouts:
        h.update(lay["idx"].tobytes())
    return h.hexdigest()


def frozen_heat_policy(heat_id: str) -> Dict:
    """Return the R6 policy dict for a frozen heat reference."""
    for p in POLICY_GRID:
        if p["policy_id"] == heat_id:
            return p
    raise ValueError(f"unknown frozen heat reference {heat_id}")


def policy_id_from_heat(heat_id: str) -> str:
    return heat_id


# ---------------------------------------------------------------------------
# Path banks (common random numbers)
# ---------------------------------------------------------------------------

@dataclass
class PathBank:
    scheme: str
    n_paths: int
    seed: int
    layouts: List[Dict]
    lay: Dict
    layout_hash: str

    def save_manifest(self, out: Path) -> None:
        out.write_text(json.dumps({
            "scheme": self.scheme,
            "n_paths": self.n_paths,
            "seed": self.seed,
            "layout_hash": self.layout_hash,
        }, indent=2), encoding="utf-8")


def build_path_bank(load: Dict, scheme: str, n_paths: int,
                    seed: int = MC_SEED) -> PathBank:
    n = len(load["ba"]["tb"])
    layouts, lay = _path_layouts(load, scheme, n_paths, n, seed)
    return PathBank(scheme, n_paths, seed, layouts, lay,
                    layout_hash(layouts, scheme, seed))


# ---------------------------------------------------------------------------
# Admission matrices (invariant to f_total and edge; cached per config x scheme)
# ---------------------------------------------------------------------------

def admitted_weights(bank: PathBank, alloc_id: str,
                     heat_id: str) -> np.ndarray:
    """(n_paths, n_events) admitted-f matrix for one (alloc, heat) on a bank.

    base_f = 1.0 (admission invariant to f_total); family weight carries the
    allocation. Returns are never inspected -> identical across edge states.
    """
    alloc = ALLOCATIONS[alloc_id]
    wA = alloc.weight("A")
    wB = alloc.weight("B")
    pol = frozen_heat_policy(heat_id)
    rows = []
    for lay in bank.layouts:
        req_mult = np.where(lay["fam"] == "A", wA, wB)
        clus = np.zeros(len(lay["entry"]))
        f_ = _admit_sweep(lay["entry"], lay["exit"], lay["fam"], lay["dir"],
                          clus, req_mult, pol, 1.0)
        rows.append(f_)
    return np.stack(rows)


def raw_r_family_mats(bank: PathBank) -> Tuple[np.ndarray, np.ndarray]:
    """(n_paths, n_events) raw R matrix and family matrix (A mask)."""
    r = np.stack([bank.lay["r_R"][l["idx"]] for l in bank.layouts])
    famA = np.stack([bank.lay["fam"][l["idx"]] == "A"
                     for l in bank.layouts])
    return r, famA


def edge_transformed_r(r: np.ndarray, famA: np.ndarray, edge: float) -> np.ndarray:
    """Frozen R5/R6 transform: positive returns scaled by edge (both families
    share the retention state in the primary frontier); negatives untouched."""
    if edge >= 1.0:
        return r
    out = r.copy()
    pos = r > 0.0
    out[pos & famA] *= edge
    out[pos & ~famA] *= edge
    return out


# ---------------------------------------------------------------------------
# Per-path MC stats (frontier metric set)
# ---------------------------------------------------------------------------

def _frontier_path_stats(eq: np.ndarray, years: float) -> Dict[str, np.ndarray]:
    """Per-path stats + full threshold / survival ladder (Block-III set)."""
    from .phases.phase_r4_mc import _simulate_stats, _longest_run_vec
    st = _simulate_stats(eq, years)
    dd = st["dd"]
    terminal = st["terminal"]
    cagr = st["cagr"]
    min_eq = st["min_eq"]
    rows: Dict[str, np.ndarray] = {
        "max_dd": st["max_dd"], "terminal": terminal,
        "cagr": cagr, "min_eq": min_eq, "dur": st["dur"],
    }
    for thr in DD_LADDER_PCT:
        rows[f"P_dd_ge_{int(thr)}"] = (st["max_dd"] >= thr / 100.0)
    rows["P_terminal_below_1"] = terminal < 1.0
    for c in CAGR_BELOW:
        rows[f"P_cagr_below_{int(c * 100)}"] = cagr < c
    rows["P_technical_ruin"] = terminal <= 0.0
    for fl in SURVIVAL_FLOORS:
        rows[f"P_below_{int(fl * 100)}"] = (min_eq < fl)
    rows["time_under_water"] = (dd > 1e-12).sum(axis=1)
    rows["insolvent"] = terminal <= 0.0
    return rows


def mc_cell_summary(st: Dict[str, np.ndarray], n_paths: int,
                    seed: int) -> Dict[str, float]:
    """One summary dict (percentiles + probabilities) from per-path stats."""
    row: Dict[str, float] = {"n_paths": n_paths, "seed": seed}
    for key in ["max_dd", "cagr", "terminal", "min_eq"]:
        for p in [5, 25, 50, 75, 90, 95, 99]:
            row[f"{key}_p{p}"] = float(np.percentile(st[key], p))
    for key in ["dur", "time_under_water"]:
        for p in [50, 95]:
            row[f"{key}_p{p}"] = float(np.percentile(st[key], p))
    row["exp_cagr"] = float(np.mean(st["cagr"]))
    row["median_cagr"] = float(np.median(st["cagr"]))
    row["exp_max_dd"] = float(np.mean(st["max_dd"]))
    row["median_terminal"] = float(np.median(st["terminal"]))
    for k, v in st.items():
        if k.startswith("P_") or k.startswith("insolvent"):
            row[k] = float(v.mean())
    return row


def run_mc_cell(bank: PathBank, alloc_id: str, heat_id: str,
                f_pct: float, edge: float, years: float,
                w_mat: Optional[np.ndarray] = None) -> Tuple[Dict, np.ndarray]:
    """Equity path + summary for one MC cell.

    Returns (row, eq) where eq is (n_paths, n_events) -- kept for paired
    analyses when requested; callers that only need summary can drop eq.
    """
    r, famA = raw_r_family_mats(bank)
    if w_mat is None:
        w_mat = admitted_weights(bank, alloc_id, heat_id)
    r_e = edge_transformed_r(r, famA, edge)
    eq = np.cumprod(1.0 + (f_pct / 100.0) * w_mat * r_e, axis=1)
    st = _frontier_path_stats(eq, years)
    row = mc_cell_summary(st, bank.n_paths, bank.seed)
    return row, eq


# ---------------------------------------------------------------------------
# Historical surface (edge transform on the historical book, admission frozen)
# ---------------------------------------------------------------------------

def historical_edge_row(load: Dict, alloc_id: str, heat_id: str,
                        f_pct: float, edge: float) -> Dict:
    """Historical cell: sealed admission + hourly accounting, with the frozen
    edge transform applied to event returns (positives scaled per family).

    Historical metrics reuse policy_metrics (the sealed R6 accounting engine)
    so H0 100%-edge cells reproduce the frozen references exactly.
    """
    from .phases.phase_r6_common import hourly_portfolio
    ba = load["ba"]
    cfg = StaticRiskConfig(
        allocation=ALLOCATIONS[alloc_id],
        base_f=1.0,
        gross_heat_cap_mult=None if heat_id == "H0" else float(heat_id.split("-")[1]),
        treatment="REJECT",
    )
    # admission never reads returns -> identical across edge states
    from .static_risk_architecture import admit_book
    adm = admit_book(ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"],
                     cfg, direction=ba["dir"])
    years = load["years"]
    wA = ALLOCATIONS[alloc_id].weight("A")
    wB = ALLOCATIONS[alloc_id].weight("B")

    # build hourly returns from the edge-transformed per-event hourly series
    r_h = _hourly_portfolio_edge(load, adm.admitted_f, f_pct / 100.0, edge)
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r_h)])
    m = policy_metrics(load, adm.admitted_f, f_pct / 100.0, years, wA, wB)
    # override equity-derived metrics with the edge-transformed path
    from .phases.phase_r4_common import equity_metrics
    m2 = equity_metrics(eq, years, hourly=True)
    m.update(m2)

    n = int(len(adm.admitted_f))
    req = np.where(ba["fam"] == "A", wA, wB)
    m["n_events"] = n
    m["n_admitted_full"] = int(adm.n_accept_full)
    m["n_admitted_scaled"] = int(adm.n_accept_scaled)
    m["n_rejected"] = int(adm.n_rejected)
    m["rejection_fraction"] = float(adm.n_rejected / max(n, 1))
    m["scaling_fraction"] = float(adm.n_accept_scaled / max(n, 1))
    m["admission_fraction"] = float((n - adm.n_rejected) / max(n, 1))
    m["capital_utilization"] = float(
        adm.admitted_f.sum() / max(req.sum(), 1e-12))
    m["max_gross_heat_pct"] = float(adm.max_gross_heat)
    m["insolvent"] = bool(eq[-1] <= 0.0 or np.any(eq <= 0.0))
    for e in RISK_ENVELOPES_PCT:
        m[f"envelope_E{int(e)}"] = bool(m["max_dd"] < e / 100.0)
    for fl in SURVIVAL_FLOORS:
        m[f"survival_floor_{int(fl * 100)}"] = bool(
            np.min(eq) >= fl and eq[-1] >= fl)
    m["edge"] = edge
    m["alloc_id"] = alloc_id
    m["heat_id"] = heat_id
    m["f_pct"] = f_pct
    return m


def _hourly_portfolio_edge(load: Dict, admitted_f: np.ndarray,
                           base_f: float, edge: float) -> np.ndarray:
    """Hourly portfolio returns with the frozen edge transform applied to
    positive event returns per family (negative event returns untouched)."""
    ba = load["ba"]
    tb = ba["tb"]
    hourly_inc = load["hourly_inc"]
    fam = ba["fam"]
    r_R = ba["r_R"]
    idx_min = idx_max = None
    cols = []
    for i, eid in enumerate(tb["event_id"]):
        f_ = admitted_f[i]
        if f_ <= 0:
            continue
        g = hourly_inc.get(eid)
        if g is None or len(g) == 0:
            continue
        scale = edge if r_R[i] > 0 else 1.0
        ts = pd.to_datetime(g["mark_time"], utc=True)
        arr = (f_ * base_f * scale
               * g["inc_R"].to_numpy(dtype=float)).astype(np.float64)
        cols.append((ts, arr))
        i0 = ts.min()
        i1 = ts.max()
        idx_min = i0 if idx_min is None else min(idx_min, i0)
        idx_max = i1 if idx_max is None else max(idx_max, i1)
    if not cols:
        return np.zeros(1)
    full = pd.date_range(idx_min, idx_max, freq="h")
    idx_int = full.to_numpy(dtype="int64")
    total = np.zeros(len(full))
    for ts, arr in cols:
        pos = np.searchsorted(idx_int, ts.to_numpy(dtype="int64"))
        for k, p in enumerate(pos):
            total[p] += arr[k]
    return total


# ---------------------------------------------------------------------------
# Probability confidence intervals (Wilson, pre-registered; 0/N handled)
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson 95% CI for an observed count. 0/N yields (0, finite upper)."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * np.sqrt(max(p * (1 - p) / n + z * z / (4.0 * n * n), 0.0)) / denom
    lo = max(0.0, centre - half)
    hi = min(1.0, centre + half)
    return (float(lo), float(hi))


def add_probability_ci(row: Dict, key: str) -> Dict:
    """Append observed + Wilson CI columns for a probability field."""
    v = float(row.get(key, 0.0))
    n = int(row.get("n_paths", 0))
    k = int(round(v * n))
    lo, hi = wilson_ci(k, n)
    row[f"{key}_ci_lo"] = lo
    row[f"{key}_ci_hi"] = hi
    row[f"{key}_obs"] = v
    row[f"{key}_count"] = k
    return row


# ---------------------------------------------------------------------------
# Quantile bootstrap CI (deterministic, frozen seed)
# ---------------------------------------------------------------------------

def bootstrap_quantile_ci(values: np.ndarray, q: float,
                          n_boot: int = BOOT_N,
                          seed: int = BOOT_SEED) -> Tuple[float, float]:
    """95% bootstrap percentile CI for the q-quantile of `values`.

    Sort-based: one sort of the full sample, then each bootstrap replicate
    resamples indices and reads the order statistic -- much faster than
    per-replicate np.percentile on 10k-path samples.
    """
    rng = np.random.default_rng(seed)
    n = len(values)
    if n == 0:
        return (np.nan, np.nan)
    v = np.sort(np.asarray(values, dtype=float))
    idx = rng.integers(0, n, size=(n_boot, n))
    rank = int(round(q / 100.0 * (n - 1)))
    sampled = v[idx]
    boot = np.sort(sampled, axis=1)[:, rank]
    return (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))


# ---------------------------------------------------------------------------
# Paired H1 vs H0 (identical path banks -> per-path deltas)
# ---------------------------------------------------------------------------

def paired_h1_vs_h0(bank: PathBank, alloc_id: str, heat_id: str,
                    f_pct: float, edge: float, years: float,
                    seed: int = BOOT_SEED,
                    w_h1: Optional[np.ndarray] = None,
                    w_h0: Optional[np.ndarray] = None) -> Dict:
    """Per-path delta of H1 relative to H0 at the same (alloc, f, edge).

    Identical path banks make the comparison paired per path.  Admission
    matrices may be passed in (cached) to avoid recomputation.
    """
    if w_h1 is None:
        w_h1 = admitted_weights(bank, alloc_id, heat_id)
    if w_h0 is None:
        w_h0 = admitted_weights(bank, alloc_id, "H0")
    r, famA = raw_r_family_mats(bank)
    r_e = edge_transformed_r(r, famA, edge)
    f = f_pct / 100.0
    eq1 = np.cumprod(1.0 + f * w_h1 * r_e, axis=1)
    eq0 = np.cumprod(1.0 + f * w_h0 * r_e, axis=1)
    st1 = _frontier_path_stats(eq1, years)
    st0 = _frontier_path_stats(eq0, years)
    out: Dict = {}
    d_cagr = st1["cagr"] - st0["cagr"]
    d_dd = st1["max_dd"] - st0["max_dd"]
    d_term = st1["terminal"] - st0["terminal"]
    d_dur = st1["dur"].astype(float) - st0["dur"].astype(float)
    out["d_median_cagr"] = float(np.median(d_cagr))
    out["d_p5_cagr"] = float(np.percentile(d_cagr, 5))
    out["d_p95_cagr"] = float(np.percentile(d_cagr, 95))
    out["d_median_max_dd"] = float(np.median(d_dd))
    out["d_p5_max_dd"] = float(np.percentile(d_dd, 5))
    out["d_p95_max_dd"] = float(np.percentile(d_dd, 95))
    out["d_median_terminal"] = float(np.median(d_term))
    out["d_p5_terminal"] = float(np.percentile(d_term, 5))
    out["d_p95_terminal"] = float(np.percentile(d_term, 95))
    out["d_median_dur"] = float(np.median(d_dur))
    out["P_h1_dd_lt_h0"] = float((d_dd < 0).mean())
    out["P_h1_term_gt_h0"] = float((d_term > 0).mean())
    lo, hi = bootstrap_quantile_ci(d_cagr, 50, seed=seed)
    out["d_median_cagr_ci_lo"] = lo
    out["d_median_cagr_ci_hi"] = hi
    lo, hi = bootstrap_quantile_ci(d_dd, 50, seed=seed)
    out["d_median_dd_ci_lo"] = lo
    out["d_median_dd_ci_hi"] = hi
    return out


# ---------------------------------------------------------------------------
# Adjacent-scale / marginal efficiency / knee (descriptive, pre-declared)
# ---------------------------------------------------------------------------

def adjacent_scale_deltas(mc: pd.DataFrame, alloc_id: str, heat_id: str,
                          edge: float, scheme: str) -> List[Dict]:
    """Paired deltas between adjacent scale points (same bank -> paired)."""
    sub = mc[(mc["alloc_id"] == alloc_id) & (mc["heat_id"] == heat_id)
             & (np.isclose(mc["edge"], edge)) & (mc["scheme"] == scheme)]
    sub = sub.sort_values("f_pct")
    rows = []
    for a, b in zip(ALL_SCALE_PCT[:-1], ALL_SCALE_PCT[1:]):
        ra = sub[sub["f_pct"] == a]
        rb = sub[sub["f_pct"] == b]
        if len(ra) == 0 or len(rb) == 0:
            continue
        ra, rb = ra.iloc[0], rb.iloc[0]
        rows.append({
            "alloc_id": alloc_id, "heat_id": heat_id, "edge": edge,
            "scheme": scheme, "f_from": a, "f_to": b,
            "d_median_cagr": rb["median_cagr"] - ra["median_cagr"],
            "d_p95_dd": rb["max_dd_p95"] - ra["max_dd_p95"],
            "d_p99_dd": rb["max_dd_p99"] - ra["max_dd_p99"],
            "d_P_dd_ge_10": rb["P_dd_ge_10"] - ra["P_dd_ge_10"],
            "d_P_dd_ge_20": rb["P_dd_ge_20"] - ra["P_dd_ge_20"],
            "d_median_dur": rb["dur_p50"] - ra["dur_p50"],
        })
    return rows


def marginal_efficiency(rows: List[Dict]) -> List[Dict]:
    """Descriptive ratios; denominator <= tiny -> flagged non-comparable."""
    out = []
    for r in rows:
        d = dict(r)
        num = r["d_median_cagr"]
        for denom_key, out_key in [("d_p95_dd", "inc_ret_per_p95_dd"),
                                   ("d_p99_dd", "inc_ret_per_p99_dd")]:
            denom = r[denom_key]
            if abs(denom) <= 1e-9:
                d[out_key] = None
                d[f"{out_key}_flag"] = "NON_COMPARABLE"
            else:
                d[out_key] = float(num / denom)
                d[f"{out_key}_flag"] = "OK"
        out.append(d)
    return out


def knee_detection(rows: List[Dict]) -> Dict:
    """Broad-interval knee: growth gain flattens while tail DD accelerates.

    Pre-declared rule: walk adjacent deltas (ascending scale). The knee
    interval starts at the first pair where the median-CAGR gain drops below
    KNEE_MIN_GAIN_PP (percentage points) while the p95-DD marginal ratio
    versus the previous pair exceeds KNEE_TAIL_ACCEL. Returns a broad interval
    (from_f .. to_f), never a single point. KNEE_UNSTABLE when the interval
    differs materially across primary schemes / edges.
    """
    if len(rows) < 2:
        return {"knee_interval": None, "knee_condition": "INSUFFICIENT_DATA"}
    gains = [(r["f_from"], r["f_to"], r["d_median_cagr"] * 100.0,
              r["d_p95_dd"] * 100.0) for r in rows]
    knee_from = knee_to = None
    prev_tail = None
    for (f0, f1, g, t) in gains:
        accel = (t / prev_tail) if (prev_tail and prev_tail > 0) else 1.0
        if g < KNEE_MIN_GAIN_PP and accel > KNEE_TAIL_ACCEL:
            knee_from, knee_to = f0, f1
            break
        prev_tail = t if prev_tail is None else t
    return {"knee_interval": [knee_from, knee_to] if knee_from else None,
            "knee_condition": "FOUND" if knee_from else "NOT_FOUND"}


# ---------------------------------------------------------------------------
# Region classification (pre-declared rules)
# ---------------------------------------------------------------------------

def classify_region(row: Dict) -> str:
    """Evidence-based cell classification. Rules pre-declared in the protocol.

    Order of checks (top-down, edge-driven):
      1. median CAGR <= 0 at 100% and 75% edge under both primary schemes
         -> NON_VIABLE (no positive expectancy even at full edge).
      2. survives only at 100% edge (fails at 75%) -> EDGE_SENSITIVE.
      3. survives 100%+75% but fails 50% -> FRAGILE_HIGH_SCALE (if high f)
         or ROBUST_LOW_SCALE (if low f), via the survival vector.
      4. survives 75%+50%+100% -> ROBUST_GROWTH / ROBUST_LOW_SCALE.
    A3 (0/100 B) is diagnostic only and never recommendation-bearing.
    """
    med = row.get("median_cagr_100", np.nan)
    med75 = row.get("median_cagr_75", np.nan)
    med50 = row.get("median_cagr_50", np.nan)
    if not np.isfinite(med):
        return "NO_DATA"
    if med <= 0.0 and med75 <= 0.0:
        return "NON_VIABLE"
    if med75 <= 0.0:
        return "EDGE_SENSITIVE"
    if med50 <= 0.0:
        f = row.get("f_pct", 1.0)
        return "FRAGILE_HIGH_SCALE" if f >= 1.0 else "ROBUST_LOW_SCALE"
    f = row.get("f_pct", 1.0)
    if f >= 1.5:
        return "AGGRESSIVE_FRAGILE" if row.get("p95_dd_100", 0.10) > 0.10 \
            else "ROBUST_GROWTH_REGION"
    return "ROBUST_LOW_SCALE" if f <= 0.5 else "ROBUST_GROWTH_REGION"


def edge_survival_vector(mc: pd.DataFrame, alloc_id: str, heat_id: str,
                         f_pct: float) -> Dict:
    """Aggregate survival truth across primary schemes at each edge state."""
    out: Dict = {}
    for edge in EDGE_STATES:
        sub = mc[(mc["alloc_id"] == alloc_id) & (mc["heat_id"] == heat_id)
                 & (np.isclose(mc["edge"], edge)) & (mc["f_pct"] == f_pct)
                 & (mc["scheme"].isin(PRIMARY_SCHEMES))]
        if len(sub) == 0:
            out[f"survives_{int(edge * 100)}"] = False
            continue
        med_ok = (sub["median_cagr"] > SURVIVE_MEDIAN_CAGR).all()
        ruin_ok = (sub["P_technical_ruin"] < SURVIVE_RUIN_TOL).all()
        out[f"survives_{int(edge * 100)}"] = bool(med_ok and ruin_ok)
        out[f"median_cagr_{int(edge * 100)}"] = float(
            sub["median_cagr"].mean())
        out[f"p95_dd_{int(edge * 100)}"] = float(
            sub["max_dd_p95"].mean())
    return out


def dependency_sensitive(block_row: pd.Series, ep_row: pd.Series) -> bool:
    """Material block/episode disagreement (pre-declared thresholds)."""
    if np.isclose(block_row["max_dd_p95"], 0) and np.isclose(ep_row["max_dd_p95"], 0):
        dd_diff = 0.0
    else:
        base = max(abs(block_row["max_dd_p95"]), abs(ep_row["max_dd_p95"]), 1e-9)
        dd_diff = abs(block_row["max_dd_p95"] - ep_row["max_dd_p95"]) / base
    cagr_diff = abs(block_row["median_cagr"] - ep_row["median_cagr"])
    pdd_diff = abs(block_row["P_dd_ge_10"] - ep_row["P_dd_ge_10"])
    return (dd_diff > DEP_REL_DD_TOL or cagr_diff > DEP_ABS_CAGR_TOL
            or pdd_diff > DEP_ABS_PDD_TOL)


def nondominated(mc: pd.DataFrame, alloc_ids: List[str],
                 heat_ids: List[str], edge: float, scheme: str) -> pd.DataFrame:
    """Non-dominated (alloc, heat, f) points on (p95 DD down, median CAGR up).

    Descriptive only -- never a selection rule.
    """
    sub = mc[(mc["edge"] == edge) & (mc["scheme"] == scheme)
             & (mc["alloc_id"].isin(alloc_ids))
             & (mc["heat_id"].isin(heat_ids))].copy()
    pts = sub[["alloc_id", "heat_id", "f_pct", "max_dd_p95", "median_cagr"]]
    dom = np.zeros(len(pts), dtype=bool)
    arr_dd = pts["max_dd_p95"].to_numpy()
    arr_c = pts["median_cagr"].to_numpy()
    for i in range(len(pts)):
        better_dd = arr_dd < arr_dd[i] - 1e-9
        better_c = arr_c > arr_c[i] + 1e-9
        equal_dd = np.abs(arr_dd - arr_dd[i]) <= 1e-9
        equal_c = np.abs(arr_c - arr_c[i]) <= 1e-9
        dom[i] = ((better_dd & (better_c | equal_c))
                  | (better_c & (better_dd | equal_dd))).any()
    out = pts[~dom].copy()
    out = out.sort_values(["alloc_id", "heat_id", "f_pct"])
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Surface grid construction
# ---------------------------------------------------------------------------

def surface_configs() -> List[Dict]:
    """All (alloc, heat, f, edge) historical/MC cells (560)."""
    out = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            for f_pct in ALL_SCALE_PCT:
                for edge in EDGE_STATES:
                    out.append({"alloc_id": alloc_id, "heat_id": heat_id,
                                "f_pct": f_pct, "edge": edge})
    return out
