import pandas as pd
from pathlib import Path

feat_dir = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\ml\data\features')
files = sorted(feat_dir.glob("*_features.parquet"))

for f in files:
    df = pd.read_parquet(f)
    symbol = f.stem.replace('_features', '')
    cols = list(df.columns)
    # Check for label columns
    has_regime = 'regime_label' in cols
    has_quality = 'entry_quality_score' in cols
    
    # Check for regime classifier features
    regime_feats = ['asian_range_pips', 'vol_ratio_3am_9am', 'hour_est', 'spread_vs_20d_avg', 
                     'impulse_to_ar_ratio', 'day_of_week', 'consecutive_losses', 'prior_session_wr']
    avail_regime = [c for c in regime_feats if c in cols]
    
    # Check for entry scorer features
    entry_feats = ['pullback_pct', 'occ_body_to_au_ratio', 'time_since_impulse_min',
                   'volume_spike_ratio', 'regime_confidence', 'distance_to_dz_center',
                   'prior_loop_outcome', 'spread_at_entry']
    avail_entry = [c for c in entry_feats if c in cols]
    
    print(f"{symbol:10s} | rows={len(df):6d} | regime_feat={len(avail_regime)}/8 | entry_feat={len(avail_entry)}/8 | regime_label={has_regime} | quality={has_quality}")
