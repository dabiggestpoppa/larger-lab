from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import lf4_common as C

def main():
 d=C.load_cache(); e=C.load_events(); e=C.add_forward(e)
 e=e[(e.z1>=2)&e.event_sign.ne(0)].copy(); e["event_index"]=e.index
 e["event_family"]=e["participation"].astype(str)+"_"+np.where(e.event_sign>0,"UP","DOWN")
 # Only same-band isolated downside events are primary loners.
 primary=e[(e.participation=="ISOLATED")&(e.event_sign<0)].copy()
 maps=[]
 for w in [25,50,100]:
  x=C.nearest_rank_context(d,primary,w); x=x.rename(columns={"rank_width":"width","n":"neighbor_n","median_ret":"neighbor_median_ret","same_sign":"neighbor_same_sign","tail_share":"neighbor_tail_share","dispersion":"neighbor_dispersion"})
  x["peer_family"]=f"RANK_{w}"; maps.append(x)
 rank=pd.concat(maps,ignore_index=True)
 # Per-event wide isolation panel.
 wide=primary[["event_index","historical_date","cmc_id","rank","rank_band","ret_1d","sigma_t0","z1","event_family","participation"]].copy()
 for w in [25,50,100]:
  x=rank[rank.peer_family.eq(f"RANK_{w}")].set_index("event_index")
  for c in ["neighbor_n","neighbor_median_ret","neighbor_same_sign","neighbor_tail_share","neighbor_dispersion"]:
   wide[f"rank{w}_{c}"]=x[c].reindex(wide.event_index).to_numpy()
  wide[f"rank{w}_isolation"]=1-wide[f"rank{w}_neighbor_same_sign"]
 # schema-reserved true peers: materialize only when exact PIT source is available.
 for c in ["behavioral_isolation","correlation_isolation","state_isolation","local_basket_residual"]: wide[c]=np.nan
 wide["behavior_peer_status"]="DATA_BLOCKED_MISSING_PRE_EVENT_FEATURES"
 wide["correlation_peer_status"]="DATA_BLOCKED_NO_TRAILING_RETURN_MATRIX"
 wide["state_peer_status"]="DATA_BLOCKED_NO_COMPLETE_STATE_BUCKETS"
 wide.to_parquet(C.RESULTS/"08_CONTEXTUAL_ISOLATION_PANEL.parquet",index=False)
 # Required peer map artifacts: rank map is valid; unavailable families are explicit empty schemas.
 rank.to_parquet(C.RESULTS/"04_RANK_NEIGHBORS.parquet",index=False)
 empty=pd.DataFrame(columns=["event_index","peer_id","distance","peer_return","peer_family","status"])
 for n in ["05_BEHAVIORAL_NEIGHBORS.parquet","06_CORRELATION_NEIGHBORS.parquet","07_STATE_NEIGHBORS.parquet"]: empty.to_parquet(C.RESULTS/n,index=False)
 # Quality audit.
 qr=[]
 for fam,g in rank.groupby("peer_family"):
  qr.append({"peer_family":fam,"status":"VALID","event_coverage":g.event_index.nunique()/max(1,primary.event_index.nunique()),"median_neighbor_count":g.neighbor_n.median(),"median_same_sign":g.neighbor_same_sign.median(),"overlap_stability":"NOT_ESTIMATED_OUT_OF_SAMPLE","out_of_sample_similarity":"NOT_AVAILABLE_FOR_SAME_DAY_RANK_MAP","missing_rate":g.neighbor_median_ret.isna().mean()})
 for fam in ["BEHAVIORAL","CORRELATION","STATE","LOCAL_BASKET"]:
  qr.append({"peer_family":fam,"status":"DATA_BLOCKED","event_coverage":0,"median_neighbor_count":np.nan,"median_same_sign":np.nan,"overlap_stability":"NOT_AVAILABLE","out_of_sample_similarity":"NOT_AVAILABLE","missing_rate":1})
 C.write_csv(pd.DataFrame(qr),"03_NEIGHBOR_MAP_QUALITY.csv")
 # Attach rank context and outcome paths.
 out=e.merge(wide[["event_index","rank50_neighbor_median_ret","rank50_neighbor_same_sign","rank50_neighbor_tail_share","rank50_neighbor_dispersion","rank50_isolation"]],on="event_index",how="left")
 for h in C.H:
  out[f"signed_fwd{h}"]=out.event_sign* C.finite(out[f"fwd{h}"])
  out[f"rev{h}"]=out[f"signed_fwd{h}"]<0
  out[f"recover1s{h}"]=out[f"signed_fwd{h}"]>=C.finite(out.sigma_t0)*np.sqrt(h)
  out[f"giveback{h}"]=np.clip(np.maximum(0,-out[f"signed_fwd{h}"])/C.finite(out.ret_1d).abs(),0,10)
 loner=out[(out.participation=="ISOLATED")&(out.event_sign<0)].copy()
 C.write_csv(loner,"04_ALL_LONER_OUTCOMES.csv")
 def paths(sign):
  q=loner[loner.event_sign.eq(sign)].copy(); rows=[]
  for h in [-30,-21,-14,-10,-7,-5,-3,-2,-1,0,1,2,3,5,7,10,14]:
   if h<0: continue
   col=f"signed_fwd{h}" if h else "ret_1d"
   if col not in q: continue
   rows.append({"sign":"DOWN" if sign<0 else "UP","horizon":h,"n":len(q),"median_asset_return":C.safe_mean(q[col]),"median_neighbor_return":C.safe_mean(q["rank50_neighbor_median_ret"]),"same_sign_share":C.safe_mean(q.rank50_neighbor_same_sign),"neighbor_tail_share":C.safe_mean(q.rank50_neighbor_tail_share),"neighbor_dispersion":C.safe_mean(q.rank50_neighbor_dispersion)})
  return rows
 C.write_csv(pd.DataFrame(paths(-1)+paths(1)),"11_NEIGHBOR_POST_EVENT_PATHS.csv")
 C.write_csv(pd.DataFrame([{**r,"window":"pre_event_not_available_in_rank_only_map"} for r in []]),"10_NEIGHBOR_PRE_EVENT_PATHS.csv")
 # False loner audit: rank-only isolated but >50% of rank neighbors same downside sign.
 fa=wide.copy(); fa["false_loner_50"]=fa.rank50_neighbor_same_sign>=.5
 rows=[]
 for b,g in fa.groupby("rank_band"):
  rows.append({"rank_band":b,"raw_rank_loners":len(g),"false_loner_n":int(g.false_loner_50.sum()),"false_loner_rate":g.false_loner_50.mean(),"definition":"rank-only isolated but >=50% rank-neighbor same-sign"})
 C.write_csv(pd.DataFrame(rows),"09_FALSE_LONER_AUDIT.csv")
 C.write_csv(pd.DataFrame([{"classification":"RANK_ONLY_ISOLATED","n":len(wide),"status":"DESCRIPTIVE_ONLY"},{"classification":"FALSE_LONER","n":int(fa.false_loner_50.sum()),"status":"DESCRIPTIVE_ONLY"}]),"12_LOCAL_CONTAGION_OUTCOMES.csv")
 print('LF4 build',len(d),len(e),len(primary))
if __name__=='__main__':main()
