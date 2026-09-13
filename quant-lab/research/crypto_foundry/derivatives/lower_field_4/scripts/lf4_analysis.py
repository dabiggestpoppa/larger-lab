from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np,pandas as pd
import lf4_common as C

def main():
 d=C.load_cache(); e=C.add_forward(C.load_events()); e=e[(e.z1>=2)&e.event_sign.ne(0)].copy()
 p=e[(e.participation=="ISOLATED")&(e.event_sign<0)].copy()
 # Rank-health clocks: positive numerical rank delta means deterioration.
 rows=[]
 for band,g in p.groupby("rank_band"):
  for h in C.RANK_H:
   rr=g[g[f"fwd{h}"].notna()]
   rows.append({"rank_band":band,"horizon":f"{h}D","n":len(rr),"p_price_recovery":C.safe_mean(rr[f"recover1s{h}"]),"p_full_reversal":C.safe_mean(rr[f"rev{h}"]),"p_price_up_rank_up":np.nan,"p_price_up_rank_down":np.nan,"rank_clock_status":"DATA_BLOCKED_RANK_FUTURE_NOT_IN_LF2_EVENT_CACHE"})
 C.write_csv(pd.DataFrame(rows),"15_PRICE_RECOVERY_CLOCK.csv")
 C.write_csv(pd.DataFrame(rows).assign(clock="RANK_HEALTH",status="DATA_BLOCKED_RANK_FUTURE_NOT_IN_LF2_EVENT_CACHE"),"16_RANK_HEALTH_CLOCK.csv")
 C.write_csv(pd.DataFrame(rows).assign(cross_state="PRICE_RANK_CROSS_STATE_NOT_ESTIMABLE_FROM_CURRENT_CACHE"),"17_PRICE_RANK_CROSS_STATE.csv")
 # Reconciliation of prior claims with the common current event universe.
 recon=[]
 for b,g in p.groupby("rank_band"):
  for h in [3,7,14]: recon.append({"rank_band":b,"threshold":"z1>=2","participation":"ISOLATED","horizon":f"{h}D","n":len(g),"p_reversal":C.safe_mean(g[f"rev{h}"]),"rank_velocity_definition":"not available as future rank; pre-event only","purge":"not applied to descriptive denominator","mech7_comparison":"not directly reproducible without MECH-7 event table","adjudication":"DESCRIPTIVE_ONLY"})
 C.write_csv(pd.DataFrame(recon),"18_RANK_HEALTH_RECONCILIATION.csv")
 # One sigma timing and outcome map.
 r=[]
 for b,g in p.groupby("rank_band"):
  for label,mask in [("EARLY_1D",g.recover1s1),("EARLY_2D",g.recover1s2),("EARLY_3D",g.recover1s3),("MID_4_5D",g.recover1s5 & ~g.recover1s3),("LATE_6_7D",g.recover1s7 & ~g.recover1s5),("NONE_7D",~g.recover1s7)]:
   q=g[mask]
   r.append({"rank_band":b,"timing_class":label,"n":len(q),"p_full_reversal_7d":C.safe_mean(q.rev7),"p_new_low_proxy_7d":C.safe_mean(~q.recover1s7),"p_giveback50_7d":C.safe_mean(q.giveback7>=.5),"status":"DESCRIPTIVE_CENSORED"})
 C.write_csv(pd.DataFrame(r),"14_ONE_SIGMA_DEEP_DIVE.csv")
 # Broad sign/participation matrix.
 a=[]
 for k,g in e.groupby(["rank_band","participation","event_sign_label"]):
  a.append({"rank_band":k[0],"participation":k[1],"sign":k[2],"n":len(g),"p_reversal_7d":C.safe_mean(g.rev7),"p_recover1s_7d":C.safe_mean(g.recover1s7),"p_giveback50_7d":C.safe_mean(g.giveback7>=.5),"median_signed_fwd7":C.safe_mean(g.signed_fwd7),"interaction_status":"DESCRIPTIVE_NO_MODEL"})
 C.write_csv(pd.DataFrame(a),"20_BROAD_UP_DOWN_ASYMMETRY.csv")
 # Liquidity proxy within available data.
 q=e.copy(); q["vol_rank_q"]=q.groupby("historical_date")["volume_24h_usd"].rank(pct=True)
 li=[]
 for b,g in q.groupby("rank_band"):
  for bucket,h in g.groupby(pd.cut(g.vol_rank_q,[0,.2,.4,.6,.8,1],labels=["Q1","Q2","Q3","Q4","Q5"],include_lowest=True)):
   li.append({"rank_band":b,"volume_bucket":str(bucket),"n":len(h),"p_early_1s":C.safe_mean(h.recover1s3),"p_full_reversal":C.safe_mean(h.rev7),"p_new_low_proxy":C.safe_mean(~h.recover1s7),"controls":"rank,z1,age,breadth,dispersion,BTC,volatility not jointly fit","status":"DESCRIPTIVE_ONLY"})
 C.write_csv(pd.DataFrame(li),"21_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv")
 # HH anatomy using date-level median breadth and per-date band dispersion.
 q["date_disp"]=q.groupby(["historical_date","rank_band"])["ret_1d"].transform("std")
 bm=q.groupby("historical_date")["top500_breadth_30d"].first().median(); dm=q.groupby(["historical_date","rank_band"])["date_disp"].transform("median").median()
 q["quad"]=np.select([(q.top500_breadth_30d>=bm)&(q.date_disp>=dm),(q.top500_breadth_30d>=bm)&(q.date_disp<dm),(q.top500_breadth_30d<bm)&(q.date_disp>=dm)], ["HH","HL","LH"],default="LL")
 hh=[]
 for k,g in q.groupby(["rank_band","quad"]): hh.append({"rank_band":k[0],"state":k[1],"n":len(g),"tail2":C.safe_mean(g.z1>=2),"tail3":C.safe_mean(g.z1>=3),"up_share":C.safe_mean(g.ret_1d>0),"isolated_down_share":C.safe_mean((g.participation=="ISOLATED")&(g.event_sign<0)) if "participation" in g else np.nan,"median_volume":C.safe_mean(g.volume_24h_usd)})
 C.write_csv(pd.DataFrame(hh),"22_HH_ASSET_ANATOMY.csv")
 # SHHM vs SHMC one final descriptive check.
 s=d[d.momentum_state.isin(["SHORT_HOT_MEDIUM_HOT","SHORT_HOT_MEDIUM_COLD"])].copy(); s["z7"]=s.fwd7_cum/(s.sigma_t0*np.sqrt(7)); out=[]
 for k,g in s.groupby(["rank_band","momentum_state"]): out.append({"rank_band":k[0],"state":k[1],"n":len(g),"p_abs2s":C.safe_mean(g.z7.abs()>=2),"p_abs3s":C.safe_mean(g.z7.abs()>=3),"p_up2s":C.safe_mean(g.z7>=2),"p_down2s":C.safe_mean(g.z7<=-2),"median_z7":C.safe_mean(g.z7),"verdict":"DESCRIPTIVE_RECHECK"})
 C.write_csv(pd.DataFrame(out),"23_SHMC_SHHM_FINAL_RECHECK.csv")
 # Integrity repair notes and rebuilt baskets/triangle.
 (C.RESULTS.parent/"24_BASKET_DISPERSION_INTEGRITY_AUDIT.md").write_text("# LF3 BASKET DISPERSION INTEGRITY AUDIT\n\nThe prior LF3 basket table is not reused as a source of inference. LF4 rebuilds dispersion from finite same-date asset returns; no sigma denominator is used for dispersion. Any empty or unavailable cohort is retained as NA. Status: REPAIRED_FOR_DESCRIPTIVE_USE; no causal or tradeability claim.\n",encoding="utf-8")
 b=[]
 cohorts={"ISOLATED_DOWN":e[(e.participation=="ISOLATED")&(e.event_sign<0)],"COORDINATED_UP":e[e.participation.isin(["BAND_BROAD","MULTI_BAND"])&(e.event_sign>0)],"HIGH_TAIL":e[e.z1>=3],"SHHM":e[e.momentum_state.eq("SHORT_HOT_MEDIUM_HOT")],"SHMC":e[e.momentum_state.eq("SHORT_HOT_MEDIUM_COLD")]}
 for name,g in cohorts.items():
  for band,h in g.groupby("rank_band"):
   b.append({"basket":name,"rank_band":band,"n":len(h),"assets":h.cmc_id.nunique(),"median_return":C.safe_mean(h.ret_1d),"breadth":C.safe_mean(h.ret_1d>0),"dispersion":finite_std(h.ret_1d),"tail_share":C.safe_mean(h.z1>=3),"neighbor_isolation":C.safe_mean(h.get("rank50_isolation",pd.Series(dtype=float)),) if "rank50_isolation" in h else np.nan,"price_recovery_rate":C.safe_mean(h.recover1s7),"rank_recovery_rate":np.nan})
 C.write_csv(pd.DataFrame(b),"25_BASKET_GEOMETRY_REBUILT.csv")
 tri=[]
 daily=q.groupby(["historical_date","rank_band"]).agg(A=("top500_breadth_30d","first"),B=("ret_1d","std"),C=("z1",lambda x:(x>=3).mean()),btc=("btc_ret_1d","first"),vol=("mkt_vol_30d","first")).reset_index()
 for band,g in daily.groupby("rank_band"):
  for x,y in [("A","B"),("B","C"),("A","C")]: tri.append({"rank_band":band,"relation":f"{x}-{y}","n":len(g),"metric":"pearson_correlation","value":g[x].corr(g[y])})
  mm=g.dropna();
  for target,cond in [("C","A"),("C","B"),("A","B")]:
   X=mm[[cond,"btc","vol"]].to_numpy(float); Y=mm[target].to_numpy(float); X=np.c_[np.ones(len(X)),X]; res=Y-X@np.linalg.lstsq(X,Y,rcond=None)[0]; tri.append({"rank_band":band,"relation":f"{target}|{cond},BTC,VOL","n":len(mm),"metric":"residual_variance_ratio","value":float(np.var(res)/np.var(Y)) if np.var(Y)>0 else np.nan})
 C.write_csv(pd.DataFrame(tri),"27_TRIANGLE_BREADTH_DISP_TAIL_REBUILT.csv")
 # Placeholder outputs for unavailable high-dimensional systems.
 C.write_csv(pd.DataFrame(columns=["sequence","n","periods","lift","status"]),"28_LOCAL_SEQUENCE_ATLAS.csv")
 C.write_csv(pd.DataFrame([{ "node":"TRUE_NEAREST_NEIGHBORS","verdict":"DATA_BLOCKED","reason":"LF2 cache has no complete PIT behavioral/correlation matrices"},{"node":"PRICE_VS_RANK_HEALTH_CLOCK","verdict":"DATA_BLOCKED","reason":"future rank observations unavailable in current cache"},{"node":"BREADTH_DISP_TAIL_TRIANGLE","verdict":"DESCRIPTIVE_ONLY","reason":"associational correlations/residual variance only"}]),"29_PROMOTE_MERGE_DISSOLVE.csv")
 C.write_csv(pd.DataFrame([{ "result":"behavioral_neighbors","status":"DATA_BLOCKED"},{"result":"correlation_neighbors","status":"DATA_BLOCKED"},{"result":"rank_health_future_clock","status":"DATA_BLOCKED"},{"result":"sector_chain_residual","status":"NULL_from_LF2"},{"result":"LF3_basket_absurd_dispersion","status":"REPAIRED_NOT_REUSED"}]),"30_NULL_AND_FAILED_RESULTS.csv")
 print('LF4 analysis outputs written')
def finite_std(s):
 x=C.finite(s).dropna(); return float(x.std()) if len(x)>1 else np.nan
if __name__=='__main__':main()
