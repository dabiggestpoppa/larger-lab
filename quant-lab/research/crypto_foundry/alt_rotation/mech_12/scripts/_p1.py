#!/usr/bin/env python
"""ALT_MECH_12 - Full State Lifecycle Physics, Broad Sequence Search,
Partial-Order Constraint Graph, Rank-Patch Threshold Hierarchy,
Peer-Formation Context, Constraint-Resolution Entropy & Light Metastability
Audit.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm, spearmanr
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261201
BOOT_N = 300
PERM_N = 200
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_12/
M11_ROOT = ROOT.parent / "mech_11"
M10_ROOT = ROOT.parent / "mech_10"
M9_ROOT = ROOT.parent / "mech_9"
OUT = ROOT

M10_SCRIPTS = M10_ROOT / "scripts"
sys.path.insert(0, str(M10_SCRIPTS))
import alt_mech_10_analysis as M10

BRD_MED = M10.BRD_MED
DISP_MED = M10.DISP_MED
SUCCESS_LABELS = M10.SUCCESS_LABELS
REENTRY_LABEL = M10.REENTRY_LABEL
CELLS = M10.CELLS
AGE_BANDS = M10.AGE_BANDS
PERT_COLS = M10.PERT_COLS
_age_band = M10._age_band
_perturbation_flags = M10._perturbation_flags

HORIZONS = [1, 2, 3, 5, 7, 10, 14, 21, 30]
BANDS_COARSE = ["26-100", "101-250", "251-500", "501-750",
                "751-1000", "1001-1500", "1501-2000"]
FINE_TO_COARSE = {"26-50": "26-100", "51-100": "26-100",
                  "101-150": "101-250", "151-250": "101-250",
                  "251-350": "251-500", "351-500": "251-500",
                  "501-625": "501-750", "626-750": "501-750",
                  "751-875": "751-1000", "876-1000": "751-1000",
                  "1001-1500": "1001-1500", "1501-2000": "1501-2000"}
PATCHES = {"UPPER_CORE": ["26-50", "51-100"],
           "UPPER_MID": ["101-150", "151-250"],
           "MID": ["251-350", "351-500"],
           "LOWER_MID": ["501-625", "626-750"],
           "TRANSITION": ["751-875", "876-1000"]}
PATCH_LONER_BANDS = {"UPPER_CORE": ["26-100"], "UPPER_MID": ["101-250"],
                     "MID": ["251-500"], "LOWER_MID": ["501-750"],
                     "TRANSITION": ["751-1000"]}
ATOMS = ["BREADTH_EXPANDS", "BREADTH_CONTRACTS", "CONCENTRATION_RELEASES",
         "CONCENTRATION_REBUILDS", "DISPERSION_EXPANDS",
         "DISPERSION_CONTRACTS", "TAIL_UP_ACTIVATES", "TAIL_DOWN_ACTIVATES",
         "RANK_RECRUITS", "RANK_DECAYS", "VOL_EXPANDS", "VOL_CONTRACTS",
         "STABLECOIN_ACTIVITY_UP", "TVL_VELOCITY_UP", "STATE_EXIT",
         "STATE_REENTRY", "PROPAGATION_CONFIRMS"]
LF6_ROOT = Path(r"C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab"
                r"\research\crypto_foundry\derivatives\lower_field_6")


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _perm_p(k, B):
    return (k + 1) / (B + 1)


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.{nd}f}"


def _fdr(p):
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    q = np.full(len(p), np.nan)
    if mask.any():
        q[mask] = multipletests(p[mask], method="fdr_bh")[1]
    return q


# =========================================================================
# LOADERS - reuse MECH-9/10/11 cached artifacts (memory-safe)
# =========================================================================

def load_dfw():
    with open(M9_ROOT / "_cache_dfw.pkl", "rb") as fh:
        df = pickle.load(fh)
    df = df.reset_index(drop=True)
    df["subperiod"] = df["subperiod"].fillna("UNKNOWN")
    return df


def load_ev():
    with open(M9_ROOT / "_cache_ev.pkl", "rb") as fh:
        return pickle.load(fh)


def load_health():
    with open(M9_ROOT / "_cache_health.pkl", "rb") as fh:
        return pickle.load(fh)


def load_band_panel():
    with open(M11_ROOT / "_cache_bandpanel.pkl", "rb") as fh:
        return pickle.load(fh)


def load_loners():
    with open(M11_ROOT / "_cache_loners.pkl", "rb") as fh:
        return pickle.load(fh)


def load_lf6_consensus():
    """LF6 consensus loner classes by event_index."""
    df = pd.read_csv(LF6_ROOT / "03_CONSENSUS_LONER_CLASSIFICATION.csv",
                     usecols=["event_index", "final_class"])
    df["loner3"] = np.where(
        df["final_class"] == "TRUE_MULTI_PEER_LONER", "TRUE_LONER",
        np.where(df["final_class"] == "AMBIGUOUS", "AMBIGUOUS",
                 "FALSE_LONER"))
    return df


def load_lf6_peer_paths():
    """LF6 event-level peer rejoin/catchdown path context."""
    df = pd.read_csv(LF6_ROOT / "10_PEER_REJOIN_CATCHDOWN.csv",
                     usecols=["event_index", "historical_date", "path_class",
                              "peer_n", "resid1", "resid7", "resid14"])
    df["d"] = pd.to_datetime(df["historical_date"]).dt.normalize()
    return df


def _fwd_window_flags(df, col, horizons):
    """For daily 0/1 column, any event within next h days for each h."""
    out = {}
    n = len(df)
    vals = df[col].to_numpy(dtype=float)
    for h in horizons:
        w = np.zeros(n)
        for i in range(n):
            j = i + h
            if j > n:
                continue
            w[i] = vals[i + 1:j].sum() > 0
        out[h] = w
    return out


def _atom_series(df):
    """Daily 0/1 atom flags (first-appearance order target)."""
    d = df.copy()
    brd = d["top500_breadth_30d"]
    brd_v = brd.diff().fillna(0)
    disp = d["top500_dispersion_30d"]
    disp_v = disp.diff().fillna(0)
    conc_v = d["top3_share_chg7"].fillna(0)
    rank_v = d["rank_depth_rel_chg"].fillna(0)
    vol_v = d["vol_med"].diff().fillna(0)
    tail_up = (d[["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"]]
               .sum(axis=1) > 0).astype(int)
    tail_dn = (d[["ev_ISOLATED_DOWNSIDE_EXTREME",
                  "ev_LOCAL_CLUSTER_DOWNSIDE"]].sum(axis=1) > 0).astype(int)
    out = pd.DataFrame({
        "BREADTH_EXPANDS": (brd_v > 0).astype(int),
        "BREADTH_CONTRACTS": (brd_v < 0).astype(int),
        "CONCENTRATION_RELEASES": (conc_v < 0).astype(int),
        "CONCENTRATION_REBUILDS": (conc_v > 0).astype(int),
        "DISPERSION_EXPANDS": (disp_v > 0).astype(int),
        "DISPERSION_CONTRACTS": (disp_v < 0).astype(int),
        "TAIL_UP_ACTIVATES": tail_up,
        "TAIL_DOWN_ACTIVATES": tail_dn,
        "RANK_RECRUITS": (rank_v > 0).astype(int),
        "RANK_DECAYS": (rank_v < 0).astype(int),
        "VOL_EXPANDS": (vol_v > 0).astype(int),
        "VOL_CONTRACTS": (vol_v < 0).astype(int),
        "STABLECOIN_ACTIVITY_UP": (d["stablecoin_change_7d"].fillna(0)
                                   > 0).astype(int),
        "TVL_VELOCITY_UP": (d["chain_tvl_med_chg7"].fillna(0) > 0).astype(int),
        "STATE_EXIT": (d["cell"] != d["cell"].shift(1)).fillna(False)
                      .astype(int),
        "STATE_REENTRY": (d["state"] == REENTRY_LABEL).astype(int),
        "PROPAGATION_CONFIRMS": d["state"].isin(SUCCESS_LABELS).astype(int),
    }, index=d.index)
    return out
