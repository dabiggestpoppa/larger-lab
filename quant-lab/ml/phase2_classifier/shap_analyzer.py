"""
Phase 2.3: SHAP Analysis
==========================
Model interpretability + audit trail for prop firm compliance.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.preprocessing import StandardScaler


class ShapAnalyzer:
    """SHAP-based feature importance for regime classifier and entry scorer."""

    def __init__(self, model, scaler: StandardScaler, feature_names: list[str]):
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names
        self.explainer = None

    def fit_explainer(self, X_background: np.ndarray):
        """Initialize SHAP TreeExplainer with background data."""
        self.explainer = shap.TreeExplainer(self.model)

    def get_shap_values(self, X: np.ndarray) -> np.ndarray:
        """Compute SHAP values for input data."""
        if self.explainer is None:
            self.fit_explainer(X)
        return self.explainer.shap_values(X)

    def get_feature_importance(self, X: np.ndarray = None) -> pd.DataFrame:
        """Get mean absolute SHAP-based feature importance."""
        if X is None:
            raise ValueError("Need data to compute SHAP importance")
        shap_vals = self.get_shap_values(X)
        # For multi-class, shap_vals is a list of arrays (one per class)
        if isinstance(shap_vals, list):
            mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_vals], axis=0)
        else:
            mean_abs = np.abs(shap_vals).mean(axis=0)

        importance = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False)
        return importance

    def save_shap_plot(self, X: np.ndarray, output_path: str | Path):
        """Save SHAP summary plot as HTML."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        shap_vals = self.get_shap_values(X)
        output_path = Path(output_path)

        fig, ax = plt.subplots(figsize=(10, 6))
        if isinstance(shap_vals, list):
            # Use class 0 (CONFIRMED) for visualization
            shap.summary_plot(shap_vals[0], X, feature_names=self.feature_names, show=False)
        else:
            shap.summary_plot(shap_vals, X, feature_names=self.feature_names, show=False)
        plt.tight_layout()
        fig.savefig(output_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"✅ SHAP plot saved: {output_path.with_suffix('.png')}")
