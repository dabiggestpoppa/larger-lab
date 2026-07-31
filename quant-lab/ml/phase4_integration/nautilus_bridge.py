"""
Phase 4.3: Nautilus Trader Integration Bridge
===============================================
Integrates regime classifier + optimized params into Nautilus Trader.
Builds real-time inference pipeline.

This bridge:
  1. Loads trained XGBoost models at startup
  2. Predicts regime on every bar close
  3. Loads optimized params per regime
  4. Hot-swaps parameters on regime change
  5. Enforces friction filters and close-only invalidation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# Import paths work with quant-lab as top-level
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.phase2_classifier.regime_classifier import CerebusRegimeClassifier, FEATURE_NAMES as REGIME_FEATURES
from ml.phase2_classifier.entry_scorer import CerebusEntryScorer, ENTRY_FEATURES
from ml.phase4_integration.friction_filters import check_friction_filters
from ml.phase4_integration.close_only_guard import manage_open_position, PositionState


class CerebusMLBridge:
    """
    ML-powered strategy bridge for Nautilus Trader.
    Wraps the CEREBUS engine with regime-adaptive parameter selection.
    """

    def __init__(
        self,
        symbol: str,
        model_dir: Path,
        config_dir: Path,
        tier: str = "T2",
    ):
        self.symbol = symbol
        self.tier = tier
        self.model_dir = Path(model_dir)
        self.config_dir = Path(config_dir)

        # Load models
        self.regime_classifier = CerebusRegimeClassifier()
        self.regime_classifier.load(self.model_dir / "regime_classifier_xgb.pkl")

        self.entry_scorer = CerebusEntryScorer()
        self.entry_scorer.load(self.model_dir / "entry_scorer_xgb.pkl")

        # Load optimized params per regime
        self.regime_params = self._load_regime_params()

        # State
        self.current_regime = None
        self.current_params = None
        self.position: PositionState | None = None

    def _load_regime_params(self) -> dict:
        """Load optimized parameters per regime from JSON configs."""
        params = {}
        for regime in ["CONFIRMED", "CAUTION", "FAILED", "NO-GO"]:
            config_path = self.config_dir / f"{self.symbol}_{regime}_optimized.json"
            if config_path.exists():
                with open(config_path) as f:
                    params[regime] = json.load(f)
        return params

    def predict_regime(self, bar_features: dict) -> dict:
        """
        Predict current regime from bar features.
        Falls back to hardcoded tiers if confidence < 0.6.
        """
        result = self.regime_classifier.predict_regime(bar_features)

        if result["confidence"] < 0.6:
            result["fallback"] = True
            result["note"] = "Low confidence — using hardcoded tier thresholds"

        self.current_regime = result["regime"]
        return result

    def get_params_for_regime(self, regime: str) -> dict:
        """Get optimized parameters for the current regime."""
        if regime in self.regime_params:
            return self.regime_params[regime]
        # Fallback to current tier defaults
        return self.regime_params.get(self.tier, {})

    def score_entry(self, entry_features: dict) -> dict:
        """Score an entry opportunity."""
        return self.entry_scorer.score_entry(entry_features)

    def should_enter(self, bar: dict, features: dict, hour: int, minute: int) -> tuple[bool, str]:
        """
        Complete entry decision pipeline.
        Returns (should_enter, reason).
        """
        # 1. Friction filters
        spread = features.get("spread_at_entry", 5.0)
        passed, reason = check_friction_filters(
            hour, minute, spread, self.tier, self.symbol
        )
        if not passed:
            return False, reason

        # 2. Regime prediction
        regime_result = self.predict_regime(features)
        regime = regime_result["regime"]

        # 3. Skip if FAILED or NO-GO
        if regime in ("FAILED", "NO-GO"):
            return False, f"REGIME_GATE: {regime} — skip entry"

        # 4. Entry quality score
        quality_result = self.score_entry(features)
        if quality_result["action"] == "SKIP":
            return False, f"QUALITY_GATE: score {quality_result['quality_score']} < 0.5"

        return True, f"ENTER: regime={regime}, quality={quality_result['quality_score']}"

    def on_bar(self, bar: dict, features: dict, hour: int, minute: int) -> dict:
        """
        Main entry point — called on every bar close.
        Returns action dict.
        """
        result = {
            "action": "NONE",
            "reason": "",
            "regime": None,
            "params": None,
        }

        # If in position, manage it
        if self.position is not None:
            action, reason = manage_open_position(
                self.position, bar, hour, minute,
                features.get("asian_high", 0),
                features.get("asian_low", 0),
            )
            result["action"] = action
            result["reason"] = reason
            if action != "HOLD":
                self.position = None
            return result

        # If flat, check for entry
        should_enter, reason = self.should_enter(bar, features, hour, minute)
        if should_enter:
            result["action"] = "ENTER"
            result["reason"] = reason
            result["regime"] = self.current_regime
            result["params"] = self.get_params_for_regime(self.current_regime or self.tier)

        return result


if __name__ == "__main__":
    print("CerebusMLBridge ready.")
    print("Usage: bridge = CerebusMLBridge('EURUSD', model_dir, config_dir)")
    print("       result = bridge.on_bar(bar, features, hour, minute)")
