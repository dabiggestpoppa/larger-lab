"""
Phase 2.4: Confidence Calibration
====================================
Calibrate predicted probabilities using isotonic regression.
Maps probability → regime with confidence bands.
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import calibration_curve
import joblib
from pathlib import Path


class ConfidenceCalibrator:
    """
    Calibrates XGBoost output probabilities using isotonic regression.
    Ensures predicted confidence matches empirical frequencies.
    """

    def __init__(self, n_classes: int = 4):
        self.n_classes = n_classes
        self.calibrators = [IsotonicRegression(out_of_bounds="clip") for _ in range(n_classes)]
        self.is_fitted = False

    def fit(self, y_true: np.ndarray, y_prob: np.ndarray):
        """
        Fit isotonic regression per class.
        y_true: integer labels (0-3)
        y_prob: predicted probabilities (n_samples, n_classes)
        """
        for c in range(self.n_classes):
            binary_true = (y_true == c).astype(float)
            self.calibrators[c].fit(y_prob[:, c], binary_true)
        self.is_fitted = True
        print("✅ Confidence calibrator fitted")

    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """Calibrate a probability vector."""
        assert self.is_fitted, "Calibrator not fitted."
        calibrated = np.zeros_like(probs)
        for c in range(self.n_classes):
            calibrated[:, c] = self.calibrators[c].predict(probs[:, c])
        # Renormalize to sum to 1
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return calibrated / row_sums

    def calibrate_single(self, probs: np.ndarray) -> np.ndarray:
        """Calibrate a single probability vector (1D)."""
        assert self.is_fitted, "Calibrator not fitted."
        calibrated = np.array([self.calibrators[c].predict(probs[c]) for c in range(self.n_classes)])
        calibrated = np.clip(calibrated, 0, 1)
        total = calibrated.sum()
        if total > 0:
            calibrated /= total
        return calibrated

    def check_calibration(self, y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict:
        """Check calibration quality. Returns per-class calibration error."""
        results = {}
        for c in range(self.n_classes):
            binary_true = (y_true == c).astype(float)
            prob_true, prob_pred = calibration_curve(binary_true, y_prob[:, c], n_bins=n_bins)
            mean_error = np.mean(np.abs(prob_true - prob_pred))
            results[f"class_{c}"] = {
                "mean_calibration_error": round(float(mean_error), 4),
                "within_3pct": mean_error <= 0.03,
            }
        return results

    def save(self, path: str | Path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.calibrators, path / "calibrators.pkl")
        joblib.dump(self.is_fitted, path / "is_fitted.pkl")

    @classmethod
    def load(cls, path: str | Path) -> "ConfidenceCalibrator":
        path = Path(path)
        inst = cls()
        inst.calibrators = joblib.load(path / "calibrators.pkl")
        inst.is_fitted = bool(joblib.load(path / "is_fitted.pkl"))
        return inst
