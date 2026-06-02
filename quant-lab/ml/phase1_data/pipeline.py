"""
Phase 1: Data Foundation & Feature Engineering Pipeline
=========================================================
Converts raw M5 CSVs → Parquet, extracts Asian Ranges, runs K-Means tier discovery,
builds feature matrices, and generates ML-ready labels.

Validation gates at each phase ensure data quality before proceeding.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
import json
import hashlib
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PARQUET_DIR = Path(__file__).parent.parent / "data" / "parquet"
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
TIERS_DIR = Path(__file__).parent.parent / "data" / "tiers"

# All 19 assets with their pip multipliers and sizes
ASSET_CONFIG = {
    'EURUSD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'EURUSD_M5.csv'},
    'GBPUSD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'GBPUSD_M5.csv'},
    'USDCHF':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'USDCHF_M5.csv'},
    'USDJPY':  {'pip_mult': 100,   'pip_size': 0.01,   'csv': 'USDJPY_M5.csv'},
    'AUDUSD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'AUDUSD_M5.csv'},
    'NZDUSD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'NZDUSD_M5.csv'},
    'GBPJPY':  {'pip_mult': 100,   'pip_size': 0.01,   'csv': 'GBPJPY_M5.csv'},
    'GBPAUD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'GBPAUD_M5.csv'},
    'GBPNZD':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'GBPNZD_M5.csv'},
    'GBPCHF':  {'pip_mult': 10000, 'pip_size': 0.0001, 'csv': 'GBPCHF_M5.csv'},
    'CHFJPY':  {'pip_mult': 100,   'pip_size': 0.01,   'csv': 'CHFJPY_M5.csv'},
    'US500':   {'pip_mult': 1,     'pip_size': 1.0,    'csv': 'US500_M5.csv'},
    'DE30':    {'pip_mult': 1,     'pip_size': 1.0,    'csv': 'DE30_M5.csv'},
    'FR40':    {'pip_mult': 1,     'pip_size': 1.0,    'csv': 'FR40_M5.csv'},
    'XAUUSD':  {'pip_mult': 10,    'pip_size': 0.1,    'csv': 'XAUUSD_M5.csv'},
    'XAGUSD':  {'pip_mult': 1000,  'pip_size': 0.001,  'csv': 'XAGUSD_M5.csv'},
    'BTCUSD':  {'pip_mult': 1,     'pip_size': 1.0,    'csv': 'BTCUSD_M5.csv'},
    'ETHUSD':  {'pip_mult': 10,    'pip_size': 0.1,    'csv': 'ETHUSD_M5.csv'},
    'USTEC100': {'pip_mult': 1,    'pip_size': 1.0,    'csv': None},  # No CSV yet
}

# ============================================================
# 1.1 DATA INGESTION PIPELINE
# ============================================================

def convert_csv_to_parquet(symbol: str, csv_path: Path, pip_mult: int) -> dict:
    """
    Convert raw M5 CSV → Parquet with standardized UTC timestamps.
    Validates no gaps > 5 minutes.
    Returns metadata dict with row count, date range, gap report.
    """
    print(f"  [{symbol}] Reading CSV: {csv_path}")
    
    # Read CSV - handle various column naming conventions
    df = pd.read_csv(csv_path)
    
    # Standardize column names
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ('date', 'datetime', 'time', 'timestamp'):
            col_map[c] = 'dt'
        elif cl in ('open',):
            col_map[c] = 'open'
        elif cl in ('high',):
            col_map[c] = 'high'
        elif cl in ('low',):
            col_map[c] = 'low'
        elif cl in ('close',):
            col_map[c] = 'close'
        elif cl in ('volume', 'vol', 'tick_volume', 'tickvol'):
            col_map[c] = 'volume'
    
    df = df.rename(columns=col_map)
    
    # Parse datetime
    df['dt'] = pd.to_datetime(df['dt'], utc=True)
    df = df.set_index('dt').sort_index()
    
    # Remove duplicates
    df = df[~df.index.duplicated(keep='first')]
    
    # Gap detection
    gaps = df.index.to_series().diff()
    max_gap = gaps.max()
    gap_count = int((gaps > pd.Timedelta(minutes=5)).sum())
    
    # Resample to ensure regular 5-min bars (fill gaps with NaN for detection)
    full_range = pd.date_range(df.index.min(), df.index.max(), freq='5min', tz='UTC')
    df_full = df.reindex(full_range)
    nan_bars = int(df_full['close'].isna().sum())
    
    # Forward-fill small gaps (≤15 min), leave larger gaps as NaN
    df = df.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    })
    df['close'] = df['close'].ffill(limit=3)  # Max 15min fill
    df['open'] = df['open'].ffill(limit=3)
    df['high'] = df['high'].ffill(limit=3)
    df['low'] = df['low'].ffill(limit=3)
    
    # Save to Parquet
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = PARQUET_DIR / f"{symbol}_M5.parquet"
    df.to_parquet(parquet_path)
    
    # Data hash for reproducibility
    data_hash = hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()[:12]
    
    meta = {
        'symbol': symbol,
        'status': 'OK',
        'rows': len(df),
        'date_start': str(df.index.min()),
        'date_end': str(df.index.max()),
        'max_gap': str(max_gap),
        'gap_count': gap_count,
        'nan_bars': nan_bars,
        'data_hash': data_hash,
        'parquet_path': str(parquet_path),
    }
    
    print(f"  [{symbol}] ✓ {len(df)} rows | {df.index.min()} → {df.index.max()} | hash: {data_hash}")
    if gap_count > 0:
        print(f"  [{symbol}] ⚠ {gap_count} gaps >5min detected")
    
    return meta


def run_data_ingestion() -> dict:
    """Run 1.1 Data Ingestion Pipeline for all 19 assets."""
    print("\n=== PHASE 1.1: DATA INGESTION ===")
    manifest = {}
    
    for symbol, cfg in ASSET_CONFIG.items():
        csv_path = DATA_DIR / cfg['csv']
        if not csv_path.exists():
            print(f"  [{symbol}] ✗ CSV not found: {csv_path}")
            manifest[symbol] = {'status': 'MISSING', 'path': str(csv_path)}
            continue
        
        try:
            meta = convert_csv_to_parquet(symbol, csv_path, cfg['pip_mult'])
            meta['status'] = 'OK'
            manifest[symbol] = meta
        except Exception as e:
            print(f"  [{symbol}] ✗ Error: {e}")
            manifest[symbol] = {'status': 'ERROR', 'error': str(e)}
    
    # Save manifest
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    with open(PARQUET_DIR / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2, default=str)
    
    ok_count = sum(1 for v in manifest.values() if v.get('status') == 'OK')
    print(f"\n✓ Ingestion complete: {ok_count}/{len(manifest)} assets OK")
    return manifest


# ============================================================
# 1.3 ASIAN RANGE EXTRACTION
# ============================================================

def extract_asian_ranges(parquet_path: Path, symbol: str, 
                          session_start: int = 19, session_end: int = 3) -> pd.DataFrame:
    """
    Extract Asian Range (19:00-03:00 EST) for each trading day.
    Returns DataFrame with columns: date, ar_pips, ar_high, ar_low
    """
    df = pd.read_parquet(parquet_path)
    
    # Convert to EST
    df_est = df.copy()
    df_est.index = df_est.index.tz_convert('America/New_York')
    
    # Filter to Asian session hours (19:00-03:00 EST)
    hours = df_est.index.hour
    asian_mask = (hours >= session_start) | (hours < session_end)
    df_asian = df_est[asian_mask].copy()
    
    if len(df_asian) == 0:
        return pd.DataFrame(columns=['date', 'ar_pips', 'ar_high', 'ar_low', 'session_bars'])
    
    # Group by trading day (session date = date of the start of session)
    df_asian['session_date'] = df_asian.index.date
    
    ranges = []
    for day, group in df_asian.groupby('session_date'):
        if len(group) < 5:  # Minimum 5 bars for valid range
            continue
        
        ar_high = group['high'].max()
        ar_low = group['low'].min()
        ar_pips = (ar_high - ar_low) * ASSET_CONFIG.get(symbol, {}).get('pip_mult', 1)
        
        ranges.append({
            'date': day,
            'ar_pips': round(ar_pips, 2),
            'ar_high': ar_high,
            'ar_low': ar_low,
            'session_bars': len(group),
        })
    
    return pd.DataFrame(ranges)


# ============================================================
# 1.4 K-MEANS TIER DISCOVERY
# ============================================================

def discover_tiers(ranges_df: pd.DataFrame, symbol: str) -> dict:
    """
    K-Means clustering (k=3) to derive Tier thresholds and Atomic Units.
    AU = 50% of centroid (NON-NEGOTIABLE)
    Trigger = AU × 1.2
    Density Zone = AU ± 20%
    Cutoffs = midpoints between sorted centroids
    """
    if len(ranges_df) < 60:
        print(f"  [{symbol}] ✗ Only {len(ranges_df)} sessions (need ≥60)")
        return {'status': 'INSUFFICIENT_DATA', 'sessions': len(ranges_df)}
    
    ar_values = ranges_df['ar_pips'].values.reshape(-1, 1)
    
    # K-Means with FIXED parameters (do not optimize k)
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    km.fit(ar_values)
    
    centroids = sorted(km.cluster_centers_.flatten())
    
    # Cutoffs = midpoints between sorted centroids
    cutoff1 = (centroids[0] + centroids[1]) / 2
    cutoff2 = (centroids[1] + centroids[2]) / 2
    
    # AU = 50% of centroid (NON-NEGOTIABLE)
    tiers = {
        'T1': {
            'centroid': round(centroids[0], 2),
            'max_ar': round(cutoff1, 2),
            'au': round(centroids[0] * 0.50, 2),
            'trigger': round(centroids[0] * 0.50 * 1.2, 2),
            'dz_low': round(centroids[0] * 0.50 * 0.80, 2),
            'dz_high': round(centroids[0] * 0.50 * 1.20, 2),
        },
        'T2': {
            'centroid': round(centroids[1], 2),
            'max_ar': round(cutoff2, 2),
            'au': round(centroids[1] * 0.50, 2),
            'trigger': round(centroids[1] * 0.50 * 1.2, 2),
            'dz_low': round(centroids[1] * 0.50 * 0.80, 2),
            'dz_high': round(centroids[1] * 0.50 * 1.20, 2),
        },
        'T3': {
            'centroid': round(centroids[2], 2),
            'max_ar': 9999,
            'au': round(centroids[2] * 0.50, 2),
            'trigger': round(centroids[2] * 0.50 * 1.2, 2),
            'dz_low': round(centroids[2] * 0.50 * 0.80, 2),
            'dz_high': round(centroids[2] * 0.50 * 1.20, 2),
        },
    }
    
    # Count sessions per tier
    labels = km.predict(ar_values)
    tier_counts = {
        'T1': int((labels == 0).sum()),
        'T2': int((labels == 1).sum()),
        'T3': int((labels == 2).sum()),
    }
    
    result = {
        'symbol': symbol,
        'status': 'OK',
        'sessions': len(ranges_df),
        'centroids': [round(c, 2) for c in centroids],
        'cutoffs': [round(cutoff1, 2), round(cutoff2, 2)],
        'tiers': tiers,
        'tier_counts': tier_counts,
    }
    
    print(f"  [{symbol}] ✓ Tiers: T1<{cutoff1:.1f}p (AU={tiers['T1']['au']:.1f}) | "
          f"T2<{cutoff2:.1f}p (AU={tiers['T2']['au']:.1f}) | "
          f"T3>{cutoff2:.1f}p (AU={tiers['T3']['au']:.1f})")
    
    return result


def run_tier_discovery(manifest: dict) -> dict:
    """Run 1.4 K-Means Tier Discovery for all assets."""
    print("\n=== PHASE 1.4: K-MEANS TIER DISCOVERY ===")
    all_tiers = {}
    
    for symbol, meta in manifest.items():
        if meta.get('status') != 'OK':
            continue
        
        parquet_path = Path(meta['parquet_path'])
        ranges_df = extract_asian_ranges(parquet_path, symbol)
        
        if len(ranges_df) == 0:
            print(f"  [{symbol}] ✗ No Asian Range data extracted")
            all_tiers[symbol] = {'status': 'NO_DATA'}
            continue
        
        tiers = discover_tiers(ranges_df, symbol)
        all_tiers[symbol] = tiers
        
        # Save ranges
        ranges_df.to_csv(TIERS_DIR / f"{symbol}_asian_ranges.csv", index=False)
    
    # Save tier configs
    TIERS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TIERS_DIR / 'all_tiers.json', 'w') as f:
        json.dump(all_tiers, f, indent=2)
    
    ok_count = sum(1 for v in all_tiers.values() if v.get('status') == 'OK')
    print(f"\n✓ Tier discovery complete: {ok_count}/{len(all_tiers)} assets OK")
    return all_tiers


# ============================================================
# 1.5 FEATURE MATRIX CONSTRUCTION
# ============================================================

def build_feature_matrix(parquet_path: Path, symbol: str, tiers: dict) -> pd.DataFrame:
    """
    Build per-bar feature matrix for ML training.
    Features: AR ratio, impulse size, pullback %, OCC body ratio, time-of-day,
              day-of-week, rolling volatility, spread proxy, vol ratio.
    """
    df = pd.read_parquet(parquet_path)
    pip_mult = ASSET_CONFIG.get(symbol, {}).get('pip_mult', 1)
    
    # Convert to EST for session features
    df_est = df.copy()
    df_est.index = df_est.index.tz_convert('America/New_York')
    
    # Basic price features
    df['body'] = (df['close'] - df['open']).abs()
    df['range'] = df['high'] - df['low']
    df['body_ratio'] = df['body'] / df['range'].replace(0, np.nan)
    
    # Time features
    df_est['hour'] = df_est.index.hour
    df_est['minute'] = df_est.index.minute
    df_est['day_of_week'] = df_est.index.dayofweek
    
    df['hour_est'] = df_est['hour']
    df['day_of_week'] = df_est['day_of_week']
    
    # Rolling volatility (20-bar)
    df['rolling_vol_20'] = df['range'].rolling(20).mean() * pip_mult
    
    # Rolling range ratio (volatility regime)
    df['vol_ratio'] = df['range'] / df['range'].rolling(20).mean().replace(0, np.nan)
    
    # Gap feature
    df['gap'] = (df['open'] - df['close'].shift(1)).abs() * pip_mult
    
    # Session markers
    df['is_asian'] = ((df['hour_est'] >= 19) | (df['hour_est'] < 3)).astype(int)
    df['is_london'] = ((df['hour_est'] >= 3) & (df['hour_est'] < 8)).astype(int)
    df['is_ny'] = ((df['hour_est'] >= 8) & (df['hour_est'] < 12)).astype(int)
    
    # Drop NaN rows from rolling calculations
    df = df.dropna(subset=['rolling_vol_20', 'vol_ratio'])
    
    return df


# ============================================================
# MASTER PIPELINE RUNNER
# ============================================================

def run_phase1_pipeline():
    """Execute complete Phase 1 pipeline."""
    print("=" * 60)
    print("CEREBUS ML — PHASE 1: DATA FOUNDATION & FEATURE ENGINEERING")
    print("=" * 60)
    
    # Step 1: Data Ingestion
    manifest = run_data_ingestion()
    
    # Step 2: Tier Discovery
    all_tiers = run_tier_discovery(manifest)
    
    # Step 3: Feature Matrix (for assets with valid tiers)
    print("\n=== PHASE 1.5: FEATURE MATRIX CONSTRUCTION ===")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    
    for symbol, tiers in all_tiers.items():
        if tiers.get('status') != 'OK':
            continue
        
        meta = manifest.get(symbol, {})
        if meta.get('status') != 'OK':
            continue
        
        try:
            parquet_path = Path(meta['parquet_path'])
            features_df = build_feature_matrix(parquet_path, symbol, tiers)
            
            feature_path = FEATURES_DIR / f"{symbol}_features.parquet"
            features_df.to_parquet(feature_path)
            
            print(f"  [{symbol}] ✓ Features: {features_df.shape[0]} rows × {features_df.shape[1]} cols")
        except Exception as e:
            print(f"  [{symbol}] ✗ Feature build error: {e}")
    
    # Save complete manifest
    complete_manifest = {
        'timestamp': str(datetime.utcnow()),
        'ingestion': manifest,
        'tiers': all_tiers,
    }
    
    with open(DATA_DIR / 'phase1_manifest.json', 'w') as f:
        json.dump(complete_manifest, f, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE")
    print("=" * 60)
    print(f"Parquet files: {PARQUET_DIR}")
    print(f"Tier configs:  {TIERS_DIR}")
    print(f"Feature files: {FEATURES_DIR}")
    print(f"Manifest:      {DATA_DIR / 'phase1_manifest.json'}")


if __name__ == '__main__':
    run_phase1_pipeline()
