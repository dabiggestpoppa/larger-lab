#!/usr/bin/env python
"""ALT_MECH_14 - precision/deepening checkpoint: MECH-13 repair, lifecycle
interaction geometry, initiation equifinality, age-residualized entropy,
waterfall validation, common-forcing model, directional constraint deepening,
disturbance->absorption->residual pilot.

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
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261401
BOOT_N = 300
PERM_N = 200
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_14/
M13_ROOT = ROOT.parent / "mech_13"
M12_ROOT = ROOT.parent / "mech_12"
OUT = ROOT

# Reuse MECH-13 base (which already pulls MECH-12 constants + loaders)
sys.path.insert(0, str(M13_ROOT / "scripts"))
import _m13base as M
# carry the M13 base module object under a stable name for constants/loaders
M13B = M

BRD_MED = M.BRD_MED
DISP_MED = M.DISP_MED
SUCCESS_LABELS = M.SUCCESS_LABELS
REENTRY_LABEL = M.REENTRY_LABEL
CELLS = M.CELLS
AGE_BANDS = M.AGE_BANDS
PERT_COLS = M.PERT_COLS
HORIZONS = M.HORIZONS
BANDS_COARSE = M.BANDS_COARSE
FINE_TO_COARSE = M.FINE_TO_COARSE
PATCHES = M.PATCHES
PATCH_LONER_BANDS = M.PATCH_LONER_BANDS
ATOMS = M.ATOMS
FAMILIES = M.FAMILIES
POTENTIAL_CHAIN = M.POTENTIAL_CHAIN
# INIT_COORDS is defined in M13's _m13p3; mirror it here for portability
INIT_COORDS = ["top500_breadth_30d", "top500_dispersion_30d", "top3_share",
               "rank_depth_rel", "vol_med", "btc_return_7d",
               "eth_btc_relative_return_7d"]
EVENT_COLS = M.EVENT_COLS
COORDS = M.COORDS
LAGS = M.LAGS
_age_band = M._age_band
_perturbation_flags = M._perturbation_flags
_atom_series = M._atom_series
_fmt = M._fmt
_perm_p = M._perm_p
_fdr = M._fdr
_entropy = M._entropy
_subperiod_split = M._subperiod_split
ACTIVATION_THRESH = 0.55
DEPTH_ORDER = ["26-100", "101-250", "251-500", "501-750", "751-1000",
               "1001-1500", "1501-2000"]

# loaders via MECH-13 base (chained to MECH-12)
load_dfw = M.load_dfw
load_ev = M.load_ev
load_health = M.load_health
load_band_panel = M.load_band_panel
load_loners = M.load_loners
load_lf6_consensus = M.load_lf6_consensus
load_lf6_peer_paths = M.load_lf6_peer_paths

# --- waterfall helpers (local; independent of M13 internals) ---
def _band_depth(bn):
    for i, co in enumerate(DEPTH_ORDER):
        if bn == co or FINE_TO_COARSE.get(bn) == co:
            return i
    return np.nan


def _activation_dates_per_band(band):
    """First activation day of each coarse-band episode (ppos>=thresh)."""
    recs = []
    for bn, g in band.groupby("band", observed=True):
        g = g.sort_values("d")
        act = (g["ppos"] >= ACTIVATION_THRESH) & \
            (g["ppos"].shift(1) < ACTIVATION_THRESH)
        for d in g[act]["d"]:
            recs.append({"band": bn, "d": d})
    return pd.DataFrame(recs)


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run14] {name} ...", flush=True)
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


def _auc_xy(x, y):
    """AUC treating x>=median as positive against binary y."""
    m = LogisticRegression(max_iter=1000).fit(
        np.asarray(x, dtype=float).reshape(-1, 1), y)
    return roc_auc_score(y, m.predict_proba(
        np.asarray(x, dtype=float).reshape(-1, 1))[:, 1])