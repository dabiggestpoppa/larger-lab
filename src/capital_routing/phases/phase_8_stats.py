"""
Phase 8 - statistical discipline (brief sections 22-23).

Bootstrap confidence intervals (fixed seed, event-level resampling), Welch
t-tests, Benjamini-Hochberg FDR, and chronological subperiod assignment.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

BOOTSTRAP_SEED = 20260815
BOOTSTRAP_ITERS = 1000
CI_ALPHA = 0.10  # two-sided -> 90% CI

SUBPERIODS: List[Tuple[str, str, str]] = [
    ("2023H2", "2023-07-01", "2023-12-31"),
    ("2024H1", "2024-01-01", "2024-06-30"),
    ("2024H2", "2024-07-01", "2024-12-31"),
    ("2025H1", "2025-01-01", "2025-06-30"),
]

# Chronological Phase 8 splits (frozen BEFORE discovery; brief section 23).
SPLIT = {
    "discovery": {"start": "2023-07-01", "end": "2024-12-31"},
    "confirmation": {"start": "2025-01-01", "end": "2025-06-30"},
    "oos": {"start": "2025-07-01", "end": "2026-05-31"},
    "oos_label": "RELATIONSHIP_CONFIRMED_OOS",
}

MIN_SUPPORT = 30  # research-eligible; below = exploratory only


def bootstrap_ci(values: np.ndarray, stat: str = "mean",
                 seed: int = BOOTSTRAP_SEED, iters: int = BOOTSTRAP_ITERS,
                 alpha: float = CI_ALPHA) -> Dict[str, float]:
    """Bootstrap CI (event-level resampling, fixed seed)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 10:
        return {"n": int(len(v)), "mean": np.nan, "median": np.nan,
                "ci_low": np.nan, "ci_high": np.nan, "se": np.nan}
    point = float(np.mean(v)) if stat == "mean" else float(np.median(v))
    rng = np.random.default_rng(seed)
    n = len(v)
    boots = np.empty(iters)
    for i in range(iters):
        s = v[rng.integers(0, n, size=n)]
        boots[i] = np.mean(s) if stat == "mean" else np.median(s)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "n": int(n), "mean": point, "median": float(np.median(v)),
        "ci_low": float(lo), "ci_high": float(hi),
        "se": float(boots.std(ddof=1)),
    }


def permutation_p(a: np.ndarray, b: np.ndarray,
                   seed: int = BOOTSTRAP_SEED, iters: int = 2000) -> float:
    """Two-sided permutation p-value for the difference in means.

    Dependency-free (no scipy); deterministic with a fixed seed. With N >= 30
    per group this is a robust alternative to the Welch t-test for heavy-tailed
    trade returns.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 5 or len(b) < 5:
        return np.nan
    obs = a.mean() - b.mean()
    pooled = np.concatenate([a, b])
    na = len(a)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(iters):
        perm = rng.permutation(pooled)
        d = perm[:na].mean() - perm[na:].mean()
        if abs(d) >= abs(obs):
            count += 1
    return (count + 1) / (iters + 1)


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted q-values (1-indexed within family)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    if n == 0:
        return np.array([])
    order = np.argsort(p)
    ranks = np.empty(n)
    ranks[order] = np.arange(1, n + 1)
    q = p * n / ranks
    # enforce monotonicity from the largest p down
    q_sorted = q[order]
    for i in range(n - 2, -1, -1):
        q_sorted[i] = min(q_sorted[i], q_sorted[i + 1])
    q[order] = q_sorted
    return np.clip(q, 0.0, 1.0)


def assign_split(ts: pd.Timestamp) -> str:
    ts = pd.Timestamp(ts)
    for name in ("discovery", "confirmation", "oos"):
        w = SPLIT[name]
        if pd.Timestamp(w["start"], tz="UTC") <= ts < pd.Timestamp(w["end"], tz="UTC"):
            return name
    return "outside"


def assign_subperiod(ts: pd.Timestamp) -> str:
    ts = pd.Timestamp(ts)
    for name, start, end in SUBPERIODS:
        if pd.Timestamp(start, tz="UTC") <= ts <= pd.Timestamp(end + " 23:59:59", tz="UTC"):
            return name
    return "OTHER"
