"""
Phase 2.2: Entry Quality Scorer (Layer 2)
============================================
Scores each potential entry 0.0-1.0 based on multi-feature interaction.
Replaces binary Goldilocks zone with continuous quality gradient.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

ENTRY_FEATURES = [
    "pullback_pct",
    "occ_body_to_au_ratio",
    "time_since_impulse_min",
    "volume_spike_ratio",
    "regime_confidence",
    "distance_to_dz_center",
    "prior_loop_outcome",
    "spread_at_entry",
]


class CerebusEntryScorer:
    """
    Layer 2: Entry Quality Scorer.
    Scores each potential entry 0.0-1.0.
    Target: normalized R-multiple from backtest (0-1 scale).
    """

    def __init__(self, params: dict = None):
        default_params = {
            "n_estimators": 150,
            "max_depth": 3,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "objective": "reg:squarederror",
            "tree_method": "hist",
            "random_state": 42,
        }
        if params:
            default_params.update(params)
        self.params = default_params
        self.model = xgb.XGBRegressor(**default_params)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ENTRY_FEATURES

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
    ) -> float:
        """Train on normalized R-multiple targets. Returns mean CV R²."""
        from sklearn.model_selection import TimeSeriesSplit
        X_train_scaled = self.scaler.fit_transform(X_train)
        eval_set = None
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_val_scaled, y_val)]
        self.model.fit(X_train_scaled, y_train, eval_set=eval_set, verbose=False)
        self.is_trained = True

        # TimeSeriesSplit CV for R²
        tscv = TimeSeriesSplit(n_splits=5)
        scores = []
        for train_idx, val_idx in tscv.split(X_train):
            fold_model = xgb.XGBRegressor(**self.params)
            fold_model.fit(X_train_scaled[train_idx], y_train[train_idx], verbose=False)
            scores.append(fold_model.score(X_train_scaled[val_idx], y_train[val_idx]))

        mean_r2 = float(np.mean(scores))
        print(f"✅ Entry Quality Scorer trained (CV R²={mean_r2:.3f})")
        return mean_r2

    def score_entry(self, features: dict) -> dict:
        """Score a single entry. Returns quality score + action."""
        assert self.is_trained, "Model not trained."
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        raw_score = float(self.model.predict(X_scaled)[0])
        quality = max(0.0, min(1.0, raw_score))

        if quality < 0.5:
            action = "SKIP"
        elif quality < 0.7:
            action = "HALF_SIZE"
        else:
            action = "ENTER_FULL"

        return {
            "score": round(quality, 3),
            "quality_score": round(quality, 3),
            "action": action,
            "size_multiplier": quality if quality >= 0.5 else 0.0,
        }

    def score_batch(self, X: np.ndarray) -> np.ndarray:
        """Score a batch of entries."""
        assert self.is_trained, "Model not trained."
        X_scaled = self.scaler.transform(X)
        return np.clip(self.model.predict(X_scaled), 0.0, 1.0)

    MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

    def save(self, path: str | Path = None):
        if path is None:
            path = self.MODEL_DIR / "entry_scorer_xgb.pkl"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        joblib.dump(self.scaler, path.with_suffix(".scaler.pkl"))
        meta = {"feature_names": self.feature_names, "params": {k: str(v) for k, v in self.params.items()}}
        with open(path.with_suffix(".json"), "w") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, path: str | Path = None) -> "CerebusEntryScorer":
        if path is None:
            path = cls.MODEL_DIR / "entry_scorer_xgb.pkl"
        path = Path(path)
        with open(path.with_suffix(".json")) as f:
            meta = json.load(f)
        inst = cls(params=meta.get("params"))
        inst.model = joblib.load(path)
        inst.scaler = joblib.load(path.with_suffix(".scaler.pkl"))
        inst.feature_names = meta["feature_names"]
        inst.is_trained = True
        return inst
