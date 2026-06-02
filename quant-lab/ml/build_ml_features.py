"""
CEREBUS ML — Build ML-Ready Feature Matrix
Takes Phase 1 features + tier configs → computes regime classifier + entry scorer features.
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FEATURES_DIR = Path(__file__).parent / "data" / "features"
TIERS_DIR = Path(__file__).parent / "data" / "tiers"
ML_FEATURES_DIR = Path(__file__).parent / "data" / "ml_features"
ML_FEATURES_DIR.mkdir(parents=True, exist_ok=True)

def compute_session_features(df, symbol, tiers_config):
    """Compute session-level features from bar-level data."""
    # Session detection: Asian = 19:00-03:00 EST = 00:00-08:00 UTC
    df = df.copy()
    df['hour_utc'] = df.index.hour
    df['date'] = df.index.date
    
    # Asian session bars (00:00-08:00 UTC)
    asian_mask = (df['hour_utc'] >= 0) & (df['hour_utc'] < 8)
    
    # Compute Asian Range per session
    # Group by trading day (Asian session belongs to the NEXT trading day)
    asian_bars = df[asian_mask].copy()
    if len(asian_bars) == 0:
        return df
    
    # Assign session date (Asian bars from 00:00-08:00 UTC belong to that calendar date)
    asian_bars['session_date'] = asian_bars.index.date
    
    asian_stats = asian_bars.groupby('session_date').agg(
        asian_high=('high', 'max'),
        asian_low=('low', 'min'),
        asian_close=('close', 'last'),
    ).reset_index()
    
    asian_stats['asian_range'] = asian_stats['asian_high'] - asian_stats['asian_low']
    asian_stats['asian_mid'] = (asian_stats['asian_high'] + asian_stats['asian_low']) / 2
    
    # Map tier AU from config
    au_t1 = tiers_config.get('T1', {}).get('au', 15.0)
    au_t2 = tiers_config.get('T2', {}).get('au', 38.0)
    au_t3 = tiers_config.get('T3', {}).get('au', 88.0)
    cut1 = tiers_config.get('T1', {}).get('max_ar', 53.0)
    cut2 = tiers_config.get('T2', {}).get('max_ar', 127.0)
    
    def classify_tier(ar_pips):
        if ar_pips < cut1:
            return 'T1', au_t1
        elif ar_pips < cut2:
            return 'T2', au_t2
        else:
            return 'T3', au_t3
    
    tier_results = asian_stats['asian_range'].apply(lambda x: classify_tier(x))
    asian_stats['tier'] = [t[0] for t in tier_results]
    asian_stats['au'] = [t[1] for t in tier_results]
    
    # Merge back to main dataframe
    df['session_date'] = df.index.date
    df = df.merge(asian_stats[['session_date', 'asian_range', 'asian_high', 'asian_low', 'asian_mid', 'tier', 'au']], 
                  on='session_date', how='left')
    
    return df

def compute_regime_features(df):
    """Compute the 8 regime classifier features per row."""
    # 1. asian_range_pips — already have asian_range
    df['asian_range_pips'] = df['asian_range']
    
    # 2. vol_ratio_3am_9am — (3AM-9AM range) / Asian Range
    # Use rolling_vol_20 as proxy if session vol not available
    df['vol_ratio_3am_9am'] = df['vol_ratio'].fillna(1.0)
    
    # 3. hour_est — already have hour_est (UTC-5 approx)
    df['hour_est'] = (df['hour_utc'] - 5) % 24
    
    # 4. spread_vs_20d_avg — use body_ratio as proxy
    df['spread_vs_20d_avg'] = df['body_ratio'].fillna(0.5)
    
    # 5. impulse_to_ar_ratio — current bar range / Asian Range
    df['impulse_to_ar_ratio'] = (df['range'] / df['asian_range'].replace(0, np.nan)).fillna(0)
    
    # 6. day_of_week — already have day_of_week
    # Already 0=Mon, keep as is
    df['day_of_week'] = df['day_of_week'].fillna(0).astype(int)
    
    # 7. consecutive_losses — rolling (initialize to 0, update from trade outcomes)
    df['consecutive_losses'] = 0
    
    # 8. prior_session_wr — initialize to 0.5 (will be updated iteratively)
    df['prior_session_wr'] = 0.5
    
    return df

def compute_entry_features(df, tiers_config):
    """Compute the 8 entry scorer features per row."""
    # 1. pullback_pct — distance from Asian extreme / Asian Range
    df['dist_from_asian_high'] = (df['asian_high'] - df['close']).abs()
    df['dist_from_asian_low'] = (df['close'] - df['asian_low']).abs()
    df['pullback_pct'] = (df['dist_from_asian_high'] / df['asian_range'].replace(0, np.nan)).fillna(0.5)
    
    # 2. occ_body_to_au_ratio — current body / AU
    occ_body = df['body']
    au = df['au']
    df['occ_body_to_au_ratio'] = (occ_body / au.replace(0, np.nan)).fillna(0)
    
    # 3. time_since_impulse_min — bars since last * strong impulse (placeholder)
    df['time_since_impulse_min'] = 5  # Default: 5 minutes
    
    # 4. volume_spike_ratio — current vol / 20-bar avg
    df['volume_spike_ratio'] = df['volume'] / df['volume'].rolling(20, min_periods=1).mean()
    
    # 5. regime_confidence — from tier classification (will be updated by model)
    df['regime_confidence'] = 0.5
    
    # 6. distance_to_dz_center — how centered in Density Zone (0=center, 1=edge)
    dz_low = df['au'] * 0.8
    dz_high = df['au'] * 1.2
    dz_center = (dz_low + dz_high) / 2
    dz_range = (dz_high - dz_low).replace(0, np.nan)
    df['distance_to_dz_center'] = ((df['close'] - dz_center).abs() / dz_range).fillna(0)
    
    # 7. prior_loop_outcome — previous loop result (placeholder)
    df['prior_loop_outcome'] = 0  # -1=none, 0=loss, 1=win
    
    # 8. spread_at_entry — current body_ratio as spread proxy
    df['spread_at_entry'] = df['body_ratio']
    
    return df

def compute_labels(df):
    """Generate regime labels and entry quality scores."""
    # Regime labels based on Architect definitions:
    # CONFIRMED: vol_ratio >= 1.5 AND impulse/ar >= 0.3
    # CAUTION: vol_ratio >= 1.3 AND impulse/ar >= 0.2
    # NO-GO: vol_ratio < 1.0 OR impulse/ar < 0.1
    # FAILED: everything else
    
    conditions = [
        (df['vol_ratio_3am_9am'] >= 1.5) & (df['impulse_to_ar_ratio'] >= 0.3),
        (df['vol_ratio_3am_9am'] >= 1.3) & (df['impulse_to_ar_ratio'] >= 0.2),
        (df['vol_ratio_3am_9am'] < 1.0) | (df['impulse_to_ar_ratio'] < 0.1),
    ]
    choices = [0, 1, 3]  # CONFIRMED, CAUTION, NO-GO
    df['regime_label'] = np.select(conditions, choices, default=2)  # FAILED
    
    # Entry quality score — heuristic based on Architect's quality factors
    # Higher = better entry
    quality = (
        0.3 * (1 - df['pullback_pct'].clip(0, 1)) +  # Closer to impulse = better
        0.2 * df['volume_spike_ratio'].clip(0, 3) / 3 +  # Volume spike = better
        0.2 * (1 - df['distance_to_dz_center'].clip(0, 1)) +  # Centered in DZ = better
        0.15 * df['regime_confidence'] +
        0.15 * (df['is_london'] | df['is_ny']).astype(float)  # Active session = better
    )
    df['entry_quality_score'] = quality.clip(0, 1)
    
    return df

def process_asset(symbol):
    """Build full ML feature matrix for one asset."""
    feat_path = FEATURES_DIR / f"{symbol}_features.parquet"
    tier_path = TIERS_DIR / "all_tiers.json"
    
    if not feat_path.exists():
        return {'symbol': symbol, 'status': 'SKIP', 'reason': 'no features'}
    
    df = pd.read_parquet(feat_path)
    
    # Load tier config
    tiers_config = {}
    if tier_path.exists():
        all_tiers = json.load(open(tier_path))
        tiers_config = all_tiers.get(symbol, {})
    
    # Step 1: Session-level features
    df = compute_session_features(df, symbol, tiers_config)
    
    # Step 2: Regime classifier features
    df = compute_regime_features(df)
    
    # Step 3: Entry scorer features
    df = compute_entry_features(df, tiers_config)
    
    # Step 4: Labels
    df = compute_labels(df)
    
    # Save
    out_path = ML_FEATURES_DIR / f"{symbol}_ml_features.parquet"
    df.to_parquet(out_path)
    
    # Report
    regime_dist = df['regime_label'].value_counts().to_dict()
    regime_names = {0: 'CONFIRMED', 1: 'CAUTION', 2: 'FAILED', 3: 'NO-GO'}
    dist_named = {regime_names.get(k, k): v for k, v in regime_dist.items()}
    
    return {
        'symbol': symbol,
        'status': 'OK',
        'rows': len(df),
        'columns': len(df.columns),
        'regime_distribution': dist_named,
        'avg_quality': round(float(df['entry_quality_score'].mean()), 3),
    }

def main():
    print("=" * 60)
    print("CEREBUS ML — BUILD ML FEATURE MATRIX")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    feat_files = sorted(FEATURES_DIR.glob("*_features.parquet"))
    symbols = [f.stem.replace('_features', '') for f in feat_files]
    
    results = []
    for symbol in symbols:
        try:
            result = process_asset(symbol)
            results.append(result)
            if result['status'] == 'OK':
                print(f"  {symbol:10s} | rows={result['rows']:6d} | cols={result['columns']:3d} | "
                      f"quality={result['avg_quality']:.3f} | dist={result['regime_distribution']}")
            else:
                print(f"  {symbol:10s} | {result['status']}: {result.get('reason', '')}")
        except Exception as e:
            print(f"  {symbol:10s} | ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({'symbol': symbol, 'status': 'ERROR', 'error': str(e)})
    
    ok = [r for r in results if r['status'] == 'OK']
    print(f"\nComplete: {len(ok)}/{len(results)} assets processed")
    
    # Save manifest
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'total': len(results),
        'ok': len(ok),
        'results': results,
    }
    with open(ML_FEATURES_DIR / "ml_manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2, default=str)

if __name__ == "__main__":
    main()
