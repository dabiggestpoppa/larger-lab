"""
CEREBUS ML — End-to-End Pipeline Runner
Runs Phase 1 (data) → Phase 2 (train) → Phase 3 (optimize)
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 60)
    print("CEREBUS ML — END-TO-END PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── PHASE 1: Data Foundation ────────────────────────────
    print("\n[PHASE 1] Data Foundation & Feature Engineering")
    print("-" * 40)
    
    from quant_lab.ml.phase1_data.pipeline import (
        convert_csv_to_parquet, extract_asian_ranges, discover_tiers,
        build_feature_matrix, generate_labels, DATA_DIR, PARQUET_DIR, FEATURES_DIR, TIERS_DIR
    )
    
    from quant_lab.ml.phase1_data.pipeline import ASSET_CONFIG
    
    phase1_results = []
    for symbol, cfg in ASSET_CONFIG.items():
        csv_name = cfg.get('csv')
        if not csv_name:
            print(f"  [{symbol}] SKIP — no CSV configured")
            continue
        
        csv_path = DATA_DIR / csv_name
        if not csv_path.exists():
            # Try alternate names
            alt_names = [f"{symbol}_M5.csv", f"{symbol}.csv", f"{symbol}PRO_M5.csv"]
            found = False
            for alt in alt_names:
                if (DATA_DIR / alt).exists():
                    csv_path = DATA_DIR / alt
                    found = True
                    break
            if not found:
                print(f"  [{symbol}] SKIP — CSV not found ({csv_name})")
                continue
        
        pip_mult = cfg['pip_mult']
        pip_size = cfg['pip_size']
        
        try:
            # Step 1: CSV → Parquet
            meta = convert_csv_to_parquet(symbol, csv_path, pip_mult)
            print(f"  [{symbol}] Parquet: {meta['rows']} rows, {meta.get('gap_count',0)} gaps")
            
            # Step 2: Asian Range extraction
            parquet_path = PARQUET_DIR / f"{symbol}_M5.parquet"
            if parquet_path.exists():
                import pandas as pd
                df = pd.read_parquet(parquet_path)
                ranges = extract_asian_ranges(df, pip_size)
                print(f"  [{symbol}] Asian Ranges: {len(ranges)} sessions, mean={sum(ranges)/max(len(ranges),1):.1f}p")
                
                # Step 3: K-Means tier discovery
                if len(ranges) >= 60:
                    tiers = discover_tiers(ranges)
                    print(f"  [{symbol}] Tiers: T1max={tiers['T1']['range_max']}p | T2max={tiers['T2']['range_max']}p")
                    
                    # Save tier config
                    import yaml
                    TIERS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(TIERS_DIR / f"{symbol}_tiers.yaml", 'w') as f:
                        yaml.dump(tiers, f, default_flow_style=False)
                else:
                    print(f"  [{symbol}] SKIP tiers — only {len(ranges)} sessions (need 60+)")
                    tiers = None
                
                # Step 4: Feature matrix
                features = build_feature_matrix(df, tiers, pip_size) if tiers else None
                if features is not None:
                    print(f"  [{symbol}] Features: {features.shape}")
                    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
                    features.to_parquet(FEATURES_DIR / f"{symbol}_features.parquet")
                
                # Step 5: Labels
                if features is not None:
                    labels = generate_labels(features, df)
                    print(f"  [{symbol}] Labels: {labels.shape}")
            
            phase1_results.append({'symbol': symbol, 'status': 'OK', 'rows': meta['rows']})
            
        except Exception as e:
            print(f"  [{symbol}] ERROR: {e}")
            phase1_results.append({'symbol': symbol, 'status': 'ERROR', 'error': str(e)})
    
    ok_count = sum(1 for r in phase1_results if r['status'] == 'OK')
    print(f"\n[PHASE 1] Complete: {ok_count}/{len(phase1_results)} assets processed")
    
    # ── PHASE 2: Train Models ───────────────────────────────
    print("\n[PHASE 2] Training XGBoost Models")
    print("-" * 40)
    
    from quant_lab.ml.phase2_classifier.regime_classifier import CerebusRegimeClassifier
    from quant_lab.ml.phase2_classifier.entry_scorer import CerebusEntryScorer
    import numpy as np
    import pandas as pd
    
    trained_assets = []
    for symbol, cfg in ASSET_CONFIG.items():
        features_path = FEATURES_DIR / f"{symbol}_features.parquet"
        if not features_path.exists():
            print(f"  [{symbol}] SKIP — no features file")
            continue
        
        try:
            features = pd.read_parquet(features_path)
            
            # Check if we have labels
            if 'regime_label' not in features.columns:
                print(f"  [{symbol}] SKIP — no labels in features")
                continue
            
            # Drop rows with NaN labels
            labeled = features.dropna(subset=['regime_label', 'entry_quality'])
            if len(labeled) < 100:
                print(f"  [{symbol}] SKIP — only {len(labeled)} labeled rows (need 100+)")
                continue
            
            # Train regime classifier
            feature_cols = CerebusRegimeClassifier.FEATURE_NAMES
            available_cols = [c for c in feature_cols if c in labeled.columns]
            if len(available_cols) < 4:
                print(f"  [{symbol}] SKIP — only {len(available_cols)} features available")
                continue
            
            X = labeled[available_cols].fillna(0).values
            y_regime = labeled['regime_label'].astype(int).values
            
            # Time-series split
            split_idx = int(len(X) * 0.7)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y_regime[:split_idx], y_regime[split_idx:]
            
            clf = CerebusRegimeClassifier()
            cv_acc = clf.train(X_train, y_train, X_val, y_val)
            
            # Save model
            from pathlib import Path
            import joblib
            model_dir = Path(__file__).parent / "models"
            model_dir.mkdir(exist_ok=True)
            joblib.dump(clf, model_dir / f"regime_{symbol}.pkl")
            
            print(f"  [{symbol}] Regime CV accuracy: {cv_acc:.1%}")
            
            # Train entry scorer
            if 'entry_quality' in labeled.columns:
                entry_cols = CerebusEntryScorer.ENTRY_FEATURES
                avail_entry = [c for c in entry_cols if c in labeled.columns]
                if len(avail_entry) >= 3:
                    X_e = labeled[avail_entry].fillna(0).values
                    y_e = labeled['entry_quality'].astype(float).values
                    e_split = int(len(X_e) * 0.7)
                    
                    scorer = CerebusEntryScorer()
                    scorer.train(X_e[:e_split], y_e[:e_split], X_e[e_split:], y_e[e_split:])
                    joblib.dump(scorer, model_dir / f"entry_{symbol}.pkl")
                    print(f"  [{symbol}] Entry scorer trained")
            
            trained_assets.append(symbol)
            
        except Exception as e:
            print(f"  [{symbol}] ERROR: {e}")
    
    print(f"\n[PHASE 2] Complete: {len(trained_assets)} assets trained")
    
    # ── SUMMARY ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(f"Phase 1: {ok_count} assets processed")
    print(f"Phase 2: {len(trained_assets)} models trained")
    print(f"Trained: {', '.join(trained_assets)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
