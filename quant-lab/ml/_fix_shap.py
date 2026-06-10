"""
Fix SHAP analysis for multi-class XGBoost model.
TreeExplainer with multi-class probability outputs returns zeros.
Solution: Use output='margin' or compute SHAP per-class.
"""
import numpy as np
import pandas as pd
import shap
import joblib
from pathlib import Path

MODEL_DIR = Path("quant-lab/ml/models")
SHAP_DIR = Path("quant-lab/ml/shap")
TRAINING_DIR = Path("quant-lab/ml/data/training")

# Load model
print("Loading model...")
art = joblib.load(MODEL_DIR / "regime_classifier_full.pkl")
model = art["model"]
feature_names = art["feature_names"]
print(f"  Model: {art['version']}, {len(feature_names)} features")

# Load a sample of validation data
print("Loading validation data...")
df = pd.read_parquet(TRAINING_DIR / "EURUSD_training.parquet")
feat_cols = [c for c in feature_names if c in df.columns]
X = df[feat_cols].values.astype(np.float64)

# Use last 20% as val (matching training split)
val_start = int(len(X) * 0.8)
X_val = X[val_start:]
print(f"  Val samples: {len(X_val):,}")

# Try different SHAP approaches
print("\nTrying SHAP with output='margin'...")
try:
    explainer = shap.TreeExplainer(model, output='margin')
    sample_size = min(2000, len(X_val))
    X_sample = X_val[:sample_size]
    shap_values = explainer.shap_values(X_sample)
    
    if isinstance(shap_values, list):
        mean_abs_shap = np.zeros(len(feat_cols))
        for sv in shap_values:
            if hasattr(sv, 'ndim') and sv.ndim == 2:
                mean_abs_shap += np.abs(sv).mean(axis=0)
        mean_abs_shap /= len(shap_values)
    else:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    importance = pd.DataFrame({
        "feature": feat_cols,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    importance["rank"] = range(1, len(importance) + 1)
    
    print("\nTop 15 SHAP (margin output):")
    for _, row in importance.head(15).iterrows():
        print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.6f}")
    
    top5 = importance.head(5)["feature"].tolist()
    if "dist_to_132_pips" in top5:
        print("\n  ✅ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
    else:
        rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
        print(f"\n  ⚠️  dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")
    
    importance.to_csv(SHAP_DIR / "feature_importance_fixed.csv", index=False)
    print("  SHAP importance saved")
    
except Exception as e:
    print(f"  margin output failed: {e}")
    
    # Fallback: use predict output
    print("\nTrying SHAP with prediction output...")
    try:
        explainer = shap.TreeExplainer(model)
        sample_size = min(1000, len(X_val))
        X_sample = X_val[:sample_size]
        
        # Get SHAP values for the predicted class only
        shap_values = explainer.shap_values(X_sample, check_additivity=False)
        
        if isinstance(shap_values, list):
            # Multi-class: average across classes
            mean_abs_shap = np.zeros(len(feat_cols))
            for sv in shap_values:
                if hasattr(sv, 'ndim') and sv.ndim == 2:
                    mean_abs_shap += np.abs(sv).mean(axis=0)
            mean_abs_shap /= len(shap_values)
        else:
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance = pd.DataFrame({
            "feature": feat_cols,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
        importance["rank"] = range(1, len(importance) + 1)
        
        print("\nTop 15 SHAP (prediction output):")
        for _, row in importance.head(15).iterrows():
            print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.6f}")
        
        top5 = importance.head(5)["feature"].tolist()
        if "dist_to_132_pips" in top5:
            print("\n  ✅ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
        else:
            rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
            print(f"\n  ⚠️  dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")
        
        importance.to_csv(SHAP_DIR / "feature_importance_fixed.csv", index=False)
        print("  SHAP importance saved")
        
    except Exception as e2:
        print(f"  prediction output also failed: {e2}")
        print("  Trying KernelExplainer on small sample...")
        
        # Last resort: KernelExplainer
        try:
            sample_size = min(100, len(X_val))
            X_sample = X_val[:sample_size]
            X_background = X_val[:50]
            
            def predict_fn(X):
                return model.predict_proba(X)
            
            explainer = shap.KernelExplainer(predict_fn, X_background)
            shap_values = explainer.shap_values(X_sample)
            
            if isinstance(shap_values, list):
                mean_abs_shap = np.zeros(len(feat_cols))
                for sv in shap_values:
                    if hasattr(sv, 'ndim') and sv.ndim == 2:
                        mean_abs_shap += np.abs(sv).mean(axis=0)
                mean_abs_shap /= len(shap_values)
            else:
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
            
            importance = pd.DataFrame({
                "feature": feat_cols,
                "mean_abs_shap": mean_abs_shap,
            }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
            importance["rank"] = range(1, len(importance) + 1)
            
            print("\nTop 15 SHAP (KernelExplainer):")
            for _, row in importance.head(15).iterrows():
                print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.6f}")
            
            top5 = importance.head(5)["feature"].tolist()
            if "dist_to_132_pips" in top5:
                print("\n  ✅ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
            else:
                rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
                print(f"\n  ⚠️  dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")
            
            importance.to_csv(SHAP_DIR / "feature_importance_fixed.csv", index=False)
            print("  SHAP importance saved")
            
        except Exception as e3:
            print(f"  All SHAP methods failed: {e3}")

print("\nDone.")
