#!/usr/bin/env python
"""ALT_MECH_20 - GLOBAL RESPONSE / REALIZATION MECHANICS base module.

Reuses the MECH-19 substrate (which chains MECH-18 -> MECH-17: data load, forcing
families, traffic objects, edge registry, threshold/saturation machinery, birth
partition, 2022 event machinery) and adds MECH-20 primitives:

- UNCLAMPED rolling response-node series (gain/ceiling/onset) - the repair fit is
  the ONLY fit used in the response-law layer.
- Changepoint helpers: CUSUM, segmented regression, rolling distribution shift.
- Matched nearest-neighbor sampling helper.
- Discrete information-decomposition helper (complementarity/substitution tests).
- Functional-dimension helpers for the forcing atlas.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]                 # mech_20/
RETRO = ROOT.parent / "mech_19"


def load_substrate():
    """Import the MECH-19 build module as `M99`, exposing its full substrate
    (globals) and helpers. Module-level writes are idempotent and cheap."""
    sys.path.insert(0, str(RETRO / "scripts"))
    import build_mech19 as M99
    return M99


def logistic_params_unc(x, y, ceil_hi=None):
    """Unclamped logistic fit (ceiling clamp LIFTED). Returns (ceil, x0, k, rmse, n)."""
    from scipy.optimize import curve_fit
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 60:
        return np.nan, np.nan, np.nan, np.nan, 0
    try:
        def model(X, ceiling, x0, k):
            return ceiling / (1.0 + np.exp(-k * (X - x0)))
        p0 = [float(np.nanmax(y)) if np.nanmax(y) > 0 else 0.55, float(np.nanmedian(x)), 1.0]
        lo = [-5.0, np.nanmin(x) - 2.0, -8.0]
        hi = [float(ceil_hi) if ceil_hi else 5.0, np.nanmax(x) + 2.0, 20.0]
        popt, _ = curve_fit(model, x, y, p0=p0, bounds=(lo, hi), maxfev=40000)
        ceil, x0, k = float(popt[0]), float(popt[1]), float(popt[2])
        pred = model(x, ceil, x0, k)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return ceil, x0, k, rmse, int(len(x))
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0


def rolling_nodes_unc(dates, fc, act, resps, win=180, step=30, fit=logistic_params_unc):
    """Rolling unclamped logistic nodes, asof-filled to daily. Returns DataFrame
    with columns '{p}_k', '{p}_ceiling', '{p}_x0' aligned to `dates`."""
    dmin, dmax = dates.min(), dates.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=win), freq=f"{step}D")
    rows = []
    for t0 in starts:
        mw = (dates >= t0) & (dates < t0 + pd.Timedelta(days=win))
        xw = fc[mw]
        rec = {"date": t0}
        for p in resps:
            yw = np.asarray(act[p], dtype=float)[mw]
            m2 = ~(np.isnan(xw) | np.isnan(yw))
            if int(m2.sum()) < 60:
                rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = np.nan, np.nan, np.nan
                continue
            ceil, x0, k, _, _ = fit(xw[m2], yw[m2])
            rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = k, ceil, x0
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dates)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])


def r2(y, pred):
    y = np.asarray(y, dtype=float); pred = np.asarray(pred, dtype=float)
    m = np.isfinite(y) & np.isfinite(pred)
    if m.sum() < 20:
        return np.nan
    ss = np.sum((y[m] - y[m].mean()) ** 2)
    return float(1 - np.sum((y[m] - pred[m]) ** 2) / ss) if ss > 1e-12 else np.nan


def run_episodes(mask):
    """Contiguous-run intervals of a boolean mask -> list of (i0, i1) inclusive."""
    mask = np.asarray(mask, dtype=bool)
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j - 1))
            i = j
        else:
            i += 1
    return out


# ------------------------------------------------------------------ changepoint helpers
def cusum_breaks(x, min_seg=180, mad_scale=True):
    """Binary-segmentation CUSUM on a series x (NaNs dropped/forward-filled by caller).
    Returns list of break indices (strictly inside the series)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    breaks = []
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if (b - a + 1) < 2 * min_seg:
            continue
        seg = x[a:b + 1]
        med = np.nanmedian(seg)
        mad = np.nanmedian(np.abs(seg - med)) * 1.4826
        if not np.isfinite(mad) or mad < 1e-9:
            mad = np.nanstd(seg)
        z = (seg - med) / max(mad, 1e-9)
        z = np.where(np.isfinite(z), z, 0.0)
        cus = np.cumsum(z)
        k = int(np.argmax(np.abs(cus)))
        if a + k < a + min_seg or a + k > b - min_seg:
            continue
        if abs(cus[k]) < 3.0 * np.sqrt(len(seg)):
            continue
        breaks.append(a + k)
        stack.append((a, a + k))
        stack.append((a + k, b))
    return sorted(breaks)


def segfit_breaks(x, cand_step=30, min_seg=180, max_breaks=2):
    """Piecewise-constant/linear segmented fit over candidate break indices spaced
    cand_step apart; returns list of break indices minimizing SSE (max_breaks)."""
    n = len(x)
    cands = list(range(min_seg, n - min_seg, cand_step))
    if not cands:
        return []
    best = []
    best_sse = np.inf
    from itertools import combinations
    for k in range(0, max_breaks + 1):
        for combo in combinations(cands, k):
            segs = [(0, combo[0])] + [(combo[i], combo[i + 1]) for i in range(len(combo) - 1)] + [(combo[-1], n)] if combo else [(0, n)]
            sse = 0.0
            for (a, b) in segs:
                s = x[a:b]
                if len(s) == 0:
                    continue
                t = np.arange(len(s))
                A = np.column_stack([np.ones(len(s)), t])
                try:
                    coef, *_ = np.linalg.lstsq(A, np.where(np.isfinite(s), s, np.nanmean(s)), rcond=None)
                except Exception:
                    coef = np.array([np.nanmean(s), 0.0])
                pred = A @ coef
                sse += float(np.nansum((s - pred) ** 2))
            if sse < best_sse:
                best_sse = sse
                best = list(combo)
    return best


def dist_shift_breaks(x, base_win=360, ref_win=90, thr_z=3.0):
    """Rolling distribution-shift: for each t, rolling ref_win mean vs base_win
    trailing mean, z-scored by trailing MAD. Returns first index with |z|>thr_z
    sustained over ref_win, and list of all such sustained starts."""
    x = pd.Series(np.asarray(x, dtype=float))
    bp = max(int(base_win * 0.4), 5)
    rp = max(int(ref_win * 0.5), 3)
    base = x.rolling(base_win, min_periods=bp).mean()
    mad = (x - base).abs().rolling(base_win, min_periods=bp).median() * 1.4826
    ref = x.rolling(ref_win, min_periods=rp).mean()
    z = (ref - base) / mad.replace(0, np.nan)
    z = z.to_numpy()
    n = len(z)
    starts = []
    i = ref_win
    while i < n:
        if np.isfinite(z[i]) and abs(z[i]) > thr_z:
            j = i
            while j < n and np.isfinite(z[j]) and abs(z[j]) > thr_z:
                j += 1
            if (j - i) >= ref_win:
                starts.append(i)
                i = j
            else:
                i += 1
        else:
            i += 1
    return starts


# ------------------------------------------------------------------ matching helper
def match_nearest(feat_X, idx_from, idx_to, k=1, rng_seed=0):
    """Nearest-neighbour matching: for each i in idx_from, pick the closest j in
    idx_to by Euclidean distance on standardized feat_X. Returns dict i -> j
    (with replacement), plus unmatched list."""
    X = np.asarray(feat_X, dtype=float)
    mu = np.nanmean(X, axis=0); sd = np.nanstd(X, axis=0) + 1e-9
    Xs = (X - mu) / sd
    out = {}
    for i in idx_from:
        d = np.nansum((Xs[idx_to] - Xs[i]) ** 2, axis=1)
        d = np.where(np.isfinite(d), d, np.inf)
        j = int(idx_to[np.argmin(d)])
        out[i] = j
    return out


# ------------------------------------------------------------------ information decomposition
def _bin(v, q=(0.33, 0.67)):
    v = np.asarray(v, dtype=float)
    lo, hi = np.nanquantile(v, q)
    b = np.full(len(v), np.nan)
    b[v <= lo] = 0; b[(v > lo) & (v < hi)] = 1; b[v >= hi] = 2
    return b


def discrete_mi(x, y):
    """Mutual information (nats) between two discrete arrays."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m].astype(int), y[m].astype(int)
    if len(x) < 30:
        return np.nan, len(x)
    n = len(x)
    hx = _ent(x); hy = _ent(y); hxy = _ent2(x, y)
    return float(hx + hy - hxy), n


def _ent(x):
    _, c = np.unique(x, return_counts=True)
    p = c / c.sum()
    return -float(np.sum(p * np.log(p)))


def _ent2(x, y):
    xy = x * 1000 + y
    _, c = np.unique(xy, return_counts=True)
    p = c / c.sum()
    return -float(np.sum(p * np.log(p)))
