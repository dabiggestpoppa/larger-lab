"""
Phase 2: Retrain Models on Full Feature Set
==============================================
Combines micro features (existing) + macro features (new) + labels (new)
into a single ML-ready dataset, then retrains XGBoost and Entry Scorer.

Feature set (30+ features):
- Micro (8): asian_range_pips, vol_ratio, hour_est, spread_vs_20d_avg,
              impulse_to_ar_ratio, day_of_week, consecutive_losses, prior_session_wr
- Macro (12): dist_to_25_pips, dist_to_50_pips, dist_to_132_pips,
               dist_to_mlr_high_pips, dist_to_mlr_low_pips, regime_ratio,
               ilm_state, is_wednesday_pm, hours_since_mlr, minutes_to_12pm_est,
               mlr_range_pips, bias_encoded
- Labels: label_25_delivery, label_50_delivery, rekey_triggered, regime_at_time

GATE: SHAP physics check — dist_to_132_pct must be in top 5 features.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
import shap
import joblib
from pathlib import Path
from collections import Counter

# ============================================================
# PATHS
# ============================================================

LABELS_DIR = Path(__file__).parent.parent / "data" / "labels"
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
ML_DATA_DIR = Path(__file__).parent.parent / "data"
MODEL_DIR = Path(__file__).parent.parent / "models"
SHAP_DIR = Path(__file__).parent.parent / "shap"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
SHAP_DIR.mkdir(parents=True, exist_ok=True)

# Feature columns for the full model
MICRO_FEATURES = [
    "asian_range_pips",
    "vol_ratio_3am_9am",
    "hour_est",
    "spread_vs_20d_avg",
    "impulse_to_ar_ratio",
    "day_of_week",
    "consecutive_losses",
    "prior_session_wr",
]

MACRO_FEATURES = [
    "dist_to_25_pips",
    "dist_to_50_pips",
    "dist_to_132_pips",
    "dist_to_mlr_high_pips",
    "dist_to_mlr_low_pips",
    "regime_ratio",
    "ilm_state",
    "is_wednesday_pm",
    "hours_since_mlr",
    "minutes_to_12pm_est",
    "mlr_range_pips",
    "bias_encoded",
]

ALL_FEATURES = MICRO_FEATURES + MACRO_FEATURES


# ============================================================
# 1. BUILD COMBINED FEATURE MATRIX
# ============================================================

def build_combined_feature_matrix(symbol: str) -> pd.DataFrame | None:
    """
    Combine micro features + macro features + labels into a single DataFrame.
    """
    labels_path = LABELS_DIR / f"{symbol}_labeled.parquet"
    features_path = FEATURES_DIR / f"{symbol}_features.parquet"

    if not labels_path.exists():
        print(f"  SKIP: no labels for {symbol}")
        return None

    df = pd.read_parquet(labels_path)

    # Add micro features if available
    if features_path.exists():
        df_micro = pd.read_parquet(features_path)
        # Only add micro feature columns that don't already exist
        micro_cols = [c for c in df_micro.columns if c not in df.columns and c not in ("open", "high", "low", "close", "volume")]
        if micro_cols:
            df = df.join(df_micro[micro_cols], how="left")

    # Encode bias as numeric
    if "bias" in df.columns:
        df["bias_encoded"] = (df["bias"] == "BULLISH").astype(int)

    # Compute mlr_range_pips if not present
    if "mlr_range_pips" not in df.columns and "mlr_range" in df.columns:
        # Determine pip multiplier
        jpy_pairs = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"]
        pip_mult = 100 if symbol in jpy_pairs else 10000
        df["mlr_range_pips"] = df["mlr_range"] * pip_mult

    return df


def build_all_feature_matrices() -> dict:
    """Build combined feature matrices for all assets."""
    print("\n=== BUILDING COMBINED FEATURE MATRICES ===")
    manifest = {}

    for labels_file in sorted(LABELS_DIR.glob("*_labeled.parquet")):
        symbol = labels_file.stem.replace("_labeled", "")
        print(f"\n{symbol}:")
        df = build_combined_feature_matrix(symbol)
        if df is None:
            continue

        # Check which features are available
        available = [f for f in ALL_FEATURES if f in df.columns]
        missing = [f for f in ALL_FEATURES if f not in df.columns]
        print(f"  Available features: {len(available)}/{len(ALL_FEATURES)}")
        if missing:
            print(f"  Missing: {missing}")

        # Save combined matrix
        out_path = ML_DATA_DIR / f"{symbol}_combined.parquet"
        df.to_parquet(out_path)

        manifest[symbol] = {
            "rows": len(df),
            "features": len(available),
            "available_features": available,
            "path": str(out_path),
        }

    return manifest


# ============================================================
# 2. PREPARE TRAINING DATA
# ============================================================

def prepare_training_data(
    symbols: list[str] | None = None,
    target_col: str = "label_25_delivery",
    drop_no_go: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """
    Prepare training data from all assets.
    Uses TimeSeriesSplit: train on all assets, validate on last 20%.

    For label_25_delivery:
    - Convert to 3-class: 0 = FAILED (-1), 1 = CHOP (0), 2 = CONFIRMED (1)
    - This maps to the regime classification task
    """
    print("\n=== PREPARING TRAINING DATA ===")

    all_X = []
    all_y = []
    feature_names = None

    if symbols is None:
        symbols = [f.stem.replace("_labeled", "") for f in LABELS_DIR.glob("*_labeled.parquet")]
        symbols = [s for s in symbols if s != "TEST"]

    for symbol in symbols:
        df_path = ML_DATA_DIR / f"{symbol}_combined.parquet"
        if not df_path.exists():
            continue

        df = pd.read_parquet(df_path)

        # Determine available features
        available = [f for f in ALL_FEATURES if f in df.columns]
        if len(available) < 10:
            print(f"  SKIP {symbol}: only {len(available)} features available")
            continue

        # Drop rows with NaN in features or target
        subset = available + [target_col, "regime_at_time"]
        df_clean = df.dropna(subset=subset)

        if drop_no_go:
            # Drop NO-GO bars
            if "regime_at_time" in df_clean.columns:
                df_clean = df_clean[df_clean["regime_at_time"] != "NO-GO"]

        if len(df_clean) < 100:
            print(f"  SKIP {symbol}: only {len(df_clean)} valid rows")
            continue

        X = df_clean[available].values
        y_raw = df_clean[target_col].values

        # Convert labels: -1 → 0 (FAILED), 0 → 1 (CHOP), 1 → 2 (CONFIRMED)
        y = np.where(y_raw == -1, 0, np.where(y_raw == 0, 1, 2))

        all_X.append(X)
        all_y.append(y)

        if feature_names is None:
            feature_names = available

        print(f"  {symbol}: {len(df_clean)} samples | label dist: {dict(Counter(y))}")

    if not all_X:
        print("  ERROR: no training data!")
        return None, None, None, None, []

    X_all = np.vstack(all_X)
    y_all = np.concatenate(all_y)

    # TimeSeriesSplit: use last 20% for validation
    split_idx = int(len(X_all) * 0.8)
    X_train, X_val = X_all[:split_idx], X_all[split_idx:]
    y_train, y_val = y_all[:split_idx], y_all[split_idx:]

    print(f"\nTotal samples: {len(X_all)}")
    print(f"Train: {len(X_train)}, Val: {len(X_val)}")
    print(f"Feature count: {len(feature_names)}")
    print(f"Label distribution (train): {dict(Counter(y_train))}")
    print(f"Label distribution (val): {dict(Counter(y_val))}")

    return X_train, X_val, y_train, y_val, feature_names


# ============================================================
# 3. RETRAIN XGBOOST REGIME CLASSIFIER
# ============================================================

def train_regime_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str],
) -> tuple[xgb.XGBClassifier, float]:
    """
    Train XGBoost regime classifier on full feature set.
    Classes: 0 = FAILED, 1 = CHOP, 2 = CONFIRMED
    """
    print("\n=== TRAINING XGBOOST REGIME CLASSIFIER ===")

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

    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # Evaluate
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    print(f"Train accuracy: {train_acc:.1%}")
    print(f"Val accuracy: {val_acc:.1%}")

    # TimeSeriesSplit CV
    print("Running TimeSeriesSplit CV...")
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
        X_t, X_v = X_train[train_idx], X_train[val_idx]
        y_t, y_v = y_train[train_idx], y_train[val_idx]

        fold_model = xgb.XGBClassifier(**model.get_params())
        fold_model.fit(X_t, y_t, verbose=False)
        acc = fold_model.score(X_v, y_v)
        cv_scores.append(acc)
        print(f"  Fold {fold + 1}: {acc:.1%}")

    mean_cv = np.mean(cv_scores)
    std_cv = np.std(cv_scores)
    print(f"CV Accuracy: {mean_cv:.1%} ± {std_cv:.1%}")

    # GATE: CV accuracy >= 88%
    if mean_cv < 0.88:
        print(f"  ⚠ WARNING: CV accuracy {mean_cv:.1%} below 88% threshold")
    else:
        print(f"  ✓ CV accuracy gate passed")

    return model, mean_cv


# ============================================================
# 4. SHAP PHYSICS CHECK
# ============================================================

def run_shap_physics_check(
    model: xgb.XGBClassifier,
    X_val: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """
    Run SHAP analysis to verify the model learned CEREBUS physics.
    GATE: dist_to_132_pips must be in top 5 features.
    """
    print("\n=== SHAP PHYSICS CHECK ===")

    # Use a sample for speed
    sample_size = min(10000, len(X_val))
    X_sample = X_val[:sample_size]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # For multi-class, shap_values is a list of arrays (one per class)
    if isinstance(shap_values, list):
        mean_abs_shap = np.zeros(len(feature_names))
        for sv in shap_values:
            if sv.ndim == 2:
                mean_abs_shap += np.abs(sv).mean(axis=0)
            elif sv.ndim == 3:
                # Some XGBoost versions return 3D arrays
                mean_abs_shap += np.abs(sv).mean(axis=(0, 2))
        mean_abs_shap /= len(shap_values)
    elif shap_values.ndim == 2:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
    elif shap_values.ndim == 3:
        mean_abs_shap = np.abs(shap_values).mean(axis=(0, 2))
    else:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)

    importance = pd.DataFrame({
        "feature": feature_names[:len(mean_abs_shap)],
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    importance["rank"] = range(1, len(importance) + 1)

    print("\nTop 10 features by SHAP importance:")
    for _, row in importance.head(10).iterrows():
        print(f"  #{int(row['rank'])} {row['feature']}: {row['mean_abs_shap']:.4f}")

    # GATE: dist_to_132_pips in top 5
    top5 = importance.head(5)["feature"].tolist()
    if "dist_to_132_pips" in top5:
        print(f"\n  ✓ SHAP PHYSICS CHECK PASSED: dist_to_132_pips is in top 5")
    else:
        rank = importance[importance["feature"] == "dist_to_132_pips"]["rank"].values
        if len(rank) > 0:
            print(f"\n  ✗ SHAP PHYSICS CHECK FAILED: dist_to_132_pips is rank {int(rank[0])}, not top 5")
        else:
            print(f"\n  ✗ SHAP PHYSICS CHECK FAILED: dist_to_132_pips not found in features")

    # Save SHAP importance
    importance.to_csv(SHAP_DIR / "feature_importance_full.csv", index=False)

    return importance


# ============================================================
# 5. SAVE MODELS
# ============================================================

def save_model_artifacts(
    model: xgb.XGBClassifier,
    feature_names: list[str],
    cv_scores: list[float],
    val_acc: float,
):
    """Save model + metadata."""
    print("\n=== SAVING MODEL ARTIFACTS ===")

    # Save model
    model_path = MODEL_DIR / "regime_classifier_full.pkl"
    artifact = {
        "model": model,
        "feature_names": feature_names,
        "cv_scores": cv_scores,
        "val_accuracy": val_acc,
        "is_trained": True,
        "version": "full_30feat",
    }
    joblib.dump(artifact, model_path)
    print(f"  ✓ Model saved: {model_path}")

    # Save metadata
    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "cv_mean": float(np.mean(cv_scores)),
        "cv_std": float(np.std(cv_scores)),
        "val_accuracy": float(val_acc),
        "model_type": "XGBoost",
        "version": "full_30feat",
    }
    with open(MODEL_DIR / "regime_classifier_full_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✓ Metadata saved")


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_phase2():
    """Run full Phase 2 pipeline."""
    print("=" * 60)
    print("PHASE 2: RETRAIN MODELS ON FULL FEATURES")
    print("=" * 60)

    # Step 1: Build combined feature matrices
    manifest = build_all_feature_matrices()

    # Step 2: Prepare training data
    X_train, X_val, y_train, y_val, feature_names = prepare_training_data()
    if X_train is None:
        print("ERROR: No training data available")
        return

    # Step 3: Train regime classifier
    model, cv_acc = train_regime_classifier(X_train, y_train, X_val, y_val, feature_names)

    # Step 4: SHAP physics check
    importance = run_shap_physics_check(model, X_val, feature_names)

    # Step 5: Save
    save_model_artifacts(model, feature_names, [cv_acc], model.score(X_val, y_val))

    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print("=" * 60)

    return {
        "cv_accuracy": cv_acc,
        "val_accuracy": model.score(X_val, y_val),
        "n_features": len(feature_names),
        "top_5_shap": importance.head(5)["feature"].tolist(),
    }


if __name__ == "__main__":
    result = run_phase2()
    print(f"\nResult: {result}")
