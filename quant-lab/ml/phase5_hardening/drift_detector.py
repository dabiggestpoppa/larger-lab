"""
Phase 5.2: PSI Drift Detection
=================================
Monitors feature distribution drift using Population Stability Index.
Alerts if PSI > 0.20 (significant regime shift).
"""
from __future__ import annotations

import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_psi(expected_array: np.ndarray, actual_array: np.ndarray, buckets: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI).

    PSI < 0.1: No significant change
    0.1 <= PSI < 0.2: Moderate change (Monitor)
    PSI >= 0.2: Significant change (Trigger Retraining)
    """
    epsilon = 1e-4

    # Create consistent bins
    breakpoints = np.linspace(
        min(expected_array.min(), actual_array.min()),
        max(expected_array.max(), actual_array.max()),
        buckets + 1,
    )

    expected_pct = np.histogram(expected_array, bins=breakpoints)[0] / len(expected_array)
    actual_pct = np.histogram(actual_array, bins=breakpoints)[0] / len(actual_array)

    # Avoid division by zero
    expected_pct = np.where(expected_pct == 0, epsilon, expected_pct)
    actual_pct = np.where(actual_pct == 0, epsilon, actual_pct)

    psi_value = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi_value)


def check_feature_drift(
    backtest_features: dict[str, np.ndarray],
    live_features: dict[str, np.ndarray],
    threshold: float = 0.20,
) -> dict:
    """
    Check drift for all features.
    Returns drift report.
    """
    report = {"features": {}, "drift_detected": False, "alerts": []}

    for feature_name in backtest_features:
        if feature_name not in live_features:
            continue

        psi = calculate_psi(backtest_features[feature_name], live_features[feature_name])
        status = "OK"
        if psi >= threshold:
            status = "DRIFT"
            report["drift_detected"] = True
            alert = f"🚨 FEATURE DRIFT: {feature_name} PSI={psi:.3f} >= {threshold}"
            report["alerts"].append(alert)
            logger.warning(alert)
        elif psi >= threshold * 0.5:
            status = "MONITOR"

        report["features"][feature_name] = {"psi": round(psi, 4), "status": status}

    return report


def check_rolling_win_rate(
    trade_results: list[float],
    backtest_wr: float,
    window: int = 50,
    confidence: float = 0.95,
) -> dict:
    """
    Check if rolling win rate is within confidence interval of backtest WR.
    trade_results: list of R-multiples (positive = win, negative = loss)
    """
    if len(trade_results) < window:
        return {"status": "INSUFFICIENT_DATA", "n_trades": len(trade_results)}

    recent = trade_results[-window:]
    wr = sum(1 for r in recent if r > 0) / len(recent)

    # Wilson score interval
    from scipy import stats
    z = stats.norm.ppf((1 + confidence) / 2)
    n = len(recent)
    denominator = 1 + z * z / n
    center = (wr + z * z / (2 * n)) / denominator
    margin = z * np.sqrt((wr * (1 - wr) + z * z / (4 * n)) / n) / denominator

    lower = center - margin
    upper = center + margin

    status = "OK"
    if backtest_wr / 100 < lower * 0.9:
        status = "DRIFT_DOWN"
    elif backtest_wr / 100 > upper * 1.1:
        status = "DRIFT_UP"

    return {
        "status": status,
        "rolling_wr": round(wr, 4),
        "backtest_wr": backtest_wr,
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "n_trades": len(trade_results),
    }
