"""
Phase 4.3: Nautilus Trader Execution Bridge
==============================================
Connects ML regime predictions + optimized params to Nautilus Trader.
Loads regime classifier, predicts regime per bar, selects params, submits orders.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Feature names expected by the regime classifier
REGIME_FEATURES = [
    "asian_range_pips",
    "vol_ratio_3am_9am",
    "hour_est",
    "spread_vs_20d_avg",
    "impulse_to_ar_ratio",
    "day_of_week",
    "consecutive_losses",
    "prior_session_wr",
]

REGIME_MAP = {0: "CONFIRMED", 1: "CAUTION", 2: "FAILED", 3: "NO-GO"}


class NautilusBridge:
    """
    Bridge between ML predictions and Nautilus Trader execution.
    """

    def __init__(
        self,
        model_path: str = "quant-lab/ml/models/regime_classifier_xgb.pkl",
        scaler_path: str = "quant-lab/ml/models/scaler.pkl",
        params_dir: str = "quant-lab/ml/configs/optimized_params",
    ):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.params_dir = Path(params_dir)
        self.model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        """Load trained regime classifier and scaler."""
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            logger.info(f"Loaded regime model from {self.model_path}")
        else:
            logger.warning(f"Model not found at {self.model_path}. Using fallback.")

        if self.scaler_path.exists():
            self.scaler = joblib.load(self.scaler_path)
            logger.info(f"Loaded scaler from {self.scaler_path}")

    def predict_regime(self, features: dict) -> dict:
        """
        Predict regime from feature dict.

        Returns
        -------
        dict with regime, confidence, all_probs
        """
        if self.model is None:
            return {"regime": "CAUTION", "confidence": 0.5, "all_probs": {}}

        X = np.array([[features.get(f, 0.0) for f in REGIME_FEATURES]])
        if self.scaler is not None:
            X = self.scaler.transform(X)

        probs = self.model.predict_proba(X)[0]
        pred_class = int(np.argmax(probs))

        return {
            "regime": REGIME_MAP.get(pred_class, "CAUTION"),
            "confidence": float(probs[pred_class]),
            "all_probs": {REGIME_MAP.get(i, f"CLASS_{i}"): float(p) for i, p in enumerate(probs)},
        }

    def load_optimized_params(self, asset: str, regime: str) -> dict:
        """
        Load optimized parameters for an asset/regime combination.

        Falls back to hardcoded defaults if no optimized params exist.
        """
        params_file = self.params_dir / f"{asset}_{regime}.json"
        if params_file.exists():
            import json
            with open(params_file) as f:
                return json.load(f)

        # Fallback defaults
        return {
            "au_multiplier": 0.50,
            "trigger_multiplier": 1.2,
            "dz_lower_pct": 0.30,
            "dz_upper_pct": 0.50,
            "buffer_pips": 5.0,
            "min_pullback_pct": 0.32,
            "max_pullback_pct": 0.50,
        }

    def get_params_for_bar(self, features: dict, asset: str) -> dict:
        """
        Full pipeline: predict regime -> load optimized params.

        Returns
        -------
        dict with regime, confidence, and optimized params
        """
        regime_result = self.predict_regime(features)
        regime = regime_result["regime"]
        params = self.load_optimized_params(asset, regime)
        return {
            "regime": regime,
            "confidence": regime_result["confidence"],
            "params": params,
        }
