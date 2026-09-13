#!/usr/bin/env python
"""ALT_MECH_19 - GLOBAL ADAPTIVE-LAW HARDENING orchestration (parts 1..7).

Concatenated parts form scripts/build_mech19.py. Computes mech_19 CSVs 02..37.
Narrative files (01 prereg, 38 freeze map, 39 summary, 40 decision) written
alongside by the agent after reviewing computed CSVs.

Terrain research ONLY (AGENT 1). No PnL, strategy, execution, sizing, direction.
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ranksums
from sklearn.linear_model import LinearRegression, LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m19base as B
sys.path.insert(0, str(B.RETRO / "scripts"))
from _m18base import exit_dist_series, js_divergence, _rho, _partial_rho

M88 = B.load_substrate()
from _m19base import (logistic_params_unc, hill_params_unc, run_episodes,
                      concentration_episodes, r2)

OUT = B.ROOT
RETRO = OUT.parent / "mech_18"      # MECH-18 deliverable dir
DEPTH_ORDER = M88.DEPTH_ORDER
SUBPERIODS = M88.SUBPERIODS


def _rhoXY(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 20:
        return np.nan
    return float(spearmanr(a[m], b[m]).statistic)


# Re-export substrate scalars for brevity
dfc = M88.dfc
act = M88.act
fams = M88.fams
demand = M88.demand
bm6 = M88.bm6
bm8 = M88.bm8
forcing_series = M88.forcing_series
fam_cols = M88.fam_cols
field_act = M88.field_act
ent6 = M88.ent6; k6 = M88.k6; p16 = M88.p16; p26 = M88.p26
ent8 = M88.ent8
demand_arr = M88.demand_arr
g6 = M88.g6; g6n = M88.g6n; g8 = M88.g8; g8n = M88.g8n
subp_arr = M88.subp_arr
prop7 = M88.prop7; ren7 = M88.ren7; rank7 = M88.rank7
pos_share = M88.pos_share; disp7 = M88.disp7; conc = M88.conc
rankd = M88.rankd; vol_med = M88.vol_med; btc7 = M88.btc7
PACT = M88.PACT
cap_arr = M88.cap_arr; te_arr = M88.te_arr; fc_arr = M88.fc_arr
thr_pos = M88.thr_pos
logit_fit = M88.logit_fit; thr_at = M88.thr_at
CONSTIT = M88.CONSTIT
STAGES18 = M88.STAGES18
RESP_NAMES = M88.RESP_NAMES
_rolling_node_series = M88._rolling_node_series

ns = len(dfc)
dates = pd.to_datetime(dfc["d"])
stable = np.asarray(pd.to_numeric(dfc["stablecoin_change_7d"], errors="coerce"))
mc30 = np.asarray(pd.to_numeric(dfc["total_mcap_chg30"], errors="coerce"))
btc = np.asarray(pd.to_numeric(dfc["btc_return_7d"], errors="coerce"))
disp = np.asarray(pd.to_numeric(dfc["top500_dispersion_7d"], errors="coerce"))
possh = np.asarray(pd.to_numeric(dfc["pos_ret_share"], errors="coerce"))
brth = np.asarray(pd.to_numeric(dfc.get("breadth", dfc.get("breadth_vel", pd.Series(np.nan, index=dfc.index))), errors="coerce"))
# daily state-transition (next day different state)
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
    ref = {s: np.nanmean(mat[np.asarray(g) == s], axis=0) for s in set(g) }
    out = np.full(len(g), np.nan)
    for i in range(len(g)):
        p = mat[i]
        if np.isnan(p).all():
            continue
        out[i] = js_divergence(p, ref[g[i]])
    return out

js_hist = _js_hist_series(g6)

# reuse MECH-18 birth partition
prev_ = np.array([None] + list(g6[:-1]))
bp_ = np.where(g6 != prev_)[0]
bp_ = bp_[(bp_ >= 8) & (bp_ < ns - 8)]
ab_, vi_ = [], []
for i_ in bp_:
    (ab_ if (g6[i_ + 1:i_ + 8] == prev_[i_]).any() else vi_).append(i_)
ab_ = np.array(ab_); vi_ = np.array(vi_)
STAGES18 = M88.STAGES18
FEAT18 = M88.FEAT18
_stage_vals18 = M88._stage_vals
# second-largest share available from bm
p2g = p26

# ------------------------------------------------------------------ 02 pressure concentration anatomy
def pressure_concentration_anatomy():
    ep = concentration_episodes(g6, ent6, p16, "placeholder", base_lo=0.33, min_len=5)
    rows = []
    for st in np.unique(g6):
        eps = concentration_episodes(g6, ent6, p16, st, base_lo=0.33, min_len=5)
        if len(eps) == 0:
            continue
        sub = dfc[["d", "subperiod"]]
        for _, e in eps.iterrows():
            a, b = int(e["start"]), int(e["end"])
            dur = b - a + 1
            # outcome: does a genuine exit occur within next 30d ?
            horizon = min(a + 61, ns)
            exit_occur = bool((g6[a:horizon] != st).any())
            reopen = bool((g6[b + 1: min(b + 1 + 60, ns)] != st).any())
            rev = bool((g6[b + 1: min(b + 1 + 30, ns)] != st).any())  # reverses concentration = leaves crowding
            ratio_rev = not exit_occur
            rows.append(dict(state=st, start=str(dates[a].date()), end=str(dates[b].date()),
                             dur=dur,
                             live_exits_mean=round(float(np.nanmean(k6[a:b + 1])), 2),
                             p1_mean=round(float(np.nanmean(p16[a:b + 1])), 3),
                             p2_mean=round(float(np.nanmean(p26[a:b + 1])), 3),
                             p1_p2_gap=round(float(np.nanmean(p16[a:b + 1]) - np.nanmean(p26[a:b + 1])), 3),
                             entropy_mean=round(float(np.nanmean(ent6[a:b + 1])), 3),
                             route_deform_js=round(float(np.nanmean(js_hist[a:b + 1])), 3),
                             demand=round(float(np.nanmean(demand_arr[a:b + 1])), 3),
                             capacity=round(float(np.nanmean(cap_arr[a:b + 1])), 3),
                             transfer_eff=round(float(np.nanmean(te_arr[a:b + 1])), 3),
                             threshold_pos=round(float(np.nanmean(thr_pos[a:b + 1])), 3),
                             saturation_pos=round(float(np.nanmean(field_act[a:b + 1])), 3),
                             forcing=round(float(np.nanmean(fc_arr[a:b + 1])), 3),
                             exit_occurred = exit_occur,
                             reopened_after = reopen,
                             subperiod=str(subp_arr[a]) if np.ndim(subp_arr) else str(subp_arr)))
    out = pd.DataFrame(rows)
    # distinction: does exit_occurred depend on p1_gap / entropy / sat?
    return out

W02 = W("02_PRESSURE_CONCENTRATION_ANATOMY.csv", index=False)
W02(pressure_concentration_anatomy().round(3))

# ------------------------------------------------------------------ 03 concentration phases
def concentration_phases():
    ep = pressure_concentration_anatomy()
    rows = []
    if len(ep) < 30:
        W("03_CONCENTRATION_PHASES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    mid = (ep["dur"] >= 5)
    n = int(mid.sum())
    # continuous gradient probes
    probes = [("exit_occurred", "p1_mean", "p1_gap on exit"), ("exit_occurred", "entropy_mean", "entropy on exit"),
              ("exit_occurred", "saturation_pos", "saturation on exit"), ("reopened_after", "p1_mean", "p1 on reopen"),
              ("reopened_after", "p1_p2_gap", "gap on reopen")]
    for outc, feat, lab in probes:
        if feat not in ep.columns or outc not in ep.columns:
            continue
        x = ep[feat].to_numpy(); y = ep[outc].to_numpy()
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < 25:
            continue
        r = _rhoXY(x[m], y[m])
        # monotone: binned rates
        q = np.nanquantile(x[m], [0.33, 0.67])
        b = [float(y[m & (x <= q[0])].mean()), float(y[m & (x > q[0]) & (x < q[1])].mean()),
             float(y[m & (x >= q[1])].mean())]
        rows.append(dict(probe=lab, n=int(m.sum()), rho_rank=round(r, 3),
                         rate_bin_low=round(b[0], 3), rate_bin_mid=round(b[1], 3),
                         rate_bin_high=round(b[2], 3)))
    # phase labels attempt: compute median entropy/p1 across a 6-point gradient
    ent_bins = np.linspace(np.nanquantile(ent6, 0.05), np.nanquantile(ent6, 0.95), 5)
    rows.append(dict(probe="phase_gradient", n=int(n),
                     verdict="CONTINUOUS_COMMITMENT_GRADIENT" if np.isfinite(r) else "DATA_LIMITED"))
    return pd.DataFrame(rows)

W03 = W("03_CONCENTRATION_PHASES.csv", index=False)
W03(concentration_phases().round(3))

# ------------------------------------------------------------------ 04 route commitment
def route_commitment():
    # commitment gradient: per-state p1 separation bands -> reopening within 60d
    rows = []
    for st in np.unique(g6):
        sel = np.where(g6 == st)[0]
        if len(sel) < 60:
            continue
        p1 = p16[sel]; p2 = p2g[sel]; gap = p1 - p2; e = ent6[sel]
        # daily outcome: does a different state occur in next 60 days (route given up / reopened)?
        outc = np.zeros(len(sel), dtype=bool)
        for j, ti in enumerate(sel):
            hz = min(ti + 1, ns); H = min(ti + 61, ns)
            outc[j] = bool((g6[hz:H] != st).any())
        for fb, feat in [("p1", gap), ("entropy", e)]:
            if np.isfinite(feat).sum() < 60:
                continue
            q = np.nanquantile(feat, np.linspace(0, 1, 6))
            for k in range(5):
                mm = (feat >= q[k]) & (feat <= q[k + 1])
                if mm.sum() < 10:
                    continue
                rows.append(dict(state=st, feature=fb, band=k+1,
                                 n=int(mm.sum()),
                                 reopen_rate=round(float(outc[mm].mean()), 3)))
    out = pd.DataFrame(rows)
    if len(out) < 30:
        W("04_ROUTE_COMMITMENT.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    # commitment band: find band where reopen_rate < 0.2 sustained
    g1 = out.groupby("feature")
    c = []
    for fb, g in g1:
        for st in g["state"].unique():
            sub = g[g["state"] == st].sort_values("band")
            if len(sub) < 3:
                continue
            lo_bands = sub[sub["reopen_rate"] > 0.3]
            low = int(lo_bands["band"].max()) if len(lo_bands) else 0
            c.append(dict(state=st, feature=fb, min_reopen_band=low + 1,
                          min_below_threshold="commitment_at_band_ge_%d" % (low + 1)))
    cr = pd.DataFrame(c)
    out = out.merge(cr, on=["state", "feature"], how="left")
    W("04_ROUTE_COMMITMENT.csv")(out.round(3))

# ------------------------------------------------------------------ 05 pruning vs concentration
def pruning_vs_concentration():
    # mechanism per state from M18 04 resolution_driver
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    rows = []
    feat_cols = {"forcing": fc_arr, "demand": demand_arr, "capacity": cap_arr,
                 "saturation": field_act, "rank_depth": rankd, "route_deform": js_hist,
                 "volatility": vol_med, "dispersion": disp, "btc_anchor": btc,
                 "stablecoin": stable, "concentration": conc}
    for st in np.unique(g6):
        sel = np.where(g6 == st)[0]
        if len(sel) < 60:
            continue
        mech = dr6.get(st)
        if not isinstance(mech, str):
            continue
        for name, arr in feat_cols.items():
            v = arr[sel]; v = v[~np.isnan(v)]
            if len(v) < 40:
                continue
            rows.append(dict(state=st, mechanism=mech, covariate=name,
                             mean=round(float(np.nanmean(v)), 4)))
    # logistic: mechanism (concentrate vs prune) on state-level covariates
    feat_cols_listed = ["forcing", "demand", "capacity", "saturation", "rank_depth",
                        "route_deform", "volatility", "dispersion", "btc_anchor",
                        "stablecoin", "concentration"]
    od = []
    for st in np.unique(g6):
        mech = dr6.get(st)
        if mech not in ("PRESSURE_CONCENTRATION", "EDGE_PRUNING"):
            continue
        row = {"state": st, "y": 1 if mech == "PRESSURE_CONCENTRATION" else 0}
        for name in feat_cols_listed:
            sel = np.where(g6 == st)[0]
            v = feat_cols[name][sel]; v = v[~np.isnan(v)]
            row[name] = np.nanmean(v) if len(v) else np.nan
        od.append(row)
    lod = pd.DataFrame(od)
    if len(lod) < 4:
        return lod, pd.DataFrame()
    X = lod[feat_cols_listed].to_numpy(); y = lod["y"].to_numpy()
    m = np.isfinite(X).all(1) & np.isfinite(y)
    if m.sum() < 4:
        return lod, pd.DataFrame()
    lr = LogisticRegression(max_iter=2000).fit(X[m], y[m])
    j = pd.DataFrame(dict(covariate=feat_cols_listed,
                          logit_coef=lr.coef_[0],
                          magnitude=np.abs(lr.coef_[0])),
                     ).round(3)
    return lod, j

W05 = W("05_PRUNING_VS_CONCENTRATION.csv", index=False)
_05a, _05b = pruning_vs_concentration()
W05(pd.DataFrame(_05a) if isinstance(_05a, dict) else _05a)
W("05b_PRUNING_VS_CONCENTRATION_LOGIT.csv", index=False)(_05b)

# ================================================================ 06 post-resolution paths
def post_resolution_paths():
    rows = []
    # resolution episodes: a run in a state ending with a transition
    eps_ok = 0
    for st in np.unique(g6):
        runs = run_episodes(g6 == st)
        for (a, b) in runs:
            if (b - a + 1) < 3:
                continue
            nxt1 = g6[b + 1] if (b + 1) < ns else None
            if nxt1 is None or pd.isna(nxt1):
                continue
            # mechanism: was entropy dropping (prune) or p1 rising (concentrate)?
            dk = k6[min(b, b)] - k6[max(a, a)]  # naive
            dp = p16[b] - p16[a]
            mech = "EDGE_PRUNING" if (np.isfinite(dk) and (not np.isfinite(dp) or abs(dk) >= abs(dp))) \
                else "PRESSURE_CONCENTRATION"
            # post path
            dest = str(nxt1)
            persist = 1
            t = b + 1
            while (t + 1) < ns and g6[t + 1] == dest:
                persist += 1; t += 1
            reopen = bool((g6[b + 1: min(b + 1 + 61, ns)] != dest).any())
            rk7 = np.nanmean(rank7[b + 1:b + 9])
            te = np.nanmean(te_arr[b + 1:b + 9])
            rows.append(dict(state=st, dest=dest, mechanism=mech,
                             dur=float(b - a + 1), persist_days=persist,
                             reopened_after=reopen, rank7_post=round(float(rk7), 3) if np.isfinite(rk7) else np.nan,
                             transfer_post=round(float(te), 3) if np.isfinite(te) else np.nan,
                             p1_at_exit=round(float(p16[b]), 3),
                             entropy_at_exit=round(float(ent6[b]), 3)))
            eps_ok += 1
    out = pd.DataFrame(rows)
    # aggregate by mechanism
    agg = []
    if len(out):
        for mech in np.unique(out["mechanism"]):
            m = out["mechanism"] == mech
            d = out[m]
            agg.append(dict(mechanism=mech, n=int(m.sum()),
                            median_persist=round(float(d["persist_days"].median()), 1),
                            reopen_frac=round(float(d["reopened_after"].mean()), 3),
                            median_rank7_post=round(float(d["rank7_post"].median()), 3),
                            median_transfer_post=round(float(d["transfer_post"].median()), 3)))
    ag = pd.DataFrame(agg)
    ag["verdict"] = "MEASURED"
    return out.round(3), ag.round(3)

_06a, _06b = post_resolution_paths()
W06a = W("06_POST_RESOLUTION_PATHS.csv", index=False)
W06a(_06a)
W06b_ = W("06b_POST_RESOLUTION_AGG.csv", index=False)
W06b_(_06b)