#!/usr/bin/env python
"""ALT_MECH_19 - GLOBAL ADAPTIVE-LAW HARDENING base module.

Reuses the MECH-18 substrate (data load, forcing families, traffic objects,
edge registry, threshold/saturation machinery, birth partition, 2022 event
machinery) and adds MECH-19 primitives: an UNCLAMPED logistic fitter (2022
repair), bounded robust alternative, contiguous-run episode segmentation, and
route-commitment / concentration helpers.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]                 # mech_19/
RETRO = ROOT.parent / "mech_18"
SCR18 = RETRO / "scripts"


def load_substrate():
    """Import the MECH-18 build module as `M88`, exposing its full substrate
    (globals) and helpers. Module-level writes are idempotent and cheap."""
    sys.path.insert(0, str(SCR18))
    if not os.path.exists(str(SCR18 / "_m18base.py")):
        raise FileNotFoundError("MECH-18 substrate missing; build it first.")
    import build_mech18 as M88
    return M88


def logistic_params_unc(x, y, x0_lo_extra=2.0, k_hi=20.0, ceil_hi=None):
    """Logistic fit with the ceiling upper clamp LIFTED.

    M17/M18 clamp ceiling to <=1.1 (activation>=~0.1 true in one state). Here the
    ceiling upper bound is free (default: no explicit cap, use 5.0 safety) so the
    2022 ceiling distortion claim can be audited directly.
    Returns (ceiling, x0, k, rmse, n); NaN on failure.
    """
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 60:
        return np.nan, np.nan, np.nan, np.nan, 0
    try:
        from scipy.optimize import curve_fit
        def model(X, ceiling, x0, k):
            return ceiling / (1.0 + np.exp(-k * (X - x0)))
        p0 = [np.nanmax(y) if np.nanmax(y) > 0 else 0.55, np.nanmedian(x), 1.0]
        lo = [-5.0, np.nanmin(x) - 2.0, -k_hi]
        hi = [float(ceil_hi) if ceil_hi else 5.0, np.nanmax(x) + 2.0, k_hi]
        popt, _ = curve_fit(model, x, y, p0=p0, bounds=(lo, hi), maxfev=40000)
        ceil, x0, k = float(popt[0]), float(popt[1]), float(popt[2])
        pred = model(x, ceil, x0, k)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return ceil, x0, k, rmse, int(len(x))
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0


def hill_params_unc(x, y, m_hi=5.0):
    """Hill fit with the response-max clamp LIFTED. Returns (m, x50, n, rmse, n)."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    msk = ~(np.isnan(x) | np.isnan(y))
    x, y = x[msk], y[msk]
    if len(x) < 60:
        return np.nan, np.nan, np.nan, np.nan, 0
    try:
        from scipy.optimize import curve_fit
        xs = x - np.nanmin(x) + 0.5
        def model(X, m, x50, n):
            return m * X ** n / (x50 ** n + X ** n)
        p0 = [np.nanmax(y), np.nanmedian(xs), 1.0]
        lo = [-3.0, 1e-3, 0.1]; hi = [m_hi, np.nanmax(xs) * 3 + 1, 20.0]
        popt, _ = curve_fit(model, xs, y, p0=p0, bounds=(lo, hi), maxfev=40000)
        m, x50, n = float(popt[0]), float(popt[1]), float(popt[2])
        pred = model(xs, m, x50, n)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return m, x50, n, rmse, int(len(x))
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0


def run_episodes(mask):
    """Contiguous-run intervals of a boolean mask. Returns list of (i0, i1) inclusive."""
    mask = np.asarray(mask, dtype=bool)
    out = []
    i = 0
    n = len(mask)
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


def concentration_episodes(state_arr, ent, p1, state, base_lo=0.33, min_len=5):
    """Episodes where a state's exit entropy falls into its lower tercile
    (crowding). Returns DataFrame rows per episode with duration, min/max p1,
    p1-p2 proxy (p1 only), and whether the state change within the next L days
    to a different state."""
    m = state_arr == state
    idx = np.where(m)[0]
    if len(idx) == 0:
        return pd.DataFrame()
    loq = np.nanquantile(ent[idx], base_lo)
    ep_mask = m & (ent <= loq)
    eps = run_episodes(ep_mask)
    rows = []
    nxt = np.where(np.isfinite(p1), 1 - np.asarray(p1), np.nan)  # fragmentation
    for (a, b) in eps:
        if (b - a + 1) < min_len:
            continue
        rows.append(dict(state=state, start=a, end=b, dur=(b - a + 1),
                         p1_mean=float(np.nanmean(p1[a:b + 1])),
                         p1_min=float(np.nanmin(p1[a:b + 1])),
                         p1_max=float(np.nanmax(p1[a:b + 1])),
                         frag_mean=float(np.nanmean(nxt[a:b + 1])) if np.isfinite(np.nanmean(nxt[a:b + 1])) else np.nan))
    return pd.DataFrame(rows)


def roll_node_deltas(node_df, patch_cols):
    """First-differences of rolling saturation nodes, aligned to time index.
    Returns df of deltas (index same as node_df)."""
    d = node_df[patch_cols].diff()
    return d


def r2(y, pred):
    y = np.asarray(y, dtype=float); pred = np.asarray(pred, dtype=float)
    m = np.isfinite(y) & np.isfinite(pred)
    if m.sum() < 20:
        return np.nan
    ss = np.sum((y[m] - y[m].mean()) ** 2)
    return float(1 - np.sum((y[m] - pred[m]) ** 2) / ss) if ss > 1e-12 else np.nan