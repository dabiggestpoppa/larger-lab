"""
Phase 3 Tests: Bayesian Optimizer + Backtest Objective + Robustness Check
"""
import pytest
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from phase3_optimizer.backtest_objective import create_backtest_objective
from phase3_optimizer.bayesian_optimizer import CerebusBayesianOptimizer, DEFAULT_SEARCH_SPACE
from phase3_optimizer.search_spaces import get_search_space, REGIME_SEARCH_SPACES
from phase3_optimizer.robustness_check import check_robustness


@pytest.fixture
def sample_trades():
    """Create a sample trades DataFrame for testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "entry_price": np.random.uniform(1.0, 2.0, n),
        "exit_price": np.random.uniform(1.0, 2.0, n),
        "direction": np.random.choice([1, -1], n),
        "regime": np.random.choice(["CONFIRMED", "CAUTION", "FAILED"], n),
        "au_value": np.random.uniform(10, 25, n),
        "outcome": np.random.choice(["WIN", "LOSS", "TIME"], n, p=[0.6, 0.3, 0.1]),
        "r_multiple": np.random.normal(1.0, 0.5, n),
    })


class TestBacktestObjective:
    """Tests for the backtest objective function."""

    def test_returns_dict_with_required_keys(self, sample_trades):
        obj = create_backtest_objective(sample_trades)
        result = obj({"au_multiplier": 0.5, "trigger_multiplier": 1.2, "dz_lower_pct": 0.3,
                       "dz_upper_pct": 0.5, "buffer_pips": 5.0, "min_pullback_pct": 0.32,
                       "max_pullback_pct": 0.5})
        assert "sharpe_ratio" in result
        assert "win_rate" in result
        assert "profit_factor" in result
        assert "max_drawdown_pct" in result

    def test_win_rate_between_0_and_1(self, sample_trades):
        obj = create_backtest_objective(sample_trades)
        result = obj({"au_multiplier": 0.5, "trigger_multiplier": 1.2, "dz_lower_pct": 0.3,
                       "dz_upper_pct": 0.5, "buffer_pips": 5.0, "min_pullback_pct": 0.32,
                       "max_pullback_pct": 0.5})
        assert 0 <= result["win_rate"] <= 1

    def test_empty_tr_returns_zeros(self):
        obj = create_backtest_objective(pd.DataFrame())
        result = obj({"au_multiplier": 0.5, "trigger_multiplier": 1.2, "dz_lower_pct": 0.3,
                       "dz_upper_pct": 0.5, "buffer_pips": 5.0, "min_pullback_pct": 0.32,
                       "max_pullback_pct": 0.5})
        assert result["win_rate"] == 0.0
        assert result["sharpe_ratio"] == 0.0

    def test_different_params_produce_different_results(self, sample_trades):
        obj = create_backtest_objective(sample_trades)
        r1 = obj({"au_multiplier": 0.35, "trigger_multiplier": 1.0, "dz_lower_pct": 0.25,
                   "dz_upper_pct": 0.45, "buffer_pips": 3.0, "min_pullback_pct": 0.25,
                   "max_pullback_pct": 0.5})
        r2 = obj({"au_multiplier": 0.65, "trigger_multiplier": 1.5, "dz_lower_pct": 0.40,
                   "dz_upper_pct": 0.60, "buffer_pips": 20.0, "min_pullback_pct": 0.40,
                   "max_pullback_pct": 0.65})
        # Results should differ with different params
        assert r1["sharpe_ratio"] != r2["sharpe_ratio"] or r1["win_rate"] != r2["win_rate"]


class TestSearchSpaces:
    """Tests for regime-specific search spaces."""

    def test_all_regimes_have_spaces(self):
        for regime in ["CONFIRMED", "CAUTION", "FAILED", "NO-GO"]:
            space = get_search_space(regime)
            assert "au_multiplier" in space
            assert "trigger_multiplier" in space
            assert "buffer_pips" in space

    def test_confirmed_has_wider_range_than_no_go(self):
        confirmed = get_search_space("CONFIRMED")
        no_go = get_search_space("NO-GO")
        conf_range = confirmed["au_multiplier"][1] - confirmed["au_multiplier"][0]
        nogo_range = no_go["au_multiplier"][1] - no_go["au_multiplier"][0]
        assert conf_range >= nogo_range

    def test_asset_class_override(self):
        space = get_search_space("CONFIRMED", "forex_major")
        assert "buffer_pips" in space
        # Forex major should have tighter buffer
        assert space["buffer_pips"][1] <= 15.0


class TestRobustnessCheck:
    """Tests for parameter robustness checking."""

    def test_robust_params_pass(self):
        def mock_bt(params):
            return {"sharpe_ratio": 1.5, "win_rate": 0.65, "profit_factor": 3.0, "max_drawdown_pct": 5.0}

        params = {"au_multiplier": 0.50, "trigger_multiplier": 1.2, "buffer_pips": 5.0}
        report = check_robustness(params, mock_bt, perturbation_pct=0.10)
        assert report["is_robust"] is True
        assert len(report["failures"]) == 0

    def test_sensitive_params_fail(self):
        call_count = [0]
        def mock_bt(params):
            call_count[0] += 1
            # Return degraded score when param is perturbed
            if params["au_multiplier"] > 0.55:
                return {"sharpe_ratio": 0.5, "win_rate": 0.3, "profit_factor": 1.0, "max_drawdown_pct": 20.0}
            return {"sharpe_ratio": 1.5, "win_rate": 0.65, "profit_factor": 3.0, "max_drawdown_pct": 5.0}

        params = {"au_multiplier": 0.50, "trigger_multiplier": 1.2}
        report = check_robustness(params, mock_bt, perturbation_pct=0.10)
        assert report["is_robust"] is False
        assert len(report["failures"]) > 0

    def test_report_has_all_tests(self):
        def mock_bt(params):
            return {"sharpe_ratio": 1.5, "win_rate": 0.65, "profit_factor": 3.0, "max_drawdown_pct": 5.0}

        params = {"au_multiplier": 0.50, "trigger_multiplier": 1.2, "buffer_pips": 5.0}
        report = check_robustness(params, mock_bt)
        # 3 params × 2 directions = 6 tests
        assert report["n_tests"] == 6


class TestBayesianOptimizer:
    """Tests for the Optuna Bayesian optimizer."""

    def test_optimizer_initializes(self):
        opt = CerebusBayesianOptimizer("EURUSD", "CONFIRMED", n_trials=10)
        assert opt.asset_name == "EURUSD"
        assert opt.regime == "CONFIRMED"
        assert opt.n_trials == 10

    def test_optimize_runs(self):
        def mock_bt(params):
            return {"sharpe_ratio": 1.5, "win_rate": 0.65, "profit_factor": 3.0, "max_drawdown_pct": 5.0}

        opt = CerebusBayesianOptimizer("EURUSD", "CONFIRMED", n_trials=5)
        result = opt.optimize(mock_bt, directions=["maximize", "maximize", "minimize"])
        assert "best_params" in result or "study" in result

    def test_search_space_used(self):
        custom_space = {"au_multiplier": (0.40, 0.60)}
        opt = CerebusBayesianOptimizer("EURUSD", "CONFIRMED", search_space=custom_space)
        assert opt.search_space == custom_space
