#!/usr/bin/env python
"""ALT_MECH_17 - TRAFFIC LAW CARTOGRAPHY orchestration.

Computes and writes mech_17 deliverable files 02..27. Narrative files
(01 prereg, 21 stress archetype, 27 field-model freeze map, 28 summary,
29 decision) are written alongside this script by the agent + this file's
auto-witnesses.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER).
No PnL, no strategy, no execution, no sizing, no direction signals.
"""
import os, pickle, sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m17base as B
from _m17base import (load_frame, load_band, forcing_families,
                      activation_surface, logistic_params, hill_params,
                      DEPTH_ORDER, SUBPERIODS, FINE2PATCH)

OUT = B.OUT
ROLL_SUB = {"2020-2021": "PRE", "2022": "MID", "2023": "POST"}

def W(df, name, index=False):
    df.to_csv(OUT / name, index=index)
    print(f"  wrote {name}  rows={len(df)}", flush=True)

def _rhs(df, gcol, metric, min_n=30):
    return B.M16.group_order_profile(df, gcol, metric, min_n=min_n)

def _chrono_rho(pair_vectors):
    pairs = 0; acc = []
    names = [p[0] for p in pair_vectors]
    for i in range(len(pair_vectors)-1):
        p1, p2 = pair_vectors[i][1], pair_vectors[i+1][1]
        # align on common keys
        ks = [k for k in p1 if k in p2]
        if len(ks) < 3: continue
        a = np.array([p1[k] for k in ks], dtype=float)
        b = np.array([p2[k] for k in ks], dtype=float)
        acc.append(float(spearmanr(a, b)[0])); pairs += 1
    return (float(np.mean(acc)) if acc else np.nan), pairs

print("=== MECH-17 build start ===", flush=True)
df = load_frame()
band = load_band()
fams = forcing_families(df)
act = activation_surface(band)
df["d"] = pd.to_datetime(df["d"])
act = act.reindex(df["d"].values)

# cache
with open(OUT/"cache_fams17.pkl","wb") as fh: pickle.dump(fams, fh)
with open(OUT/"cache_act17.pkl","wb") as fh: pickle.dump(act, fh)

fams_d = fams.set_index("d")
act_d = act

# also ensure grp surfaces present
for c in ["grp4s","grp6","grp8"]:
    if c not in df: df[c] = df["mcell"]

# ---------------------------------------------------------------- 02 ROAD FREEZE AUDIT
def road_freeze_audit():
    rows=[]
    surf_metric = {"grp4s":"TOPOLOGY_4STATE","grp6":"TOPOLOGY_6CELL","grp8":"TOPOLOGY_8CELL"}
    topo_metrics = {"self_transition": "self_transition", "modal_exit": "modal_exit",
                    "branch_entropy": "branch_entropy"}
    xfer_metrics = {"prop":"prop","ren":"ren","rank":"rank"}
    for gcol, sname in surf_metric.items():
        sub = df[df["subperiod"].isin(SUBPERIODS)]
        # topology ordering profile per subperiod (self-transition)
        topo_vecs=[]; xfer_vecs=[]
        for sp in SUBPERIODS:
            s = sub[sub["subperiod"]==sp]
            if len(s)<60: continue
            tv = _rhs(s, gcol, "self_transition")
            xv = _rhs(s, gcol, "prop")
            topo_vecs.append((sp,tv)); xfer_vecs.append((sp,xv))
        t_rho, t_n = _chrono_rho(topo_vecs)
        x_rho, x_n = _chrono_rho(xfer_vecs)
        rows.append({
            "surface": sname, "group_col": gcol, "topology_metric": "self_transition",
            "topology_chrono_rho": round(t_rho,3), "topology_pairs": t_n,
            "transfer_metric": "prop7", "transfer_chrono_rho": round(x_rho,3),
            "transfer_pairs": x_n, "verdict": "FREEZE_CANDIDATE" if np.nanmean([t_rho])>0.6 else "PARTIAL",
        })
    # spatial activation / local highway as invariants: report branch stability
    # local highways: modal exits per 6cell by half
    s = df[df["subperiod"].isin(SUBPERIODS)].copy(); s=s.sort_values("d").reset_index(drop=True)
    half=len(s)//2
    eh = _rhs(s.iloc[:half], "grp6", "modal_exit"); lh=_rhs(s.iloc[half:], "grp6", "modal_exit")
    mh_rho,_ = B.M16.rank_order_rho(eh,lh)
    rows.append({"surface":"LOCAL_HIGHWAYS_6CELL","group_col":"grp6","topology_metric":"modal_exit",
                 "topology_chrono_rho":round(mh_rho,3),"topology_pairs":len(set(eh)&set(lh)),
                 "transfer_metric":"n/a","transfer_chrono_rho":np.nan,"transfer_pairs":0,
                 "verdict":"INVARIANT_CANDIDATE" if mh_rho>0.6 else "PARTIAL"})
    return pd.DataFrame(rows)

W(road_freeze_audit(), "02_ROAD_SYSTEM_FREEZE_AUDIT.csv", index=False)

# ---------------------------------------------------------------- 03 TRAFFIC OBJECT DEFINITIONS
obj_defs = pd.DataFrame([
    dict(object="TRAFFIC_DEMAND", definition="daily composite of participation (breadth_vel, pos_ret_share), rank recruitment (rank_depth_rel), dispersion growth, spatial activation",
         inputs="breadth_vel,pos_ret_share,rank_depth_rel,top500_dispersion_7d,spatial_activation",
         pit_safe=True, response="none (state descriptor)",
         object_type="DEMAND", provisional="CANDIDATE"),
    dict(object="CAPACITY", definition="per-surface-cell response ceiling: logistic ceiling of field activation vs demand/forcing within the cell",
         inputs="activation(FIELD), demand, forcing", pit_safe=True, response="none",
         object_type="CAPACITY", provisional="CANDIDATE"),
    dict(object="CONGESTION", definition="standardized demand relative to cell capacity (demand/capacity ratio within state)",
         inputs="demand, capacity", pit_safe=True, response="none",
         object_type="CONGESTION", provisional="CANDIDATE"),
    dict(object="EXIT_PRESSURE", definition="branch structure of forward 6-cell exits: branch entropy, dominant share p1, k, concentration",
         inputs="grp6 next-7 window", pit_safe=True, response="none",
         object_type="EXIT", provisional="CANDIDATE"),
    dict(object="TRANSFER_EFFICIENCY", definition="realized propagation per unit demand/forcing (prop7/demand, incremental breadth/demand)",
         inputs="prop7, demand, forcing", pit_safe=True, response="prop7",
         object_type="EFFICIENCY", provisional="CANDIDATE"),
    dict(object="SATURATION_LAW", definition="per-patch activation-vs-forcing logistic half-sat x0, slope k, ceiling",
         inputs="act[patch], forcing", pit_safe=True, response="act[patch]",
         object_type="SATURATION", provisional="CANDIDATE"),
    dict(object="THRESHOLD_BAND", definition="forcing levels at P_act = 0.10/0.30/0.70/0.90 per patch -> DORMANT/LOW/TRANSITION/HIGH/SATURATED",
         inputs="pact[patch], forcing", pit_safe=True, response="pact[patch]",
         object_type="THRESHOLD", provisional="CANDIDATE"),
])
W(obj_defs, "03_TRAFFIC_OBJECT_DEFINITIONS.csv", index=False)


# ---------------------------------------------------------------- DEMAND + branch helpers
def build_demand():
    cols = ["breadth_vel","pos_ret_share","rank_depth_rel","top500_dispersion_7d","spatial_activation"]
    parts = []
    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce")
        sd = s.std()
        parts.append((s - s.mean())/sd if sd > 0 else s*0)
    d = sum(parts)/len(parts)
    sd = d.std()
    return (d - d.mean())/sd if sd > 0 else d*0

demand = build_demand()
with open(OUT/"cache_demand17.pkl","wb") as fh:
    pickle.dump(demand, fh)

def branch_metrics_series(seq):
    n = len(seq); out = []
    for i in range(n):
        w = seq.iloc[i+1:min(i+8, n)].dropna()
        curr = seq.iloc[i]
        if len(w) < 3:
            out.append(dict(k=np.nan, ent=np.nan, p1=np.nan, p2=np.nan, conc=np.nan,
                            stay_share=np.nan, exit_rate=np.nan)); continue
        stay = float((w == curr).mean())
        leaving = w[w != curr]
        if len(leaving) < 1:
            out.append(dict(k=0, ent=0.0, p1=0.0, p2=np.nan, conc=0.0,
                            stay_share=stay, exit_rate=1.0-stay)); continue
        vc = leaving.value_counts(normalize=True)
        k = len(vc)
        p = vc.to_numpy(dtype=float)
        ent = -float(np.sum(p*np.log2(p)))
        Hmax = float(np.log2(k))
        ps = np.sort(p)[::-1]
        out.append(dict(k=int(k), ent=ent, p1=float(ps[0]),
                        p2=float(ps[1]) if k > 1 else np.nan,
                        conc=1.0 - ent/Hmax if Hmax > 0 else np.nan,
                        stay_share=stay, exit_rate=1.0-stay))
    return pd.DataFrame(out, index=seq.index)

bm6 = branch_metrics_series(df["grp6"])
bm8 = branch_metrics_series(df["grp8"])
with open(OUT/"cache_bm6_17.pkl","wb") as fh: pickle.dump(bm6, fh)
with open(OUT/"cache_bm8_17.pkl","wb") as fh: pickle.dump(bm8, fh)

# ---------------------------------------------------------------- 04 FORCING VARIANT ATLAS
fam_cols = [c for c in fams.columns if c not in ("d","COMMON_FORCING")]
atlas = []
for c in fam_cols:
    v = pd.to_numeric(fams[c], errors="coerce")
    cf = pd.to_numeric(fams["COMMON_FORCING"], errors="coerce")
    ok = v.notna() & cf.notna()
    corr = float(spearmanr(v[ok], cf[ok])[0]) if ok.sum() > 50 else np.nan
    atlas.append(dict(family=c, mean=round(float(v.mean()),3), std=round(float(v.std()),3),
                      min=round(float(v.min()),2), max=round(float(v.max()),2),
                      spearman_vs_common=round(corr,3)))
W(pd.DataFrame(atlas), "04_FORCING_VARIANT_ATLAS.csv", index=False)

# ---------------------------------------------------------------- 05 FORCING COMPRESSION
def forcing_compression():
    X = fams[fam_cols].apply(pd.to_numeric, errors="coerce")
    corr = X.corr(method="spearman")
    m = corr.to_numpy(); np.fill_diagonal(m, np.nan)
    mean_abs_corr = float(np.nanmean(np.abs(m)))
    Xz = (X - X.mean())/X.std()
    Xz = Xz.dropna(how="any").reset_index(drop=True)
    pca = PCA(n_components=len(fam_cols)).fit(Xz)
    var = pca.explained_variance_ratio_
    load1 = pca.components_[0]; load2 = pca.components_[1]
    cf = pd.to_numeric(fams["COMMON_FORCING"], errors="coerce").to_numpy()
    fa = act["FIELD"].reindex(df["d"].values).to_numpy()
    mm = ~(np.isnan(cf)|np.isnan(fa))
    r_common = float(np.corrcoef(cf[mm], fa[mm])[0,1]) if mm.sum() > 100 else np.nan
    from sklearn.linear_model import LinearRegression
    W2 = np.column_stack([pca.transform(Xz)[:,0], pca.transform(Xz)[:,1]])
    tv = act["FIELD"].reindex(df["d"].values).to_numpy()[Xz.index]
    valid = ~np.isnan(tv)
    W2v = W2[valid]; tvs = tv[valid]
    if len(W2v) >= 100:
        lr = LinearRegression().fit(W2v, tvs)
        r2factor = float(np.corrcoef(lr.predict(W2v), tvs)[0,1])
    else:
        r2factor = np.nan
    rows = []
    rows.append(dict(metric="n_families", value=len(fam_cols)))
    rows.append(dict(metric="mean_abs_spearman_corr", value=round(mean_abs_corr,3)))
    rows.append(dict(metric="pca1_explained_variance", value=round(float(var[0]),3)))
    rows.append(dict(metric="pca2_explained_variance", value=round(float(var[1]),3)))
    rows.append(dict(metric="pca1_plus_pca2_variance", value=round(float(var[0]+var[1]),3)))
    rows.append(dict(metric="top3_loadings_pc1", value=";".join(
        f"{a}:{b:.2f}" for a,b in sorted(zip(fam_cols,load1), key=lambda t:-abs(t[1]))[:3])))
    rows.append(dict(metric="top3_loadings_pc2", value=";".join(
        f"{a}:{b:.2f}" for a,b in sorted(zip(fam_cols,load2), key=lambda t:-abs(t[1]))[:3])))
    rows.append(dict(metric="corr_common_forcing_vs_field_activation", value=round(r_common,3)))
    rows.append(dict(metric="corr_2factor_reconstruct_vs_field_activation", value=round(r2factor,3)))
    rows.append(dict(metric="verdict", value="RENDER_AFTER_REVIEW"))
    return pd.DataFrame(rows)

W(forcing_compression(), "05_FORCING_COMPRESSION.csv", index=False)

# ---------------------------------------------------------------- 06 CAPACITY MAP
def capacity_map():
    surf = {"6CELL":"grp6","8CELL":"grp8"}
    rows = []
    for sname, gcol in surf.items():
        for cell, sub in df.groupby(gcol):
            if len(sub) < 60: continue
            x = demand.loc[sub.index].to_numpy()
            y = act["FIELD"].reindex(sub["d"].values).to_numpy()
            m = ~(np.isnan(x)|np.isnan(y))
            ceil, x0, k, rmse, n = logistic_params(x[m], y[m])
            if n < 60: continue
            rows.append(dict(surface=sname, cell=cell, n=n,
                capacity_ceiling=round(float(ceil),3), half_sat_demand=round(float(x0),3),
                capacity_slope=round(float(k),3), fit_rmse=round(float(rmse),4),
                mean_vol=round(float(sub["vol_med"].mean()),2),
                mean_conc=round(float(sub["top3_share"].mean()),3),
                occupancy_share=round(len(sub)/len(df),3)))
    out = pd.DataFrame(rows).sort_values(["surface","capacity_ceiling"],
                                         ascending=[True,False]).reset_index(drop=True)
    for sname in ["6CELL","8CELL"]:
        q = out.loc[out["surface"]==sname,"capacity_ceiling"]
        lo, hi = q.quantile(1/3), q.quantile(2/3)
        sel = out["surface"]==sname
        out.loc[sel & (out["capacity_ceiling"]>=hi), "capacity_band"] = "HIGH"
        out.loc[sel & (out["capacity_ceiling"]<lo), "capacity_band"] = "LOW"
        out.loc[sel & (out["capacity_ceiling"]>=lo) & (out["capacity_ceiling"]<hi), "capacity_band"] = "MID"
    return out

cap = capacity_map()
W(cap, "06_CAPACITY_MAP.csv", index=False)

# ---------------------------------------------------------------- 07 CONGESTION MAP
def congestion_map():
    rowlist = []
    cc_all = {}
    for sname, gcol in {"6CELL":"grp6","8CELL":"grp8"}.items():
        cellC = cap[cap["surface"]==sname]
        cc = dict(zip(cellC["cell"], cellC["capacity_ceiling"]))
        cc_all[sname] = cc
        for cell, sub in df.groupby(gcol):
            if cell not in cc or len(sub) < 60: continue
            dem = demand.loc[sub.index].to_numpy()
            cong = dem / cc[cell]
            prop = sub["prop7"].to_numpy(); ren = sub["reentry7"].to_numpy(); rank = sub["rank7"].to_numpy()
            m = ~np.isnan(cong)&~np.isnan(prop)&~np.isnan(ren)&~np.isnan(rank)
            if m.sum() < 40: continue
            rowlist.append(dict(surface=sname, cell=cell, n=int(m.sum()),
                congestion_mean=round(float(np.nanmean(cong)),3),
                congestion_p25=round(float(np.nanquantile(cong,0.25)),3),
                congestion_p75=round(float(np.nanquantile(cong,0.75)),3),
                rho_cong_vs_prop=round(float(spearmanr(cong[m], prop[m])[0]),3),
                rho_cong_vs_reentry=round(float(spearmanr(cong[m], ren[m])[0]),3),
                rho_cong_vs_rankprop=round(float(spearmanr(cong[m], rank[m])[0]),3)))
    out = pd.DataFrame(rowlist)
    # capacity band for congestion level
    q = out["congestion_mean"].quantile([1/3, 2/3])
    out["congestion_band"] = np.select([out["congestion_mean"]>=q.iloc[1],
                                          out["congestion_mean"]<q.iloc[0]],
                                         ["HIGH","LOW"], "MID")
    # pooled correlations across all cells
    cc6, cc8 = cc_all["6CELL"], cc_all["8CELL"]
    cong6 = demand.to_numpy() / np.array([cc6.get(s, np.nan) for s in df["grp6"].to_numpy()])
    prop = df["prop7"].to_numpy(); ren = df["reentry7"].to_numpy(); rank = df["rank7"].to_numpy()
    m = ~np.isnan(cong6)&~np.isnan(prop)&~np.isnan(ren)&~np.isnan(rank)
    pooled = pd.DataFrame([dict(pool="6CELL", n=int(m.sum()),
        rho_cong_vs_prop=round(float(spearmanr(cong6[m], prop[m])[0]),3),
        rho_cong_vs_reentry=round(float(spearmanr(cong6[m], ren[m])[0]),3),
        rho_cong_vs_rankprop=round(float(spearmanr(cong6[m], rank[m])[0]),3))])
    return out, pooled

_cong, _cong_pool = congestion_map()
W(_cong, "07_CONGESTION_MAP.csv", index=False)
W(_cong_pool, "07b_CONGESTION_POOLED.csv", index=False)

# ---------------------------------------------------------------- shared: exit band classifier
def exit_band(p1, conc):
    if p1 is None or np.isnan(p1): return ""
    if p1 >= 0.60: return "NEAR_SINGLE_EXIT"
    if p1 >= 0.45: return "CONCENTRATED"
    if not np.isnan(conc) and conc is not None and conc == conc:
        if conc >= 0.0: return "NARROWING"
    return "OPEN_EXIT_SET"

# ---------------------------------------------------------------- 08 EXIT PRESSURE REGIME MAP
def exit_pressure_map():
    rows = []
    for sp in SUBPERIODS:
        idx = (df["subperiod"]==sp).values
        m6 = bm6.iloc[idx]
        dsub = df[idx]
        for cell, g in dsub.groupby("grp6"):
            gi = g.index
            sub_b = m6.loc[gi]
            v = sub_b.dropna(subset=["p1"])
            if len(v) < 20: continue
            p1m = float(v["p1"].mean()); k = int(v["k"].mean())
            ent = float(v["ent"].mean()); p2 = float(v["p2"].mean())
            conc = float(v["conc"].mean())
            rows.append(dict(subperiod=sp, state_6cell=cell, n=int(len(v)),
                branch_count_k=k, branch_entropy=round(ent,3),
                dominant_exit_share_p1=round(p1m,3), second_exit_share_p2=round(p2,3),
                exit_concentration=round(conc,3),
                exit_band=exit_band(p1m, conc)))
    out = pd.DataFrame(rows)
    return out

W(exit_pressure_map(), "08_EXIT_PRESSURE_REGIME_MAP.csv", index=False)

# ---------------------------------------------------------------- 09 ENTROPY x DEMAND MATRIX
def entropy_demand_matrix():
    m = bm6.copy()
    m["demand"] = demand.to_numpy()
    m["ent"] = m["ent"]
    qd = m["demand"].quantile(0.5); qe = m["ent"].quantile(0.5)
    m["dem_tier"] = np.where(m["demand"] >= qd, "HIGH", "LOW")
    m["ent_tier"] = np.where(m["ent"] >= qe, "HIGH_ENT", "LOW_ENT")
    mcell_map = dict(zip(df["d"].astype(str), df["grp6"].values))
    m["state"] = df["grp6"].values
    m["prop7"] = df["prop7"].values; m["reentry7"] = df["reentry7"].values
    m["rank7"] = df["rank7"].values; m["p1"] = m["p1"]
    rows = []
    for dt in ["LOW","HIGH"]:
        for et in ["LOW_ENT","HIGH_ENT"]:
            g = m[(m["dem_tier"]==dt)&(m["ent_tier"]==et)]
            if len(g) < 30: continue
            rows.append(dict(demand=dt, exit_entropy=et, n=len(g),
                mean_prop7=round(float(g["prop7"].mean()),3),
                mean_reentry7=round(float(g["reentry7"].mean()),3),
                mean_rank7=round(float(g["rank7"].mean()),3),
                dominant_exit_share=round(float(g["p1"].mean()),3)))
    return pd.DataFrame(rows).sort_values(["demand","exit_entropy"])

W(entropy_demand_matrix(), "09_ENTROPY_DEMAND_MATRIX.csv", index=False)

# ---------------------------------------------------------------- 10 TRANSFER EFFICIENCY
def transfer_efficiency():
    rows = []
    cf = pd.to_numeric(fams["COMMON_FORCING"], errors="coerce")
    for sp in SUBPERIODS:
        idxm = (df["subperiod"]==sp).values
        ds = df[idxm]
        for cell, g in ds.groupby("grp6"):
            gi = g.index
            prop = g["prop7"].to_numpy(); ren = g["reentry7"].to_numpy()
            fc_g = cf.loc[gi].to_numpy(); d_g = demand.loc[gi].to_numpy()
            cens = (np.abs(fc_g) > 0.30) & (np.abs(d_g) > 0.30) & ~np.isnan(prop)
            if cens.sum() < 30: continue
            rows.append(dict(subperiod=sp, state_6cell=cell, n=int(cens.sum()),
                eff_prop_per_demand=round(float(np.nanmean(prop[cens]/np.abs(d_g[cens]))),3),
                eff_prop_per_forcing=round(float(np.nanmean(prop[cens]/np.abs(fc_g[cens]))),3),
                eff_reentry_per_forcing=round(float(np.nanmean(ren[cens]/np.abs(fc_g[cens]))),3)))
    return pd.DataFrame(rows).sort_values(["subperiod","eff_prop_per_demand"], ascending=[True,False])

W(transfer_efficiency(), "10_TRANSFER_EFFICIENCY.csv", index=False)

# ---------------------------------------------------------------- threshold helpers
from sklearn.linear_model import LogisticRegression

def logit_fit(forcing, pf, min_n=80):
    x = np.asarray(forcing, dtype=float); y = np.asarray(pf, dtype=float)
    m = ~(np.isnan(x)|np.isnan(y)); x, y = x[m], y[m]
    if len(x) < min_n or y.sum() < 10 or (1-y).sum() < 10:
        return None
    mu, sd = float(x.mean()), float(x.std())
    if sd <= 0: return None
    xs = (x - mu)/sd
    clf = LogisticRegression(max_iter=1000).fit(xs.reshape(-1,1), y)
    b0, b1 = float(clf.intercept_[0]), float(clf.coef_[0][0])
    return dict(mu=mu, sd=sd, b0=b0, b1=b1, n=len(x))

def thr_at(par, prob):
    return par["mu"] + (np.log(prob/(1-prob)) - par["b0"])/(par["b1"] + 1e-9) * par["sd"]

def build_pact():
    out = {}
    for patch in DEPTH_ORDER:
        out[patch] = (act[patch] >= 0.55).astype(float)
    return pd.DataFrame(out, index=act.index)

pact = build_pact()
forcing_series = pd.to_numeric(fams["COMMON_FORCING"], errors="coerce").reset_index(drop=True)

# ---------------------------------------------------------------- 11 THRESHOLD BANDS
def threshold_bands():
    rows = []
    for patch in DEPTH_ORDER:
        pf = pact[patch].to_numpy(); fc = forcing_series.to_numpy()
        par = logit_fit(fc, pf)
        if par is None: continue
        t10 = thr_at(par, 0.10); t30 = thr_at(par, 0.30); t50 = thr_at(par, 0.50)
        t70 = thr_at(par, 0.70); t90 = thr_at(par, 0.90)
        # subperiod drift of half-sat
        sp50 = []
        for sp in SUBPERIODS:
            idx = (df["subperiod"]==sp).values
            spar = logit_fit(fc[idx], pf[idx])
            if spar: sp50.append(thr_at(spar, 0.50))
        drift = float(np.ptp(sp50)) if len(sp50) >= 2 else np.nan
        width = float(t90 - t10)
        rows.append(dict(patch=patch, n=par["n"],
            force_DORMANT_below=round(float(t10),3),
            force_LOW_band=round(float(t30),3),
            force_TRANSITION_hi=round(float(t70),3),
            force_HIGH_hi=round(float(t90),3),
            force_halfsat_t50=round(float(t50),3),
            band_width_t90_t10=round(width,3),
            subperiod_halfsat_drift_span=round(drift,3),
            slack=round(float(drift/width),3) if width>0 else np.nan))
    return pd.DataFrame(rows)

W(threshold_bands(), "11_THRESHOLD_BANDS.csv", index=False)

# ---------------------------------------------------------------- 12 THRESHOLD SURFACES
def threshold_surfaces():
    cond_cols = {"VOLATILITY":"vol_med","DISPERSION":"top500_dispersion_7d",
                 "CONCENTRATION":"top3_share","EXIT_ENTROPY":None,
                 "RANK_DEPTH":"rank_depth_rel","BTC_ANCHOR":"btc_return_7d",
                 "DEMAND":None}
    rows = []
    ent = bm6["ent"].to_numpy()
    for patch in DEPTH_ORDER:
        pf = pact[patch].to_numpy(); fc = forcing_series.to_numpy()
        for label, col in cond_cols.items():
            if col is None:
                if label == "EXIT_ENTROPY": cvar = ent
                elif label == "DEMAND": cvar = demand.to_numpy()
                else: continue
            else:
                cvar = pd.to_numeric(df[col], errors="coerce").to_numpy()
            ok = ~(np.isnan(cvar)|np.isnan(pf)|np.isnan(fc))
            if ok.sum() < 150: continue
            try:
                q = np.nanquantile(cvar[ok], [1/3, 2/3])
                tvals = {}
                for tier, mask in {"low": cvar<=q[0], "mid":(cvar>q[0])&(cvar<q[1]), "high": cvar>=q[1]}.items():
                    m = ok & mask
                    if m.sum() < 80: continue
                    par = logit_fit(fc[m], pf[m], min_n=60)
                    tvals[tier] = thr_at(par, 0.50) if par else np.nan
                if len(tvals) < 2: continue
                shift = tvals.get("high", np.nan) - tvals.get("low", np.nan)
                rows.append(dict(patch=patch, conditioning=label, n=int(ok.sum()),
                    thr50_low=round(float(tvals.get("low", np.nan)),3) if np.isfinite(tvals.get("low",np.nan)) else np.nan,
                    thr50_mid=round(float(tvals.get("mid", np.nan)),3) if np.isfinite(tvals.get("mid",np.nan)) else np.nan,
                    thr50_high=round(float(tvals.get("high", np.nan)),3) if np.isfinite(tvals.get("high",np.nan)) else np.nan,
                    shift_high_minus_low=round(float(shift),3)))
            except Exception:
                continue
    return pd.DataFrame(rows)

W(threshold_surfaces(), "12_THRESHOLD_SURFACES.csv", index=False)

# ---------------------------------------------------------------- 13 SATURATION ANATOMY
def sat_anatomy():
    rows = []
    for patch in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[patch].to_numpy()
        m = ~(np.isnan(x)|np.isnan(y)); x, y = x[m], y[m]
        ceil, x0, k, rmse, n = logistic_params(x, y)
        if n < 60 or np.isnan(ceil): continue
        lo, hi = float(y.min()), float(y.max())
        overshoot = float(hi - ceil)
        def x_of_frac(f):
            # forcing level where model reaches frac*ceil between floor and ceil
            yf = lo + f*(ceil-lo)
            denom = (ceil - yf + 1e-9)
            return x0 + np.log(yf/max(denom,1e-9))/k if k != 0 else np.nan
        onset = x_of_frac(0.20); halfsat = x0; highz = x_of_frac(0.70)
        top = y[x >= np.quantile(x, 0.85)]
        persistence = float(top.mean()) if len(top)>=10 else np.nan
        rows.append(dict(patch=patch, n=n,
            subthreshold_below=round(float(x_of_frac(0.05)),3),
            onset_f20=round(float(onset),3), half_saturation_x0=round(float(halfsat),3),
            acceleration_upper=round(float(x0+1.0/k),3) if k>0 else np.nan,
            high_zone_f70=round(float(highz),3),
            ceiling=round(float(ceil),3), slope_k=round(float(k),3),
            observed_peak=round(float(hi),3), overshoot=round(float(overshoot),3),
            post_sat_persistence=round(float(persistence),3), fit_rmse=round(float(rmse),4)))
    return pd.DataFrame(rows)

W(sat_anatomy(), "13_SATURATION_ANATOMY.csv", index=False)

# ---------------------------------------------------------------- 14 SATURATION SHAPE FAMILIES
def sat_shape_families():
    train = (df["subperiod"] != "2025-2026").values
    test = ~train
    rows = []
    for patch in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[patch].to_numpy()
        m = ~(np.isnan(x)|np.isnan(y))
        from sklearn.linear_model import LinearRegression
        def shape_labels(xs, ys):
            ceil, x0, k, r_log, _ = logistic_params(xs, ys)
            mx, x50, nH, r_hill, _ = hill_params(xs, ys)
            xs2 = xs.reshape(-1,1)
            lr = LinearRegression().fit(xs2, ys)
            pred = lr.predict(xs2)
            r_lin = float(np.sqrt(np.mean((ys-pred)**2)))
            return (None if np.isnan(r_log) else r_log), (None if np.isnan(r_hill) else r_hill), r_lin
        rl_tr, rh_tr, rlin_tr = shape_labels(x[m & train], y[m & train])
        rl_te, rh_te, rlin_te = shape_labels(x[m & test], y[m & test])
        if (m & test).sum() < 40: rl_te=rh_te=rlin_te=np.nan
        opts = [("LOGISTIC", rl_te), ("HILL", rh_te), ("LINEAR", rlin_te)]
        fin = [(nm, v) for nm, v in opts if nm and v==v]
        fam_name = min(fin, key=lambda t: t[1])[0] if fin else "INSUFFICIENT_TEST"
        rows.append(dict(patch=patch, n_train=int((m&train).sum()), n_test=int((m&test).sum()),
            rmse_logistic_tr=round(float(rl_tr),4) if rl_tr==rl_tr else np.nan,
            rmse_hill_tr=round(float(rh_tr),4) if rh_tr==rh_tr else np.nan,
            rmse_linear_tr=round(float(rlin_tr),4),
            rmse_logistic_test=round(float(rl_te),4) if rl_te==rl_te else np.nan,
            rmse_hill_test=round(float(rh_te),4) if rh_te==rh_te else np.nan,
            rmse_linear_test=round(float(rlin_te),4) if rlin_te==rlin_te else np.nan,
            best_family=fam_name))
    return pd.DataFrame(rows)

W(sat_shape_families(), "14_SATURATION_SHAPE_FAMILIES.csv", index=False)

# ---------------------------------------------------------------- 15 SATURATION NODE DRIFT
def sat_node_drift():
    rows = []
    for patch in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[patch].to_numpy()
        for sp in SUBPERIODS:
            idx = (df["subperiod"]==sp).values
            m = ~(np.isnan(x)|np.isnan(y)) & idx
            if m.sum() < 60: continue
            ceil, x0, k, rmse, n = logistic_params(x[m], y[m])
            if n < 60 or np.isnan(ceil): continue
            rows.append(dict(patch=patch, subperiod=sp, n=n,
                half_sat_x0=round(float(x0),3), ceiling=round(float(ceil),3),
                slope_k=round(float(k),3), fit_rmse=round(float(rmse),4)))
    return pd.DataFrame(rows)

W(sat_node_drift(), "15_SATURATION_NODE_DRIFT.csv", index=False)

# ---------------------------------------------------------------- 16 HYSTERESIS PILOT
def hysteresis_pilot():
    fdiff = forcing_series.diff().to_numpy()
    rising = fdiff >= 0
    rows = []
    for patch in DEPTH_ORDER:
        x = forcing_series.to_numpy(); y = act[patch].to_numpy()
        m = ~(np.isnan(x)|np.isnan(y)|np.isnan(fdiff))
        if m.sum() < 200: continue
        bins = np.quantile(x[m], np.linspace(0,1,7))
        diffs=[]; ns=[]
        for i in range(len(bins)-1):
            loB, hiB = bins[i], bins[i+1]
            rsel = m & (x>=loB) & (x<hiB)
            if rsel.sum() < 30: continue
            ru = rsel & rising; rd = rsel & ~rising
            if ru.sum()<10 or rd.sum()<10: continue
            mu = float(y[ru].mean()); md = float(y[rd].mean())
            diffs.append(mu-md); ns.append(int(rsel.sum()))
        if len(diffs) < 2: continue
        from scipy.stats import ranksums
        p = float(ranksums(y[m&rising], y[m&~rising]).pvalue) if len(y[m&rising])>=10 and len(y[m&~rising])>=10 else np.nan
        rows.append(dict(patch=patch,
            mean_hysteresis_gap=round(float(np.mean(diffs)),4),
            max_abs_gap=round(float(max(np.abs(np.array(diffs)))),4),
            n_bins=int(len(diffs)), ranksums_p=round(p,4) if p==p else np.nan,
            rising_share=round(float(len(y[m&rising])/m.sum()),3)))
    return pd.DataFrame(rows)

W(hysteresis_pilot(), "16_HYSTERESIS_PILOT.csv", index=False)

# ---------------------------------------------------------------- birth trajectory machinery
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

dfc = df.reset_index(drop=True)
g6 = dfc["grp6"].to_numpy()
prev_ = np.array([None] + list(g6[:-1]))
birth_mask = (g6 != prev_)
birth_pos = np.where(birth_mask)[0]
birth_pos = birth_pos[birth_pos >= 8]
birth_pos = birth_pos[birth_pos < len(dfc) - 8]

FEAT = {"demand": demand.reset_index(drop=True).to_numpy(),
        "breadth": pd.to_numeric(dfc["pos_ret_share"], errors="coerce").to_numpy(),
        "dispersion": pd.to_numeric(dfc["top500_dispersion_7d"], errors="coerce").to_numpy(),
        "forcing": forcing_series.to_numpy(),
        "concentration": pd.to_numeric(dfc["top3_share"], errors="coerce").to_numpy(),
        "rank_depth": pd.to_numeric(dfc["rank_depth_rel"], errors="coerce").to_numpy(),
        "exit_entropy": bm6["ent"].to_numpy()}
STAGES = ["PRECONDITION","INITIATION","COMMITMENT","EARLY_SURVIVAL"]

def birth_stage_matrix(pos):
    """Return dict stage x feature -> mean/median over births."""
    acc = {s: {f: [] for f in FEAT} for s in STAGES}
    for i in pos:
        pre = slice(i-7, i)
        com = slice(i+1, i+4)
        sur = slice(i+4, i+8)
        for f, arr in FEAT.items():
            acc["PRECONDITION"][f].append(np.nanmean(arr[pre]))
            acc["INITIATION"][f].append(arr[i])
            acc["COMMITMENT"][f].append(np.nanmean(arr[com]))
            acc["EARLY_SURVIVAL"][f].append(np.nanmean(arr[sur]))
    return acc

def birth_trajectory_df(pos):
    acc = birth_stage_matrix(pos)
    rows = []
    for s in STAGES:
        for f in FEAT:
            v = np.asarray(acc[s][f], dtype=float); v = v[~np.isnan(v)]
            if len(v) == 0: continue
            rows.append(dict(stage=s, feature=f, n=len(v),
                mean=round(float(np.mean(v)),4), sd=round(float(np.std(v)),4),
                p25=round(float(np.quantile(v,0.25)),4), p75=round(float(np.quantile(v,0.75)),4)))
    return pd.DataFrame(rows)

W(birth_trajectory_df(birth_pos), "17_BIRTH_TRAJECTORY_STAGES.csv", index=False)

# ---------------------------------------------------------------- 18 BIRTH EQUIFINALITY
def birth_vectors(pos):
    """Flatten each birth into a standardized feature vector over all stages.
    Rows = births, cols = feature x stage (preserves per-birth trajectory)."""
    acc = birth_stage_matrix(pos)
    cols = []
    for f in FEAT:
        for s in STAGES:
            cols.append(np.array(acc[s][f], dtype=float))
    X = np.column_stack(cols)
    X = np.nan_to_num(X)
    mu = X.mean(0); sd = X.std(0); sd[sd==0] = 1.0
    return (X - mu)/sd

def birth_equifinality():
    X = birth_vectors(birth_pos)
    dest = g6[birth_pos]  # destination state entered
    prevst = prev_[birth_pos]
    sub_arr = dfc["subperiod"].to_numpy()[birth_pos]
    best_k, best_s, best_lab = None, -9, None
    for k in range(3, 6):
        if k >= len(X): break
        km = KMeans(n_clusters=k, n_init=10, random_state=202617).fit(X)
        s = silhouette_score(X, km.labels_) if len(set(km.labels_)) > 1 else -9
        if s > best_s: best_s, best_k, best_lab = s, k, km.labels_
    if best_k is None:
        return pd.DataFrame([dict(verdict="DATA_LIMITED", n=len(X))])
    rows = []
    for c in range(best_k):
        sel = best_lab == c
        d = dest[sel]
        sp = sub_arr[sel]
        vc = pd.Series(sp).value_counts(normalize=True)
        rows.append(dict(cluster=c, n=len(d),
            subperiod_top=vc.index[0], subperiod_top_share=round(float(vc.iloc[0]),3),
            n_subperiods=int(vc.shape[0]),
            dominant_dest_state=pd.Series(d).value_counts().index[0],
            dominant_dest_share=round(float(pd.Series(d).value_counts(normalize=True).iloc[0]),3),
            mean_init_demand=round(float(np.nanmean(FEAT["demand"][birth_pos[sel]])),3),
            mean_init_forcing=round(float(np.nanmean(FEAT["forcing"][birth_pos[sel]])),3)))
    out = pd.DataFrame(rows)
    out["silhouette"] = round(best_s, 3)
    out["verdict"] = "MULTIPLE_BIRTH_PATHS" if out["n"].max() >= 50 and out.shape[0] >= 3 else ("DATA_LIMITED" if out.shape[0] < 2 else "SINGLE_DOMINANT_PATH")
    # multi-roads: for each dest with n>=30, count clusters
    multi = []
    for st, sub in pd.DataFrame({"d": dest, "c": best_lab}).groupby("d"):
        if len(sub) >= 30:
            multi.append(dict(destination=st, n_births=len(sub), n_clusters=int(sub["c"].nunique())))
    out_d = pd.DataFrame(multi)
    out_d["note"] = "DISTINCT" + " paths to same state" if out_d.shape[0]>0 else ""
    return out

W(birth_equifinality_ := birth_equifinality(), "18_BIRTH_TRAJECTORY_EQUIFINALITY.csv", index=False)

# ---------------------------------------------------------------- 19 ABORTED FORMATIONS
def aborted_formations():
    ab = []; vi = []
    for i in birth_pos:
        prev_state = prev_[i]
        win = g6[i+1:i+8]
        aborted = (win == prev_state).any()
        (ab if aborted else vi).append(i)
    rows = []
    for grp, name, ixs in [(ab, "ABORTED", ab), (vi, "VIABLE", vi)]:
        if len(ixs) < 20: continue
        acc = birth_stage_matrix(ixs)
        for s in STAGES:
            for f in FEAT:
                v = np.asarray(acc[s][f], dtype=float); v = v[~np.isnan(v)]
                if len(v) == 0: continue
                rows.append(dict(group=name, stage=s, feature=f, n=len(v),
                    mean=round(float(np.mean(v)),4), sd=round(float(np.std(v)),4)))
    return pd.DataFrame(rows)

W(aborted_formations(), "19_ABORTED_FORMATIONS.csv", index=False)

# ---------------------------------------------------------------- 20 2022 SHIFT RECONSTRUCTION

# ---------------------------------------------------------------- 20 2022 SHIFT RECONSTRUCTION
def _win_mask(darr, lo, hi):
    return (darr >= lo) & (darr <= hi)

DN = dfc["d"].dt.strftime("%Y-%m-%d").to_numpy()
PRE = _win_mask(DN, "2021-01-01", "2021-12-31")
DUR = _win_mask(DN, "2022-02-16", "2022-04-17")
POS = _win_mask(DN, "2022-05-01", "2022-12-31")
Y2022 = _win_mask(DN, "2022-01-01", "2022-12-31")

def _fmean(arr, mask):
    m = mask & ~np.isnan(arr)
    return float(np.mean(arr[m])) if m.sum() >= 10 else np.nan

def shift2022():
    coords = {
        "common_forcing": forcing_series.to_numpy(),
        "activation_field": act["FIELD"].reindex(dfc["d"].values).to_numpy(),
        "branch_entropy": bm6["ent"].to_numpy(),
        "branch_count": bm6["k"].to_numpy(),
        "dominant_exit_share": bm6["p1"].to_numpy(),
        "breadth_participation": pd.to_numeric(dfc["pos_ret_share"], errors="coerce").to_numpy(),
        "dispersion": pd.to_numeric(dfc["top500_dispersion_7d"], errors="coerce").to_numpy(),
        "concentration": pd.to_numeric(dfc["top3_share"], errors="coerce").to_numpy(),
        "rank_depth": pd.to_numeric(dfc["rank_depth_rel"], errors="coerce").to_numpy(),
    }
    rows = []
    for name, arr in coords.items():
        pr, du, po = _fmean(arr,PRE), _fmean(arr,DUR), _fmean(arr,POS)
        mu = _fmean(arr,Y2022); sd = np.nanstd(arr[Y2022 & ~np.isnan(arr)])
        z_dur = (du-mu)/sd if sd>0 else np.nan
        rows.append(dict(coordinate=name,
            pre_2021=round(pr,4) if pr==pr else np.nan,
            during_022_0417=round(du,4) if du==du else np.nan,
            post=round(po,4) if po==po else np.nan,
            z_during_vs_2022=round(z_dur,3) if z_dur==z_dur else np.nan,
            n_pre=int(PRE.sum()), n_during=int(DUR.sum()), n_post=int(POS.sum())))
    def _topo(mask):
        return _rhs(dfc[mask], "grp6", "self_transition")
    tp = _topo(PRE); td = _topo(DUR); tpo = _topo(POS)
    rPD,_ = B.M16.rank_order_rho(tp, td)
    rDP,_ = B.M16.rank_order_rho(td, tpo)
    rows.append(dict(coordinate="topology_self_transition_rho",
        pre_2021=round(rPD,3) if rPD==rPD else np.nan,
        during_022_0417=round(rDP,3) if rDP==rDP else np.nan,
        post=np.nan, z_during_vs_2022=np.nan,
        n_pre=int(PRE.sum()), n_during=int(DUR.sum()), n_post=int(POS.sum())))
    return pd.DataFrame(rows)

W(shift2022(), "20_2022_SHIFT_RECONSTRUCTION.csv", index=False)

# ---------------------------------------------------------------- 22 ADAPTIVE NODE ROLE ASSIGNMENT
def node_roles():
    sp_drift = None; thr = None
    p1 = OUT/"15_SATURATION_NODE_DRIFT.csv"; p2 = OUT/"11_THRESHOLD_BANDS.csv"
    if p1.exists(): sp_drift = pd.read_csv(p1)
    if p2.exists(): thr = pd.read_csv(p2)
    sath_drift = float(sp_drift["half_sat_x0"].std()) if sp_drift is not None and "half_sat_x0" in sp_drift else np.nan
    thr_drift = float(thr["subperiod_halfsat_drift_span"].mean()) if thr is not None and "subperiod_halfsat_drift_span" in thr else np.nan
    rows = [
        dict(node="STATE_AGE", role="STRUCTURAL_CORE", evidence="age overlays state but is not a universal clock (MECH-16 UNSTABLE_CLOCK)"),
        dict(node="ENTROPY_RESPONSE", role="ADAPTIVE_LAW", evidence="entropy topology survives; response drifts (MECH-16 ENTROPY_RESPONSE_DRIFT)"),
        dict(node="COMMON_FORCING", role="ADAPTIVE_LAW", evidence="single scalar drifts; family decomposition preferred (MECH-16 FULL_FORCING_DRIFT)"),
        dict(node="THRESHOLD_HIERARCHY", role=("ADAPTIVE_LAW" if thr_drift>0.4 else "STRUCTURAL_CORE"), evidence=f"subperiod half-sat drift span mean={thr_drift:.3f}"),
        dict(node="PHYSICAL_VS_SIGMA_EFFECT", role="LOCAL_PHYSICS", evidence="regime-modulated, patch-local"),
        dict(node="BIRTH_GEOMETRY", role="ADAPTIVE_LAW", evidence="birth geometry drifts; stage-dependent trajectory"),
        dict(node="SATURATION_LAW", role=("STRUCTURAL_CORE" if sath_drift<0.35 else "ADAPTIVE_LAW"), evidence=f"node-drift half-sat std={sath_drift:.3f}"),
        dict(node="TRAFFIC_DEMAND", role="ADAPTIVE_LAW", evidence="composite participation/recruitment descriptor"),
        dict(node="CAPACITY", role="LOCAL_PHYSICS", evidence="state-local response ceiling"),
        dict(node="CONGESTION", role="LOCAL_PHYSICS", evidence="demand/capacity within state"),
        dict(node="EXIT_PRESSURE", role="STRUCTURAL_CORE", evidence="branch geometry; directional-narrowing input"),
        dict(node="TRANSFER_EFFICIENCY", role="ADAPTIVE_LAW", evidence="realized propagation per unit demand; drifts"),
    ]
    return pd.DataFrame(rows)

W(node_roles(), "22_ADAPTIVE_NODE_ROLE_ASSIGNMENT.csv", index=False)

# ---------------------------------------------------------------- 23 DIRECTIONAL GEOMETRY LINK
def directional_link():
    m = bm6.copy()
    m["demand"] = demand.to_numpy()
    m["state"] = dfc["grp6"].to_numpy()
    capc = cap[cap["surface"]=="6CELL"]
    cc = dict(zip(capc["cell"], capc["capacity_ceiling"]))
    m["capacity"] = [cc.get(s, np.nan) for s in m["state"]]
    qd, qe, qc = m["demand"].quantile(0.5), m["ent"].quantile(0.5), m["capacity"].quantile(0.5)
    m["dt"] = np.where(m["demand"]>=qd, "HIGH", "LOW")
    m["et"] = np.where(m["ent"]>=qe, "OPEN", "TIGHT")
    m["ct"] = np.where(m["capacity"]>=qc, "HIGH_CAP", "LOW_CAP")
    rows = []
    for (dt,et,ct), g in m.dropna(subset=["capacity"]).groupby(["dt","et","ct"]):
        if len(g)<30: continue
        rows.append(dict(demand=dt, exit_entropy=et, capacity=ct, n=len(g),
            branch_concentration=round(float(g["conc"].mean()),3),
            dominant_exit_share=round(float(g["p1"].mean()),3),
            effective_exit_families_k=round(float(g["k"].mean()),2),
            exit_band=exit_band(float(g["p1"].mean()), float(g["conc"].mean())),
            directional_narrowing="YES_NARROW" if float(g["conc"].mean())>0.3 else "OPEN"))
    return pd.DataFrame(rows)

W(directional_link(), "23_DIRECTIONAL_GEOMETRY_LINK.csv", index=False)

# ---------------------------------------------------------------- 24 FREE EXTERNAL CONTEXT
free_ctx = pd.DataFrame([
    dict(source="SoSoValue", access_class="FREE_LIMITED_AUTOMATED", local_data=False, status="DATA_BLOCKED", note="No local ETF-flow cache (MECH-16 pilot also DATA_BLOCKED)"),
    dict(source="Spectre Explorer", access_class="FREE_LIMITED_AUTOMATED", local_data=False, status="DATA_BLOCKED", note="Not integrated this checkpoint"),
    dict(source="LI.FI / Jumper", access_class="FREE_LIMITED_AUTOMATED", local_data=False, status="DATA_BLOCKED", note="Quote/sim only; execution not authorized"),
    dict(source="Token Terminal", access_class="PAID_EXCLUDED", local_data=False, status="DATA_BLOCKED", note="No free programmatic API"),
    dict(source="Polymarket / Falcon", access_class="FREE_REFERENCE_ONLY", local_data=False, status="DATA_BLOCKED", note="$0 API unverified"),
    dict(source="Yieldz / protocol-native", access_class="FREE_REFERENCE_ONLY", local_data=False, status="DATA_BLOCKED", note="Use protocol-native free reads later"),
    dict(source="Stablecoin capital (local panel)", access_class="LOCAL_FREE", local_data=True, status="AVAILABLE_LOCAL", note="stablecoin_change_7d + stablecoin_mcap_share in forcing atlas"),
    dict(source="Chain TVL / DEX vol (local panel)", access_class="LOCAL_FREE", local_data=True, status="AVAILABLE_LOCAL", note="context only"),
])
W(free_ctx, "24_FREE_EXTERNAL_CONTEXT.csv", index=False)

# ---------------------------------------------------------------- 25 PROMOTE / MERGE / DISSOLVE
def promote_merge_dissolve():
    hy = None
    p = OUT/"16_HYSTERESIS_PILOT.csv"
    if p.exists(): hy = pd.read_csv(p)
    hy_max = float(hy["max_abs_gap"].max()) if hy is not None and len(hy) and "max_abs_gap" in hy else 0.02
    rows = [
        dict(object="TRAFFIC_DEMAND", decision="PROMOTE", role="ADAPTIVE_LAW", reason="interpretable composite; efficiency denominator"),
        dict(object="CAPACITY", decision="PROMOTE", role="LOCAL_PHYSICS", reason="state-local response ceiling on 6/8-cell"),
        dict(object="CONGESTION", decision="PROMOTE", role="LOCAL_PHYSICS", reason="demand/capacity ratio"),
        dict(object="EXIT_PRESSURE", decision="PROMOTE", role="STRUCTURAL_CORE", reason="branch geometry; narrowing without sign"),
        dict(object="TRANSFER_EFFICIENCY", decision="PROMOTE", role="ADAPTIVE_LAW", reason="propagation per unit demand; censored"),
        dict(object="SATURATION_LAW", decision="PROMOTE", role="STRUCTURAL_CORE_CANDIDATE", reason="stable shape; nodes drift"),
        dict(object="THRESHOLD_BAND", decision="PROMOTE", role="ADAPTIVE_LAW", reason="bands more transportable than point thresholds"),
        dict(object="HYSTERESIS", decision=("DISSOLVE" if hy_max<0.02 else "PARK"), role="RESEARCH_ONLY", reason=f"max_abs_gap={hy_max:.3f}"),
        dict(object="16_CELL_RAW_SURFACE", decision="DISSOLVE", role="REPLACED_BY_REDUCED", reason="MECH-16 dissolved"),
        dict(object="COMMON_FORCING_SCALAR_ONLY", decision="DISSOLVE", role="REPLACED_BY_FAMILIES", reason="family decomposition preferred"),
        dict(object="STATE_X_AGE_CLOCK_LAW", decision="DISSOLVE", role="UNSTABLE_CLOCK", reason="MECH-16 dissolved"),
    ]
    return pd.DataFrame(rows)

W(promote_merge_dissolve(), "25_PROMOTE_MERGE_DISSOLVE.csv", index=False)

# ---------------------------------------------------------------- 26 NULL AND FAILED RESULTS
nulls = pd.DataFrame([
    dict(avenue="Free ETF/institutional flow sensor", status="DATA_BLOCKED", note="no local data; only stablecoin-capital local proxy"),
    dict(avenue="Absolute physical capacity units", status="NULL", note="no physical units supportable; capacity = state-local response ceiling"),
    dict(avenue="Hysteresis / path dependence", status="PILOT", note="gap magnitude check; not promoted unless robust"),
    dict(avenue="Forcing as single deterministic scalar", status="NULL", note="family decomposition preferred"),
    dict(avenue="Directional sign prediction", status="FORBIDDEN", note="traffic geometry only; no sign signal"),
    dict(avenue="16-cell raw operational surface", status="DISSOLVED", note="replaced by reduced 6/8-cell dual"),
    dict(avenue="State-age as universal clock", status="DISSOLVED", note="UNSTABLE_CLOCK"),
    dict(avenue="Archetype naming without sample support", status="NULL", note="requires n>=50, >=3 subperiods, no single period >50%"),
    dict(avenue="SoSoValue ETF-flow forcing coordinate", status="DATA_BLOCKED", note="no runtime dependency; blocked"),
])
W(nulls, "26_NULL_AND_FAILED_RESULTS.csv", index=False)

print("=== MECH-17 build complete ===", flush=True)
