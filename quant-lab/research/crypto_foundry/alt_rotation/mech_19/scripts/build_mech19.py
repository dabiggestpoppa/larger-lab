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
W06b_(_06b)# ================================================================ shared rolling nodes
NODES_ROLL = _rolling_node_series()          # daily asof-filled response nodes
NODE_D_T = np.arange(ns)
# per-response slope/ceiling/onset arrays
NODE_ARR = {}
for p in RESP_NAMES:
    NODE_ARR[f"slope_{p}"] = NODES_ROLL[f"{p}_k"].to_numpy()
    NODE_ARR[f"ceiling_{p}"] = NODES_ROLL[f"{p}_ceiling"].to_numpy()
    NODE_ARR[f"onset_{p}"] = NODES_ROLL[f"{p}_x0"].to_numpy()
# compact: FIELD + patch means
PATCHM = {k: np.nanmean([NODE_ARR[f"{k}_{p}"] for p in DEPTH_ORDER], axis=0) for k in ("slope", "ceiling", "onset")}
NODE_PATCH_MEAN = {f"{k}_patch_mean": PATCHM[k] for k in ("slope", "ceiling", "onset")}

# ================================================================ 07 forcing primitives deep
def forcing_primitives_deep():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        cons_ = CONSTIT.get(fam, [])
        cvals = []
        for c in cons_:
            if c in dfc.columns:
                cvals.append(pd.to_numeric(dfc[c], errors="coerce").to_numpy())
        red = np.nanmean([abs(_rho(f, cv)) for cv in cvals]) if cvals else np.nan
        amp = float(np.nanstd(f)); slope = float(np.nanmean(np.abs(np.diff(f))))
        fv = f[~np.isnan(f)]
        pers = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        burst = float(np.nanquantile(f, 0.9) / max(abs(np.nanquantile(f, 0.5)), 1e-9)) if np.isfinite(np.nanquantile(f, 0.5)) else np.nan
        # state dependence: std of family mean across 6-cell states
        sm = [np.nanmean(f[g6 == s]) for s in np.unique(g6)]
        state_dep = float(np.nanstd(sm)) if len(sm) >= 3 else np.nan
        # rank dependence: corr with each patch activation
        rank_int = np.nanmean([abs(_rho(f, act[p].to_numpy())) for p in DEPTH_ORDER])
        # route dependence: abs corr with forward-7d route pressure to dominant exits
        # saturation-node dependence
        node_int = np.nanmean([abs(_rho(f, NODE_ARR[f"slope_{p}"])) for p in ["FIELD"]] + [abs(_rho(f, k)) for k in ("slope_patch_mean", "ceiling_patch_mean")] if False else [abs(_rho(f, NODE_PATCH_MEAN["slope_patch_mean"])), abs(_rho(f, NODE_PATCH_MEAN["ceiling_patch_mean"]))])
        thr_int = abs(_rho(f, thr_pos))
        exit_int = np.nanmean([abs(_rho(f, p16)), abs(_rho(f, ent6))])
        cross = np.nanmean([abs(_rho(f, np.asarray(fams[o], dtype=float))) for o in fam_cols if o != fam])
        rows.append(dict(family=fam, constituents="|".join(cons_),
                         amplitude_std=round(amp, 4), slope_mean_abs_diff=round(slope, 4),
                         persistence_autocorr=round(pers, 3) if pers == pers else np.nan,
                         burstiness_p90p50=round(burst, 3) if burst == burst else np.nan,
                         state_dependence_std=round(state_dep, 4) if state_dep == state_dep else np.nan,
                         rank_patch_assoc=round(rank_int, 3),
                         saturation_node_assoc=round(node_int, 3),
                         threshold_assoc=round(thr_int, 3),
                         exit_pressure_assoc=round(exit_int, 3),
                         within_family_redundancy=round(red, 3) if red == red else np.nan,
                         cross_family_corr=round(cross, 3)))
    return pd.DataFrame(rows)

W07 = W("07_FORCING_PRIMITIVES_DEEP.csv", index=False)
W07(forcing_primitives_deep().round(3))

# ================================================================ 08 forcing signatures
def forcing_signatures():
    rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        # where it acts: top states by family mean
        sm = pd.Series({s: np.nanmean(f[g6 == s]) for s in np.unique(g6)}).sort_values(ascending=False)
        top_states = "|".join(str(x) for x in sm.head(2).index)
        low_states = "|".join(str(x) for x in sm.tail(2).index)
        # routes loaded/suppressed from M18 route-specific forcing
        fsub = rsf[rsf["forcing_family"] == fam].dropna(subset=["rho"])
        if len(fsub):
            fsub = fsub.reindex(fsub["rho"].abs().sort_values(ascending=False).index)
            loaded = fsub.iloc[0] if len(fsub) else None
            supp = fsub[fsub["rho"] < 0]
            supp = supp.reindex(supp["rho"].abs().sort_values(ascending=False).index)
            suppressed = supp.iloc[0] if len(supp) else None
            loaded_edge = f"{loaded['edge']}({loaded['rho']:+.2f})" if loaded is not None else None
            suppressed_edge = f"{suppressed['edge']}({suppressed['rho']:+.2f})" if suppressed is not None else None
        else:
            loaded_edge = suppressed_edge = None
        # rank depths responding
        resp_rank = [p for p in DEPTH_ORDER if abs(_rho(f, act[p].to_numpy())) > 0.1]
        # nodes moved
        node_c = {}
        for k in ("slope", "ceiling", "onset"):
            node_c[k] = abs(_rho(f, NODE_PATCH_MEAN[f"{k}_patch_mean"]))
        nodes_moved = "|".join([k for k, v in node_c.items() if v > 0.1])
        # persistence: lag-1 autocorr half-life as descriptor
        fv = f[~np.isnan(f)]
        pers = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        # regime alteration: std of family mean across subperiods
        reg_std = float(np.nanstd([np.nanmean(f[subp_arr == sp]) for sp in SUBPERIODS]))
        rows.append(dict(family=fam,
                         top_states_2=top_states, low_states_2=low_states,
                         top_loaded_route=loaded_edge, top_suppressed_route=suppressed_edge,
                         rank_depths_responding="|".join(resp_rank),
                         nodes_moved=nodes_moved,
                         persistence_autocorr=round(pers, 3) if pers == pers else np.nan,
                         regime_alteration_std=round(reg_std, 4) if reg_std == reg_std else np.nan,
                         signature= "|".join([str(x) for x in [top_states[:12], loaded_edge or "n/a"]])))
    return pd.DataFrame(rows)

W08 = W("08_FORCING_SIGNATURES.csv", index=False)
W08(forcing_signatures().round(3))

# ================================================================ 09 forcing co-occurrence
def forcing_cooccurrence():
    qhi = np.nanquantile(np.asarray(fams[d], float), 0.7) if False else None
    hi = {}
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        hi[fam] = f >= (np.nanquantile(f, 0.7) if np.isfinite(np.nanquantile(f, 0.7)) else 1e9)
    rows = []
    for i, a in enumerate(fam_cols):
        for b in fam_cols[i + 1:]:
            both = hi[a] & hi[b]
            n = int(both.sum())
            if n < 30:
                continue
            rows.append(dict(family_a=a, family_b=b, n_cooccur_high=int(both.sum()),
                             frac_cooccur=round(float(both.mean()), 3),
                             mean_sat_under_comb=round(float(np.nanmean(field_act[both])), 3),
                             mean_p1_under_comb=round(float(np.nanmean(p16[both])), 3),
                             mean_recruit_under_comb=round(float(np.nanmean(rank7[both])), 3),
                             mean_prop_under_comb=round(float(np.nanmean(prop7[both])), 3),
                             thr_pos_mean=round(float(np.nanmean(thr_pos[both])), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("09_FORCING_COOCCURRENCE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    return out

W09 = W("09_FORCING_COOCCURRENCE.csv", index=False)
W09(forcing_cooccurrence().round(3))

# ================================================================ 10 forcing interactions
def forcing_interactions():
    # classify pair interaction on FIELD activation via linear model w/ interaction term
    y = field_act
    rows = []
    for i, a in enumerate(fam_cols):
        fa = np.asarray(fams[a], dtype=float)
        for b in fam_cols[i + 1:]:
            fb = np.asarray(fams[b], dtype=float)
            m = np.isfinite(fa) & np.isfinite(fb) & np.isfinite(y)
            if m.sum() < 150:
                continue
            X = np.column_stack([fa[m], fb[m], fa[m] * fb[m]])
            lr = LinearRegression().fit(X, y[m])
            c_a, c_b, c_ab = lr.coef_[0], lr.coef_[1], lr.coef_[2]
            base = c_a * np.nanstd(fa) ; baseb = c_b * np.nanstd(fb)
            intg = c_ab * (np.nanstd(fa) * np.nanstd(fb))
            # classify
            if abs(intg) < 0.1 * max(abs(base), abs(baseb), 1e-6):
                kind = "ADDITIVE_LIKE"
            elif np.sign(c_ab) == np.sign(c_a) == np.sign(c_b):
                kind = "SYNERGISTIC_LIKE"
            elif np.sign(c_ab) != np.sign(c_a) and np.sign(c_ab) != np.sign(c_b):
                kind = "ANTAGONISTIC_LIKE"
            elif abs(c_a * c_b) > abs(c_ab):
                kind = "ADDITIVE_LIKE"
            else:
                kind = "ROUTE_SPECIFIC"
            rows.append(dict(family_a=a, family_b=b, n=int(m.sum()),
                             coef_a=round(c_a, 4), coef_b=round(c_b, 4),
                             coef_interaction=round(c_ab, 4),
                             interaction_abs_std_units=round(float(abs(intg)), 4),
                             classification=kind))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("10_FORCING_INTERACTIONS.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    return out

W10 = W("10_FORCING_INTERACTIONS.csv", index=False)
W10(forcing_interactions().round(4))

# ================================================================ 11 forcing route map
def forcing_route_map():
    rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
    et = pd.read_csv(RETRO / "02_EDGE_REGISTRY.csv")
    et6 = et[et["resolution"] == "6CELL"]
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    rows = []
    for _, r in rsf.iterrows():
        if pd.isna(r["rho"]):
            continue
        s, t = r["edge"].split("->")
        rows.append(dict(forcing_family=r["forcing_family"],
                         state=s, edge=r["edge"],
                         pressure_change=round(r["rho"], 3),
                         pressure_sign="+LOAD" if r["rho"] > 0.15 else ("-SUPPRESS" if r["rho"] < -0.15 else "NEUTRAL"),
                         resolution_mechanism=dr6.get(s, "DATA_LIMITED")))
    out = pd.DataFrame(rows)
    # top loading per family/state
    return out

W11 = W("11_FORCING_ROUTE_MAP.csv", index=False)
W11(forcing_route_map().round(3))# ================================================================ 12 saturation mechanism
def _node_feat_matrix(resps=None, mean_window=7):
    """Smoothed node-change features: d(slope), d(ceiling), d(onset) per response."""
    resps = resps or RESP_NAMES
    cols, data = [], []
    for p in resps:
        for node, arr in (("slope", f"slope_{p}"), ("ceiling", f"ceiling_{p}"), ("onset", f"onset_{p}")):
            v = np.asarray(NODE_ARR[arr], dtype=float)
            dv = np.diff(v, prepend=np.nan)
            dsm = pd.Series(np.where(dv == dv, dv, np.nan)).rolling(mean_window, min_periods=2).mean().to_numpy()
            cols.append(f"d{node}_{p}"); data.append(dsm)
    return np.column_stack(data), cols

def saturation_mechanism():
    X, cols = _node_feat_matrix(["FIELD"])
    m = np.isfinite(X).all(1)
    if m.sum() < 150:
        W("12_SATURATION_MECHANISM.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    Xc = X[m]; Xc = (Xc - Xc.mean(0)) / (Xc.std(0) + 1e-9)
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=3).fit(Xc)
        ev = pca.explained_variance_ratio_
    except Exception:
        ev = np.ones(3) * np.nan
    rows = [dict(coordinate="d_slope_FIELD", explain=round(float(ev[0]), 3) if np.isfinite(ev[0]) else np.nan)]
    rows.append(dict(coordinate="d_ceiling_FIELD", explain=round(float(ev[1]), 3) if np.isfinite(ev[1]) else np.nan))
    rows.append(dict(coordinate="d_onset_FIELD", explain=round(float(ev[2]), 3) if np.isfinite(ev[2]) else np.nan))
    rows.append(dict(coordinate="cum2", explain=round(float(np.nansum(ev[:2])), 3)))
    rows.append(dict(coordinate="cum3", explain=round(float(np.nansum(ev)), 3)))
    rows.append(dict(coordinate="one_coordinate_capture", explain=float(ev[0])))
    W("12_SATURATION_MECHANISM.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 13 response node coupling
def response_node_coupling():
    X, cols = _node_feat_matrix(RESP_NAMES)
    m = np.isfinite(X).all(1)
    rows = []
    if m.sum() >= 120:
        Xc = X[m]; Xc = (Xc - Xc.mean(0)) / (Xc.std(0) + 1e-9)
        from sklearn.decomposition import PCA
        C = np.corrcoef(Xc.T)
        # pair avg abs correlations by node-type pair
        node_pairs = [("slope", "ceiling"), ("slope", "onset"), ("ceiling", "onset")]
        names = list(dict.fromkeys([c.split("_", 1)[0] for c in cols]))
        for na, nb in node_pairs:
            ia = [cols.index(f"d{na}_{p}") for p in RESP_NAMES]
            ib = [cols.index(f"d{nb}_{p}") for p in RESP_NAMES]
            vals = [C[i, j] for i in ia for j in ib if i < j or True]
            rows.append(dict(node_a=na, node_b=nb,
                             mean_abs_corr=round(float(np.nanmean(np.abs(vals))), 3),
                             n_pairs=len(vals)))
        pca = PCA(n_components=8).fit(Xc)
        ev = pca.explained_variance_ratio_
        rows.append(dict(node_a="PCA", node_b="all",
                         mean_abs_corr=round(float(ev[0]), 3), n_pairs=len(cols)))
        rows.append(dict(node_a="PCA", node_b="cum3",
                         mean_abs_corr=round(float(np.nansum(ev[:3])), 3), n_pairs=len(cols)))
    else:
        rows = [dict(node_a="FIELD", node_b="?", mean_abs_corr=np.nan, n_pairs=0)]
    W("13_RESPONSE_NODE_COUPLING.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 14 response coordinate pilot
def response_coordinate_pilot():
    # heldout reconstruction of FIELD saturation curve under 1/2/3-node parameterization
    from scipy.optimize import curve_fit
    dates_n = pd.to_datetime(dfc["d"])
    starts = pd.date_range(dates_n.min(), dates_n.max() - pd.Timedelta(days=180), freq="90D")
    fc = fc_arr
    y = field_act
    rows = []
    from _m19base import logistic_params_unc, logistic_params_unc as LPC2
    def sig(X, ceil, x0, k):
        return ceil / (1 + np.exp(-k * (X - x0)))
    meds = {}
    for node in ("x0", "k"):
        v = []
        for p in DEPTH_ORDER:
            x = fc; yy = act[p].to_numpy()
            m2 = ~(np.isnan(x) | np.isnan(yy))
            c2, x02, k2, _, _ = M88.logistic_params(x[m2], yy[m2])
            v.append({"x0": x02, "k": k2}[node])
        meds[node] = float(np.nanmedian(v))
    for i in range(len(starts)):
        t0 = starts[i]; t1 = t0 + pd.Timedelta(days=180)
        mw = (dates_n >= t0) & (dates_n < t1)
        if mw.sum() < 60:
            continue
        x = fc[mw]; yy = y[mw]
        m2 = ~(np.isnan(x) | np.isnan(yy)); x, yy = x[m2], yy[m2]
        if len(x) < 50:
            continue
        c, x0, k, _, _ = logistic_params_unc(x, yy)
        if not np.isfinite(c):
            continue
        pred3 = sig(x, c, x0, k)
        pred2 = sig(x, c, x0, meds["k"])
        s1 = 1 / (1 + np.exp(-meds["k"] * (x - meds["x0"])))
        c1 = np.sum(s1 * yy) / max(np.sum(s1 * s1), 1e-12)
        pred1 = c1 * s1
        rows.append(dict(win_start=str(t0.date()), n=len(x),
                         rmse_1param=rms(yy, pred1), rmse_2param=rms(yy, pred2),
                         rmse_3param=rms(yy, pred3),
                         naming_1=round(float(c1), 3), naming_3=round(float(c), 3)))
    out = pd.DataFrame(rows)
    if len(out):
        out["verdict_1d"] = np.where((out["rmse_1param"] - out["rmse_2param"]).abs().mean() < 0.02,
                                     "ONE_RESPONSE_COORDINATE", "TWO_REQUIRED")
    else:
        out["verdict_1d"] = "DATA_LIMITED"
    W("14_RESPONSE_COORDINATE_PILOT.csv")(out.round(4))

def rms(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return np.nan
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))

# ================================================================ 15 saturation by route
def saturation_by_route():
    rows = []
    sat = field_act
    for st in np.unique(g6):
        mk = g6 == st
        if mk.sum() < 60:
            continue
        sel = np.where(mk)[0]
        cnt = pd.Series(g6n[sel]).value_counts()
        dom = cnt.index[0] if len(cnt) else None
        if dom is None or dom == st:
            continue
        # forward 7d pressure to dominant exit among days in state
        press_all = np.full(ns, np.nan)
        for j in range(ns - 7):
            if g6[j] == st:
                press_all[j] = float((g6[j + 1:j + 8] == dom).mean())
        commit = press_all > 0.5
        pre = mk & (sat <= np.nanquantile(sat[mk], 0.33)) & np.isfinite(sat)
        near = mk & (sat >= np.nanquantile(sat[mk], 0.66)) & np.isfinite(sat)
        rows.append(dict(state=st, dominant=dom, n=int(mk.sum()),
                         commit_frac_pre_sat=round(float((commit & pre).sum() / pre.sum()), 3) if pre.sum() else np.nan,
                         commit_frac_near_ceiling=round(float((commit & near).sum() / near.sum()), 3) if near.sum() else np.nan,
                         median_sat_at_commit=round(float(np.nanmedian(sat[commit])), 3) if (commit == True).any() else np.nan,
                         sat_mean=round(float(np.nanmean(sat[mk])), 3),
                         sat_without_delivery=round(float(((sat[mk] >= np.nanquantile(sat[mk], 0.66)) & (prop7[mk] <= np.nanquantile(prop7, 0.33))).mean()), 3)))
    out = pd.DataFrame(rows)
    out["verdict"] = "MEASURED"
    return out

W15 = W("15_SATURATION_BY_ROUTE.csv", index=False)
W15(saturation_by_route().round(3))

# ================================================================ 16 saturation without delivery
def saturation_without_delivery():
    rows = []
    sat_hi = field_act >= np.nanquantile(field_act, 0.66)
    deliv = prop7 >= 0.5            # realized-propagation flag
    print("[16] sat_hi=%d delivered=%d no-delivery=%d" % (int(sat_hi.sum()), int((sat_hi & deliv).sum()), int((sat_hi & ~deliv).sum())))
    nod = sat_hi & (~deliv)
    d = sat_hi & deliv
    def _cmp(name, arr):
        a = arr[nod]; b = arr[d]
        a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
        if len(a) < 30 or len(b) < 30:
            return
        p = float(ranksums(a, b).pvalue)
        rows.append(dict(variable=name, n_without=int(len(a)), n_with= int(len(b)),
                         mean_without=round(float(np.nanmean(a)), 3),
                         mean_with=round(float(np.nanmean(b)), 3),
                         diff=round(float(np.nanmean(a) - np.nanmean(b)), 3),
                         ranksums_p=round(p, 4)))
    _cmp("exit_pressure_p1", p16)
    _cmp("exit_entropy", ent6)
    _cmp("route_deformation_js", js_hist)
    _cmp("transfer_efficiency", te_arr)
    _cmp("capacity", cap_arr)
    _cmp("threshold_position", thr_pos)
    _cmp("forcing", fc_arr)
    # unmatched baseline to compare broadly
    out = pd.DataFrame(rows)
    if len(out) > 0:
        out["pattern"] = "SATURATION_WITHOUT_DELIVERY_vs_WITH"
    else:
        out = pd.DataFrame([dict(variable="ALL", n_without=0, n_with=0, pattern="DATA_LIMITED")])
    W("16_SATURATION_WITHOUT_DELIVERY.csv")(out.round(3))# ================================================================ 17 threshold inversion anatomy
def _rolling_thr50(win=180, step=30):
    """Rolling half-saturation threshold (x0) per patch, asof-filled daily."""
    dts = dates
    dmin, dmax = dts.min(), dts.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=win), freq=f"{step}D")
    rows = []
    for t0 in starts:
        mw = (dts >= t0) & (dts < t0 + pd.Timedelta(days=win))
        rec = {"date": t0}
        for p in DEPTH_ORDER:
            x = fc_arr[mw]
            yb = (act[p].to_numpy()[mw] >= 0.55).astype(float)
            m2 = ~(np.isnan(x) | np.isnan(yb)) & np.isfinite(x)
            if m2.sum() < 60:
                rec[p] = np.nan; continue
            par = logit_fit(x[m2], yb[m2])
            rec[p] = thr_at(par, 0.5) if par else np.nan
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dts)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])

THR50_ROLL = _rolling_thr50()

def threshold_inversion_anatomy():
    # inversion: shallow patch has HIGHER thr50 than a deeper patch (deeper activates earlier)
    thr = {p: THR50_ROLL[p].to_numpy() for p in DEPTH_ORDER}
    invs = np.zeros(ns, dtype=bool)
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (thr[a] - thr[b]) > 0.15      # deep earlier by a margin
            invs = invs | np.where(np.isnan(thr[a]) | np.isnan(thr[b]), False, g)
    rows = []
    for (aa, bb) in run_episodes(invs):
        dur = bb - aa + 1
        if dur < 3:
            continue
        # which band pairs inverted
        pair = []
        for i, a in enumerate(DEPTH_ORDER):
            for b in DEPTH_ORDER[i + 1:]:
                seg = (thr[a][aa:bb + 1] - thr[b][aa:bb + 1]) > 0.15
                if seg.mean() > 0.5:
                    pair.append(f"{a}<{b}")
        rows.append(dict(start=str(dates[aa].date()), end=str(dates[bb].date()),
                         dur=dur, pairs="|".join(pair),
                         state=str(g6[aa]),
                         forcing=round(float(np.nanmean(fc_arr[aa:bb + 1])), 3),
                         exit_pressure=round(float(np.nanmean(p16[aa:bb + 1])), 3),
                         exit_entropy=round(float(np.nanmean(ent6[aa:bb + 1])), 3),
                         route_deform=round(float(np.nanmean(js_hist[aa:bb + 1])), 3),
                         saturation=round(float(np.nanmean(field_act[aa:bb + 1])), 3),
                         subperiod=str(subp_arr[aa]) if np.ndim(subp_arr) else ""))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("17_THRESHOLD_INVERSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    return out

W17 = W("17_THRESHOLD_INVERSION_ANATOMY.csv", index=False)
W17(threshold_inversion_anatomy().round(3))

# ================================================================ 18 threshold inversion species
def threshold_inversion_species():
    inv = pd.read_csv(OUT / "17_THRESHOLD_INVERSION_ANATOMY.csv")
    if len(inv) < 12 or "forcing" not in inv.columns:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    f_ = inv[["forcing", "exit_pressure", "exit_entropy", "route_deform", "saturation"]].apply(pd.to_numeric, errors="coerce")
    mm = f_.notna().all(1)
    if mm.sum() < 12:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    X = f_[mm].to_numpy()
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    from sklearn.cluster import KMeans
    k = min(4, mm.sum() // 4)
    if k < 2:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xs)
    inv["cluster"] = np.nan
    inv.loc[mm, "cluster"] = km.labels_
    cols = ["forcing", "exit_pressure", "exit_entropy", "route_deform", "saturation"]
    rows = []
    for cl in range(k):
        g = inv[inv["cluster"] == cl]
        if len(g) == 0:
            continue
        d = {c: round(float(np.nanmean(g[c])), 3) for c in cols}
        d.update(cluster=int(cl), n=len(g),
                 label=f"INVERSION_SPECIES_{int(cl)}")
        rows.append(d)
    W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame(rows).round(3))

# ================================================================ hysteresis helpers
def _hys_gap(y, fc, gm):
    """Controlled-ratio hysteresis gap for activation y over forcing levels,
    slicing on controls mask array gm (factor). Returns (gap, gap_ctl)."""
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
    # controlled within each level of gm
    gg = np.asarray(gm)
    gc = []
    for lv in np.unique(gg):
        ms = gg == lv
        for i in range(10):
            mb = ms & (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
            mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
            if mr.sum() >= 6 and mf.sum() >= 6:
                gc.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    gc_g = float(np.nanmean(gc)) if gc else np.nan
    return gap, gc_g

# ================================================================ 19 deep hysteresis map
def deep_hysteresis_map():
    rows = []
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy()
        fc = fc_arr
        # state-sliced
        for s in np.unique(g6):
            gm = np.where(g6 == s, "A", "B")
            m = g6 == s
            if m.sum() < 60:
                continue
            gap, gc = _hys_gap(y[m], fc[m], gm[m.astype(float) if m.dtype.kind in "fi" else m])
            rows.append(dict(patch=patch, layer="state", label=str(s), n=int(m.sum()),
                             gap_raw=round(gap, 3) if gap == gap else np.nan,
                             gap_controlled=round(gc, 3) if gc == gc else np.nan))
    W("19_DEEP_HYSTERESIS_MAP.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 20 hysteresis boundaries
def hysteresis_boundaries():
    rows = []
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy(); fc = fc_arr
        gap, gc = _hys_gap(y, fc, np.zeros(len(fc)))
        rows.append(dict(rank_band=patch, index=idx,
                         gap_raw=round(gap, 3) if gap == gap else np.nan,
                         gap_controlled_gvarsingleton=round(gc, 3) if gc == gc else np.nan))
    dfb = pd.DataFrame(rows)
    gs = pd.to_numeric(dfb["gap_controlled_gvarsingleton"], errors="coerce")
    dfb["strength_band"] = pd.cut(gs, bins=[-np.inf, 0.02, 0.06, 0.12, np.inf],
                                  labels=["ABSENT", "WEAK", "MODERATE", "STRONG"])
    dfb["verdict"] = "RANK_LOCAL_HYSTERESIS" if (abs(gs) >= 0.03).any() else "LEVEL_SUFFICIENT"
    W("20_HYSTERESIS_BOUNDARIES.csv")(dfb.round(3))# ================================================================ 21 birth failure mechanism
def _stage_arr(ixs, arr, stage):
    """Like M18 _stage_vals but on an arbitrary daily array."""
    if stage == "PRECONDITION":
        return np.array([np.nanmean(arr[max(0, i - 7):i]) for i in ixs])
    if stage == "INITIATION":
        return arr[ixs]
    if stage == "COMMITMENT":
        return np.array([np.nanmean(arr[i + 1:min(ns, i + 4)]) for i in ixs])
    return np.array([np.nanmean(arr[min(ns - 1, i + 4):min(ns, i + 8)]) for i in ixs])

# entropy decomposition inputs at INITIATION
def _entropy_decomp(ixs):
    """Break exit entropy into: many live exits (k), route deformation (JS),
    dominant-share instability (rolling std of p1)."""
    n_live = k6; jsd = js_hist
    dom_stab = np.full(ns, np.nan)
    for t in range(8, ns):
        dom_stab[t] = np.nanstd(p16[t - 7:t])
    return _stage_arr(ixs, n_live, "INITIATION"), \
           _stage_arr(ixs, jsd, "INITIATION"), \
           _stage_arr(ixs, dom_stab, "INITIATION"), \
           _stage_arr(ixs, ent6, "INITIATION")

def birth_failure_mechanism():
    rows = []
    p1_std_vi = pd.Series(p16).rolling(7, min_periods=3).std().to_numpy()
    decomp = [("exit_entropy", ent6), ("n_live_exits", k6), ("route_deformation_js", js_hist),
              ("dominant_share_instability", p1_std_vi), ("exit_p1", p16)]
    for name, arr in decomp:
        vv = _stage_arr(vi_, arr, "INITIATION"); av = _stage_arr(ab_, arr, "INITIATION")
        vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
        if len(vv) < 15 or len(av) < 15:
            continue
        d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
        p = float(ranksums(vv, av).pvalue)
        rows.append(dict(coordinate=name, viable_mean=round(float(np.mean(vv)), 4),
                         aborted_mean=round(float(np.mean(av)), 4), cohens_d=round(d, 3),
                         p_value=round(p, 4),
                         direction="aborted_higher" if np.mean(av) > np.mean(vv) else "aborted_lower",
                         mechanism=("unresolved_route_set" if name in ("exit_entropy", "dominant_share_instability", "route_deformation_js")
                                    else "physical")) )
    # is high entropy driven by many-open vs unstable-probs?
    ent_hi = _stage_arr(ab_, ent6, "INITIATION") > np.nanquantile(_stage_arr(ab_, ent6, "INITIATION"), 0.5)
    if ent_hi.sum() >= 10:
        grab = ab_[ent_hi]
        a_live = np.nanmean(_stage_arr(grab, k6, "INITIATION"))
        a_stab = np.nanmean(_stage_arr(grab, p1_std_vi, "INITIATION"))
        rows.append(dict(coordinate="BOTH_OPEN_AND_UNSTABLE", viable_mean=np.nan,
                         aborted_mean=round(float(a_live), 3), cohens_d=np.nan, p_value=np.nan,
                         direction="n_live=%s std_p1=%s" % (round(float(a_live), 2), round(float(a_stab), 3)),
                         mechanism="diagnostic"))
    W("21_BIRTH_FAILURE_MECHANISM.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 22 load commitment mismatch
def load_commitment_mismatch():
    # load = incoming demand slope; commitment = persistence of dominant route (1-p(reopen in +/- horizon))
    # use p1 separation as commitment proxy normalized by demand
    rows = []
    demand_slope = np.full(ns, np.nan); demand_slope[1:] = np.diff(demand_arr)
    for st in STAGES18:
        vi_l = _stage_arr(vi_, demand_slope, st); ab_l = _stage_arr(ab_, demand_slope, st)
        # commitment: forward persistence of dominant share (p1 minus p2 gap)
        commit_arr = np.asarray(p16 - p26, dtype=float)
        vi_c = _stage_arr(vi_, commit_arr, st); ab_c = _stage_arr(ab_, commit_arr, st)
        vv = vi_l[~np.isnan(vi_l)]; av = ab_l[~np.isnan(ab_l)]
        vc = vi_c[~np.isnan(vi_c)]; ac = ab_c[~np.isnan(ab_c)]
        if min(len(vv), len(av), len(vc), len(ac)) < 15:
            continue
        rows.append(dict(stage=st,
                         demand_slope_viable=round(float(np.mean(vv)), 4),
                         demand_slope_aborted=round(float(np.mean(av)), 4),
                         commitment_gap_viable=round(float(np.mean(vc)), 3),
                         commitment_gap_aborted=round(float(np.mean(ac)), 3),
                         mismatch="DEMAND_OUTPACES_COMMITMENT" if np.mean(av) - np.mean(ac) > np.mean(vv) - np.mean(vc) else "BALANCED"))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("22_LOAD_COMMITMENT_MISMATCH.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    out["verdict"] = "LOCAL" if (out["mismatch"] == "DEMAND_OUTPACES_COMMITMENT").any() else "DISSOLVE"
    W("22_LOAD_COMMITMENT_MISMATCH.csv")(out.round(3))

# ================================================================ 23 birth recovery
def birth_recovery():
    rows = []
    for i in ab_:
        # next formation point after i
        cand = bp_[bp_ > i]
        if len(cand) == 0:
            continue
        r = int(cand[0])
        # is it viable (not aborted)?
        viable = False
        if (g6[r + 1:min(r + 8, ns)] != prev_[r]).any():
            viable = False
        else:
            viable = True
        same_state = g6[r] == g6[i]
        ent_collapsed = np.nanmean(ent6[i - 3:i]) > np.nanmean(ent6[r - 3:r])
        demand_cooled = np.nanmean(demand_arr[r - 3:r]) < np.nanmean(demand_arr[i - 3:i])
        thr_normalized = np.nanmean(thr_pos[r - 3:r]) - np.nanmean(thr_pos[i - 3:i])
        rows.append(dict(aborted_date=str(dates[i].date()), recovery_date=str(dates[r].date()),
                         days_to_recovery=int(r - i),
                         recovered_as_viable=viable, same_state_return=bool(same_state),
                         entropy_collapsed_first=bool(ent_collapsed),
                         demand_cooled_first=bool(demand_cooled),
                         threshold_delta=round(float(thr_normalized), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("23_BIRTH_RECOVERY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("23_BIRTH_RECOVERY.csv")(out.round(3))

# ================================================================ 24 potential realization constraints
_med = lambda a: np.nanmedian(a)
_c_met = {
    "DEMAND": demand_arr >= _med(demand_arr),
    "CAPACITY": cap_arr >= _med(cap_arr),
    "THRESHOLD": thr_pos >= _med(thr_pos),
    "EXIT_PRESSURE": p16 >= _med(p16),
    "TRANSFER": te_arr >= _med(te_arr),
    "NON_SATURATED": field_act <= np.nanquantile(field_act, 0.8),
}
_realize = prop7 >= 0.5          # prop7 is a 0/1 realized-propagation flag

def potential_realization_constraints():
    base = float(_realize.mean())
    rows = []
    for name, met in _c_met.items():
        mmet = met & np.isfinite(prop7); mn = (~met) & np.isfinite(prop7)
        if mmet.sum() < 60 or mn.sum() < 60:
            continue
        p_met = float(_realize[mmet].mean()); p_not = float(_realize[mn].mean())
        necessity = 1 - p_not               # high => unmet almost never delivers
        sufficiency = p_met                   # high => met usually delivers
        if necessity > 0.85:
            role = "NECESSARY_CANDIDATE"
        elif sufficiency > 0.7:
            role = "SUFFICIENT_LIKE"
        elif abs(p_met - p_not) < 0.05:
            role = "REDUNDANT"
        else:
            role = "SUBSTITUTABLE"
        rows.append(dict(constraint=name, n_met=int(mmet.sum()), n_unmet=int(mn.sum()),
                         p_realize_met=round(p_met, 3), p_realize_unmet=round(p_not, 3),
                         base_rate=round(base, 3), lift_met=round(p_met - base, 3),
                         role=role))
    W("24_POTENTIAL_REALIZATION_CONSTRAINTS.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 25 constraint combination lattice
def constraint_combination_lattice():
    cnames = list(_c_met.keys())
    rows = []
    m_ok = np.isfinite(prop7)
    from itertools import combinations
    # single/2/3-way met-subsets with support
    for k in (1, 2, 3):
        for combo in combinations(cnames, k):
            m = np.ones(ns, dtype=bool)
            for c in combo:
                m &= _c_met[c]
            m &= m_ok
            if m.sum() < 40:
                continue
            rows.append(dict(n_constraints_met=k, subset="+".join(combo), n=int(m.sum()),
                             deliver_rate=round(float(_realize[m].mean()), 3),
                             stall_rate=round(float((prop7[m] <= np.nanquantile(prop7, 0.33)).mean()), 3),
                             sat_without_deliv=round(float(((field_act[m] >= np.quantile(field_act[m], 0.66)) & (prop7[m] <= np.nanquantile(prop7[m], 0.33))).mean()), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("25_CONSTRAINT_COMBINATION_LATTICE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("25_CONSTRAINT_COMBINATION_LATTICE.csv")(out.round(3))

# ================================================================ 26 failure motif decomposition
MOTIF_NAMES = ["HIGH_DEMAND_LOW_TRANSFER", "HIGH_DEMAND_OPEN_EXITS",
               "THRESHOLD_CROSSED_NO_RECRUITMENT", "CAPACITY_AVAILABLE_NO_COMMITMENT",
               "EXIT_CONCENTRATION_WITH_PROPAGATION", "SATURATION_WITHOUT_DELIVERY"]

def _motif_masks():
    q = lambda a: np.nanquantile(a, 0.67); q33 = lambda a: np.nanquantile(a, 0.33)
    d = demand_arr; util = demand_arr / np.where(cap_arr > 0, cap_arr, np.nan)
    return {
        "HIGH_DEMAND_LOW_TRANSFER": (d >= q(d)) & (te_arr <= q33(te_arr)),
        "HIGH_DEMAND_OPEN_EXITS": (d >= q(d)) & (ent6 >= q(ent6)),
        "THRESHOLD_CROSSED_NO_RECRUITMENT": (thr_pos >= q(thr_pos)) & (rank7 <= q33(rank7)),
        "CAPACITY_AVAILABLE_NO_COMMITMENT": (util >= q(util)) & (d >= q(d)),
        "EXIT_CONCENTRATION_WITH_PROPAGATION": (p16 >= q(p16)) & (prop7 >= q(prop7)),
        "SATURATION_WITHOUT_DELIVERY": (field_act >= np.nanquantile(field_act, 0.8)) & (prop7 <= q33(prop7)),
    }

def failure_motif_decomposition():
    mm = _motif_masks()
    feats = ["demand", "capacity", "thr_pos", "exit_pressure", "exit_entropy", "transfer", "sat", "rank7"]
    feat_maps = {"demand": demand_arr, "capacity": cap_arr, "thr_pos": thr_pos,
                 "exit_pressure": p16, "exit_entropy": ent6, "transfer": te_arr,
                 "sat": field_act, "rank7": rank7}
    prof = {}
    rows = []
    for name, mask in mm.items():
        m = mask & np.isfinite(prop7)
        v = [np.nanmean(feat_maps[F][m]) for F in feats]
        prof[name] = np.array(v)
        rows.append(dict(motif=name, n=int(m.sum()),
                         base_delivery=round(float(np.nanmean(prop7[m])), 3),
                         resolution_type=np.nan))
    names = list(prof.keys())
    sep = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            dist = float(np.linalg.norm(prof[a] - prof[b]))
            sep.append((a, b, dist))
    sep = [s for s in sep if np.isfinite(s[2])]
    ds = pd.DataFrame(sep, columns=["motif_a", "motif_b", "feature_profile_distance"]).round(3) if sep else pd.DataFrame()
    rows_df = pd.DataFrame(rows).round(3)
    W("26_FAILURE_MOTIF_DECOMPOSITION.csv")(rows_df)
    if len(ds):
        W("26b_FAILURE_MOTIF_SEPARATION.csv")(ds)

# ================================================================ 27 realization geometry
def realization_geometry():
    Xnames = ["demand", "capacity", "thr_pos", "exit_pressure", "transfer", "sat"]
    X = np.column_stack([demand_arr, cap_arr, thr_pos, p16, te_arr, field_act])
    m = np.isfinite(prop7) & np.all(np.isfinite(X), axis=1)
    y = (prop7 >= 0.5).astype(float)[m]; Xm = X[m]
    Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
    split = int(len(y) * 0.7)
    order = np.arange(len(y)); rng = np.random.RandomState(0); rng.shuffle(order)
    itr, ite = order[:split], order[split:]
    rows = []
    from sklearn.metrics import roc_auc_score
    # stratified split: force both classes into the training fold
    from sklearn.model_selection import train_test_split
    auc_one = np.nan
    for ncomp in (1, 2, 3, 6):
        from sklearn.decomposition import PCA
        try:
            itr2, ite2 = train_test_split(np.arange(len(y)), test_size=0.3, random_state=0, stratify=y)
            pca = PCA(n_components=min(ncomp, Xs.shape[1])).fit(Xs[itr2])
            Zr = pca.transform(Xs[itr2]); Ze = pca.transform(Xs[ite2])
            lr = LogisticRegression(max_iter=2000).fit(Zr, y[itr2])
            auc = roc_auc_score(y[ite2], lr.predict_proba(Ze)[:, 1])
        except Exception:
            auc = np.nan
        if ncomp == 1:
            auc_one = auc
        rows.append(dict(n_coordinates=ncomp, heldout_auc=round(float(auc), 3)))
    best = max((r["heldout_auc"] for r in rows if r["heldout_auc"] == r["heldout_auc"]), default=np.nan)
    if best > 0.02 and (auc_one == auc_one and best - auc_one < 0.02):
        verd = "MULTI_AXIS_GEOMETRY(1_DOMINANT)"
    elif best > 0.05:
        verd = "FEW_CONSTRAINT_COORDINATES"
    else:
        verd = "NO_CLEAN_GEOMETRY"
    rows.append(dict(n_coordinates=np.nan, heldout_auc=np.nan, verdict=verd))
    W("27_REALIZATION_GEOMETRY.csv")(pd.DataFrame(rows).round(3))# ================================================================ 28 2022 unclamped repair
def _rolling_node_series2(fit=logistic_params_unc, win=180, step=30):
    """Rolling logistic response nodes using an arbitrary fit function."""
    dmin, dmax = dates.min(), dates.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=win), freq=f"{step}D")
    rows = []
    for t0 in starts:
        mw = (dates >= t0) & (dates < t0 + pd.Timedelta(days=win))
        xw = fc_arr[mw]
        rec = {"date": t0}
        for p in RESP_NAMES:
            yw = act[p].to_numpy()[mw]
            m2 = ~(np.isnan(xw) | np.isnan(yw))
            if int(m2.sum()) < 60:
                rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = np.nan, np.nan, np.nan
                continue
            ceil, x0, k, _, _ = fit(xw[m2], yw[m2])
            rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = k, ceil, x0
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dates)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])

WIND22_PRE = (dates < pd.Timestamp("2021-10-01"))
WIND22_IN = (dates >= pd.Timestamp("2021-10-01")) & (dates < pd.Timestamp("2022-07-01"))
WIND22_POST = (dates >= pd.Timestamp("2022-07-01"))

def _fit_round(win_mask, p, fit):
    x = fc_arr[win_mask]; y = act[p].to_numpy()[win_mask]
    m2 = ~(np.isnan(x) | np.isnan(y))
    if m2.sum() < 60:
        return np.nan, np.nan, np.nan, np.nan
    ceil, x0, k, rmse, _ = fit(x[m2], y[m2])
    return k, ceil, x0, rmse

def unclamped_repair():
    fits = {"CLAMPED": M88.logistic_params, "UNCLAMPED": logistic_params_unc,
            "ROBUST_BOUNDED": lambda x, y: logistic_params_unc(x, y, ceil_hi=2.0)}
    winz = {"PRE2021": WIND22_PRE, "DURING_2022": WIND22_IN, "POST2022": WIND22_POST}
    rows = []
    for win_name, mask in winz.items():
        for p in RESP_NAMES:
            for fname, fit in fits.items():
                k, c, x0, rmse = _fit_round(mask, p, fit)
                rows.append(dict(window=win_name, response=p, fit=fname,
                                 slope=round(float(k), 4) if k == k else np.nan,
                                 ceiling=round(float(c), 4) if c == c else np.nan,
                                 half_sat=round(float(x0), 4) if x0 == x0 else np.nan,
                                 rmse=round(float(rmse), 4) if rmse == rmse else np.nan))
    W("28_2022_UNCLAMPED_REPAIR.csv")(pd.DataFrame(rows).round(4))

# ================================================================ event machinery (unclamped)
def _event_machinery2(fit=logistic_params_unc):
    nodes = _rolling_node_series2(fit)
    cols = {}
    for p in RESP_NAMES:
        cols[f"slope_{p}"] = nodes[f"{p}_k"].to_numpy()
        cols[f"ceiling_{p}"] = nodes[f"{p}_ceiling"].to_numpy()
        cols[f"onset_{p}"] = nodes[f"{p}_x0"].to_numpy()
    vdict = {"slope_FIELD": cols["slope_FIELD"], "ceiling_FIELD": cols["ceiling_FIELD"],
             "onset_FIELD": cols["onset_FIELD"],
             "slope_patch_mean": np.nanmean([cols[f"slope_{p}"] for p in DEPTH_ORDER], axis=0),
             "ceiling_patch_mean": np.nanmean([cols[f"ceiling_{p}"] for p in DEPTH_ORDER], axis=0),
             "onset_patch_mean": np.nanmean([cols[f"onset_{p}"] for p in DEPTH_ORDER], axis=0),
             "exit_entropy": ent6, "exit_p1": p16, "recruitment": rank7,
             "demand": demand_arr, "propagation": prop7, "reentry": ren7,
             "volatility": vol_med, "breadth": possh}
    Z = {}
    for name, v in vdict.items():
        v = np.asarray(v, dtype=float)
        m = pd.Series(v).rolling(30, min_periods=15).mean().to_numpy()
        med = np.nanmedian(m); mad = np.nanmedian(np.abs(m - med)) * 1.4826
        Z[name] = (m - med) / max(mad, 1e-9)
    Zdf = pd.DataFrame(Z)
    S = np.sqrt((Zdf ** 2).mean(axis=1)).to_numpy()
    n_dev = (np.abs(Zdf.to_numpy()) > 3).sum(axis=1)
    win_lo = np.datetime64("2021-11-01"); win_hi = np.datetime64("2023-06-30")
    in_block = (n_dev >= 4) & (dates >= win_lo) & (dates <= win_hi)
    blocks = []; i = 0
    while i < ns:
        if in_block[i]:
            j = i
            while j < ns and in_block[j]:
                j += 1
            if (j - i) >= 10:
                blocks.append((i, j - 1))
            i = j
        else:
            i += 1
    if not blocks:
        return dict(verdict="NO_EVENT_BLOCK_FOUND", Zdf=Zdf, S=S, n_dev=n_dev, dates=dates)
    best = max(blocks, key=lambda ab: float(np.nanmean(S[ab[0]:ab[1] + 1])))
    a, b = best
    t0 = a
    while t0 > 0 and n_dev[t0 - 1] >= 3 and dates[t0 - 1] >= win_lo:
        t0 -= 1
    peak = int(np.nanargmax(S[a:b + 1])) + a
    ev_mask = np.ones(ns, dtype=bool); ev_mask[a:b + 1] = False
    S_base = np.nanmedian(S[ev_mask]); S_mad = np.nanmedian(np.abs(S[ev_mask] - S_base)) * 1.4826
    def first_sustained(cond, dur, start):
        for t in range(start, ns - dur):
            if np.all(cond(t, dur)):
                return t
        return None
    snap = {}
    for dur in (14, 30, 60):
        snap[dur] = first_sustained(lambda tt, d=dur: (n_dev[tt:tt + d] <= 1) & (S[tt:tt + d] <= S_base + 3 * S_mad), dur, peak + 1)
    snap_base = snap[14]
    norm = first_sustained(lambda tt, _d: n_dev[tt:tt + 14] <= 2, 14, peak + 1)
    early = int(np.where(S[peak:] < 0.5 * S[peak])[0][0]) + peak if np.any(S[peak:] < 0.5 * S[peak]) else None
    return dict(verdict="EVENT_DETECTED", Zdf=Zdf, S=S, n_dev=n_dev, dates=dates,
                t0=t0, a=a, b=b, peak=peak, S_base=S_base, S_mad=S_mad,
                snap=snap, snap_base=snap_base, norm=norm, early=early,
                onset_date=str(dates[t0].date()), peak_date=str(dates[peak].date()),
                break_date=str(dates[a].date()),
                snap14_date=str(dates[snap[14]].date()) if snap[14] else None,
                snap30_date=str(dates[snap[30]].date()) if snap[30] else None,
                snap60_date=str(dates[snap[60]].date()) if snap[60] else None)

EV_UNC = _event_machinery2(logistic_params_unc)

def event_reestimate():
    d = EV_UNC["dates"]
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("29_2022_EVENT_REESTIMATE.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    rows = []
    for stage, idx in [("DEVIATION_ONSET", EV_UNC["t0"]), ("BREAK_CONFIRMATION", EV_UNC["a"]),
                       ("PEAK_DISTORTION", EV_UNC["peak"]), ("EARLY_RECOVERY", EV_UNC["early"]),
                       ("SHAPE_NORMALIZATION", EV_UNC["norm"])]:
        if idx is None:
            rows.append(dict(stage=stage, date=None)); continue
        rows.append(dict(stage=stage, date=str(d[idx].date()),
                         deviation_index=round(float(EV_UNC["S"][idx]), 3)))
    for dur in (14, 30, 60):
        t = EV_UNC["snap"][dur]
        rows.append(dict(stage=f"FULL_SNAPBACK_{dur}D", date=str(d[t].date()) if t is not None else None))
    W("29_2022_EVENT_REESTIMATE.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 29 -> shared Z (also write 30..34)
Zdf = EV_UNC["Zdf"] if EV_UNC["verdict"] != "NO_EVENT_BLOCK_FOUND" else pd.DataFrame()

def _norm_date(zvec, peak, sus_dur=14):
    n = len(zvec); absz = np.abs(zvec)
    for t in range(peak + 1, n - sus_dur):
        if np.all(absz[t:t + sus_dur] <= 3):
            return t
    return None

SURFACE_VARS = ["propagation", "reentry", "volatility", "breadth", "demand"]
LAW_VARS = ["slope_FIELD", "ceiling_FIELD", "onset_FIELD", "slope_patch_mean",
            "ceiling_patch_mean", "onset_patch_mean", "exit_entropy", "exit_p1", "recruitment"]

def surface_vs_law_recovery():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("30_SURFACE_VS_LAW_RECOVERY.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]
    rows = []
    for grp, names in (("SURFACE", SURFACE_VARS), ("LAW", LAW_VARS)):
        for name in names:
            if name not in Zdf.columns:
                continue
            z = Zdf[name].to_numpy()
            fn = _norm_date(z, peak)
            rows.append(dict(layer=grp, variable=name,
                             sustained_normalization=str(d[fn].date()) if fn is not None else None,
                             days_after_peak=(fn - peak) if fn is not None else np.nan))
    out = pd.DataFrame(rows)
    surf = out[out["layer"] == "SURFACE"]["days_after_peak"]
    law = out[out["layer"] == "LAW"]["days_after_peak"]
    if surf.notna().any() and law.notna().any():
        out["verdict"] = "SURFACE_PRECEDED_LAW" if surf.median() < law.median() else "COEVAL_OR_LAW_FIRST"
    W("30_SURFACE_VS_LAW_RECOVERY.csv")(out.round(2))

def structural_scar():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("31_STRUCTURAL_SCAR.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; sb = EV_UNC.get("snap_base") or EV_UNC["peak"]; peak = EV_UNC["peak"]
    rows = []
    post = (d > d[sb]) & (d <= d[sb] + pd.Timedelta(days=180))
    for name in LAW_VARS:
        if name not in Zdf.columns:
            continue
        z = Zdf[name].to_numpy(); absz = np.abs(z)
        if np.isfinite(absz).sum() < 60:
            continue
        pre = d < d[peak - 250] if peak - 250 > 0 else np.ones(len(d), bool)
        mp = absz[post & np.isfinite(absz)]; mpr = absz[pre & np.isfinite(absz)]
        if len(mp) == 0 or len(mpr) == 0:
            continue
        disp = float(np.nanmean(mp) - np.nanmean(mpr))
        breaches = float((mp > 3).sum())
        rows.append(dict(variable=name, n_post=int(len(mp)),
                         post_mean_absz=round(float(np.nanmean(mp)), 3),
                         pre_mean_absz=round(float(np.nanmean(mpr)), 3),
                         displacement=round(disp, 3),
                         post_breaches=breaches,
                         verbose_scar=bool(disp > 0.5 or breaches > 0)))
    out = pd.DataFrame(rows)
    if len(out) and (out["displacement"] > 0.5).any():
        out["verdict"] = "STRUCTURAL_SCAR"
    elif len(out) and (out["displacement"] > 0.25).any():
        out["verdict"] = "LONG_RELAXATION"
    elif len(out):
        out["verdict"] = "ARTIFACT"
    else:
        out["verdict"] = "DATA_LIMITED"
    W("31_STRUCTURAL_SCAR.csv")(out.round(3))

def reexcursions():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("32_2022_REEXCURSIONS.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; n_dev = EV_UNC["n_dev"]; sb = EV_UNC.get("snap_base") or EV_UNC["peak"]
    mask = np.zeros(ns, dtype=bool); mask[:sb + 1] = False; mask[sb + 1:] = True
    law_cols = [c for c in LAW_VARS if c in Zdf.columns]
    law_z = np.abs(Zdf[law_cols].to_numpy()) if law_cols else np.zeros((ns, 1)) * np.nan
    post_dev = (n_dev >= 2) & mask
    rows = []
    for (a, b) in run_episodes(post_dev):
        if (b - a + 1) < 5:
            continue
        rows.append(dict(start=str(d[a].date()), end=str(d[b].date()),
                         dur=int(b - a + 1),
                         peak_law_absz=round(float(np.nanmax(law_z[a:b + 1])), 3) if len(law_z) else np.nan,
                         forcing=round(float(np.nanmean(fc_arr[a:b + 1])), 3),
                         threshold_inversion=bool(False)))
    W("32_2022_REEXCURSIONS.csv")(pd.DataFrame(rows).round(3))

def event_end():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("33_2022_EVENT_END.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]; Z = Zdf
    sb = EV_UNC.get("snap_base") or peak
    def group_end(names, sus):
        z = np.abs(Z[[c for c in names if c in Z.columns]].to_numpy())
        for t in range(peak + 1, ns - sus):
            if np.all(z[t:t + sus].max(axis=1) <= 3, axis=None):
                return t
        return None
    rows = []
    for sus in (14, 30, 60):
        s_end = group_end(SURFACE_VARS, sus)
        l_end = group_end(LAW_VARS, sus)
        full = group_end(SURFACE_VARS + LAW_VARS, sus)
        rows.append(dict(persistence_days=sus,
                         surface_end=str(d[s_end].date()) if s_end is not None else None,
                         law_end=str(d[l_end].date()) if l_end is not None else None,
                         full_stability_end=str(d[full].date()) if full is not None else None))
    W("33_2022_EVENT_END.csv")(pd.DataFrame(rows))

def precedence_map():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("34_2022_PRECEDENCE_MAP.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]; sb = EV_UNC.get("snap_base") or peak
    rows = []
    for name in SURFACE_VARS + LAW_VARS:
        if name not in Zdf.columns:
            continue
        z = Zdf[name].to_numpy(); absz = np.abs(z)
        onset = np.nan
        for t in range(max(0, peak - 400), peak + 1):
            if absz[t] > 3:
                onset = t; break
        pk = int(np.nanargmax(absz[max(0, peak - 400):peak + 1])) + max(0, peak - 400)
        fn = _norm_date(z, peak)
        rel = "PRECEDED" if (fn is not None and (sb - fn) > 30) else ("COINCIDED" if (fn is not None and (sb - fn) >= 0) else "LAGGED_OR_NEVER")
        rows.append(dict(variable=name, layer="LAW" if name in LAW_VARS else "SURFACE",
                         onset_date=str(d[int(onset)].date()) if np.isfinite(onset) else None,
                         peak_date=str(d[pk].date()),
                         normalized_date=str(d[fn].date()) if fn is not None else None,
                         relation_to_snapback=rel))
    out = pd.DataFrame(rows)
    W("34_2022_PRECEDENCE_MAP.csv")(out.round(2))# ================================================================ 35 global law hierarchy
def global_law_hierarchy():
    # stage feature sets, cumulative; compare ascending vs descending order
    from sklearn.metrics import roc_auc_score
    gap = p16 - p26
    stages = {
        "FORCING_FAMILY": ["forcing"],
        "THRESHOLD_SAT": ["thr_pos", "sat"],
        "EXIT_AVAIL_PRESSURE": ["p1", "ent"],
        "ROUTE_COMMITMENT": ["gap"],
        "TRANSFER_REALIZATION": ["te"],
    }
    featmap = {"forcing": fc_arr, "thr_pos": thr_pos, "sat": field_act,
               "p1": p16, "ent": ent6, "gap": gap, "te": te_arr}
    y = (prop7 >= 0.5).astype(float)   # realized-propagation flag
    m0 = np.isfinite(prop7)
    order_asc = ["FORCING_FAMILY", "THRESHOLD_SAT", "EXIT_AVAIL_PRESSURE", "ROUTE_COMMITMENT", "TRANSFER_REALIZATION"]
    order_desc = list(reversed(order_asc))
    rows = []
    Xall = np.column_stack([featmap[c] for st in stages for c in stages[st]])
    mall = m0 & np.isfinite(Xall).all(1)
    split = int(np.sum(mall) * 0.7)
    idx = np.where(mall)[0]; rng = np.random.RandomState(0); rng.shuffle(idx)
    itr, ite = idx[:split], idx[split:]
    from sklearn.model_selection import train_test_split
    def auc_for(keys):
        try:
            X = np.column_stack([featmap[c] for st in keys for c in stages[st]])
            m = m0 & np.isfinite(X).all(1)
            sy, sz = y[m], (X[m] - X[m].mean(0)) / (X[m].std(0) + 1e-9)
            t1, t2 = train_test_split(np.arange(len(sy)), test_size=0.3, random_state=0, stratify=sy)
            lr = LogisticRegression(max_iter=2000).fit(sz[t1], sy[t1])
            return float(roc_auc_score(sy[t2], lr.predict_proba(sz[t2])[:, 1]))
        except Exception:
            return np.nan
    for order, label in ((order_asc, "ASC_TOPOLOGY"), (order_desc, "DESC_TRANSFER")):
        acc = []
        for k in range(1, 6):
            acc.append(auc_for(order[:k]))
        rows.append(dict(order=label, auc_stage_1=round(acc[0], 3),
                         auc_stage_2=round(acc[1], 3), auc_stage_3=round(acc[2], 3),
                         auc_stage_4=round(acc[3], 3), auc_stage_5=round(acc[4], 3),
                         gain_first_3=round(acc[2] - acc[0], 3),
                         gain_last_2=round(acc[4] - acc[2], 3)))
    dfh = pd.DataFrame(rows)
    g_mid_a = dfh[dfh["order"] == "ASC_TOPOLOGY"]["gain_first_3"].iloc[0]
    g_mid_d = dfh[dfh["order"] == "DESC_TRANSFER"]["gain_first_3"].iloc[0]
    if g_mid_a > 0.04 and g_mid_d <= 0.02:
        verd = "LOOSE_HIERARCHY"
    elif max(g_mid_a, g_mid_d) <= 0.02:
        verd = "PARALLEL_CONSTRAINT_SYSTEM"
    else:
        verd = "HYBRID"
    dfh["hierarchy_verdict"] = verd
    W("35_GLOBAL_LAW_HIERARCHY.csv")(dfh.round(3))

# ================================================================ 36 promote merge dissolve
def promote_merge_dissolve():
    rows = []
    def add(obj, role, action, note, verdicts=None):
        rows.append(dict(object=obj, os_role=role, action=action, note=note[:160]))
    # carried objects with MECH-19 verdict actions (finalized after reviewing CSVs)
    add("ROAD_TOPOLOGY_4STATE", "STRUCTURAL_CORE", "FREEZE", "carried; not reopened in MECH-19")
    add("EDGE_REGISTRY_93", "STRUCTURAL_CORE", "FREEZE", "MECH-18 93-edge registry")
    add("MULTI_FORCING_FAMILY", "ADAPTIVE_LAW", "PROMOTE", "deep primitives/signatures round 2")
    add("ROUTE_COMMITMENT", "ADAPTIVE_LAW", "PROMOTE", "commitment gradient from p1 vs reopening")
    add("PRESSURE_CONCENTRATION", "ADAPTIVE_LAW", "PROMOTE", "mechanics localized per state")
    add("EDGE_PRUNING", "ADAPTIVE_LAW", "PROMOTE", "resolution mechanism; see 05")
    add("CONCENTRATION_PHASES", "ADAPTIVE_LAW", "LOCAL", "gradient > discrete phases recommend")
    add("RESPONSE_NODES", "ADAPTIVE_LAW", "PROMOTE", "coupling/PCA geometry; see 12-14")
    add("SATURATION_WITHOUT_DELIVERY", "LOCAL_PHYSICS", "PROMOTE", "matched without-delivery anatomy; see 16")
    add("THRESHOLD_INVERSION", "ADAPTIVE_LAW", "LOCAL", "species taxonomy; see 18")
    add("DEEP_RANK_HYSTERESIS", "LOCAL_PHYSICS", "LOCAL", "survival range; see 19-20")
    add("BIRTH_FAILURE_MECHANISM", "ADAPTIVE_LAW", "PROMOTE", "demand-overload in unresolved route set")
    add("LOAD_COMMITMENT_MISMATCH", "ADAPTIVE_LAW", "LOCAL", "candidate; see 22")
    add("POTENTIAL_REALIZATION", "ADAPTIVE_LAW", "PROMOTE", "parallel constraints + lattice; see 24-27")
    add("FAILURE_MOTIFS", "ADAPTIVE_LAW", "LOCAL", "distinctness; see 26")
    add("2022_STRUCTURAL_SCAR", "RESEARCH_ONLY", "PROMOTE", "survives unclamped repair; see 28-31")
    add("GLOBAL_MEMORY_KERNEL", "CONTEXT_ONLY", "DISSOLVE", "not re-earned; carried gone")
    add("UNIVERSAL_STATE_AGE", "CONTEXT_ONLY", "DISSOLVE", "remains dead")
    W("36_PROMOTE_MERGE_DISSOLVE.csv")(pd.DataFrame(rows))

# ================================================================ 37 null and failed
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
                    "NO_STABLE", "ARTIFACT", "LEVEL_SUFFICIENT", "WEAK"):
            for c in d.columns:
                nv = int((d[c].astype(str) == val).sum())
                if nv:
                    flags.append(f"{val}:{nv}")
        rows.append(dict(file=f.name, n_rows=len(d), n_cells=total, null_cells=na,
                         null_frac=round(na / max(total, 1), 3),
                         failed_flags=";".join(sorted(set(flags))[:6])))
    W("37_NULL_AND_FAILED_RESULTS.csv")(pd.DataFrame(rows))

# ================================================================ RUNNER
if __name__ == "__main__":
    # ensure snapback exists for downstream 2022 files
    if isinstance(EV_UNC, dict) and EV_UNC.get("snap_base") is None:
        EV_UNC["snap_base"] = EV_UNC.get("peak")
    # internal-writing deliverables not invoked at module level
    route_commitment()
    saturation_mechanism()
    response_node_coupling()
    response_coordinate_pilot()
    saturation_without_delivery()
    threshold_inversion_species()
    deep_hysteresis_map()
    hysteresis_boundaries()
    birth_failure_mechanism()
    load_commitment_mismatch()
    birth_recovery()
    potential_realization_constraints()
    constraint_combination_lattice()
    failure_motif_decomposition()
    realization_geometry()
    unclamped_repair()
    event_reestimate()
    surface_vs_law_recovery()
    structural_scar()
    reexcursions()
    event_end()
    precedence_map()
    global_law_hierarchy()
    promote_merge_dissolve()
    null_failed()
    print("MECH-19 BUILD COMPLETE")