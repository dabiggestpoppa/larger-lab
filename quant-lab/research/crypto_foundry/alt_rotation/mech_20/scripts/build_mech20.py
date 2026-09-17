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
# ================================================================ shared sat-with/without masks
SAT_HI = field_act >= np.nanquantile(field_act, 0.66)
DELIV = prop7 >= 0.5
NOD = SAT_HI & (~DELIV) & np.isfinite(prop7)
WITH = SAT_HI & DELIV & np.isfinite(prop7)

# ================================================================ 08 saturation failure matched
def _mean_diff(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 20 or len(b) < 20:
        return np.nan, np.nan, np.nan
    p = float(ranksums(a, b).pvalue)
    return float(np.nanmean(a)), float(np.nanmean(b)), p


def saturation_failure_matched():
    rows = []
    # matching covariates: state, gain, ceiling, demand, saturation position
    feat = np.column_stack([GAIN_F, CEIL_F, demand_arr, field_act])
    feat = np.where(np.isfinite(feat), feat, np.nan)
    idx_from = np.where(NOD & np.all(np.isfinite(feat), 1))[0]
    idx_to = np.where(WITH & np.all(np.isfinite(feat), 1))[0]
    if len(idx_from) < 30 or len(idx_to) < 30:
        W("08_SATURATION_FAILURE_MATCHED.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    # greedy nearest-neighbour within same 6-cell state
    matched = {}
    for st in np.unique(g6):
        f_ = idx_from[g6[idx_from] == st]
        t_ = idx_to[g6[idx_to] == st]
        if len(f_) < 10 or len(t_) < 10:
            continue
        sub_feat = feat[np.concatenate([f_, t_])]
        # per-state standardization
        mu = np.nanmean(sub_feat, axis=0); sd = np.nanstd(sub_feat, axis=0) + 1e-9
        fX = (feat[f_] - mu) / sd; tX = (feat[t_] - mu) / sd
        for jj, i in enumerate(f_):
            d = np.nansum((tX - fX[jj]) ** 2, axis=1)
            d = np.where(np.isfinite(d), d, np.inf)
            matched[i] = int(t_[np.argmin(d)])
    if len(matched) < 25:
        W("08_SATURATION_FAILURE_MATCHED.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED", n_matched=len(matched))]))
        return
    f_idx = np.array(list(matched.keys()), dtype=int)
    t_idx = np.array(list(matched.values()), dtype=int)
    comp = {"threshold_position": thr_pos, "transfer": te_arr, "forcing": fc_arr,
            "route_deformation": js_hist, "exit_pressure": p16, "exit_entropy": ent6,
            "volatility": vol_med, "stablecoin": stable, "btc_anchor": btc,
            "participation": possh, "capacity": cap_arr, "gain": GAIN_F, "ceiling": CEIL_F}
    for name, arr in comp.items():
        a, b, p = _mean_diff(arr[f_idx], arr[t_idx])
        rows.append(dict(variable=name, n_matched=int(len(f_idx)),
                         mean_without=round(a, 4) if a == a else np.nan,
                         mean_with=round(b, 4) if b == b else np.nan,
                         diff=round(a - b, 4) if (a == a and b == b) else np.nan,
                         ranksums_p=round(p, 4) if p == p else np.nan))
    # resolution mechanism split (from M18 04)
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    mech_nod = [dr6.get(g6[i]) for i in f_idx]
    mech_wit = [dr6.get(g6[i]) for i in t_idx]
    rows.append(dict(variable="resolution_mechanism_prune_frac",
                     n_matched=int(len(f_idx)),
                     mean_without=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_nod])), 3),
                     mean_with=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_wit])), 3),
                     diff=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_nod]) - np.mean([m == "EDGE_PRUNING" for m in mech_wit])), 3)))
    # forcing-family composition comparison
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        a, b, p = _mean_diff(f[f_idx], f[t_idx])
        rows.append(dict(variable=f"forcing_{fam}", n_matched=int(len(f_idx)),
                         mean_without=round(a, 4) if a == a else np.nan,
                         mean_with=round(b, 4) if b == b else np.nan,
                         diff=round(a - b, 4) if (a == a and b == b) else np.nan,
                         ranksums_p=round(p, 4) if p == p else np.nan))
    out = pd.DataFrame(rows)
    W("08_SATURATION_FAILURE_MATCHED.csv")(out.round(4))


# ================================================================ 09 saturation failure transitions
def saturation_failure_transitions():
    ep = run_episodes(NOD)
    rows = []
    for (a, b) in ep:
        if (b - a + 1) < 2:
            continue
        end = b + 1
        rec = {"start": str(dates[a].date()), "end": str(dates[b].date()), "dur": int(b - a + 1)}
        for hz, hzn in ((1, 1), (3, 3), (7, 7), (14, 14), (30, 30)):
            w = slice(min(end, ns - 1), min(end + hz, ns))
            if w.start >= w.stop:
                continue
            rec[f"forcing_strengthens_{hz}d"] = bool(np.nanmean(fc_arr[w]) > np.nanmean(fc_arr[a:b + 1]) + 0.1 * np.nanstd(fc_arr))
            rec[f"threshold_satisfied_{hz}d"] = bool(np.nanmean(thr_pos[w]) > np.nanquantile(thr_pos, 0.67))
            rec[f"transfer_repairs_{hz}d"] = bool(np.nanmean(te_arr[w]) > np.nanmean(te_arr[a:b + 1]) + 0.1 * np.nanstd(te_arr))
            rec[f"state_changed_{hz}d"] = bool(np.any(g6[w] != g6[a]))
            rec[f"saturation_decayed_{hz}d"] = bool(np.nanmean(field_act[w]) < np.nanmean(field_act[a:b + 1]) - 0.1 * np.nanstd(field_act))
            rec[f"realization_occurs_{hz}d"] = bool(np.any(prop7[w] >= 0.5))
            rec[f"exits_reopen_or_prune_{hz}d"] = bool(np.nanmean(ent6[w]) > np.nanmean(ent6[a:b + 1]) + 0.05 or np.nanmean(k6[w]) < np.nanmean(k6[a:b + 1]) - 0.05)
        rows.append(rec)
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("09_SATURATION_FAILURE_TRANSITIONS.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    # aggregate: fraction of episodes with each event at each horizon
    agg = []
    for hz in (1, 3, 7, 14, 30):
        for ev in ("forcing_strengthens", "threshold_satisfied", "transfer_repairs",
                   "state_changed", "saturation_decayed", "realization_occurs", "exits_reopen_or_prune"):
            col = f"{ev}_{hz}d"
            if col not in out.columns:
                continue
            agg.append(dict(horizon=hz, event=ev, frac_episodes=round(float(out[col].mean()), 3)))
    ag = pd.DataFrame(agg)
    W("09_SATURATION_FAILURE_TRANSITIONS.csv")(out.round(3))
    W("09b_SATURATION_FAILURE_TRANSITION_AGG.csv")(ag.round(3))


# ================================================================ 10 saturation failure -> delivery conversion
def saturation_to_delivery():
    # episodes of NOD that later see delivery within 30d -> which variable changes first?
    ep = run_episodes(NOD)
    rows = []
    var_changes = {"transfer": te_arr, "threshold": thr_pos, "forcing": fc_arr,
                   "gain": GAIN_F, "ceiling": CEIL_F, "exit_pressure": p16,
                   "route_deformation": js_hist}
    for (a, b) in ep:
        end = b + 1
        conv = np.where(prop7[min(end, ns):min(end + 30, ns)] >= 0.5)[0]
        if len(conv) == 0:
            continue
        t_conv = end + int(conv[0])
        base = a  # pre-episode baseline
        deltas = {}
        for name, arr in var_changes.items():
            pre = np.nanmean(arr[max(0, base - 5):base])
            post = np.nanmean(arr[t_conv - 2:t_conv + 3])
            if np.isfinite(pre) and np.isfinite(post):
                deltas[name] = post - pre
        if not deltas:
            continue
        first = max(deltas, key=lambda k: abs(deltas[k]))
        rows.append(dict(ep_start=str(dates[a].date()), ep_end=str(dates[b].date()),
                         conv_date=str(dates[t_conv].date()), days_to_conv=int(t_conv - end),
                         first_changed=first,
                         delta_first=round(float(deltas[first]), 4),
                         relation="PRECEDES" if int(t_conv - end) > 3 else "COINCIDES"))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("10_SATURATION_TO_DELIVERY.csv")(pd.DataFrame([dict(verdict="NO_CONVERSIONS")]))
        return
    agg = out["first_changed"].value_counts().reset_index()
    agg.columns = ["first_changed", "n_episodes"]
    agg["frac"] = round(agg["n_episodes"] / len(out), 3)
    W("10_SATURATION_TO_DELIVERY.csv")(out.round(4))
    W("10b_SATURATION_TO_DELIVERY_AGG.csv")(agg)
# ================================================================ 11 capacity interpretation
def capacity_interpretation():
    rows = []
    cap_hi = cap_arr >= np.nanquantile(cap_arr, 0.67); cap_lo = cap_arr <= np.nanquantile(cap_arr, 0.33)
    mm = np.isfinite(cap_arr) & np.isfinite(prop7)
    # H1 ENABLEMENT: high capacity -> more realization
    rows.append(dict(hypothesis="H1_ENABLEMENT",
                     delivery_high_cap=round(float(np.nanmean(prop7[mm & cap_hi] >= 0.5)), 3),
                     delivery_low_cap=round(float(np.nanmean(prop7[mm & cap_lo] >= 0.5)), 3)))
    # H2 ABSORPTION: high capacity + high forcing -> pressure absorbed without delivery
    f_hi = fc_arr >= np.nanquantile(fc_arr, 0.67)
    rows.append(dict(hypothesis="H2_ABSORPTION",
                     prop_high_cap_high_forcing=round(float(np.nanmean(prop7[mm & cap_hi & f_hi] >= 0.5)), 3),
                     prop_low_cap_high_forcing=round(float(np.nanmean(prop7[mm & cap_lo & f_hi] >= 0.5)), 3),
                     sat_without_delivery_high_cap=round(float(np.nanmean((field_act[cap_hi] >= np.nanquantile(field_act, 0.8)) & (prop7[cap_hi] <= np.nanquantile(prop7, 0.33)))), 3),
                     sat_without_delivery_low_cap=round(float(np.nanmean((field_act[cap_lo] >= np.nanquantile(field_act, 0.8)) & (prop7[cap_lo] <= np.nanquantile(prop7, 0.33)))), 3)))
    # H3 STATE_DEPENDENT: capacity vs delivery corr within states
    st_rhos = []
    for st in np.unique(g6):
        m = (g6 == st) & np.isfinite(cap_arr) & np.isfinite(prop7)
        if m.sum() < 60:
            continue
        st_rhos.append(_rhoXY(cap_arr[m], prop7[m]))
    rows.append(dict(hypothesis="H3_STATE_DEPENDENT",
                     median_state_rho=round(float(np.nanmedian(st_rhos)), 3) if st_rhos else np.nan,
                     n_states=int(len(st_rhos)),
                     positive_states=int(np.sum(np.array(st_rhos) > 0.05)),
                     negative_states=int(np.sum(np.array(st_rhos) < -0.05))))
    # conditional on threshold/transfer/gain/ceiling
    cond = {"threshold_hi": thr_pos >= np.nanquantile(thr_pos, 0.67),
            "threshold_lo": thr_pos <= np.nanquantile(thr_pos, 0.33),
            "transfer_hi": te_arr >= np.nanquantile(te_arr, 0.67),
            "transfer_lo": te_arr <= np.nanquantile(te_arr, 0.33),
            "gain_hi": GAIN_F >= np.nanquantile(GAIN_F, 0.67),
            "gain_lo": GAIN_F <= np.nanquantile(GAIN_F, 0.33),
            "ceiling_hi": CEIL_F >= np.nanquantile(CEIL_F, 0.67),
            "ceiling_lo": CEIL_F <= np.nanquantile(CEIL_F, 0.33)}
    for name, cm in cond.items():
        m = cm & np.isfinite(cap_arr) & np.isfinite(prop7)
        if m.sum() < 60:
            continue
        rows.append(dict(hypothesis="H3_CONDITIONAL", condition=name,
                         rho_cap_prop=round(_rhoXY(cap_arr[m], prop7[m]), 3), n=int(m.sum())))
    out = pd.DataFrame(rows)
    W("11_CAPACITY_INTERPRETATION.csv")(out.round(3))


# ================================================================ 12 capacity response law
def capacity_response_law():
    rows = []
    load_lo = fc_arr <= np.nanquantile(fc_arr, 0.33)
    load_mid = (fc_arr > np.nanquantile(fc_arr, 0.33)) & (fc_arr < np.nanquantile(fc_arr, 0.67))
    load_hi = fc_arr >= np.nanquantile(fc_arr, 0.67)
    cap_bins = np.nanquantile(cap_arr, np.linspace(0, 1, 5))
    for load_name, load_mk in (("LOW_LOAD", load_lo), ("MID_LOAD", load_mid), ("HIGH_LOAD", load_hi)):
        for k in range(4):
            cb = (cap_arr >= cap_bins[k]) & (cap_arr < cap_bins[k + 1]) & load_mk & np.isfinite(prop7)
            if cb.sum() < 30:
                continue
            rows.append(dict(load_band=load_name, capacity_band=f"Q{k+1}",
                             cap_mid=round(float(np.nanmedian(cap_arr[cb])), 3),
                             n=int(cb.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[cb] >= 0.5)), 3),
                             propagation=round(float(np.nanmean(prop7[cb])), 3)))
    out = pd.DataFrame(rows)
    # nonlinearity: within HIGH_LOAD does delivery rise then fall with capacity?
    try:
        hi = out[out["load_band"] == "HIGH_LOAD"].sort_values("capacity_band")
        d = hi["delivery_rate"].to_numpy()
        mono_up = bool(np.all(np.diff(d) >= -0.02))
        mono_dn = bool(np.all(np.diff(d) <= 0.02))
        if mono_up:
            verd = "ENABLING_CAPACITY"
        elif mono_dn:
            verd = "ABSORPTIVE_CAPACITY"
        elif len(d) >= 3 and d[0] < d[1] > d[2]:
            verd = "DUAL_ROLE_CAPACITY(enable_then_absorb)"
        else:
            verd = "STATE_LOCAL_CAPACITY"
    except Exception:
        verd = "STATE_LOCAL_CAPACITY"
    out["verdict"] = verd
    W("12_CAPACITY_RESPONSE_LAW.csv")(out.round(3))


# ================================================================ 14 threshold x transfer 2x2
def threshold_transfer_2x2():
    thr_hi = thr_pos >= np.nanquantile(thr_pos, 0.67); thr_lo = thr_pos <= np.nanquantile(thr_pos, 0.33)
    te_hi = te_arr >= np.nanquantile(te_arr, 0.67); te_lo = te_arr <= np.nanquantile(te_arr, 0.33)
    cells = {"THR_LO_TE_LO": thr_lo & te_lo, "THR_HI_TE_LO": thr_hi & te_lo,
             "THR_LO_TE_HI": thr_lo & te_hi, "THR_HI_TE_HI": thr_hi & te_hi}
    rows = []
    for name, mk in cells.items():
        m = mk & np.isfinite(prop7)
        if m.sum() < 40:
            continue
        rows.append(dict(cell=name, n=int(m.sum()),
                         delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3),
                         base_lift=round(float(np.nanmean(prop7[m] >= 0.5) - np.nanmean(prop7 >= 0.5)), 3)))
    # by 6-cell state
    for st in np.unique(g6):
        mst = g6 == st
        if mst.sum() < 60:
            continue
        for name, mk in cells.items():
            m = mst & mk & np.isfinite(prop7)
            if m.sum() < 10:
                continue
            rows.append(dict(cell=f"{name}_6C_{st}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    # by 8-cell state
    for st in np.unique(g8):
        mst = g8 == st
        if mst.sum() < 60:
            continue
        for name, mk in cells.items():
            m = mst & mk & np.isfinite(prop7)
            if m.sum() < 10:
                continue
            rows.append(dict(cell=f"{name}_8C_{st}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    # by rank depth: per-patch activation under each cell
    for p in DEPTH_ORDER:
        for name, mk in cells.items():
            m = mk & np.isfinite(prop7)
            if m.sum() < 20:
                continue
            rows.append(dict(cell=f"{name}_patch_{p}", n=int(m.sum()),
                             patch_activation=round(float(np.nanmean(act[p].to_numpy()[m])), 3)))
    # by gain band
    g_hi = GAIN_F >= np.nanquantile(GAIN_F, 0.67); g_lo = GAIN_F <= np.nanquantile(GAIN_F, 0.33)
    for g_name, gm in (("GAIN_LO", g_lo), ("GAIN_HI", g_hi)):
        for name, mk in cells.items():
            m = gm & mk & np.isfinite(prop7)
            if m.sum() < 20:
                continue
            rows.append(dict(cell=f"{name}_{g_name}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    out = pd.DataFrame(rows)
    W("14_THRESHOLD_TRANSFER_2X2.csv")(out.round(3))


# ================================================================ 15 complementarity / substitution test
def threshold_transfer_interaction():
    rows = []
    y = (prop7 >= 0.5).astype(float)
    tb = _bin(thr_pos); ub = _bin(te_arr)
    m = np.isfinite(thr_pos) & np.isfinite(te_arr) & np.isfinite(prop7)
    # information decomposition on binned variables
    mi_t, n1 = discrete_mi(tb[m], y[m])
    mi_u, n2 = discrete_mi(ub[m], y[m])
    # joint MI via 2D binning (threshold x transfer x y)
    xy = tb[m].astype(float) * 10 + ub[m].astype(float)
    mi_tu, n3 = discrete_mi(xy, y[m])
    rows.append(dict(probe="MI_threshold_delivery", value=round(mi_t, 4) if mi_t == mi_t else np.nan))
    rows.append(dict(probe="MI_transfer_delivery", value=round(mi_u, 4) if mi_u == mi_u else np.nan))
    rows.append(dict(probe="MI_threshold_transfer_delivery", value=round(mi_tu, 4) if mi_tu == mi_tu else np.nan))
    sum_ = (mi_t + mi_u) if (mi_t == mi_t and mi_u == mi_u) else np.nan
    rows.append(dict(probe="MI_sum_individual", value=round(sum_, 4) if sum_ == sum_ else np.nan))
    # interaction logistic: y ~ thr + te + thr*te
    X = np.column_stack([thr_pos[m], te_arr[m], thr_pos[m] * te_arr[m]])
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    try:
        lr = LogisticRegression(max_iter=2000).fit(Xs, y[m])
        c_thr, c_te, c_int = lr.coef_[0]
        rows.append(dict(probe="logit_coef_threshold", value=round(float(c_thr), 4)))
        rows.append(dict(probe="logit_coef_transfer", value=round(float(c_te), 4)))
        rows.append(dict(probe="logit_coef_interaction", value=round(float(c_int), 4)))
        # classify
        base_eff = abs(c_thr) * np.nanstd(thr_pos[m]) + abs(c_te) * np.nanstd(te_arr[m])
        int_eff = abs(c_int) * np.nanstd(thr_pos[m]) * np.nanstd(te_arr[m])
        if int_eff < 0.1 * max(base_eff, 1e-6):
            kind = "INDEPENDENT_OR_ADDITIVE"
        elif np.sign(c_int) == np.sign(c_thr) == np.sign(c_te):
            kind = "COMPLEMENTS(SYNERGISTIC)"
        elif np.sign(c_int) != np.sign(c_thr) and np.sign(c_int) != np.sign(c_te):
            kind = "SUBSTITUTES"
        else:
            kind = "CONDITIONAL_MIXTURE"
        rows.append(dict(probe="classification", value=kind))
    except Exception:
        rows.append(dict(probe="classification", value="DATA_LIMITED"))
    # conditional complementarity probe: does threshold matter MORE when transfer low?
    te_lo = te_arr <= np.nanquantile(te_arr, 0.33); te_hi = te_arr >= np.nanquantile(te_arr, 0.67)
    thr_hi = thr_pos >= np.nanquantile(thr_pos, 0.67); thr_lo = thr_pos <= np.nanquantile(thr_pos, 0.33)
    mm = np.isfinite(prop7)
    d_te_lo = float(np.nanmean(prop7[mm & te_lo & thr_hi] >= 0.5)) - float(np.nanmean(prop7[mm & te_lo & thr_lo] >= 0.5))
    d_te_hi = float(np.nanmean(prop7[mm & te_hi & thr_hi] >= 0.5)) - float(np.nanmean(prop7[mm & te_hi & thr_lo] >= 0.5))
    rows.append(dict(probe="threshold_lift_when_transfer_low", value=round(d_te_lo, 3)))
    rows.append(dict(probe="threshold_lift_when_transfer_high", value=round(d_te_hi, 3)))
    out = pd.DataFrame(rows)
    W("15_THRESHOLD_TRANSFER_INTERACTION.csv")(out.round(4))


# ================================================================ 16 realization core
def realization_core():
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    y = (prop7 >= 0.5).astype(float)
    coords = {"THRESHOLD": thr_pos, "TRANSFER": te_arr, "GAIN": GAIN_F, "CAPACITY": cap_arr}
    m0 = np.isfinite(prop7)
    rows = []
    for k in (1, 2, 3, 4):
        import itertools
        best_combo, best_auc = None, -1.0
        for combo in itertools.combinations(coords.keys(), k):
            X = np.column_stack([coords[c] for c in combo])
            m = m0 & np.all(np.isfinite(X), 1) & np.isfinite(GAIN_F)
            if m.sum() < 400:
                continue
            Xm = X[m]; ym = y[m]
            Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
            try:
                tr, te = train_test_split(np.arange(len(ym)), test_size=0.3, random_state=0, stratify=ym)
                lr = LogisticRegression(max_iter=2000).fit(Xs[tr], ym[tr])
                auc = float(roc_auc_score(ym[te], lr.predict_proba(Xs[te])[:, 1]))
            except Exception:
                auc = np.nan
            if auc == auc and auc > best_auc:
                best_auc, best_combo = auc, combo
        if best_combo is not None:
            rows.append(dict(n_coords=k, best_combo="+".join(best_combo),
                             heldout_auc=round(float(best_auc), 3)))
    # individual coordinate AUCs
    for c in coords:
        X = np.column_stack([coords[c]])
        m = m0 & np.all(np.isfinite(X), 1)
        if m.sum() < 400:
            continue
        Xm = X[m]; ym = y[m]
        Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
        try:
            tr, te = train_test_split(np.arange(len(ym)), test_size=0.3, random_state=0, stratify=ym)
            lr = LogisticRegression(max_iter=2000).fit(Xs[tr], ym[tr])
            auc = float(roc_auc_score(ym[te], lr.predict_proba(Xs[te])[:, 1]))
            rows.append(dict(n_coords=1, best_combo=c, heldout_auc=round(auc, 3), single=True))
        except Exception:
            pass
    out = pd.DataFrame(rows)
    if len(out):
        core = out[(out["n_coords"] == 2)].sort_values("heldout_auc", ascending=False)
        if len(core):
            out["verdict"] = f"CORE_2={core.iloc[0]['best_combo']}"
        else:
            out["verdict"] = "NO_CLEAN_CORE"
    else:
        out = pd.DataFrame([dict(verdict="DATA_LIMITED")])
    W("16_REALIZATION_CORE.csv")(out.round(3))
# ================================================================ 17 potential-realization relations
def realization_relations():
    coords = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "GAIN": GAIN_F, "CEILING": CEIL_F,
        "EXIT_PRESSURE": p16, "ROUTE_DEFORM": js_hist,
    }
    names = list(coords.keys())
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = _rhoXY(coords[a], coords[b])
            # conditional dependency: partial corr controlling for DELIVERY-relevant set
            ctrl = np.nanmean([coords[c] for c in names if c not in (a, b)], axis=0)
            pr = _partial_rho(coords[a], coords[b], ctrl)[0]
            rows.append(dict(coord_a=a, coord_b=b,
                             rho=round(r, 3) if r == r else np.nan,
                             partial_rho=round(pr, 3) if pr == pr else np.nan,
                             relation=("AMPLIFICATION" if abs(r) > 0.4 and r > 0 else
                                       ("SUPPRESSION" if abs(r) > 0.4 and r < 0 else
                                        ("MODEST" if abs(r) > 0.15 else "WEAK/INDEPENDENT")))))
    # redundancy: high pair rho AND similar delivery association
    mm = np.isfinite(prop7)
    y = (prop7 >= 0.5).astype(float)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra = _rhoXY(coords[a], y)
            rb = _rhoXY(coords[b], y)
            if abs(ra - rb) < 0.05 and abs(_rhoXY(coords[a], coords[b])) > 0.5:
                rows.append(dict(coord_a=a, coord_b=b, rho=round(_rhoXY(coords[a], coords[b]), 3),
                                 relation="REDUNDANT_DOWNSTREAM"))
    out = pd.DataFrame(rows)
    # state localization: rho stability across subperiods for key pairs
    sp_rows = []
    for a, b in (("THRESHOLD", "TRANSFER"), ("THRESHOLD", "GAIN"), ("GAIN", "CEILING"),
                 ("EXIT_PRESSURE", "TRANSFER"), ("CAPACITY", "THRESHOLD")):
        for sp in SUBPERIODS:
            m = subp_arr == sp
            r = _rhoXY(coords[a][m], coords[b][m])
            sp_rows.append(dict(coord_a=a, coord_b=b, subperiod=sp,
                                rho=round(r, 3) if r == r else np.nan))
    spdf = pd.DataFrame(sp_rows)
    spdf["regime_modulated"] = spdf.groupby(["coord_a", "coord_b"])["rho"].transform(lambda s: float(np.nanstd(s)) > 0.25)
    W("17_REALIZATION_RELATIONS.csv")(out.round(3))
    W("17b_REALIZATION_RELATIONS_SUBPERIOD.csv")(spdf.round(3))


# ================================================================ 18 realization constraint network
def realization_constraint_network():
    coords = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "GAIN": GAIN_F, "CEILING": CEIL_F,
        "EXIT_PRESSURE": p16, "ROUTE_DEFORM": js_hist,
        "FORCING": fc_arr,
    }
    names = list(coords.keys())
    rows = []
    ctrl = np.nanmean([coords[c] for c in names if c not in ("DEMAND", "CAPACITY", "THRESHOLD", "TRANSFER", "EXIT_PRESSURE")], axis=0)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = _rhoXY(coords[a], coords[b])
            pr = _partial_rho(coords[a], coords[b], ctrl)[0]
            tag = "NULL"
            if abs(r) > 0.4:
                tag = "SUPPORTED"
            elif abs(r) > 0.2:
                # check subperiod stability
                rr = []
                for sp in SUBPERIODS:
                    m = subp_arr == sp
                    v = _rhoXY(coords[a][m], coords[b][m])
                    if v == v:
                        rr.append(v)
                tag = "REGIME_MODULATED" if (len(rr) >= 3 and np.nanstd(rr) > 0.2) else "STATE_LOCAL"
            elif abs(pr) > 0.2 and abs(r) <= 0.1:
                tag = "CONDITIONAL_ONLY"
            rows.append(dict(node_a=a, node_b=b, rho=round(r, 3) if r == r else np.nan,
                             partial_rho=round(pr, 3) if pr == pr else np.nan,
                             tag=tag))
    out = pd.DataFrame(rows)
    out["verdict"] = "DESCRIPTIVE_GRAPH"
    W("18_REALIZATION_CONSTRAINT_NETWORK.csv")(out.round(3))


# ================================================================ 19 realization minimal sets
def realization_minimal_sets():
    import itertools
    y = (prop7 >= 0.5).astype(float)
    mm = np.isfinite(prop7)
    c_met = {
        "DEMAND": demand_arr >= np.nanquantile(demand_arr, 0.67),
        "CAPACITY": cap_arr >= np.nanquantile(cap_arr, 0.67),
        "THRESHOLD": thr_pos >= np.nanquantile(thr_pos, 0.67),
        "TRANSFER": te_arr >= np.nanquantile(te_arr, 0.67),
        "EXIT_PRESSURE": p16 >= np.nanquantile(p16, 0.67),
        "NON_SATURATED": field_act <= np.nanquantile(field_act, 0.8),
        "GAIN_HI": GAIN_F >= np.nanquantile(GAIN_F, 0.67),
    }
    cnames = list(c_met.keys())
    rows = []
    base = float(y[mm].mean())
    rows.append(dict(k=0, subset="BASE", n=int(mm.sum()), deliver_rate=round(base, 3), target="DELIVERY"))
    # frequent minimal sets: all pairs and triples with support
    for k in (1, 2, 3):
        for combo in itertools.combinations(cnames, k):
            m = mm.copy()
            for c in combo:
                m = m & c_met[c]
            if m.sum() < 40:
                continue
            rows.append(dict(k=k, subset="+".join(combo), n=int(m.sum()),
                             deliver_rate=round(float(y[m].mean()), 3),
                             stall_rate=round(float((prop7[m] <= np.nanquantile(prop7, 0.33)).mean()), 3),
                             target="DELIVERY"))
    # stall / abort / sat-without-delivery target subsets
    stall = prop7 <= np.nanquantile(prop7, 0.33)
    swod = SAT_HI & (~DELIV)
    for target, tmask in (("STALL", stall), ("SAT_WITHOUT_DELIVERY", swod)):
        for k in (2, 3):
            for combo in itertools.combinations(cnames, k):
                m = mm.copy()
                for c in combo:
                    m = m & c_met[c]
                if m.sum() < 40:
                    continue
                rows.append(dict(k=k, subset="+".join(combo), n=int(m.sum()),
                                 target=target,
                                 rate=round(float(tmask[m].mean()), 3)))
    out = pd.DataFrame(rows)
    # minimal sets: for each target, smallest k whose max rate > 0.7
    summ = []
    for target in ("DELIVERY", "STALL", "SAT_WITHOUT_DELIVERY"):
        sub = out[out["target"] == target].copy()
        if len(sub) == 0:
            continue
        rate_col = "deliver_rate" if target == "DELIVERY" else "rate"
        for k in (1, 2, 3):
            ksub = sub[sub["k"] == k]
            if len(ksub) == 0:
                continue
            top = ksub.loc[ksub[rate_col].idxmax()]
            summ.append(dict(target=target, minimal_k=k,
                             best_subset=top["subset"], best_rate=round(float(top[rate_col]), 3)))
    sdf = pd.DataFrame(summ)
    W("19_REALIZATION_MINIMAL_SETS.csv")(out.round(3))
    W("19b_REALIZATION_MINIMAL_SETS_SUMMARY.csv")(sdf.round(3))


# ================================================================ 20 realization equifinality
def realization_equifinality():
    import itertools
    y = (prop7 >= 0.5).astype(float)
    mm = np.isfinite(prop7) & np.isfinite(GAIN_F)
    deliv = np.where(mm)[0][y[mm] >= 0.5]
    c_met = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "EXIT_PRESSURE": p16, "GAIN": GAIN_F,
    }
    cnames = list(c_met.keys())
    # encode each delivery day as met/unmet pattern (above median)
    pat = np.zeros((len(deliv), len(cnames)), dtype=int)
    for j, c in enumerate(cnames):
        med = np.nanmedian(c_met[c])
        pat[:, j] = (c_met[c][deliv] >= med).astype(int)
    pat_key = ["".join(str(x) for x in row) for row in pat]
    from collections import Counter
    cnt = Counter(pat_key)
    n_patterns = len(cnt)
    top = cnt.most_common(8)
    rows = []
    for pk, c in top:
        mask = np.array([k == pk for k in pat_key])
        d = delivery_days = int(c)
        # characterize pattern
        on = [cnames[j] for j in range(len(cnames)) if pk[j] == "1"]
        rows.append(dict(pattern=pk, n_delivery_days=d, frac=round(c / len(deliv), 3),
                         constraints_met="+".join(on) if on else "NONE"))
    # distinctness: are top patterns spread across multiple constraint combos?
    rows.append(dict(pattern="TOTAL", n_delivery_days=int(len(deliv)),
                     frac=1.0, constraints_met=f"{n_patterns}_distinct_patterns"))
    out = pd.DataFrame(rows)
    # equifinality verdict
    top3_frac = float(sum(c for _, c in top[:3]) / max(len(deliv), 1))
    if n_patterns >= 8 and top3_frac < 0.6:
        verd = "MULTIPLE_REALIZATION_PATHS"
    elif top3_frac > 0.8:
        verd = "ONE_DOMINANT_CONSTRAINT_CORE"
    else:
        verd = "STATE_LOCAL_PATHS"
    out["verdict"] = verd
    W("20_REALIZATION_EQUIFINALITY.csv")(out.round(3))
# ================================================================ 21 birth failure deep
def birth_failure_deep():
    rows = []
    coords = {
        "live_exits": k6, "entropy": ent6, "dominant_share": p16,
        "pressure_concentration": p16 - p26, "forcing": fc_arr,
        "gain": GAIN_F, "ceiling": CEIL_F, "threshold": thr_pos,
        "transfer": te_arr, "capacity": cap_arr, "demand_slope": np.concatenate([[np.nan], np.diff(demand_arr)]),
    }
    p1_std = pd.Series(p16).rolling(7, min_periods=3).std().to_numpy()
    coords["dominant_instability"] = p1_std
    # pruning indicator at INITIATION: live exits dropping over prior 7d
    prun = np.full(ns, np.nan); prun[7:] = k6[7:] - k6[:-7]
    coords["pruning_rate"] = prun
    for stage in STAGES18:
        for name, arr in coords.items():
            vv = _stage_arr(vi_, arr, stage); av = _stage_arr(ab_, arr, stage)
            vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
            if len(vv) < 15 or len(av) < 15:
                continue
            d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
            p = float(ranksums(vv, av).pvalue)
            rows.append(dict(stage=stage, coordinate=name,
                             viable_mean=round(float(np.mean(vv)), 4),
                             aborted_mean=round(float(np.mean(av)), 4),
                             cohens_d=round(d, 3), p_value=round(p, 4)))
    out = pd.DataFrame(rows)
    # top discriminators per stage
    out["abs_d"] = out["cohens_d"].abs()
    top = out.loc[out.groupby("stage")["abs_d"].idxmax(), ["stage", "coordinate", "cohens_d"]]
    out["verdict"] = "MEASURED"
    W("21_BIRTH_FAILURE_DEEP.csv")(out.round(4))
    W("21b_BIRTH_FAILURE_TOP_DISCRIMINATORS.csv")(top.round(3))


# ================================================================ 22 load-resolution mismatch
def load_resolution_mismatch():
    # LOAD_ARRIVAL_RATE = d(demand)/dt + d(forcing)/dt (smoothed)
    load_rate = pd.Series(demand_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    load_rate = load_rate + pd.Series(fc_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    # ROUTE_RESOLUTION_RATE = -d(entropy)/dt (positive = resolving) and -d(live exits)/dt
    res_rate = -pd.Series(ent6).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = res_rate + (-pd.Series(k6).diff().rolling(3, min_periods=2).mean().to_numpy())
    rows = []
    for stage in STAGES18:
        vl = _stage_arr(vi_, load_rate, stage); al = _stage_arr(ab_, load_rate, stage)
        vr = _stage_arr(vi_, res_rate, stage); ar = _stage_arr(ab_, res_rate, stage)
        vl = vl[~np.isnan(vl)]; al = al[~np.isnan(al)]
        vr = vr[~np.isnan(vr)]; ar = ar[~np.isnan(ar)]
        if min(len(vl), len(al), len(vr), len(ar)) < 12:
            continue
        rows.append(dict(stage=stage,
                         load_rate_viable=round(float(np.mean(vl)), 4),
                         load_rate_aborted=round(float(np.mean(al)), 4),
                         resolution_rate_viable=round(float(np.mean(vr)), 4),
                         resolution_rate_aborted=round(float(np.mean(ar)), 4),
                         mismatch_d=round(float(abs(np.mean(al) - np.mean(vl)) / max((np.std(al) + np.std(vl)) / 2, 1e-9)), 3),
                         resolution_d=round(float(abs(np.mean(ar) - np.mean(vr)) / max((np.std(ar) + np.std(vr)) / 2, 1e-9)), 3),
                         load_vs_resolve=("LOAD_OUTPACES_RESOLUTION" if np.mean(al) - np.mean(ar) > np.mean(vl) - np.mean(vr) else "BALANCED")))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("22_LOAD_RESOLUTION_MISMATCH.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    promotable = (out["load_vs_resolve"] == "LOAD_OUTPACES_RESOLUTION").any()
    out["verdict"] = "PROMOTE" if promotable else "LOCAL"
    W("22_LOAD_RESOLUTION_MISMATCH.csv")(out.round(4))


# ================================================================ 23 birth failure surface
def birth_failure_surface():
    load_rate = pd.Series(demand_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    load_rate = load_rate + pd.Series(fc_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = -pd.Series(ent6).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = res_rate + (-pd.Series(k6).diff().rolling(3, min_periods=2).mean().to_numpy())
    # at INITIATION only
    lr = _stage_arr(bp_, load_rate, "INITIATION")
    rr = _stage_arr(bp_, res_rate, "INITIATION")
    out_bin = np.array([1 if i in ab_ else 0 for i in bp_])
    m = np.isfinite(lr) & np.isfinite(rr)
    if m.sum() < 40:
        W("23_BIRTH_FAILURE_SURFACE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED", n=int(m.sum()))]))
        return
    rows = []
    lq = np.nanquantile(lr[m], np.linspace(0, 1, 4))
    rq = np.nanquantile(rr[m], np.linspace(0, 1, 4))
    for li in range(3):
        for ri in range(3):
            cell = m & (lr >= lq[li]) & (lr < lq[li + 1]) & (rr >= rq[ri]) & (rr < rq[ri + 1])
            if cell.sum() < 5:
                continue
            rows.append(dict(load_band=f"L{li+1}", resolve_band=f"R{ri+1}",
                             n=int(cell.sum()),
                             abort_rate=round(float(out_bin[cell].mean()), 3)))
    out = pd.DataFrame(rows)
    if len(out):
        # gradient check: abort rate increases with load and decreases with resolution?
        hi_ab = out[(out["load_band"] == "L3")]["abort_rate"].mean()
        lo_ab = out[(out["load_band"] == "L1")]["abort_rate"].mean()
        hi_res = out[(out["resolve_band"] == "R3")]["abort_rate"].mean()
        lo_res = out[(out["resolve_band"] == "R1")]["abort_rate"].mean()
        out["verdict"] = (f"SURFACE(load_d={round(hi_ab-lo_ab,3)},resolve_d={round(lo_res-hi_res,3)})"
                          if (hi_ab - lo_ab > 0.05 or lo_res - hi_res > 0.05) else "FLAT_OR_DATA_LIMITED")
    else:
        out["verdict"] = "DATA_LIMITED"
    W("23_BIRTH_FAILURE_SURFACE.csv")(out.round(3))


# ================================================================ 24 birth recovery path
def birth_recovery_path():
    rows = []
    varmap = {"demand": demand_arr, "routes_prune": k6, "pressure_concentrates": p16,
              "transfer_repairs": te_arr, "threshold_normalizes": thr_pos,
              "gain_changes": GAIN_F, "entropy_collapses": ent6}
    for i in ab_:
        cand = bp_[bp_ > i]
        if len(cand) == 0:
            continue
        r = int(cand[0])
        viable = not (g6[r + 1:min(r + 8, ns)] == prev_[r]).any()
        if not viable:
            continue
        changes = {}
        for name, arr in varmap.items():
            pre = np.nanmean(arr[max(0, i - 5):i]); post = np.nanmean(arr[max(0, r - 5):r])
            if np.isfinite(pre) and np.isfinite(post):
                changes[name] = post - pre
        if not changes:
            continue
        first = max(changes, key=lambda k: abs(changes[k]))
        rows.append(dict(aborted_date=str(dates[i].date()), recovery_date=str(dates[r].date()),
                         days_to_recovery=int(r - i),
                         first_change=first,
                         delta_first=round(float(changes[first]), 4),
                         demand_cooled=bool(changes.get("demand", 0) < 0),
                         routes_pruned=bool(changes.get("routes_prune", 0) < 0),
                         pressure_concentrated=bool(changes.get("pressure_concentrates", 0) > 0),
                         transfer_repaired=bool(changes.get("transfer_repairs", 0) > 0),
                         threshold_normalized=bool(changes.get("threshold_normalizes", 0) > 0),
                         gain_changed=bool(abs(changes.get("gain_changes", 0)) > 0.05)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("24_BIRTH_RECOVERY_PATH.csv")(pd.DataFrame([dict(verdict="NO_VIABLE_RECOVERIES")]))
        return
    agg = out["first_change"].value_counts().reset_index()
    agg.columns = ["first_change", "n_episodes"]
    agg["frac"] = round(agg["n_episodes"] / len(out), 3)
    W("24_BIRTH_RECOVERY_PATH.csv")(out.round(4))
    W("24b_BIRTH_RECOVERY_ORDER_AGG.csv")(agg.round(3))
# ================================================================ shared rolling thr50 (reuse M19 compute)
THR50_ROLL = M99.THR50_ROLL
THR50 = {p: THR50_ROLL[p].to_numpy() for p in DEPTH_ORDER}


def _inversion_days(margin=0.15):
    """Daily inversion indicator: deeper patch activates earlier than shallower
    by a threshold-margin (thr50 shallow - thr50 deep > margin)."""
    invs = np.zeros(ns, dtype=bool)
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > margin
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            invs = invs | g
    return invs


# ================================================================ 25 threshold inversion materiality
def threshold_inversion_materiality():
    invs = _inversion_days()
    rows = []
    # 1) absolute physical response size: activation gap between inverted patches
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > 0.15
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            if g.sum() < 20:
                continue
            act_gap = np.nanmean(act[a].to_numpy()[g] - act[b].to_numpy()[g])
            thr_gap = np.nanmean(THR50[a][g] - THR50[b][g])
            rows.append(dict(probe=f"pair_{a}_vs_{b}", n_inversion_days=int(g.sum()),
                             thr50_gap=round(float(thr_gap), 4),
                             activation_gap_shallow_minus_deep=round(float(act_gap), 4),
                             absolute_response_size=round(float(abs(act_gap)), 4)))
    out = pd.DataFrame(rows)
    # overall materiality: mean |activation gap| during inversions
    gaps = []
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > 0.15
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            gaps.append(np.abs(np.nanmean(act[a].to_numpy()[g] - act[b].to_numpy()[g])))
    gaps = [x for x in gaps if x == x]
    mean_gap = float(np.nanmean(gaps)) if gaps else np.nan
    # standardized: relative to typical activation spread within patches
    act_std = float(np.nanmean([np.nanstd(act[p].to_numpy()) for p in DEPTH_ORDER]))
    std_gap = mean_gap / max(act_std, 1e-9) if mean_gap == mean_gap else np.nan
    # volatility normalization: is inversion more likely in high-vol?
    m = np.isfinite(vol_med)
    rows.append(dict(probe="OVERALL", n_inversion_days=int(invs.sum()),
                     mean_abs_activation_gap=round(mean_gap, 4) if mean_gap == mean_gap else np.nan,
                     standardized_gap_z=round(std_gap, 3) if std_gap == std_gap else np.nan,
                     vol_during_inversion=round(float(np.nanmean(vol_med[invs])), 4),
                     vol_baseline=round(float(np.nanmean(vol_med[m])), 4),
                     stablecoin_during_inversion=round(float(np.nanmean(stable[invs])), 4),
                     stablecoin_baseline=round(float(np.nanmean(stable[m])), 4),
                     n_assets_patch="DATA_BLOCKED(panel-aggregate)",
                     constituent_turnover="DATA_BLOCKED",
                     liquidity="DATA_BLOCKED",
                     asset_age="DATA_BLOCKED",
                     missingness_act=round(float(np.mean(np.isnan(act[g6 == g6[invs][0] if np.any(invs) else 0].to_numpy()))), 4)))
    # survivorship / rank migration proxy: rank7 recruitment during inversions
    rows.append(dict(probe="RANK_MIGRATION_PROXY", n_inversion_days=int(invs.sum()),
                     rank7_during=round(float(np.nanmean(rank7[invs])), 3),
                     rank7_baseline=round(float(np.nanmean(rank7[m])), 3)))
    out = pd.DataFrame(rows)
    if len(out) and std_gap == std_gap:
        out["verdict"] = ("MATERIAL" if std_gap > 0.5 else ("MARGINAL" if std_gap > 0.25 else "COMPOSITION_ARTIFACT"))
    else:
        out["verdict"] = "DATA_LIMITED"
    W("25_THRESHOLD_INVERSION_MATERIALITY.csv")(out.round(4))


# ================================================================ 26 threshold inversion post audit
def threshold_inversion_post_audit():
    mat = pd.read_csv(OUT / "25_THRESHOLD_INVERSION_MATERIALITY.csv")
    verd = mat["verdict"].iloc[0] if len(mat) else "DATA_LIMITED"
    rows = []
    if verd in ("COMPOSITION_ARTIFACT", "DATA_LIMITED"):
        W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(
            pd.DataFrame([dict(verdict=f"NOT_APPLICABLE_{verd}", note="materiality gate not passed; mechanism analysis demoted")]))
        return
    invs = _inversion_days()
    ep = run_episodes(invs)
    eps = [(a, b) for (a, b) in ep if (b - a + 1) >= 3]
    if len(eps) == 0:
        W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    for (a, b) in eps:
        rows.append(dict(start=str(dates[a].date()), end=str(dates[b].date()), dur=int(b - a + 1),
                         state=str(g6[a]),
                         exit_pressure=round(float(np.nanmean(p16[a:b + 1])), 3),
                         exit_entropy=round(float(np.nanmean(ent6[a:b + 1])), 3),
                         forcing=round(float(np.nanmean(fc_arr[a:b + 1])), 3),
                         gain=round(float(np.nanmean(GAIN_F[a:b + 1])), 3),
                         capacity=round(float(np.nanmean(cap_arr[a:b + 1])), 3),
                         physical_disturbance=round(float(np.nanmean(mc30[a:b + 1])), 3),
                         rank_recruitment=round(float(np.nanmean(rank7[a:b + 1])), 3),
                         concentration_release=round(float(np.nanmean(np.asarray(fams["CONCENTRATION_RELEASE_FORCING"], dtype=float)[a:b + 1])), 3)))
    out = pd.DataFrame(rows)
    out["verdict"] = f"MATERIALITY_PASSED_{verd}"
    W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(out.round(3))


# ================================================================ 27 threshold inversion function
def threshold_inversion_function():
    mat = pd.read_csv(OUT / "25_THRESHOLD_INVERSION_MATERIALITY.csv")
    verd = mat["verdict"].iloc[0] if len(mat) else "DATA_LIMITED"
    if verd in ("COMPOSITION_ARTIFACT", "DATA_LIMITED"):
        W("27_THRESHOLD_INVERSION_FUNCTION.csv")(
            pd.DataFrame([dict(verdict=f"DEMOTED_{verd}", function="NONE_ARTIFACT")]))
        return
    invs = _inversion_days()
    ep = run_episodes(invs)
    eps = [(a, b) for (a, b) in ep if (b - a + 1) >= 3]
    rows = []
    for (a, b) in eps:
        # which bands inverted
        pairs = []
        for i, aa in enumerate(DEPTH_ORDER):
            for bb in DEPTH_ORDER[i + 1:]:
                seg = (THR50[aa][a:b + 1] - THR50[bb][a:b + 1]) > 0.15
                if np.nanmean(seg) > 0.5:
                    pairs.append(f"{aa}<{bb}")
        deep_pair = any(p.startswith("751-1000") or p.startswith("1001-1500") or p.startswith("1501-2000") for p in pairs)
        shallow_pair = any(p.startswith("26-100") or p.startswith("101-250") for p in pairs)
        # context classification
        d = int(b - a + 1)
        f = float(np.nanmean(fc_arr[a:b + 1]))
        qf = np.nanquantile(fc_arr, [0.33, 0.67])
        rec = float(np.nanmean(rank7[a:b + 1]))
        if deep_pair and shallow_pair:
            func = "PATCH_BYPASS"
        elif deep_pair and f >= qf[1]:
            func = "DEEP_EARLY_ACTIVATION"
        elif deep_pair:
            func = "ROUTE_SPECIFIC_RECRUITMENT"
        elif not deep_pair:
            func = "SHALLOW_SUPPRESSION"
        else:
            func = "OTHER"
        rows.append(dict(start=str(dates[a].date()), end=str(dates[b].date()), dur=d,
                         pairs="|".join(pairs), function=func,
                         forcing_tier="HIGH" if f >= qf[1] else ("LOW" if f <= qf[0] else "MID"),
                         rank_recruitment=round(rec, 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("27_THRESHOLD_INVERSION_FUNCTION.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    vc = out["function"].value_counts()
    if len(vc) == 1:
        out["verdict"] = f"FEW_INVERSION_MECHANISMS_({vc.index[0]}_dominant)"
    elif len(vc) <= 3:
        out["verdict"] = "FEW_INVERSION_MECHANISMS"
    else:
        out["verdict"] = "CONTINUOUS_INVERSION_GEOMETRY"
    W("27_THRESHOLD_INVERSION_FUNCTION.csv")(out.round(3))
# ================================================================ hysteresis helpers
def _hys_gap2(y, fc, gm=None):
    """Controlled hysteresis gap: mean(y|rising) - mean(y|falling) at matched
    forcing levels, optionally within each level of control array gm."""
    y = np.asarray(y, dtype=float); fc = np.asarray(fc, dtype=float)
    d3 = np.full(len(fc), np.nan); d3[3:] = fc[3:] - fc[:-3]
    thr = np.nanstd(d3) * 0.25
    direc = np.where(d3 > thr, "rising", np.where(d3 < -thr, "falling", "flat"))
    qs = np.nanquantile(fc, np.linspace(0, 1, 11))
    gaps = []
    for i in range(10):
        mb = (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
        mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
        if mr.sum() >= 10 and mf.sum() >= 10:
            gaps.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    gap = float(np.nanmean(gaps)) if gaps else np.nan
    if gm is None:
        return gap, gap
    gc = []
    for lv in np.unique(gm):
        ms = gm == lv
        for i in range(10):
            mb = ms & (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
            mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
            if mr.sum() >= 6 and mf.sum() >= 6:
                gc.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    return gap, float(np.nanmean(gc)) if gc else np.nan


# ================================================================ 28 hysteresis reconciliation
def hysteresis_reconciliation():
    rows = []
    fams_sel = ["PARTICIPATION_FORCING", "VOLATILITY_FORCING", "BTC_ANCHOR_FORCING",
                "DISPERSION_FORCING", "STABLECOIN_CAPITAL_FORCING"]
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy()
        for st in np.unique(g6):
            m = g6 == st
            if m.sum() < 90:
                continue
            gap, gap_c = _hys_gap2(y[m], fc_arr[m])
            for fam in fams_sel:
                f = np.asarray(fams[fam], dtype=float)
                gf = np.full(ns, np.nan)
                gf[1:] = f[1:] - f[:-1]
                tier = np.where(gf[m] > 0, "up", np.where(gf[m] < 0, "dn", "flat"))
                gap_f, gap_fc = _hys_gap2(y[m], fc_arr[m], gm=tier)
                rows.append(dict(patch=patch, state=str(st), n=int(m.sum()),
                                 gap_raw=round(gap, 3) if gap == gap else np.nan,
                                 gap_ctl_state=round(gap_c, 3) if gap_c == gap_c else np.nan,
                                 forcing_family=fam,
                                 gap_ctl_family=round(gap_fc, 3) if gap_fc == gap_fc else np.nan))
    out = pd.DataFrame(rows)
    W("28_HYSTERESIS_RECONCILIATION.csv")(out.round(3))


# ================================================================ 29 hysteresis survival map
def hysteresis_survival_map():
    rec = pd.read_csv(OUT / "28_HYSTERESIS_RECONCILIATION.csv")
    if len(rec) == 0:
        W("29_HYSTERESIS_SURVIVAL_MAP.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rows = []
    from scipy.stats import ranksums
    for patch in DEPTH_ORDER:
        for st in np.unique(g6):
            sub = rec[(rec["patch"] == patch) & (rec["state"] == st)]
            if len(sub) == 0:
                continue
            g = sub["gap_ctl_state"].to_numpy()
            g = g[~np.isnan(g)]
            if len(g) == 0:
                continue
            # subperiod stability of the state-level gap
            sp_vals = []
            y = act[patch].to_numpy(); m = g6 == st
            for sp in SUBPERIODS:
                msp = m & (subp_arr == sp)
                if msp.sum() < 60:
                    continue
                gap, _ = _hys_gap2(y[msp], fc_arr[msp])
                if gap == gap:
                    sp_vals.append(gap)
            fam_sens = float(np.nanstd(rec[(rec["patch"] == patch) & (rec["state"] == st)]["gap_ctl_family"].dropna())) if rec[(rec["patch"] == patch) & (rec["state"] == st)]["gap_ctl_family"].notna().any() else np.nan
            rows.append(dict(patch=patch, state=str(st),
                             gap_ctl_mean=round(float(np.nanmean(g)), 3),
                             gap_ctl_max=round(float(np.nanmax(g)), 3),
                             n_cells=len(g),
                             subperiod_std=round(float(np.nanstd(sp_vals)), 3) if len(sp_vals) >= 3 else np.nan,
                             forcing_family_sensitivity=round(fam_sens, 3) if fam_sens == fam_sens else np.nan))
    out = pd.DataFrame(rows)
    strong = out[out["gap_ctl_max"] >= 0.05]
    if len(strong) == 0:
        out["verdict"] = "WEAK_LOCAL_HYSTERESIS"
    elif strong["subperiod_std"].notna().any() and strong["subperiod_std"].max() > 0.03:
        out["verdict"] = "INTERACTION_HYSTERESIS(state_x_depth_x_regime)"
    else:
        # which dominates: state spread vs depth spread
        depth_spread = out.groupby("patch")["gap_ctl_mean"].mean().std()
        state_spread = out.groupby("state")["gap_ctl_mean"].mean().std()
        out["verdict"] = ("STATE_DOMINANT_HYSTERESIS" if state_spread > depth_spread else "DEPTH_DOMINANT_HYSTERESIS")
    W("29_HYSTERESIS_SURVIVAL_MAP.csv")(out.round(3))


# ================================================================ 30 forcing functional dimensions
def forcing_functional_dimensions():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        fv = f[~np.isnan(f)]
        ac1 = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        burst = float(np.nanquantile(f, 0.9) / max(abs(np.nanquantile(f, 0.5)), 1e-9)) if np.isfinite(np.nanquantile(f, 0.5)) else np.nan
        temporal = "PERSISTENT" if (ac1 == ac1 and ac1 > 0.6) else ("BURSTY" if (burst == burst and burst > 2.0) else "MIXED")
        # spatial: broad vs rank-local = std of |corr with each patch|
        patch_c = [abs(_rhoXY(f, act[p].to_numpy())) for p in DEPTH_ORDER]
        spatial = "RANK_LOCAL" if (len(patch_c) and float(np.std(patch_c)) > 0.12) else "BROAD"
        # route function: load/suppress from M19 11 map
        rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
        fsub = rsf[rsf["forcing_family"] == fam].dropna(subset=["rho"])
        loads = int((fsub["rho"] > 0.15).sum()); supps = int((fsub["rho"] < -0.15).sum())
        route_fn = "LOAD_ROUTE" if loads > supps * 2 else ("SUPPRESS_ROUTE" if supps > loads * 2 else "MIXED")
        # response function: which node moves most
        node_c = {k: abs(_rhoXY(f, PATCHM[f"{k}"])) for k in ("slope", "ceiling", "onset")}
        resp_fn = max(node_c, key=node_c.get) if any(v == v for v in node_c.values()) else "none"
        resp_mag = node_c[resp_fn] if resp_fn != "none" else np.nan
        # resolution function: pruning vs concentration (per-state mechanism association)
        dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
        dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
        pr = [np.nanmean(f[g6 == s]) for s, m in dr6.items() if m == "EDGE_PRUNING"]
        co = [np.nanmean(f[g6 == s]) for s, m in dr6.items() if m == "PRESSURE_CONCENTRATION"]
        res_fn = "FAVOR_PRUNING" if (len(pr) and len(co) and np.nanmean(pr) > np.nanmean(co)) else "FAVOR_CONCENTRATION" if (len(pr) and len(co)) else "NEUTRAL"
        rows.append(dict(family=fam,
                         temporal_character=temporal, autocorr1=round(ac1, 3) if ac1 == ac1 else np.nan,
                         burstiness=round(burst, 3) if burst == burst else np.nan,
                         spatial_character=spatial, patch_corr_spread=round(float(np.std(patch_c)), 3),
                         route_function=route_fn, n_routes_loaded=loads, n_routes_suppressed=supps,
                         response_function=f"MOVE_{resp_fn.upper()}", response_mag=round(float(resp_mag), 3) if resp_mag == resp_mag else np.nan,
                         resolution_function=res_fn))
    W("30_FORCING_FUNCTIONAL_DIMENSIONS.csv")(pd.DataFrame(rows).round(3))


# ================================================================ 31 forcing functional map
def forcing_functional_map():
    fd = pd.read_csv(OUT / "30_FORCING_FUNCTIONAL_DIMENSIONS.csv")
    # 2D map: temporal (autocorr) x spatial (patch spread)
    rows = []
    for _, r in fd.iterrows():
        rows.append(dict(family=r["family"],
                         temporal_axis=round(float(r["autocorr1"]), 3) if r["autocorr1"] == r["autocorr1"] else np.nan,
                         spatial_axis=round(float(r["patch_corr_spread"]), 3),
                         route_function=r["route_function"], response_function=r["response_function"],
                         resolution_function=r["resolution_function"],
                         quadrant=("PERSISTENT_BROAD" if (r["autocorr1"] or 0) > 0.5 and r["patch_corr_spread"] <= 0.12 else
                                   "PERSISTENT_RANKLOCAL" if (r["autocorr1"] or 0) > 0.5 else
                                   "IMPULSE_BROAD" if r["patch_corr_spread"] <= 0.12 else "IMPULSE_RANKLOCAL")))
    out = pd.DataFrame(rows)
    W("31_FORCING_FUNCTIONAL_MAP.csv")(out.round(3))


# ================================================================ 32 forcing temporal scales
def forcing_temporal_scales():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        fv = f[~np.isnan(f)]
        acs = []
        for lag in (1, 3, 5, 10, 20):
            if len(fv) > lag + 10:
                acs.append(float(np.corrcoef(fv[:-lag], fv[lag:])[0, 1]))
            else:
                acs.append(np.nan)
        # half-life: first lag where autocorr < 0.5
        half = next((lag for lag, a in zip((1, 3, 5, 10, 20), acs) if a == a and a < 0.5), None)
        # burst duration: mean length of above-median runs
        med = np.nanmedian(f)
        runs = run_episodes(f >= med)
        burst_len = float(np.mean([b - a + 1 for (a, b) in runs])) if runs else np.nan
        # lead/lag vs route pressure: cross-correlation of family with forward exit pressure
        from scipy.signal import correlate
        ff = np.nan_to_num(f); pp = np.nan_to_num(p16)
        ff = (ff - ff.mean()) / (ff.std() + 1e-9); pp = (pp - pp.mean()) / (pp.std() + 1e-9)
        lags = np.arange(-10, 11)
        xc = [float(np.corrcoef(ff[:len(ff) - abs(l)] if l >= 0 else ff[abs(l):],
                                pp[abs(l):] if l >= 0 else pp[:len(pp) - abs(l)])[0, 1]) if len(ff) > abs(l) + 20 else np.nan for l in lags]
        best_lag = int(lags[int(np.nanargmax(np.abs(xc)))]) if any(x == x for x in xc) else np.nan
        gain_c = _rhoXY(f, GAIN_F)
        rows.append(dict(family=fam,
                         ac_lag1=round(acs[0], 3) if acs[0] == acs[0] else np.nan,
                         ac_lag5=round(acs[2], 3) if acs[2] == acs[2] else np.nan,
                         ac_lag20=round(acs[4], 3) if acs[4] == acs[4] else np.nan,
                         half_life_lag=half,
                         mean_burst_days=round(burst_len, 2) if burst_len == burst_len else np.nan,
                         best_lag_vs_route_pressure=int(best_lag) if best_lag == best_lag else np.nan,
                         rho_with_gain=round(gain_c, 3) if gain_c == gain_c else np.nan,
                         temporal_class=("BACKGROUND_FIELD" if (acs[0] == acs[0] and acs[0] > 0.6 and (half or 99) >= 10)
                                         else "IMPULSE" if (acs[0] == acs[0] and acs[0] < 0.4)
                                         else "MIXED")))
    W("32_FORCING_TEMPORAL_SCALES.csv")(pd.DataFrame(rows).round(3))


# ================================================================ 33 forcing interaction deep
def forcing_interaction_deep():
    it = pd.read_csv(RETRO19 / "10_FORCING_INTERACTIONS.csv")
    sel = it[it["classification"].isin(["SYNERGISTIC_LIKE", "ANTAGONISTIC_LIKE", "ROUTE_SPECIFIC"])]
    outcomes = {"route_pressure": p16, "transfer": te_arr, "threshold": thr_pos,
                "gain": GAIN_F, "ceiling": CEIL_F, "rank_recruitment": rank7}
    rows = []
    for _, r in sel.iterrows():
        a, b = r["family_a"], r["family_b"]
        fa = np.asarray(fams[a], dtype=float); fb = np.asarray(fams[b], dtype=float)
        hi_a = fa >= np.nanquantile(fa, 0.7); hi_b = fb >= np.nanquantile(fb, 0.7)
        for oname, oarr in outcomes.items():
            both = hi_a & hi_b & np.isfinite(oarr)
            only_a = hi_a & (~hi_b) & np.isfinite(oarr)
            only_b = (~hi_a) & hi_b & np.isfinite(oarr)
            neither = (~hi_a) & (~hi_b) & np.isfinite(oarr)
            if min(both.sum(), only_a.sum(), only_b.sum(), neither.sum()) < 30:
                continue
            # interaction effect beyond additivity
            exp_add = float(np.nanmean(oarr[only_a]) + np.nanmean(oarr[only_b]) - np.nanmean(oarr[neither]))
            obs_both = float(np.nanmean(oarr[both]))
            delta = obs_both - exp_add
            rows.append(dict(family_a=a, family_b=b, interaction_type=r["classification"],
                             outcome=oname, n_both=int(both.sum()),
                             observed_both=round(obs_both, 4),
                             additive_expectation=round(exp_add, 4),
                             interaction_delta=round(delta, 4),
                             alters_outcome=bool(abs(delta) > 0.1 * max(abs(obs_both), 1e-6))))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("33_FORCING_INTERACTION_DEEP.csv")(pd.DataFrame([dict(verdict="NO_SUPPORTED_INTERACTIONS")]))
        return
    W("33_FORCING_INTERACTION_DEEP.csv")(out.round(4))
# ================================================================ shared era windows
EV_UNC = M99.EV_UNC
ZDF = EV_UNC["Zdf"] if isinstance(EV_UNC, dict) and EV_UNC.get("verdict") == "EVENT_DETECTED" else pd.DataFrame()
ONSET_DT = pd.Timestamp("2021-12-16")
SNAPBACK_DT = pd.Timestamp("2022-06-28")
PRE_ERA = dates < pd.Timestamp("2021-10-01")
TRANS_ERA = (dates >= pd.Timestamp("2021-10-01")) & (dates < pd.Timestamp("2022-07-01"))
POST_ERA = dates >= pd.Timestamp("2023-07-01")


# ================================================================ 34 2022 era hypotheses
def _gain_monthly():
    s = pd.Series(GAIN_F, index=dates)
    return s.resample("MS").mean().dropna()


def _regime_of(m, lo=0.35, hi=0.9):
    return np.where(m <= lo, "LOW", np.where(m >= hi, "HIGH", "MID"))


def era_hypotheses():
    rows = []
    g = GAIN_F
    gm = _gain_monthly()
    pre_m_ = gm[gm.index < pd.Timestamp("2021-10-01")]
    post_m_ = gm[gm.index >= pd.Timestamp("2023-07-01")]
    pre_mean = float(pre_m_.mean()); post_mean = float(post_m_.mean())
    pre_sd = float(pre_m_.std())
    # H1: does the LOW-GAIN regime frequency return to pre levels? (bimodal-safe)
    lo_pre = float((_regime_of(pre_m_.to_numpy()) == "LOW").mean())
    lo_post = float((_regime_of(post_m_.to_numpy()) == "LOW").mean())
    rows.append(dict(hypothesis="H1_TEMPORARY_SCAR",
                     pre_gain_mean=round(pre_mean, 4), post_gain_mean=round(post_mean, 4),
                     low_gain_regime_frac_pre=round(lo_pre, 3),
                     low_gain_regime_frac_post=round(lo_post, 3),
                     test="post recovers pre low-regime frequency" if abs(lo_post - lo_pre) < 0.2 else "post low-regime frequency differs"))
    # H2: stability of post-2023 by year (does a single baseline exist?)
    for yr in (2023, 2024, 2025, 2026):
        m = (dates.dt.year == yr) & np.isfinite(g)
        rows.append(dict(hypothesis="H2_ERA_TRANSITION", year=yr,
                         gain_mean=round(float(np.nanmean(g[m])), 4),
                         gain_std=round(float(np.nanstd(g[m])), 4),
                         n_days=int(m.sum())))
    # H3: count regime transitions (LOW<->HIGH excursions) on monthly grid, full panel
    reg = _regime_of(gm.to_numpy())
    trans = int(np.sum(reg[1:] != reg[:-1]))
    n_lo_runs = len(run_episodes(reg == "LOW"))
    n_hi_runs = len(run_episodes(reg == "HIGH"))
    rows.append(dict(hypothesis="H3_MULTIPLE_MODULATIONS",
                     monthly_regime_transitions=int(trans),
                     n_low_gain_runs=int(n_lo_runs), n_high_gain_runs=int(n_hi_runs),
                     post_frac_low_regime=round(lo_post, 3)))
    out = pd.DataFrame(rows)
    # verdict: bimodal structure -> repeated modulations unless post is uniformly low/high
    if n_lo_runs >= 2 and n_hi_runs >= 2:
        out["verdict"] = "H3_MULTIPLE_REGIME_MODULATIONS"
    elif abs(lo_post - lo_pre) < 0.2 and n_lo_runs <= 1:
        out["verdict"] = "H1_TEMPORARY_SCAR"
    else:
        out["verdict"] = "H2_ERA_TRANSITION"
    W("34_2022_ERA_HYPOTHESES.csv")(out.round(4))


# ================================================================ 35 response gain changepoints
def response_gain_changepoints():
    # operate on the MONTHLY gain grid (73 observations) - matches the 30d fit cadence
    gm = _gain_monthly()
    gv = gm.to_numpy()
    n = len(gv)
    min_seg = 6  # months
    # CUSUM on monthly grid
    cb = [k for k in cusum_breaks(gv, min_seg=min_seg) if k < n - 1]
    # segmented regression on monthly grid
    sb = segfit_breaks(gv, cand_step=2, min_seg=min_seg, max_breaks=3)
    # distribution shift on monthly grid
    ds = dist_shift_breaks(gv, base_win=12, ref_win=3)
    rows = []
    for k in cb:
        rows.append(dict(method="CUSUM", break_index=int(k), break_date=str(gm.index[k].date())))
    for k in sb:
        rows.append(dict(method="SEGMENTED_REGRESSION", break_index=int(k), break_date=str(gm.index[k].date())))
    for k in ds:
        rows.append(dict(method="DISTRIBUTION_SHIFT", break_index=int(k), break_date=str(gm.index[k].date())))
    out = pd.DataFrame(rows)
    # agreement within +-2 months across >=2 methods
    all_breaks = sorted(cb + sb + ds)
    agree = []
    for k in all_breaks:
        near = [x for x in all_breaks if abs(x - k) <= 2]
        if len(near) >= 2 and k not in agree:
            agree.append(int(np.mean(near)))
    agree = sorted(set(agree))
    first_break = agree[0] if agree else None
    if first_break is not None:
        pre_level = float(np.nanmean(gv[:first_break]))
        post_level = float(np.nanmean(gv[first_break:]))
    else:
        pre_level = post_level = np.nan
    rows2 = [dict(method="AGREED_BREAK", break_index=k, break_date=str(gm.index[k].date())) for k in agree]
    out = pd.concat([out, pd.DataFrame(rows2)], ignore_index=True)
    out["first_break_date"] = str(gm.index[first_break].date()) if first_break is not None else None
    out["pre_level"] = round(pre_level, 4) if pre_level == pre_level else np.nan
    out["post_level"] = round(post_level, 4) if post_level == post_level else np.nan
    out["verdict"] = "CHANGEPOINTS_AGREED" if len(agree) >= 1 else "NO_AGREED_CHANGEPOINT"
    W("35_RESPONSE_GAIN_CHANGEPOINTS.csv")(out.round(4))


# ================================================================ 36 pre transition post law
def pre_transition_post_law():
    rows = []
    eras = {"PRE2022": PRE_ERA, "TRANSITION": TRANS_ERA, "POST2022": POST_ERA}
    # gain / ceiling / transfer / route deformation
    for e_name, em in eras.items():
        rows.append(dict(era=e_name, variable="gain",
                         mean=round(float(np.nanmean(GAIN_F[em])), 4),
                         q50=round(float(np.nanquantile(GAIN_F[em], 0.5)), 4)))
        rows.append(dict(era=e_name, variable="ceiling",
                         mean=round(float(np.nanmean(CEIL_F[em])), 4)))
        rows.append(dict(era=e_name, variable="transfer",
                         mean=round(float(np.nanmean(te_arr[em])), 4)))
        rows.append(dict(era=e_name, variable="route_deformation",
                         mean=round(float(np.nanmean(js_hist[em])), 4)))
        rows.append(dict(era=e_name, variable="birth_abort_rate",
                         mean=round(float(np.mean([1 if i in ab_ else 0 for i in bp_ if em[i]])), 3)))
        rows.append(dict(era=e_name, variable="realization_rate",
                         mean=round(float(np.nanmean(prop7[em] >= 0.5)), 3)))
    # threshold hierarchy per era: per-patch thr50 mean
    for p in DEPTH_ORDER:
        for e_name, em in eras.items():
            rows.append(dict(era=e_name, variable=f"thr50_{p}",
                             mean=round(float(np.nanmean(THR50[p][em])), 4)))
    # forcing-route relationships per era: corr(forcing, exit pressure) per family
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        for e_name, em in eras.items():
            r = _rhoXY(f[em], p16[em])
            rows.append(dict(era=e_name, variable=f"route_load_{fam}",
                             mean=round(r, 3) if r == r else np.nan))
    # pruning vs concentration mix per era
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    for e_name, em in eras.items():
        mechs = [dr6.get(s) for s in g6[em]]
        rows.append(dict(era=e_name, variable="prune_frac",
                         mean=round(float(np.mean([m == "EDGE_PRUNING" for m in mechs if m])), 3)))
    W("36_PRE_TRANSITION_POST_LAW.csv")(pd.DataFrame(rows).round(4))


# ================================================================ 37 new baseline vs scar
def new_baseline_vs_scar():
    rows = []
    g = GAIN_F
    gm = _gain_monthly()
    for yr in (2023, 2024, 2025, 2026):
        m = (dates.dt.year == yr) & np.isfinite(g)
        if m.sum() < 60:
            continue
        ym = gm[gm.index.year == yr]
        reg = _regime_of(ym.to_numpy())
        rows.append(dict(year=yr, n_days=int(m.sum()),
                         gain_mean=round(float(np.nanmean(g[m])), 4),
                         gain_std=round(float(np.nanstd(g[m])), 4),
                         low_regime_months=int((reg == "LOW").sum()),
                         high_regime_months=int((reg == "HIGH").sum()),
                         regime_transitions=len(run_episodes(reg[1:] != reg[:-1])) if len(reg) > 1 else 0))
    out = pd.DataFrame(rows)
    if len(out):
        year_means = out["gain_mean"].to_numpy()
        drift = float(np.nanmax(year_means) - np.nanmin(year_means))
        low_months_total = int(out["low_regime_months"].sum())
        hi_months_total = int(out["high_regime_months"].sum())
        if drift < 0.2 and low_months_total <= 2 and hi_months_total <= 2:
            verd = "NEW_BASELINE"
        elif low_months_total >= 3 and hi_months_total >= 3:
            verd = "REPEATED_SCAR(bimodal)"
        elif low_months_total >= 6 or hi_months_total >= 6:
            verd = "LONG_RECOVERY"
        else:
            verd = "MIXED"
    else:
        verd = "DATA_LIMITED"
    out["verdict"] = verd
    W("37_NEW_BASELINE_VS_SCAR.csv")(out.round(4))


# ================================================================ 38 reexcursion anatomy
def reexcursion_anatomy():
    rex = pd.read_csv(RETRO19 / "32_2022_REEXCURSIONS.csv")
    if len(rex) == 0 or "start" not in rex.columns:
        W("38_REEXCURSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rows = []
    for _, r in rex.iterrows():
        try:
            a = int(np.where(dates == pd.Timestamp(r["start"]))[0][0])
            b = int(np.where(dates == pd.Timestamp(r["end"]))[0][0])
        except Exception:
            continue
        rows.append(dict(start=r["start"], end=r["end"], dur=int(b - a + 1),
                         state=str(g6[a]),
                         gain=round(float(np.nanmean(GAIN_F[a:b + 1])), 3),
                         ceiling=round(float(np.nanmean(CEIL_F[a:b + 1])), 3),
                         transfer=round(float(np.nanmean(te_arr[a:b + 1])), 3),
                         threshold=round(float(np.nanmean(thr_pos[a:b + 1])), 3),
                         surface_propagation=round(float(np.nanmean(prop7[a:b + 1])), 3),
                         surface_volatility=round(float(np.nanmean(vol_med[a:b + 1])), 3),
                         dominant_forcing=max(fam_cols, key=lambda f: abs(_rhoXY(np.asarray(fams[f], dtype=float)[a:b + 1], p16[a:b + 1]))),
                         threshold_inversion=bool(np.any(_inversion_days()[a:b + 1]))))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("38_REEXCURSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("38_REEXCURSION_ANATOMY.csv")(out.round(3))


# ================================================================ 39 surface vs law generalization
def surface_vs_law_generalization():
    if len(ZDF) == 0:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="NO_EVENT_MACHINERY")]))
        return
    SURFACE_VARS = ["propagation", "reentry", "volatility", "breadth", "demand"]
    LAW_VARS = ["slope_FIELD", "ceiling_FIELD", "onset_FIELD", "slope_patch_mean",
                "ceiling_patch_mean", "onset_patch_mean", "exit_entropy", "exit_p1", "recruitment"]
    surf = [c for c in SURFACE_VARS if c in ZDF.columns]
    law = [c for c in LAW_VARS if c in ZDF.columns]
    if not surf or not law:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rex = pd.read_csv(RETRO19 / "32_2022_REEXCURSIONS.csv")
    rows = []
    for _, r in rex.iterrows():
        try:
            a = int(np.where(dates == pd.Timestamp(r["start"]))[0][0])
        except Exception:
            continue
        b = min(int(np.where(dates == pd.Timestamp(r["end"]))[0][0]) if np.any(dates == pd.Timestamp(r["end"])) else a + 30, ns - 1)
        end_norm = min(b + 60, ns - 1)
        if b - a < 5 or end_norm - b < 14:
            continue
        # peak abs z during episode vs 30d after
        def decay(cols):
            z = np.abs(ZDF[cols].to_numpy())
            pk = float(np.nanmax(z[a:b + 1]))
            post = float(np.nanmean(z[b + 1:end_norm]))
            return pk, post
        spk, spos = decay(surf)
        lpk, lpos = decay(law)
        rows.append(dict(start=r["start"], end=r["end"],
                         surface_peak_absz=round(spk, 2), surface_post_absz=round(spos, 2),
                         law_peak_absz=round(lpk, 2), law_post_absz=round(lpos, 2),
                         surface_decay=round(spk - spos, 2), law_decay=round(lpk - lpos, 2),
                         surface_precedes=bool(lpos > spos)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    n_pre = int(out["surface_precedes"].sum())
    if n_pre >= max(2, 0.6 * len(out)):
        out["verdict"] = "SURFACE_VS_LAW_CLOCKS_GENERALIZE"
    elif n_pre >= 1:
        out["verdict"] = "PARTIAL_GENERALIZATION"
    else:
        out["verdict"] = "SURFACE_VS_LAW_2022_LOCAL"
    W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(out.round(3))
# ================================================================ 41 old node reconnection
def old_node_reconnection():
    rows = []
    def add(node, prior_role, connection, changed):
        rows.append(dict(old_node=node, prior_role=prior_role,
                         mech20_connection=connection[:200], placement_changed=changed))
    # old promoted/local nodes, re-examined for NEW explanatory connections only
    add("POTENTIAL_REALIZATION", "ADAPTIVE_LAW",
        "M20 17-20: realization = constraint network with equifinality; THRESHOLD x TRANSFER 2x2 repaired; MI-based complementarity replaces M19 inconsistent SUBSTITUTABLE language", "yes")
    add("EQUIFINALITY", "ADAPTIVE_LAW",
        "M20 20: initiation equifinality (MECH-14) now mirrored downstream: realization shows multiple constraint patterns (realization equifinality)", "yes")
    add("BRANCH_CLOSURE", "ADAPTIVE_LAW",
        "M20 17: route deformation / exit pressure remain weakly coupled to gain; branch closure is a downstream expression of transfer+threshold, not an independent law", "yes")
    add("RANK_RECRUITMENT", "ADAPTIVE_LAW",
        "M20 08: not a differentiator in matched sat-with/without-delivery; remains rank7 coordinate, not a response-law node", "no")
    add("PHYSICAL_VS_SIGMA", "RESEARCH_ONLY",
        "M20 25-27: threshold inversion materiality audit reframes 'deep early activation' as composition-artifact-prone; physical/sigma question absorbed into materiality gate", "yes")
    add("STATE_TOPOLOGY", "STRUCTURAL_CORE",
        "Frozen; M20 uses states only as conditioning strata (08 matching, 14 2x2, 29 hysteresis) - no structural change", "no")
    add("SPATIAL_ACTIVATION", "STRUCTURAL_CORE",
        "M20 30-31: spatial character (broad vs rank-local) of forcing families reuses patch activation correlations - consistent with frozen topology", "no")
    add("SATURATION_LAW", "ADAPTIVE_LAW",
        "M20 03-07: gain + ceiling confirmed as the 2-coordinate saturation description; slope x ceiling surface defines response environments; saturation meaning is response-dependent", "yes")
    add("THRESHOLD_BAND", "ADAPTIVE_LAW",
        "M20 14-16: threshold position is the strongest single realization coordinate; complements transfer", "no")
    add("BIRTH_GEOMETRY", "ADAPTIVE_LAW",
        "M20 21-24: failure = load-vs-resolution mismatch; recovery path mapped (which variable normalizes first)", "yes")
    add("2022_STRUCTURAL_SCAR", "RESEARCH_ONLY",
        "M20 34-39: era hypotheses + changepoint agreement + surface-vs-law generalization tested; verdict finalizes 2022 interpretation", "yes")
    out = pd.DataFrame(rows)
    W("41_OLD_NODE_RECONNECTION.csv")(out)


# ================================================================ 42 promote park dissolve
def promote_park_dissolve():
    rows = []
    def add(obj, os_role, action, note):
        rows.append(dict(object=obj, os_role=os_role, action=action, note=note[:200]))
    add("RESPONSE_LAW_GAIN_CEILING", "ADAPTIVE_LAW", "FREEZE",
        "gain+ceiling = 2-coordinate response description (anti-coupled r=-0.85, together explain 96% of node motion); unclamped fit only; see 02")
    add("RESPONSE_GAIN_STATE", "ADAPTIVE_LAW", "PROMOTE",
        "CONTINUOUS_GAIN_COORDINATE: autocorr 0.99 (lag1)/0.66 (lag30), near-absorbing tercile states; era-adaptive; see 04")
    add("CEILING_ROLE", "ADAPTIVE_LAW", "LOCAL",
        "regime-local scaling (H4): ceiling varies by era (0.67 pre -> 0.93 2022 -> 1.01 2025-26), anti-coupled with gain, NOT enabler/absorber; see 05")
    add("SLOPE_X_CEILING_SURFACE", "ADAPTIVE_LAW", "PROMOTE",
        "distinct environments: HI_GAIN_LO_CEIL delivers 0.40 vs LO_GAIN_HI_CEIL 0.31; see 06")
    add("SATURATION_WITHOUT_DELIVERY", "LOCAL_PHYSICS", "PROMOTE",
        "matched (state/gain/ceiling/demand/sat): impaired transfer (-0.08,p<0.05) + lower concentration-release (-0.66) + higher volatility forcing (+0.38), NOT exit structure; see 08")
    add("SATURATION_FAILURE_TRANSITIONS", "LOCAL_PHYSICS", "PARK",
        "sterile saturation resolves fast (decays 1-3d; state change 82% @14d; realization 51% @30d); no new mechanism beyond 08; see 09")
    add("SATURATION_TO_DELIVERY", "LOCAL_PHYSICS", "LOCAL",
        "first-changed variable: threshold 31% / forcing 30% / exit-pressure 27%; transfer rarely first (3%); see 10")
    add("CAPACITY_ROLE", "ADAPTIVE_LAW", "LOCAL",
        "ABSORPTIVE_CAPACITY: delivery falls monotonically with capacity in every load band (HIGH_LOAD Q1 0.81 -> Q4 0.45); state-structural attribute; see 11-12")
    add("THRESHOLD_X_TRANSFER", "ADAPTIVE_LAW", "PROMOTE",
        "2x2 repaired: THR_HI_TE_HI 0.79 vs THR_LO_TE_LO 0.12; MI + interaction logit classify SUBSTITUTES with conditional complementarity at high transfer; see 14-15")
    add("REALIZATION_CORE", "ADAPTIVE_LAW", "PROMOTE",
        "single-coordinate core = TRANSFER (heldout AUC 0.83); threshold 0.72, capacity 0.69, gain 0.54; extra coords add nothing; see 16")
    add("REALIZATION_NETWORK", "ADAPTIVE_LAW", "PROMOTE",
        "descriptive graph: THRESHOLD~FORCING 0.92, CAPACITY suppresses THRESHOLD/TRANSFER (-0.46/-0.50), EXIT_PRESSURE~ROUTE_DEFORM 0.43; see 17-18")
    add("REALIZATION_MINIMAL_SETS", "ADAPTIVE_LAW", "PROMOTE",
        "DELIVERY: TRANSFER alone 0.73, +THRESHOLD 0.79, +GAIN 0.88; STALL: CAPACITY+NON_SATURATED 0.80; see 19")
    add("REALIZATION_EQUIFINALITY", "ADAPTIVE_LAW", "PROMOTE",
        "MULTIPLE_REALIZATION_PATHS: 62 distinct met-patterns, top <11%; realization equifinality mirrors M14 initiation equifinality; see 20")
    add("BIRTH_LOAD_RESOLUTION_MISMATCH", "ADAPTIVE_LAW", "PROMOTE",
        "at INITIATION aborted births: routes OPENING (+0.33) while load rises (+0.15) vs viable routes PRUNING (-0.80) with load falling; resolution_d 1.65; see 22")
    add("BIRTH_RECOVERY_PATH", "ADAPTIVE_LAW", "LOCAL",
        "first restoration: routes prune 38% / demand cools 35% / threshold normalizes 22%; transfer rarely first; see 24")
    add("THRESHOLD_INVERSION", "RESEARCH_ONLY", "DEMOTE",
        "materiality audit: activation gaps 0.001-0.03 (5.7% of patch sigma) during thr50 'inversions' -> COMPOSITION_ARTIFACT; mechanism analysis demoted (25-27)")
    add("DEEP_HYSTERESIS", "LOCAL_PHYSICS", "PARK",
        "final reconciliation: STATE_DOMINANT (state spread 0.040 > depth spread 0.009); 6C_2 strongest (0.12-0.16); depth gradient only inside 6C_0; no global object; see 28-29")
    add("FORCING_FUNCTIONAL_MAP", "ADAPTIVE_LAW", "PROMOTE",
        "functional dimensions without scalar collapse: VOLATILITY/STABLECOIN/RANK_RECRUITMENT = persistent background fields; PARTICIPATION/CONC_RELEASE/PHYSICAL = impulses; response fns: MOVE_CEILING/MOVE_SLOPE/MOVE_ONSET; see 30-32")
    add("FORCING_INTERACTIONS_DEEP", "ADAPTIVE_LAW", "LOCAL",
        "supported pairs alter threshold most (PARTICIPATIONxVOLATILITY -0.46, PARTICIPATIONxBTC -0.29); route pressure/transfer/gain mostly additive; see 33")
    add("2022_RESPONSE_GAIN_ERA", "RESEARCH_ONLY", "PROMOTE",
        "H3_MULTIPLE_REGIME_MODULATIONS: 21 monthly gain-regime transitions, 5 LOW runs, 7 HIGH runs; no single era break agreed (SEG finds 2021-12/2022-12/2024-12 collapses); see 34-38")
    add("SURFACE_VS_LAW_CLOCKS", "ADAPTIVE_LAW", "LOCAL",
        "PARTIAL_GENERALIZATION: surface precedes law in first 2 post-2022 excursions only; later excursions law decays at least as fast; 2022-anchored clock, see 39")
    add("RESPONSELAW_STATE", "ADAPTIVE_LAW", "PROPOSAL",
        "OS runtime object proposal (gain/ceiling/baseline_version/deviation/changepoint/recovery_status); see 40_RESPONSE_LAW_STATE_PROPOSAL.md")
    W("42_PROMOTE_PARK_DISSOLVE.csv")(pd.DataFrame(rows))


# ================================================================ 43 null and failed
def null_failed():
    rows = []
    for f in sorted(OUT.glob("*.csv")):
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        na = int(d.isna().sum().sum()); total = int(d.size)
        flags = []
        for val in ("DATA_LIMITED", "NO_EVENT_BLOCK_FOUND", "NULL", "DATA_BLOCKED",
                    "NO_STABLE", "ARTIFACT", "WEAK", "DEMOTED", "COMPOSITION_ARTIFACT",
                    "NO_CONVERSIONS", "NO_SUPPORTED_INTERACTIONS", "NONE", "DATA_BLOCKED(panel-aggregate)"):
            for c in d.columns:
                nv = int((d[c].astype(str) == val).sum())
                if nv:
                    flags.append(f"{val}:{nv}")
        rows.append(dict(file=f.name, n_rows=len(d), n_cells=total, null_cells=na,
                         null_frac=round(na / max(total, 1), 3),
                         failed_flags=";".join(sorted(set(flags))[:8])))
    W("43_NULL_AND_FAILED_RESULTS.csv")(pd.DataFrame(rows))


# ================================================================ RUNNER
if __name__ == "__main__":
    response_law_decomposition()
    saturation_response_coords()
    response_gain_state()
    ceiling_role()
    slope_ceiling_surface()
    saturation_position_by_response()
    saturation_failure_matched()
    saturation_failure_transitions()
    saturation_to_delivery()
    capacity_interpretation()
    capacity_response_law()
    threshold_transfer_2x2()
    threshold_transfer_interaction()
    realization_core()
    realization_relations()
    realization_constraint_network()
    realization_minimal_sets()
    realization_equifinality()
    birth_failure_deep()
    load_resolution_mismatch()
    birth_failure_surface()
    birth_recovery_path()
    threshold_inversion_materiality()
    threshold_inversion_post_audit()
    threshold_inversion_function()
    hysteresis_reconciliation()
    hysteresis_survival_map()
    forcing_functional_dimensions()
    forcing_functional_map()
    forcing_temporal_scales()
    forcing_interaction_deep()
    era_hypotheses()
    response_gain_changepoints()
    pre_transition_post_law()
    new_baseline_vs_scar()
    reexcursion_anatomy()
    surface_vs_law_generalization()
    old_node_reconnection()
    promote_park_dissolve()
    null_failed()
    print("MECH-20 BUILD COMPLETE")
