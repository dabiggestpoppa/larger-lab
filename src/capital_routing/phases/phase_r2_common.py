"""
CR-RISK-BLOCK1 R2 — Loss Anatomy (shared primitives).

Common constants, net-PnL path construction, first-passage times, and bootstrap
helpers used across the R2 studies.

Path construction note: R2 uses the frozen H1 panel ONLY (the sealed baseline's
price source). The committed M5 feed was tested against the panel and REJECTED:
closes differ by median -0.7 bps but p95 |diff| 22 bps / max 42 bps (different
feed). Mixing it would corrupt MAE/failure-speed measurements. Consequence:
the recovery-surface age grid is hourly (0-1h .. 5-6h); the brief's 0-30m /
30-60m sub-bins are structurally unavailable at research grade and are not
fabricated.

Net-PnL path: net_bps(h) = mark_bps(h) - cost_pnl_bps, where mark_bps is the
directional market PnL of the vol-normalized position from the frozen panel and
cost_pnl_bps the modeled all-in cost. The final bar therefore equals the sealed
net PnL exactly: net_bps(5) == pnl_bps (unit-tested).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r1_ledger import risk_unit_bps

# ---------------------------------------------------------------------------
# Bins / thresholds (documented, no threshold rescue)
# ---------------------------------------------------------------------------

# Depth bins on the ADVERSITY side (depth = -MAE in R). pd.cut with right=False
# -> intervals [a, b). Boundary convention: depth 0.25 belongs to the deeper bin
# "-0.25 to -0.50R" (upper-inclusive on the R label). Documented, not tuned.
MAE_DEPTH_BINS: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, np.inf]
MAE_BIN_LABELS: List[str] = [
    "0 to -0.25R", "-0.25 to -0.50R", "-0.50 to -0.75R", "-0.75 to -1.00R",
    "-1.00 to -1.50R", "-1.50 to -2.00R", "-2.00 to -2.50R", "worse than -2.50R",
]

# Age (hours since economic entry bar) bins. Hourly resolution (see module doc).
AGE_BIN_EDGES: List[float] = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
AGE_BIN_LABELS: List[str] = ["0-1h", "1-2h", "2-3h", "3-4h", "4-5h", "5-6h"]

# First-passage thresholds (R, adverse direction)
FAILURE_THRESHOLDS_R: List[float] = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0]

MIN_SUPPORT = 30  # cells with N < MIN_SUPPORT are labelled exploratory
BOOTSTRAP_SEED = 20260815
BOOTSTRAP_ITERS = 500
BLOCK_BOOTSTRAP_BLOCK = 25

# Temporal splits (existing honest partitions; RELATIONSHIP_CONFIRMED_OOS is
# NOT relabelled as untouched)
SPLITS = ["inner_sel", "inner_val", "RELATIONSHIP_CONFIRMED_OOS"]


# ---------------------------------------------------------------------------
# Path construction
# ---------------------------------------------------------------------------

def build_net_paths(ledger: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """Net-PnL path per event from the frozen panel marks + modeled costs.

    Returns long frame: event_id, h_since_entry, age_h, mark_bps (gross),
    mkt_bps (directional market move, pre-position), net_bps, net_R,
    running min/max (net), win (final net > 0).
    """
    ld = ledger[["event_id", "cost_pnl_bps", "pos", "risk_unit_bps", "pnl_bps"]]
    p = marks.merge(ld, on="event_id", how="inner")
    p = p.sort_values(["event_id", "h_since_entry"]).reset_index(drop=True)
    p["age_h"] = p["h_since_entry"].astype(float)
    p["mkt_bps"] = p["mark_bps"] / p["pos"]
    p["net_bps"] = p["mark_bps"] - p["cost_pnl_bps"]
    p["net_R"] = p["net_bps"] / p["risk_unit_bps"]
    p["cum_min_R"] = p.groupby("event_id")["net_R"].cummin()
    p["cum_max_R"] = p.groupby("event_id")["net_R"].cummax()
    p["final_net_R"] = p.groupby("event_id")["net_R"].transform("last")
    p["win"] = p["pnl_bps"] > 0.0
    # depth of the running-min state (adversity), binned
    p["mae_depth_R"] = (-p["cum_min_R"]).clip(lower=0.0)
    return p


def mae_bin_of(depth: np.ndarray) -> np.ndarray:
    """Map adversity depth (>=0, in R) to the documented MAE bin label."""
    return pd.cut(pd.Series(depth), bins=MAE_DEPTH_BINS, labels=MAE_BIN_LABELS,
                  right=False, include_lowest=True).astype(str)


def age_bin_of(age_h: np.ndarray) -> np.ndarray:
    return pd.cut(pd.Series(age_h), bins=AGE_BIN_EDGES, labels=AGE_BIN_LABELS,
                  right=False, include_lowest=True).astype(str)


def per_event_paths(paths: pd.DataFrame) -> Dict[str, np.ndarray]:
    """event_id -> sorted net_R path array."""
    out = {}
    for eid, gr in paths.groupby("event_id"):
        out[eid] = gr.sort_values("h_since_entry")["net_R"].to_numpy(dtype=float)
    return out


def first_passage(net_R_path: np.ndarray, threshold_R: float) -> Optional[float]:
    """Age (hours since entry bar) at which net_R <= -threshold_R, else NaN."""
    hit = np.where(net_R_path <= -threshold_R)[0]
    if len(hit) == 0:
        return np.nan
    return float(hit[0])


def time_to_worst_mae(net_R_path: np.ndarray) -> float:
    """Age at which the running minimum is achieved (first occurrence)."""
    if len(net_R_path) == 0:
        return np.nan
    return float(np.argmin(net_R_path))


def max_after(net_R_path: np.ndarray, start_idx: int) -> float:
    """Max net_R after a given age index (inclusive of the state bar)."""
    seg = net_R_path[start_idx:]
    return float(np.max(seg)) if len(seg) else np.nan


# ---------------------------------------------------------------------------
# Bootstrap helpers (deterministic, fixed seed)
# ---------------------------------------------------------------------------

def percentile_ci(values: np.ndarray, stat: str = "mean",
                  seed: int = BOOTSTRAP_SEED, iters: int = BOOTSTRAP_ITERS,
                  alpha: float = 0.05) -> Dict[str, float]:
    """Percentile bootstrap CI (event-level resampling, fixed seed)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"n": 0, "mean": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                "se": np.nan}
    rng = np.random.default_rng(seed)
    n = len(v)
    boots = np.empty(iters)
    for i in range(iters):
        s = v[rng.integers(0, n, size=n)]
        boots[i] = np.mean(s) if stat == "mean" else float((s > 0).mean())
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"n": int(n), "mean": float(np.mean(v)),
            "ci_low": float(lo), "ci_high": float(hi),
            "se": float(np.std(boots, ddof=1))}


def block_bootstrap_max_streak(pnl: np.ndarray, block: int = BLOCK_BOOTSTRAP_BLOCK,
                               seed: int = BOOTSTRAP_SEED,
                               iters: int = BOOTSTRAP_ITERS) -> Dict[str, float]:
    """Block bootstrap on the chronological losing-trade streak statistic.

    Resamples contiguous blocks (block size = `block` trades) with replacement,
    recomputes the max consecutive-loss streak, and returns its distribution.
    Preserves within-block path dependence; fixed seed.
    """
    pnl = np.asarray(pnl, dtype=float)
    n = len(pnl)
    if n == 0:
        return {}
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    streaks = np.empty(iters)
    for i in range(iters):
        starts = rng.integers(0, n, size=n_blocks)
        seq = np.concatenate([pnl[s:s + block] for s in starts])[:n]
        streaks[i] = _max_loss_streak(seq)
    return {
        "n": int(n), "block_size": block,
        "observed_max_streak": float(_max_loss_streak(pnl)),
        "boot_median": float(np.median(streaks)),
        "boot_p90": float(np.percentile(streaks, 90)),
        "boot_p95": float(np.percentile(streaks, 95)),
        "boot_max": float(streaks.max()),
    }


def _max_loss_streak(pnl: np.ndarray) -> int:
    best = cur = 0
    for v in pnl:
        if v < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best
