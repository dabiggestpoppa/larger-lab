#!/usr/bin/env python
"""ALT_MECH_13 - Lifecycle Deepening, Initiation Geometry,
Constraint-Entropy Propagation, Waterfall Subtype Matrix, Patch Response
Curves, Metastability Recheck, Absolute x Sigma Shock Geometry, Full
Directional Asymmetry Map.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm, spearmanr, kendalltau
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261301
BOOT_N = 300
PERM_N = 200
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_13/
M12_ROOT = ROOT.parent / "mech_12"
OUT = ROOT

M12_SCRIPTS = M12_ROOT / "scripts"
sys.path.insert(0, str(M12_SCRIPTS))
import alt_mech_12_analysis as M12

# ---- reuse MECH-12 constants & helpers ----
BRD_MED = M12.BRD_MED
DISP_MED = M12.DISP_MED
SUCCESS_LABELS = M12.SUCCESS_LABELS
REENTRY_LABEL = M12.REENTRY_LABEL
CELLS = M12.CELLS
AGE_BANDS = M12.AGE_BANDS
PERT_COLS = M12.PERT_COLS
HORIZONS = M12.HORIZONS
BANDS_COARSE = M12.BANDS_COARSE
FINE_TO_COARSE = M12.FINE_TO_COARSE
PATCHES = M12.PATCHES
PATCH_LONER_BANDS = M12.PATCH_LONER_BANDS
ATOMS = M12.ATOMS
FAMILIES = M12.FAMILIES
POTENTIAL_CHAIN = M12.POTENTIAL_CHAIN
_age_band = M12._age_band
_perturbation_flags = M12._perturbation_flags
_atom_series = M12._atom_series
_fmt = M12._fmt
_perm_p = M12._perm_p
_fdr = M12._fdr

EVENT_COLS = M12.EVENT_COLS

# loaders
load_dfw = M12.load_dfw
load_ev = M12.load_ev
load_health = M12.load_health
load_band_panel = M12.load_band_panel
load_loners = M12.load_loners
load_lf6_consensus = M12.load_lf6_consensus
load_lf6_peer_paths = M12.load_lf6_peer_paths

# WS2 failure-geometry coordinate/coordinate lag helpers reused for WS3
COORDS = M12.COORDS
LAGS = M12.LAGS


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run13] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _entropy(series):
    """Shannon entropy (bits) of a categorical value series."""
    vc = series.value_counts(normalize=True)
    return float(-(vc * np.log2(vc)).sum())


def _subperiod_split(df):
    """Return list of (subperiod, indices) for leave-one-out runs."""
    sp = df["subperiod"].to_numpy()
    groups = {}
    for i, s in enumerate(sp):
        groups.setdefault(s, []).append(i)
    return list(groups.items())