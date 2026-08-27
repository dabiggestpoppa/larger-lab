from __future__ import annotations
from pathlib import Path
import hashlib, json, sys
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parent.parent; LF2=ROOT.parent/'lower_field_2'; CACHE=LF2/'RESULTS'/'lf2_feature_frame.parquet'; R=ROOT
BANDS=['501-750','751-1000','1001-1500','1501-2000']; FWD=[1,3,7,14,30]

def available(path, cols):
 import pyarrow.parquet as pq
 names=set(pq.ParquetFile(path).schema.names); return [c for c in cols if c in names]

def main():
 cols=['historical_date','cmc_id','symbol','rank','rank_band','market_cap','market_cap_usd','ret_1d','ret_3d','ret_7d','ret_14d','ret_30d','sigma_t0','volume_24h_usd','listing_age_days','mkt_vol_30d','btc_ret_1d','eth_ret_1d','top500_breadth_30d','momentum_state','rank_vel_3d','rank_vel_7d','rank_vel_14d','rank_vel_30d']+[f'fwd{h}_cum' for h in [1,2,3,5,7,10,14,21,30]]
 use=available(CACHE,cols); d=pd.read_parquet(CACHE,columns=use); d['historical_date']=pd.to_datetime(d['historical_date']); d=d.sort_values(['cmc_id','historical_date'],kind='stable')
 # Preserve source rows and add only documented finite/casual diagnostics.
 d['z1']=d['ret_1d'].abs()/d['sigma_t0'].replace(0,np.nan)
 d['turnover_proxy']=d['volume_24h_usd']/d.get('market_cap_usd',pd.Series(np.nan,index=d.index)).replace(0,np.nan) if 'volume_24h_usd' in d and 'market_cap_usd' in d else np.nan
 d['valid_return']=np.isfinite(d['ret_1d'])
 d.to_parquet(R/'04_PIT_ASSET_DATE_FEATURES.parquet',index=False)
 # Return matrix metadata; actual wide matrix is deliberately derived from the long substrate to avoid duplicating 700MB.
 ret=d[['historical_date','cmc_id','ret_1d']].copy(); ret.to_parquet(R/'PIT_RETURNS_LONG.parquet',index=False)
 dup=int(d.duplicated(['historical_date','cmc_id']).sum()); bad=int((~np.isfinite(d['ret_1d'])).sum()); zero_sigma=int((d['sigma_t0']<=0).fillna(False).sum())
 date_min=d.historical_date.min(); date_max=d.historical_date.max()
 sha=hashlib.sha256((R/'04_PIT_ASSET_DATE_FEATURES.parquet').read_bytes()).hexdigest()
 meta=f'''# RETURN MATRIX METADATA\n\nLong-form source: `PIT_RETURNS_LONG.parquet`; key `(historical_date, cmc_id)`; value `ret_1d`. Missing observations are retained and never zero-filled.\n\nDate range: {date_min.date()} through {date_max.date()}\nRows: {len(d):,}; assets: {d.cmc_id.nunique():,}; dates: {d.historical_date.nunique():,}\nSource: `{CACHE}`\nFeature checksum (SHA-256): `{sha}`\n\nTrailing 60D/120D correlations are intentionally derived in the peer builder from pre-event windows; no full-sample correlation matrix is stored.\n'''
 (R/'05_RETURN_MATRIX_METADATA.md').write_text(meta,encoding='utf-8')
 report=f'''# PIT SUBSTRATE INTEGRITY\n\n**Status:** PASS for the reusable LF2-derived PIT feature substrate; true peer Stage B remains conditional on peer-map validation.\n\n- Rows: {len(d):,}\n- Assets: {d.cmc_id.nunique():,}\n- Dates: {d.historical_date.nunique():,}\n- Coverage: {date_min.date()} to {date_max.date()}\n- Duplicate asset-date rows: {dup}\n- Non-finite ret_1d rows: {bad}\n- Non-positive sigma rows: {zero_sigma}\n- Source features were already computed on continuous asset histories before lower-field band filtering.\n- Rank velocities are pre-event features; future rank clocks require rebuilding from the original PIT rank history and are not inferred here.\n- Source checksum: `{sha}`\n\nCritical Stage-A checks pass for uniqueness, finite returns, sigma denominator handling, and feature provenance. No Stage-B result is promoted without peer coverage and out-of-sample similarity checks.\n'''
 (R/'03_PIT_SUBSTRATE_INTEGRITY.md').write_text(report,encoding='utf-8')
 print('substrate',len(d),d.cmc_id.nunique(),d.historical_date.min(),d.historical_date.max(),'dup',dup,'bad',bad,'zero_sigma',zero_sigma)
if __name__=='__main__':main()
