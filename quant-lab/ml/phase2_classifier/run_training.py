"""
Run CEREBUS ML Training — Complete Pipeline
=============================================
1. Prep training data (features + labels)
2. Train XGBoost regime classifier
3. Train entry scorer
4. SHAP physics check
5. Save model artifacts

Usage:
    python run_training.py
"""
import sys
sys.path.insert(0, str(Path(__file__).parent))

from prep_training_data import main as prep_data
from retrain_full import (
    prepare_training_data, train_regime_classifier,
    run_shap_physics_check, save_model_artifacts,
    MODEL_DIR, SHAP_DIR, ALL_FEATURES
)
import json
from pathlib import Path


def main():
    print("=" * 70)
    print("CEREBUS ML — FULL TRAINING PIPELINE")
    print("=" * 70)
    
    # Step 1: Prep data
    print("\n[1/5] Preparing training data...")
    prep_data()
    
    # Step 2: Load and combine
    print("\n[2/5] Loading training data...")
    training_dir = Path("quant-lab/ml/data/training")
    
    all_X = []
    all_y = []
    feature_names = None
    
    for f in sorted(training_dir.glob("*_training.parquet")):
        name = f.stem.replace("_training", "")
        df = pd.read_parquet(f)
        
        # Select available features
        available = [c for c in ALL_FEATURES if c in df.columns]
        if len(available) < 10:
            print(f"  SKIP {name}: only {len(available)} features")
            continue
        
        # Labels: use label_25_delivery as primary target
        # Convert -1/0/1 to 0/1/2
        y_raw = df["label_25_delivery"].values
        y = np.where(y_raw == -1, 0, np.where(y_raw == 0, 1, 2))
        
        X = df[available].values
        
        all_X.append(X)
        all_y.append(y)
        
        if feature_names is None:
            feature_names = available
        
        print(f"  {name}: {len(df):,} samples | features: {len(available)}")
    
    if not all_X:
        print("ERROR: no training data!")
        return
    
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    import shap
    import joblib
    from collections import Counter
    
    X_all = np.vstack(all_X)
    y_all = np.concatenate(all_y)
    
    # TimeSeriesSplit: 80% train, 20% val
    split_idx = int(len(X_all) * 0.8)
    X_train, X_val = X_all[:split_idx], X_all[split_idx:]
    y_train, y_val = y_all[:split_idx], y_all[split_idx:]
    
    print(f"\nTotal samples: {len(X_all):,}")
    print(f"Train: {len(X_train):,} | Val: {len(X_val):,}")
    print(f"Features: {len(feature_names)}")
    print(f"Label dist (train): {dict(Counter(y_train))}")
    
    # Step 3: Train
    print("\n[3/5] Training XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0,
        objective="multi:softprob", num_class=3,
        eval_metric="mlogloss", random_state=42, n_jobs=-1, tree_method="hist"
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    print(f"Train accuracy: {train_acc:.1%}")
    print(f"Val accuracy: {val_acc:.1%}")
    
    # TimeSeriesSplit CV
    print("\n[4/5] TimeSeriesSplit CV...")
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
        X_t, X_v = X_train[train_idx], X_train[val_idx]
        y_t, y_v = y_train[train_idx], y_train[val_idx]
        fold_model = xgb.XGBClassifier(**model.get_params())
        fold_model.fit(X_t, y_t, verbose=False)
        acc = fold_model.score(X_v, y_v)
        cv_scores.append(acc)
        print(f"  Fold {fold+1}: {acc:.1%}")
    
    mean_cv = np.mean(cv_scores)
    print(f"CV Accuracy: {mean_cv:.1%} ± {np.std(cv_scores):.1%}")
    
    # Step 4: SHAP
    print("\n[5/5] SHAP physics check...")
    sample_size = min(10000, len(X_val))
    X_sample = X_val[:sample_size]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    if isinstance(shap_values, list):
        mean_abs_shap = np.zeros(len(feature_names))
        for sv in shap_values:
            if sv.ndim == 2:
                mean_abs_shap += np.abs(sv).mean(axis=0)
        mean_abs_shap /= len(shap_values)
    else:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    importance = pd.DataFrame({
        "feature": feature_names[:len(mean_abs_shap)],
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    importance["rank"] = range(1, len(importance) + 1)
    
    print("\nTop 10 SHAP features:")
    for _, row in importance.head(10).iterrows():
        print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.4f}")
    
    top5 = importance.head(5)["feature"].tolist()
    if "dist_to_132_pips" in top5:
        print("\n  ✓ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
    else:
        rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
        print(f"\n  ⚠ dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")
    
    # Save
    MODEL_DIR = Path("quant-lab/ml/models")
    SHAP_DIR = Path("quant-lab/ml/shap")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    SHAP_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = MODEL_DIR / "regime_classifier_full.pkl"
    artifact = {
        "model": model, "feature_names": feature_names,
        "cv_scores": cv_scores, "val_accuracy": val_acc,
        "is_trained": True, "version": "full_30feat"
    }
    joblib.dump(artifact, model_path)
    print(f"\nModel saved: {model_path}")
    
    importance.to_csv(SHAP_DIR / "feature_importance_full.csv", index=False)
    print(f"SHAP saved: {SHAP_DIR / 'feature_importance_full.csv'}")
    
    print(f"\n{'='*70}")
    print(f"TRAINING COMPLETE")
    print(f"  CV: {mean_cv:.1%} | Val: {val_acc:.1%}")
    print(f"  Samples: {len(X_all):,} | Features: {len(feature_names)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    from pathlib import Path
    main()
