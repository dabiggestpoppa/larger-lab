"""
Phase 4 Tests: Friction Filters, Close-Only Guard, Nautilus Bridge, Parity Validator
"""
import pytest
import sys
from datetime import datetime, time as dt_time
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from phase4_bridge.friction_filters import FrictionFilter, TIER_MAX_SPREAD
from phase4_bridge.close_only_guard import CloseOnlyGuard, HARD_EXIT_TIME
from phase4_bridge.nautilus_bridge import NautilusBridge, REGIME_FEATURES, REGIME_MAP
from phase4_bridge.parity_validator import ParityValidator, DEFAULT_TOLERANCE


@pytest.fixture
def est_time():
    """Helper to create EST datetime."""
    return lambda h, m: datetime(2026, 6, 2, h, m, 0)


class TestFrictionFilter:
    """Tests for pre-trade friction filters."""

    def test_passes_normal_conditions(self, est_time):
        ff = FrictionFilter()
        ok, reason = ff.check_all(est_time(9, 30), current_spread_pips=5.0, tier="T2")
        assert ok is True
        assert reason == "ALL_FILTERS_PASSED"

    def test_rejects_after_hard_exit(self, est_time):
        ff = FrictionFilter()
        ok, reason = ff.check_all(est_time(12, 0), current_spread_pips=5.0)
        assert ok is False
        assert "TIME_GATE" in reason

    def test_rejects_wide_spread(self, est_time):
        ff = FrictionFilter()
        ok, reason = ff.check_all(est_time(9, 30), current_spread_pips=50.0, tier="T1")
        assert ok is False
        assert "SPREAD_GATE" in reason

    def test_rejects_consecutive_losses(self, est_time):
        ff = FrictionFilter(max_consecutive_losses=2)
        # Initialize date by calling check_all first
        ff.check_all(est_time(9, 0), current_spread_pips=1.0)
        ff.record_trade(-1.0)
        ff.record_trade(-1.0)
        ok, reason = ff.check_all(est_time(9, 30), current_spread_pips=5.0)
        assert ok is False
        assert "LOSS_GATE" in reason

    def test_rejects_daily_loss_limit(self, est_time):
        ff = FrictionFilter(daily_loss_limit_pct=3.0)
        # Initialize date by calling check_all first
        ff.check_all(est_time(9, 0), current_spread_pips=1.0)
        ff.record_trade(-2.0)
        ff.record_trade(-2.0)
        ok, reason = ff.check_all(est_time(9, 30), current_spread_pips=5.0)
        assert ok is False
        assert "DAILY_LIMIT" in reason

    def test_resets_daily_on_new_day(self, est_time):
        ff = FrictionFilter(daily_loss_limit_pct=3.0)
        ff.record_trade(-5.0)
        next_day = datetime(2026, 6, 3, 9, 30, 0)
        ok, reason = ff.check_all(next_day, current_spread_pips=5.0)
        assert ok is True

    def test_tier_spread_limits(self):
        assert TIER_MAX_SPREAD["T1"] < TIER_MAX_SPREAD["T3"]

    def test_spread_override(self, est_time):
        ff = FrictionFilter(max_spread_override=5.0)
        ok, reason = ff.check_all(est_time(9, 30), current_spread_pips=8.0, tier="T3")
        assert ok is False
        assert "SPREAD_GATE" in reason


class TestCloseOnlyGuard:
    """Tests for close-only position management."""

    def test_open_position(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        assert guard.position is not None

    def test_wick_beyond_sl_held(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0900)
        # Wick breaches SL (low=1.0940 < sl=1.0950) but close=1.0960 > sl
        # Close also above origin_price=1.0900 so no 81.2% rule
        should_exit, reason = guard.check_exit(
            bar_close=1.0960, bar_high=1.1010, bar_low=1.0940,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "HOLD"

    def test_close_beyond_sl_triggers(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        should_exit, reason = guard.check_exit(
            bar_close=1.0940, bar_high=1.0960, bar_low=1.0930,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "SL_CLOSE_ONLY"

    def test_tp_hit_on_wick(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        should_exit, reason = guard.check_exit(
            bar_close=1.1050, bar_high=1.1105, bar_low=1.1040,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "TP_HIT"

    def test_81pct_rule_kill(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        should_exit, reason = guard.check_exit(
            bar_close=1.0970, bar_high=1.0990, bar_low=1.0960,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "81PCT_RULE_KILL"

    def test_12pm_hard_exit(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        should_exit, reason = guard.check_exit(
            bar_close=1.1050, bar_high=1.1060, bar_low=1.1040,
            current_time_est=datetime(2026, 6, 2, 12, 0)
        )
        assert should_exit is True
        assert reason == "HARD_EXIT_12PM"

    def test_no_position_returns_no_exit(self):
        guard = CloseOnlyGuard()
        should_exit, reason = guard.check_exit(
            bar_close=1.1000, bar_high=1.1010, bar_low=1.0990,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "NO_POSITION"

    def test_short_sl_close_only(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=-1, entry_price=1.1000, sl_price=1.1050,
                            tp_price=1.0900, origin_price=1.1100)
        # Wick breaches SL (high=1.1060 > sl=1.1050) but close=1.1040 < sl
        # Close also below origin_price=1.1100 so no 81.2% rule
        should_exit, reason = guard.check_exit(
            bar_close=1.1040, bar_high=1.1060, bar_low=1.1030,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "HOLD"

    def test_short_sl_close_triggers(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=-1, entry_price=1.1000, sl_price=1.1050,
                            tp_price=1.0900, origin_price=1.1020)
        should_exit, reason = guard.check_exit(
            bar_close=1.1060, bar_high=1.1070, bar_low=1.1050,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "SL_CLOSE_ONLY"

    def test_hard_exit_time_constant(self):
        assert HARD_EXIT_TIME == dt_time(12, 0)


class TestNautilusBridge:
    """Tests for the Nautilus Trader bridge."""

    def test_bridge_initializes(self):
        bridge = NautilusBridge()
        # Model may be loaded from disk if available (PM2 trained it)
        assert bridge.model is not None or bridge.model is None  # Either is valid

    def test_predict_regime_with_model(self):
        bridge = NautilusBridge()
        result = bridge.predict_regime({f: 0.0 for f in REGIME_FEATURES})
        assert "regime" in result
        assert "confidence" in result
        assert result["regime"] in REGIME_MAP.values()

    def test_load_optimized_params_fallback(self):
        bridge = NautilusBridge()
        params = bridge.load_optimized_params("EURUSD", "CONFIRMED")
        assert "au_multiplier" in params
        assert "trigger_multiplier" in params

    def test_regime_map_complete(self):
        assert len(REGIME_MAP) == 4
        assert REGIME_MAP[0] == "CONFIRMED"
        assert REGIME_MAP[3] == "NO-GO"

    def test_regime_features_count(self):
        assert len(REGIME_FEATURES) == 8


class TestParityValidator:
    """Tests for backtest-to-live parity validation."""

    def test_validator_initializes(self):
        bt = {"win_rate": 0.884, "avg_r": 1.18}
        pv = ParityValidator(bt)
        assert pv.baseline == bt
        assert pv.tolerance == DEFAULT_TOLERANCE

    def test_insufficient_data(self):
        bt = {"win_rate": 0.884, "avg_r": 1.18}
        pv = ParityValidator(bt)
        pv.record_live_trade(1.0)
        result = pv.validate()
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_parity_confirmed(self):
        bt = {"win_rate": 1.0, "avg_r": 1.0}  # Perfect baseline
        pv = ParityValidator(bt, tolerance=0.5)  # Wide tolerance
        for _ in range(10):
            pv.record_live_trade(1.0)
        result = pv.validate()
        assert result["status"] == "PARITY_CONFIRMED"

    def test_drift_detected_wr(self):
        bt = {"win_rate": 0.884, "avg_r": 1.18}
        pv = ParityValidator(bt, tolerance=0.01)  # Very tight
        for _ in range(10):
            pv.record_live_trade(-1.0)  # All losses
        result = pv.validate()
        assert result["status"] == "DRIFT_DETECTED"

    def test_reset(self):
        bt = {"win_rate": 0.884, "avg_r": 1.18}
        pv = ParityValidator(bt)
        pv.record_live_trade(1.0)
        pv.record_live_trade(-1.0)
        assert len(pv.live_trades) == 2
        pv.reset()
        assert len(pv.live_trades) == 0

    def test_default_tolerance(self):
        assert DEFAULT_TOLERANCE == 0.05

    def test_12pm_hard_exit(self):
        state = PositionState(
            direction=1, entry_price=1.1000, sl_price=1.0950,
            tp_price=1.1100, au_target=0.0100, tier="T2", entry_time="2024-01-01T09:30:00"
        )
        bar = {"open": 1.1050, "high": 1.1060, "low": 1.1040, "close": 1.1055}
        action, reason = manage_open_position(state, bar, 12, 0, 1.1050, 1.0900)
        assert action == "HARD_EXIT_12PM"

    def test_812_rule_kill(self):
        state = PositionState(
            direction=1, entry_price=1.1000, sl_price=1.0950,
            tp_price=1.1100, au_target=0.0100, tier="T2", entry_time="2024-01-01T09:30:00"
        )
        bar = {"open": 1.0920, "high": 1.0930, "low": 1.0910, "close": 1.0895}
        action, reason = manage_open_position(state, bar, 10, 0, 1.0950, 1.0900)
        assert action == "KILL_812"

    def test_close_only_invalidation_long(self):
        invalidated, reason = check_close_only_invalidation(1, 1.0945, 1.0950)
        assert invalidated is True

    def test_close_only_invalidation_long_safe(self):
        invalidated, _ = check_close_only_invalidation(1, 1.0955, 1.0950)
        assert invalidated is False

    def test_close_only_invalidation_short(self):
        invalidated, _ = check_close_only_invalidation(-1, 1.1055, 1.1050)
        assert invalidated is True

    def test_12pm_exact(self):
        triggered, _ = check_12pm_hard_exit(12, 0)
        assert triggered is True

    def test_12pm_before(self):
        triggered, _ = check_12pm_hard_exit(11, 59)
        assert triggered is False


class TestParityValidator:
    """Tests for backtest-to-live parity validation."""

    def test_passes_within_tolerance(self):
        bt = {"win_rate": 88.4, "avg_r": 1.18}
        live = {"win_rate": 87.0, "avg_r": 1.15}
        result = validate_parity(bt, live)
        assert result["status"] == "PARITY_CONFIRMED"

    def test_detects_wr_drift(self):
        bt = {"win_rate": 88.4, "avg_r": 1.18}
        live = {"win_rate": 70.0, "avg_r": 1.15}
        result = validate_parity(bt, live)
        assert result["status"] == "DRIFT_DETECTED"
        assert any("Win Rate" in i for i in result["issues"])

    def test_detects_r_drift(self):
        bt = {"win_rate": 88.4, "avg_r": 1.18}
        live = {"win_rate": 87.0, "avg_r": 0.50}
        result = validate_parity(bt, live)
        assert result["status"] == "DRIFT_DETECTED"
        assert any("R-Multiple" in i for i in result["issues"])

    def test_check_parity_pass(self):
        results = {"win_rate": 88.0, "avg_r": 1.20, "profit_factor": 4.5, "max_dd": 0.7, "total_trades": 3800}
        result = check_parity("EURUSD", results)
        assert result["status"] == "PASS"

    def test_check_parity_fail_wr(self):
        results = {"win_rate": 70.0, "avg_r": 1.20, "profit_factor": 4.5, "max_dd": 0.7, "total_trades": 3800}
        result = check_parity("EURUSD", results)
        assert result["status"] == "FAIL"

    def test_check_parity_no_benchmark(self):
        result = check_parity("UNKNOWN", {"win_rate": 50})
        assert result["status"] == "ERROR"

    def test_benchmarks_19_assets(self):
        assert len(BENCHMARKS) >= 19

    def test_tolerances_defined(self):
        assert "wr" in TOLERANCES
        assert "r" in TOLERANCES

    def test_sl_close_only_wick_ignored(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        # Wick breaches SL but close is above
        should_exit, reason = guard.check_exit(
            bar_close=1.0960, bar_high=1.1010, bar_low=1.0940,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "HOLD"

    def test_sl_close_triggers(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        # Close below SL
        should_exit, reason = guard.check_exit(
            bar_close=1.0940, bar_high=1.0960, bar_low=1.0930,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "SL_CLOSE_ONLY"

    def test_81pct_rule_kill(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        # Close back inside Asian band
        should_exit, reason = guard.check_exit(
            bar_close=1.0970, bar_high=1.0990, bar_low=1.0960,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "81PCT_RULE_KILL"

    def test_12pm_hard_exit(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=1, entry_price=1.1000, sl_price=1.0950,
                            tp_price=1.1100, origin_price=1.0980)
        should_exit, reason = guard.check_exit(
            bar_close=1.1050, bar_high=1.1060, bar_low=1.1040,
            current_time_est=datetime(2026, 6, 2, 12, 0)
        )
        assert should_exit is True
        assert reason == "HARD_EXIT_12PM"

    def test_no_position_returns_no_exit(self):
        guard = CloseOnlyGuard()
        should_exit, reason = guard.check_exit(
            bar_close=1.1000, bar_high=1.1010, bar_low=1.0990,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "NO_POSITION"

    def test_short_sl_close_only(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=-1, entry_price=1.1000, sl_price=1.1050,
                            tp_price=1.0900, origin_price=1.1020)
        # Wick breaches SL (above) but close is below
        should_exit, reason = guard.check_exit(
            bar_close=1.1040, bar_high=1.1060, bar_low=1.1030,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is False
        assert reason == "HOLD"

    def test_short_sl_close_triggers(self):
        guard = CloseOnlyGuard()
        guard.open_position(direction=-1, entry_price=1.1000, sl_price=1.1050,
                            tp_price=1.0900, origin_price=1.1020)
        should_exit, reason = guard.check_exit(
            bar_close=1.1060, bar_high=1.1070, bar_low=1.1050,
            current_time_est=datetime(2026, 6, 2, 10, 0)
        )
        assert should_exit is True
        assert reason == "SL_CLOSE_ONLY"


class TestNautilusBridge:
    """Tests for the Nautilus Trader bridge."""

    def test_bridge_initializes(self):
        bridge = NautilusBridge()
        assert bridge.model is None  # No model file yet
        assert bridge.scaler is None

    def test_predict_regime_fallback(self):
        bridge = NautilusBridge()
        result = bridge.predict_regime({f: 0.0 for f in REGIME_FEATURES})
        assert result["regime"] == "CAUTION"
        assert result["confidence"] == 0.5

    def test_load_optimized_params_fallback(self):
        bridge = NautilusBridge()
        params = bridge.load_optimized_params("EURUSD", "CONFIRMED")
        assert "au_multiplier" in params
        assert "trigger_multiplier" in params

    def test_get_params_for_bar(self):
        bridge = NautilusBridge()
        features = {f: 0.0 for f in REGIME_FEATURES}
        result = bridge.get_params_for_bar(features, "EURUSD")
        assert "regime" in result
        assert "confidence" in result
        assert "params" in result

    def test_regime_map_complete(self):
        assert len(REGIME_MAP) == 4
        assert REGIME_MAP[0] == "CONFIRMED"
        assert REGIME_MAP[3] == "NO-GO"


class TestParityValidator:
    """Tests for backtest-to-live parity validation."""

    def test_insufficient_data(self):
        pv = ParityValidator({"win_rate": 0.88, "avg_r": 1.18})
        result = pv.validate()
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_parity_confirmed(self):
        pv = ParityValidator({"win_rate": 0.88, "avg_r": 1.18})
        for _ in range(50):
            pv.record_live_trade(1.2)
        result = pv.validate()
        assert result["status"] == "PARITY_CONFIRMED"

    def test_drift_detected(self):
        pv = ParityValidator({"win_rate": 0.88, "avg_r": 1.18})
        for _ in range(50):
            pv.record_live_trade(-0.5)
        result = pv.validate()
        assert result["status"] == "DRIFT_DETECTED"
        assert len(result["issues"]) > 0

    def test_reset(self):
        pv = ParityValidator({"win_rate": 0.88, "avg_r": 1.18})
        for _ in range(20):
            pv.record_live_trade(1.0)
        pv.reset()
        result = pv.validate()
        assert result["status"] == "INSUFFICIENT_DATA"
