"""
Tests for Phase 1B: Macro Feature Engine
==========================================
Validates that macro features are computed correctly.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the macro feature engine
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1_data"))

from macro_feature_engine import (
    compute_mlr,
    compute_fib_targets,
    compute_distance_features,
    compute_ilm_state,
    compute_regime_ratio,
    compute_time_blocks,
    get_pip_multiplier,
)


@pytest.fixture
def sample_eur_usd_data():
    """Create sample EURUSD M15 data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=1000, freq="5min", tz="UTC")
    df = pd.DataFrame({
        "open": np.random.randn(1000).cumsum() * 0.001 + 1.1,
        "high": np.random.randn(1000).cumsum() * 0.001 + 1.101,
        "low": np.random.randn(1000).cumsum() * 0.001 + 1.099,
        "close": np.random.randn(1000).cumsum() * 0.001 + 1.1,
        "volume": np.random.randint(100, 1000, 1000),
    }, index=dates)
    # Ensure high >= low
    df["high"] = df[["open", "close", "high"]].max(axis=1) + 0.0005
    df["low"] = df[["open", "close", "low"]].min(axis=1) - 0.0005
    return df


@pytest.fixture
def sample_jpy_data():
    """Create sample USDJPY M15 data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=500, freq="5min", tz="UTC")
    df = pd.DataFrame({
        "open": np.random.randn(500).cumsum() * 0.01 + 150.0,
        "high": np.random.randn(500).cumsum() * 0.01 + 150.1,
        "low": np.random.randn(500).cumsum() * 0.01 + 149.9,
        "close": np.random.randn(500).cumsum() * 0.01 + 150.0,
        "volume": np.random.randint(100, 1000, 500),
    }, index=dates)
    df["high"] = df[["open", "close", "high"]].max(axis=1) + 0.05
    df["low"] = df[["open", "close", "low"]].min(axis=1) - 0.05
    return df


class TestPipMultiplier:
    def test_standard_pair(self):
        assert get_pip_multiplier("EURUSD") == 10000

    def test_jpy_pair(self):
        assert get_pip_multiplier("USDJPY") == 100

    def test_gold(self):
        assert get_pip_multiplier("XAUUSD") == 10

    def test_crypto(self):
        assert get_pip_multiplier("BTCUSD") == 1

    def test_unknown(self):
        assert get_pip_multiplier("UNKNOWN") == 10000


class TestMLR:
    def test_mlr_columns_added(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        assert "mlr_high" in df.columns
        assert "mlr_low" in df.columns
        assert "mlr_range" in df.columns
        assert "mlr_mid" in df.columns
        assert "bias" in df.columns

    def test_mlr_forward_filled(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        # MLR should be forward-filled (not all NaN)
        assert df["mlr_high"].notna().sum() > 0

    def test_mlr_range_positive(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        valid = df["mlr_range"].dropna()
        assert (valid >= 0).all()

    def test_bias_values(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        valid_bias = df["bias"].dropna()
        assert set(valid_bias.unique()).issubset({"BULLISH", "BEARISH"})


class TestFibTargets:
    def test_fib_columns_added(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        df = compute_fib_targets(df)
        assert "target_25" in df.columns
        assert "target_50" in df.columns
        assert "target_100" in df.columns
        assert "target_168" in df.columns
        assert "kill_switch_132" in df.columns

    def test_kill_switch_below_bullish(self, sample_eur_usd_data):
        """For bullish bias, kill switch should be below MLR low."""
        df = compute_mlr(sample_eur_usd_data)
        df = compute_fib_targets(df)
        bullish = df[df["bias"] == "BULLISH"]
        if len(bullish) > 0:
            valid = bullish.dropna(subset=["kill_switch_132", "mlr_low"])
            if len(valid) > 0:
                assert (valid["kill_switch_132"] < valid["mlr_low"]).all()


class TestDistanceFeatures:
    def test_distance_columns_added(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        df = compute_fib_targets(df)
        df = compute_distance_features(df, "EURUSD")
        assert "dist_to_25_pips" in df.columns
        assert "dist_to_132_pips" in df.columns

    def test_dist_132_always_positive(self, sample_eur_usd_data):
        df = compute_mlr(sample_eur_usd_data)
        df = compute_fib_targets(df)
        df = compute_distance_features(df, "EURUSD")
        valid = df["dist_to_132_pips"].dropna()
        assert (valid >= 0).all()

    def test_jpy_pip_scaling(self, sample_jpy_data):
        df = compute_mlr(sample_jpy_data)
        df = compute_fib_targets(df)
        df = compute_distance_features(df, "USDJPY")
        # JPY pairs should have larger pip values (abs)
        valid = df["dist_to_25_pips"].dropna()
        if len(valid) > 0:
            # EURUSD would be ~0.5-5 pips, USDJPY should be ~50-500 pips
            assert valid.abs().mean() > 10


class TestILMState:
    def test_ilm_state_column(self, sample_eur_usd_data):
        df = compute_ilm_state(sample_eur_usd_data)
        assert "ilm_state" in df.columns

    def test_ilm_state_values(self, sample_eur_usd_data):
        df = compute_ilm_state(sample_eur_usd_data)
        valid = df["ilm_state"].dropna()
        assert set(valid.unique()).issubset({0, 1, 2, 3})


class TestRegimeRatio:
    def test_regime_ratio_column(self, sample_eur_usd_data):
        df = compute_regime_ratio(sample_eur_usd_data)
        assert "regime_ratio" in df.columns
        assert "regime_status" in df.columns

    def test_regime_status_values(self, sample_eur_usd_data):
        df = compute_regime_ratio(sample_eur_usd_data)
        valid = df["regime_status"].dropna()
        assert set(valid.unique()).issubset({"CONFIRMED", "CAUTION", "FAILED", "UNKNOWN"})


class TestTimeBlocks:
    def test_time_block_columns(self, sample_eur_usd_data):
        df = compute_time_blocks(sample_eur_usd_data)
        assert "day_of_week" in df.columns
        assert "session" in df.columns
        assert "is_monday" in df.columns
        assert "is_wednesday" in df.columns
        assert "is_wednesday_pm" in df.columns
        assert "minutes_to_12pm_est" in df.columns

    def test_is_monday_binary(self, sample_eur_usd_data):
        df = compute_time_blocks(sample_eur_usd_data)
        assert set(df["is_monday"].unique()).issubset({0, 1})

    def test_is_wednesday_pm_only_on_wednesday(self, sample_eur_usd_data):
        df = compute_time_blocks(sample_eur_usd_data)
        wed_pm = df[df["is_wednesday_pm"] == 1]
        if len(wed_pm) > 0:
            assert (wed_pm.index.dayofweek == 2).all()

    def test_minutes_to_12pm_non_negative(self, sample_eur_usd_data):
        df = compute_time_blocks(sample_eur_usd_data)
        assert (df["minutes_to_12pm_est"] >= 0).all()


class TestNoFutureLeakage:
    """Critical test: verify no future leakage in any computation."""

    def test_mlr_uses_only_past_data(self, sample_eur_usd_data):
        """MLR for Tuesday should only use Monday 07:00-10:00 UTC data.
        
        Verifies no future leakage by checking that Tuesday's MLR high
        equals the max high of Monday 07:00-10:00 UTC bars from the
        SAME week_key grouping used in the actual computation.
        """
        df = compute_mlr(sample_eur_usd_data)
        # Find a Tuesday
        tuesdays = df.index[df.index.dayofweek == 1]
        if len(tuesdays) > 0:
            tue = tuesdays[0]
            mlr_val = df.loc[tue, "mlr_high"]
            
            # Reconstruct the same week_key logic as compute_mlr
            # to_period("W") drops tz, so we work with tz-naive
            tue_naive = tue.tz_localize(None) if tue.tz else tue
            tue_period = tue_naive.to_period("W")
            week_start = pd.Timestamp(tue_period.start_time)
            
            # Get all Monday 07:00-10:00 UTC bars in this week
            # Handle timezone-aware index
            idx = df.index
            if idx.tz:
                week_start_tz = week_start.tz_localize(idx.tz)
                week_end_tz = week_start_tz + pd.Timedelta(days=7)
                week_mask = (idx >= week_start_tz) & (idx < week_end_tz)
            else:
                week_end_tz = week_start + pd.Timedelta(days=7)
                week_mask = (idx >= week_start) & (idx < week_end_tz)
            
            week_bars = df.loc[week_mask]
            monday_mask = (week_bars.index.dayofweek == 0) & \
                          (week_bars.index.hour >= 7) & \
                          (week_bars.index.hour < 10)
            monday_bars = week_bars.loc[monday_mask]
            
            if len(monday_bars) > 0:
                expected_high = monday_bars["high"].max()
                # Exact match — same computation logic
                assert abs(mlr_val - expected_high) < 0.0001, \
                    f"MLR future leakage: Tuesday MLR high={mlr_val:.6f}, " \
                    f"Monday raw high={expected_high:.6f}, diff={abs(mlr_val - expected_high):.6f}"


class TestRealData:
    """Tests using the actual computed macro features."""

    def test_eur_usd_macro_features_exist(self):
        path = Path("quant-lab/ml/data/macro_features/EURUSD_macro.parquet")
        if not path.exists():
            pytest.skip("EURUSD macro features not computed yet")
        df = pd.read_parquet(path)
        assert len(df) > 0
        assert "mlr_high" in df.columns
        assert "target_25" in df.columns
        assert "kill_switch_132" in df.columns
        assert "dist_to_132_pips" in df.columns

    def test_all_assets_have_macro_features(self):
        macro_dir = Path("quant-lab/ml/data/macro_features")
        if not macro_dir.exists():
            pytest.skip("Macro features directory not found")
        files = list(macro_dir.glob("*_macro.parquet"))
        assert len(files) >= 15, f"Expected at least 15 assets, found {len(files)}"

    def test_label_files_exist(self):
        labels_dir = Path("quant-lab/ml/data/labels")
        if not labels_dir.exists():
            pytest.skip("Labels directory not found")
        files = list(labels_dir.glob("*_labeled.parquet"))
        assert len(files) >= 15, f"Expected at least 15 labeled assets, found {len(files)}"
