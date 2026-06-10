"""
Fix SHAP analysis — handle multi-class KernelExplainer output correctly.
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

# Load validation data
print("Loading validation data...")
df = pd.read_parquet(TRAINING_DIR / "EURUSD_training.parquet")
feat_cols = [c for c in feature_names if c in df.columns]
X = df[feat_cols].values.astype(np.float64)
val_start = int(len(X) * 0.8)
X_val = X[val_start:]
print(f"  Val samples: {len(X_val):,}")

# Use KernelExplainer with small sample
print("\nRunning KernelExplainer (this will take ~2 min)...")
sample_size = 200
X_sample = X_val[:sample_size]
X_background = shap.sample(X_val[:500], 50)  # 50 background samples

def predict_fn(X):
    return model.predict_proba(X)

explainer = shap.KernelExplainer(predict_fn, X_background)
shap_values = explainer.shap_values(X_sample)

print(f"  SHAP output type: {type(shap_values)}")
if isinstance(shap_values, list):
    print(f"  Classes: {len(shap_values)}")
    for i, sv in enumerate(shap_values):
        print(f"  Class {i} shape: {sv.shape}")
    
    # Average absolute SHAP across all classes
    mean_abs_shap = np.zeros(len(feat_cols))
    for sv in shap_values:
        mean_abs_shap += np.abs(sv).mean(axis=0)
    mean_abs_shap /= len(shap_values)
elif isinstance(shap_values, np.ndarray):
    print(f"  Shape: {shap_values.shape}")
    if shap_values.ndim == 3:
        # (samples, features, classes) — average across classes
        mean_abs_shap = np.abs(shap_values).mean(axis=(0, 2))
    else:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)

# Build importance DataFrame
importance = pd.DataFrame({
    "feature": feat_cols,
    "mean_abs_shap": mean_abs_shap,
}).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
importance["rank"] = range(1, len(importance) + 1)

print("\nTop 15 SHAP:")
for _, row in importance.head(15).iterrows():
    print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.6f}")

top5 = importance.head(5)["feature"].tolist()
if "dist_to_132_pips" in top5:
    print("\n  ✅ SHAP PHYSICS CHECK PASSED: dist_to_132_pips in top 5")
else:
    rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
    print(f"\n  ⚠️  dist_to_132_pips rank: {int(rank[0]) if len(rank) > 0 else 'N/A'}")

importance.to_csv(SHAP_DIR / "feature_importance_fixed.csv", index=False)
print("\nSHAP importance saved.")
