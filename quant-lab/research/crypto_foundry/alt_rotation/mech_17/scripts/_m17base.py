#!/usr/bin/env python
"""ALT_MECH_17 - TRAFFIC LAW CARTOGRAPHY base module.

Loads the canonical daily field panel (MECH-16 frame) + rank-band surface,
derives the PIT-safe forcing families and traffic-law objects (demand,
capacity, congestion, exit pressure, transfer efficiency), and exposes small
fitting helpers reused by the MECH-17 orchestration.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

ROOT = Path(__file__).resolve().parents[1]            # mech_17/
M16_ROOT = ROOT.parent / "mech_16"
M15_ROOT = ROOT.parent / "mech_15"
OUT = ROOT

# reuse MECH-16 base (chains to mech_15 -> 14 -> 13 -> 12)
sys.path.insert(0, str(M16_ROOT / "scripts"))
import _m16base as M16

SUBPERIODS = M16.SUBPERIODS
DEPTH_ORDER = M16.DEPTH_ORDER
STATE_CODE = M16.STATE_CODE
_entropy = M16._entropy
_fdr = M16._fdr
_fmt = M16._fmt

# fine -> coarse patch map (DEPTH_ORDER start at 26, excludes 1-25)
FINE2PATCH = {
    "26-50": "26-100", "51-100": "26-100",
    "101-150": "101-250", "151-250": "101-250",
    "251-350": "251-500", "351-500": "251-500",
    "501-625": "501-750", "626-750": "501-750",
    "751-875": "751-1000", "876-1000": "751-1000",
    "1001-1500": "1001-1500", "1501-2000": "1501-2000",
}

W2022_LO, W2022_HI = "2022-02-16", "2022-04-17"


def load_frame():
    df = pickle.load(open(M16_ROOT / "_cache_frame16.pkl", "rb"))
    df["d"] = pd.to_datetime(df["d"]).dt.normalize()
    return df.sort_values("d").reset_index(drop=True)


def load_band():
    b = pickle.load(open(M16_ROOT / "_cache_band16.pkl", "rb"))
    b["d"] = pd.to_datetime(b["d"]).dt.normalize()
    return b


def _z(s):
    s = np.asarray(s, dtype=float)
    sd = np.nanstd(s)
    return (s - np.nanmean(s)) / sd if sd > 0 else s * 0.0


def forcing_families(df):
    """PIT-safe daily forcing family atlas (z-scored, descriptive)."""
    f = pd.DataFrame(index=df.index)
    f["d"] = df["d"]
    f["PARTICIPATION_FORCING"] = _z(0.5 * _z(df["breadth_vel"]) + 0.5 * _z(df["pos_ret_share"]))
    f["DISPERSION_FORCING"] = _z(df["top500_dispersion_7d"] - df["top500_dispersion_7d"].rolling(30, min_periods=20).mean())
    f["VOLATILITY_FORCING"] = _z(np.log1p(df["vol_med"]))
    f["BTC_ANCHOR_FORCING"] = _z(df["btc_return_7d"])
    f["ETH_RELATIVE_FORCING"] = _z(df["eth_btc_relative_return_7d"])
    f["RANK_RECRUITMENT_FORCING"] = _z(df["rank_depth_rel"])
    f["CONCENTRATION_RELEASE_FORCING"] = _z(-df["top3_share_chg7"])
    f["STABLECOIN_CAPITAL_FORCING"] = _z(df["stablecoin_change_7d"])
    f["PHYSICAL_DISTURBANCE_FORCING"] = _z(df["total_mcap_chg30"])
    f["COMMON_FORCING"] = df["forcing"].to_numpy()
    return f


def activation_surface(band):
    """Daily coarse-patch activation = mean ppos per DEPTH_ORDER patch,
    plus daily field activation = grand mean across patches."""
    b = band.copy()
    b = b[b["band"].astype(str).isin(FINE2PATCH)]
    b["patch"] = b["band"].astype(str).map(FINE2PATCH)
    act = b.groupby(["d", "patch"])["ppos"].mean().reset_index()
    wide = act.pivot(index="d", columns="patch", values="ppos")
    wide = wide.reindex(columns=DEPTH_ORDER)
    wide["FIELD"] = wide[DEPTH_ORDER].mean(axis=1)
    return wide


def close_event(s, thresh=1e-9):
    a = np.asarray(s, dtype=float)
    return a[~np.isnan(a)][(a > thresh) & (a < 1 - thresh)]


def logistic_params(x, y):
    """Fit y = ceiling / (1 + exp(-k*(x - x0))). Returns
    (ceiling, half_sat x0, slope k, train_rmse, n). Raises/gives NaN on fail."""
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
        lo = [-5.0, np.nanmin(x) - 2.0, -20.0]
        hi = [1.1, np.nanmax(x) + 2.0, 20.0]
        popt, _ = curve_fit(model, x, y, p0=p0, bounds=(lo, hi), maxfev=20000)
        ceil, x0, k = float(popt[0]), float(popt[1]), float(popt[2])
        pred = model(x, ceil, x0, k)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return ceil, x0, k, rmse, int(len(x))
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0


def hill_params(x, y):
    """Fit Hill: y = m * x**n / (x50**n + x**n). Offset-shift x to be > 0.
    Returns (m, x50, n, rmse, n)."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 60:
        return np.nan, np.nan, np.nan, np.nan, 0
    try:
        from scipy.optimize import curve_fit
        xs = x - np.nanmin(x) + 0.5
        def model(X, m, x50, n):
            return m * X ** n / (x50 ** n + X ** n)
        p0 = [np.nanmax(y), np.nanmedian(xs), 1.0]
        lo = [-3.0, 1e-3, 0.1]; hi = [1.1, np.nanmax(xs) * 3 + 1, 20.0]
        popt, _ = curve_fit(model, xs, y, p0=p0, bounds=(lo, hi), maxfev=20000)
        m, x50, n = float(popt[0]), float(popt[1]), float(popt[2])
        pred = model(xs, m, x50, n)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return m, x50, n, rmse, int(len(x))
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0


def patch_activation_daily(act, patch, on=0.55):
    """Daily binary activation >= on for a coarse patch."""
    x = act[patch]
    out = (x >= on).astype(float)
    return out
