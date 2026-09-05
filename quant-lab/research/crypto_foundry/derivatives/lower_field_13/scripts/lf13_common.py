"""LOWER-FIELD-13 shared frame builders and temporal protocol.

LF13 is NOT a new discovery sweep: it finalizes the local-law layer
(capacity dependency structure, contagion mechanism relations, sign-asymmetry
localization, decoupling placement) under a MANDATORY STATIC + ROLLING
temporal protocol, then decides whether the local ontology can stop evolving.

This module loads the LF12 master frame (cached) and adds:

- the STATIC + ROLLING temporal protocol helpers used by every temporal object
- capacity-family coordinate normalization (for the dependency matrix and
  core-coordinate compression)
- contagion mechanism-surface inputs (shock magnitude x recency x early reach)
- stage outcome flags (absorption / propagation / containment / reactivation /
  decoupling) used by the sign-asymmetry-by-stage analysis

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_12" / "scripts"))
import lf12_common as W12  # noqa: E402
import lf9_common as C9      # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_13/
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

A = C9.A
_fmt = A._fmt
_med = C9._med
_mean = C9._mean
_purged_auc = A._purged_auc
MIN_SUPPORT = C9.MIN_SUPPORT

SUB_PERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]

STATIC_HORIZONS = {"1D": 1, "3D": 3, "7D": 7, "14D": 14, "30D": 30, "60D": 60}
ROLLING_WINDOWS = {"3D": 3, "7D": 7, "14D": 14, "30D": 30}


# ---------------------------------------------------------------------------
# Base frame
# ---------------------------------------------------------------------------

def base_frame(use_cache: bool = True) -> pd.DataFrame:
    return W12.master_frame(use_cache=True)


# ---------------------------------------------------------------------------
# Capacity family coordinates (normalized, for dependency / compression)
# ---------------------------------------------------------------------------

def capacity_coordinates(snap: pd.DataFrame) -> pd.DataFrame:
    """Five capacity-family coordinates, normalized to [0,1] where higher =
    stronger/more capacity. RECOVERY uses recovery_index (0=disturbed)."""
    d = snap.copy()
    d["cap_structural"] = d["struct_integrity"].rank(pct=True)
    d["cap_liquidity"] = d["liq_proxy"].rank(pct=True)
    # rank health: lower rank number = better; invert so higher = healthier
    d["cap_rankhealth"] = (1.0 - d["rank"].rank(pct=True))
    # peer_stress is near-constant (2 unique) -> use peer dispersion as the
    # stress coordinate instead so the family matrix is not degenerate
    d["cap_stress"] = (1.0 - d["peer_dispersion"].rank(pct=True)) if "peer_dispersion" in d.columns else (1.0 - d["peer_stress"].rank(pct=True))
    d["cap_recovery"] = d["recovery_index"].clip(0, 1).rank(pct=True)
    return d


# ---------------------------------------------------------------------------
# Stage outcome flags (sign-asymmetry-by-stage and 2x2 analyses)
# ---------------------------------------------------------------------------

def stage_flags(snap: pd.DataFrame) -> pd.DataFrame:
    """Stage outcomes for each event: ABSORPTION / PROPAGATION / CONTAINMENT /
    REACTIVATION / DECOUPLING. Containment is defined descriptively as:
    event propagated (out_contagion==1) but did NOT decouple within 30d."""
    d = snap.copy()
    d["stg_absorption"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["stg_reorganization"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["stg_propagation"] = d["out_contagion"].fillna(0).astype(int)
    d["stg_containment"] = ((d["out_contagion"].fillna(0) == 1) & (d["out_decouple"].fillna(0) == 0)).astype(int)
    d["stg_reactivation"] = d["out_relapse"].fillna(0).astype(int)
    d["stg_decoupling"] = d["out_decouple"].fillna(0).astype(int)
    d["stg_rejoin"] = d["out_rejoin"].fillna(0).astype(int)
    return d


# ---------------------------------------------------------------------------
# Contagion mechanism-surface coordinates (section 14)
# ---------------------------------------------------------------------------

def mechanism_coordinates(snap: pd.DataFrame) -> pd.DataFrame:
    """Continuous mechanism coordinates for contagion events:
    SHOCK_MAGNITUDE (abs_ret), RECENCY (days since prior, inverted so higher =
    more recent), EARLY_REACH (peer negative fraction at 1d)."""
    d = snap.copy()
    d["mech_shock_mag"] = d["abs_ret"]
    d["mech_recency"] = np.clip(1.0 / (1.0 + d["days_since_prior"].fillna(365)), 0, 1)
    d["mech_early_reach"] = d["peer_neg_frac1"].fillna(0)
    d["mech_latency"] = d["latency_T1"].fillna(np.nan)
    d["mech_radius"] = d["radius_T7"].fillna(np.nan)
    d["mech_peak_time"] = d["peak_time_T3"].fillna(np.nan)
    d["mech_persist"] = d["persistence_T30"].fillna(np.nan)
    d["mech_decay"] = d["CONT_DECAY"].fillna(np.nan)
    return d


# ---------------------------------------------------------------------------
# Temporal contagion species (carried forward from LF12 geometry)
# ---------------------------------------------------------------------------

def temporal_species(snap: pd.DataFrame, seed: int = 2026) -> pd.DataFrame:
    """Carry the LF12 temporal-species geometry forward: re-cluster contagion
    events on the same feature set / seed, then NAME clusters by their tempo
    (latency / peak time) instead of numeric labels. Only used for
    organization — the mission forbids new species hunting."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    d = snap.copy()
    d["temp_species"] = "NON_CONTAGION"
    cont = d[d["out_contagion"] == 1].copy()
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    avail = [f for f in feats if f in cont.columns]
    csub = cont.dropna(subset=avail).copy()
    if len(csub) < 100:
        return d
    X = csub[avail].to_numpy(dtype=float)
    Z = StandardScaler().fit_transform(X)
    best = {"k": 1, "sil": -2}
    for k in range(2, 6):
        km = KMeans(n_clusters=k, n_init=8, random_state=seed)
        y = km.fit_predict(Z)
        if (np.bincount(y) < 15).any():
            continue
        s = float(silhouette_score(Z, y))
        if s > best["sil"]:
            best = {"k": k, "sil": s}
    k = max(best["k"], 2)
    km = KMeans(n_clusters=k, n_init=8, random_state=seed)
    labs = km.fit_predict(Z)
    csub = csub.copy()
    csub["_lab"] = labs
    # name clusters by tempo: latency and peak time
    names = {}
    order = csub.groupby("_lab")[["latency_T1", "peak_time_T3"]].median()\
                .sort_values(["latency_T1", "peak_time_T3"]).index
    for i, lab in enumerate(order):
        if i == 0:
            names[lab] = "FAST"
        elif i == 1:
            names[lab] = "MEDIUM"
        elif i == 2:
            names[lab] = "SLOW"
        else:
            names[lab] = "PERSISTENT"
    csub["temp_species"] = csub["_lab"].map(names)
    d.loc[csub.index, "temp_species"] = csub["temp_species"]
    return d


# ---------------------------------------------------------------------------
# STATIC + ROLLING temporal protocol
# ---------------------------------------------------------------------------

# Static-horizon columns available in the LF12 frame (forward-looking measures
# at fixed horizons). ROLLING counterparts are computed as trailing
# market-level means over the same horizon (see rolling_protocol).
STATIC_MAP = {
    "1D": {
        "peer_neg_frac1": "peer_neg_frac1",
        "peer_touch_frac1": "peer_touch_frac1",
        "fwd_ret": "signed_fwd1",
        "fwd_rank_vel": "fwd_rank_vel_1d",
        "fwd_abs": "fwd1_cum",
    },
    "3D": {
        "peer_neg_frac3": "peer_neg_frac3",
        "peer_touch_frac3": "peer_touch_frac3",
        "fwd_ret": "signed_fwd3",
        "fwd_rank_vel": "fwd_rank_vel_3d",
        "fwd_abs": "fwd3_cum",
    },
    "7D": {
        "peer_neg_frac7": "peer_neg_frac7",
        "peer_touch_frac7": "peer_touch_frac7",
        "fwd_ret": "signed_fwd7",
        "fwd_rank_vel": "fwd_rank_vel_7d",
        "fwd_abs": "fwd7_cum",
    },
    "14D": {
        "peer_neg_frac14": "peer_neg_frac14",
        "peer_touch_frac14": "peer_touch_frac14",
        "fwd_ret": "signed_fwd14",
        "fwd_rank_vel": "fwd_rank_vel_14d",
        "fwd_abs": "fwd14_cum",
    },
    "30D": {
        "peer_neg_frac30": "peer_neg_frac30",
        "peer_touch_frac30": "peer_touch_frac30",
        "fwd_ret": "signed_fwd30",
        "fwd_rank_vel": "fwd_rank_vel_30d",
        "fwd_abs": "fwd30_cum",
    },
    "60D": {
        "peer_neg_frac60": None,          # not in LF12 frame -> NaN
        "peer_touch_frac60": None,
        "fwd_ret": None,                  # not in LF12 frame -> NaN
        "fwd_rank_vel": None,
        "fwd_abs": None,
    },
}


def static_horizons(snap: pd.DataFrame, measure: str) -> pd.Series:
    """Return a DataFrame of static-horizon values for one measure
    (peer_neg_frac / peer_touch_frac / fwd_ret / fwd_rank_vel / fwd_abs)
    across the six static horizons. Missing horizons -> NaN (reported, not
    silently dropped)."""
    out = {}
    for h in ["1D", "3D", "7D", "14D", "30D", "60D"]:
        col = STATIC_MAP[h].get(measure)
        if col is None or col not in snap.columns:
            out[h] = np.nan
        else:
            out[h] = snap[col]
    return pd.DataFrame(out)


def rolling_protocol(snap: pd.DataFrame) -> pd.DataFrame:
    """Compute trailing ROLLING market-level means (3/7/14/30d) of the key
    temporal measures at each event date, using only PAST events. Returns a
    DataFrame indexed like snap with columns roll_<measure>_<horizon>."""
    d = snap.copy()
    d = d.sort_values("historical_date")
    dts = d["historical_date"]
    # per-date means of the measures (market level)
    base_measures = {
        "peer_neg_frac": "peer_neg_frac1",
        "peer_touch_frac": "peer_touch_frac1",
        "fwd_ret": "signed_fwd1",
        "fwd_rank_vel": "fwd_rank_vel_1d",
        "fwd_abs": "fwd1_cum",
    }
    agg = d.groupby(dts).agg(**{f"m_{k}": (v, "mean") for k, v in base_measures.items()})
    agg = agg.sort_index()
    for hname, hd in ROLLING_WINDOWS.items():
        # trailing window mean over [t-hd, t] EXCLUDING current day's events
        # is complex; use rolling with closed='left' on the per-date series to
        # keep the protocol PIT-safe (only past dates feed the window).
        roll = agg.rolling(window=hd, closed="left", min_periods=1).mean()
        for k in base_measures:
            d[f"roll_{k}_{hname}"] = dts.map(roll[f"m_{k}"])
    return d


def temporal_row(label: str, static: dict, rolling: dict, subperiods: dict,
                 verdict: str = "", note: str = "") -> dict:
    """One standardized temporal-protocol row: static values, rolling values,
    peak/trough (across static horizons), persistence (last-static vs peak),
    subperiod stability (count of subperiods with same sign/level)."""
    svals = {k: v for k, v in static.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}
    if svals:
        peak = max(svals.values())
        trough = min(svals.values())
        first = next((k for k, v in svals.items() if v != trough), None)
    else:
        peak = trough = np.nan
        first = None
    static_s = {f"static_{k}": _fmt(v) if isinstance(v, (int, float)) else str(v) for k, v in static.items()}
    roll_s = {f"roll_{k}": _fmt(v) if isinstance(v, (int, float)) else str(v) for k, v in rolling.items()}
    row = {
        "temporal_object": label,
        **static_s,
        **roll_s,
        "peak_static": _fmt(peak) if not isinstance(peak, str) else peak,
        "trough_static": _fmt(trough) if not isinstance(trough, str) else trough,
        "first_meaningful_deviation": first if first else "n/a",
        "persistence_last_vs_peak": _fmt((static.get("30D") / peak)) if (svals and peak not in (0, np.nan) and static.get("30D") is not None) else "n/a",
        "n_subperiods_consistent": int(subperiods.get("n", 0)),
        "subperiod_stable": subperiods.get("stable", "n/a"),
        "verdict": verdict,
        "note": note,
    }
    return row


# ---------------------------------------------------------------------------
# Master construction (cached)
# ---------------------------------------------------------------------------

def fix_days_since_contagion(snap: pd.DataFrame) -> pd.DataFrame:
    """Repair LF12's days_since_contagion: the LF12 construction used ffill
    that includes the current row, so every contagion event got days=0 (time
    since ITSELF). Recompute as time since the PRIOR contagion event per asset
    (shift before carry-forward)."""
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    d["_pc"] = d.groupby("cmc_id")["out_contagion"].shift(1).fillna(0)
    d["_cont_date"] = d["historical_date"].where(d["_pc"] == 1)
    d["last_cont_date"] = d.groupby("cmc_id")["_cont_date"].ffill()
    d["days_since_contagion"] = (d["historical_date"] - d["last_cont_date"]).dt.days
    d = d.drop(columns=["_pc", "_cont_date", "last_cont_date"])
    return d


def master_frame(use_cache: bool = True) -> pd.DataFrame:
    cache_p = CACHE / "lf13_master_frame.parquet"
    if use_cache and cache_p.exists() and cache_p.stat().st_size > 0:
        return pd.read_parquet(cache_p)

    base = base_frame(use_cache=True)
    base = fix_days_since_contagion(base)
    base = capacity_coordinates(base)
    base = stage_flags(base)
    base = mechanism_coordinates(base)
    base = temporal_species(base)
    base = rolling_protocol(base)
    base = base.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    base.to_parquet(cache_p, index=False)
    return base


if __name__ == "__main__":
    df = master_frame()
    print("LF13 master frame rows:", df.shape, flush=True)
    for c in ["cap_structural", "cap_liquidity", "cap_rankhealth", "cap_stress",
              "cap_recovery", "stg_absorption", "stg_propagation", "stg_containment",
              "mech_early_reach", "roll_peer_neg_frac_7D", "temp_species"]:
        print(("OK " if c in df.columns else "MISS"), c)
    print(df[["roll_peer_neg_frac_3D", "roll_peer_neg_frac_7D", "roll_fwd_ret_7D"]].describe())
