from __future__ import annotations
from pathlib import Path
import pandas as pd,numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent)); import lf5_common as C
R=Path(__file__).resolve().parent.parent

def main():
 e=C.add_forward(C.load_events()); e=e[(e.z1>=2)&e.event_sign.ne(0)].copy(); e['event_index']=e.index
 p=e[(e.participation=='ISOLATED')&(e.event_sign<0)].copy()
 rank=pd.read_parquet(R/'07_RANK_PEERS.parquet'); rank=rank[rank.peer_family.eq('RANK_50')]
 agg=rank.groupby('event_index').agg(peer_median=('peer_return','median'),peer_dispersion=('peer_return','std'),peer_same_sign=('peer_return',lambda x:np.nan)).reset_index()
 out=p.merge(agg,on='event_index',how='left'); out['rank_isolation']=out.ret_1d-out.peer_median
 # rank-only event audit and peer categories; unavailable true peers remain explicit.
 rows=[]
 for b,g in out.groupby('rank_band'):
  rows.append({'rank_band':b,'threshold':'z1>=2','rank_only_loners':len(g),'peer_matched':g.peer_median.notna().sum(),'peer_false_loner':np.nan,'true_multi_peer_loner':np.nan,'status':'DATA_BLOCKED_TRUE_PEER_ATTRIBUTION'})
 pd.DataFrame(rows).to_csv(R/'12_TRUE_FALSE_LONER_AUDIT.csv',index=False)
 # post paths based on frozen rank peer return is descriptive only; no future rematching.
 path=[]
 for h in [1,2,3,5,7,10,14]:
  for b,g in out.groupby('rank_band'):
   path.append({'rank_band':b,'horizon':f'{h}D','n':len(g),'asset_median_signed_return':C.safe_mean(g[f'signed_fwd{h}']),'frozen_peer_median_return':C.safe_mean(g.peer_median),'asset_peer_residual':C.safe_mean(g[f'signed_fwd{h}']-g.peer_median),'classification':'RANK_PEER_DESCRIPTIVE_ONLY'})
 pd.DataFrame(path).to_csv(R/'15_POST_EVENT_PEER_PATHS.csv',index=False)
 pd.DataFrame([{'classification':'TRUE_PEER_CONTAGION','n':0,'status':'DATA_BLOCKED'},{'classification':'RANK_CONTEXT_ONLY','n':len(out),'status':'DESCRIPTIVE_ONLY'},{'classification':'PEER_NORMALIZATION','n':0,'status':'DATA_BLOCKED'}]).to_csv(R/'16_PEER_CONTAGION_NORMALIZATION.csv',index=False)
 # recovery clock using corrected signed cumulative semantics inherited from LF2.
 rc=[]
 for b,g in p.groupby('rank_band'):
  for label,m in [('1SIGMA_BY_1D',g.recover1s1),('1SIGMA_BY_2D',g.recover1s2),('1SIGMA_BY_3D',g.recover1s3),('1SIGMA_BY_5D',g.recover1s5),('1SIGMA_BY_7D',g.recover1s7),('NO_1SIGMA_BY_7D',~g.recover1s7)]:
   q=g[m]; rc.append({'rank_band':b,'class':label,'n':len(q),'p_full_reversal_7d':C.safe_mean(q.rev7),'p_new_low_proxy_7d':C.safe_mean(~q.recover1s7),'p_peer_normalization':np.nan,'status':'DESCRIPTIVE_PRICE_ONLY'})
 pd.DataFrame(rc).to_csv(R/'19_ONE_SIGMA_RECOVERY_CLOCK.csv',index=False)
 # Price/rank split requires future ranks absent.
 for fn in ['20_PRICE_RECOVERY_CLOCK.csv','21_RANK_HEALTH_CLOCK.csv','22_PRICE_RANK_HEALTH_MATRIX.csv','23_HEALTH_STRESS_RESPONSE.csv']:
  pd.DataFrame([{'status':'DATA_BLOCKED','reason':'future PIT rank history unavailable in LF2-derived source cache'}]).to_csv(R/fn,index=False)
 # reconciliation and liquidity/asymmetry.
 pd.DataFrame([{'comparison':'MECH7_vs_LF3','common_event_gate':'not reproducible from available MECH7 event export','rank_sign':'requires source-level audit','purge':'not applied here','adjudication':'UNRESOLVED_DATA_BLOCKED'}]).to_csv(R/'24_RANK_DETERIORATION_RECONCILIATION.csv',index=False)
 a=[]
 for k,g in e.groupby(['rank_band','participation','event_sign_label']): a.append({'rank_band':k[0],'participation':k[1],'sign':k[2],'n':len(g),'p_reversal7':C.safe_mean(g.rev7),'p_recovery1s7':C.safe_mean(g.recover1s7),'p_giveback50':C.safe_mean(g.giveback7>=.5),'status':'DESCRIPTIVE_PEER_CONTROL_NOT_AVAILABLE'})
 pd.DataFrame(a).to_csv(R/'26_BROAD_UP_DOWN_PEER_CONTROLLED.csv',index=False)
 pd.DataFrame([{'status':'DATA_BLOCKED','reason':'joint controlled shock-absorption model and peer-relative volume unavailable'}]).to_csv(R/'25_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv',index=False)
 pd.DataFrame([{'state':'HH','status':'DESCRIPTIVE_ONLY','true_loner_frequency':np.nan,'peer_stress':np.nan},{'state':'HL','status':'DESCRIPTIVE_ONLY'},{'state':'LH','status':'DESCRIPTIVE_ONLY'},{'state':'LL','status':'DESCRIPTIVE_ONLY'}]).to_csv(R/'27_HH_TRUE_PEER_ANATOMY.csv',index=False)
 # repaired basket finite raw-return summaries.
 baskets=[]
 for name,g in {'TRUE_LONER':out,'EARLY_1SIGMA':p[p.recover1s3],'NO_1SIGMA':p[~p.recover1s7],'COORDINATED_UP':e[(e.event_sign>0)&e.participation.isin(['BAND_BROAD','MULTI_BAND'])]}.items():
  for b,h in g.groupby('rank_band'): baskets.append({'basket':name,'rank_band':b,'n':len(h),'median_return':C.safe_mean(h.ret_1d),'dispersion':C.safe_mean(h.ret_1d.abs()),'breadth':C.safe_mean(h.ret_1d>0),'tail_share':C.safe_mean(h.z1>=3),'internal_correlation':np.nan,'peer_normalization_rate':np.nan,'status':'DESCRIPTIVE_ONLY'})
 pd.DataFrame(baskets).to_csv(R/'28_REPAIRED_LOCAL_BASKET_GEOMETRY.csv',index=False)
 tri=[]; q=e.groupby(['historical_date','rank_band']).agg(A=('top500_breadth_30d','first'),B=('ret_1d','std'),C=('z1',lambda x:(x>=3).mean()),btc=('btc_ret_1d','first'),vol=('mkt_vol_30d','first')).reset_index()
 for b,g in q.groupby('rank_band'):
  for x,y in [('A','B'),('B','C'),('A','C')]: tri.append({'rank_band':b,'relation':f'{x}-{y}','metric':'pearson_correlation','value':g[x].corr(g[y]),'n':len(g)})
 pd.DataFrame(tri).to_csv(R/'29_TRIANGLE_TRUE_PEER_DISPERSION.csv',index=False)
 pd.DataFrame([{'sequence':'PEER_DIVERGENCE -> TRUE_LONER -> RECOVERY','status':'DATA_BLOCKED','n':0},{'sequence':'HH -> TRUE_LONER -> NORMALIZATION','status':'DATA_BLOCKED','n':0}]).to_csv(R/'30_LOCAL_SEQUENCE_ATLAS.csv',index=False)
 print('analysis complete',len(out))
if __name__=='__main__':main()
