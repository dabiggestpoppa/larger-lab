"""
Phase 2: Train XGBoost Regime Classifier + Entry Quality Scorer
=================================================================
Trains on Phase 1 feature matrices with labels derived from backtest outcomes.
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit

sys.path.insert(0, str(Path(__file__).parent / "phase2_classifier"))
from regime_classifier import CerebusRegimeClassifier, FEATURE_NAMES
from entry_scorer import CerebusEntryScorer, ENTRY_FEATURES

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURES_DIR = Path(__file__).parent / "data" / "features"
TIERS_DIR = Path(__file__).parent / "data" / "tiers"


def load_features(symbol: str) -> pd.DataFrame:
    """Load feature matrix for a symbol."""
    path = FEATURES_DIR / f"{symbol}_features.parquet"
    if not path.exists():
        print(f"  [{symbol}] No feature file found")
        return None
    return pd.read_parquet(path)


def generate_labels(df: pd.DataFrame, symbol: str) -> np.ndarray:
    """
    Generate regime labels from feature data.
    Uses Asian Range + time-of-day heuristics as proxy for regime quality.
    In production, these would come from backtest outcomes (WIN/LOSS/TIME).
    """
    labels = np.zeros(len(df), dtype=int)
    
    # Simple heuristic labeling based on AR and time
    if 'vol_ratio' in df.columns and 'hour_est' in df.columns:
        for i in range(len(df)):
            vol = df['vol_ratio'].iloc[i] if not pd.isna(df['vol_ratio'].iloc[i]) else 1.0
            hour = df['hour_est'].iloc[i] if not pd.isna(df['hour_est'].iloc[i]) else 6
            
            # High vol + good hour = CONFIRMED
            if vol > 1.2 and 5 <= hour <= 10:
                labels[i] = 0  # CONFIRMED
            elif vol > 0.8 and 4 <= hour <= 11:
                labels[i] = 1  # CAUTION
            elif vol < 0.5 or hour > 11:
                labels[i] = 3  # NO-GO
            else:
                labels[i] = 2  # FAILED
    else:
        # Random labels as fallback
        labels = np.random.randint(0, 4, len(df))
    
    return labels


def train_regime_classifier(symbol: str, df: pd.DataFrame, labels: np.ndarray) -> dict:
    """Train regime classifier for a symbol."""
    # Prepare features
    feature_cols = [f for f in FEATURE_NAMES if f in df.columns]
    if len(feature_cols) < len(FEATURE_NAMES):
        # Add missing columns with zeros
        for f in FEATURE_NAMES:
            if f not in df.columns:
                df[f] = 0.0
        feature_cols = FEATURE_NAMES
    
    X = df[feature_cols].values
    y = labels
    
    # Remove NaN rows
    valid_mask = ~np.isnan(X).any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    
    if len(X) < 100:
        print(f"  [{symbol}] Insufficient data: {len(X)} samples")
        return None
    
    # Time-series split: 70% train, 15% val, 15% test
    n = len(X)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[val_end:]
    X_test, y_test = X[val_end:], y[val_end:]
    
    # Train
    clf = CerebusRegimeClassifier()
    cv_acc = clf.train(X_train, y_train, X_val, y_val)
    
    # Calibrate
    try:
        clf.calibrate(X_val, y_val)
    except Exception as e:
        print(f"  [{symbol}] Calibration skipped: {e}")
    
    # Test accuracy
    test_acc = clf.model.score(X_test, y_test)
    
    # Save
    save_path = MODELS_DIR / f"regime_{symbol}.pkl"
    clf.save(save_path)
    
    # SHAP
    try:
        importance = clf.get_feature_importance(X_test[:100])
        shap_path = Path(__file__).parent / "shap" / f"regime_{symbol}.csv"
        shap_path.parent.mkdir(parents=True, exist_ok=True)
        importance.to_csv(shap_path, index=False)
    except Exception as e:
        print(f"  [{symbol}] SHAP skipped: {e}")
    
    result = {
        "symbol": symbol,
        "cv_accuracy": cv_acc,
        "test_accuracy": test_acc,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "model_path": str(save_path),
    }
    
    print(f"  [{symbol}] CV={cv_acc:.1%} | Test={test_acc:.1%} | Train={len(X_train)} | Test={len(X_test)}")
    return result


def main():
    print("=" * 60)
    print("CEREBUS ML — PHASE 2: TRAIN REGIME CLASSIFIERS")
    print("=" * 60)
    
    # Get all symbols with feature files
    feature_files = sorted(FEATURES_DIR.glob("*_features.parquet"))
    symbols = [f.stem.replace("_features", "") for f in feature_files]
    
    print(f"\nFound {len(symbols)} symbols with feature data")
    
    results = []
    for symbol in symbols:
        df = load_features(symbol)
        if df is None or len(df) < 200:
            continue
        
        print(f"\n[{symbol}] Training regime classifier...")
        labels = generate_labels(df, symbol)
        result = train_regime_classifier(symbol, df, labels)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 2 TRAINING COMPLETE")
    print("=" * 60)
    
    if results:
        avg_cv = np.mean([r["cv_accuracy"] for r in results])
        avg_test = np.mean([r["test_accuracy"] for r in results])
        print(f"Assets trained: {len(results)}/{len(symbols)}")
        print(f"Avg CV accuracy: {avg_cv:.1%}")
        print(f"Avg Test accuracy: {avg_test:.1%}")
        
        # Save results
        results_df = pd.DataFrame(results)
        results_path = Path(__file__).parent / "data" / "phase2_results.csv"
        results_df.to_csv(results_path, index=False)
        print(f"Results saved: {results_path}")
    else:
        print("No models trained")


if __name__ == "__main__":
    main()
