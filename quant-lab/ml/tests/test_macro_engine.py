"""
Macro Feature Engine Tests
===========================
Tests for MLR engine, kill-switch, ILM detector, pattern recognizer,
and macro feature builder.

Run with: pytest quant-lab/ml/tests/test_macro_engine.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add phase1_data to path
PHASE1_DIR = Path(__file__).parent.parent / "phase1_data"
sys.path.insert(0, str(PHASE1_DIR))

from macro.mlr_engine import compute_mlr_features, compute_fib_targets, FIB_LEVELS, KILL_SWITCH_132
from macro.kill_switch import (
    compute_132_proximity, compute_rekey_state,
    RekeyState, APPROACH_THRESHOLD_PIPS, CRITICAL_THRESHOLD_PIPS,
)
from macro.ilm_detector import (
    compute_ilm_state, compute_regime_ratio,
    ILMState, CONFIRMED_THRESHOLD, CAUTION_LOW_THRESHOLD,
)
from macro.pattern_recognizer import (
    detect_alpha_leg, detect_beta_leg, detect_abcd, detect_occ_extreme,
    ALPHA_RETRACE_RATIO, BETA_RETRACE_RATIO,
    AB_CD_EXTENSION_LOW, AB_CD_EXTENSION_HIGH,
)
from macro.macro_feature_builder import build_macro_feature_matrix, get_macro_feature_names


# ─── Fixtures ──────────────────────────────────────────────────────────────────


def _make_ohlcv_bars(n=500, freq='5min', start='2024-01-01', tz='UTC', seed=42):
    """Create a synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=n, freq=freq, tz=tz)
    base = 1.1000
    noise = rng.normal(0, 0.001, n).cumsum()
    close = base + noise
    high = close + np.abs(rng.normal(0, 0.0005, n))
    low = close - np.abs(rng.normal(0, 0.0005, n))
    open_ = close + rng.normal(0, 0.0003, n)
    volume = rng.integers(100, 1000, n)

    return pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)


def _make_trending_bars(n=200, direction='up', freq='5min', start='2024-01-01', tz='UTC'):
    """Create a trending OHLCV DataFrame for pattern detection tests."""
    dates = pd.date_range(start, periods=n, freq=freq, tz=tz)
    base = 1.1000

    if direction == 'up':
        trend = np.linspace(0, 0.0100, n)
    elif direction == 'down':
        trend = np.linspace(0, -0.0100, n)
    else:
        trend = np.zeros(n)

    close = base + trend + np.random.default_rng(42).normal(0, 0.0002, n)
    high = close + np.abs(np.random.default_rng(43).normal(0, 0.0003, n))
    low = close - np.abs(np.random.default_rng(44).normal(0, 0.0003, n))
    open_ = close + np.random.default_rng(45).normal(0, 0.0002, n)
    volume = np.random.default_rng(46).integers(100, 1000, n)

    return pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)


@pytest.fixture
def sample_df():
    """Standard synthetic OHLCV data."""
    return _make_ohlcv_bars()


@pytest.fixture
def trending_up_df():
    """Upward trending OHLCV data."""
    return _make_trending_bars(direction='up')


@pytest.fixture
def trending_down_df():
    """Downward trending OHLCV data."""
    return _make_trending_bars(direction='down')


@pytest.fixture
def df_with_mlr(sample_df):
    """DataFrame with MLR features already computed."""
    return compute_mlr_features(sample_df.copy())


@pytest.fixture
def df_with_fib(df_with_mlr):
    """DataFrame with Fib targets already computed."""
    return compute_fib_targets(df_with_mlr.copy())


@pytest.fixture
def df_with_proximity(df_with_fib):
    """DataFrame with 132% proximity features (needed for rekey state)."""
    return compute_132_proximity(df_with_fib.copy(), pip_size=0.0001)


# ─── MLR Engine Tests ─────────────────────────────────────────────────────────


class TestMLREngine:
    """Tests for Monday London Range computation."""

    def test_compute_mlr_returns_dataframe(self, sample_df):
        """Should return a DataFrame."""
        result = compute_mlr_features(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_mlr_columns_added(self, sample_df):
        """Should add MLR columns."""
        result = compute_mlr_features(sample_df)
        expected_cols = ['mlr_high', 'mlr_low', 'mlr_close', 'mlr_range',
                         'mlr_mid', 'bias', 'hours_since_mlr']
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_mlr_no_nan_for_monday_weeks(self, sample_df):
        """Bars in weeks with Monday data should have non-NaN MLR values."""
        result = compute_mlr_features(sample_df)
        # At least some bars should have MLR data
        has_mlr = result['mlr_high'].notna()
        assert has_mlr.sum() > 0, "No MLR data computed"

    def test_mlr_range_positive(self, sample_df):
        """MLR range should be positive where computed."""
        result = compute_mlr_features(sample_df)
        valid = result[result['mlr_range'].notna()]
        if len(valid) > 0:
            assert (valid['mlr_range'] > 0).all()

    def test_mlr_mid_between_high_low(self, sample_df):
        """MLR midpoint should be between high and low."""
        result = compute_mlr_features(sample_df)
        valid = result[result['mlr_high'].notna() & result['mlr_low'].notna()]
        if len(valid) > 0:
            assert (valid['mlr_mid'] >= valid['mlr_low']).all()
            assert (valid['mlr_mid'] <= valid['mlr_high']).all()

    def test_bias_values_valid(self, sample_df):
        """Bias should be BULLISH, BEARISH, or NEUTRAL."""
        result = compute_mlr_features(sample_df)
        valid = result[result['bias'] != 'UNKNOWN']
        if len(valid) > 0:
            assert set(valid['bias'].unique()).issubset({'BULLISH', 'BEARISH', 'NEUTRAL'})

    def test_fib_targets_return_dataframe(self, df_with_mlr):
        """Fib targets should return a DataFrame."""
        result = compute_fib_targets(df_with_mlr)
        assert isinstance(result, pd.DataFrame)

    def test_fib_targets_columns_added(self, df_with_mlr):
        """Should add Fib target columns."""
        result = compute_fib_targets(df_with_mlr)
        expected = ['target_minus_25', 'target_minus_50', 'target_minus_100',
                    'target_minus_168', 'kill_switch_132',
                    'dist_to_25_pct', 'dist_to_50_pct', 'dist_to_132_pct']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_fib_targets_bullish_above_mlr(self, df_with_mlr):
        """For bullish bias, Fib targets should be above MLR high."""
        result = compute_fib_targets(df_with_mlr)
        bullish = result[result['bias'] == 'BULLISH']
        valid = bullish[bullish['target_minus_25'].notna()]
        if len(valid) > 0:
            # Targets should be above MLR high for bullish
            assert (valid['target_minus_25'] > valid['mlr_high']).all()

    def test_kill_switch_below_mlr_for_bullish(self, df_with_mlr):
        """For bullish bias, kill-switch should be below MLR low."""
        result = compute_fib_targets(df_with_mlr)
        bullish = result[result['bias'] == 'BULLISH']
        valid = bullish[bullish['kill_switch_132'].notna()]
        if len(valid) > 0:
            assert (valid['kill_switch_132'] < valid['mlr_low']).all()

    def test_dist_to_132_non_negative(self, df_with_fib):
        """Distance to 132% should be non-negative."""
        result = df_with_fib
        valid = result[result['dist_to_132_pct'].notna()]
        if len(valid) > 0:
            assert (valid['dist_to_132_pct'] >= 0).all()


# ─── Kill-Switch Tests ────────────────────────────────────────────────────────


class TestKillSwitch:
    """Tests for 132% kill-switch proximity and rekey state."""

    def test_compute_132_proximity_returns_dataframe(self, df_with_fib):
        """Should return a DataFrame."""
        result = compute_132_proximity(df_with_fib, pip_size=0.0001)
        assert isinstance(result, pd.DataFrame)

    def test_proximity_columns_added(self, df_with_fib):
        """Should add proximity columns."""
        result = compute_132_proximity(df_with_fib, pip_size=0.0001)
        expected = ['dist_to_132_pips', 'pct_to_132', 'is_near_132', 'is_critical_132']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_dist_to_132_pips_non_negative(self, df_with_fib):
        """Distance in pips should be non-negative."""
        result = compute_132_proximity(df_with_fib, pip_size=0.0001)
        valid = result[result['dist_to_132_pips'].notna()]
        if len(valid) > 0:
            assert (valid['dist_to_132_pips'] >= 0).all()

    def test_is_near_132_binary(self, df_with_fib):
        """is_near_132 should be 0 or 1."""
        result = compute_132_proximity(df_with_fib, pip_size=0.0001)
        assert set(result['is_near_132'].dropna().unique()).issubset({0, 1})

    def test_compute_rekey_state_returns_dataframe(self, df_with_proximity):
        """Should return a DataFrame."""
        result = compute_rekey_state(df_with_proximity, pip_size=0.0001)
        assert isinstance(result, pd.DataFrame)

    def test_rekey_state_columns_added(self, df_with_proximity):
        """Should add rekey state columns."""
        result = compute_rekey_state(df_with_proximity, pip_size=0.0001)
        expected = ['rekey_state', 'rekey_state_label', 'bars_in_current_state',
                    'wednesday_pm_flag']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_rekey_state_values_valid(self, df_with_proximity):
        """Rekey state should be a valid RekeyState value."""
        result = compute_rekey_state(df_with_proximity, pip_size=0.0001)
        valid_states = {s.value for s in RekeyState}
        states = set(result['rekey_state'].dropna().unique())
        assert states.issubset(valid_states), f"Invalid states: {states - valid_states}"

    def test_wednesday_pm_flag_binary(self, df_with_proximity):
        """Wednesday PM flag should be 0 or 1."""
        result = compute_rekey_state(df_with_proximity, pip_size=0.0001)
        assert set(result['wednesday_pm_flag'].unique()).issubset({0, 1})

    def test_bars_in_state_non_negative(self, df_with_proximity):
        """bars_in_current_state should be non-negative."""
        result = compute_rekey_state(df_with_proximity, pip_size=0.0001)
        valid = result[result['bars_in_current_state'].notna()]
        if len(valid) > 0:
            assert (valid['bars_in_current_state'] >= 0).all()


# ─── ILM Detector Tests ───────────────────────────────────────────────────────


class TestILMDetector:
    """Tests for ILM state and regime ratio computation."""

    def test_compute_ilm_state_returns_dataframe(self, sample_df):
        """Should return a DataFrame."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        assert isinstance(result, pd.DataFrame)

    def test_ilm_columns_added(self, sample_df):
        """Should add ILM columns."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        expected = ['asian_high', 'asian_low', 'asian_range', 'asian_range_pips',
                    'london_high', 'london_low', 'london_range', 'london_range_pips',
                    'ilm_state', 'ilm_state_label', 'impulse_direction', 'is_wilm']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_ilm_state_values_valid(self, sample_df):
        """ILM state should be a valid ILMState value."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        valid_states = {s.value for s in ILMState}
        states = set(result['ilm_state'].dropna().unique())
        assert states.issubset(valid_states), f"Invalid states: {states - valid_states}"

    def test_ilm_state_label_valid(self, sample_df):
        """ILM state label should be a valid state name."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        valid_labels = {s.name for s in ILMState}
        labels = set(result['ilm_state_label'].dropna().unique())
        labels.discard('UNKNOWN')
        assert labels.issubset(valid_labels), f"Invalid labels: {labels - valid_labels}"

    def test_asian_range_pips_non_negative(self, sample_df):
        """Asian range in pips should be non-negative."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        valid = result[result['asian_range_pips'].notna()]
        if len(valid) > 0:
            assert (valid['asian_range_pips'] >= 0).all()

    def test_impulse_direction_valid(self, sample_df):
        """Impulse direction should be -1, 0, or 1."""
        result = compute_ilm_state(sample_df, pip_size=0.0001)
        dirs = set(result['impulse_direction'].dropna().unique())
        assert dirs.issubset({-1, 0, 1}), f"Invalid directions: {dirs}"

    def test_compute_regime_ratio_returns_dataframe(self, sample_df):
        """Should return a DataFrame."""
        result = compute_regime_ratio(sample_df, pip_size=0.0001)
        assert isinstance(result, pd.DataFrame)

    def test_regime_ratio_columns_added(self, sample_df):
        """Should add regime ratio columns."""
        result = compute_regime_ratio(sample_df, pip_size=0.0001)
        expected = ['regime_ratio', 'regime_label', 'regime_encoded',
                    'is_confirmed', 'is_caution', 'is_failed']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_regime_label_valid(self, sample_df):
        """Regime label should be CONFIRMED, CAUTION, FAILED, or UNKNOWN."""
        result = compute_regime_ratio(sample_df, pip_size=0.0001)
        valid_labels = {'CONFIRMED', 'CAUTION', 'FAILED', 'UNKNOWN'}
        labels = set(result['regime_label'].unique())
        assert labels.issubset(valid_labels), f"Invalid labels: {labels - valid_labels}"

    def test_regime_binary_flags(self, sample_df):
        """Binary regime flags should be 0 or 1."""
        result = compute_regime_ratio(sample_df, pip_size=0.0001)
        for col in ['is_confirmed', 'is_caution', 'is_failed']:
            assert set(result[col].dropna().unique()).issubset({0, 1})

    def test_regime_ratio_non_negative(self, sample_df):
        """Regime ratio should be non-negative where computed."""
        result = compute_regime_ratio(sample_df, pip_size=0.0001)
        valid = result[result['regime_ratio'].notna()]
        if len(valid) > 0:
            assert (valid['regime_ratio'] >= 0).all()


# ─── Pattern Recognizer Tests ─────────────────────────────────────────────────


class TestPatternRecognizer:
    """Tests for Alpha/Beta/AB-CD pattern detection."""

    def test_detect_alpha_returns_dataframe(self, sample_df):
        """Alpha detection should return a DataFrame."""
        result = detect_alpha_leg(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_alpha_columns_added(self, sample_df):
        """Should add alpha pattern columns."""
        result = detect_alpha_leg(sample_df)
        assert 'alpha_pattern' in result.columns
        assert 'alpha_direction' in result.columns

    def test_alpha_pattern_binary(self, sample_df):
        """Alpha pattern should be 0 or 1."""
        result = detect_alpha_leg(sample_df)
        assert set(result['alpha_pattern'].unique()).issubset({0, 1})

    def test_alpha_direction_valid(self, sample_df):
        """Alpha direction should be -1, 0, or 1."""
        result = detect_alpha_leg(sample_df)
        assert set(result['alpha_direction'].unique()).issubset({-1, 0, 1})

    def test_detect_beta_returns_dataframe(self, sample_df):
        """Beta detection should return a DataFrame."""
        result = detect_beta_leg(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_beta_columns_added(self, sample_df):
        """Should add beta pattern columns."""
        result = detect_beta_leg(sample_df)
        assert 'beta_pattern' in result.columns
        assert 'beta_direction' in result.columns

    def test_beta_pattern_binary(self, sample_df):
        """Beta pattern should be 0 or 1."""
        result = detect_beta_leg(sample_df)
        assert set(result['beta_pattern'].unique()).issubset({0, 1})

    def test_detect_abcd_returns_dataframe(self, sample_df):
        """AB-CD detection should return a DataFrame."""
        result = detect_abcd(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_abcd_columns_added(self, sample_df):
        """Should add AB-CD pattern columns."""
        result = detect_abcd(sample_df)
        assert 'abcd_pattern' in result.columns
        assert 'abcd_direction' in result.columns
        assert 'abcd_extension' in result.columns

    def test_abcd_pattern_binary(self, sample_df):
        """AB-CD pattern should be 0 or 1."""
        result = detect_abcd(sample_df)
        assert set(result['abcd_pattern'].unique()).issubset({0, 1})

    def test_detect_occ_extreme_returns_dataframe(self, sample_df):
        """OCC extreme detection should return a DataFrame."""
        result = detect_occ_extreme(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_occ_extreme_columns_added(self, sample_df):
        """Should add OCC extreme columns."""
        result = detect_occ_extreme(sample_df)
        expected = ['occ_extreme_high', 'occ_extreme_low', 'occ_direction', 'is_at_occ_extreme']
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_occ_direction_valid(self, sample_df):
        """OCC direction should be -1, 0, or 1."""
        result = detect_occ_extreme(sample_df)
        assert set(result['occ_direction'].unique()).issubset({-1, 0, 1})

    def test_occ_extreme_high_above_low(self, sample_df):
        """OCC extreme high should be >= extreme low."""
        result = detect_occ_extreme(sample_df)
        valid = result[result['occ_extreme_high'].notna() & result['occ_extreme_low'].notna()]
        if len(valid) > 0:
            assert (valid['occ_extreme_high'] >= valid['occ_extreme_low']).all()


# ─── Macro Feature Builder Tests ──────────────────────────────────────────────


class TestMacroFeatureBuilder:
    """Tests for the full macro feature matrix builder."""

    def test_build_macro_returns_dataframe(self, sample_df):
        """Should return a DataFrame."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert isinstance(result, pd.DataFrame)

    def test_build_macro_preserves_original_columns(self, sample_df):
        """Should preserve original OHLCV columns."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns

    def test_build_macro_adds_mlr_features(self, sample_df):
        """Should add MLR features."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert 'mlr_high' in result.columns
        assert 'bias' in result.columns

    def test_build_macro_adds_fib_features(self, sample_df):
        """Should add Fib target features."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert 'target_minus_25' in result.columns
        assert 'kill_switch_132' in result.columns
        assert 'dist_to_132_pct' in result.columns

    def test_build_macro_adds_kill_switch_features(self, sample_df):
        """Should add kill-switch proximity features."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert 'dist_to_132_pips' in result.columns
        assert 'rekey_state' in result.columns
        assert 'wednesday_pm_flag' in result.columns

    def test_build_macro_adds_ilm_features(self, sample_df):
        """Should add ILM state features."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert 'ilm_state' in result.columns
        assert 'asian_range_pips' in result.columns

    def test_build_macro_adds_regime_features(self, sample_df):
        """Should add regime ratio features."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=False)
        assert 'regime_ratio' in result.columns
        assert 'regime_label' in result.columns

    def test_build_macro_with_patterns(self, sample_df):
        """Should add pattern features when include_patterns=True."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=True,
                                            include_time_blocks=False)
        assert 'alpha_pattern' in result.columns
        assert 'beta_pattern' in result.columns
        assert 'abcd_pattern' in result.columns
        assert 'occ_direction' in result.columns
        assert 'any_pattern' in result.columns

    def test_build_macro_with_time_blocks(self, sample_df):
        """Should add time block features when include_time_blocks=True."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001,
                                            include_patterns=False,
                                            include_time_blocks=True)
        assert 'day_of_week' in result.columns
        assert 'hour_utc' in result.columns
        assert 'session' in result.columns
        assert 'is_monday' in result.columns

    def test_get_macro_feature_names_returns_list(self):
        """Should return a list of feature names."""
        names = get_macro_feature_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert 'mlr_high' in names
        assert 'regime_ratio' in names

    def test_build_macro_row_count_preserved(self, sample_df):
        """Should preserve the number of rows."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001)
        assert len(result) == len(sample_df)

    def test_build_macro_index_preserved(self, sample_df):
        """Should preserve the DatetimeIndex."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001)
        pd.testing.assert_index_equal(result.index, sample_df.index)


# ─── Integration Tests ────────────────────────────────────────────────────────


class TestMacroEngineIntegration:
    """Integration tests — full pipeline on real-ish data."""

    def test_full_pipeline_on_synthetic_data(self):
        """Full pipeline should run without errors on synthetic data."""
        df = _make_ohlcv_bars(n=1000)
        result = build_macro_feature_matrix(df, pip_size=0.0001,
                                            include_patterns=True,
                                            include_time_blocks=True)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1000

    def test_pipeline_on_trending_data(self, trending_up_df, trending_down_df):
        """Pipeline should handle trending data without errors."""
        for df in [trending_up_df, trending_down_df]:
            result = build_macro_feature_matrix(df, pip_size=0.0001,
                                                include_patterns=False,
                                                include_time_blocks=True)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(df)

    def test_no_future_leakage_in_mlr(self, sample_df):
        """MLR should not use future data — each bar only uses past/current week."""
        result = compute_mlr_features(sample_df)
        # MLR values should be constant within a week (forward-filled from Monday)
        valid = result[result['mlr_high'].notna()]
        if len(valid) > 0:
            # Group by week and check MLR is constant
            weekly = valid.groupby(pd.Grouper(freq='W-MON'))
            for _, group in weekly:
                if len(group) > 1:
                    # All MLR values in the same week should be identical
                    assert group['mlr_high'].nunique() <= 1, \
                        "MLR should be constant within a week (forward-filled)"

    def test_dist_to_132_in_top_features(self, sample_df):
        """dist_to_132_pct should be present in the feature matrix."""
        result = build_macro_feature_matrix(sample_df, pip_size=0.0001)
        assert 'dist_to_132_pct' in result.columns, \
            "dist_to_132_pct must be in feature matrix (Ironclad Rule #3)"
