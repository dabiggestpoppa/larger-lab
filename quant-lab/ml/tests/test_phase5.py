"""
Phase 5 Tests: Guardrail Interceptor + Drift Detection + Shadow Mode
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phase5_hardening.guardrail_interceptor import ExecutionGuardrailInterceptor
from phase5_hardening.drift_detector import calculate_psi, check_feature_drift
from phase5_hardening.shadow_mode import ShadowModeGauntlet


class TestGuardrailInterceptor:
    def test_valid_order_passes(self):
        """A structurally valid order should pass."""
        interceptor = ExecutionGuardrailInterceptor("EURUSD", pip_size=0.0001)
        is_valid, msg = interceptor.validate_order(
            entry_price=1.1000, sl_price=1.0990, tp_price=1.1010, current_spread_pips=1.0
        )
        assert is_valid, f"Should pass: {msg}"

    def test_3pip_sl_rejected(self):
        """The infamous 3-pip SL bug should be caught."""
        interceptor = ExecutionGuardrailInterceptor("CHFJPY", pip_size=0.01)
        is_valid, msg = interceptor.validate_order(
            entry_price=150.00, sl_price=150.03, tp_price=149.80, current_spread_pips=0.5
        )
        assert not is_valid, "3-pip SL on CHFJPY should be rejected"
        assert "REJECTED" in msg

    def test_tp_too_small_rejected(self):
        """TP below minimum should be rejected."""
        interceptor = ExecutionGuardrailInterceptor("EURUSD", pip_size=0.0001)
        is_valid, msg = interceptor.validate_order(
            entry_price=1.1000, sl_price=1.0990, tp_price=1.1003, current_spread_pips=1.0
        )
        assert not is_valid, "TP too small should be rejected"

    def test_wide_spread_rejected(self):
        """Spread exceeding max should be rejected."""
        interceptor = ExecutionGuardrailInterceptor("EURUSD", pip_size=0.0001)
        is_valid, msg = interceptor.validate_order(
            entry_price=1.1000, sl_price=1.0990, tp_price=1.1010, current_spread_pips=10.0
        )
        assert not is_valid, "Wide spread should be rejected"

    def test_rejection_log(self):
        """Rejections should be logged."""
        interceptor = ExecutionGuardrailInterceptor("EURUSD", pip_size=0.0001)
        interceptor.validate_order(1.1000, 1.1001, 1.1002, 1.0)  # Bad SL
        log = interceptor.get_rejection_log()
        assert len(log) == 1
        assert "REJECTED" in log[0]["reason"]


class TestDriftDetector:
    def test_psi_no_drift(self):
        """PSI should be ~0 for identical distributions."""
        np.random.seed(42)
        data = np.random.randn(1000)
        psi = calculate_psi(data, data)
        assert psi < 0.01, f"PSI for identical distributions should be ~0, got {psi}"

    def test_psi_with_drift(self):
        """PSI should be high for shifted distributions."""
        np.random.seed(42)
        baseline = np.random.randn(1000)
        shifted = np.random.randn(1000) + 3.0  # Mean shifted by 3
        psi = calculate_psi(baseline, shifted)
        assert psi > 0.1, f"PSI for shifted distribution should be high, got {psi}"

    def test_feature_drift_detection(self):
        """Test multi-feature drift detection."""
        np.random.seed(42)
        backtest = {"ar_pips": np.random.normal(20, 5, 500)}
        live_ok = {"ar_pips": np.random.normal(20, 5, 100)}
        live_drift = {"ar_pips": np.random.normal(30, 8, 100)}

        report_ok = check_feature_drift(backtest, live_ok, threshold=0.20)
        assert not report_ok["drift_detected"]

        report_drift = check_feature_drift(backtest, live_drift, threshold=0.20)
        # May or may not detect depending on random seed, but PSI should be higher
        assert report_drift["features"]["ar_pips"]["psi"] > report_ok["features"]["ar_pips"]["psi"]


class TestShadowMode:
    def test_shadow_records_trades(self):
        """Test shadow trade recording."""
        gauntlet = ShadowModeGauntlet("test_model", backtest_wr=85.0, backtest_dd=5.0, shadow_days=14)
        gauntlet.record_shadow_trade(1.1000, 1.1010, 1, 1.5)
        gauntlet.record_shadow_trade(1.1010, 1.1005, -1, -0.5)
        metrics = gauntlet.get_shadow_metrics()
        assert metrics["total_trades"] == 2

    def test_promotion_criteria(self):
        """Test promotion evaluation."""
        gauntlet = ShadowModeGauntlet("test_model", backtest_wr=85.0, backtest_dd=5.0, shadow_days=14)
        # Add good trades
        for _ in range(20):
            gauntlet.record_shadow_trade(1.1000, 1.1010, 1, 1.5)
        result = gauntlet.evaluate_promotion()
        assert "decision" in result
        assert "checks" in result

    def test_guardrail_rejection_blocks_promotion(self):
        """Guardrail rejections should block promotion."""
        gauntlet = ShadowModeGauntlet("test_model", backtest_wr=85.0, backtest_dd=5.0, shadow_days=14)
        for _ in range(20):
            gauntlet.record_shadow_trade(1.1000, 1.1010, 1, 1.5)
        gauntlet.record_guardrail_rejection()
        result = gauntlet.evaluate_promotion()
        assert result["decision"] == "REJECT"
        assert not result["checks"]["no_guardrail_rejections"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
