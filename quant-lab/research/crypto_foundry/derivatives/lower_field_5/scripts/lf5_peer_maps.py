from __future__ import annotations
from pathlib import Path
import sys, numpy as np, pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import lf5_common as C

ROOT=Path(__file__).resolve().parent.parent; R=ROOT

def norm_features(g, cols):
 x=g[cols].apply(pd.to_numeric,errors='coerce'); scale=x.sub(x.median()).abs().median().replace(0,np.nan); return (x-x.median())/(scale+1e-12)

def main():
 d=C.load_cache(); e=C.add_forward(C.load_events()); e=e[(e.z1>=2)&e.event_sign.ne(0)].copy(); e['event_index']=e.index
 events=e[(e.participation=='ISOLATED')&(e.event_sign<0)].copy()
 # Rank peer maps across required windows.
 rankrows=[]
 for date,g in events.groupby('historical_date',sort=False):
  n=d[d.historical_date.eq(date)]
  for idx,a in g.iterrows():
   for w in [25,50,100]:
    q=n[(n.cmc_id!=a.cmc_id)&(n['rank'].sub(a['rank']).abs()<=w)]
    for _,p in q.iterrows(): rankrows.append({'event_index':idx,'asset_id':a.cmc_id,'peer_id':p.cmc_id,'peer_family':f'RANK_{w}','distance':abs(float(p['rank'])-float(a['rank'])),'peer_return':p.ret_1d,'valid_overlap':np.nan})
 rank=pd.DataFrame(rankrows); rank.to_parquet(R/'07_RANK_PEERS.parquet',index=False)
 # Behavioral matching: use only pre-event state columns present in cache. Same-date rows are PIT-safe.
 bcols=[c for c in ['rank','market_cap_usd','volume_24h_usd','listing_age_days','mkt_vol_30d','ret_3d','ret_30d'] if c in d.columns]
 behrows=[]; beh_status='VALID' if len(bcols)>=5 else 'DATA_BLOCKED'
 if beh_status=='VALID':
  for date,g in events.groupby('historical_date',sort=False):
   n=d[d.historical_date.eq(date)].copy(); X=norm_features(n,bcols); X.index=n.index
   for idx,a in g.iterrows():
    if idx not in X.index: continue
    dist=((X-X.loc[idx]).pow(2).sum(axis=1,min_count=1)).pow(.5); dist.loc[idx]=np.nan
    for k in [5,10,20]:
     ids=dist.nsmallest(k).dropna().index
     for pid in ids: behrows.append({'event_index':idx,'asset_id':a.cmc_id,'peer_id':n.loc[pid,'cmc_id'],'peer_family':f'BEHAVIORAL_{k}','distance':dist.loc[pid],'peer_return':n.loc[pid,'ret_1d'],'valid_overlap':np.nan})
 beh=pd.DataFrame(behrows,columns=['event_index','asset_id','peer_id','peer_family','distance','peer_return','valid_overlap']); beh.to_parquet(R/'08_BEHAVIORAL_PEERS.parquet',index=False)
 # Correlation peers are derived from pre-event return history if the reusable long substrate can be loaded.
 corrrows=[]; corr_status='VALID'
 dates=pd.Index(sorted(d.historical_date.dropna().unique())); ids=d.cmc_id.dropna().unique()
 # Full pairwise event-date correlation is intentionally avoided unless enough observations; use a bounded same-date candidate set.
 # Current cache has only event-date rows and no prior return matrix in memory after Stage A; mark explicit blocked rather than fabricate.
 corr_status='DATA_BLOCKED_NO_PRE_EVENT_MATRIX_IN_CURRENT_CACHE'
 pd.DataFrame(columns=['event_index','asset_id','peer_id','peer_family','correlation','overlap','lookback']).to_parquet(R/'09_CORRELATION_PEERS.parquet',index=False)
 # State peers where state labels exist; same-date same-band/state is valid descriptive peer family.
 strows=[]; state_status='VALID' if 'momentum_state' in d.columns else 'DATA_BLOCKED'
 if state_status=='VALID':
  for date,g in events.groupby('historical_date',sort=False):
   n=d[d.historical_date.eq(date)]
   for idx,a in g.iterrows():
    q=n[(n.cmc_id!=a.cmc_id)&n.momentum_state.eq(a.get('momentum_state',np.nan))&n.rank_band.eq(a.rank_band)]
    for _,p in q.iterrows(): strows.append({'event_index':idx,'asset_id':a.cmc_id,'peer_id':p.cmc_id,'peer_family':'STATE','distance':np.nan,'peer_return':p.ret_1d,'valid_overlap':np.nan})
 pd.DataFrame(strows,columns=['event_index','asset_id','peer_id','peer_family','distance','peer_return','valid_overlap']).to_parquet(R/'10_STATE_PEERS.parquet',index=False)
 # Hybrid uses behavioral peer records only when behavioral matching succeeded.
 hyb=beh[beh.peer_family.isin(['BEHAVIORAL_10','BEHAVIORAL_20'])].copy(); hyb['peer_family']='HYBRID_LOCAL_BASKET'; hyb.to_parquet(R/'11_HYBRID_LOCAL_BASKETS.parquet',index=False)
 def quality(name,df,status):
  return {'peer_family':name,'status':status,'event_coverage':df.event_index.nunique()/max(1,events.event_index.nunique()) if len(df) else 0,'median_peer_count':df.groupby('event_index').size().median() if len(df) else np.nan,'membership_turnover':'NOT_ESTIMATED' if status!='DATA_BLOCKED' else 'NOT_AVAILABLE','jaccard_persistence':'NOT_ESTIMATED','pre_event_similarity':df.groupby('event_index').distance.mean().median() if len(df) and 'distance' in df else np.nan,'next_window_similarity':'NOT_ESTIMATED','basket_correlation':'NOT_ESTIMATED','missing_rate':df.peer_return.isna().mean() if len(df) else 1}
 rows=[quality('RANK_25',rank[rank.peer_family.eq('RANK_25')],'VALID'),quality('RANK_50',rank[rank.peer_family.eq('RANK_50')],'VALID'),quality('RANK_100',rank[rank.peer_family.eq('RANK_100')],'VALID'),quality('BEHAVIORAL',beh,beh_status),quality('CORRELATION',pd.DataFrame(),corr_status),quality('STATE',pd.DataFrame(strows),state_status),quality('HYBRID_LOCAL_BASKET',hyb,'VALID_WITH_LIMITATIONS' if len(hyb) else 'DATA_BLOCKED')]
 pd.DataFrame(rows).to_csv(R/'06_PEER_MAP_QUALITY.csv',index=False)
 print('peer maps',len(events),len(rank),len(beh),len(strows),beh_status,corr_status)
if __name__=='__main__':main()
