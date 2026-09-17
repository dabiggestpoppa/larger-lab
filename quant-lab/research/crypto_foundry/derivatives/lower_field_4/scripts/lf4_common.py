from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LF3 = ROOT.parent / "lower_field_3"
LF2 = ROOT.parent / "lower_field_2"
RESULTS = ROOT
RESULTS.mkdir(exist_ok=True)
CACHE = LF2 / "RESULTS" / "lf2_feature_frame.parquet"
EVENTS = LF3 / "RESULTS" / "_lf3_events_internal.csv"
BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
H = [1,2,3,5,7,10,14,21,30]
FWD = {h:f"fwd{h}_cum" for h in H}
RANK_H = [3,7,14,30]

BASE_COLS = ["historical_date","cmc_id","rank","rank_band","ret_1d","sigma_t0",
 "market_cap","market_cap_usd","volume_24h_usd","listing_age_days","mkt_vol_30d",
 "btc_ret_1d","eth_ret_1d","top500_breadth_30d","momentum_state",
 "rank_vel_3d","rank_vel_7d","rank_vel_14d","rank_vel_30d"] + list(FWD.values())

def available(path, cols):
    import pyarrow.parquet as pq
    names=set(pq.ParquetFile(path).schema.names)
    return [c for c in cols if c in names]

def load_cache():
    cols=available(CACHE, BASE_COLS)
    d=pd.read_parquet(CACHE, columns=cols)
    d["historical_date"]=pd.to_datetime(d["historical_date"])
    d=d.sort_values(["cmc_id","historical_date"], kind="stable")
    d["z1"]=d["ret_1d"].abs()/d["sigma_t0"].replace(0,np.nan)
    d["event_sign"]=np.sign(d["ret_1d"])
    return d

def load_events():
    e=pd.read_csv(EVENTS, low_memory=False)
    e["historical_date"]=pd.to_datetime(e["historical_date"])
    for c in ["z1","event_sign","ret_1d","sigma_t0"]:
        if c in e: e[c]=pd.to_numeric(e[c], errors="coerce")
    return e

def finite(s):
    return pd.to_numeric(s, errors="coerce").replace([np.inf,-np.inf],np.nan)

def safe_mean(s):
    x=finite(s).dropna(); return float(x.mean()) if len(x) else np.nan

def cohend(a,b):
    a=finite(a).dropna(); b=finite(b).dropna()
    if len(a)<2 or len(b)<2:return np.nan
    den=np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2)
    return float((a.mean()-b.mean())/den) if den>0 else np.nan

def periods(s): return pd.to_datetime(s).dt.to_period("Q").astype(str)

def nearest_rank_context(d, events, width):
    rows=[]
    # Efficient same-date rank join for event rows; only event-date pairs are materialized.
    cols=["historical_date","cmc_id","rank","ret_1d","z1"]
    base=d[cols].dropna(subset=["historical_date","rank"])
    for date,g in events.groupby("historical_date", sort=False):
        n=base[base.historical_date.eq(date)]
        if n.empty: continue
        for idx,r in g.iterrows():
            q=n[(n["cmc_id"]!=r["cmc_id"]) & (n["rank"].sub(r["rank"]).abs()<=width)]
            rr=finite(q.ret_1d); zz=finite(q.z1)
            rows.append({"event_index":idx,"rank_width":width,"n":int(rr.notna().sum()),
             "median_ret":safe_mean(rr) if len(rr) else np.nan,
             "same_sign":float((np.sign(rr)==r.event_sign).mean()) if len(rr) else np.nan,
             "tail_share":float((zz>=2).mean()) if len(zz) else np.nan,
             "dispersion":float(rr.std()) if rr.notna().sum()>1 else np.nan})
    return pd.DataFrame(rows)

def add_forward(e):
    e=e.copy()
    for h in H:
        f=f"fwd{h}"
        if f not in e and FWD[h] in e: e[f]=e[FWD[h]]
        e[f"signed_fwd{h}"]=e.event_sign*finite(e[f])
        e[f"rev{h}"]=e[f"signed_fwd{h}"]<0
        e[f"giveback{h}"]=np.clip(np.maximum(0,-e[f"signed_fwd{h}"])/finite(e.ret_1d).abs(),0,10)
        e[f"recover1s{h}"]=e[f"signed_fwd{h}"]>=finite(e.sigma_t0)*np.sqrt(h)
    return e

def write_csv(df,name):
    df.to_csv(RESULTS/name,index=False)
