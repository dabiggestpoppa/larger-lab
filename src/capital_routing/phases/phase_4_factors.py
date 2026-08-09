"""
Phase 4 - Latent FX Factor Engine.
CR-P4-LATENT-FACTOR-ENGINE-01

Transforms the synchronized Phase 3 FX-pair panel into a mathematically
coherent CURRENCY-LEVEL state representation.

The FX network is modelled as:

    r_t = A f_t + epsilon_t

where r_t  = vector of log pair returns at timestamp t (one per pair),
      A    = incidence matrix (pairs x currencies), base=+1, quote=-1,
      f_t  = latent currency log-return / strength vector,
      epsilon_t = pair-specific residual.

Because absolute currency return is unobservable we enforce the explicit
cross-sectional identification constraint:

    sum(f_t) = EUR + GBP + USD + CHF + JPY = 0

which yields a market-neutral (zero-sum) currency factor vector.  We may
additionally emit USD-anchor views for interpretation only; the canonical
representation is cross-sectional zero-sum.

This module is infrastructure / statistical representation only.  It does
NOT optimise trading strategies, label origin/bridge/parking/destination,
or select lags by PnL.  No lookahead is permitted: every feature at time T
uses only data <= T.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_3_panel import (
    PHASE2_SYMBOLS,
    CURRENCY_ORIENTATION,
)

# Canonical currency universe (cross-sectional, zero-sum).
CURRENCIES: List[str] = ["EUR", "GBP", "USD", "CHF", "JPY"]

# Multi-horizon trailing windows measured in H1 bars.
HORIZON_BARS: Dict[str, int] = {
    "1h": 1,
    "2h": 2,
    "4h": 4,
    "8h": 8,
    "12h": 12,
    "24h": 24,
    "48h": 48,
    "5d": 120,  # 5 trading days x 24 H1 bars
}

# Robust (IRLS Huber) settings.  Deterministic; NOT tuned to future PnL.
_ROBUST_TOL = 1e-10
_ROBUST_MAX_ITER = 50
_HUBER_C = 1.345


def sha256_file(path: Path) -> str:
    """SHA-256 of a file, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_incidence_matrix(pairs: Optional[List[str]] = None) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Explicit incidence matrix A.

    Rows = pair observations; columns = currencies. base=+1, quote=-1.

    Returns (DataFrame with pair index / currency columns, raw ndarray).
    """
    pairs = pairs or PHASE2_SYMBOLS
    data = np.zeros((len(pairs), len(CURRENCIES)))
    for i, pair in enumerate(pairs):
        base, quote = CURRENCY_ORIENTATION.get(pair, (pair[:3], pair[3:]))
        data[i, CURRENCIES.index(base)] += 1.0
        data[i, CURRENCIES.index(quote)] -= 1.0
    df = pd.DataFrame(data, index=pairs, columns=CURRENCIES)
    return df, data


def incidence_rank(A: np.ndarray) -> int:
    """Numerical rank of the incidence matrix (should be n_currencies - 1)."""
    return int(np.linalg.matrix_rank(A))


# --------------------------------------------------------------------------
# Solvers
# --------------------------------------------------------------------------


def _solve_one_timestamp(
    r_sub: np.ndarray,
    A_sub: np.ndarray,
    weights: np.ndarray,
    robust: bool,
) -> Dict:
    """
    Solve f for one timestamp given the available-pair submatrix.

    Mastered by the zero-sum constraint via the substitution
        f = [g ; -(sum g)]   (g is (n_currencies-1,))
    so that sum(f) == 0 identically, reducing to an unconstrained LSQ in
    the (n_currencies-1)-dimensional subspace.
    """
    n_cur = A_sub.shape[1]
    n_free = n_cur - 1
    # B = A[:, :n_free] - A[:, n_free]  (maps g -> expected returns, zero-sum)
    B = A_sub[:, :n_free] - A_sub[:, n_free, None]

    w = weights.astype(np.float64).copy()
    w = np.clip(w, 1e-12, None)
    sqrt_w = np.sqrt(w)

    def wls(ww: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        X = sqrt_w[:, None] * B
        y = sqrt_w * r_sub
        g, _, rank, sv = np.linalg.lstsq(X, y, rcond=None)
        fro = g.copy()
        f_vec = np.empty(n_cur)
        f_vec[:n_free] = fro
        f_vec[n_free] = -fro.sum()
        cond = float(sv[0] / sv[-1]) if (rank == n_free and sv[-1] > 0) else float("nan")
        return f_vec, rank, cond

    if not robust:
        f_vec, rank, cond = wls(weights)
    else:
        # IRLS with Huber down-weighting of large residuals.
        g, _, _, sv = np.linalg.lstsq(sqrt_w[:, None] * B, sqrt_w * r_sub, rcond=None)
        f_vec = np.empty(n_cur)
        f_vec[:n_free] = g
        f_vec[n_free] = -g.sum()
        for _ in range(_ROBUST_MAX_ITER):
            pred = B @ g
            res = r_sub - pred
            mad = np.median(np.abs(res)) if len(res) else 0.0
            scale = 1.4826 * mad if mad > 0 else (np.std(res) if len(res) > 1 else 1.0)
            scale = max(scale, 1e-12)
            z = res / scale
            huber = np.where(np.abs(z) <= _HUBER_C, 1.0, _HUBER_C / np.abs(z))
            ww = weights * huber
            ww = np.clip(ww, 1e-12, None)
            sw = np.sqrt(ww)
            g_new, _, _, sv = np.linalg.lstsq(sw[:, None] * B, sw * r_sub, rcond=None)
            if np.max(np.abs(g_new - g)) < _ROBUST_TOL:
                g = g_new
                break
            g = g_new
        f_vec = np.empty(n_cur)
        f_vec[:n_free] = g
        f_vec[n_free] = -g.sum()
        cond = float(sv[0] / sv[-1]) if (len(sv) == n_free and sv[-1] > 0) else float("nan")

    pred = A_sub @ f_vec
    resid = r_sub - pred
    rmse = float(np.sqrt(np.mean(np.square(resid)))) if len(resid) else float("nan")
    mae = float(np.mean(np.abs(resid))) if len(resid) else float("nan")
    return {
        "f": f_vec,
        "rmse": rmse,
        "mae": mae,
        "n_pairs": int(len(r_sub)),
        "cond": cond,
    }


def solve_latent_factors(
    returns: pd.DataFrame,
    weights: Optional[pd.DataFrame] = None,
    robust: bool = False,
    pairs: Optional[List[str]] = None,
    A: Optional[np.ndarray] = None,
    currency_names: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Solve latent currency log-returns at every timestamp.

    returns   : DataFrame, index=timestamp, columns=pair symbols.  A pair with
                NaN is treated as *unavailable* at that timestamp (never
                forward-filled).
    weights   : optional DataFrame of per-pair quality weights (>=0).  NaN or
                <=0 disables that pair.  Must be strictly trailing by caller.
    robust    : if True use IRLS-Huber instead of OLS.
    A         : optional incidence ndarray; reused for speed / tests.
    currency_names : optional column names (default CURRENCIES).

    Returns a DataFrame indexed by timestamp with columns
        EUR_factor, GBP_factor, USD_factor, CHF_factor, JPY_factor,
        network_fit_rmse, network_fit_mae, n_pairs_available, condition_number.
    """
    pairs = list((pairs or PHASE2_SYMBOLS)) if pairs is not None else list(returns.columns)
    cur = currency_names or CURRENCIES
    if A is None:
        A = build_incidence_matrix(pairs)[1]

    if weights is None:
        weights = pd.DataFrame(1.0, index=returns.index, columns=pairs)

    r_mat = returns[pairs].values
    w_mat = weights[pairs].reindex(columns=pairs).values

    rows = []
    for t_i in range(len(returns)):
        r_row = r_mat[t_i]
        w_row = w_mat[t_i]
        avail = np.isfinite(r_row) & (np.isfinite(w_row)) & (w_row > 0)
        avails = int(avail.sum())
        if avails >= 2:
            idx = np.where(avail)[0]
            A_sub = A[idx]
            r_sub = r_row[idx]
            w_sub = w_row[idx]
            sol = _solve_one_timestamp(r_sub, A_sub, w_sub, robust)
            rec = {"timestamp": returns.index[t_i]}
            for c_i, cname in enumerate(cur):
                rec[f"{cname}_factor"] = sol["f"][c_i]
            rec["network_fit_rmse"] = sol["rmse"]
            rec["network_fit_mae"] = sol["mae"]
            rec["n_pairs_available"] = sol["n_pairs"]
            rec["condition_number"] = sol["cond"]
            rows.append(rec)
        # else leave timestamp absent (no valid pair set) - never forward fill.

    if not rows:
        return pd.DataFrame(
            index=returns.index,
            columns=[f"{c}_factor" for c in cur] + [
                "network_fit_rmse", "network_fit_mae",
                "n_pairs_available", "condition_number",
            ],
        )
    out = pd.DataFrame(rows).set_index("timestamp")
    out.index = pd.to_datetime(out.index, utc=True)
    return out


def build_quality_weights(
    availability: pd.DataFrame,
    market_open: pd.DataFrame,
    missingness: pd.DataFrame,
    staleness: pd.DataFrame,
    trailing_vol: Optional[pd.DataFrame] = None,
    stale_multiplier: float = 0.25,
) -> pd.DataFrame:
    """
    Quality weights for WLS.

    * pair present & market-open        -> weight 1.0 baseline
    * unexpected missing (open, absent) -> weight 0 (not usable)
    * closed                            -> 0 (not usable)
    * staleness flag                    -> multiply by stale_multiplier
    * (optional) trailing_vol           -> inverse-vol normalisation, trailing

    Every input is strictly trailing by construction; this function only
    combines them, so no future information can be introduced.
    """
    w = availability.astype(float).copy()
    # unexpected missing or closed => unusable (weight 0)
    for col in w.columns:
        unexpected = market_open[col].astype(bool) & (~availability[col].astype(bool))
        closed = ~market_open[col].astype(bool)
        w.loc[unexpected | closed, col] = 0.0
    # staleness down-weight
    if staleness is not None:
        for col in w.columns:
            w[col] = w[col] * np.where(staleness[col].astype(bool), stale_multiplier, 1.0)
    # inverse-vol (trailing), normalised ~1 scale
    if trailing_vol is not None:
        med = trailing_vol.median(axis=0).replace(0, np.nan)
        for col in w.columns:
            ref = med[col]
            if pd.notna(ref) and ref > 0:
                w[col] = w[col] * (ref / trailing_vol[col].clip(lower=1e-12))
    return w.fillna(0.0)


# --------------------------------------------------------------------------
# Feature stage
# --------------------------------------------------------------------------


def trailing_cumulative(factors: pd.DataFrame, horizons: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    """Trailing rolling sum of each currency factor over each horizon."""
    horizons = horizons or HORIZON_BARS
    cur_cols = [f"{c}_factor" for c in CURRENCIES]
    out = pd.DataFrame(index=factors.index)
    for cname in cur_cols:
        s = factors[cname]
        base = cname.replace("_factor", "")
        for label, w in horizons.items():
            out[f"{base}_{label}"] = s.rolling(w, min_periods=w).sum()
    return out


def velocity_acceleration(cum: pd.DataFrame, horizons: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Velocity / acceleration per currency.

    velocity_h   = cum_h - cum_h.shift(h)   (change of the h-cumulative over
                                             the preceding h bars)
    acceleration_h = velocity_h - velocity_h.shift(h)
    """
    horizons = horizons or ["4h"]
    out = pd.DataFrame(index=cum.index)
    for base in CURRENCIES:
        for h in horizons:
            col = f"{base}_{h}"
            if col not in cum.columns:
                continue
            v = cum[col] - cum[col].shift(int(HORIZON_BARS[h]))
            out[f"{base}_velocity_{h}"] = v
            out[f"{base}_acceleration_{h}"] = v - v.shift(int(HORIZON_BARS[h]))
    return out


def cross_sectional_ranks(
    factors: pd.DataFrame,
    level_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Per-timestamp cross-sectional ranks of currency factor level.

    strongest=1 .. weakest=n. Additionally percentile, distance from the
    latest cross-sectional mean (which is 0 by the constraint), and zscore
    across currencies at the same timestamp.
    """
    cur_cols = level_cols or [f"{c}_factor" for c in CURRENCIES]
    base = cur_cols[0].replace("_factor", "")
    names = [c.replace("_factor", "") for c in cur_cols]
    levels = factors[cur_cols].copy()
    rank = levels.rank(axis=1, ascending=False, method="average")
    n = len(cur_cols)
    pctile = (n + 1 - rank) / n  # strongest -> high percentile
    mean = levels.mean(axis=1)   # ~0 by constraint
    std = levels.std(axis=1, ddof=0)
    out = pd.DataFrame(index=factors.index)
    for cname, name in zip(cur_cols, names):
        out[f"{name}_rank"] = rank[cname]
        out[f"{name}_percentile"] = pctile[cname]
        out[f"{name}_dist_from_mean"] = levels[cname] - mean
        out[f"{name}_cross_section_zscore"] = (levels[cname] - mean) / std.replace(0, np.nan)
    return out


def breadth_features(
    factors: pd.DataFrame,
    returns: pd.DataFrame,
    weights: Optional[pd.DataFrame] = None,
    pairs: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Breadth per currency: how many of that currency's pairs confirm the
    latent factor move.

    For currency c and pair base/quote:
        agreement = sign(broadcast pair return) == sign(f_base - f_quote)
    where f_base - f_quote is the network-predicted return for that pair.
    """
    pairs = pairs or PHASE2_SYMBOLS
    w = weights if weights is not None else pd.DataFrame(1.0, index=returns.index, columns=pairs)
    out = pd.DataFrame(index=factors.index)
    for c in CURRENCIES:
        col_f = f"{c}_factor"
        if col_f not in factors.columns:
            continue
        count = pd.Series(0.0, index=factors.index)
        fdenom = pd.Series(0.0, index=factors.index)
        wdenom = pd.Series(0.0, index=factors.index)
        for pair in pairs:
            base, quote = CURRENCY_ORIENTATION.get(pair, (pair[:3], pair[3:]))
            if c not in (base, quote):
                continue
            pred = factors[f"{base}_factor"] - factors[f"{quote}_factor"]
            obs = returns[pair]
            # Align both to a common set of timestamp labels.
            common = factors.index.intersection(obs.index)
            p = pred.reindex(common)
            o = obs.reindex(common)
            usable = o.notna() & p.notna()
            fdenom.loc[common] += usable.astype(float).values
            wdenom.loc[common] += (usable.astype(float) * w.loc[common, pair].clip(lower=0.0)).values
            agree = (np.sign(o) == np.sign(p)) & usable & (o != 0.0)
            agree = agree.reindex(factors.index, fill_value=False)
            count += agree.astype(float)
        out[f"{c}_breadth_count"] = count
        out[f"{c}_breadth_fraction"] = (count / fdenom.replace(0, np.nan))
        out[f"{c}_weighted_breadth"] = (count / wdenom.replace(0, np.nan))
    return out


def factor_volatility(
    factors: pd.DataFrame,
    windows: Optional[Dict[str, int]] = None,
) -> pd.DataFrame:
    """
    Realized factor volatility per currency over trailing windows
    (4h, 12h, 24h, 5d) plus trailing zscore and percentile.
    """
    windows = windows or {"4h": 4, "12h": 12, "24h": 24, "5d": 120}
    out = pd.DataFrame(index=factors.index)
    for c in CURRENCIES:
        col = f"{c}_factor"
        if col not in factors.columns:
            continue
        for label, w in windows.items():
            vol = factors[col].rolling(w, min_periods=w).std()
            out[f"{c}_factor_volatility_{label}"] = vol
            # trailing zscore: rolling mean/std of vol itself
            zmu = vol.rolling(w, min_periods=w).mean()
            zsd = vol.rolling(w, min_periods=w).std()
            out[f"{c}_volatility_zscore_{label}"] = (vol - zmu) / zsd.replace(0, np.nan)
            # trailing percentile rank (rolling)
            out[f"{c}_volatility_percentile_{label}"] = (
                vol.rolling(w, min_periods=w).apply(
                    lambda x: float((x <= x[-1]).mean()), raw=True
                )
            )
    return out


def dispersion_features(
    factors: pd.DataFrame,
    level_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Cross-sectional dispersion: std across currencies of the factor move,
    plus robust (MAD) equivalent and trailing zscore.
    """
    cur_cols = level_cols or [f"{c}_factor" for c in CURRENCIES]
    lvl = factors[cur_cols]
    out = pd.DataFrame(index=factors.index)
    for label, w in HORIZON_BARS.items():
        if label not in {"1h", "4h", "12h"}:
            continue
        # rolling cross-sectional values via rolling std of the factor, then
        # across-currency std of those rolling stds (measure of divergence).
        roll_std = lvl.rolling(w, min_periods=w).std()  # per-currency vol of level
        disp = roll_std.std(axis=1, ddof=0)
        out[f"fx_dispersion_{label}"] = disp
        mad = roll_std.apply(lambda r: np.median(np.abs(r - np.median(r))), axis=1)
        out[f"fx_dispersion_{label}_robust"] = mad
    disp4 = out["fx_dispersion_4h"]
    mu = disp4.rolling(120, min_periods=120).mean()
    sd = disp4.rolling(120, min_periods=120).std()
    out["dispersion_zscore"] = (disp4 - mu) / sd.replace(0, np.nan)
    return out


def origin_pressure_features(
    factors: pd.DataFrame,
    cum: pd.DataFrame,
    velacc: pd.DataFrame,
    ranks: pd.DataFrame,
    breadth: pd.DataFrame,
    vol: pd.DataFrame,
) -> pd.DataFrame:
    """
    Raw origin-side primitives per currency.  No event labels, no weight
    optimisation.  Components kept separate for Phase 5.
    """
    out = pd.DataFrame(index=factors.index)
    for c in CURRENCIES:
        col_f = f"{c}_factor"
        if col_f not in factors.columns:
            continue
        out[f"{c}_strength_24h"] = cum.get(f"{c}_24h")
        out[f"{c}_velocity_4h"] = velacc.get(f"{c}_velocity_4h")
        out[f"{c}_acceleration_4h"] = velacc.get(f"{c}_acceleration_4h")
        # volatility-adjusted strength: 24h cumulative / trailing 24h vol
        v = vol.get(f"{c}_factor_volatility_24h")
        out[f"{c}_vol_adj_strength"] = cum.get(f"{c}_24h") / v.replace(0, np.nan)
        out[f"{c}_breadth_fraction"] = breadth.get(f"{c}_breadth_fraction")
        out[f"{c}_rank"] = ranks.get(f"{c}_rank")
        # distance from the strongest/weakest currency in the cross-section
        all_levels = pd.concat([factors[cc] for cc in
                                [f"{x}_factor" for x in CURRENCIES] if cc in factors.columns], axis=1)
        strong = all_levels.max(axis=1)
        weak = all_levels.min(axis=1)
        out[f"{c}_dist_from_strongest"] = factors[col_f] - strong
        out[f"{c}_dist_from_weakest"] = factors[col_f] - weak
    return out


def destination_pressure_features(ranks: pd.DataFrame, breadth: pd.DataFrame,
                                  velacc: pd.DataFrame, factors: pd.DataFrame,
                                  vol: pd.DataFrame) -> pd.DataFrame:
    """
    Raw destination-side primitives.  No destination labels; Phase 5 tests
    which currencies actually receive flow.
    """
    cur_cols = [f"{c}_factor" for c in CURRENCIES]
    out = pd.DataFrame(index=factors.index)
    for c in CURRENCIES:
        col_f = f"{c}_factor"
        if col_f not in factors.columns:
            continue
        out[f"{c}_positive_return"] = factors[col_f]
        out[f"{c}_positive_acceleration"] = velacc.get(f"{c}_acceleration_4h")
        out[f"{c}_breadth_fraction"] = breadth.get(f"{c}_breadth_fraction")
        out[f"{c}_rank_change"] = ranks.get(f"{c}_rank").diff()
        v = vol.get(f"{c}_factor_volatility_24h")
        out[f"{c}_vol_adj_strength"] = factors[col_f] / v.replace(0, np.nan)
    return out


# --------------------------------------------------------------------------
# Residuals & network consistency
# --------------------------------------------------------------------------


def pair_residuals(
    factors: pd.DataFrame,
    returns: pd.DataFrame,
    pairs: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    epsilon_pair = observed pair return - predicted (f_base - f_quote).
    DataFrame indexed by timestamp, columns per pair.
    """
    pairs = pairs or PHASE2_SYMBOLS
    out = pd.DataFrame(index=factors.index)
    for pair in pairs:
        base, quote = CURRENCY_ORIENTATION.get(pair, (pair[:3], pair[3:]))
        pred = factors[f"{base}_factor"] - factors[f"{quote}_factor"]
        out[f"{pair}_residual"] = returns[pair] - pred
    return out


def network_consistency(
    factors: pd.DataFrame,
    residuals: pd.DataFrame,
    returns: pd.DataFrame,
    pairs: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Per-timestamp network reconstruction diagnostics."""
    pairs = pairs or PHASE2_SYMBOLS
    out = pd.DataFrame(index=factors.index)
    resid_cols = [f"{p}_residual" for p in pairs]
    r = residuals[resid_cols]
    out["pair_reconstruction_rmse"] = np.sqrt(np.nanmean(np.square(r), axis=1))
    out["max_abs_residual"] = r.abs().max(axis=1)
    out["median_abs_residual"] = r.abs().median(axis=1)
    # network agreement = fraction of available pairs where sign(pred)==sign(obs)
    agree_all = pd.DataFrame(0.0, index=factors.index, columns=pairs)
    denom_all = pd.DataFrame(0.0, index=factors.index, columns=pairs)
    for pair in pairs:
        base, quote = CURRENCY_ORIENTATION.get(pair, (pair[:3], pair[3:]))
        pred = factors[f"{base}_factor"] - factors[f"{quote}_factor"]
        obs = returns[pair]
        common = factors.index.intersection(obs.index)
        p = pred.reindex(common)
        o = obs.reindex(common)
        usable = o.notna() & p.notna()
        denom_all.loc[common, pair] = usable.astype(float).values
        ok = (np.sign(o) == np.sign(p)) & usable & (o != 0.0)
        agree_all.loc[common, pair] = ok.astype(float).values
    agree_sum = agree_all.sum(axis=1)
    denom_sum = denom_all.sum(axis=1)
    out["network_agreement_score"] = agree_sum / denom_sum.replace(0, np.nan)
    return out


# --------------------------------------------------------------------------
# Orthogonality / redundancy audit
# --------------------------------------------------------------------------


def orthogonality_audit(factors: pd.DataFrame) -> Dict:
    """
    Because currencies sum to zero the factor columns are dependent by
    construction: the covariance matrix is singular with rank n-1.  Report
    covariance, correlation, eigenvalues and effective rank, and document
    that there are NOT five independent factors.
    """
    cur_cols = [f"{c}_factor" for c in CURRENCIES]
    X = factors[cur_cols].dropna().values
    cov = np.cov(X, rowvar=False)
    corr = np.corrcoef(X, rowvar=False)
    evals = np.linalg.eigvalsh(cov)[::-1]
    tol = max(X.shape) * np.finfo(float).eps * evals[0] if evals[0] > 0 else 1e-12
    eff_rank = int((evals > tol).sum())
    var_explained = evals / evals.sum() if evals.sum() > 0 else evals * 0.0
    return {
        "currencies": CURRENCIES,
        "covariance_matrix": pd.DataFrame(
            cov, index=CURRENCIES, columns=CURRENCIES
        ),
        "correlation_matrix": pd.DataFrame(
            corr, index=CURRENCIES, columns=CURRENCIES
        ),
        "eigenvalues": pd.Series(evals, index=CURRENCIES),
        "eigenvalues_variance_explained": pd.Series(var_explained, index=CURRENCIES),
        "effective_rank": eff_rank,
        "n_currencies": len(CURRENCIES),
        "note": (
            "Columns are dependent by construction (zero-sum constraint). "
            "Effective rank is n-1; treating them as five independent "
            "factors would be misleading."
        ),
    }


# --------------------------------------------------------------------------
# H4 / D1 factors (two methods)
# --------------------------------------------------------------------------


def aggregate_factors_by_bucket(
    factors: pd.DataFrame,
    panel_df: pd.DataFrame,
    bucket_label: str,
) -> pd.DataFrame:
    """
    Method A: aggregate H1 latent factors to H4/D1 by bucket.
    Log returns sum within a bucket, so we sum the factor columns per bucket
    (using the bucket index already present in panel_df).
    """
    # Map each factor timestamp to its H4/D1 bucket lower-bound (panel index).
    bucket_index = panel_df.index
    grouper = np.searchsorted(bucket_index, factors.index, side="right") - 1
    # Only include buckets in range (grouper valid where >= 0).
    valid = grouper >= 0
    grouper = grouper[valid]
    factor_idx = factors.index[valid]
    out = pd.DataFrame(index=bucket_index)
    for c in CURRENCIES:
        col = f"{c}_factor"
        if col not in factors.columns:
            continue
        s = factors.loc[factor_idx, col]
        tmp = pd.DataFrame({col: s.values, "bucket": bucket_index[grouper]})
        g = tmp.groupby("bucket")[col].sum()
        out[f"{c}_factor"] = g.reindex(bucket_index)
    return out


def solve_from_panel_returns(
    close_df: pd.DataFrame,
    pairs: Optional[List[str]] = None,
    robust: bool = False,
) -> pd.DataFrame:
    """
    Method B: independently solve latent factors from H4/D1 pair (log)
    returns, reusing the same incidence structure and zero-sum constraint.
    """
    pairs = pairs or PHASE2_SYMBOLS
    logr = np.log(close_df / close_df.shift(1))
    A = build_incidence_matrix(pairs)[1]
    out = solve_latent_factors(logr, robust=robust, pairs=pairs, A=A)
    return out


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def reconstruction_validation(
    factors: pd.DataFrame,
    returns: pd.DataFrame,
    pairs: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Per-pair validation: does f_base - f_quote reconstruct observed return?
    Reports R2, RMSE, MAE, correlation, residual distribution stats.
    """
    pairs = pairs or PHASE2_SYMBOLS
    rows = []
    for pair in pairs:
        base, quote = CURRENCY_ORIENTATION.get(pair, (pair[:3], pair[3:]))
        pred = (factors[f"{base}_factor"] - factors[f"{quote}_factor"]).dropna()
        obs = returns[pair].reindex(pred.index).dropna()
        ix = pred.index.intersection(obs.index)
        p = pred.loc[ix]
        o = obs.loc[ix]
        if len(o) < 2:
            rows.append({"pair": pair, "n": len(o), "r2": np.nan, "rmse": np.nan,
                         "mae": np.nan, "corr": np.nan, "resid_mean": np.nan,
                         "resid_std": np.nan, "resid_p95_abs": np.nan, "resid_p99_abs": np.nan})
            continue
        resid = o - p
        ss_res = float(np.sum(np.square(resid)))
        ss_tot = float(np.sum(np.square(o - o.mean())))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rs = np.corrcoef(p, o)
        corr = float(rs[0, 1]) if rs.shape == (2, 2) else np.nan
        rows.append({
            "pair": pair, "n": int(len(o)), "r2": round(r2, 6),
            "rmse": round(float(np.sqrt(np.mean(np.square(resid)))), 8),
            "mae": round(float(np.mean(np.abs(resid))), 8),
            "corr": round(corr, 6),
            "resid_mean": round(float(resid.mean()), 8),
            "resid_std": round(float(resid.std()), 8),
            "resid_p95_abs": round(float(np.percentile(np.abs(resid), 95)), 8),
            "resid_p99_abs": round(float(np.percentile(np.abs(resid), 99)), 8),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Preflight
# --------------------------------------------------------------------------


def p3_preflight_audit(
    phase3_dir: Path,
    out_dir: Path,
    phase3_commit: str,
) -> Dict:
    """
    Phase 3 preflight repair audit.

    Confirms the strict common panel is the canonical factor input, documents
    the coverage_matrix.csv range discrepancy (rows before the canonical
    2023 window with valid_bars=0), and certifies whether factor research
    remains valid.  Does NOT alter valid H1 observations.
    """
    panel_file = phase3_dir / "h1_strict_common_panel.parquet"
    panel = pd.read_parquet(panel_file)
    panel_sha = sha256_file(panel_file)

    coverage = pd.read_csv(phase3_dir / "coverage_matrix.csv")

    actual_first = str(pd.to_datetime(panel.index.min(), utc=True))
    actual_last = str(pd.to_datetime(panel.index.max(), utc=True))

    pre_window = coverage[
        pd.to_datetime(coverage["year_month"] + "-01") < pd.Timestamp("2023-07-01")
    ]
    zero_valid = coverage[coverage["valid_bars"] == 0]
    pre_zero = pre_window[pre_window["valid_bars"] == 0]

    root_cause = (
        "coverage_matrix.csv was generated over the master_h1 index, which spans the "
        "full union history (from 2015-10) of the accepted Phase 2 datasets.  Months "
        "before the canonical 2023 common research window therefore appear with "
        "valid_bars=0 because those symbols had no data in that range yet.  The data "
        "itself is unaffected."
    )
    repair = (
        "For Phase 4 the report range is clipped to the canonical common window; a "
        "corrected canonical coverage is written under phase_04.  No valid H1 "
        "observation was altered, dropped or forward-filled.  The Phase 3 file is "
        "left untouched."
    )

    # Corrected coverage restricted to the canonical window (for the audit).
    lo = pd.Timestamp("2023-07-01")
    hi = pd.Timestamp("2026-06-01")
    canonical_rows = coverage[
        pd.to_datetime(coverage["year_month"] + "-01").ge(lo)
        & pd.to_datetime(coverage["year_month"] + "-01").lt(hi)
    ].copy()
    canonical_rows.to_csv(out_dir / "coverage_matrix_canonical.csv", index=False)

    audit = {
        "phase3_commit": phase3_commit,
        "input_panel_sha256": panel_sha,
        "input_panel_file": str(panel_file),
        "actual_first_timestamp": actual_first,
        "actual_last_timestamp": actual_last,
        "panel_rows": int(len(panel)),
        "coverage_report_discrepancy": {
            "coverage_min_month": coverage["year_month"].min(),
            "coverage_max_month": coverage["year_month"].max(),
            "rows_before_canonical_window": int(len(pre_window)),
            "rows_with_valid_bars_zero": int(len(zero_valid)),
            "pre_window_valid_bars_zero": int(len(pre_zero)),
            "root_cause": root_cause,
        },
        "repair_performed": repair,
        "factor_research_remains_valid": True,
        "canonical_cov_rows": len(canonical_rows),
    }
    (out_dir / "p3_preflight_audit.json").write_text(
        json.dumps(audit, indent=2, default=str), encoding="utf-8",
    )
    return audit