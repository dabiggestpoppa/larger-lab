"""
CEREBUS ML — Phase 2: Train XGBoost Models
Trains regime classifier + entry scorer per asset on Phase 1 features.
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quant_lab.ml.phase2_classifier.regime_classifier import CerebusRegimeClassifier
from quant_lab.ml.phase2_classifier.entry_scorer import CerebusEntryScorer

FEATURES_DIR = Path(__file__).parent / "data" / "features"
MODELS_DIR = Path(__file__).parent / "results" / "models"
REPORTS_DIR = Path(__file__).parent / "results" / "reports"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

REGIME_LABELS = {0: 'CONFIRMED', 1: 'CAUTION', 2: 'FAILED', 3: 'NO-GO'}

def label_regime(row):
    """Derive regime label from features + outcome."""
    ar_ratio = row.get('vol_ratio_3am_9am', 1.0)
    impulse_ar = row.get('impulse_to_ar_ratio', 0.0)
    
    if ar_ratio >= 1.5 and impulse_ar >= 0.3:
        return 0  # CONFIRMED
    elif ar_ratio >= 1.3 and impulse_ar >= 0.2:
        return 1  # CAUTION
    elif ar_ratio < 1.0 or impulse_ar < 0.1:
        return 3  # NO-GO
    else:
        return 2  # FAILED

def train_asset(symbol):
    """Train regime classifier and entry scorer for one asset."""
    feat_path = FEATURES_DIR / f"{symbol}_features.parquet"
    if not feat_path.exists():
        return {'symbol': symbol, 'status': 'SKIP', 'reason': 'no features file'}
    
    df = pd.read_parquet(feat_path)
    print(f"\n[{symbol}] Features loaded: {df.shape}")
    
    # Generate regime labels if not present
    if 'regime_label' not in df.columns:
        df['regime_label'] = df.apply(label_regime, axis=1)
        print(f"  Labels generated: {df['regime_label'].value_counts().to_dict()}")
    
    # Drop rows with NaN in key columns
    feature_cols = [c for c in CerebusRegimeClassifier.FEATURE_NAMES if c in df.columns]
    df_clean = df.dropna(subset=feature_cols).copy()
    
    if len(df_clean) < 200:
        return {'symbol': symbol, 'status': 'SKIP', 'reason': f'only {len(df_clean)} clean rows'}
    
    # Prepare training data
    X = df_clean[feature_cols].fillna(0).values.astype(np.float32)
    y = df_clean['regime_label'].astype(int).values
    
    # Time-series split: 70/15/15
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    
    # Train regime classifier
    clf = CerebusRegimeClassifier()
    
    # Override feature names to match available columns
    clf.feature_names = feature_cols
    
    cv_acc = clf.train(X_train, y_train, X_val, y_val)
    
    # Test set accuracy
    test_pred = clf.model.predict(X_test)
    test_acc = np.mean(test_pred == y_test)
    
    # Save model
    model_path = MODELS_DIR / f"regime_{symbol}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
    
    # Feature importance
    importance = dict(zip(feature_cols, clf.model.feature_importances_))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    print(f"  Regime CV accuracy: {cv_acc:.1%} | Test: {test_acc:.1%}")
    print(f"  Top features: {sorted_imp[:3]}")
    
    # Train entry scorer
    entry_features = [c for c in CerebusEntryScorer.ENTRY_FEATURES if c in df_clean.columns]
    entry_result = None
    if len(entry_features) >= 3 and 'entry_quality_score' in df_clean.columns:
        eq_scores = df_clean['entry_quality_score'].dropna()
        if len(eq_scores) > 100:
            X_e = df_clean.loc[eq_scores.index, entry_features].fillna(0).values.astype(np.float32)
            y_e = eq_scores.values.astype(np.float32)
            
            e_train = int(len(X_e) * 0.7)
            e_val = int(len(X_e) * 0.85)
            
            scorer = CerebusEntryScorer()
            scorer.feature_names = entry_features
            cv_r2 = scorer.train(X_e[:e_train], y_e[:e_train], X_e[e_train:e_val], y_e[e_train:e_val])
            
            scorer_path = MODELS_DIR / f"entry_{symbol}.pkl"
            with open(scorer_path, 'wb') as f:
                pickle.dump(scorer, f)
            
            entry_result = {'cv_r2': round(cv_r2, 3), 'features': len(entry_features)}
            print(f"  Entry scorer R²: {cv_r2:.3f}")
    
    return {
        'symbol': symbol,
        'status': 'TRAINED',
        'train_size': len(X_train),
        'val_size': len(X_val),
        'test_size': len(X_test),
        'cv_accuracy': round(cv_acc, 4),
        'test_accuracy': round(test_acc, 4),
        'feature_importance': sorted_imp[:5],
        'entry_scorer': entry_result,
    }

def main():
    print("=" * 60)
    print("CEREBUS ML — PHASE 2: TRAIN XGBOOST MODELS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get all feature files
    feat_files = sorted(FEATURES_DIR.glob("*_features.parquet"))
    symbols = [f.stem.replace('_features', '') for f in feat_files]
    
    print(f"\nAssets to train: {len(symbols)}")
    
    results = []
    for symbol in symbols:
        try:
            result = train_asset(symbol)
            results.append(result)
        except Exception as e:
            print(f"\n[{symbol}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({'symbol': symbol, 'status': 'ERROR', 'error': str(e)})
    
    # Summary
    trained = [r for r in results if r['status'] == 'TRAINED']
    errors = [r for r in results if r['status'] == 'ERROR']
    skipped = [r for r in results if r['status'] == 'SKIP']
    
    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print(f"Trained: {len(trained)} | Errors: {len(errors)} | Skipped: {len(skipped)}")
    
    if trained:
        avg_cv = np.mean([r['cv_accuracy'] for r in trained])
        avg_test = np.mean([r['test_accuracy'] for r in trained])
        print(f"Avg CV accuracy: {avg_cv:.1%}")
        print(f"Avg Test accuracy: {avg_test:.1%}")
        
        print("\nPer-asset results:")
        for r in trained:
            print(f"  {r['symbol']:10s} | CV: {r['cv_accuracy']:.1%} | Test: {r['test_accuracy']:.1%}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_assets': len(symbols),
        'trained': len(trained),
        'errors': len(errors),
        'skipped': len(skipped),
        'avg_cv_accuracy': round(float(avg_cv), 4) if trained else 0,
        'avg_test_accuracy': round(float(avg_test), 4) if trained else 0,
        'results': results,
    }
    
    report_path = REPORTS_DIR / "phase2_training_report.json"
    with open(report_path, 'w') as f:
        # Convert numpy types for JSON serialization
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReport saved: {report_path}")
    return report

if __name__ == "__main__":
    main()
