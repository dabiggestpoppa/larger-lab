from __future__ import annotations
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent.parent; LF2=ROOT.parent/'lower_field_2'; LF3=ROOT.parent/'lower_field_3'; CACHE=LF2/'RESULTS'/'lf2_feature_frame.parquet'; EVENTS=LF3/'RESULTS'/'_lf3_events_internal.csv'
H=[1,2,3,5,7,10,14,21,30]
def finite(x): return pd.to_numeric(x,errors='coerce').replace([np.inf,-np.inf],np.nan)
def load_cache():
 d=pd.read_parquet(CACHE); d['historical_date']=pd.to_datetime(d['historical_date']); d=d.sort_values(['cmc_id','historical_date'],kind='stable'); d['z1']=finite(d.ret_1d).abs()/finite(d.sigma_t0).replace(0,np.nan); d['event_sign']=np.sign(d.ret_1d); return d
def load_events():
 e=pd.read_csv(EVENTS,low_memory=False); e['historical_date']=pd.to_datetime(e.historical_date); return e
def add_forward(e):
 e=e.copy()
 for h in H:
  f=f'fwd{h}'; src=f'fwd{h}_cum'
  if f not in e and src in e:e[f]=e[src]
  if f not in e: e[f]=np.nan
  e[f'signed_fwd{h}']=finite(e.event_sign)*finite(e[f]); e[f'rev{h}']=e[f'signed_fwd{h}']<0; e[f'giveback{h}']=np.clip(np.maximum(0,-e[f'signed_fwd{h}'])/finite(e.ret_1d).abs(),0,10); e[f'recover1s{h}']=e[f'signed_fwd{h}']>=finite(e.sigma_t0)*np.sqrt(h)
 return e
def safe_mean(x):
 x=finite(x).dropna(); return float(x.mean()) if len(x) else np.nan
