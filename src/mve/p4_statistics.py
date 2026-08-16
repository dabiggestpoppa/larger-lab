"""P4 — Interpretable statistics for the Causal Acceptance Engine.

Deterministic, dependency-light statistics used by P4:

- Wilson score binomial CI,
- seeded percentile bootstrap CI (differences and single statistics),
- Benjamini-Hochberg FDR correction,
- logistic regression via iteratively reweighted least squares (IRLS) with
  Wald z-statistics and a likelihood-ratio test against a nested model,
- Kaplan-Meier survival / discrete hazard tables,
- transition (crosstab) matrices.

No black-box ML. No statsmodels dependency: everything is numpy (+scipy for
the chi2 tail in the likelihood-ratio test, scipy already being a project
dependency). All randomness uses caller-supplied seeds for reproducibility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2

Z95 = 1.959963984540054


def wilson_ci(k: int, n: int, z: float = Z95) -> tuple:
    """Wilson score interval for a binomial proportion k/n. Returns (p, lo, hi)."""
    if n <= 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_ci(
    stat_fn,
    data: np.ndarray,
    n_boot: int = 2000,
    seed: int = 7777,
    alpha: float = 0.05,
) -> tuple:
    """Percentile bootstrap CI for a scalar statistic of `data`.

    stat_fn: callable(array) -> float. Deterministic given seed.
    Returns (estimate, lo, hi) over the bootstrap distribution.
    """
    rng = np.random.default_rng(seed)
    est = float(stat_fn(data))
    if len(data) == 0:
        return (est, np.nan, np.nan)
    draws = np.empty(n_boot)
    n = len(data)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        draws[i] = stat_fn(data[idx])
    lo, hi = np.percentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (est, float(lo), float(hi))


def bootstrap_diff_ci(
    a: np.ndarray,
    b: np.ndarray,
    n_boot: int = 2000,
    seed: int = 7777,
    alpha: float = 0.05,
) -> tuple:
    """Bootstrap CI for mean(a) - mean(b). Returns (diff, lo, hi)."""
    rng = np.random.default_rng(seed)
    diff = float(np.nanmean(a) - np.nanmean(b))
    draws = np.empty(n_boot)
    na, nb = len(a), len(b)
    for i in range(n_boot):
        ia = rng.integers(0, na, size=na)
        ib = rng.integers(0, nb, size=nb)
        draws[i] = np.nanmean(a[ia]) - np.nanmean(b[ib])
    lo, hi = np.percentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (diff, float(lo), float(hi))


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR q-values (monotone)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    # enforce monotonicity from the largest p downward
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.minimum(q, 1.0)
    out = np.empty(n)
    out[order] = q
    return out


# ---------------------------------------------------------------------------
# Logistic regression (IRLS) — interpretable incremental-information tests
# ---------------------------------------------------------------------------

def _design_matrix(rows: list, columns: list) -> tuple:
    """Build numeric design matrix + column names from row dicts.

    Numeric columns pass through; categorical columns are one-hot encoded
    (k-1 dummies, reference = first level). Returns (X, colnames).
    """
    names = []
    for col in columns:
        val = rows[0].get(col)
        if isinstance(val, (int, float, np.floating, np.integer)) and not isinstance(val, bool):
            names.append((col, "num"))
        else:
            names.append((col, "cat"))
    X_cols = []
    for col, kind in names:
        if kind == "num":
            X_cols.append(col)
        else:
            levels = sorted({r.get(col) for r in rows}, key=str)
            for lv in levels[1:]:
                X_cols.append(f"{col}__{lv}")
    X = np.zeros((len(rows), len(X_cols)))
    for i, r in enumerate(rows):
        for j, col in enumerate(X_cols):
            if "__" in col:
                base, lv = col.rsplit("__", 1)
                X[i, j] = 1.0 if str(r.get(base)) == lv else 0.0
            else:
                X[i, j] = r.get(col, np.nan)
    return X, X_cols


def fit_logistic(X: np.ndarray, y: np.ndarray, max_iter: int = 200, tol: float = 1e-9) -> dict:
    """IRLS logistic regression with intercept. Returns coefs, se, z, p, deviance."""
    n, p = X.shape
    Xd = np.column_stack([np.ones(n), X])
    coef = np.zeros(p + 1)
    for _ in range(max_iter):
        eta = Xd @ coef
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        w = mu * (1.0 - mu)
        # guard against perfect separation collapse
        w = np.clip(w, 1e-12, None)
        z_work = eta + (y - mu) / w
        try:
            Xw = Xd * np.sqrt(w)[:, None]
            beta_new = np.linalg.lstsq(Xw, np.sqrt(w) * z_work, rcond=None)[0]
        except np.linalg.LinAlgError:  # pragma: no cover
            break
        if np.max(np.abs(beta_new - coef)) < tol:
            coef = beta_new
            break
        coef = beta_new
    eta = Xd @ coef
    mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
    eps = 1e-12
    dev = -2.0 * np.sum(y * np.log(np.clip(mu, eps, 1)) + (1 - y) * np.log(np.clip(1 - mu, eps, 1)))
    # Wald standard errors from the observed information matrix
    w = np.clip(mu * (1 - mu), 1e-12, None)
    Xw = Xd * np.sqrt(w)[:, None]
    try:
        cov = np.linalg.inv(Xw.T @ Xw)
        se = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    except np.linalg.LinAlgError:  # pragma: no cover
        se = np.full(p + 1, np.nan)
    z = coef / se
    pvals = 2.0 * (1.0 - _norm_cdf(np.abs(z)))
    return {
        "coef": coef,
        "se": se,
        "z": z,
        "p": pvals,
        "deviance": float(dev),
        "n": int(n),
        "converged": bool(np.isfinite(dev)),
    }


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF via the Abramowitz-Stegun 7.1.26 erf (max err ~1.5e-7)."""
    x = np.asarray(x, dtype=float)
    sign = np.sign(x)
    ax = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    poly = t * (
        0.254829592
        + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    erf = sign * (1.0 - poly * np.exp(-ax * ax))
    return 0.5 * (1.0 + erf)


def likelihood_ratio_test(full_dev: float, null_dev: float, df_diff: int) -> float:
    """LR test p-value: chi2(df_diff) survival of the deviance difference."""
    stat = max(0.0, null_dev - full_dev)
    return float(chi2.sf(stat, df_diff))


# ---------------------------------------------------------------------------
# Survival / transition tables
# ---------------------------------------------------------------------------

def kaplan_meier(
    times: np.ndarray,
    events: np.ndarray,
    max_t: int = 24,
) -> pd.DataFrame:
    """Kaplan-Meier survival table.

    times: time-to-event (or censoring) in bars; events: 1 = event occurred,
    0 = censored (still beyond at the observation horizon). Returns a
    DataFrame with survival probability and discrete hazard per bar.
    """
    out_rows = []
    at_risk = len(times)
    surv = 1.0
    for t in range(1, max_t + 1):
        d = int(np.sum((events == 1) & (times == t)))
        censored_now = int(np.sum((events == 0) & (times == t)))
        if at_risk > 0:
            hazard = d / at_risk
            surv *= 1.0 - hazard
        else:
            hazard = np.nan
        out_rows.append(
            {
                "bar": t,
                "at_risk": at_risk,
                "events": d,
                "censored": censored_now,
                "hazard": hazard,
                "survival": surv,
            }
        )
        at_risk -= d + censored_now
    return pd.DataFrame(out_rows)


def transition_matrix(
    from_states: np.ndarray,
    to_states: np.ndarray,
    labels: tuple = (0, 1, 2, 3, 4),
) -> pd.DataFrame:
    """Count-based transition matrix (crosstab) with row-normalized probs."""
    idx = pd.MultiIndex.from_arrays([from_states, to_states])
    counts = pd.Series(1, index=idx).groupby(level=[0, 1]).sum().unstack(fill_value=0)
    counts = counts.reindex(index=labels, columns=labels, fill_value=0)
    probs = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)
    out = probs.copy()
    out["N"] = counts.sum(axis=1)
    return out
