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

from phase4_integration.friction_filters import check_friction_filters, TIER_MAX_SPREAD
from phase4_integration.close_only_guard import (
    manage_open_position, PositionState, check_close_only_invalidation,
    check_812_rule, check_12pm_hard_exit, check_tp_hit
)
from phase4_integration.nautilus_bridge import CerebusMLBridge
from phase4_integration.parity_validator import validate_parity, BacktestMetrics, LiveMetrics, compute_metrics_from_trades


class TestFrictionFilters:
    """Tests for pre-trade friction filters."""

    def test_passes_normal_conditions(self):
        ok, reason = check_friction_filters(
            current_hour=9, current_minute=30,
            current_spread_pips=5.0, tier="T2", symbol="EURUSD"
        )
        assert ok is True
        assert "PASSED" in reason

    def test_rejects_after_hard_exit(self):
        ok, reason = check_friction_filters(
            current_hour=12, current_minute=0,
            current_spread_pips=5.0, tier="T1", symbol="EURUSD"
        )
        assert ok is False
        assert "TIME_GATE" in reason

    def test_rejects_wide_spread(self):
        ok, reason = check_friction_filters(
            current_hour=9, current_minute=30,
            current_spread_pips=50.0, tier="T1", symbol="EURUSD"
        )
        assert ok is False
        assert "SPREAD_GATE" in reason

    def test_tighter_spread_for_t1(self):
        ok_t2, _ = check_friction_filters(
            current_hour=9, current_minute=0,
            current_spread_pips=12.0, tier="T2", symbol="EURUSD"
        )
        ok_t1, _ = check_friction_filters(
            current_hour=9, current_minute=0,
            current_spread_pips=12.0, tier="T1", symbol="EURUSD"
        )
        assert ok_t2 is True
        assert ok_t1 is False

    def test_tier_spread_limits_ordered(self):
        assert TIER_MAX_SPREAD["T1"] < TIER_MAX_SPREAD["T2"]
        assert TIER_MAX_SPREAD["T2"] < TIER_MAX_SPREAD["T3"]

    def test_slippage_gate(self):
        ok, reason = check_friction_filters(
            current_hour=9, current_minute=0,
            current_spread_pips=5.0, tier="T2", symbol="EURUSD",
            simulated_slippage_pips=5.0
        )
        assert ok is False
        assert "SLIPPAGE_GATE" in reason


class TestCloseOnlyGuard:
    """Tests for close-only position management."""

    def test_wick_beyond_sl_held(self):
        state = PositionState(
            direction=1, entry_price=1.1000, sl_price=1.0950,
            tp_price=1.1100, au_target=0.0100, tier="T2", entry_time="2024-01-01T09:30:00"
        )
        bar = {"open": 1.0960, "high": 1.0970, "low": 1.0940, "close": 1.0955}
        action, reason = manage_open_position(state, bar, 10, 0, 1.1050, 1.0900)
        assert action == "HOLD"

    def test_close_beyond_sl_invalidated(self):
        state = PositionState(
            direction=1, entry_price=1.1000, sl_price=1.0950,
            tp_price=1.1100, au_target=0.0100, tier="T2", entry_time="2024-01-01T09:30:00"
        )
        bar = {"open": 1.0960, "high": 1.0970, "low": 1.0940, "close": 1.0945}
        action, reason = manage_open_position(state, bar, 10, 0, 1.1050, 1.0900)
        assert action == "SL_HIT"

    def test_tp_hit_on_wick(self):
        state = PositionState(
            direction=1, entry_price=1.1000, sl_price=1.0950,
            tp_price=1.1100, au_target=0.0100, tier="T2", entry_time="2024-01-01T09:30:00"
        )
        bar = {"open": 1.1050, "high": 1.1105, "low": 1.1040, "close": 1.1080}
        action, reason = manage_open_position(state, bar, 10, 0, 1.1050, 1.0900)
        assert action == "TP_HIT"

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
        bt = BacktestMetrics(win_rate=88.4, avg_r=1.18, profit_factor=4.18, max_dd_pct=0.8, total_trades=3842)
        live = LiveMetrics(win_rate=87.0, avg_r=1.15, profit_factor=4.0, max_dd_pct=0.9, total_trades=3700)
        result = validate_parity(bt, live)
        assert result.status == "PASS"

    def test_detects_wr_drift(self):
        bt = BacktestMetrics(win_rate=88.4, avg_r=1.18, profit_factor=4.18, max_dd_pct=0.8, total_trades=3842)
        live = LiveMetrics(win_rate=70.0, avg_r=1.15, profit_factor=4.0, max_dd_pct=0.9, total_trades=3700)
        result = validate_parity(bt, live)
        assert result.status in ("DRIFT_DETECTED", "FAIL")

    def test_detects_r_drift(self):
        bt = BacktestMetrics(win_rate=88.4, avg_r=1.18, profit_factor=4.18, max_dd_pct=0.8, total_trades=3842)
        live = LiveMetrics(win_rate=87.0, avg_r=0.50, profit_factor=4.0, max_dd_pct=0.9, total_trades=3700)
        result = validate_parity(bt, live)
        assert result.status in ("DRIFT_DETECTED", "FAIL")

    def test_pf_floor(self):
        bt = BacktestMetrics(win_rate=88.4, avg_r=1.18, profit_factor=4.18, max_dd_pct=0.8, total_trades=3842)
        live = LiveMetrics(win_rate=87.0, avg_r=1.15, profit_factor=1.5, max_dd_pct=0.9, total_trades=3700)
        result = validate_parity(bt, live)
        assert any("Profit Factor" in i for i in result.issues)

    def test_compute_metrics_from_trades(self):
        trades = [
            {"outcome": "WIN", "r_multiple": 1.5, "pnl": 150},
            {"outcome": "WIN", "r_multiple": 1.0, "pnl": 100},
            {"outcome": "LOSS", "r_multiple": -1.0, "pnl": -100},
            {"outcome": "WIN", "r_multiple": 2.0, "pnl": 200},
        ]
        metrics = compute_metrics_from_trades(trades)
        assert metrics.win_rate == 75.0
        assert metrics.total_trades == 4

    def test_compute_metrics_empty(self):
        metrics = compute_metrics_from_trades([])
        assert metrics.total_trades == 0

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
