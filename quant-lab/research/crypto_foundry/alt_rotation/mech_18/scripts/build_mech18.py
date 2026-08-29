#!/usr/bin/env python
"""ALT_MECH_18 - EDGE-LAW & RESPONSE-LAW CARTOGRAPHY orchestration.

Computes and writes mech_18 deliverable files 02..32. Narrative files
(01 prereg, 33 global law freeze map, 34 summary, 35 decision) are written
alongside by the agent after reviewing the computed CSVs.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import os, pickle, sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, ranksums
from sklearn.linear_model import LinearRegression, LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m18base as B
from _m18base import (load_frame, load_caches, DEPTH_ORDER, SUBPERIODS,
                      exit_dist_series, js_divergence, memory_kernels,
                      edge_table, _rho, _partial_rho, _fmean, W2022_LO,
                      W2022_HI)
from _m17base import logistic_params, hill_params

OUT = B.OUT

# ------------------------------------------------------------------ substrate
df = load_frame()
dfc = df.reset_index(drop=True)
act, fams, demand, bm6, bm8 = load_caches()
forcing_series = pd.to_numeric(fams["COMMON_FORCING"], errors="coerce").reset_index(drop=True)
fam_cols = [c for c in fams.columns if c not in ("d", "COMMON_FORCING")]
field_act = act["FIELD"].to_numpy()
ent6 = bm6["ent"].to_numpy(); k6 = bm6["k"].to_numpy(); p16 = bm6["p1"].to_numpy()
p26 = bm6["p2"].to_numpy()
ent8 = bm8["ent"].to_numpy()
demand_arr = demand.to_numpy()
g6 = dfc["grp6"].to_numpy(); g6n = dfc["grp6_next"].to_numpy()
g8 = dfc["grp8"].to_numpy(); g8n = dfc["grp8_next"].to_numpy()
subp_arr = dfc["subperiod"].to_numpy()
prop7 = pd.to_numeric(dfc["prop7"], errors="coerce").to_numpy()
ren7 = pd.to_numeric(dfc["reentry7"], errors="coerce").to_numpy()
rank7 = pd.to_numeric(dfc["rank7"], errors="coerce").to_numpy()
pos_share = pd.to_numeric(dfc["pos_ret_share"], errors="coerce").to_numpy()
disp7 = pd.to_numeric(dfc["top500_dispersion_7d"], errors="coerce").to_numpy()
conc = pd.to_numeric(dfc["top3_share"], errors="coerce").to_numpy()
rankd = pd.to_numeric(dfc["rank_depth_rel"], errors="coerce").to_numpy()
vol_med = pd.to_numeric(dfc["vol_med"], errors="coerce").to_numpy()
btc7 = pd.to_numeric(dfc["btc_return_7d"], errors="coerce").to_numpy()


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

# ================================================================ 02 EDGE REGISTRY
def edge_registry():
    rows = []
    for res, col, ncol in [("6CELL", "grp6", "grp6_next"), ("8CELL", "grp8", "grp8_next")]:
        et = edge_table(dfc, col, ncol, demand=demand_arr,
                        forcing_series=forcing_series.to_numpy(),
                        entropy_series=ent6)
        et.insert(0, "resolution", res)
        rows.append(et)
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["resolution", "from_state", "prob"], ascending=[True, True, False])

W02 = W("02_EDGE_REGISTRY.csv", index=False)
W02(edge_registry())

# ================================================================ 03 EDGE HAZARDS
def edge_hazards():
    rows = []
    # time-in-state (run length) per day
    run = np.zeros(len(dfc), dtype=int)
    for i in range(1, len(dfc)):
        run[i] = run[i - 1] + 1 if g6[i] == g6[i - 1] else 0
    tiers = np.full(len(dfc), "late", dtype=object)
    tiers[run <= 2] = "early"; tiers[(run > 2) & (run <= 6)] = "mid"
    dem_t = _tier(demand_arr); sat_t = _tier(field_act); ent_t = _tier(ent6)
    fdiff = np.diff(forcing_series.to_numpy(), prepend=0)
    rise = fdiff >= 0
    for s in np.unique(g6):
        sel = g6 == s
        n_in = int(sel.sum())
        if n_in < 60:
            continue
        for t in np.unique(g6n[~pd.isna(g6n)]):
            et = sel & (g6n == t)
            n = int(et.sum())
            if n == 0:
                continue
            h = n / n_in
            def haz(mask):
                d = int((sel & mask).sum())
                return round(float(et[mask].sum() / d), 4) if d >= 10 else np.nan
            rows.append(dict(from_state=s, to_state=t, n=n,
                base_hazard=round(float(h), 4),
                hazard_early_run= haz(tiers == "early"),
                hazard_mid_run= haz(tiers == "mid"),
                hazard_late_run= haz(tiers == "late"),
                hazard_demand_lo= haz(dem_t == "low"),
                hazard_demand_hi= haz(dem_t == "high"),
                hazard_sat_lo= haz(sat_t == "low"),
                hazard_sat_hi= haz(sat_t == "high"),
                hazard_ent_lo= haz(ent_t == "low"),
                hazard_ent_hi= haz(ent_t == "high"),
                hazard_rising= haz(rise),
                hazard_falling= haz(~rise)))
    out = pd.DataFrame(rows)
    # per-state clock verdict: does hazard change with run length?
    verdicts = []
    for s in np.unique(g6):
        g = out[out["from_state"] == s]
        if len(g) == 0:
            continue
        dom = g.sort_values("base_hazard", ascending=False).iloc[0]
        h = [dom["hazard_early_run"], dom["hazard_mid_run"], dom["hazard_late_run"]]
        h = [x for x in h if x == x]
        span = (max(h) - min(h)) if len(h) >= 2 else np.nan
        base = dom["base_hazard"]
        if span == span and base > 0:
            rel = span / base
            verdict = "EDGE_CLOCKS_EARNED" if rel >= 0.5 else ("WEAK_EDGE_TIMING" if rel >= 0.25 else "NO_STABLE_EDGE_CLOCK")
        else:
            verdict = "DATA_LIMITED"
        verdicts.append(dict(from_state=s, dominant_exit=dom["to_state"],
            hazard_span=round(float(span), 4) if span == span else np.nan,
            hazard_span_rel=round(float(span / base), 3) if (span == span and base > 0) else np.nan,
            clock_verdict=verdict))
    return out, pd.DataFrame(verdicts)

_03a, _03b = edge_hazards()
W03a = W("03_EDGE_HAZARDS.csv", index=False)
W03a(_03a)
W03b = W("03b_EDGE_CLOCK_VERDICTS.csv", index=False)
W03b(_03b)

# ================================================================ 04 EXIT AVAILABILITY vs PRESSURE
def exit_avail_pressure():
    rows = []
    for res, col, bm in [("6CELL", "grp6", bm6), ("8CELL", "grp8", bm8)]:
        g = dfc[col].to_numpy()
        for s in np.unique(g):
            sel = g == s
            m = bm.loc[sel]
            v = m.dropna(subset=["ent", "p1"])
            if len(v) < 30:
                continue
            ent = v["ent"].to_numpy(); k = v["k"].to_numpy(); p1 = v["p1"].to_numpy()
            p2 = v["p2"].to_numpy()
            r_k = _rho(ent, k); r_p1 = _rho(ent, p1)
            if r_k == r_k and r_p1 == r_p1:
                driver = ("EDGE_PRUNING" if abs(r_k) >= abs(r_p1)
                          else "PRESSURE_CONCENTRATION")
            else:
                driver = "DATA_LIMITED"
            # reopening frequency: exits observed in 2nd half but not 1st half
            half = int(sel.sum() // 2)
            idx = np.where(sel)[0]
            first = set(g6n[idx[:half]]) if res == "6CELL" else set(g8n[idx[:half]])
            second = set(g6n[idx[half:]]) if res == "6CELL" else set(g8n[idx[half:]])
            reopened = len(second - first)
            rows.append(dict(resolution=res, state=s, n=int(sel.sum()),
                n_live_exits=round(float(v["k"].mean()), 2),
                effective_exit_count=round(float(np.mean(2 ** ent)), 2),
                mean_exit_entropy=round(float(ent.mean()), 3),
                dominant_exit_share_p1=round(float(p1.mean()), 3),
                second_share_p2=round(float(np.nanmean(p2)), 3),
                p1_p2_gap=round(float(np.nanmean(p1) - np.nanmean(p2)), 3),
                reopening_exits=int(reopened),
                corr_entropy_k=round(r_k, 3) if r_k == r_k else np.nan,
                corr_entropy_p1=round(r_p1, 3) if r_p1 == r_p1 else np.nan,
                resolution_driver=driver))
    return pd.DataFrame(rows)

W04 = W("04_EXIT_AVAILABILITY_PRESSURE.csv", index=False)
W04(exit_avail_pressure())

# ================================================================ 05 ENTROPY HIERARCHY
def entropy_hierarchy():
    rows = []
    for res, col, bm in [("6CELL", "grp6", bm6), ("8CELL", "grp8", bm8)]:
        g = dfc[col].to_numpy()
        ent = bm["ent"].to_numpy(); k = bm["k"].to_numpy(); p1 = bm["p1"].to_numpy()
        for s in np.unique(g):
            sel = g == s
            for sp in SUBPERIODS:
                m = sel & (subp_arr == sp)
                e = ent[m]; kk = k[m]; pp = p1[m]
                e = e[~np.isnan(e)]
                if len(e) < 30:
                    continue
                # deltas (resolution velocity)
                d1 = np.diff(e, n=1); d3 = np.diff(e, n=3); d7 = np.diff(e, n=7)
                # time-to-low-entropy: forward search from high-entropy days
                lo_b = np.nanquantile(ent[sel], 0.25)
                hi_mask = (ent[sel] >= np.nanquantile(ent[sel], 0.75))
                tt = []
                idx = np.where(sel)[0]
                hi_idx = idx[hi_mask]
                for i in hi_idx:
                    j = i + 1
                    while j < len(dfc) and j <= i + 60:
                        if ent[j] < lo_b and not np.isnan(ent[j]):
                            tt.append(j - i); break
                        j += 1
                # reopening: entropy rise after contraction
                cont = (ent[sel] < np.nanquantile(ent[sel], 0.25)) & np.roll(hi_mask, -5)
                reopen = float(cont.mean()) if cont.sum() >= 5 else np.nan
                rows.append(dict(resolution=res, state=s, subperiod=sp, n=int(len(e)),
                    exit_count_k=round(float(np.nanmean(kk)), 2),
                    exit_entropy=round(float(np.nanmean(e)), 3),
                    dominant_share_p1=round(float(np.nanmean(pp)), 3),
                    delta_ent_1d=round(float(np.nanmean(d1)), 4),
                    delta_ent_3d=round(float(np.nanmean(d3)), 4),
                    delta_ent_7d=round(float(np.nanmean(d7)), 4),
                    entropy_slope_rho=round(_rho(np.arange(len(e)), e), 3),
                    median_days_to_low_ent=round(float(np.median(tt)), 1) if tt else np.nan,
                    reopening_rate=round(reopen, 3) if reopen == reopen else np.nan))
    return pd.DataFrame(rows)

W05 = W("05_ENTROPY_HIERARCHY.csv", index=False)
W05(entropy_hierarchy())

# ================================================================ 06 ENTROPY DECAY
def entropy_decay():
    labels = []
    level = np.full(len(dfc), "CONSTRAINED", dtype=object)
    for s in np.unique(g6):
        m = g6 == s
        med = np.nanmedian(ent6[m])
        level[m] = np.where(ent6[m] >= med, "OPEN", "CONSTRAINED")
    d7 = np.full(len(dfc), np.nan)
    d7[:len(dfc) - 7] = ent6[7:] - ent6[:len(dfc) - 7]
    vel = np.full(len(dfc), "STABLE", dtype=object)
    vel[d7 <= -0.15] = "COLLAPSING"; vel[d7 >= 0.15] = "REOPENING"
    lab = np.char.add(np.char.add(level.astype(str), "_"), vel.astype(str))
    rows = []
    for name in np.unique(lab):
        m = lab == name
        if m.sum() < 40:
            continue
        rows.append(dict(label=name, n=int(m.sum()),
            mean_prop7=round(float(np.nanmean(prop7[m])), 4),
            mean_exit_rate=round(float(np.nanmean(1 - bm6["stay_share"].to_numpy()[m])), 4),
            mean_rank7=round(float(np.nanmean(rank7[m])), 4),
            mean_p1=round(float(np.nanmean(p16[m])), 4),
            mean_reentry7=round(float(np.nanmean(ren7[m])), 4)))
    # does velocity add info beyond level? compare within OPEN and CONSTRAINED
    info = []
    for lvl in ["OPEN", "CONSTRAINED"]:
        base = lab == f"{lvl}_STABLE"
        coll = lab == f"{lvl}_COLLAPSING"
        reop = lab == f"{lvl}_REOPENING"
        if base.sum() >= 40 and coll.sum() >= 40:
            p = float(ranksums(prop7[base], prop7[coll]).pvalue)
            info.append(dict(level=lvl, comparison="STABLE_vs_COLLAPSING",
                d_prop7=round(float(np.nanmean(prop7[base]) - np.nanmean(prop7[coll])), 4),
                ranksums_p=round(p, 4)))
        if base.sum() >= 40 and reop.sum() >= 40:
            p = float(ranksums(prop7[base], prop7[reop]).pvalue)
            info.append(dict(level=lvl, comparison="STABLE_vs_REOPENING",
                d_prop7=round(float(np.nanmean(prop7[base]) - np.nanmean(prop7[reop])), 4),
                ranksums_p=round(p, 4)))
    return pd.DataFrame(rows), pd.DataFrame(info)

_06a, _06b = entropy_decay()
W06a = W("06_ENTROPY_DECAY.csv", index=False)
W06a(_06a)
W06b = W("06b_ENTROPY_VELOCITY_INFO.csv", index=False)
W06b(_06b)

# ================================================================ 07 ROUTE DEFORMATION
def route_deformation():
    mat, labs = exit_dist_series(g6, 7)
    dts = dfc["d"].to_numpy()
    state_of = {}
    for i in range(len(dfc)):
        state_of.setdefault(g6[i], []).append(i)
    ref_hist = {}
    ref_reg = {}
    for s, idx in state_of.items():
        m = mat[idx]
        ref_hist[s] = np.nanmean(m, axis=0)
    for sp in np.unique(subp_arr):
        idx = np.where(subp_arr == sp)[0]
        ref_reg[sp] = np.nanmean(mat[idx], axis=0)
    js_hist = np.full(len(dfc), np.nan); js_reg = np.full(len(dfc), np.nan)
    js_prev = np.full(len(dfc), np.nan)
    for i in range(len(dfc)):
        p = mat[i]
        if np.isnan(p).all():
            continue
        js_hist[i] = js_divergence(p, ref_hist[g6[i]])
        js_reg[i] = js_divergence(p, ref_reg[subp_arr[i]])
        if i > 0 and not np.isnan(mat[i - 1]).all():
            js_prev[i] = js_divergence(p, mat[i - 1])
    rows = []
    for ref, arr in [("STATE_HISTORICAL", js_hist), ("REGIME_SUBPERIOD", js_reg),
                     ("PREVIOUS_DAY", js_prev)]:
        a = arr[~np.isnan(arr)]
        if len(a) < 60:
            continue
        rows.append(dict(reference=ref, n=len(a),
            mean=round(float(a.mean()), 4), median=round(float(np.median(a)), 4),
            p90=round(float(np.quantile(a, 0.90)), 4),
            max=round(float(a.max()), 4)))
    # subperiod means of state-historical deformation
    sp_rows = []
    for sp in SUBPERIODS:
        m = (subp_arr == sp) & ~np.isnan(js_hist)
        if m.sum() < 40:
            continue
        sp_rows.append(dict(subperiod=sp, mean_js_vs_state=round(float(js_hist[m].mean()), 4)))
    out = pd.DataFrame(rows)
    out2 = pd.DataFrame(sp_rows)
    # verdict: robust if median state-JS reasonably bounded and regime ref differs
    med = float(np.nanmedian(js_hist)) if np.isfinite(np.nanmedian(js_hist)) else np.nan
    p90v = float(np.nanquantile(js_hist, 0.9)) if np.isfinite(np.nanquantile(js_hist, 0.9)) else np.nan
    verdict = ("PROMOTE" if (med == med and p90v == p90v and p90v < 0.5)
               else "LOCAL" if (med == med and p90v == p90v and p90v < 1.0)
               else "DISSOLVE")
    out2["verdict"] = verdict
    return out, out2

_07a, _07b = route_deformation()
W07a = W("07_ROUTE_DEFORMATION.csv", index=False)
W07a(_07a)
W07b = W("07b_ROUTE_DEFORMATION_SUBPERIOD.csv", index=False)
W07b(_07b)

# ================================================================ 08 FORCING PRIMITIVES
CONSTIT = {
    "PARTICIPATION_FORCING": ["breadth_vel", "pos_ret_share"],
    "DISPERSION_FORCING": ["top500_dispersion_7d"],
    "VOLATILITY_FORCING": ["vol_med"],
    "BTC_ANCHOR_FORCING": ["btc_return_7d"],
    "ETH_RELATIVE_FORCING": ["eth_btc_relative_return_7d"],
    "RANK_RECRUITMENT_FORCING": ["rank_depth_rel"],
    "CONCENTRATION_RELEASE_FORCING": ["top3_share_chg7"],
    "STABLECOIN_CAPITAL_FORCING": ["stablecoin_change_7d"],
    "PHYSICAL_DISTURBANCE_FORCING": ["total_mcap_chg30"],
}
PACT = (act[DEPTH_ORDER] >= 0.55).astype(float)
thr_pos = PACT.mean(axis=1).to_numpy()

def forcing_primitives():
    rows = []
    for fam in fam_cols:
        f = fams[fam].to_numpy()
        cons = CONSTIT.get(fam, [])
        cvals = []
        for c in cons:
            if c in dfc.columns:
                cvals.append(pd.to_numeric(dfc[c], errors="coerce").to_numpy())
        # within-family redundancy
        red = np.nanmean([abs(_rho(f, cv)) for cv in cvals]) if cvals else np.nan
        # regime stability: std of family mean across subperiods
        spm = [np.nanmean(f[subp_arr == sp]) for sp in SUBPERIODS]
        stab = float(np.nanstd(spm)) if len(spm) >= 3 else np.nan
        # associations
        edge_a = np.nanmean([abs(_rho(f, p16)), abs(_rho(f, ent6))])
        thr_a = abs(_rho(f, thr_pos))
        sat_a = abs(_rho(f, field_act))
        rank_a = np.nanmean([abs(_rho(f, act[p].to_numpy())) for p in DEPTH_ORDER])
        cross = np.nanmean([abs(_rho(f, fams[o].to_numpy()))
                            for o in fam_cols if o != fam])
        rows.append(dict(family=fam, constituents="|".join(cons),
            within_family_redundancy=round(red, 3) if red == red else np.nan,
            regime_stability_std_of_mean=round(stab, 4) if stab == stab else np.nan,
            edge_assoc_mean_abs_rho=round(edge_a, 3),
            threshold_assoc_abs_rho=round(thr_a, 3),
            saturation_assoc_abs_rho=round(sat_a, 3),
            rank_patch_assoc_mean_abs_rho=round(rank_a, 3),
            cross_family_mean_abs_rho=round(cross, 3)))
    return pd.DataFrame(rows)

W08 = W("08_FORCING_PRIMITIVES.csv", index=False)
W08(forcing_primitives())

# ================================================================ 09 FORCING HIERARCHY
def forcing_hierarchy():
    rows = []
    n = len(dfc)
    for a in fam_cols:
        fa = fams[a].to_numpy()
        up = []
        for b in fam_cols:
            if a == b:
                continue
            fb = fams[b].to_numpy()
            ab = _rho(fa[:-1], fb[1:])      # a today -> b tomorrow
            ba = _rho(fb[:-1], fa[1:])      # b today -> a tomorrow
            up.append((ab - ba) if (ab == ab and ba == ba) else np.nan)
        upscore = float(np.nanmean(up)) if len(up) else np.nan
        cont = np.nanmean([abs(_rho(fams[a].to_numpy(), fams[b].to_numpy()))
                           for b in fam_cols if b != a])
        rows.append(dict(family=a,
            upstream_score=round(upscore, 4) if upscore == upscore else np.nan,
            mean_contemporaneous_abs_corr=round(cont, 3)))
    out = pd.DataFrame(rows)
    # classify: redundant pairs
    pairs = []
    for i, a in enumerate(fam_cols):
        for b in fam_cols[i + 1:]:
            r = _rho(fams[a].to_numpy(), fams[b].to_numpy())
            pairs.append(dict(family_a=a, family_b=b,
                contemporaneous_rho=round(r, 3) if r == r else np.nan,
                lag_a_to_b=round(_rho(fams[a].to_numpy()[:-1], fams[b].to_numpy()[1:]), 3),
                lag_b_to_a=round(_rho(fams[b].to_numpy()[:-1], fams[a].to_numpy()[1:]), 3)))
    return out, pd.DataFrame(pairs)

_09a, _09b = forcing_hierarchy()
W09a = W("09_FORCING_HIERARCHY.csv", index=False)
W09a(_09a)
W09b = W("09b_FORCING_PAIRWISE.csv", index=False)
W09b(_09b)

# ================================================================ 10 ROUTE-SPECIFIC FORCING
def route_specific_forcing():
    mat6, _ = exit_dist_series(g6, 7)
    reg = pd.read_csv(OUT / "02_EDGE_REGISTRY.csv")
    major = reg[(reg["edge_class"].isin(["PRIMARY", "SECONDARY", "STAY"])) & (reg["n"] >= 30)]
    rows = []
    for _, r in major.iterrows():
        res = r["resolution"]
        col = "grp6" if res == "6CELL" else "grp8"
        ncol = "grp6_next" if res == "6CELL" else "grp8_next"
        s, t = r["from_state"], r["to_state"]
        g = dfc[col].to_numpy()
        m = (g == s)
        if m.sum() < 60:
            continue
        labels = sorted(set(dfc[ncol].dropna().unique().tolist()), key=str)
        # pressure toward t in forward-7d window among days in state s
        if res == "6CELL":
            mat = mat6
            lab_ok = labels == sorted(set(g6n[~pd.isna(g6n)]), key=str)
            labi = sorted(set(g6n[~pd.isna(g6n)]), key=str).index(t)
        else:
            mat, lab_ok = None, None
            labi = labels.index(t)
            if labi is None:
                continue
        if res == "6CELL":
            press = mat[m, labi]
        else:
            # recompute 8-cell forward-window pressure
            mat8, _ = exit_dist_series(g8, 7)
            press = mat8[m, labels.index(t)]
        for fam in fam_cols:
            rho = _rho(fams[fam].to_numpy()[m], press, min_n=30)
            rows.append(dict(edge=f"{s}->{t}", resolution=res,
                forcing_family=fam, rho=round(rho, 3) if rho == rho else np.nan,
                n=int(m.sum())))
    out = pd.DataFrame(rows)
    return out.sort_values(["edge", "forcing_family"])

W10 = W("10_ROUTE_SPECIFIC_FORCING.csv", index=False)
W10(route_specific_forcing())

# ================================================================ threshold helpers
def logit_fit(forcing, pf, min_n=80):
    x = np.asarray(forcing, dtype=float); y = np.asarray(pf, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y)); x, y = x[m], y[m]
    if len(x) < min_n or y.sum() < 10 or (1 - y).sum() < 10:
        return None
    mu, sd = float(x.mean()), float(x.std())
    if sd <= 0:
        return None
    xs = (x - mu) / sd
    clf = LogisticRegression(max_iter=1000).fit(xs.reshape(-1, 1), y)
    b0, b1 = float(clf.intercept_[0]), float(clf.coef_[0][0])
    return dict(mu=mu, sd=sd, b0=b0, b1=b1, n=len(x))


def thr_at(par, prob):
    return par["mu"] + (np.log(prob / (1 - prob)) - par["b0"]) / (par["b1"] + 1e-9) * par["sd"]


def _thr50_table():
    """patch x subperiod half-saturation threshold table."""
    rows = []
    for patch in DEPTH_ORDER:
        pf = PACT[patch].to_numpy(); fc = forcing_series.to_numpy()
        for sp in SUBPERIODS:
            idx = (subp_arr == sp)
            par = logit_fit(fc[idx], pf[idx])
            if par is None:
                continue
            rows.append(dict(patch=patch, subperiod=sp, n=par["n"],
                thr50=round(thr_at(par, 0.50), 3)))
    return pd.DataFrame(rows)

THR50_TABLE = _thr50_table()

# ================================================================ 11 THRESHOLD DEPENDENCIES
def threshold_dependencies():
    cond_cols = {"VOLATILITY": vol_med, "DISPERSION": disp7, "CONCENTRATION": conc,
                 "EXIT_ENTROPY": ent6, "RANK_DEPTH": rankd, "BTC_ANCHOR": btc7,
                 "DEMAND": demand_arr}
    fdiff = np.diff(forcing_series.to_numpy(), prepend=0)
    cond_cols["HYSTERESIS_DIRECTION"] = None
    rows = []
    for patch in DEPTH_ORDER:
        pf = PACT[patch].to_numpy(); fc = forcing_series.to_numpy()
        for label, cvar in cond_cols.items():
            if cvar is None:
                c = np.where(fdiff >= 0, 1.0, 0.0)  # rising=1 falling=0
            else:
                c = cvar
            ok = ~(np.isnan(c) | np.isnan(pf) | np.isnan(fc))
            if ok.sum() < 150:
                continue
            q = np.nanquantile(c[ok], [1 / 3, 2 / 3])
            tvals = {}
            for tier, mask in {"low": c <= q[0], "mid": (c > q[0]) & (c < q[1]),
                               "high": c >= q[1]}.items():
                m = ok & mask
                if m.sum() < 60:
                    continue
                par = logit_fit(fc[m], pf[m], min_n=50)
                tvals[tier] = (thr_at(par, 0.50), thr_at(par, 0.90) - thr_at(par, 0.10)) if par else (np.nan, np.nan)
            if len(tvals) < 2:
                continue
            t50 = {k: v[0] for k, v in tvals.items()}
            tw = {k: v[1] for k, v in tvals.items()}
            rows.append(dict(patch=patch, conditioning=label, n=int(ok.sum()),
                thr50_low=round(float(t50["low"]), 3) if np.isfinite(t50["low"]) else np.nan,
                thr50_mid=round(float(t50.get("mid", np.nan)), 3) if np.isfinite(t50.get("mid", np.nan)) else np.nan,
                thr50_high=round(float(t50["high"]), 3) if np.isfinite(t50["high"]) else np.nan,
                thr50_shift_high_minus_low=round(float(t50["high"] - t50["low"]), 3),
                band_width_low=round(float(tw["low"]), 3) if np.isfinite(tw["low"]) else np.nan,
                band_width_high=round(float(tw["high"]), 3) if np.isfinite(tw["high"]) else np.nan,
                band_width_shift=round(float(tw["high"] - tw["low"]), 3)))
    out = pd.DataFrame(rows)
    # subperiod rows appended as separate block
    sp_rows = []
    for patch in DEPTH_ORDER:
        pf = PACT[patch].to_numpy(); fc = forcing_series.to_numpy()
        for sp in SUBPERIODS:
            idx = (subp_arr == sp)
            par = logit_fit(fc[idx], pf[idx])
            if par is None:
                continue
            sp_rows.append(dict(patch=patch, conditioning="SUBPERIOD", subperiod=sp,
                thr50=round(thr_at(par, 0.50), 3),
                band_width=round(thr_at(par, 0.90) - thr_at(par, 0.10), 3)))
    return out, pd.DataFrame(sp_rows)

_11a, _11b = threshold_dependencies()
W11a = W("11_THRESHOLD_DEPENDENCIES.csv", index=False)
W11a(_11a)
W11b = W("11b_THRESHOLD_SUBPERIOD.csv", index=False)
W11b(_11b)

# ================================================================ 12 THRESHOLD HIERARCHY
def threshold_hierarchy():
    tbl = THR50_TABLE.pivot(index="subperiod", columns="patch", values="thr50")
    tbl = tbl.reindex(columns=DEPTH_ORDER)
    rows = []
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            va = tbl[a]; vb = tbl[b]
            m = va.notna() & vb.notna()
            if m.sum() < 3:
                continue
            gap = (vb[m] - va[m]).to_numpy()
            frac = float((gap >= 0).mean())  # deep requires >= shallow
            rows.append(dict(shallow=a, deep=b, n_subperiods=int(m.sum()),
                frac_deep_ge_shallow=round(frac, 3),
                mean_gap=round(float(gap.mean()), 3),
                min_gap=round(float(gap.min()), 3), max_gap=round(float(gap.max()), 3),
                inversion_subperiods="|".join(tbl.index[m][gap < 0].astype(str))))
    out = pd.DataFrame(rows)
    # overall monotonicity: within each subperiod, thr50 non-decreasing in depth?
    mono = []
    for sp in tbl.index:
        v = tbl.loc[sp].to_numpy()
        mono.append(float((np.diff(v) >= 0).mean()) if len(v) >= 3 else np.nan)
    frac_mono = float(np.nanmean(mono)) if mono else np.nan
    overall = pd.DataFrame([dict(frac_subperiods_monotonic=round(frac_mono, 3),
        verdict="NESTED_THRESHOLD_HIERARCHY" if frac_mono >= 0.8 else
               ("MOSTLY_NESTED_WITH_LOCAL_INVERSIONS" if frac_mono >= 0.5 else "NO_STABLE_HIERARCHY"))])
    return out, overall

_12a, _12b = threshold_hierarchy()
W12a = W("12_THRESHOLD_HIERARCHY.csv", index=False)
W12a(_12a)
W12b = W("12b_THRESHOLD_HIERARCHY_OVERALL.csv", index=False)
W12b(_12b)

# ================================================================ 13 RESPONSE FINGERPRINTS
def _fingerprint(x, y, fdiff):
    """One response fingerprint from forcing x and response y."""
    ceil, x0, k, rmse, n = logistic_params(x, y)
    if n < 60 or np.isnan(ceil):
        return None
    lo, hi = float(np.nanmin(y)), float(np.nanmax(y))
    def x_of_frac(f):
        yf = lo + f * (ceil - lo)
        return x0 + np.log(yf / max(ceil - yf, 1e-9)) / k if k != 0 else np.nan
    onset = x_of_frac(0.20); highz = x_of_frac(0.70)
    top = y[x >= np.quantile(x, 0.85)]
    persistence = float(np.nanmean(top)) if len(top) >= 10 else np.nan
    # relaxation: response 3-7d after a forcing peak
    rel = np.nan
    peak_days = np.where((x >= np.quantile(x, 0.9)) & (fdiff <= 0))[0]
    relax = []
    for i in peak_days:
        j = i + 3
        if j + 4 < len(y):
            relax.append(float(np.nanmean(y[j:j + 5])))
    if len(relax) >= 10:
        rel = float(np.nanmean(relax))
    # hysteresis gap (binned rising - falling at same forcing level)
    gaps = []
    bins = np.quantile(x, np.linspace(0, 1, 7))
    for i in range(len(bins) - 1):
        sel = (x >= bins[i]) & (x < bins[i + 1]) & ~np.isnan(fdiff)
        if sel.sum() < 30:
            continue
        ru = sel & (fdiff >= 0); rd = sel & (fdiff < 0)
        if ru.sum() < 10 or rd.sum() < 10:
            continue
        gaps.append(float(np.nanmean(y[ru]) - np.nanmean(y[rd])))
    hgap = float(np.nanmean(gaps)) if len(gaps) >= 2 else np.nan
    return dict(onset_f20=onset, half_sat_x0=x0, slope_k=k, ceiling=ceil,
                overshoot=hi - ceil, persistence=persistence,
                relaxation_after_peak=rel, hysteresis_gap=hgap,
                fit_rmse=rmse, n=n)


def response_fingerprints():
    fdiff = np.diff(forcing_series.to_numpy(), prepend=0)
    series = [("FIELD", act["FIELD"].to_numpy())]
    for p in DEPTH_ORDER:
        series.append((p, act[p].to_numpy()))
    rows = []
    for name, y in series:
        x = forcing_series.to_numpy()
        for sp in SUBPERIODS:
            idx = (subp_arr == sp)
            m = ~(np.isnan(x) | np.isnan(y)) & idx
            if m.sum() < 60:
                continue
            fp = _fingerprint(x[m], y[m], fdiff[m])
            if fp is None:
                continue
            rows.append(dict(response=name, subperiod=sp, **{k: round(v, 4) if isinstance(v, float) else v for k, v in fp.items()}))
    return pd.DataFrame(rows)

W13 = W("13_RESPONSE_FINGERPRINTS.csv", index=False)
W13(response_fingerprints())

# ================================================================ 14 SATURATION DATA COLLAPSE
def saturation_data_collapse():
    train = (subp_arr != "2025-2026")
    test = ~train
    rows = []
    pooled_x = []; pooled_y = []
    for p in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[p].to_numpy()
        m = ~(np.isnan(x) | np.isnan(y))
        # full-sample fit for normalization constants
        ceil, x0, k, _, n = logistic_params(x[m], y[m])
        if n < 60 or np.isnan(ceil):
            continue
        xs = (x[m] - x0) * k
        ys = y[m] / ceil
        pooled_x.append(xs); pooled_y.append(ys)
        # local fit on normalized space (train only)
        tr = train[m]; te = test[m]
        if tr.sum() < 60 or te.sum() < 40:
            continue
        cx, cy = xs[tr], ys[tr]
        tx, ty = xs[te], ys[te]
        def fit(xs_, ys_):
            try:
                from scipy.optimize import curve_fit
                def model(X, a, b):
                    return 1.0 / (1.0 + np.exp(-(X - a) * b))
                popt, _ = curve_fit(model, xs_, ys_, p0=[0.0, 1.0],
                                    bounds=([-5, 0.05], [5, 20]), maxfev=20000)
                return popt
            except Exception:
                return None
        pl = fit(cx, cy)
        if pl is None:
            continue
        loc_rmse = float(np.sqrt(np.mean((1.0 / (1 + np.exp(-(tx - pl[0]) * pl[1])) - ty) ** 2)))
        rows.append(dict(patch=p, n_train=int(tr.sum()), n_test=int(te.sum()),
            local_normalized_test_rmse=round(loc_rmse, 4)))
    X = np.concatenate(pooled_x); Y = np.concatenate(pooled_y)
    Xtr, Ytr, Xte, Yte = [], [], [], []
    for p in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[p].to_numpy()
        m = ~(np.isnan(x) | np.isnan(y))
        ceil, x0, k, _, n = logistic_params(x[m], y[m])
        if n < 60 or np.isnan(ceil):
            continue
        xs = (x[m] - x0) * k; ys = y[m] / ceil
        tr = train[m]; te = test[m]
        Xtr.append(xs[tr]); Ytr.append(ys[tr])
        if te.sum() >= 40:
            Xte.append(xs[te]); Yte.append(ys[te])
    Xtr = np.concatenate(Xtr); Ytr = np.concatenate(Ytr)
    Xte = np.concatenate(Xte) if Xte else np.array([])
    Yte = np.concatenate(Yte) if Yte else np.array([])
    def fit_common(xs_, ys_):
        try:
            from scipy.optimize import curve_fit
            def model(X, a, b):
                return 1.0 / (1.0 + np.exp(-(X - a) * b))
            popt, _ = curve_fit(model, xs_, ys_, p0=[0.0, 1.0],
                                bounds=([-5, 0.05], [5, 20]), maxfev=20000)
            return popt
        except Exception:
            return None
    pc = fit_common(Xtr, Ytr)
    if pc is None or len(Xte) == 0:
        pooled_rmse = np.nan; ratio = np.nan; verdict = "DATA_LIMITED"
    else:
        pooled_rmse = float(np.sqrt(np.mean((1.0 / (1 + np.exp(-(Xte - pc[0]) * pc[1])) - Yte) ** 2)))
        loc_mean = float(np.nanmean([r["local_normalized_test_rmse"] for r in rows]))
        ratio = pooled_rmse / loc_mean if loc_mean > 0 else np.nan
        verdict = ("UNIVERSALISH_RESPONSE_SHAPE" if ratio <= 1.25 else
                   "FEW_NORMALIZED_SHAPES" if ratio <= 1.6 else "STATE_LOCAL_SHAPES")
    rows.append(dict(patch="POOLED", n_train=int(len(Xtr)), n_test=int(len(Xte)),
        local_normalized_test_rmse=np.nan,
        pooled_normalized_test_rmse=round(pooled_rmse, 4) if pooled_rmse == pooled_rmse else np.nan,
        ratio_pooled_over_local=round(ratio, 3) if ratio == ratio else np.nan,
        verdict=verdict))
    out = pd.DataFrame(rows)
    out["pooled_normalized_test_rmse"] = out["pooled_normalized_test_rmse"].fillna(np.nan)
    out.loc[out["patch"] == "POOLED", "pooled_normalized_test_rmse"] = (
        round(pooled_rmse, 4) if pooled_rmse == pooled_rmse else np.nan)
    return out

W14 = W("14_SATURATION_DATA_COLLAPSE.csv", index=False)
W14(saturation_data_collapse())

# ================================================================ 15 RESPONSE DIMENSIONALITY
def response_dimensionality():
    # global median nodes across patches (full sample)
    meds = {}
    for node in ["x0", "k", "ceiling"]:
        vals = []
        for p in DEPTH_ORDER:
            x = forcing_series.to_numpy(); y = act[p].to_numpy()
            m = ~(np.isnan(x) | np.isnan(y))
            ceil, x0, k, _, n = logistic_params(x[m], y[m])
            if n < 60 or np.isnan(ceil):
                continue
            vals.append({"x0": x0, "k": k, "ceiling": ceil}[node])
        meds[node] = float(np.median(vals))
    def sigmoid(x, ceil, x0, k):
        return ceil / (1 + np.exp(-k * (x - x0)))
    rows = []
    for p in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[p].to_numpy()
        m = ~(np.isnan(x) | np.isnan(y))
        ceil, x0, k, _, n = logistic_params(x[m], y[m])
        if n < 60 or np.isnan(ceil):
            continue
        y3 = sigmoid(x[m], ceil, x0, k)
        y2 = sigmoid(x[m], ceil, x0, meds["k"])
        # 1-param: only ceiling free (k, x0 at cross-patch medians)
        s1 = 1 / (1 + np.exp(-meds["k"] * (x[m] - meds["x0"])))
        c1 = np.sum(s1 * y[m]) / max(np.sum(s1 * s1), 1e-12)
        y1 = c1 * s1
        y0 = np.full(int(n), np.nanmean(y[m]))
        def _rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
        def _r2(a, b): return float(1 - np.sum((a - b) ** 2) / max(np.sum((a - a.mean()) ** 2), 1e-12))
        rows.append({
            "patch": p, "n": int(n),
            "rmse_1param": _rmse(y[m], y1), "rmse_2param": _rmse(y[m], y2),
            "rmse_3param": _rmse(y[m], y3), "rmse_baseline": _rmse(y[m], y0),
            "r2_1param": _r2(y[m], y1), "r2_2param": _r2(y[m], y2),
            "r2_3param": _r2(y[m], y3),
            "gain_2v1": _rmse(y[m], y1) - _rmse(y[m], y2),
            "gain_3v2": _rmse(y[m], y2) - _rmse(y[m], y3),
            "gain_3v1": _rmse(y[m], y1) - _rmse(y[m], y3),
        })
    W("15_RESPONSE_DIMENSIONALITY.csv")(pd.DataFrame(rows).round(4))

# ================================================================ 16 SATURATION NODE DYNAMICS
def saturation_node_dynamics():
    dates = pd.to_datetime(dfc["d"])
    dmin, dmax = dates.min(), dates.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=180), freq="30D")
    wins = [(t0, t0 + pd.Timedelta(days=180)) for t0 in starts]
    node_s = {p: {"x0": [], "k": [], "ceiling": [], "win": []} for p in DEPTH_ORDER}
    for (t0, t1) in wins:
        mw = (dates >= t0) & (dates < t1)
        if int(mw.sum()) < 60:
            continue
        xw = forcing_series.to_numpy()[mw]
        for p in DEPTH_ORDER:
            yw = act[p].to_numpy()[mw]
            m2 = ~(np.isnan(xw) | np.isnan(yw))
            if int(m2.sum()) < 60:
                node_s[p]["x0"].append(np.nan); node_s[p]["k"].append(np.nan)
                node_s[p]["ceiling"].append(np.nan); node_s[p]["win"].append(str(t0.date()))
                continue
            ceil, x0, k, _, _ = logistic_params(xw[m2], yw[m2])
            node_s[p]["x0"].append(x0); node_s[p]["k"].append(k)
            node_s[p]["ceiling"].append(ceil); node_s[p]["win"].append(str(t0.date()))
    rows = []
    for p in DEPTH_ORDER:
        wl = node_s[p]["win"]
        if len(wl) < 6:
            continue
        rec = {"patch": p, "n_windows": len(wl)}
        chg = {}
        for node in ("x0", "k", "ceiling"):
            v = np.array(node_s[p][node], dtype=float)
            dv = np.diff(v)
            lag = v[:-1]
            mf = ~(np.isnan(dv) | np.isnan(lag))
            slope = np.polyfit(lag[mf], dv[mf], 1)[0] if mf.sum() >= 10 else np.nan
            ac = np.corrcoef(v[:-1], v[1:])[0, 1] if np.isfinite(v).sum() >= 8 else np.nan
            rec[f"{node}_mean"] = float(np.nanmean(v))
            rec[f"{node}_std"] = float(np.nanstd(v))
            rec[f"{node}_drift30d"] = float(np.nanmean(np.abs(dv)))
            rec[f"{node}_autocorr"] = float(ac) if ac is not None else np.nan
            rec[f"{node}_reversion"] = float(slope) if not np.isnan(slope) else np.nan
            chg[node] = np.array(dv, dtype=float)
        cor = {}
        for (a, b) in (("x0", "k"), ("x0", "ceiling"), ("k", "ceiling")):
            ma = np.isfinite(chg[a]) & np.isfinite(chg[b])
            cor[f"corr_{a}_{b}"] = float(np.corrcoef(chg[a][ma], chg[b][ma])[0, 1]) if ma.sum() >= 10 else np.nan
        rec.update(cor)
        cv = [abs(rec[f"corr_{a}_{b}"]) for (a, b) in (("x0", "k"), ("x0", "ceiling"), ("k", "ceiling"))]
        if all(c >= 0.4 for c in cv if not np.isnan(c)) and cv:
            rec["node_verdict"] = "COORDINATED_NODE_MOTION"
        elif any(c >= 0.4 for c in cv if not np.isnan(c)):
            rec["node_verdict"] = "PARTIAL_COUPLING"
        else:
            rec["node_verdict"] = "INDEPENDENT_NODE_DRIFT"
        rows.append(rec)
    W("16_SATURATION_NODE_DYNAMICS.csv")(pd.DataFrame(rows).round(4))
# ================================================================ 17 GLOBAL HYSTERESIS RECHECK
def global_hysteresis_recheck():
    fc = forcing_series.to_numpy()
    d3 = np.full(len(fc), np.nan); d3[3:] = fc[3:] - fc[:-3]
    thr = np.nanstd(d3) * 0.25
    direc = np.where(d3 > thr, "rising", np.where(d3 < -thr, "falling", "flat"))
    vol_t = _tier(vol_med); dem_t = _tier(demand_arr); ent_t = _tier(ent6)
    qs = np.nanquantile(fc, np.linspace(0, 1, 11))
    rows = []
    for p in DEPTH_ORDER:
        y = act[p].to_numpy()
        gaps = []
        for i in range(10):
            mb = (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
            mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
            if mr.sum() >= 15 and mf.sum() >= 15:
                gaps.append(float(np.mean(y[mr]) - np.mean(y[mf])))
        gap_raw = float(np.mean(gaps)) if gaps else np.nan
        gaps_c = []
        for s in np.unique(g6):
            ms0 = g6 == s
            for vt in ("low", "mid", "high"):
                ms = ms0 & (vol_t == vt)
                for i in range(10):
                    mb = ms & (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
                    mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
                    if mr.sum() >= 8 and mf.sum() >= 8:
                        gaps_c.append(float(np.mean(y[mr]) - np.mean(y[mf])))
        gap_ctl = float(np.mean(gaps_c)) if gaps_c else np.nan
        m = np.isfinite(y) & np.isfinite(fc) & np.isfinite(vol_med) & np.isfinite(demand_arr) & np.isfinite(ent6) & (direc != "flat")
        if m.sum() > 250:
            X = np.column_stack([fc[m], vol_med[m], demand_arr[m], ent6[m]])
            lr = LinearRegression().fit(X, y[m])
            res = y[m] - lr.predict(X)
            r_ = res[direc[m] == "rising"]; f_ = res[direc[m] == "falling"]
            if len(r_) > 20 and len(f_) > 20:
                gap_res = float(np.mean(r_) - np.mean(f_)); pval = float(ranksums(r_, f_).pvalue)
            else:
                gap_res, pval = np.nan, np.nan
        else:
            gap_res, pval = np.nan, np.nan
        if not np.isnan(gap_ctl) and abs(gap_ctl) >= 0.02 and pval < 0.05:
            verd = "HYSTERESIS_AFTER_CONTROLS"
        elif not np.isnan(gap_raw) and abs(gap_raw) >= 0.02:
            verd = "CONTROLLED_AWAY"
        else:
            verd = "LEVEL_SUFFICIENT"
        rows.append({"patch": p, "gap_raw_rising_minus_falling": gap_raw,
                     "gap_controlled": gap_ctl, "gap_residual": gap_res,
                     "p_value": pval, "n_rising": int(np.sum(direc == "rising")),
                     "n_falling": int(np.sum(direc == "falling")), "verdict": verd})
    W("17_GLOBAL_HYSTERESIS_RECHECK.csv")(pd.DataFrame(rows).round(4))

# ================================================================ 18 MEMORY VARIABLES
def memory_variables():
    fc = forcing_series.to_numpy()
    n = len(fc)
    d1 = np.full(n, np.nan); d1[1:] = fc[1:] - fc[:-1]
    d2 = np.full(n, np.nan); d2[2:] = fc[2:] - 2 * fc[1:-1] + fc[:-2]
    w30 = pd.Series(fc).rolling(30, min_periods=10).max().to_numpy()
    dd30 = np.where(np.isfinite(w30), w30 - fc, np.nan)
    cum30 = pd.Series(d1).rolling(30, min_periods=10).sum().to_numpy()
    thr75 = np.nanquantile(fc, 0.75)
    above = (fc > thr75).astype(float); above[np.isnan(fc)] = np.nan
    t_above = pd.Series(above).rolling(90, min_periods=10).sum().to_numpy()
    t_since_breach = np.full(n, np.nan)
    last_breach = -1
    for t in range(n):
        if np.isfinite(above[t]):
            if above[t] == 1:
                last_breach = t
            t_since_breach[t] = t - last_breach if last_breach >= 0 else np.nan
    t_since_peak = np.full(n, np.nan)
    last_peak = -1
    for t in range(n):
        if np.isfinite(w30[t]):
            if np.isfinite(fc[t]) and np.isclose(fc[t], w30[t]) and w30[t] > np.nanmean(w30) - 5 * np.nanstd(w30):
                last_peak = t
            t_since_peak[t] = t - last_peak if last_peak >= 0 else np.nan
    cross90 = np.full(n, np.nan)
    prev = np.nan
    cnt = 0
    for t in range(n):
        if not np.isfinite(fc[t]):
            continue
        cur = fc[t] > thr75
        if np.isfinite(prev) and cur != prev:
            cnt += 1
        prev = cur
        if t >= 89 and np.isfinite(fc[t - 89]):
            cross90[t] = cnt
    mem = {"forcing_level": fc, "forcing_slope": d1, "forcing_accel": d2,
           "recent_max30": w30, "drawdown30": dd30, "cum_load30": cum30,
           "time_above_90d": t_above, "time_since_breach": t_since_breach,
           "time_since_peak": t_since_peak, "crossings_90d": cross90}
    base_cols = ["forcing_level", "forcing_slope", "forcing_accel"]
    rows = []
    for p in DEPTH_ORDER:
        y = act[p].to_numpy()
        Xb = np.column_stack([mem[c] for c in base_cols])
        rec = {"patch": p}
        for name, v in mem.items():
            if name in base_cols:
                continue
            X = np.column_stack([Xb, v])
            m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
            if m.sum() < 200:
                rec[name + "_dR2"] = np.nan; continue
            split = int(m.sum() * 0.8)
            idx = np.where(m)[0]
            itr, ite = idx[:split], idx[split:]
            r2 = lambda Xt, ii: max(0.0, 1 - np.sum((y[ii] - LinearRegression().fit(Xt, y[ii]).predict(Xt)) ** 2)
                                    / max(np.sum((y[ii] - y[ii].mean()) ** 2), 1e-12))
            r2b_tr = r2(Xb[itr], itr); r2b_te = r2(Xb[ite], ite)
            r2m_tr = r2(X[itr], itr); r2m_te = r2(X[ite], ite)
            rec[name + "_dR2_test"] = float(r2m_te - r2b_te)
            rec[name + "_dR2_train"] = float(r2m_tr - r2b_tr)
        rows.append(rec)
    dfm = pd.DataFrame(rows)
    inc = [c for c in dfm.columns if c.endswith("_dR2_test") and not np.isnan(dfm[c]).all()]
    if inc:
        dfm["best_memory_var"] = dfm[inc].idxmax(axis=1).str.replace("_dR2_test", "")
        dfm["best_dR2"] = dfm[inc].max(axis=1)
        dfm["memory_verdict"] = np.where(dfm["best_dR2"] >= 0.01, "PATH_HISTORY_EARNED",
                                  np.where(dfm["best_dR2"] >= 0.003, "STATE_LOCAL_MEMORY", "LEVEL_SUFFICIENT"))
    W("18_MEMORY_VARIABLES.csv")(dfm.round(4))

# ================================================================ 19 MEMORY KERNEL PILOT
def memory_kernel_pilot():
    fc = forcing_series.to_numpy()
    n = len(fc)
    def kern_series(weights, horizon=90):
        out = np.zeros(n)
        wsum = np.sum(weights)
        L = min(len(weights), horizon, n - 1)
        for i in range(1, L + 1):
            out[i:] += fc[:n - i] * weights[i - 1]
        out /= wsum
        out[~np.isfinite(fc)] = np.nan
        return out
    kernels = {}
    for tau in (5, 10, 20, 40):
        kernels[f"exp_tau{tau}"] = np.exp(-np.arange(90) / tau)
    for alpha in (0.5, 1.0):
        kernels[f"power_a{alpha}"] = np.power(np.arange(90, 0, -1), -alpha)
    for w in (10, 30, 60):
        kernels[f"flat_w{w}"] = np.ones(w)
    rows = []
    for p in DEPTH_ORDER:
        y = act[p].to_numpy()
        m0 = np.isfinite(y) & np.isfinite(fc)
        r_level = float(spearmanr(fc[m0], y[m0]).statistic)
        best = None; best_r = -2
        for kname, w in kernels.items():
            ks = kern_series(w)
            mk = m0 & np.isfinite(ks)
            if mk.sum() < 100:
                continue
            r = float(spearmanr(ks[mk], y[mk]).statistic)
            if r > best_r:
                best_r = r; best = kname
        halflife = np.nan
        if best is not None and best.startswith("exp_tau"):
            halflife = float(int(best.split("tau")[1]) * np.log(2))
        rows.append({"patch": p, "corr_level": r_level, "best_kernel": best,
                     "best_corr": best_r if best else np.nan,
                     "kernel_gain_over_level": (best_r - r_level) if best else np.nan,
                     "exp_halflife_days": halflife})
    dfk = pd.DataFrame(rows)
    dfk["kernel_verdict"] = np.where(dfk["kernel_gain_over_level"] >= 0.02,
                                     "MEMORY_KERNEL_EARNED",
                                     np.where(dfk["kernel_gain_over_level"] >= 0.005,
                                              "WEAK_KERNEL_SUPPORT", "LEVEL_SUFFICIENT"))
    W("19_MEMORY_KERNEL_PILOT.csv")(dfk.round(4))
# ================================================================ 20-22 BIRTH VIABILITY
_M17 = Path(__file__).resolve().parent.parent.parent / "mech_17"
CAP17 = pd.read_csv(_M17 / "06_CAPACITY_MAP.csv")
TE17 = pd.read_csv(_M17 / "10_TRANSFER_EFFICIENCY.csv")
_cap_map = CAP17.loc[CAP17["surface"] == "6CELL"].set_index("cell")["capacity_ceiling"]
_te_map = TE17.set_index(["subperiod", "state_6cell"])["eff_prop_per_forcing"]
cap_arr = np.array([_cap_map.get(s, np.nan) for s in g6])
te_arr = np.array([_te_map.get((sp, st), np.nan) for sp, st in zip(subp_arr.astype(str), g6.astype(str))])
fc_arr = forcing_series.to_numpy()
ddem = np.full(len(demand_arr), np.nan); ddem[1:] = np.diff(demand_arr)
thr50_sp = THR50_TABLE.groupby("subperiod")["thr50"].mean()
thr_pos = np.array([fc_arr[t] / thr50_sp.get(str(subp_arr[t]), np.nan) for t in range(len(fc_arr))])
FEAT18 = {"demand": demand_arr, "demand_slope": ddem, "breadth": pos_share,
          "dispersion": disp7, "forcing": fc_arr, "concentration": conc,
          "rank_depth": rankd, "exit_entropy": ent6, "exit_p1": p16,
          "capacity_ceiling": cap_arr, "transfer_eff": te_arr, "thr_position": thr_pos}
STAGES18 = ["PRECONDITION", "INITIATION", "COMMITMENT", "EARLY_SURVIVAL"]
prev_ = np.array([None] + list(g6[:-1]))
bp = np.where(g6 != prev_)[0]
bp = bp[bp >= 8]; bp = bp[bp < len(dfc) - 8]
ab, vi = [], []
for i in bp:
    (ab if (g6[i + 1:i + 8] == prev_[i]).any() else vi).append(i)
ab, vi = np.array(ab), np.array(vi)

def _stage_vals(ixs, fname, stage):
    arr = FEAT18[fname]
    if stage == "PRECONDITION":
        return np.array([np.nanmean(arr[i - 7:i]) for i in ixs])
    if stage == "INITIATION":
        return arr[ixs]
    if stage == "COMMITMENT":
        return np.array([np.nanmean(arr[i + 1:i + 4]) for i in ixs])
    return np.array([np.nanmean(arr[i + 4:i + 8]) for i in ixs])

def birth_viability_map():
    rows = []
    for s in STAGES18:
        for f in FEAT18:
            vv = _stage_vals(vi, f, s); av = _stage_vals(ab, f, s)
            vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
            if len(vv) < 15 or len(av) < 15:
                rows.append(dict(stage=s, feature=f, n_viable=len(vv), n_aborted=len(av), verdict="DATA_LIMITED"))
                continue
            d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
            p = float(ranksums(vv, av).pvalue)
            rows.append(dict(stage=s, feature=f, n_viable=len(vv), n_aborted=len(av),
                             viable_mean=round(float(np.mean(vv)), 4),
                             viable_p25=round(float(np.quantile(vv, 0.25)), 4),
                             viable_p75=round(float(np.quantile(vv, 0.75)), 4),
                             aborted_mean=round(float(np.mean(av)), 4),
                             cohens_d=round(float(d), 3), p_value=round(p, 4),
                             verdict="SEPARATES" if d >= 0.35 and p < 0.05 else "NO_SEPARATION"))
    W("20_BIRTH_VIABILITY_MAP.csv")(pd.DataFrame(rows).round(4))

def viability_boundaries():
    bands = {}
    for s in STAGES18:
        for f in FEAT18:
            vv = _stage_vals(vi, f, s); vv = vv[~np.isnan(vv)]
            if len(vv) < 15:
                continue
            bands[(s, f)] = (np.quantile(vv, 0.25), np.quantile(vv, 0.75))
    leave_rows = {f: 0 for f in FEAT18}
    stage_leaves = {s: 0 for s in STAGES18}
    first_out = 0; n_ab = 0
    for i in ab:
        n_ab += 1
        found = None
        for s in STAGES18:
            for f in FEAT18:
                if (s, f) not in bands:
                    continue
                v = _stage_vals(np.array([i]), f, s)[0]
                if not np.isfinite(v):
                    continue
                lo, hi = bands[(s, f)]
                if v < lo or v > hi:
                    if found is None:
                        found = (s, f)
                    leave_rows[f] += 1
                    break
            if found is not None:
                stage_leaves[found[0]] += 1
                break
        if found is not None:
            first_out += 1
    reentry = 0
    for i in ab:
        if (g6[i + 1:i + 61] != prev_[i]).any():
            reentry += 1
    rows = [dict(measure="first_coordinate_leaves_band", n_aborted=n_ab,
                 n_with_first_leave=first_out,
                 frac=round(first_out / max(n_ab, 1), 3))]
    for s in STAGES18:
        rows.append(dict(measure=f"first_leave_at_{s}", n_aborted=n_ab,
                         n_with_first_leave=stage_leaves[s],
                         frac=round(stage_leaves[s] / max(n_ab, 1), 3)))
    for f, c in leave_rows.items():
        rows.append(dict(measure=f"first_leaver_coordinate_{f}", n_aborted=n_ab,
                         n_with_first_leave=c, frac=round(c / max(n_ab, 1), 3)))
    rows.append(dict(measure="aborted_reentry_within_60d", n_aborted=n_ab,
                     n_with_first_leave=reentry, frac=round(reentry / max(n_ab, 1), 3)))
    W("21_VIABILITY_BOUNDARIES.csv")(pd.DataFrame(rows).round(3))

def aborted_formation_mechanism():
    rows = []
    for f in ("demand", "exit_entropy", "transfer_eff", "thr_position", "capacity_ceiling", "exit_p1"):
        vv = _stage_vals(vi, f, "INITIATION"); av = _stage_vals(ab, f, "INITIATION")
        vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
        if len(vv) < 15 or len(av) < 15:
            continue
        d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
        p = float(ranksums(vv, av).pvalue)
        rows.append(dict(coordinate=f, viable_mean=round(float(np.mean(vv)), 4),
                         aborted_mean=round(float(np.mean(av)), 4),
                         cohens_d=round(float(d), 3), p_value=round(p, 4),
                         direction="aborted_higher" if np.mean(av) > np.mean(vv) else "aborted_lower"))
    # demand rising vs saturated at initiation
    dsl_vi = _stage_vals(vi, "demand_slope", "INITIATION"); dsl_ab = _stage_vals(ab, "demand_slope", "INITIATION")
    for grp, name, sl in ((vi, "VIABLE", dsl_vi), (ab, "ABORTED", dsl_ab)):
        sl = sl[~np.isnan(sl)]
        if len(sl) < 15:
            continue
        rows.append(dict(coordinate=f"demand_direction_{name}",
                         viable_mean=round(float(np.mean(sl)), 4),
                         frac_rising=round(float(np.mean(sl > 0)), 3),
                         frac_saturated=np.nan, cohens_d=np.nan, p_value=np.nan))
    # post-abort destination
    post = pd.Series(g6[np.concatenate([ab + t for t in (1, 2, 3)])]).value_counts(normalize=True)
    for st, sh in post.head(6).items():
        rows.append(dict(coordinate=f"post_abort_state_{st}", viable_mean=np.nan,
                         aborted_mean=round(float(sh), 3), cohens_d=np.nan, p_value=np.nan))
    W("22_ABORTED_FORMATION_MECHANISM.csv")(pd.DataFrame(rows).round(4))
# ================================================================ 23 POTENTIAL->REALIZATION
def potential_realization_reconstruction():
    prop = prop7; ren = ren7; rec = rank7
    util = demand_arr / np.where(cap_arr > 0, cap_arr, np.nan)
    rows = []
    links = [("demand_to_capacity", demand_arr, cap_arr),
             ("capacity_to_threshold", cap_arr, thr_pos),
             ("threshold_to_exit_pressure", thr_pos, p16),
             ("exit_pressure_to_transfer", p16, te_arr),
             ("transfer_to_propagation", te_arr, prop)]
    prev_el = None
    for name, a, b in links:
        m = np.isfinite(a) & np.isfinite(b)
        rho = _rho(a[m], b[m])
        pr = np.nan
        if prev_el is not None:
            m2 = np.isfinite(a) & np.isfinite(b) & np.isfinite(prev_el)
            if m2.sum() >= 60:
                pr = _partial_rho(a[m2], b[m2], prev_el[m2])[0]
        rows.append(dict(link=name, n=int(m.sum()),
                         rho=round(rho, 3) if rho is not None else np.nan,
                         partial_rho_ctrl_prev=round(pr, 3) if pr is not None else np.nan,
                         verdict="SUPPORTED" if (rho is not None and abs(rho) > 0.15) else "WEAK"))
        prev_el = b
    base_prop = float(np.nanmean(prop))
    q67 = lambda a: np.nanquantile(a, 0.67); q33 = lambda a: np.nanquantile(a, 0.33)
    d_hi = demand_arr >= q67(demand_arr); te_lo = te_arr <= q33(te_arr)
    ent_hi = ent6 >= q67(ent6); p1_hi = p16 >= q67(p16)
    rec_lo = rec <= q33(rec); sat_hi = field_act >= np.nanquantile(field_act, 0.8)
    thr_hi = thr_pos >= q67(thr_pos); util_hi = util >= q67(util)
    motifs = [("HIGH_DEMAND_LOW_TRANSFER", d_hi & te_lo),
              ("HIGH_DEMAND_OPEN_EXITS", d_hi & ent_hi),
              ("THRESHOLD_CROSSED_NO_RECRUITMENT", thr_hi & rec_lo),
              ("CAPACITY_AVAILABLE_NO_COMMITMENT", util_hi & d_hi),
              ("EXIT_CONCENTRATION_WITH_PROPAGATION", p1_hi & (prop >= np.nanquantile(prop, 0.67))),
              ("SATURATION_WITHOUT_DELIVERY", sat_hi & (prop <= q33(prop)))]
    for name, mask in motifs:
        m = mask & np.isfinite(prop) & np.isfinite(ren) & np.isfinite(rec)
        if m.sum() < 30:
            continue
        rows.append(dict(link=f"motif_{name}", n=int(m.sum()),
                         rho=round(float(np.nanmean(prop[m]) - base_prop), 4),
                         partial_rho_ctrl_prev=round(float(np.nanmean(ren[m])), 4),
                         verdict="SUPPORTED" if abs(np.nanmean(prop[m]) - base_prop) > 0.05 else "WEAK"))
    W("23_POTENTIAL_REALIZATION_RECONSTRUCTION.csv")(pd.DataFrame(rows).round(4))

# ================================================================ 24 POTENTIAL->REALIZATION HIERARCHY
def potential_realization_hierarchy():
    Xnames = ["demand", "thr_position", "exit_entropy", "exit_p1", "transfer_eff"]
    X = np.column_stack([demand_arr, thr_pos, ent6, p16, te_arr])
    rows = []
    for st in sorted(set(g6)):
        m = (g6 == st) & np.all(np.isfinite(X), axis=1) & np.isfinite(prop7)
        if m.sum() < 60:
            continue
        Xs = (X[m] - X[m].mean(0)) / X[m].std(0)
        ys = (prop7[m] - prop7[m].mean()) / prop7[m].std()
        beta = LinearRegression().fit(Xs, ys).coef_
        rec = {"state": st, "n": int(m.sum())}
        for n_, b in zip(Xnames, beta):
            rec[f"beta_{n_}"] = round(float(b), 3)
        rec["n_active_links"] = int(np.sum(np.abs(beta) >= 0.1))
        rec["dominant_link"] = Xnames[int(np.argmax(np.abs(beta)))]
        rows.append(rec)
    df24 = pd.DataFrame(rows)
    act_ = df24["n_active_links"]
    if len(df24) and act_.median() >= 3:
        verd = "PARALLEL_CONSTRAINTS"
    elif len(df24) and act_.median() == 1:
        verd = "SEQUENTIAL_DEPENDENCY"
    elif len(df24) and act_.std() >= 0.9:
        verd = "STATE_LOCAL_PATHS"
    elif len(df24):
        verd = "PARTIAL_ORDER"
    else:
        verd = "DATA_LIMITED"
    df24["hierarchy_verdict"] = verd
    W("24_POTENTIAL_REALIZATION_HIERARCHY.csv")(df24.round(4))
# ================================================================ 2022 EVENT MACHINERY
RESP_NAMES = ["FIELD"] + DEPTH_ORDER

def _rolling_node_series(win=180, step=30):
    """Rolling logistic response nodes per patch, asof-filled to daily."""
    dates = pd.to_datetime(dfc["d"])
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
            ceil, x0, k, _, _ = logistic_params(xw[m2], yw[m2])
            rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = k, ceil, x0
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dates)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])

def _event_machinery():
    n = len(dfc); dates = pd.to_datetime(dfc["d"])
    nodes = _rolling_node_series()
    cols = {}
    for p in RESP_NAMES:
        cols[f"slope_{p}"] = nodes[f"{p}_k"].to_numpy()
        cols[f"ceiling_{p}"] = nodes[f"{p}_ceiling"].to_numpy()
        cols[f"onset_{p}"] = nodes[f"{p}_x0"].to_numpy()
    for p in ["FIELD"] + DEPTH_ORDER:
        cols.pop(f"ceiling_{p}" if p != "FIELD" else None, None) if False else None
    # keep FIELD nodes + patch means for compactness
    vdict = {"slope_FIELD": cols["slope_FIELD"], "ceiling_FIELD": cols["ceiling_FIELD"],
             "onset_FIELD": cols["onset_FIELD"],
             "slope_patch_mean": np.nanmean([cols[f"slope_{p}"] for p in DEPTH_ORDER], axis=0),
             "ceiling_patch_mean": np.nanmean([cols[f"ceiling_{p}"] for p in DEPTH_ORDER], axis=0),
             "onset_patch_mean": np.nanmean([cols[f"onset_{p}"] for p in DEPTH_ORDER], axis=0),
             "exit_entropy": ent6, "exit_p1": p16, "recruitment": rank7,
             "demand": demand_arr, "propagation": prop7, "reentry": ren7,
             "volatility": vol_med, "breadth": pos_share}
    Z = {}
    for name, v in vdict.items():
        v = np.asarray(v, dtype=float)
        m = pd.Series(v).rolling(30, min_periods=15).mean().to_numpy()
        med = np.nanmedian(m); mad = np.nanmedian(np.abs(m - med)) * 1.4826
        Z[name] = (m - med) / max(mad, 1e-9)
    Zdf = pd.DataFrame(Z)
    S = np.sqrt((Zdf ** 2).mean(axis=1)).to_numpy()
    n_dev = (np.abs(Zdf.to_numpy()) > 3).sum(axis=1)
    # hypothesis window: MECH-17 found 2022-02..2022-04; allow data to date it
    win_lo = np.datetime64("2021-11-01"); win_hi = np.datetime64("2023-06-30")
    in_block = (n_dev >= 4) & (dates >= win_lo) & (dates <= win_hi)
    blocks = []; i = 0
    while i < n:
        if in_block[i]:
            j = i
            while j < n and in_block[j]:
                j += 1
            if (j - i) >= 10:
                blocks.append((i, j - 1))
            i = j
        else:
            i += 1
    best = None
    for (a, b) in blocks:
        ms = float(np.nanmean(S[a:b + 1]))
        if best is None or ms > best[0]:
            best = (ms, a, b)
    out = dict(Zdf=Zdf, S=S, n_dev=n_dev, dates=dates, blocks=blocks, best=best)
    if best is None:
        out["verdict"] = "NO_EVENT_BLOCK_FOUND"
        return out
    _, a, b = best
    t0 = a
    while t0 > 0 and n_dev[t0 - 1] >= 3 and dates[t0 - 1] >= win_lo:
        t0 -= 1
    peak = int(np.nanargmax(S[a:b + 1])) + a
    ev_mask = np.ones(n, dtype=bool); ev_mask[a:b + 1] = False
    S_base = np.nanmedian(S[ev_mask]); S_mad = np.nanmedian(np.abs(S[ev_mask] - S_base)) * 1.4826
    def first_sustained(cond, dur, start):
        for t in range(start, n - dur):
            if np.all(cond(t, dur)):
                return t
        return None
    snap = {}
    for dur in (14, 30, 60):
        t = first_sustained(lambda tt, d=dur: (n_dev[tt:tt + d] <= 1) & (S[tt:tt + d] <= S_base + 3 * S_mad), dur, peak + 1)
        snap[dur] = t
    snap_base = snap[14]
    norm = first_sustained(lambda tt, _d: n_dev[tt:tt + 14] <= 2, 14, peak + 1)
    early = int(np.where(S[peak:] < 0.5 * S[peak])[0][0]) + peak if np.any(S[peak:] < 0.5 * S[peak]) else None
    out.update(dict(t0=t0, a=a, b=b, peak=peak, S_base=S_base, S_mad=S_mad,
                    snap=snap, snap_base=snap_base, norm=norm, early=early,
                    verdict="EVENT_DETECTED",
                    onset_date=str(dates[t0].date()), peak_date=str(dates[peak].date()),
                    break_date=str(dates[a].date()),
                    snap14_date=str(dates[snap[14]].date()) if snap[14] else None,
                    snap30_date=str(dates[snap[30]].date()) if snap[30] else None,
                    snap60_date=str(dates[snap[60]].date()) if snap[60] else None))
    return out

E2022 = _event_machinery()

def event_boundaries():
    rows = []
    d = E2022["dates"]
    rows.append(dict(stage="PRE_EVENT", date=str(d[0].date()), n_deviating=int(E2022["n_dev"][0])))
    if E2022["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("25_2022_EVENT_BOUNDARIES.csv")(pd.DataFrame([dict(stage="NONE", verdict=E2022["verdict"])]))
        return
    for stage, idx in [("DEVIATION_ONSET", E2022["t0"]), ("BREAK_CONFIRMATION", E2022["a"]),
                       ("PEAK_DISTORTION", E2022["peak"]), ("EARLY_RECOVERY", E2022["early"]),
                       ("SHAPE_NORMALIZATION", E2022["norm"]), ("FULL_SNAPBACK_14D", E2022["snap_base"])]:
        if idx is None:
            rows.append(dict(stage=stage, date=None, n_deviating=np.nan))
            continue
        rows.append(dict(stage=stage, date=str(d[idx].date()),
                         n_deviating=int(E2022["n_dev"][idx]),
                         deviation_index=round(float(E2022["S"][idx]), 3)))
    rows.append(dict(stage="RESIDUAL_PERIOD_START", date=str(d[E2022["snap_base"]].date()) if E2022["snap_base"] else None,
                     n_deviating=int(E2022["n_dev"][E2022["snap_base"]]) if E2022["snap_base"] else np.nan))
    W("25_2022_EVENT_BOUNDARIES.csv")(pd.DataFrame(rows).round(3))

def snapback_definition():
    d = E2022["dates"]
    if E2022["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("26_2022_SNAPBACK.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    rows = []
    for dur in (14, 30, 60):
        t = E2022["snap"][dur]
        rows.append(dict(persistence_window_days=dur,
                         snapback_date=str(d[t].date()) if t is not None else None,
                         days_after_peak=(t - E2022["peak"]) if t is not None else None,
                         sensitivity="STABLE" if (t is not None and abs((t or 0) - (E2022["snap_base"] or 0)) <= 30) else "SENSITIVE"))
    W("26_2022_SNAPBACK.csv")(pd.DataFrame(rows).round(3))

def variable_strip():
    d = E2022["dates"]; Zdf = E2022["Zdf"]; n = len(d)
    rows = []
    if E2022["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("27_2022_VARIABLE_STRIP.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    t0, peak, sb = E2022["t0"], E2022["peak"], E2022["snap_base"]
    for name in Zdf.columns:
        z = Zdf[name].to_numpy()
        absz = np.abs(z)
        in_ev = np.zeros(n, dtype=bool); in_ev[t0:sb + 1 if sb else peak + 1] = True
        m_ev = in_ev & np.isfinite(absz)
        if m_ev.sum() == 0:
            rows.append(dict(variable=name, onset_date=None, peak_date=None, peak_dev=np.nan))
            continue
        onset = int(np.where(m_ev & (absz > 3))[0][0]) if np.any(m_ev & (absz > 3)) else int(np.where(m_ev)[0][0])
        pk = int(np.nanargmax(absz[m_ev])) + int(np.where(m_ev)[0][0])
        first_norm = None
        for t in range(pk + 1, n):
            if absz[t] <= 3:
                first_norm = t; break
        sust_norm = None
        for t in range(pk + 1, n - 14):
            if np.all(absz[t:t + 14] <= 3):
                sust_norm = t; break
        post = absz[sb + 1:min(sb + 121, n)] if sb else absz[peak + 1:peak + 121]
        rows.append(dict(variable=name,
                         onset_date=str(d[onset].date()),
                         peak_date=str(d[pk].date()),
                         peak_dev=round(float(absz[pk]), 3),
                         first_normalization=str(d[first_norm].date()) if first_norm else None,
                         sustained_normalization=str(d[sust_norm].date()) if sust_norm else None,
                         post_event_max_absz=round(float(np.nanmax(post)), 3) if len(post) else np.nan,
                         residue_overshoot=round(float(np.nanmax(post) - 3), 3) if len(post) and np.nanmax(post) > 3 else 0.0))
    W("27_2022_VARIABLE_STRIP.csv")(pd.DataFrame(rows).round(3))

def end_mechanism():
    d = E2022["dates"]; Zdf = E2022["Zdf"]
    if E2022["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("28_2022_END_MECHANISM.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    sb = E2022["snap_base"]; peak = E2022["peak"]
    rows = []
    for name in Zdf.columns:
        absz = np.abs(Zdf[name].to_numpy())
        fn = None
        for t in range(peak + 1, sb + 1 if sb else len(absz)):
            if absz[t] <= 3:
                fn = t; break
        if fn is None:
            rel = "LAGGED_OR_NEVER"; days_before_snapback = np.nan
        else:
            days_before_snapback = (sb - fn) if sb else np.nan
            rel = "PRECEDED" if days_before_snapback > 30 else ("COINCIDED" if (sb is not None and days_before_snapback >= -14) else "LAGGED")
        rows.append(dict(variable=name,
                         first_normalization_date=str(d[fn].date()) if fn is not None else None,
                         days_before_snapback=days_before_snapback,
                         relation=rel))
    W("28_2022_END_MECHANISM.csv")(pd.DataFrame(rows).round(3))

def residue_check():
    d = E2022["dates"]; Zdf = E2022["Zdf"]
    if E2022["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("29_2022_RESIDUE.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    sb = E2022["snap_base"]; n = len(d)
    pre = np.ones(n, dtype=bool); pre[:E2022["t0"]] = True
    post = np.zeros(n, dtype=bool); post[sb + 1:min(sb + 121, n)] = True
    rows = []
    for name in Zdf.columns:
        absz = np.abs(Zdf[name].to_numpy())
        bp = np.nanmedian(absz[pre]); bm = np.nanmedian(np.abs(absz[pre] - bp)) * 1.4826
        pv = absz[post]
        if len(pv) == 0:
            rows.append(dict(variable=name, verdict="DATA_LIMITED")); continue
        resid = float(np.nanmean(pv) - bp)
        any_breach = bool(np.nanmax(pv) > 3)
        rows.append(dict(variable=name,
                         pre_event_mean_absz=round(float(bp), 3),
                         post_event_mean_absz=round(float(np.nanmean(pv)), 3),
                         residue_mean_absz=round(resid, 3),
                         post_max_absz=round(float(np.nanmax(pv)), 3),
                         any_post_breach=any_breach,
                         verdict="RESIDUE" if (resid > max(bm * 1.5, 0.5) or any_breach) else "NO_RESIDUE"))
    W("29_2022_RESIDUE.csv")(pd.DataFrame(rows).round(3))
# ================================================================ 30 REGIME/ROUTE LAW TABLE
def regime_route_law_table():
    et = edge_table(dfc, "grp6", "grp6_next", demand=demand_arr,
                    forcing_series=fc_arr, entropy_series=ent6)
    rsf = pd.read_csv(OUT / "10_ROUTE_SPECIFIC_FORCING.csv")
    rf = pd.read_csv(OUT / "13_RESPONSE_FINGERPRINTS.csv")
    hy = pd.read_csv(OUT / "17_GLOBAL_HYSTERESIS_RECHECK.csv")
    g = pd.Series(g6); gn = pd.Series(g6n)
    st_cap = pd.Series(cap_arr).groupby(g).mean()
    st_p1 = pd.Series(p16).groupby(g).mean()
    st_ent = pd.Series(ent6).groupby(g).mean()
    st_te = pd.Series(te_arr).groupby(g).mean()
    fp_ceil = rf.groupby("response")["ceiling"].mean().to_dict() if "ceiling" in rf.columns else {}
    fp_slope = rf.groupby("response")["slope_k"].mean().to_dict() if "slope_k" in rf.columns else {}
    rows = []
    for _, r in et.iterrows():
        s, t = r["from_state"], r["to_state"]
        key = f"{s}->{t}"
        f6 = rsf[(rsf["edge"] == key) & (rsf["resolution"] == "6CELL")]
        f6 = f6.reindex(f6["rho"].abs().sort_values(ascending=False).index) if len(f6) else f6
        top = f6.iloc[0] if len(f6) else None
        top2 = f6.iloc[1] if len(f6) > 1 else None
        sp_probs = []
        for sp in SUBPERIODS:
            m = (g.to_numpy() == s) & (subp_arr == sp)
            if int(m.sum()) >= 20:
                sp_probs.append(float((gn.to_numpy()[m] == t).mean()))
        reg_mod = float(np.std(sp_probs)) if len(sp_probs) >= 3 else np.nan
        rows.append(dict(route=key, from_state=s, to_state=t,
                         edge_class=r["edge_class"], n=int(r["n"]),
                         prob=round(float(r["prob"]), 4),
                         median_days_to_exit=r["median_days_to_exit"],
                         prob_demand_lo=r["prob_demand_lo"], prob_demand_hi=r["prob_demand_hi"],
                         prob_rising=r["prob_rising"], prob_falling=r["prob_falling"],
                         prob_ent_lo=r["prob_ent_lo"], prob_ent_hi=r["prob_ent_hi"],
                         top_forcing_family=top["forcing_family"] if top is not None else None,
                         top_family_rho=round(float(top["rho"]), 3) if top is not None else np.nan,
                         second_forcing_family=top2["forcing_family"] if top2 is not None else None,
                         thr50_mean=round(float(thr50_sp.mean()), 3),
                         thr50_regime_range=round(float(thr50_sp.max() - thr50_sp.min()), 3),
                         hysteresis_gap_mean=round(float(hy["gap_controlled"].mean()), 3) if "gap_controlled" in hy else np.nan,
                         exit_p1_mean=round(float(st_p1.get(s, np.nan)), 3),
                         exit_entropy_mean=round(float(st_ent.get(s, np.nan)), 3),
                         capacity_ceiling=round(float(st_cap.get(s, np.nan)), 3),
                         transfer_eff_mean=round(float(st_te.get(s, np.nan)), 3),
                         resp_ceiling_patch_mean=round(float(np.nanmean(list(fp_ceil.values()))), 3),
                         resp_slope_patch_mean=round(float(np.nanmean(list(fp_slope.values()))), 3),
                         regime_modulation_std=round(reg_mod, 3) if reg_mod == reg_mod else np.nan))
    return pd.DataFrame(rows)

W30 = W("30_REGIME_ROUTE_LAW_TABLE.csv", index=False)

# ================================================================ 31 PROMOTE / MERGE / DISSOLVE
def promote_merge_dissolve():
    rows = []
    def add(obj, source, vcol, role, action, note=""):
        try:
            d = pd.read_csv(OUT / source)
        except FileNotFoundError:
            d = pd.DataFrame()
        vs = d[vcol].dropna().unique().tolist() if vcol in d.columns else []
        rows.append(dict(object=obj, source=source, empirical_verdicts=";".join(map(str, vs[:4])),
                         n_rows=len(d), os_role=role, action=action, note=note))
    add("TRAFFIC_DEMAND", "20_BIRTH_VIABILITY_MAP.csv", "verdict", "STRUCTURAL_CORE", "PROMOTE", "MECH-17 earned; viability coordinate")
    add("CAPACITY", "02_EDGE_REGISTRY.csv", "prob", "ADAPTIVE_LAW", "PROMOTE", "state-local ceiling (0.51-1.10)")
    add("CONGESTION", "23_POTENTIAL_REALIZATION_RECONSTRUCTION.csv", "verdict", "LOCAL_PHYSICS", "LOCAL", "weak but real")
    add("EXIT_PRESSURE", "04_EXIT_AVAILABILITY_PRESSURE.csv", "resolution_driver", "ADAPTIVE_LAW", "PROMOTE", "branch geometry")
    add("TRANSFER_EFFICIENCY", "24_POTENTIAL_REALIZATION_HIERARCHY.csv", "dominant_link", "LOCAL_PHYSICS", "LOCAL", "state-local")
    add("SATURATION_LAW", "14_SATURATION_DATA_COLLAPSE.csv", "verdict", "ADAPTIVE_LAW", "PROMOTE", "shape stable, nodes drift")
    add("THRESHOLD_BAND", "12_THRESHOLD_HIERARCHY.csv", "verdict", "ADAPTIVE_LAW", "PROMOTE", "bands > points")
    add("COMPACT_FORCING_SCALAR", "08_FORCING_PRIMITIVES.csv", "verdict", "DISSOLVE", "DISSOLVE", "MECH-17 rejection")
    add("FORCING_FAMILIES", "09_FORCING_HIERARCHY.csv", "verdict", "ADAPTIVE_LAW", "PROMOTE", "multi-family")
    add("EDGE_LAWS", "02_EDGE_REGISTRY.csv", "edge_class", "STRUCTURAL_CORE", "PROMOTE", "MECH-18 registry")
    add("EDGE_LOCAL_CLOCKS", "03_EDGE_HAZARDS.csv", "verdict", "LOCAL_PHYSICS", "LOCAL", "edge-specific timing")
    add("ENTROPY_DECAY_RATE", "06_ENTROPY_DECAY.csv", "verdict", "ADAPTIVE_LAW", "LOCAL", "velocity adds info")
    add("ROUTE_DEFORMATION", "07_ROUTE_DEFORMATION.csv", "verdict", "ADAPTIVE_LAW", "LOCAL", "JS divergence")
    add("GLOBAL_HYSTERESIS", "17_GLOBAL_HYSTERESIS_RECHECK.csv", "verdict", "ADAPTIVE_LAW", "LOCAL", "parked candidate")
    add("MEMORY_KERNEL", "19_MEMORY_KERNEL_PILOT.csv", "kernel_verdict", "ADAPTIVE_LAW", "LOCAL", "horizon pilot")
    add("BIRTH_VIABILITY", "21_VIABILITY_BOUNDARIES.csv", "measure", "ADAPTIVE_LAW", "PROMOTE", "envelope geometry")
    add("POTENTIAL_REALIZATION", "24_POTENTIAL_REALIZATION_HIERARCHY.csv", "hierarchy_verdict", "ADAPTIVE_LAW", "LOCAL", "partial-order chain")
    add("2022_STRESS_EVENT", "25_2022_EVENT_BOUNDARIES.csv", "stage", "RESEARCH_ONLY", "LOCAL", "reserved archetype")
    W("31_PROMOTE_MERGE_DISSOLVE.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 32 NULL AND FAILED RESULTS
def null_failed_results():
    rows = []
    for f in sorted(OUT.glob("*.csv")):
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        na = int(d.isna().sum().sum()); total = int(d.size)
        flags = []
        for val in ("DATA_LIMITED", "NO_STABLE", "NO_EVENT_BLOCK_FOUND", "NULL",
                    "DATA_BLOCKED", "NO_RESIDUE", "LEVEL_SUFFICIENT", "WEAK"):
            for c in d.columns:
                nv = int((d[c].astype(str) == val).sum())
                if nv:
                    flags.append(f"{val}:{nv}")
        rows.append(dict(file=f.name, n_rows=len(d), n_cells=total, null_cells=na,
                         null_frac=round(na / max(total, 1), 3),
                         failed_flags=";".join(sorted(set(flags))[:6])))
    W("32_NULL_AND_FAILED_RESULTS.csv")(pd.DataFrame(rows))

# ================================================================ RUNNER
if __name__ == "__main__":
    response_dimensionality()
    saturation_node_dynamics()
    global_hysteresis_recheck()
    W30(regime_route_law_table())
    memory_variables()
    memory_kernel_pilot()
    birth_viability_map()
    viability_boundaries()
    aborted_formation_mechanism()
    potential_realization_reconstruction()
    potential_realization_hierarchy()
    event_boundaries()
    snapback_definition()
    variable_strip()
    end_mechanism()
    residue_check()
    promote_merge_dissolve()
    null_failed_results()
    print("MECH-18 BUILD COMPLETE")
