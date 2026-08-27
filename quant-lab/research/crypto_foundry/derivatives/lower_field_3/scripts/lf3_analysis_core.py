"""LF3 compact, reproducible analyses from LF2 feature cache and LF3 event table."""
from __future__ import annotations
import numpy as np
import pandas as pd
import lf3_common as C

H = C.H

def load_events():
    return pd.read_csv(C.RESULTS / "_lf3_events_internal.csv", low_memory=False)

def add_path_features(ev):
    e = ev.copy()
    e["date"] = pd.to_datetime(e["historical_date"])
    e["period"] = C.periods(e["date"])
    # Event-time descriptive paths. Always use finite forward fields only;
    # missing end-of-series values remain censored, never zero-filled.
    for h in H:
        fcol = f"fwd{h}" if f"fwd{h}" in e else C.FWD[h]
        s = e[f"signed_fwd{h}"] if f"signed_fwd{h}" in e else e["event_sign"] * e[fcol]
        e[f"signed_fwd{h}"] = s
        e[f"rev{h}"] = s < 0
        e[f"giveback{h}"] = np.clip(np.maximum(0, -s) / e["ret_1d"].abs(), 0, 10)
        e[f"recover1s{h}"] = s >= e["sigma_t0"] * np.sqrt(h)
        e[f"new_extreme{h}"] = s >= e["ret_1d"].abs()
    return e

def _summary(g, label_cols):
    row = {c: g[c].iloc[0] for c in label_cols}
    row.update(n=int(len(g)), assets=int(g.cmc_id.nunique()),
               p_rev7=float(g.rev7.mean()), p_recover1s_3d=float(g.recover1s3.mean()),
               p_giveback50_7d=float((g.giveback7 >= .5).mean()),
               p_new_extreme_7d=float(g.new_extreme7.mean()),
               med_signed_fwd7=float(g.signed_fwd7.replace([np.inf, -np.inf], np.nan).median()),
               p_1s_7d=float(g.recover1s7.mean()))
    return row

def loner_clusters(e):
    # Rule-free descriptive outcome families on post-event path geometry.
    l = e[(e.participation == "ISOLATED") & (e.event_sign < 0) & (e.z1 >= 3)].copy()
    # Mutually exclusive geometry labels, minimum counts checked in output.
    l["path_family"] = np.select([
        (l.recover1s3 & (l.giveback7 >= .5)),
        (l.recover1s7 & (l.giveback7 < .5)),
        (~l.recover1s3 & l.new_extreme7),
        (~l.recover1s3 & ~l.new_extreme7),
    ], ["FAST_REBOUND", "SLOW_REPAIR", "CONTINUED_DECLINE", "PARTIAL_REBOUND"], default="UNCLASSIFIED")
    rows=[]
    for band, g0 in l.groupby("rank_band"):
        for fam, g in g0.groupby("path_family"):
            # Named families require >=50 effective events and >=3 quarters.
            if len(g) < 50 or g.period.nunique() < 3:
                continue
            r=_summary(g,["rank_band","path_family"])
            r["n_periods"]=g.period.nunique(); r["effective_rule"]=">=50 events and >=3 quarters"; rows.append(r)
    return pd.DataFrame(rows)

def loner_discriminators(e):
    l=e[(e.participation == "ISOLATED") & (e.event_sign < 0) & (e.z1 >= 3)].copy()
    l["outcome"] = np.where(l.recover1s3, "RECOVERABLE_1S_BY_3D", "NO_1S_BY_3D")
    cols=["z1","rank","rank_neighbor_median_ret","rank_neighbor_same_sign","rank_neighbor_tail_share",
          "rank_context_isolation","listing_age_days","volume_24h_usd","mkt_vol_30d",
          "btc_ret_1d","eth_ret_1d","top500_breadth_30d","rank_vel_7d","rank_vel_14d"]
    rows=[]
    for b,g in l.groupby("rank_band"):
        a=g[g.outcome=="RECOVERABLE_1S_BY_3D"]; q=g[g.outcome=="NO_1S_BY_3D"]
        for col in cols:
            if col not in g or len(a[col].dropna())<20 or len(q[col].dropna())<20: continue
            aa=a[col].replace([np.inf,-np.inf],np.nan).dropna(); qq=q[col].replace([np.inf,-np.inf],np.nan).dropna(); pool=np.sqrt((aa.var(ddof=1)+qq.var(ddof=1))/2)
            rows.append({"rank_band":b,"outcome_split":"RECOVER_1S_BY_3D","feature":col,"n_recover":len(aa),"n_fail":len(qq),"cohen_d":(aa.mean()-qq.mean())/pool if pool>0 else np.nan,"recover_mean":aa.mean(),"fail_mean":qq.mean()})
    return pd.DataFrame(rows)

def state_machine(e):
    rows=[]
    for family,g0 in e[e.z1>=3].groupby(["participation","event_sign_label","rank_band"]):
        part,sign,band=family
        for h in H:
            s=g0[f"signed_fwd{h}"]
            # competing states at h; a row can satisfy several thresholds.
            valid = s.notna() & g0["sigma_t0"].notna()
            states={"STABILIZED":(s>=0),"1S_RECOVERY":(s>=g0.sigma_t0*np.sqrt(h)),
                    "25P_GIVEBACK":(g0[f"giveback{h}"]>=.25),"50P_GIVEBACK":(g0[f"giveback{h}"]>=.5),
                    "FULL_REVERSAL":(s<0),"NEW_EXTREME":(s>=g0.ret_1d.abs())}
            for st,m in states.items():
                m = m & valid
                denom = int(valid.sum())
                rows.append({"participation":part,"sign":sign,"rank_band":band,"horizon":f"{h}D","state":st,"n":int(m.sum()),"n_valid":denom,"prob":float(m.sum()/denom) if denom else np.nan,"assets":int(g0.loc[m,"cmc_id"].nunique())})
    return pd.DataFrame(rows)

def coordinated_up(e):
    u=e[(e.event_sign>0)&e.participation.isin(["BAND_BROAD","MULTI_BAND"])].copy()
    u["class7"] = np.select([u.signed_fwd7 >= .25*u.ret_1d.abs(), u.giveback7 >= .50, u.new_extreme7], ["CONTINUATION","FULL_GIVEBACK","NEW_HIGH_EXTENSION"], default="PARTIAL_GIVEBACK_NEUTRAL")
    rows=[]
    for b,g in u.groupby("rank_band"):
        for c,gg in g.groupby("class7"):
            rows.append(_summary(gg,["rank_band","class7"]))
    # first divergence: standardized t0 coordinate differences between continuation and giveback.
    drows=[]
    a=u[u.class7=="CONTINUATION"]; b=u[u.class7.isin(["FULL_GIVEBACK","PARTIAL_GIVEBACK_NEUTRAL"])]
    for col in ["top500_breadth_30d","mkt_vol_30d","volume_24h_usd","rank","rank_vel_7d","rank_neighbor_same_sign"]:
        if col not in u: continue
        aa=a[col].dropna(); bb=b[col].dropna()
        if len(aa)<30 or len(bb)<30: continue
        pool=np.sqrt((aa.var(ddof=1)+bb.var(ddof=1))/2)
        drows.append({"feature":col,"n_cont":len(aa),"n_noncont":len(bb),"cohen_d":(aa.mean()-bb.mean())/pool if pool else np.nan,"cont_mean":aa.mean(),"noncont_mean":bb.mean()})
    return pd.DataFrame(rows),pd.DataFrame(drows)

def topology(e):
    rows=[]
    for fam,g in e[e.z1>=3].groupby(["participation","event_sign_label"]):
        r=_summary(g,["participation","event_sign_label"]); r["rank_mix"]=g["rank"].median(); r["breadth_med"]=g["top500_breadth_30d"].median(); r["isolation_med"]=g["absolute_isolation"].median(); rows.append(r)
    return pd.DataFrame(rows)

def deterioration(e):
    # Rank deterioration is positive rank velocity (rank number increasing).
    d=e[(e.event_sign<0)&e.participation.eq("ISOLATED")&(e.z1>=3)].copy()
    for h in [3,7,14,30]:
        c=f"rank_vel_{h}d"
        if c in d: d[c+"_state"]=np.select([d[c]>0,d[c]<0],["DETERIORATING","IMPROVING"],default="FLAT")
    rows=[]
    cands=[c for c in ["rank_vel_3d","rank_vel_7d","rank_vel_14d","rank_vel_30d"] if c in d]
    for c in cands:
        for st,g in d.groupby(c+"_state"):
            if len(g)<30: continue
            r=_summary(g,[c+"_state"]);r["velocity_feature"]=c; rows.append(r)
    return pd.DataFrame(rows)

def shhm_vs_shmc(d):
    # Compare state geometry on all valid rows, not only event rows.
    x=d[d.momentum_state.isin(["SHORT_HOT_MEDIUM_HOT","SHORT_HOT_MEDIUM_COLD"])].copy()
    x["z7"] = x.fwd7_cum/(x.sigma_t0*np.sqrt(7))
    rows=[]
    for band,g in x.groupby(["rank_band","momentum_state"]):
        b,st=band; rows.append({"rank_band":b,"state":st,"n":len(g),"p_abs2s":(g.z7.abs()>=2).mean(),"p_abs3s":(g.z7.abs()>=3).mean(),"p_up2s":(g.z7>=2).mean(),"p_down2s":(g.z7<=-2).mean(),"median_z7":g.z7.median(),"raw15":(g.fwd7_cum.abs()>=.15).mean()})
    return pd.DataFrame(rows)

def high_breadth_disp(d):
    # Daily state group; asset anatomy inside four quadrants.
    d=d.copy(); d["z1"]=d.ret_1d.abs()/d.sigma_t0
    bm=d.top500_breadth_30d.median(); dm=d.groupby("rank_band")["ret_1d"].transform("std").median()
    # per date/band local dispersion
    bd=d.groupby(["historical_date","rank_band"])["ret_1d"].transform("std")
    d["quadrant"]=np.select([(d.top500_breadth_30d>bm)&(bd>dm),(d.top500_breadth_30d>bm)&(bd<=dm),(d.top500_breadth_30d<=bm)&(bd>dm)], ["BRD_HI_DISP_HI","BRD_HI_DISP_LO","BRD_LO_DISP_HI"],default="BRD_LO_DISP_LO")
    rows=[]
    for q,g in d.groupby(["rank_band","quadrant"]):
        rows.append({"rank_band":q[0],"quadrant":q[1],"n":len(g),"assets":g.cmc_id.nunique(),"tail2":(g.z1>=2).mean(),"tail3":(g.z1>=3).mean(),"up_share":(g.ret_1d>0).mean(),"disp":g.ret_1d.std(),"median_z":g.z1.median()})
    return pd.DataFrame(rows)

def baskets(d,e):
    rows=[]
    # Descriptive dynamic cohorts, not positions or trades.
    cohorts={"ISOLATED_DOWN":e[(e.participation=="ISOLATED")&(e.event_sign<0)],"COORDINATED_UP":e[(e.participation.isin(["BAND_BROAD","MULTI_BAND"]))&(e.event_sign>0)],"HIGH_TAIL":d[d.ret_1d.abs()/d.sigma_t0>=3],"SHHM":d[d.momentum_state=="SHORT_HOT_MEDIUM_HOT"]}
    for name,g in cohorts.items():
        for band,bb in g.groupby("rank_band"):
            rows.append({"basket":name,"rank_band":band,"n":len(bb),"assets":bb.cmc_id.nunique(),"median_ret":bb.ret_1d.median(),"breadth":(bb.ret_1d>0).mean(),"dispersion":bb.ret_1d.std(),"tail_share":(bb.ret_1d.abs()/bb.sigma_t0>=3).mean()})
    return pd.DataFrame(rows)

def triangle(d):
    # Daily band aggregates; A=top breadth, B=lower dispersion, C=tail share.
    x=d.copy(); x["z1"]=x.ret_1d.abs()/x.sigma_t0
    q=x.groupby(["historical_date","rank_band"]).agg(A=("top500_breadth_30d","last"),B=("ret_1d","std"),C=("z1",lambda s:(s>=3).mean()),btc=("btc_ret_1d","last"),vol=("mkt_vol_30d","last")).reset_index()
    rows=[]
    for band,g in q.groupby("rank_band"):
        for a,b in [("A","B"),("B","C"),("A","C")]: rows.append({"rank_band":band,"relation":f"{a}-{b}","n":len(g),"corr":g[a].corr(g[b])})
        # residualized partial correlations with the third coordinate + common controls.
        for target, cond in [("A","B"),("B","A"),("C","B")]:
            cols=[cond,"btc","vol"]; mm=g[[target]+cols].dropna()
            if len(mm)<30: continue
            X=np.column_stack([np.ones(len(mm)),mm[cols].to_numpy(float)]); y=mm[target].to_numpy(float)
            resid=y-X@np.linalg.lstsq(X,y,rcond=None)[0]
            rows.append({"rank_band":band,"relation":f"{target}|{cond},BTC,VOL","n":len(mm),"corr":np.corrcoef(resid, y)[0,1] if np.std(resid)>0 else np.nan})
    return pd.DataFrame(rows)

def sequences(e):
    # Event-level local sequences, requiring >=50 effective events and >=3 quarters.
    e=e.copy(); e["period"]=C.periods(e["historical_date"])
    e["sequence"] = e["participation"]+"_"+e["event_sign_label"]+" -> "+np.where(e["recover1s3"],"1S_RECOVERY","NO_1S_BY_3D")
    rows=[]
    for seq,g in e.groupby("sequence"):
        if len(g)<50 or g.period.nunique()<3: continue
        base=e.recover1s3.mean(); rows.append({"sequence":seq,"n":len(g),"assets":g.cmc_id.nunique(),"periods":g.period.nunique(),"p_recover1s3":g.recover1s3.mean(),"baseline":base,"lift":g.recover1s3.mean()-base})
    return pd.DataFrame(rows)

def main():
    d=C.load_panel(); e=load_events(); e=add_path_features(e)
    for fn,name in [(loner_clusters,"05_LONER_PATH_CLUSTERS.csv"),(loner_discriminators,"06_LONER_PRE_EVENT_DISCRIMINATORS.csv"),(state_machine,"07_REVERSAL_STATE_MACHINE.csv"),(topology,"12_SIGN_PARTICIPATION_TOPOLOGY.csv"),(deterioration,"13_RANK_DETERIORATION_SHOCK_BRIDGE.csv"),(sequences,"18_LOCAL_SEQUENCE_ATLAS.csv")]:
        fn(e).to_csv(C.RESULTS/name,index=False)
    sm=state_machine(e); sm.to_csv(C.RESULTS/"07_REVERSAL_STATE_MACHINE.csv",index=False)
    # Transition hazards by origin sign/participation/rank at first threshold horizon.
    hazards=[]
    for keys,g in e[e.z1>=3].groupby(["participation","event_sign_label","rank_band"]):
        for h in H:
            for st,m in {"1S_RECOVERY":g[f"recover1s{h}"],"FULL_REVERSAL":g[f"rev{h}"],"NEW_EXTREME":g[f"new_extreme{h}"],"50P_GIVEBACK":g[f"giveback{h}"]>=.5}.items():
                hazards.append({"participation":keys[0],"sign":keys[1],"rank_band":keys[2],"horizon":f"{h}D","state":st,"n_risk":len(g),"n_transition":int(m.sum()),"hazard":float(m.mean())})
    pd.DataFrame(hazards).to_csv(C.RESULTS/"08_REVERSAL_TRANSITION_HAZARDS.csv",index=False)
    co,fd=coordinated_up(e);co.to_csv(C.RESULTS/"10_COORDINATED_UP_OUTCOMES.csv",index=False);fd.to_csv(C.RESULTS/"11_COORD_UP_FIRST_DIVERGENCE.csv",index=False)
    shhm_vs_shmc(d).to_csv(C.RESULTS/"14_SHHM_VS_SHMC.csv",index=False)
    high_breadth_disp(d).to_csv(C.RESULTS/"15_HIGH_BRD_HIGH_DISP_ASSET_ANATOMY.csv",index=False)
    baskets(d,e).to_csv(C.RESULTS/"16_LOCAL_BASKET_GEOMETRY.csv",index=False)
    triangle(d).to_csv(C.RESULTS/"17_TRIANGLE_BREADTH_DISP_TAIL.csv",index=False)
    # 09 checkpoint: first-1sigma path by family/band.
    rows=[]
    for fam,g in e[e.z1>=3].groupby(["participation","event_sign_label","rank_band"]):
        for h in H:
            m=g[f"recover1s{h}"]
            rows.append({"participation":fam[0],"sign":fam[1],"rank_band":fam[2],"horizon":f"{h}D","n":len(g),"p_1s":m.mean(),"p_50giveback":(g[f"giveback{h}"]>=.5).mean(),"p_full_reversal":g[f"rev{h}"].mean(),"p_new_extreme":g[f"new_extreme{h}"].mean()})
    pd.DataFrame(rows).to_csv(C.RESULTS/"09_ONE_SIGMA_CHECKPOINT.csv",index=False)
    # Compare 4-class path stats to preserve an all-loner outcome map.
    print("LF3 core outputs written; events",len(e),"loner down 3s",int(((e.participation=="ISOLATED")&(e.event_sign<0)&(e.z1>=3)).sum()))
if __name__=="__main__": main()
