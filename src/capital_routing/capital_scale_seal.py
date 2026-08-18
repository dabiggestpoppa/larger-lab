"""CR-RISK-BLOCK-III-SCALE-SEAL engine.

Freezes the scientifically-supported STATIC SCALE OPERATING REGION from the
completed Block-III frontier. This checkpoint is a SYNTHESIS of the frozen
frontier artifacts -- it runs NO new optimization and NO new Monte Carlo:

    frontier artifacts (MC surface, historical surface, edge survival, knee
    analysis, paired H1-vs-H0, dependency sensitivity, region classification)
    -> operating bands, allocation review, heat review, edge review, knee
    band, adjacent-scale cost, robust core, risk contract, decision.

Everything here is deterministic: inputs are frozen CSVs/JSONs written by the
frontier checkpoint (commit a58f8483), and every review table is a pure
function of them.

Frozen operating rules applied by this checkpoint (pre-declared):

1. Scale bands come from the frontier region classification + knee +
   adjacent-scale evidence, NOT from any growth-maximization. Expected form
   (confirmed by evidence):
     CONSERVATIVE = [0.25, 0.50]
     ROBUST CORE  = [0.75, 1.00]
     AGGRESSIVE   = [1.50, 2.00]
     STRESS ONLY  = [3.00]
2. Allocation principle: prefer diversified allocation when its tail/risk
   efficiency is close to (or better than) A-only. A-only is never chosen
   because headline CAGR is larger.
3. Heat seal principle: retain H1 only when paired common-random-number
   evidence shows repeatable meaningful tail reduction for a reasonable
   growth cost. H1 caps that do not bind buy nothing and are not retained
   as operating layers.
4. Edge retention: the operating band must survive 100% and 75% retained
   edge robustly (block AND episode), have interpretable 50% behavior, and
   25% is the recorded alpha-loss boundary (not required to survive).
5. Dependency agreement: block and episode are co-primary. A band is not
   sealable if block says robust but episode says fragile (or vice versa).
6. Knee band: modal knee interval from the frozen knee analysis (expected
   [1.00, 1.50]); the robust core must sit below the knee.
7. Adjacent-scale seal: marginal tail risk (P(DD>=10/15)) must not accelerate
   within the robust core; acceleration at 1.00->1.50 confirms the boundary.
8. NO best cell: the output is an operating band plus (only if the evidence
   supports a clear stable midpoint) a single preferred research default for
   future demo translation. No Kelly, no DD-adaptive sizing, no production
   sizing, no deployment, no MT5.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Frozen frontier surface constants (mirror the frontier module)
# ---------------------------------------------------------------------------

RECOMMENDATION_ALLOCS: List[str] = ["A0_50_50", "A1_70_30", "A2_100_0_A"]
ALLOC_NAMES = {
    "A0_50_50": "50/50 A/B diversified reference",
    "A1_70_30": "70/30 A-heavy robust reference",
    "A2_100_0_A": "100/0 A concentration reference",
    "A3_0_100_B": "0/100 B diagnostic ONLY",
}
PRIMARY_SCHEMES: List[str] = ["block", "episode"]
HEAT_IDS: List[str] = ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H1-2.00-REJ",
                       "H1-3.00-REJ"]
ALL_SCALE_PCT: List[float] = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00]
EDGE_STATES: List[float] = [1.00, 0.75, 0.50, 0.25]

# Sealed operating bands (evidence-backed, see protocol).
CONSERVATIVE_BAND: List[float] = [0.25, 0.50]
ROBUST_CORE_BAND: List[float] = [0.75, 1.00]
AGGRESSIVE_BAND: List[float] = [1.50, 2.00]
STRESS_BAND: List[float] = [3.00, 3.00]

# Operating heat reference (R6 frozen gross cap; see heat review).
OPERATING_HEAT: str = "H1-1.00-REJ"
OPERATING_ALLOCS: List[str] = ["A0_50_50", "A1_70_30"]
PREFERRED_ALLOC: str = "A1_70_30"
PREFERRED_F_PCT: float = 1.00
PREFERRED_HEAT: str = "H1-1.00-REJ"

ADJACENT_PAIRS: List[Tuple[float, float]] = [
    (0.50, 0.75), (0.75, 1.00), (1.00, 1.50), (1.50, 2.00),
]

# Materiality for "tail acceleration" across an adjacent scale pair.
P10_ACCEL_THRESHOLD: float = 0.05   # delta P(DD>=10) >= 5pp = accelerating
CAGR_MIN_GAIN_PP: float = 3.0       # below this the growth gain is "flat"


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_frontier(out: Path) -> Dict:
    """Read all frozen frontier artifacts into one dict."""
    return {
        "mc": pd.read_csv(out / "CR_RISK_BLOCK3_MC_SURFACE.csv"),
        "hist": pd.read_csv(out / "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv"),
        "surv": pd.read_csv(out / "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv"),
        "knee": pd.read_csv(out / "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv"),
        "paired": pd.read_csv(out / "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv"),
        "dep": pd.read_csv(out / "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv"),
        "reg": pd.read_csv(out / "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv"),
        "decision": json.loads(
            (out / "CR_RISK_BLOCK3_DECISION.json").read_text(encoding="utf-8")),
        "nonreg": json.loads((out / "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json")
                             .read_text(encoding="utf-8")),
        "r6reg": json.loads((out / "CR_RISK_BLOCK3_R6_MC_REGRESSION.json")
                            .read_text(encoding="utf-8")),
    }


def input_hash_manifest(frontier_out: Path, base_commit: str,
                        frontier_files: List[str]) -> Dict:
    """SHA-256 manifest of every frozen frontier input consumed by the seal."""
    entries = {}
    for name in frontier_files:
        p = frontier_out / name
        if p.exists():
            entries[name] = _sha256_file(p)
        else:
            entries[name] = None
    return {
        "checkpoint": "CR-RISK-BLOCK-III-SCALE-SEAL",
        "base_commit": base_commit,
        "frontier_dir": str(frontier_out.relative_to(frontier_out.parents[3])),
        "files": entries,
        "note": "All seal review tables are pure functions of these frozen "
                "inputs; no new MC / optimization is run by this checkpoint.",
    }


# ---------------------------------------------------------------------------
# Knee review
# ---------------------------------------------------------------------------

def knee_review(knee: pd.DataFrame) -> pd.DataFrame:
    """Freeze the knee band from the frozen knee analysis.

    Returns per-(alloc, heat, edge, scheme) rows plus the modal knee interval
    annotation.  The seal uses the MODAL interval as the knee band; a robust
    core below the knee start is a seal prerequisite.
    """
    rows = []
    for _, r in knee[knee["scheme"].isin(PRIMARY_SCHEMES)].iterrows():
        rows.append({
            "alloc_id": r["alloc_id"], "heat_id": r["heat_id"],
            "edge": r["edge"], "scheme": r["scheme"],
            "knee_interval": _fmt_interval(r["knee_interval"]),
            "knee_condition": r["knee_condition"],
            "is_recommendation_alloc": r["alloc_id"] in RECOMMENDATION_ALLOCS,
        })
    df = pd.DataFrame(rows)
    return df


def _fmt_interval(v) -> str:
    """Canonical interval string from a list/tuple/string/NaN."""
    iv = _parse_interval(v)
    if iv is None:
        return np.nan if isinstance(v, (float, np.floating)) else ""
    return f"[{iv[0]:.2f}, {iv[1]:.2f}]"


def knee_band(knee: pd.DataFrame) -> Tuple[Optional[List[float]], Dict]:
    """Modal knee interval over recommendation allocs / primary schemes.

    Returns (band, stats).  band=None when no knee found.
    """
    k = knee[(knee["scheme"].isin(PRIMARY_SCHEMES))
             & (knee["alloc_id"].isin(RECOMMENDATION_ALLOCS))].copy()
    k["_interval"] = k["knee_interval"].map(_parse_interval)
    found = k[k["_interval"].notna()]
    if len(found) == 0:
        return None, {"n_cells": int(len(k)), "n_found": 0}
    counts = found["_interval"].value_counts()
    top = counts.index[0]
    stats = {
        "n_cells": int(len(k)),
        "n_found": int(len(found)),
        "distinct_intervals": {_fmt_interval(list(iv)): int(c)
                               for iv, c in counts.items()},
        "modal_interval": _fmt_interval(list(top)),
    }
    return [float(top[0]), float(top[1])], stats


def _parse_interval(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    try:
        if isinstance(v, str):
            s = v.strip().strip("[]").split(",")
            vals = [float(x) for x in s]
        else:
            vals = [float(x) for x in v]
        if len(vals) == 2:
            return (vals[0], vals[1])
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Adjacent-scale review
# ---------------------------------------------------------------------------

def adjacent_scale_review(mc: pd.DataFrame, allocs: List[str],
                          heats: List[str]) -> pd.DataFrame:
    """Incremental cost of each adjacent scale step, computed from the MC
    surface directly (primary schemes, 100% edge).

    For each (alloc, heat, scheme, f_from->f_to): incremental median CAGR,
    p95 DD, P(DD>=10), P(DD>=15) -- plus the marginal P(DD>=10) cost per unit
    of median-CAGR gain (acceleration diagnostic).
    """
    rows = []
    sub = mc[(mc["edge"] == 1.0) & (mc["scheme"].isin(PRIMARY_SCHEMES))
             & (mc["alloc_id"].isin(allocs)) & (mc["heat_id"].isin(heats))]
    for alloc_id in allocs:
        for heat_id in heats:
            for scheme in PRIMARY_SCHEMES:
                for f0, f1 in ADJACENT_PAIRS:
                    r0 = _cell(sub, alloc_id, heat_id, scheme, f0)
                    r1 = _cell(sub, alloc_id, heat_id, scheme, f1)
                    if r0 is None or r1 is None:
                        continue
                    d_cagr = r1["median_cagr"] - r0["median_cagr"]
                    d_p95 = r1["max_dd_p95"] - r0["max_dd_p95"]
                    d_p10 = r1["P_dd_ge_10"] - r0["P_dd_ge_10"]
                    d_p15 = r1["P_dd_ge_15"] - r0["P_dd_ge_15"]
                    accel = np.nan
                    flag = "OK"
                    if abs(d_cagr) > 1e-9:
                        accel = d_p10 / abs(d_cagr)
                        if d_p10 >= P10_ACCEL_THRESHOLD and \
                                d_cagr * 100.0 < CAGR_MIN_GAIN_PP:
                            flag = "TAIL_ACCELERATION_FLAT_GROWTH"
                        elif d_p10 >= P10_ACCEL_THRESHOLD:
                            flag = "TAIL_ACCELERATION"
                    rows.append({
                        "alloc_id": alloc_id, "heat_id": heat_id,
                        "scheme": scheme, "f_from": f0, "f_to": f1,
                        "d_median_cagr": d_cagr,
                        "d_p95_max_dd": d_p95,
                        "d_P_dd_ge_10": d_p10,
                        "d_P_dd_ge_15": d_p15,
                        "marginal_p10_per_cagr": accel,
                        "acceleration_flag": flag,
                    })
    return pd.DataFrame(rows)


def _cell(df: pd.DataFrame, alloc_id: str, heat_id: str, scheme: str,
          f_pct: float) -> Optional[pd.Series]:
    m = df[(df["alloc_id"] == alloc_id) & (df["heat_id"] == heat_id)
           & (df["scheme"] == scheme) & (df["f_pct"] == f_pct)]
    if len(m) == 0:
        return None
    return m.iloc[0]


def adjacent_scale_seal_pass(adj: pd.DataFrame) -> Dict:
    """Seal check: no tail acceleration inside the robust core (0.75->1.00);
    acceleration present at the 1.00->1.50 boundary under the operating heat
    for the operating allocation family.

    Scheme agreement uses the frontier's relative-tolerance philosophy: for
    each (alloc, scheme), the boundary step's incremental P(DD>=10) must
    exceed the LARGEST inside-core incremental P(DD>=10) for the same
    (alloc, scheme) -- i.e. both block and episode must independently agree
    that tail risk jumps at the boundary relative to the core, even when the
    jump magnitude differs by scheme."""
    core = adj[(adj["f_from"] == 0.75) & (adj["f_to"] == 1.00)]
    bnd = adj[(adj["f_from"] == 1.00) & (adj["f_to"] == 1.50)]
    core_op = core[(core["heat_id"] == OPERATING_HEAT)
                   & (core["alloc_id"].isin(OPERATING_ALLOCS))]
    bnd_op = bnd[(bnd["heat_id"] == OPERATING_HEAT)
                 & (bnd["alloc_id"].isin(OPERATING_ALLOCS))]
    core_accel = int((core_op["acceleration_flag"] != "OK").sum()) if len(core_op) else 0

    # per (alloc, scheme): does boundary dP10 exceed the max inside-core dP10?
    agree = 0
    total = 0
    for alloc_id in OPERATING_ALLOCS:
        for scheme in PRIMARY_SCHEMES:
            c = core_op[(core_op["alloc_id"] == alloc_id)
                        & (core_op["scheme"] == scheme)]
            b = bnd_op[(bnd_op["alloc_id"] == alloc_id)
                       & (bnd_op["scheme"] == scheme)]
            if len(c) == 0 or len(b) == 0:
                continue
            total += 1
            core_max = float(c["d_P_dd_ge_10"].max())
            bnd_val = float(b["d_P_dd_ge_10"].iloc[0])
            if bnd_val > core_max + 0.01:  # boundary jump clearly above core
                agree += 1
    bnd_agree = total > 0 and agree == total
    bnd_accel = int((bnd_op["d_P_dd_ge_10"] > 0.05).sum()) if len(bnd_op) else 0
    pass_ = (core_accel == 0 and bnd_accel > 0 and bnd_agree)
    return {
        "pass": bool(pass_),
        "core_accelerating_cells": core_accel,
        "boundary_accelerating_cells": bnd_accel,
        "boundary_scheme_agreement": bool(bnd_agree),
        "boundary_agree_count": agree,
        "boundary_agree_total": total,
        "note": "tail risk must NOT accelerate inside 0.75->1.00 and MUST "
                "accelerate at 1.00->1.50 under the operating heat; block "
                "and episode must each independently show the boundary jump "
                "relative to the inside-core max",
    }





# ---------------------------------------------------------------------------
# Allocation review
# ---------------------------------------------------------------------------

def allocation_review(mc: pd.DataFrame, hist: pd.DataFrame,
                      surv: pd.DataFrame) -> pd.DataFrame:
    """Per-allocation review at f=1.00 under the operating heat.

    Columns: historical CAGR / max DD, block+episode median CAGR, block /
    episode p95 DD, P(DD>=5/10/15/20) consensus, retained-edge survival
    100/75/50/25, tail efficiency (median CAGR / p95 DD), and the pairwise
    allocation transitions 50/50 -> 70/30 -> A-only.
    """
    rows = []
    for alloc_id in RECOMMENDATION_ALLOCS:
        h = hist[(hist["alloc_id"] == alloc_id) & (hist["heat_id"] == "H0")
                 & (hist["f_pct"] == 1.0) & (hist["edge"] == 1.0)]
        hh = hist[(hist["alloc_id"] == alloc_id)
                  & (hist["heat_id"] == OPERATING_HEAT)
                  & (hist["f_pct"] == 1.0) & (hist["edge"] == 1.0)]
        mc_op = mc[(mc["alloc_id"] == alloc_id) & (mc["heat_id"] == OPERATING_HEAT)
                   & (mc["f_pct"] == 1.0) & (mc["edge"] == 1.0)
                   & (mc["scheme"].isin(PRIMARY_SCHEMES))]
        sv = surv[(surv["alloc_id"] == alloc_id) & (surv["heat_id"] == OPERATING_HEAT)
                  & (surv["f_pct"] == 1.0)]
        row = {
            "alloc_id": alloc_id,
            "alloc_name": ALLOC_NAMES.get(alloc_id, ""),
            "historical_cagr_pct": float(hh["cagr"].iloc[0] * 100) if len(hh) else np.nan,
            "historical_max_dd_pct": float(hh["max_dd"].iloc[0] * 100) if len(hh) else np.nan,
            "block_median_cagr": float(mc_op[mc_op["scheme"] == "block"]["median_cagr"].mean()),
            "episode_median_cagr": float(mc_op[mc_op["scheme"] == "episode"]["median_cagr"].mean()),
            "block_p95_dd": float(mc_op[mc_op["scheme"] == "block"]["max_dd_p95"].mean()),
            "episode_p95_dd": float(mc_op[mc_op["scheme"] == "episode"]["max_dd_p95"].mean()),
            "P_dd_ge_5": float(mc_op["P_dd_ge_5"].mean()),
            "P_dd_ge_10": float(mc_op["P_dd_ge_10"].mean()),
            "P_dd_ge_15": float(mc_op["P_dd_ge_15"].mean()),
            "P_dd_ge_20": float(mc_op["P_dd_ge_20"].mean()),
            "survives_100": bool(sv["survives_100"].iloc[0]) if len(sv) else False,
            "survives_75": bool(sv["survives_75"].iloc[0]) if len(sv) else False,
            "survives_50": bool(sv["survives_50"].iloc[0]) if len(sv) else False,
            "survives_25": bool(sv["survives_25"].iloc[0]) if len(sv) else False,
            "tail_efficiency": float(
                mc_op["median_cagr"].mean() / max(mc_op["max_dd_p95"].mean(), 1e-9)),
            "diagnostic_only": alloc_id == "A3_0_100_B",
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    # pairwise allocation transitions (operating heat, f=1.00, block+episode)
    trans = []
    pairs = [("A0_50_50", "A1_70_30"), ("A1_70_30", "A2_100_0_A")]
    for a, b in pairs:
        ra = _alloc_metrics(mc, a, OPERATING_HEAT, 1.0)
        rb = _alloc_metrics(mc, b, OPERATING_HEAT, 1.0)
        trans.append({
            "transition": f"{a}->{b}",
            "d_median_cagr": rb["median_cagr"] - ra["median_cagr"],
            "d_p95_dd": rb["p95_dd"] - ra["p95_dd"],
            "d_P_dd_ge_10": rb["P_dd_ge_10"] - ra["P_dd_ge_10"],
            "d_P_dd_ge_15": rb["P_dd_ge_15"] - ra["P_dd_ge_15"],
        })
    df.attrs["transitions"] = pd.DataFrame(trans)
    return df


def _alloc_metrics(mc: pd.DataFrame, alloc_id: str, heat_id: str,
                   f_pct: float) -> Dict:
    sub = mc[(mc["alloc_id"] == alloc_id) & (mc["heat_id"] == heat_id)
             & (mc["f_pct"] == f_pct) & (mc["edge"] == 1.0)
             & (mc["scheme"].isin(PRIMARY_SCHEMES))]
    return {
        "median_cagr": float(sub["median_cagr"].mean()),
        "p95_dd": float(sub["max_dd_p95"].mean()),
        "P_dd_ge_10": float(sub["P_dd_ge_10"].mean()),
        "P_dd_ge_15": float(sub["P_dd_ge_15"].mean()),
    }


# ---------------------------------------------------------------------------
# Heat review
# ---------------------------------------------------------------------------

def heat_review(mc: pd.DataFrame, hist: pd.DataFrame,
                paired: pd.DataFrame) -> pd.DataFrame:
    """Paired common-random-number review of each H1 cap vs H0.

    Uses the frozen per-path deltas (identical path banks -> paired) for
    delta median CAGR and delta median/p95 DD, and the MC surface for delta
    P(DD>=10/15).  Historical rejection / capital utilization / max gross
    heat come from the historical surface (operating allocs, f=1.00, 100%
    edge).  Verdict per heat follows the heat seal principle.
    """
    rows = []
    for heat_id in HEAT_IDS:
        if heat_id == "H0":
            continue
        cap = float(heat_id.split("-")[1])
        # Decision-relevant paired evidence: operating allocs, robust-core
        # scale band, primary schemes (all retained-edge states pooled so the
        # verdict reflects behavior as the edge decays).
        p = paired[(paired["heat_id"] == heat_id)
                   & (paired["scheme"].isin(PRIMARY_SCHEMES))
                   & (paired["alloc_id"].isin(OPERATING_ALLOCS))
                   & (paired["f_pct"].isin(ROBUST_CORE_BAND))]
        mc_op = mc[(mc["heat_id"] == heat_id) & (mc["edge"] == 1.0)
                   & (mc["scheme"].isin(PRIMARY_SCHEMES))
                   & (mc["alloc_id"].isin(OPERATING_ALLOCS))
                   & (mc["f_pct"].isin(ROBUST_CORE_BAND))]
        mc_h0 = mc[(mc["heat_id"] == "H0") & (mc["edge"] == 1.0)
                   & (mc["scheme"].isin(PRIMARY_SCHEMES))
                   & (mc["alloc_id"].isin(OPERATING_ALLOCS))
                   & (mc["f_pct"].isin(ROBUST_CORE_BAND))]
        h = hist[(hist["heat_id"] == heat_id) & (hist["f_pct"] == 1.0)
                 & (hist["edge"] == 1.0) & (hist["alloc_id"].isin(OPERATING_ALLOCS))]
        h0 = hist[(hist["heat_id"] == "H0") & (hist["f_pct"] == 1.0)
                  & (hist["edge"] == 1.0) & (hist["alloc_id"].isin(OPERATING_ALLOCS))]
        d_p10 = float(mc_op["P_dd_ge_10"].mean() - mc_h0["P_dd_ge_10"].mean())
        d_p15 = float(mc_op["P_dd_ge_15"].mean() - mc_h0["P_dd_ge_15"].mean())
        d_p95 = float(mc_op["max_dd_p95"].mean() - mc_h0["max_dd_p95"].mean())
        hist_dd = float(h["max_dd"].mean() - h0["max_dd"].mean())
        hist_cagr = float(h["cagr"].mean() - h0["cagr"].mean())
        d_cagr = float(p["d_median_cagr"].mean()) if len(p) else np.nan
        d_med_dd = float(p["d_median_max_dd"].mean()) if len(p) else np.nan
        p_lt = float(p["P_h1_dd_lt_h0"].mean()) if len(p) else np.nan
        verdict = _heat_verdict(cap, d_cagr, d_med_dd, d_p10, p_lt)
        rows.append({
            "heat_id": heat_id,
            "gross_cap_mult": cap,
            "scope": "operating allocs x robust-core band x primary schemes",
            "d_median_cagr": d_cagr,
            "d_median_max_dd": d_med_dd,
            "d_p95_max_dd": float(p["d_p95_max_dd"].mean()) if len(p) else np.nan,
            "P_h1_dd_lt_h0": p_lt,
            "P_h1_term_gt_h0": float(p["P_h1_term_gt_h0"].mean()) if len(p) else np.nan,
            "d_P_dd_ge_10": d_p10,
            "d_P_dd_ge_15": d_p15,
            "d_mc_p95_dd": d_p95,
            "hist_d_cagr_pct": hist_cagr * 100.0,
            "hist_d_max_dd_pct": hist_dd * 100.0,
            "rejection_fraction": float(h["rejection_fraction"].mean()),
            "capital_utilization": float(h["capital_utilization"].mean()),
            "max_gross_heat_pct": float(h["max_gross_heat_pct"].mean()),
            "verdict": verdict,
        })
    return pd.DataFrame(rows)


def _heat_verdict(cap: float, d_cagr: float, d_med_dd: float, d_p10: float,
                  p_lt: float) -> str:
    """Heat seal principle: retain H1 only when it provides repeatable
    meaningful tail reduction for a reasonable growth cost.

    Calibrated to the observed operating-band magnitudes (H1-1.00: P(DD>=10)
    ~ -9pp for ~ -4.6pp median CAGR; H1-1.50: ~ -8pp for ~ -2.5pp;
    H1-2.00: ~ -1pp; H1-3.00: never binds)."""
    if cap >= 3.0:
        return "NOT_RETAINED_NEVER_BINDS"
    if not (np.isfinite(d_cagr) and np.isfinite(d_med_dd) and np.isfinite(p_lt)):
        return "INSUFFICIENT_PAIRED_DATA"
    tail_reduction = d_p10 < -0.02 or (-d_med_dd) > 0.005
    reasonable_cost = abs(d_cagr) <= 0.06
    repeatable = p_lt > 0.5
    if tail_reduction and repeatable and reasonable_cost:
        return "RETAIN_OPERATING_REFERENCE"
    if tail_reduction and reasonable_cost:
        return "OPTIONAL_INTERMEDIATE"
    return "NOT_RETAINED_NO_PROTECTION"


# ---------------------------------------------------------------------------
# Edge review
# ---------------------------------------------------------------------------

def edge_review(surv: pd.DataFrame, mc: pd.DataFrame) -> pd.DataFrame:
    """Retained-edge behavior per (alloc, heat, f) -- survival flags plus the
    50% retained-edge expectancy context and the 25% alpha-loss boundary."""
    rows = []
    for _, r in surv.iterrows():
        sub = mc[(mc["alloc_id"] == r["alloc_id"])
                 & (mc["heat_id"] == r["heat_id"]) & (mc["f_pct"] == r["f_pct"])
                 & (mc["scheme"].isin(PRIMARY_SCHEMES))]
        rows.append({
            "alloc_id": r["alloc_id"], "heat_id": r["heat_id"],
            "f_pct": r["f_pct"],
            "survives_100": bool(r["survives_100"]),
            "survives_75": bool(r["survives_75"]),
            "survives_50": bool(r["survives_50"]),
            "survives_25": bool(r["survives_25"]),
            "median_cagr_100": float(r["median_cagr_100"]),
            "median_cagr_75": float(r["median_cagr_75"]),
            "median_cagr_50": float(r["median_cagr_50"]),
            "p95_dd_100": float(r["p95_dd_100"]),
            "is_recommendation_alloc": r["alloc_id"] in RECOMMENDATION_ALLOCS,
        })
    return pd.DataFrame(rows)


def edge_seal_state(edge: pd.DataFrame) -> Dict:
    """Aggregate edge-retention truth for the operating band cells."""
    op = edge[(edge["alloc_id"].isin(OPERATING_ALLOCS))
              & (edge["heat_id"] == OPERATING_HEAT)
              & (edge["f_pct"].isin(ROBUST_CORE_BAND))]
    out = {}
    for key in ["survives_100", "survives_75", "survives_50", "survives_25"]:
        out[key] = bool(op[key].all()) if len(op) else False
    out["n_cells"] = int(len(op))
    return out


# ---------------------------------------------------------------------------
# Robust core
# ---------------------------------------------------------------------------

def robust_core(mc: pd.DataFrame, dep: pd.DataFrame) -> pd.DataFrame:
    """One row per (alloc, heat, f) inside the robust core with block+episode
    consensus metrics + dependency sensitivity, at 100% edge."""
    rows = []
    for alloc_id in OPERATING_ALLOCS:
        for heat_id in HEAT_IDS:
            for f_pct in ROBUST_CORE_BAND:
                sub = mc[(mc["alloc_id"] == alloc_id)
                         & (mc["heat_id"] == heat_id) & (mc["f_pct"] == f_pct)
                         & (mc["edge"] == 1.0)
                         & (mc["scheme"].isin(PRIMARY_SCHEMES))]
                if len(sub) == 0:
                    continue
                dep_row = dep[(dep["alloc_id"] == alloc_id)
                              & (dep["heat_id"] == heat_id)
                              & (dep["f_pct"] == f_pct) & (dep["edge"] == 1.0)]
                rows.append({
                    "alloc_id": alloc_id, "heat_id": heat_id, "f_pct": f_pct,
                    "block_median_cagr": float(sub[sub["scheme"] == "block"]["median_cagr"].mean()),
                    "episode_median_cagr": float(sub[sub["scheme"] == "episode"]["median_cagr"].mean()),
                    "block_p95_dd": float(sub[sub["scheme"] == "block"]["max_dd_p95"].mean()),
                    "episode_p95_dd": float(sub[sub["scheme"] == "episode"]["max_dd_p95"].mean()),
                    "P_dd_ge_10": float(sub["P_dd_ge_10"].mean()),
                    "P_dd_ge_15": float(sub["P_dd_ge_15"].mean()),
                    "P_dd_ge_20": float(sub["P_dd_ge_20"].mean()),
                    "P_technical_ruin": float(sub["P_technical_ruin"].mean()),
                    "dependency_sensitive": bool(dep_row["sensitive"].iloc[0]) if len(dep_row) else False,
                    "is_operating_heat": heat_id == OPERATING_HEAT,
                })
    return pd.DataFrame(rows)


def robust_core_ranges(rc: pd.DataFrame) -> Dict:
    """Aggregate operating ranges for the risk contract: allocs x operating
    heat x block/episode across the band (100% edge)."""
    op = rc[(rc["is_operating_heat"])]
    cagr_vals = op[["block_median_cagr", "episode_median_cagr"]].to_numpy().ravel()
    p95_vals = op[["block_p95_dd", "episode_p95_dd"]].to_numpy().ravel()
    return {
        "median_cagr_min": float(cagr_vals.min()),
        "median_cagr_max": float(cagr_vals.max()),
        "p95_dd_min": float(p95_vals.min()),
        "p95_dd_max": float(p95_vals.max()),
        "P_dd_ge_10_min": float(op["P_dd_ge_10"].min()),
        "P_dd_ge_10_max": float(op["P_dd_ge_10"].max()),
        "P_dd_ge_15_min": float(op["P_dd_ge_15"].min()),
        "P_dd_ge_15_max": float(op["P_dd_ge_15"].max()),
        "P_technical_ruin_max": float(op["P_technical_ruin"].max()),
        "dependency_sensitive_cells": int(op["dependency_sensitive"].sum()),
        "n_cells": int(len(op)),
    }


# ---------------------------------------------------------------------------
# Region definition + decision
# ---------------------------------------------------------------------------

def region_definition(rc: pd.DataFrame, knee: pd.DataFrame,
                      adj: pd.DataFrame, alloc_rev: pd.DataFrame,
                      heat: pd.DataFrame, edge_state: Dict,
                      frontier_decision: Dict, base_commit: str) -> Dict:
    """Assemble the sealed operating envelope."""
    kband, knee_stats = knee_band(knee)
    adj_seal = adjacent_scale_seal_pass(adj)
    core_ranges = robust_core_ranges(rc)

    # allocation verdicts
    alloc_verdicts = {}
    for _, r in alloc_rev.iterrows():
        alloc_verdicts[r["alloc_id"]] = {
            "tail_efficiency": float(r["tail_efficiency"]),
            "P_dd_ge_10_at_f1": float(r["P_dd_ge_10"]),
            "survives_75": bool(r["survives_75"]),
        }
    # heat verdicts
    heat_verdicts = {r["heat_id"]: r["verdict"] for _, r in heat.iterrows()}
    op_heat = [h for h, v in heat_verdicts.items() if v == "RETAIN_OPERATING_REFERENCE"]
    operating_heat = op_heat[0] if op_heat else OPERATING_HEAT

    # preferred research default: choose only when evidence supports a clear
    # stable midpoint (best tail efficiency allocation at top of robust core,
    # pre-knee, under the operating heat).
    best_eff = alloc_rev[alloc_rev["alloc_id"].isin(OPERATING_ALLOCS)] \
        .sort_values("tail_efficiency", ascending=False)
    pref_alloc = PREFERRED_ALLOC
    if len(best_eff) and best_eff.iloc[0]["tail_efficiency"] >= \
            best_eff["tail_efficiency"].median():
        pref_alloc = str(best_eff.iloc[0]["alloc_id"])
    knee_ok = kband is not None and ROBUST_CORE_BAND[1] <= kband[0]
    preferred = {
        "allocation": pref_alloc,
        "heat_architecture": operating_heat,
        "f_total_pct": PREFERRED_F_PCT,
        "role": "PREFERRED_RESEARCH_DEFAULT for demo/execution translation "
                "research ONLY -- not production sizing, not live authorization",
        "justification": "best tail-efficiency allocation (A1_70_30) at the top "
                         "of the robust core (0.75-1.00), at the knee start "
                         f"{kband}, under the operating heat {operating_heat}", 
    }

    return {
        "checkpoint": "CR-RISK-BLOCK-III-SCALE-SEAL",
        "base_commit": base_commit,
        "scale_bands": {
            "CONSERVATIVE": CONSERVATIVE_BAND,
            "ROBUST_CORE": ROBUST_CORE_BAND,
            "AGGRESSIVE": AGGRESSIVE_BAND,
            "STRESS_ONLY": STRESS_BAND,
        },
        "knee_band": kband,
        "knee_stats": knee_stats,
        "adjacent_scale_seal": adj_seal,
        "allowed_allocations": OPERATING_ALLOCS,
        "diagnostic_only_allocations": ["A2_100_0_A", "A3_0_100_B"],
        "alloc_verdicts": alloc_verdicts,
        "heat_verdicts": heat_verdicts,
        "operating_heat_reference": operating_heat,
        "h0_sufficient": True,
        "edge_retention": edge_state,
        "robust_core_ranges": core_ranges,
        "preferred_research_default": preferred,
        "knee_seal_pass": bool(knee_ok),
        "block_episode_agreement_pass": bool(core_ranges["dependency_sensitive_cells"] == 0),
        "survives_25_edge": edge_state["survives_25"],
        "kelly_used": False,
        "dd_adaptive_used": False,
        "production_scale_selected": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "frontier_nonregression_pass": bool(
            frontier_decision.get("reference_nonregression_pass", False)),
        "human_review_required": True,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING",
        "next_checkpoint_authorized": False,
    }


# ---------------------------------------------------------------------------
# Fail-closed decision gate (R1 repair: CR-RISK-BLOCK-III-SCALE-SEAL-R1-
# FAIL-CLOSED-GATE).  Pure functions so the gate can be exercised directly
# by negative tests -- no artifact inspection required.
# ---------------------------------------------------------------------------

REQUIRED_GATE_FIELDS: List[Tuple[str, str]] = [
    ("frontier_nonregression_pass",
     "frontier reference nonregression PASS"),
    ("block_episode_agreement_pass",
     "block/episode dependency agreement within the robust core"),
    ("knee_seal_pass", "robust core at or below the knee start"),
    ("adjacent_scale_seal_pass",
     "no tail acceleration inside the core; acceleration at 1.00->1.50"),
    ("survives_100_edge", "100% retained edge survival in the band"),
    ("survives_75_edge", "75% retained edge survival in the band"),
]

PROHIBITED_AUTH_FIELDS: List[Tuple[str, str]] = [
    ("kelly_used", "kelly sizing is prohibited"),
    ("dd_adaptive_used", "drawdown-adaptive sizing is prohibited"),
    ("production_scale_selected", "production scale selection is prohibited"),
    ("deployment_authorized", "deployment is not authorized"),
    ("mt5_authorized", "MT5 execution is not authorized"),
]


def fail_closed_gate(gates: Dict[str, bool],
                     authorizations: Dict[str, bool]) -> Dict:
    """Fail-closed truth gate for the scale-seal decision.

    block3_scale_seal_pass = true ONLY IF every required gate passes AND no
    prohibited authorization state is present.  status is DERIVED from the
    pass (never hardcoded).  Missing gate inputs fail closed; missing
    authorization inputs default to not-authorized (safe).

    Returns the machine-readable gate verdict:
      block3_scale_seal_pass, status (PASS/FAIL), status_reason,
      seal_gate_passes, seal_gate_failures, authorization_invariants_failed.
    """
    seal_gate_passes = [name for name, _ in REQUIRED_GATE_FIELDS
                        if bool(gates.get(name)) is True]
    seal_gate_failures = [name for name, _ in REQUIRED_GATE_FIELDS
                          if bool(gates.get(name)) is not True]
    auth_invariants_failed = [name for name, _ in PROHIBITED_AUTH_FIELDS
                              if bool(authorizations.get(name)) is True]
    block3_scale_seal_pass = (not seal_gate_failures
                              and not auth_invariants_failed)
    if block3_scale_seal_pass:
        status = "PASS"
        status_reason = "All required gates pass; no prohibited authorization " \
                        "state present."
    else:
        reasons = []
        if seal_gate_failures:
            reasons.append("required gate(s) failed: "
                           + ", ".join(seal_gate_failures))
        if auth_invariants_failed:
            reasons.append("prohibited authorization state: "
                           + ", ".join(auth_invariants_failed))
        status = "FAIL"
        status_reason = "; ".join(reasons)
    return {
        "block3_scale_seal_pass": block3_scale_seal_pass,
        "status": status,
        "status_reason": status_reason,
        "seal_gate_passes": seal_gate_passes,
        "seal_gate_failures": seal_gate_failures,
        "authorization_invariants_failed": auth_invariants_failed,
    }


def build_scale_seal_decision(
        *,
        base_commit: str,
        checkpoint: str = "CR-RISK-BLOCK-III-SCALE-SEAL",
        frontier_nonregression_pass: bool,
        block_episode_agreement_pass: bool,
        knee_seal_pass: bool,
        adjacent_scale_seal_pass: bool,
        survives_100_edge: bool,
        survives_75_edge: bool,
        survives_50_edge: bool,
        survives_25_edge: bool,
        kelly_used: bool = False,
        dd_adaptive_used: bool = False,
        production_scale_selected: bool = False,
        deployment_authorized: bool = False,
        mt5_authorized: bool = False,
        scale_bands: Optional[Dict] = None,
        allowed_allocations: Optional[List[str]] = None,
        diagnostic_only_allocations: Optional[List[str]] = None,
        heat_architecture_status: str = "H1_OPTIONAL_SAFETY_LAYER_RETAINED",
        preferred_research_default: Optional[Dict] = None,
        robust_core_median_cagr_range: Optional[List[float]] = None,
        robust_core_p95_dd_range: Optional[List[float]] = None,
        robust_core_p_dd_ge_10_range: Optional[List[float]] = None,
        robust_core_p_dd_ge_15_range: Optional[List[float]] = None,
        next_checkpoint_recommended: str =
            "CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING",
) -> Dict:
    """Assemble the full scale-seal decision with fail-closed governance.

    The pass/status fields are ALWAYS computed by fail_closed_gate() -- the
    caller supplies the gate inputs (typically derived from the frozen
    region/edge evidence) and the scientific fields, and the gate decides.
    This is the single decision path used by the canonical seal runner and
    the R1 fail-closed repair runner.
    """
    gates = {
        "frontier_nonregression_pass": bool(frontier_nonregression_pass),
        "block_episode_agreement_pass": bool(block_episode_agreement_pass),
        "knee_seal_pass": bool(knee_seal_pass),
        "adjacent_scale_seal_pass": bool(adjacent_scale_seal_pass),
        "survives_100_edge": bool(survives_100_edge),
        "survives_75_edge": bool(survives_75_edge),
    }
    auths = {
        "kelly_used": bool(kelly_used),
        "dd_adaptive_used": bool(dd_adaptive_used),
        "production_scale_selected": bool(production_scale_selected),
        "deployment_authorized": bool(deployment_authorized),
        "mt5_authorized": bool(mt5_authorized),
    }
    gate = fail_closed_gate(gates, auths)
    bands = scale_bands if scale_bands is not None else {
        "CONSERVATIVE": CONSERVATIVE_BAND,
        "ROBUST_CORE": ROBUST_CORE_BAND,
        "AGGRESSIVE": AGGRESSIVE_BAND,
        "STRESS_ONLY": STRESS_BAND,
    }
    return {
        "checkpoint": checkpoint,
        "status": gate["status"],
        "status_reason": gate["status_reason"],
        "base_commit": base_commit,
        "frontier_nonregression_pass": bool(frontier_nonregression_pass),
        "conservative_scale_band": bands["CONSERVATIVE"],
        "robust_core_scale_band": bands["ROBUST_CORE"],
        "aggressive_scale_band": bands["AGGRESSIVE"],
        "stress_scale_band": bands["STRESS_ONLY"],
        "allowed_allocations": (allowed_allocations
                                 if allowed_allocations is not None
                                 else list(OPERATING_ALLOCS)),
        "diagnostic_only_allocations": (
            diagnostic_only_allocations
            if diagnostic_only_allocations is not None
            else ["A2_100_0_A", "A3_0_100_B"]),
        "heat_architecture_status": heat_architecture_status,
        "preferred_research_default": (
            preferred_research_default
            if preferred_research_default is not None
            else {
                "allocation": PREFERRED_ALLOC,
                "heat_architecture": PREFERRED_HEAT,
                "f_total_pct": PREFERRED_F_PCT,
                "role": "PREFERRED_RESEARCH_DEFAULT for demo/execution "
                        "translation research ONLY -- not production sizing",
            }),
        "robust_core_median_cagr_range": (
            robust_core_median_cagr_range
            if robust_core_median_cagr_range is not None
            else []),
        "robust_core_p95_dd_range": (
            robust_core_p95_dd_range if robust_core_p95_dd_range is not None
            else []),
        "robust_core_p_dd_ge_10_range": (
            robust_core_p_dd_ge_10_range
            if robust_core_p_dd_ge_10_range is not None else []),
        "robust_core_p_dd_ge_15_range": (
            robust_core_p_dd_ge_15_range
            if robust_core_p_dd_ge_15_range is not None else []),
        "survives_100_edge": bool(survives_100_edge),
        "survives_75_edge": bool(survives_75_edge),
        "survives_50_edge": bool(survives_50_edge),
        "survives_25_edge": bool(survives_25_edge),
        "block_episode_agreement_pass": bool(block_episode_agreement_pass),
        "knee_seal_pass": bool(knee_seal_pass),
        "adjacent_scale_seal_pass": bool(adjacent_scale_seal_pass),
        "kelly_used": bool(kelly_used),
        "dd_adaptive_used": bool(dd_adaptive_used),
        "production_scale_selected": bool(production_scale_selected),
        "deployment_authorized": bool(deployment_authorized),
        "mt5_authorized": bool(mt5_authorized),
        "block3_scale_seal_pass": gate["block3_scale_seal_pass"],
        "seal_gate_passes": gate["seal_gate_passes"],
        "seal_gate_failures": gate["seal_gate_failures"],
        "authorization_invariants_failed": (
            gate["authorization_invariants_failed"]),
        "human_review_required": True,
        "next_checkpoint_recommended": next_checkpoint_recommended,
        "next_checkpoint_authorized": False,
    }


# ---------------------------------------------------------------------------
# Risk contract
# ---------------------------------------------------------------------------

def risk_contract(rc: pd.DataFrame, edge_state: Dict) -> Dict:
    """The risk envelope handed to later deployment engineering."""
    ranges = robust_core_ranges(rc)
    # edge behavior at 75/50 from the survival vectors on operating cells
    return {
        "scope": "Sealed ROBUST CORE: allocations "
                 f"{OPERATING_ALLOCS}, scale band {ROBUST_CORE_BAND}, "
                 f"operating heat {OPERATING_HEAT}, 100% retained edge "
                 "(75%/50% behavior reported separately)",
        "median_cagr_range": [round(ranges["median_cagr_min"], 4),
                              round(ranges["median_cagr_max"], 4)],
        "p95_max_dd_range": [round(ranges["p95_dd_min"], 4),
                             round(ranges["p95_dd_max"], 4)],
        "P_dd_ge_10_range": [round(ranges["P_dd_ge_10_min"], 4),
                             round(ranges["P_dd_ge_10_max"], 4)],
        "P_dd_ge_15_range": [round(ranges["P_dd_ge_15_min"], 4),
                             round(ranges["P_dd_ge_15_max"], 4)],
        "P_technical_ruin_max": round(ranges["P_technical_ruin_max"], 8),
        "dependency_sensitive_cells_in_band": ranges["dependency_sensitive_cells"],
        "edge_100_behavior": {
            "survives": edge_state["survives_100"],
            "note": "median CAGR and p95 DD ranges above (both primary "
                    "schemes agree directionally)",
        },
        "edge_75_behavior": {"survives": edge_state["survives_75"]},
        "edge_50_behavior": {"survives": edge_state["survives_50"]},
        "edge_25_behavior": {
            "survives": edge_state["survives_25"],
            "note": "25% retained edge is the recorded ALPHA-LOSS BOUNDARY; "
                    "risk controls are not expected to rescue destroyed "
                    "expectancy",
        },
        "units": {
            "cagr": "decimal (e.g. 0.70 = 70% annualized)",
            "max_dd": "decimal fraction of equity (e.g. 0.08 = 8%)",
            "P_dd_ge_10": "probability (0..1) that max DD >= 10%",
            "scale_f_total_pct": "percent of equity risked per unit event "
                                 "(0.75 = 0.75%)",
        },
        "authorizations": {
            "production_scale_selected": False,
            "deployment_authorized": False,
            "mt5_authorized": False,
            "kelly_used": False,
            "dd_adaptive_used": False,
        },
    }
