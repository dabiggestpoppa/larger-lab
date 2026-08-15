"""
Phase 6 - Statistical machinery: bootstrap confidence intervals, Benjamini-
Hochberg FDR, effect sizes, subperiod and overlapping-event helpers.
CR-P6-FORWARD-ROUTING-STUDY-01

All bootstrap procedures use event-level resampling with a fixed seed so
results are fully deterministic.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

BOOTSTRAP_SEED = 42
BOOTSTRAP_N = 200
ALPHA = 0.05


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals (event-level resampling, fixed seed)
# ---------------------------------------------------------------------------


def bootstrap_ci(sample: np.ndarray, stat: str = "mean", n_boot: int = BOOTSTRAP_N,
                 seed: int = BOOTSTRAP_SEED) -> Dict:
    """
    Bootstrap estimate + 95% CI + standard error for a statistic.

    stat: "mean" | "median" | "prob_true" (sample is 0/1).
    Resampling is at the observation (event) level. Deterministic for a seed.
    """
    sample = np.asarray(sample, dtype=float)
    sample = sample[np.isfinite(sample)]
    n = len(sample)
    if n == 0:
        return {"n": 0, "estimate": np.nan, "ci_low": np.nan,
                "ci_high": np.nan, "se": np.nan}

    rng = np.random.default_rng(seed)

    def _est(x):
        if stat == "mean":
            return float(np.mean(x))
        if stat == "median":
            return float(np.median(x))
        if stat == "prob_true":
            return float(np.mean(x > 0.5))
        raise ValueError(f"unknown stat {stat}")

    est = _est(sample)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        draws[b] = _est(sample[idx])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    se = float(draws.std(ddof=1))
    return {
        "n": int(n),
        "estimate": float(est),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "se": se,
    }


def bootstrap_destination_probability(is_dest: np.ndarray, n_boot: int = BOOTSTRAP_N,
                                      seed: int = BOOTSTRAP_SEED) -> Dict:
    """Bootstrap CI for a destination probability from a 0/1 mask."""
    return bootstrap_ci(is_dest, stat="mean", n_boot=n_boot, seed=seed)


# ---------------------------------------------------------------------------
# Multiple-testing control (Benjamini-Hochberg FDR)
# ---------------------------------------------------------------------------


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """
    Benjamini-Hochberg adjusted q-values. NaN p-values stay NaN.
    Deterministic; largest p that keeps p <= (i/m)*alpha marks the threshold.
    """
    pvals = np.asarray(pvals, dtype=float)
    q = np.full_like(pvals, np.nan)
    finite = np.isfinite(pvals)
    p = pvals[finite]
    m = len(p)
    if m == 0:
        return q
    order = np.argsort(p, kind="stable")
    ranked = p[order]
    # BH step-up
    q_ranked = np.full(m, np.nan)
    running = 1.0
    for i in range(m - 1, -1, -1):
        val = ranked[i] * m / (i + 1)
        running = min(running, val)
        q_ranked[i] = min(running, 1.0)
    # Place q-values back at the original positions (inverse permutation).
    inverse = np.empty(m, dtype=int)
    inverse[order] = np.arange(m)
    q[finite] = q_ranked[inverse]
    return q


# ---------------------------------------------------------------------------
# Effect sizes and summary stats
# ---------------------------------------------------------------------------


def cohen_d_one(sample: np.ndarray) -> float:
    """Standardised mean effect for a one-sample test (mean / sample sd)."""
    sample = np.asarray(sample, dtype=float)
    sample = sample[np.isfinite(sample)]
    if len(sample) < 2:
        return np.nan
    sd = sample.std(ddof=1)
    if sd <= 0:
        return np.nan
    return float(sample.mean() / sd)


def describe(sample: np.ndarray) -> Dict:
    """Effect-size-first summary: N, mean, median, sd, se, CI, effect."""
    s = np.asarray(sample, dtype=float)
    s = s[np.isfinite(s)]
    n = len(s)
    if n == 0:
        return {"n": 0, "mean": np.nan, "median": np.nan, "std": np.nan,
                "se": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                "effect": np.nan}
    mean = float(s.mean())
    std = float(s.std(ddof=1))
    se = std / np.sqrt(n) if n > 1 else np.nan
    boot = bootstrap_ci(s, stat="mean")
    return {
        "n": n,
        "mean": mean,
        "median": float(np.median(s)),
        "std": std,
        "se": se,
        "ci_low": boot["ci_low"],
        "ci_high": boot["ci_high"],
        "effect": cohen_d_one(s),
    }


def rank_corr(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman-style rank correlation (Pearson on ranks). NaN pairs dropped."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return np.nan
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if rx.std(ddof=1) == 0 or ry.std(ddof=1) == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])


def one_sample_t(sample: np.ndarray) -> Dict:
    """Approximate two-sided one-sample t-test vs 0 (normal approximation)."""
    s = np.asarray(sample, dtype=float)
    s = s[np.isfinite(s)]
    n = len(s)
    if n < 2:
        return {"n": n, "t": np.nan, "p": np.nan}
    mean = float(s.mean())
    sd = float(s.std(ddof=1))
    if sd <= 0 or np.isnan(sd):
        return {"n": n, "t": np.nan, "p": np.nan}
    se = sd / np.sqrt(n)
    t = mean / se
    # normal approximation two-sided p
    p = 2.0 * (1.0 - _norm_cdf(abs(t)))
    return {"n": n, "t": float(t), "p": float(p)}


def _norm_cdf(x: float) -> float:
    """Standard normal CDF (Abramowitz-Stegun approximation)."""
    if x < 0:
        return 1.0 - _norm_cdf(-x)
    t = 1.0 / (1.0 + 0.2316419 * x)
    d = 0.3989422804014327 * np.exp(-0.5 * x * x)
    p = d * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 +
        t * (-1.821255978 + t * 1.330274429))))
    return float(1.0 - p)


# ---------------------------------------------------------------------------
# Overlapping-event dependence
# ---------------------------------------------------------------------------


def non_overlapping_mask(events: pd.DataFrame, cooldown_h: int) -> np.ndarray:
    """
    Deterministic mask keeping one observation per cooldown block.

    Events are sorted by event_start; an event is kept iff it starts at least
    `cooldown_h` hours after the last kept event. This is a sensitivity tool:
    ALL cooldowns are reported, none is chosen because it performs best.
    """
    ts = pd.to_datetime(events["event_start"], utc=True).sort_values()
    keep = np.zeros(len(events), dtype=bool)
    order = ts.index
    last_kept_ns = None
    cooldown_ns = int(cooldown_h * 3600 * 10**9)
    for i in order:
        t = int(ts.loc[i].value)
        if last_kept_ns is None or (t - last_kept_ns) >= cooldown_ns:
            keep[events.index.get_loc(i)] = True
            last_kept_ns = t
    return keep
