#!/usr/bin/env python
"""ALT_MECH_15 - 16-cell market field matrix consolidation/formalization:
state x constraint surface, cell differentiation, collapse/merge search,
information retention, state-age overlay, forcing/threshold positioning,
directional entropy, rank recruitment, initiation archetype mix,
branch-closure geometry, Market-OS state surface candidate.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm, spearmanr
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261501
PERM_N = 200
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_15/
M14_ROOT = ROOT.parent / "mech_14"
M13_ROOT = ROOT.parent / "mech_13"
OUT = ROOT

# reuse MECH-14 base (chains to MECH-13 -> MECH-12 constants + loaders)
sys.path.insert(0, str(M14_ROOT / "scripts"))
import _m14base as M
M14B = M

CELLS = M.CELLS
SUCCESS_LABELS = M.SUCCESS_LABELS
REENTRY_LABEL = M.REENTRY_LABEL
AGE_BANDS = M.AGE_BANDS
PATCHES = M.PATCHES
FINE_TO_COARSE = M.FINE_TO_COARSE
EVENT_COLS = M.EVENT_COLS
ACTIVATION_THRESH = M.ACTIVATION_THRESH
DEPTH_ORDER = M.DEPTH_ORDER
FORCING_COLS = ["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
                "btc_return_7d", "stablecoin_change_7d", "top3_share"]

_age_band = M._age_band
_fdr = M._fdr
_entropy = M._entropy
_subperiod_split = M._subperiod_split
_fmt = M._fmt

load_dfw = M.load_dfw
load_ev = M.load_ev
load_band_panel = M.load_band_panel

# short codes for global states and constraint conditions
STATE_CODE = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
              "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}
CODE_STATE = {v: k for k, v in STATE_CODE.items()}
CONSTRAINT_CODES = ["HA_HE", "HA_LE", "LA_HE", "LA_LE"]
MC = []   # canonical 16-cell names in deterministic order
for st in ["HH", "HL", "LH", "LL"]:
    for cc in CONSTRAINT_CODES:
        MC.append(f"{st}_{cc}")


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run15] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _cohen_d(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) < 10 or len(b) < 10:
        return np.nan
    s = float(np.sqrt((np.var(a) + np.var(b)) / 2))
    return float((np.mean(a) - np.mean(b)) / s) if s > 0 else np.nan


def _ztest_prop(pa, na, pb, nb):
    """Two-proportion z-test (normal approx). Returns z, two-sided p."""
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


def _proportion_and_n(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan, 0
    return float(x.mean()), int(len(x))


def build_matrix_frame(dfw, band):
    """Per-day 16-cell frame. EXACT MECH-14 WS15 construction for the two
    constraint axes (age-residualized entropy is mandatory)."""
    from _m13p5 import _daily_patch_activation as _dpa
    act = _dpa(band)
    df = dfw.copy()
    df["d"] = pd.to_datetime(df["d"]).dt.normalize()
    df = df.set_index("d").join(act.rename("spatial_activation"), how="left")
    df["spatial_activation"] = df["spatial_activation"].fillna(0)
    df = df.reset_index()
    n = len(df)
    df["next_cell"] = df["cell"].shift(-1)
    cells_list = df["cell"].to_list()
    state_list = df["state"].to_list()
    # per-day forward branch entropy (7D next-cell distribution)
    fe = []
    for i in range(n):
        w = cells_list[i + 1:i + 8]
        if len(w) < 3:
            fe.append(np.nan)
            continue
        vc = pd.Series(w).value_counts(normalize=True)
        fe.append(float(-(vc * np.log2(vc)).sum()))
    df["fbe"] = fe
    df["ab"] = df["age_in_cell"].apply(_age_band)
    mean_fbe = df.groupby(["cell", "ab"])["fbe"].transform("mean")
    df["ent_resid"] = df["fbe"] - mean_fbe
    # axes (same thresholds as M14 WS15)
    df["spatial_ax"] = np.where(df["spatial_activation"] >= 3, "HA", "LA")
    df["temporal_ax"] = np.where(df["ent_resid"] >= 0, "HE", "LE")
    df["constraint"] = df["spatial_ax"] + "_" + df["temporal_ax"]
    df["state_code"] = df["cell"].map(STATE_CODE)
    df["mcell"] = df["state_code"] + "_" + df["constraint"]
    # next-day mcell (t+1 transition target)
    df["mcell_next"] = df["mcell"].shift(-1)
    # forward outcomes at 1/3/7/14D (state-based, future-separated)
    up_cols = ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
               "ev_ISOLATED_UPSIDE"]
    dn_cols = ["ev_ISOLATED_DOWNSIDE_EXTREME", "ev_LOCAL_CLUSTER_DOWNSIDE",
               "ev_COORDINATED_DOWNSIDE"]
    d2 = df.copy()
    d2["dir_today"] = np.sign(d2[up_cols].sum(axis=1) - d2[dn_cols].sum(axis=1))
    df["next_dir"] = d2["dir_today"].shift(-1)
    fwd = {"prop": {}, "ren": {}, "tail": {}, "rank": {}}
    for h in [1, 3, 7, 14]:
        fp = np.zeros(n); fr = np.zeros(n); ft = np.zeros(n); fk = np.zeros(n)
        for i in range(n - h):
            seg = pd.Series(state_list[i + 1:i + 1 + h])
            fp[i] = seg.isin(SUCCESS_LABELS).any()
            fr[i] = (seg == REENTRY_LABEL).any()
            seg_t = df.iloc[i + 1:i + 1 + h][[c for c in EVENT_COLS]]
            ft[i] = seg_t.sum().sum() > 0
            fk[i] = (df["rank_depth_rel_chg"].to_numpy()[i + 1:i + 1 + h]
                     > 0).any()
        fwd["prop"][h] = fp; fwd["ren"][h] = fr
        fwd["tail"][h] = ft; fwd["rank"][h] = fk
    for h in [1, 3, 7, 14]:
        df[f"prop{h}"] = fwd["prop"][h]
        df[f"ren{h}"] = fwd["ren"][h]
        df[f"tail{h}"] = fwd["tail"][h]
        df[f"rank{h}"] = fwd["rank"][h]
    # common forcing coordinate (PC1 of forcing cols, M14 WS13 style);
    # fit on complete rows only, NaN elsewhere
    forcing_cols = [c for c in FORCING_COLS if c in df.columns]
    sub = df[forcing_cols]
    comp_mask = sub.notna().all(axis=1)
    X = sub[comp_mask].to_numpy(dtype=float)
    df["forcing"] = np.nan
    if len(X) >= 100:
        sc = StandardScaler().fit(X)
        comp = PCA(n_components=1).fit(sc.transform(X))
        df.loc[comp_mask, "forcing"] = comp.transform(
            sc.transform(X)).ravel()
    # per-day initiation archetype (breadth/disp/macro medians, M14 WS22 style)
    brd_med = float(df["top500_breadth_30d"].median())
    disp_med = float(df["top500_dispersion_30d"].median())
    btc_med = float(df["btc_return_7d"].median())
    eth_med = float(df["eth_btc_relative_return_7d"].median())
    hi_brd = df["top500_breadth_30d"] >= brd_med
    hi_disp = df["top500_dispersion_30d"] >= disp_med
    hi_macro = (df["btc_return_7d"] >= btc_med) | (
        df["eth_btc_relative_return_7d"] >= eth_med)
    arch = np.where(hi_brd & hi_disp,
                    np.where(hi_macro, "BREADTH_DISPERSION_LED",
                             "BREADTH_LED"),
                    np.where(hi_macro & ~hi_brd, "MACRO_ANCHORED",
                             np.where(hi_disp, "DISPERSION_LED", "MIXED")))
    df["archetype"] = arch
    # family flags (directional families, M14 WS16 mapping)
    fam_map = {"BROAD_UP": ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"],
               "ISOLATED_UP": ["ev_ISOLATED_UPSIDE"],
               "LOCAL_CLUSTER_UP": [], "BROAD_DOWN": ["ev_COORDINATED_DOWNSIDE"],
               "ISOLATED_DOWN": ["ev_ISOLATED_DOWNSIDE_EXTREME",
                                 "ev_LOCAL_CLUSTER_DOWNSIDE"],
               "LOCAL_CLUSTER_DOWN": []}
    for fam, cols in fam_map.items():
        cols = [c for c in cols if c in df.columns]
        df[f"fam_{fam}"] = (df[cols].sum(axis=1) > 0).astype(int) if cols \
            else 0
    df["fam_broad_up"] = (df["ev_BAND_BROAD_UPSIDE"].fillna(0) +
                          df["ev_MULTI_BAND_UPSIDE"].fillna(0) > 0).astype(int)
    df["fam_broad_down"] = (df["ev_COORDINATED_DOWNSIDE"].fillna(0) > 0) \
        .astype(int)
    return df


def cell_stats(df, mcell):
    """Aggregate stats for one matrix cell (or any filtered subset)."""
    g = df[df["mcell"] == mcell] if mcell is not None else df
    if len(g) == 0:
        return None
    sp = g["subperiod"].replace("UNKNOWN", np.nan).dropna()
    nsp = int(sp.nunique()) if len(sp) else 0
    vc = sp.value_counts()
    max_share = float(vc.max() / vc.sum()) if len(vc) else np.nan
    row = {
        "mcell": mcell, "n_days": int(len(g)), "n_subperiods": nsp,
        "max_subperiod_share": max_share,
        "median_age": float(g["age_in_cell"].median()),
        "age_band_dist": ";".join(f"{k}:{v}" for k, v in
                                  g["ab"].value_counts().items()),
        "breadth": float(g["top500_breadth_30d"].mean()),
        "dispersion": float(g["top500_dispersion_30d"].mean()),
        "forcing": float(g["forcing"].mean()),
        "rank_depth_rel": float(g["rank_depth_rel"].mean()),
        "tail_share": float(g["tail7"].mean()),
        "rank_recruit": float(g["rank7"].mean()),
        "p_prop_1d": float(g["prop1"].mean()),
        "p_prop_3d": float(g["prop3"].mean()),
        "p_prop_7d": float(g["prop7"].mean()),
        "p_prop_14d": float(g["prop14"].mean()),
        "p_reentry_1d": float(g["ren1"].mean()),
        "p_reentry_3d": float(g["ren3"].mean()),
        "p_reentry_7d": float(g["ren7"].mean()),
        "p_reentry_14d": float(g["ren14"].mean()),
        "next_cell_entropy": float(_entropy(g["next_cell"].dropna())) if
        g["next_cell"].notna().sum() >= 20 else np.nan,
        "dir_entropy": float(_entropy(g["next_dir"].dropna())) if
        g["next_dir"].notna().sum() >= 20 else np.nan,
        "dominant_next_branch": str(g["next_cell"].dropna().mode().iloc[0])
        if g["next_cell"].dropna().nunique() else "",
        "p_up": float((g["next_dir"] > 0).mean()) if
        g["next_dir"].notna().any() else np.nan,
        "p_down": float((g["next_dir"] < 0).mean()) if
        g["next_dir"].notna().any() else np.nan,
        "p_broad_up": float(g["fam_broad_up"].mean()),
        "p_broad_down": float(g["fam_broad_down"].mean()),
    }
    return row
