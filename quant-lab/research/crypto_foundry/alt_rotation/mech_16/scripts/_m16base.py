#!/usr/bin/env python
"""ALT_MECH_16 - state-surface drift checkpoint: topology vs transfer-function
stability, 6-cell vs 8-cell representation, conditional law change,
common-forcing transportability, state x age hazard drift, entropy / branch
closure stability, rank-recruitment law, birth-geometry transport, field-law
changepoints, Market-OS surface freeze audit.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm, spearmanr, ttest_ind
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261601
ROLL_WIN = 365
ROLL_STEP = 30
FDR_Q = 0.10
MIN_SEG_N = 50

ROOT = Path(__file__).resolve().parents[1]            # mech_16/
M15_ROOT = ROOT.parent / "mech_15"
M14_ROOT = ROOT.parent / "mech_14"
OUT = ROOT

# reuse MECH-15 base (chains to MECH-14 -> MECH-13 -> MECH-12)
sys.path.insert(0, str(M15_ROOT / "scripts"))
import _m15base as M15
from _m15p2 import ws6_partition_at

MC = M15.MC
STATE_CODE = M15.STATE_CODE
AGE_BANDS = M15.AGE_BANDS
DEPTH_ORDER = M15.DEPTH_ORDER
SUCCESS_LABELS = M15.SUCCESS_LABELS
REENTRY_LABEL = M15.REENTRY_LABEL
_age_band = M15._age_band
_fdr = M15._fdr
_entropy = M15._entropy
_fmt = M15._fmt
_subperiod_split = M15._subperiod_split
_cell_dist = None  # not needed

SUBPERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]
AGE_BAND_ORDER = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run16] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _js_distance(p, q):
    """Jensen-Shannon distance in [0,1] between two distributions given as
    pandas Series (values) or dict-like (counts/probabilities). Aligned on
    the union of categories."""
    if isinstance(p, pd.Series):
        p = p.value_counts(normalize=True)
        q = q.value_counts(normalize=True)
    keys = sorted(set(p.index) | set(q.index))
    a = np.array([float(p.get(k, 0.0)) for k in keys])
    b = np.array([float(q.get(k, 0.0)) for k in keys])
    sa, sb = a.sum(), b.sum()
    a = a / sa if sa > 0 else a
    b = b / sb if sb > 0 else b
    m = 0.5 * (a + b)
    def _kl(x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        mk = x > 0
        return float(np.sum(x[mk] * np.log2(x[mk] / np.maximum(y[mk],
                                                              1e-12))))
    return float(np.sqrt(0.5 * (_kl(a, b) + _kl(b, a))))


def _ztest_prop(pa, na, pb, nb):
    pa, pb = float(pa), float(pb)
    na, nb = int(na), int(nb)
    if na < 10 or nb < 10:
        return np.nan, np.nan
    p = (pa * na + pb * nb) / (na + nb)
    if p <= 0 or p >= 1:
        return np.nan, np.nan
    se = np.sqrt(p * (1 - p) * (1 / na + 1 / nb))
    if se == 0:
        return np.nan, np.nan
    z = (pa - pb) / se
    return z, 2 * norm.sf(abs(z))


def _cohen_d(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) < 10 or len(b) < 10:
        return np.nan
    s = float(np.sqrt((np.var(a) + np.var(b)) / 2))
    return float((np.mean(a) - np.mean(b)) / s) if s > 0 else np.nan


def _slope_std(x, y):
    """Standardized binned slope: mean y within x-terciles, OLS slope of the
    tercile means vs z-scored x-centers. Returns slope (per 1 SD of x)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 50:
        return np.nan, 0
    try:
        q = np.quantile(x, [1 / 3, 2 / 3])
        bins = np.digitize(x, q)
        xs = (x - x.mean()) / (x.std() + 1e-12)
        cents = np.array([xs[bins == k].mean() if (bins == k).sum() else np.nan
                          for k in [0, 1, 2]])
        means = np.array([y[bins == k].mean() if (bins == k).sum() else np.nan
                          for k in [0, 1, 2]])
        m2 = ~np.isnan(cents) & ~np.isnan(means)
        if m2.sum() < 2:
            return np.nan, 0
        c = np.polyfit(cents[m2], means[m2], 1)
        return float(c[0]), int(len(x))
    except Exception:
        return np.nan, 0


def _logit_slope(x, y):
    """Logistic regression slope of y on z-scored x (per 1 SD)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 50 or y.sum() < 5 or (1 - y).sum() < 5:
        return np.nan, 0
    try:
        xs = (x - x.mean()) / (x.std() + 1e-12)
        clf = LogisticRegression(max_iter=1000).fit(xs.reshape(-1, 1), y)
        return float(clf.coef_[0][0]), int(len(x))
    except Exception:
        return np.nan, 0


def _rolling_series(df, col, group=None, win=ROLL_WIN):
    """Chronological rolling mean of col (optionally within group), returned
    aligned to df index (NaN where support < 50 obs)."""
    df = df.sort_values("d")
    out = pd.Series(np.nan, index=df.index)
    vals = df[col].to_numpy(dtype=float)
    g = df[group].to_numpy() if group else None
    dts = df["d"].to_numpy()
    for i in range(len(df)):
        lo = max(0, i - win + 1)
        seg = vals[lo:i + 1]
        if g is not None:
            seg = seg[g[lo:i + 1] == g[i]]
        seg = seg[~np.isnan(seg)]
        if len(seg) >= 50:
            out.iloc[i] = float(np.mean(seg))
    return out


def load_frame15():
    """Per-day 16-cell frame exactly as built by MECH-15 (cache exists)."""
    p = M15_ROOT / "_cache_frame15.pkl"
    if not p.exists():
        raise FileNotFoundError(f"MECH-15 frame cache missing: {p}")
    with open(p, "rb") as fh:
        df = pickle.load(fh)
    return df.reset_index(drop=True)


def load_band15():
    p = M15_ROOT / "_cache_band15.pkl"
    if not p.exists():
        raise FileNotFoundError(f"MECH-15 band cache missing: {p}")
    with open(p, "rb") as fh:
        return pickle.load(fh)


def load_ev15():
    p = M15_ROOT / "_cache_ev15.pkl"
    if not p.exists():
        raise FileNotFoundError(f"MECH-15 ev cache missing: {p}")
    with open(p, "rb") as fh:
        return pickle.load(fh)


def build_surfaces(df):
    """Attach group labels for all five surfaces + derived helpers.

    grp16 = mcell; grp8/grp6/grp4 = deterministic average-linkage cuts;
    grp4s = global state. Deterministic replay of MECH-15 WS5/6.
    """
    df = df.copy()
    n = len(df)
    df["grp16"] = df["mcell"]
    df["grp4s"] = df["state_code"]
    for nc in [8, 6, 4]:
        part = ws6_partition_at(df, MC, nc)
        m2g = {}
        for gi, grp in enumerate(part):
            for mi in grp:
                m2g[MC[mi]] = f"{nc}C_{gi}"
        df[f"grp{nc}"] = df["mcell"].map(m2g)
    # forward branch count (distinct next-cells in next 7 days)
    cells = df["cell"].to_list()
    nb = np.full(n, np.nan)
    for i in range(n - 1):
        w = cells[i + 1:min(i + 8, n)]
        nb[i] = len(set(w)) if len(w) >= 3 else np.nan
    df["nbranch7"] = nb
    # next-group columns (t+1) for each surface
    for c in ["grp16", "grp8", "grp6", "grp4", "grp4s"]:
        df[c + "_next"] = df[c].shift(-1)
    # entropy tier and activation tier (for WS15 chain)
    df["ent_tier"] = np.where(df["ent_resid"] >= 0, "HE", "LE")
    df["act_tier"] = df["spatial_ax"]
    # forcing tercile
    q = df["forcing"].quantile([1 / 3, 2 / 3])
    df["f_tier"] = np.select(
        [df["forcing"] <= q.iloc[0], df["forcing"] <= q.iloc[1]],
        ["F1", "F2"], "F3")
    return df


def patch_activation_daily(band):
    """Per-day activation flag per coarse depth band (max ppos >= 0.55)."""
    b = band.copy()
    b["d"] = pd.to_datetime(b["d"]).dt.normalize()
    b = b[b["band"].isin(DEPTH_ORDER)]
    act = b.groupby(["d", "band"])["ppos"].max().reset_index()
    act["active"] = (act["ppos"] >= 0.55).astype(int)
    wide = act.pivot(index="d", columns="band", values="active")
    wide = wide.reindex(columns=DEPTH_ORDER)
    return wide.fillna(0)


def forcing_threshold_per_patch(pact, forcing, patch, prob=0.5, min_n=80):
    """Forcing level at which activation probability reaches `prob`, from a
    logistic fit. Returns (threshold, slope, n, ceiling) or NaNs.
    `forcing` must be a Series with DatetimeIndex so pact aligns by date."""
    x = forcing.to_numpy(dtype=float)
    if isinstance(forcing.index, pd.DatetimeIndex):
        y = pact.reindex(forcing.index)[patch].to_numpy(dtype=float)
    else:
        y = pact[patch].to_numpy(dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < min_n or y.sum() < 10 or (1 - y).sum() < 10:
        return np.nan, np.nan, 0, np.nan
    xs = (x - x.mean()) / (x.std() + 1e-12)
    try:
        clf = LogisticRegression(max_iter=1000).fit(xs.reshape(-1, 1), y)
        b0, b1 = float(clf.intercept_[0]), float(clf.coef_[0][0])
        thr = x.mean() + (np.log(prob / (1 - prob)) - b0) / (b1 + 1e-12) * \
            (x.std() + 1e-12)
        # ceiling: mean activation in top decile of forcing
        top = y[x >= np.quantile(x, 0.9)]
        ceiling = float(top.mean()) if len(top) >= 10 else np.nan
        return float(thr), float(b1), int(len(x)), ceiling
    except Exception:
        return np.nan, np.nan, 0, np.nan


def period_slices(df, mode):
    """Return list of (name, index-mask) for a period mode."""
    if mode == "subperiod":
        out = []
        for sp in SUBPERIODS:
            m = df["subperiod"] == sp
            if m.sum() >= MIN_SEG_N:
                out.append((sp, m))
        return out
    if mode == "halves":
        d = df.sort_values("d").reset_index(drop=True)
        half = len(d) // 2
        return [("early_half", d.index < half), ("late_half", d.index >= half)]
    if mode == "chrono80":
        d = df.sort_values("d").reset_index(drop=True)
        cut = int(0.8 * len(d))
        return [("early_80", d.index < cut), ("late_20", d.index >= cut)]
    raise ValueError(mode)


def group_order_profile(df, group_col, metric, min_n=30):
    """Per-group scalar for ordering comparisons. Returns dict group->value.
    metric in prop/ren/rank/tail/branch_entropy/dir_entropy/self_transition.
    """
    out = {}
    for g, sub in df.groupby(group_col):
        if len(sub) < min_n:
            continue
        if metric == "prop":
            out[g] = float(sub["prop7"].mean())
        elif metric == "ren":
            out[g] = float(sub["ren7"].mean())
        elif metric == "rank":
            out[g] = float(sub["rank7"].mean())
        elif metric == "tail":
            out[g] = float(sub["tail7"].mean())
        elif metric == "branch_entropy":
            v = sub["fbe"].dropna()
            out[g] = float(v.mean()) if len(v) >= 20 else None
        elif metric == "dir_entropy":
            v = sub["next_dir"].dropna()
            out[g] = float(_entropy(v)) if len(v) >= 20 else None
        elif metric == "self_transition":
            v = sub[[group_col, group_col + "_next"]].dropna()
            if len(v) >= 20:
                out[g] = float((v[group_col] == v[group_col + "_next"]).mean())
            else:
                out[g] = None
        elif metric == "modal_exit":
            v = sub[[group_col, group_col + "_next"]].dropna()
            if len(v) >= 20:
                out[g] = float(v[group_col + "_next"].value_counts(
                    normalize=True).iloc[0])
            else:
                out[g] = None
    return {k: v for k, v in out.items() if v is not None}


def rank_order_rho(p1, p2):
    ks = [k for k in p1 if k in p2]
    if len(ks) < 3:
        return np.nan, len(ks)
    a = np.array([p1[k] for k in ks], dtype=float)
    b = np.array([p2[k] for k in ks], dtype=float)
    return float(spearmanr(a, b)[0]), len(ks)


SURFACE_GROUP_COLS = {"16_cell": "grp16", "8_cell": "grp8", "6_cell": "grp6",
                      "4_cell": "grp4", "4_state": "grp4s"}
ORDERING_METRICS = ["prop", "ren", "dir_entropy", "rank", "self_transition",
                    "branch_entropy"]
