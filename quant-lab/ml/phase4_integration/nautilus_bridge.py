"""
Phase 4.3: Nautilus Trader Execution Bridge
==============================================
Connects ML regime predictions to execution.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

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


class CerebusMLBridge:
    """Bridge between ML predictions and execution."""

    def __init__(self, model_path=None, scaler_path=None, params_dir=None):
        self.model = None
        self.scaler = None

    def predict_regime(self, features: dict) -> dict:
        """Predict regime from features. Fallback when no model loaded."""
        return {"regime": "CAUTION", "confidence": 0.5, "all_probs": {}}

    def load_optimized_params(self, asset: str, regime: str) -> dict:
        """Load optimized params. Fallback defaults."""
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
        """Full pipeline: predict regime -> load params."""
        regime_result = self.predict_regime(features)
        params = self.load_optimized_params(asset, regime_result["regime"])
        return {
            "regime": regime_result["regime"],
            "confidence": regime_result["confidence"],
            "params": params,
        }
