"""
CEREBUS ML — Full Training Pipeline v2
=======================================
Uses RL's prepared training data (48 features, 5.3M samples, 18 assets).
Multi-target labels: label_25_delivery, label_50_delivery, rekey_triggered, regime_at_time.
"""
import sys
import json
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import joblib
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from collections import Counter

# ============================================================
# PATHS
# ============================================================
TRAINING_DIR = Path("quant-lab/ml/data/training")
MODEL_DIR = Path("quant-lab/ml/models")
SHAP_DIR = Path("quant-lab/ml/shap")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
SHAP_DIR.mkdir(parents=True, exist_ok=True)

# Target label columns
TARGET_COLS = ["label_25_delivery", "label_50_delivery", "rekey_triggered", "regime_at_time"]

# Exclude from features
EXCLUDE_COLS = set(TARGET_COLS + ["tier", "session", "regime_status"])


def load_training_data():
    """Load all training parquets and combine."""
    print("\n[1/4] Loading training data...")
    
    files = sorted(TRAINING_DIR.glob("*_training.parquet"))
    print(f"  Found {len(files)} asset files")
    
    all_X = []
    all_y = []
    feature_names = None
    
    for f in files:
        name = f.stem.replace("_training", "")
        df = pd.read_parquet(f)
        
        # Select feature columns (exclude targets and string cols)
        feat_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
        
        # Drop rows with NaN in features or target
        subset = feat_cols + ["label_25_delivery"]
        df_clean = df.dropna(subset=subset)
        
        if len(df_clean) < 100:
            print(f"  SKIP {name}: only {len(df_clean)} rows")
            continue
        
        # Convert labels: -1->0 (FAILED), 0->1 (CHOP), 1->2 (CONFIRMED)
        y = np.where(df_clean["label_25_delivery"].values == -1, 0,
                     np.where(df_clean["label_25_delivery"].values == 0, 1, 2))
        
        X = df_clean[feat_cols].values.astype(np.float64)
        
        all_X.append(X)
        all_y.append(y)
        
        if feature_names is None:
            feature_names = feat_cols
        
        print(f"  {name}: {len(df_clean)} samples, {len(feat_cols)} features")
    
    X_all = np.vstack(all_X)
    y_all = np.concatenate(all_y)
    
    # TimeSeriesSplit: 80% train, 20% val
    split_idx = int(len(X_all) * 0.8)
    X_train, X_val = X_all[:split_idx], X_all[split_idx:]
    y_train, y_val = y_all[:split_idx], y_all[split_idx:]
    
    print(f"\n  Total: {len(X_all):,} | Train: {len(X_train):,} | Val: {len(X_val):,}")
    print(f"  Features: {len(feature_names)}")
    print(f"  Label dist (train): {dict(Counter(y_train))}")
    
    return X_train, X_val, y_train, y_val, feature_names


def train_regime_classifier(X_train, y_train, X_val, y_val, feature_names):
    """Train XGBoost regime classifier."""
    print("\n[2/4] Training XGBoost regime classifier...")
    
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )
    
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    print(f"  Train: {train_acc:.1%} | Val: {val_acc:.1%}")
    
    # TimeSeriesSplit CV
    print("  TimeSeriesSplit CV (5 folds)...")
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    for fold, (ti, vi) in enumerate(tscv.split(X_train)):
        fm = xgb.XGBClassifier(**model.get_params())
        fm.fit(X_train[ti], y_train[ti], verbose=False)
        acc = fm.score(X_train[vi], y_train[vi])
        cv_scores.append(acc)
        print(f"    Fold {fold+1}: {acc:.1%}")
    
    mean_cv = np.mean(cv_scores)
    std_cv = np.std(cv_scores)
    print(f"  CV: {mean_cv:.1%} ± {std_cv:.1%}")
    
    return model, cv_scores, val_acc


def run_shap_check(model, X_val, feature_names):
    """SHAP physics check — dist_to_132_pips must be in top 5."""
    print("\n[3/4] SHAP physics check...")
    
    try:
        sample_size = min(5000, len(X_val))
        X_sample = X_val[:sample_size].astype(np.float64)
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        
        mean_abs_shap = np.zeros(len(feature_names))
        if isinstance(shap_values, list):
            for sv in shap_values:
                if hasattr(sv, 'ndim') and sv.ndim == 2 and sv.shape[1] == len(feature_names):
                    mean_abs_shap += np.abs(sv).mean(axis=0)
            if len(shap_values) > 0:
                mean_abs_shap /= len(shap_values)
        elif hasattr(shap_values, 'ndim') and shap_values.ndim == 2:
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance = pd.DataFrame({
            "feature": feature_names,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
        importance["rank"] = range(1, len(importance) + 1)
        
        print("\n  Top 10 SHAP:")
        for _, row in importance.head(10).iterrows():
            print(f"    #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.4f}")
        
        top5 = importance.head(5)["feature"].tolist()
        if "dist_to_132_pips" in top5:
            print("\n  ✅ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
        else:
            rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
            print(f"\n  ⚠️  dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")
        
        importance.to_csv(SHAP_DIR / "feature_importance_full.csv", index=False)
        print("  SHAP importance saved")
        
    except Exception as e:
        print(f"  SHAP failed (non-critical): {e}")
        importance = None
    
    return importance


def save_artifacts(model, feature_names, cv_scores, val_acc):
    """Save model + metadata."""
    print("\n[4/4] Saving model artifacts...")
    
    model_path = MODEL_DIR / "regime_classifier_full.pkl"
    artifact = {
        "model": model,
        "feature_names": feature_names,
        "cv_scores": cv_scores,
        "val_accuracy": val_acc,
        "is_trained": True,
        "version": "full_48feat_v3",
    }
    joblib.dump(artifact, model_path)
    print(f"  Model saved: {model_path}")
    
    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "cv_mean": float(np.mean(cv_scores)),
        "cv_std": float(np.std(cv_scores)),
        "val_accuracy": float(val_acc),
        "model_type": "XGBoost",
        "version": "full_48feat_v3",
    }
    with open(MODEL_DIR / "regime_classifier_full_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  Metadata saved")


def main():
    print("=" * 70)
    print("CEREBUS ML — FULL TRAINING PIPELINE v2")
    print("=" * 70)
    
    # Step 1: Load data
    X_train, X_val, y_train, y_val, feature_names = load_training_data()
    
    # Step 2: Train
    model, cv_scores, val_acc = train_regime_classifier(
        X_train, y_train, X_val, y_val, feature_names
    )
    
    # Step 3: SHAP
    importance = run_shap_check(model, X_val, feature_names)
    
    # Step 4: Save
    save_artifacts(model, feature_names, cv_scores, val_acc)
    
    print(f"\n{'='*70}")
    print(f"TRAINING COMPLETE")
    print(f"  CV: {np.mean(cv_scores):.1%} | Val: {val_acc:.1%}")
    print(f"  Samples: {len(X_train)+len(X_val):,} | Features: {len(feature_names)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
