#!/usr/bin/env python
"""ALT_MECH_20 - GLOBAL RESPONSE / REALIZATION MECHANICS orchestration (parts 1..8).

Concatenated parts form scripts/build_mech20.py. Computes mech_20 CSVs 02..39,
41..43. Narrative files (01 prereg, 13 note, 40 proposal, 44 freeze input,
45 summary, 46 decision) written alongside by the agent after reviewing CSVs.

Terrain research ONLY (AGENT 1). No PnL, strategy, execution, sizing, direction.
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ranksums
from sklearn.linear_model import LinearRegression, LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m20base as B
sys.path.insert(0, str(B.RETRO / "scripts"))
sys.path.insert(0, str(B.RETRO.parent / "mech_18" / "scripts"))
from _m19base import logistic_params_unc as _LPC_UNC
from _m18base import exit_dist_series, js_divergence, _rho, _partial_rho

M99 = B.load_substrate()
from _m20base import (rolling_nodes_unc, r2, run_episodes, cusum_breaks,
                      segfit_breaks, dist_shift_breaks, match_nearest,
                      discrete_mi, _bin, logistic_params_unc)

OUT = B.ROOT
RETRO = OUT.parent / "mech_18"     # cross-deliverable reads (M18 files)
RETRO19 = OUT.parent / "mech_19"    # M19 deliverables
DEPTH_ORDER = M99.DEPTH_ORDER
SUBPERIODS = M99.SUBPERIODS


def _rhoXY(a, b, min_n=20):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < min_n:
        return np.nan
    return float(spearmanr(a[m], b[m]).statistic)


# Re-export substrate scalars (identical to MECH-19)
dfc = M99.dfc
act = M99.act
fams = M99.fams
demand = M99.demand
bm6 = M99.bm6
bm8 = M99.bm8
forcing_series = M99.forcing_series
fam_cols = M99.fam_cols
field_act = M99.field_act
ent6 = M99.ent6; k6 = M99.k6; p16 = M99.p16; p26 = M99.p26
ent8 = M99.ent8
demand_arr = M99.demand_arr
g6 = M99.g6; g6n = M99.g6n; g8 = M99.g8; g8n = M99.g8n
subp_arr = M99.subp_arr
prop7 = M99.prop7; ren7 = M99.ren7; rank7 = M99.rank7
pos_share = M99.pos_share; disp7 = M99.disp7; conc = M99.conc
rankd = M99.rankd; vol_med = M99.vol_med; btc7 = M99.btc7
PACT = M99.PACT
cap_arr = M99.cap_arr; te_arr = M99.te_arr; fc_arr = M99.fc_arr
thr_pos = M99.thr_pos
logit_fit = M99.logit_fit; thr_at = M99.thr_at
CONSTIT = M99.CONSTIT
STAGES18 = M99.STAGES18
RESP_NAMES = M99.RESP_NAMES

ns = len(dfc)
dates = pd.to_datetime(dfc["d"])
stable = np.asarray(pd.to_numeric(dfc["stablecoin_change_7d"], errors="coerce"))
mc30 = np.asarray(pd.to_numeric(dfc["total_mcap_chg30"], errors="coerce"))
btc = np.asarray(pd.to_numeric(dfc["btc_return_7d"], errors="coerce"))
disp = np.asarray(pd.to_numeric(dfc["top500_dispersion_7d"], errors="coerce"))
possh = np.asarray(pd.to_numeric(dfc["pos_ret_share"], errors="coerce"))
brth = np.asarray(pd.to_numeric(dfc.get("breadth", dfc.get("breadth_vel", pd.Series(np.nan, index=dfc.index))), errors="coerce"))
change6 = np.zeros(ns, dtype=bool)
for i in range(ns - 1):
    change6[i] = (g6[i + 1] != g6[i])


def W(name, index=False):
    def _w(dfw):
        p = OUT / name
        dfw.to_csv(p, index=index)
        print(f"wrote {name} ({len(dfw)} rows)")
    return _w


def _tier(v, q=(0.33, 0.67)):
    v = np.asarray(v, dtype=float)
    lo, hi = np.nanquantile(v, q)
    out = np.full(len(v), "mid", dtype=object)
    out[v <= lo] = "low"; out[v >= hi] = "high"
    return out


# daily route deformation (JS vs same-state historical baseline) - shared
def _js_hist_series(g):
    mat, labs = exit_dist_series(g, 7)
    ref = {s: np.nanmean(mat[np.asarray(g) == s], axis=0) for s in set(g)}
    out = np.full(len(g), np.nan)
    for i in range(len(g)):
        p = mat[i]
        if np.isnan(p).all():
            continue
        out[i] = js_divergence(p, ref[g[i]])
    return out


js_hist = _js_hist_series(g6)

# reuse MECH-18/19 birth partition
prev_ = np.array([None] + list(g6[:-1]))
bp_ = np.where(g6 != prev_)[0]
bp_ = bp_[(bp_ >= 8) & (bp_ < ns - 8)]
ab_, vi_ = [], []
for i_ in bp_:
    (ab_ if (g6[i_ + 1:i_ + 8] == prev_[i_]).any() else vi_).append(i_)
ab_ = np.array(ab_); vi_ = np.array(vi_)
FEAT18 = M99.FEAT18


def _stage_arr(ixs, arr, stage):
    if stage == "PRECONDITION":
        return np.array([np.nanmean(arr[max(0, i - 7):i]) for i in ixs])
    if stage == "INITIATION":
        return arr[ixs]
    if stage == "COMMITMENT":
        return np.array([np.nanmean(arr[i + 1:min(ns, i + 4)]) for i in ixs])
    return np.array([np.nanmean(arr[min(ns - 1, i + 4):min(ns, i + 8)]) for i in ixs])


# ================================================================ SHARED: unclamped rolling nodes
print("computing unclamped rolling response nodes (one-time)...")
NODE20 = rolling_nodes_unc(dates, fc_arr, act, RESP_NAMES)
NODE_ARR = {}
for p in RESP_NAMES:
    NODE_ARR[f"slope_{p}"] = NODE20[f"{p}_k"].to_numpy()
    NODE_ARR[f"ceiling_{p}"] = NODE20[f"{p}_ceiling"].to_numpy()
    NODE_ARR[f"onset_{p}"] = NODE20[f"{p}_x0"].to_numpy()
PATCHM = {k: np.nanmean([NODE_ARR[f"{k}_{p}"] for p in DEPTH_ORDER], axis=0) for k in ("slope", "ceiling", "onset")}
GAIN_F = NODE_ARR["slope_FIELD"]                 # primary response-gain coordinate
GAIN_P = PATCHM["slope"]                          # patch-mean gain (secondary)
CEIL_F = NODE_ARR["ceiling_FIELD"]
CEIL_P = PATCHM["ceiling"]
ONSET_F = NODE_ARR["onset_FIELD"]
print("unclamped nodes done:", int(np.isfinite(GAIN_F).sum()), "finite gain days")

# ================================================================ 02 response law decomposition
def response_law_decomposition():
    coords = {
        "GAIN": GAIN_F, "CEILING": CEIL_F, "THRESHOLD_POS": thr_pos,
        "TRANSFER": te_arr, "DEMAND": demand_arr, "EXIT_PRESSURE": p16,
        "EXIT_ENTROPY": ent6, "CAPACITY": cap_arr, "ROUTE_DEFORM": js_hist,
    }
    names = list(coords.keys())
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = _rhoXY(coords[a], coords[b])
            pr = _partial_rho(coords[a], coords[b], np.nanmean([coords[c] for c in names if c not in (a, b)], axis=0))[0]
            rows.append(dict(coordinate_a=a, coordinate_b=b,
                             rho=round(r, 3) if r == r else np.nan,
                             partial_rho_ctl=round(pr, 3) if pr == pr else np.nan,
                             coupling=("COUPLED" if abs(r) > 0.4 else ("PARTIAL" if abs(r) > 0.2 else "INDEPENDENT"))))
    # redundancy check: is ceiling a downstream expression of gain/forcing?
    rows.append(dict(coordinate_a="CEILING", coordinate_b="GAIN|FORCING",
                     rho=round(_rhoXY(CEIL_F, GAIN_F), 3) if np.isfinite(_rhoXY(CEIL_F, GAIN_F)) else np.nan,
                     partial_rho_ctl=round(_rhoXY(CEIL_F, fc_arr), 3) if np.isfinite(_rhoXY(CEIL_F, fc_arr)) else np.nan,
                     coupling="DIAGNOSTIC"))
    out = pd.DataFrame(rows)
    # era-adaptive probe: correlation stability across subperiods
    sp_rows = []
    for a, b in (("GAIN", "THRESHOLD_POS"), ("GAIN", "TRANSFER"), ("CEILING", "GAIN"), ("CEILING", "TRANSFER")):
        for sp in SUBPERIODS:
            m = subp_arr == sp
            r = _rhoXY(coords[a][m], coords[b][m])
            sp_rows.append(dict(coordinate_a=a, coordinate_b=b, subperiod=sp,
                                rho=round(r, 3) if r == r else np.nan))
    spdf = pd.DataFrame(sp_rows)
    spdf["era_adaptive"] = spdf.groupby(["coordinate_a", "coordinate_b"])["rho"].transform(lambda s: float(np.nanstd(s)))
    W("02_RESPONSE_LAW_DECOMPOSITION.csv")(out.round(3))
    W("02b_RESPONSE_LAW_SUBPERIOD.csv")(spdf.round(3))


# ================================================================ 03 saturation response coords
def saturation_response_coords():
    rows = []
    for node, arr in (("GAIN", GAIN_F), ("CEILING", CEIL_F)):
        v = arr[~np.isnan(arr)]
        if len(v) < 60:
            continue
        q = np.nanquantile(v, [0.1, 0.25, 0.5, 0.75, 0.9])
        rows.append(dict(node=node, n=len(v),
                         mean=round(float(np.nanmean(v)), 4), std=round(float(np.nanstd(v)), 4),
                         q10=round(float(q[0]), 4), q25=round(float(q[1]), 4),
                         q50=round(float(q[2]), 4), q75=round(float(q[3]), 4),
                         q90=round(float(q[4]), 4),
                         persistence_autocorr=round(float(np.corrcoef(v[:-1], v[1:])[0, 1]), 3),
                         monthly_turnover=round(float(np.nanmean(np.abs(np.diff(v)))), 4)))
    # rank dependence: per-patch gain/ceiling
    for p in DEPTH_ORDER:
        rows.append(dict(node=f"GAIN_{p}", n=int(np.isfinite(NODE_ARR[f"slope_{p}"]).sum()),
                         mean=round(float(np.nanmean(NODE_ARR[f"slope_{p}"])), 4),
                         q50=round(float(np.nanquantile(NODE_ARR[f"slope_{p}"], 0.5)), 4)))
    for p in DEPTH_ORDER:
        rows.append(dict(node=f"CEILING_{p}", n=int(np.isfinite(NODE_ARR[f"ceiling_{p}"]).sum()),
                         mean=round(float(np.nanmean(NODE_ARR[f"ceiling_{p}"])), 4),
                         q50=round(float(np.nanquantile(NODE_ARR[f"ceiling_{p}"], 0.5)), 4)))
    # what moves gain/ceiling: corr of node level with candidate drivers
    drivers = {"forcing": fc_arr, "demand": demand_arr, "volatility": vol_med,
               "dispersion": disp, "concentration": conc, "exit_pressure": p16,
               "exit_entropy": ent6, "transfer": te_arr, "threshold": thr_pos,
               "capacity": cap_arr, "stablecoin": stable, "btc": btc}
    for node, arr in (("GAIN", GAIN_F), ("CEILING", CEIL_F)):
        for name, dv in drivers.items():
            rows.append(dict(node=node, driver=name,
                             rho=round(_rhoXY(arr, dv), 3) if np.isfinite(_rhoXY(arr, dv)) else np.nan))
    # state dependence: mean gain/ceiling by 6-cell and 8-cell state
    for node, arr in (("GAIN", GAIN_F), ("CEILING", CEIL_F)):
        for res, gl in (("6C", g6), ("8C", g8)):
            for st in np.unique(gl):
                m = gl == st
                if m.sum() < 40:
                    continue
                rows.append(dict(node=node, state=f"{res}_{st}",
                                 mean=round(float(np.nanmean(arr[m])), 4)))
    # historical drift by subperiod
    for node, arr in (("GAIN", GAIN_F), ("CEILING", CEIL_F)):
        for sp in SUBPERIODS:
            m = subp_arr == sp
            rows.append(dict(node=node, subperiod=sp,
                             mean=round(float(np.nanmean(arr[m])), 4),
                             q50=round(float(np.nanquantile(arr[m], 0.5)), 4)))
    W("03_SATURATION_RESPONSE_COORDS.csv")(pd.DataFrame(rows).round(4))


# ================================================================ 04 response gain state
def response_gain_state():
    v = GAIN_F
    m = np.isfinite(v)
    rows = []
    rows.append(dict(probe="distribution", n=int(m.sum()),
                     mean=round(float(np.nanmean(v)), 4), std=round(float(np.nanstd(v)), 4),
                     q10=round(float(np.nanquantile(v, 0.1)), 4), q50=round(float(np.nanquantile(v, 0.5)), 4),
                     q90=round(float(np.nanquantile(v, 0.9)), 4)))
    # persistence: autocorr at several lags
    vv = v[~np.isnan(v)]
    for lag in (1, 5, 10, 20, 30):
        rows.append(dict(probe=f"autocorr_lag{lag}",
                         value=round(float(np.corrcoef(vv[:-lag], vv[lag:])[0, 1]), 3)))
    # transitions: tercile-state Markov (low/mid/high gain persistence)
    tiers = _tier(v)
    tm = np.zeros((3, 3))
    for i in range(ns - 1):
        a, b = tiers[i], tiers[i + 1]
        if a in ("low", "mid", "high") and b in ("low", "mid", "high"):
            tm[{"low": 0, "mid": 1, "high": 2}[a], {"low": 0, "mid": 1, "high": 2}[b]] += 1
    tm = tm / tm.sum(1, keepdims=True)
    for i, lab in enumerate(("low", "mid", "high")):
        rows.append(dict(probe=f"transition_from_{lab}",
                         to_low=round(float(tm[i, 0]), 3), to_mid=round(float(tm[i, 1]), 3),
                         to_high=round(float(tm[i, 2]), 3)))
    # relationship to delivery / inversion / route loading / forcing composition
    hi = v >= np.nanquantile(v, 0.67); lo = v <= np.nanquantile(v, 0.33)
    mm = np.isfinite(v) & np.isfinite(prop7)
    rows.append(dict(probe="delivery_rate_by_gain",
                     low=round(float(np.nanmean(prop7[mm & lo])), 3),
                     high=round(float(np.nanmean(prop7[mm & hi])), 3)))
    rows.append(dict(probe="sat_without_delivery_frac_by_gain",
                     low=round(float(np.nanmean((field_act[lo] >= np.nanquantile(field_act, 0.8)) & (prop7[lo] <= np.nanquantile(prop7, 0.33)))), 3),
                     high=round(float(np.nanmean((field_act[hi] >= np.nanquantile(field_act, 0.8)) & (prop7[hi] <= np.nanquantile(prop7, 0.33)))), 3)))
    # forcing composition by gain tier
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        rows.append(dict(probe=f"forcing_{fam}_by_gain",
                         low=round(float(np.nanmean(f[lo])), 3),
                         high=round(float(np.nanmean(f[hi])), 3)))
    out = pd.DataFrame(rows)
    # verdict: continuous coordinate?
    ac1 = float(np.corrcoef(vv[:-1], vv[1:])[0, 1])
    out["verdict"] = "CONTINUOUS_GAIN_COORDINATE" if ac1 > 0.7 else "STATE_LOCAL_GAIN"
    W("04_RESPONSE_GAIN_STATE.csv")(out.round(3))


# ================================================================ 05 ceiling role
def ceiling_role():
    rows = []
    hi = CEIL_F >= np.nanquantile(CEIL_F, 0.67)
    lo = CEIL_F <= np.nanquantile(CEIL_F, 0.33)
    mm = np.isfinite(CEIL_F) & np.isfinite(prop7)
    # H1 max attainable response / H2 absorptive buffer
    rows.append(dict(hypothesis="H1_ENABLE_MAX_RESPONSE",
                     delivery_high_ceil=round(float(np.nanmean(prop7[mm & hi])), 3),
                     delivery_low_ceil=round(float(np.nanmean(prop7[mm & lo])), 3),
                     diff=round(float(np.nanmean(prop7[mm & hi]) - np.nanmean(prop7[mm & lo])), 3)))
    # absorption: pressure high + high ceiling -> does propagation stall more?
    pres_hi = p16 >= np.nanquantile(p16, 0.67)
    rows.append(dict(hypothesis="H2_ABSORPTION",
                     prop_high_ceil_high_pres=round(float(np.nanmean(prop7[mm & hi & pres_hi])), 3),
                     prop_low_ceil_high_pres=round(float(np.nanmean(prop7[mm & lo & pres_hi])), 3)))
    # H3 saturation boundary: does high ceiling associate with higher field_act?
    rows.append(dict(hypothesis="H3_SATURATION_BOUNDARY",
                     field_act_high_ceil=round(float(np.nanmean(field_act[hi])), 3),
                     field_act_low_ceil=round(float(np.nanmean(field_act[lo])), 3)))
    # H4 regime-local scaling: ceiling variation across subperiods
    for sp in SUBPERIODS:
        m = subp_arr == sp
        rows.append(dict(hypothesis="H4_REGIME_SCALING", subperiod=sp,
                         ceiling_mean=round(float(np.nanmean(CEIL_F[m])), 4),
                         ceiling_std=round(float(np.nanstd(CEIL_F[m])), 4)))
    # H5 downstream expression: partial corr of ceiling with forcing after gain
    rows.append(dict(hypothesis="H5_DOWNSTREAM",
                     rho_ceiling_forcing=round(_rhoXY(CEIL_F, fc_arr), 3),
                     rho_ceiling_gain=round(_rhoXY(CEIL_F, GAIN_F), 3),
                     rho_gain_forcing=round(_rhoXY(GAIN_F, fc_arr), 3)))
    out = pd.DataFrame(rows)
    W("05_CEILING_ROLE.csv")(out.round(3))


# ================================================================ 06 slope x ceiling surface
def slope_ceiling_surface():
    g_hi = GAIN_F >= np.nanquantile(GAIN_F, 0.67); g_lo = GAIN_F <= np.nanquantile(GAIN_F, 0.33)
    c_hi = CEIL_F >= np.nanquantile(CEIL_F, 0.67); c_lo = CEIL_F <= np.nanquantile(CEIL_F, 0.33)
    cells = {"LO_GAIN_LO_CEIL": g_lo & c_lo, "LO_GAIN_HI_CEIL": g_lo & c_hi,
             "HI_GAIN_LO_CEIL": g_hi & c_lo, "HI_GAIN_HI_CEIL": g_hi & c_hi}
    rows = []
    for name, mk in cells.items():
        m = mk & np.isfinite(prop7)
        if m.sum() < 40:
            continue
        rows.append(dict(cell=name, n=int(m.sum()),
                         propagation=round(float(np.nanmean(prop7[m])), 3),
                         delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3),
                         reentry=round(float(np.nanmean(ren7[m])), 3),
                         threshold_crossing=round(float(np.nanmean(thr_pos[m])), 3),
                         exit_concentration=round(float(np.nanmean(p16[m])), 3),
                         rank_recruitment=round(float(np.nanmean(rank7[m])), 3),
                         sat_without_delivery=round(float(np.nanmean((field_act[m] >= np.nanquantile(field_act, 0.8)) & (prop7[m] <= np.nanquantile(prop7, 0.33)))), 3)))
    out = pd.DataFrame(rows)
    if len(out):
        best = out.loc[out["delivery_rate"].idxmax(), "cell"]
        worst = out.loc[out["delivery_rate"].idxmin(), "cell"]
        out["verdict"] = f"DISTINCT_ENVIRONMENTS_best={best}_worst={worst}"
    else:
        out["verdict"] = "DATA_LIMITED"
    W("06_SLOPE_CEILING_SURFACE.csv")(out.round(3))


# ================================================================ 07 saturation position x response state
def saturation_position_by_response():
    sat_lo = field_act <= np.nanquantile(field_act, 0.33)
    sat_mid = (field_act > np.nanquantile(field_act, 0.33)) & (field_act < np.nanquantile(field_act, 0.67))
    sat_hi = field_act >= np.nanquantile(field_act, 0.67)
    g_hi = GAIN_F >= np.nanquantile(GAIN_F, 0.67); g_lo = GAIN_F <= np.nanquantile(GAIN_F, 0.33)
    rows = []
    for sat_name, sat_mk in (("SAT_LOW", sat_lo), ("SAT_MID", sat_mid), ("SAT_HIGH", sat_hi)):
        for g_name, g_mk in (("LO_GAIN", g_lo), ("HI_GAIN", g_hi)):
            m = sat_mk & g_mk & np.isfinite(prop7)
            if m.sum() < 40:
                continue
            rows.append(dict(saturation_position=sat_name, gain_state=g_name,
                             n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3),
                             propagation=round(float(np.nanmean(prop7[m])), 3),
                             transfer=round(float(np.nanmean(te_arr[m])), 3),
                             threshold=round(float(np.nanmean(thr_pos[m])), 3),
                             exit_pressure=round(float(np.nanmean(p16[m])), 3)))
    out = pd.DataFrame(rows)
    # does "saturated" mean different things? compare high-sat delivery under low vs high gain
    try:
        d_hi = out[(out["saturation_position"] == "SAT_HIGH") & (out["gain_state"] == "HI_GAIN")]["delivery_rate"].iloc[0]
        d_lo = out[(out["saturation_position"] == "SAT_HIGH") & (out["gain_state"] == "LO_GAIN")]["delivery_rate"].iloc[0]
        out["verdict"] = "SATURATION_IS_RESPONSE_DEPENDENT" if abs(d_hi - d_lo) > 0.1 else "SATURATION_MEANING_STABLE"
    except Exception:
        out["verdict"] = "DATA_LIMITED"
    W("07_SATURATION_POSITION_BY_RESPONSE.csv")(out.round(3))
