"""
Phase 2: XGBoost Regime Classifier (Layer 1)
==============================================
Trains XGBoost model to classify market regime from features.
Replaces hardcoded tier thresholds with learned regime boundaries.

Classes: CONFIRMED (0), CAUTION (1), FAILED (2), NO-GO (3)
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
import shap
import joblib
from pathlib import Path
from typing import Optional, Tuple

MODEL_DIR = Path(__file__).parent.parent / "models"
SHAP_DIR = Path(__file__).parent.parent / "shap"

FEATURE_NAMES = [
    'asian_range_pips',
    'vol_ratio_3am_9am',
    'hour_est',
    'spread_vs_20d_avg',
    'impulse_to_ar_ratio',
    'day_of_week',
    'consecutive_losses',
    'prior_session_wr',
]

REGIME_MAP = {0: 'CONFIRMED', 1: 'CAUTION', 2: 'FAILED', 3: 'NO-GO'}
REGIME_REVERSE = {v: k for k, v in REGIME_MAP.items()}


class CerebusRegimeClassifier:
    """
    Layer 1: Regime Classification via XGBoost.
    Trained on backtest-labeled outcomes (WIN/LOSS/TIME by regime quality).
    """

    def __init__(self):
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective='multi:softprob',
            num_class=4,
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1,
            tree_method='hist',
        )
        self.calibrated = None
        self.is_trained = False
        self.cv_scores = []
        self.feature_names = FEATURE_NAMES

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> float:
        """
        Train regime classifier with TimeSeriesSplit CV.
        Returns mean CV accuracy.
        """
        eval_set = [(X_val, y_val)] if X_val is not None else None

        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False,
        )

        # TimeSeriesSplit cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        scores = []
        for train_idx, val_idx in tscv.split(X_train):
            X_t, X_v = X_train[train_idx], X_train[val_idx]
            y_t, y_v = y_train[train_idx], y_train[val_idx]

            fold_model = xgb.XGBClassifier(
                **self.model.get_params()
            )
            fold_model.fit(X_t, y_t, verbose=False)
            acc = fold_model.score(X_v, y_v)
            scores.append(acc)

        self.cv_scores = scores
        mean_acc = np.mean(scores)
        print(f"Regime Classifier CV Accuracy: {mean_acc:.1%} ± {np.std(scores):.1%}")
        print(f"  Fold scores: {[f'{s:.1%}' for s in scores]}")

        if mean_acc < 0.88:
            print(f"  ⚠ WARNING: CV accuracy {mean_acc:.1%} below 88% threshold")

        self.is_trained = True
        return mean_acc

    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray):
        """Calibrate predicted probabilities using isotonic regression."""
        self.calibrated = CalibratedClassifierCV(
            self.model, method='isotonic', cv='prefit'
        )
        self.calibrated.fit(X_cal, y_cal)
        print("  ✓ Probability calibration complete")

    def predict_regime(self, features: dict) -> dict:
        """Returns regime prediction + confidence probabilities."""
        assert self.is_trained, "Model not trained — call train() first"

        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        if self.calibrated is not None:
            probs = self.calibrated.predict_proba(X)[0]
        else:
            probs = self.model.predict_proba(X)[0]

        pred_class = int(np.argmax(probs))

        return {
            'regime': REGIME_MAP[pred_class],
            'confidence': float(probs[pred_class]),
            'probabilities': {
                REGIME_MAP[i]: float(probs[i]) for i in range(4)
            },
        }

    def get_feature_importance(self, X_sample: np.ndarray) -> pd.DataFrame:
        """SHAP-based feature importance for audit trail."""
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X_sample)

        # For multi-class, average absolute SHAP across classes
        if isinstance(shap_values, list):
            mean_abs_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            mean_abs_shap = np.abs(shap_values).mean(axis=0)

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap': mean_abs_shap,
        }).sort_values('mean_abs_shap', ascending=False)
        importance['rank'] = range(1, len(importance) + 1)

        return importance

    def save(self, path: Optional[Path] = None):
        """Save model + scaler + metadata."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = path or MODEL_DIR / 'regime_classifier_xgb.pkl'

        artifact = {
            'model': self.model,
            'calibrated': self.calibrated,
            'feature_names': self.feature_names,
            'cv_scores': self.cv_scores,
            'is_trained': self.is_trained,
        }
        joblib.dump(artifact, path)
        print(f"  ✓ Model saved: {path}")

    def load(self, path: Optional[Path] = None):
        """Load model from disk."""
        path = path or MODEL_DIR / 'regime_classifier_xgb.pkl'
        artifact = joblib.load(path)
        self.model = artifact['model']
        self.calibrated = artifact.get('calibrated')
        self.feature_names = artifact['feature_names']
        self.cv_scores = artifact.get('cv_scores', [])
        self.is_trained = artifact.get('is_trained', True)
        print(f"  ✓ Model loaded: {path}")
