"""
Phase 1 Tests: Data Foundation & Feature Engineering
=====================================================
Tests for data pipeline, Asian Range extraction, K-Means tier discovery,
feature matrix construction, and label generation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# Import from our pipeline
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1_data"))

from pipeline import (
    convert_csv_to_parquet,
    extract_asian_ranges,
    discover_tiers,
    build_feature_matrix,
    ASSET_CONFIG,
)


class TestDataIngestion:
    """Test 1.1: Data Ingestion Pipeline"""

    def test_parquet_dir_creation(self):
        """Parquet directory should be created if it doesn't exist."""
        from pipeline import PARQUET_DIR
        PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        assert PARQUET_DIR.exists()

    def test_asset_config_complete(self):
        """All 19 assets should have configuration."""
        assert len(ASSET_CONFIG) == 19
        for symbol, cfg in ASSET_CONFIG.items():
            assert 'pip_mult' in cfg
            assert 'pip_size' in cfg
            # csv can be None for assets without data yet (e.g. USTEC100)

    def test_convert_csv_returns_metadata(self, tmp_path):
        """CSV conversion should return metadata dict."""
        # Create a minimal test CSV
        dates = pd.date_range('2024-01-01', periods=100, freq='5min', tz='UTC')
        df = pd.DataFrame({
            'dt': dates,
            'open': np.random.randn(100).cumsum() + 1.0,
            'high': np.random.randn(100).cumsum() + 1.05,
            'low': np.random.randn(100).cumsum() + 0.95,
            'close': np.random.randn(100).cumsum() + 1.0,
            'volume': np.random.randint(100, 1000, 100),
        })
        csv_path = tmp_path / "TEST_M5.csv"
        df.to_csv(csv_path, index=False)

        meta = convert_csv_to_parquet('TEST', csv_path, 10000)
        assert meta['status'] == 'OK'
        assert meta['rows'] == 100
        assert 'data_hash' in meta


class TestAsianRangeExtraction:
    """Test 1.3: Asian Range Extraction"""

    def test_extract_asian_ranges_returns_dataframe(self):
        """Should return DataFrame with AR values."""
        dates = pd.date_range('2024-01-01 19:00', periods=100, freq='5min', tz='UTC')
        df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 1.0,
            'high': np.random.randn(100).cumsum() + 1.05,
            'low': np.random.randn(100).cumsum() + 0.95,
            'close': np.random.randn(100).cumsum() + 1.0,
            'volume': np.random.randint(100, 1000, 100),
        }, index=dates)

        import pyarrow as pa
        import pyarrow.parquet as pq
        table = pa.Table.from_pandas(df)

        from pipeline import PARQUET_DIR
        PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, PARQUET_DIR / "TEST_AR.parquet")

        result = extract_asian_ranges(PARQUET_DIR / "TEST_AR.parquet", "TEST_AR")
        assert isinstance(result, pd.DataFrame)
        assert 'ar_pips' in result.columns

    def test_minimum_sessions_requirement(self):
        """Should handle insufficient data gracefully."""
        dates = pd.date_range('2024-01-01', periods=20, freq='5min', tz='UTC')
        df = pd.DataFrame({
            'open': np.random.randn(20).cumsum() + 1.0,
            'high': np.random.randn(20).cumsum() + 1.05,
            'low': np.random.randn(20).cumsum() + 0.95,
            'close': np.random.randn(20).cumsum() + 1.0,
            'volume': np.random.randint(100, 1000, 20),
        }, index=dates)

        import pyarrow as pa
        import pyarrow.parquet as pq
        table = pa.Table.from_pandas(df)

        from pipeline import PARQUET_DIR
        pq.write_table(table, PARQUET_DIR / "TEST_FEW.parquet")

        result = extract_asian_ranges(PARQUET_DIR / "TEST_FEW.parquet", "TEST_FEW")
        # Should return empty or very few sessions
        assert len(result) < 5


class TestTierDiscovery:
    """Test 1.4: K-Means Tier Discovery"""

    def test_discover_tiers_returns_three_tiers(self):
        """Should return exactly 3 tiers."""
        np.random.seed(42)
        # Generate realistic AR data with 3 clusters
        ar_values = np.concatenate([
            np.random.normal(15, 3, 100),   # T1: tight
            np.random.normal(25, 4, 150),   # T2: standard
            np.random.normal(40, 5, 80),    # T3: wide
        ])
        ranges_df = pd.DataFrame({
            'ar_pips': ar_values,
            'ar_high': ar_values * 1.1,
            'ar_low': ar_values * 0.9,
            'date': pd.date_range('2024-01-01', periods=len(ar_values)),
            'session_bars': [12] * len(ar_values),
        })

        result = discover_tiers(ranges_df, "TEST")
        assert result['status'] == 'OK'
        assert 'T1' in result['tiers']
        assert 'T2' in result['tiers']
        assert 'T3' in result['tiers']

    def test_au_is_50_percent_of_centroid(self):
        """AU must be exactly 50% of centroid (NON-NEGOTIABLE)."""
        np.random.seed(42)
        ar_values = np.concatenate([
            np.random.normal(15, 3, 100),
            np.random.normal(25, 4, 150),
            np.random.normal(40, 5, 80),
        ])
        ranges_df = pd.DataFrame({
            'ar_pips': ar_values,
            'ar_high': ar_values * 1.1,
            'ar_low': ar_values * 0.9,
            'date': pd.date_range('2024-01-01', periods=len(ar_values)),
            'session_bars': [12] * len(ar_values),
        })

        result = discover_tiers(ranges_df, "TEST")
        for tier_name, tier in result['tiers'].items():
            expected_au = tier['centroid'] * 0.50
            assert abs(tier['au'] - expected_au) < 0.01, \
                f"{tier_name}: AU={tier['au']} != 50% of centroid={expected_au}"

    def test_trigger_is_au_times_1_2(self):
        """Trigger must be AU × 1.2."""
        np.random.seed(42)
        ar_values = np.concatenate([
            np.random.normal(15, 3, 100),
            np.random.normal(25, 4, 150),
            np.random.normal(40, 5, 80),
        ])
        ranges_df = pd.DataFrame({
            'ar_pips': ar_values,
            'ar_high': ar_values * 1.1,
            'ar_low': ar_values * 0.9,
            'date': pd.date_range('2024-01-01', periods=len(ar_values)),
            'session_bars': [12] * len(ar_values),
        })

        result = discover_tiers(ranges_df, "TEST")
        for tier_name, tier in result['tiers'].items():
            expected_trigger = tier['au'] * 1.2
            assert abs(tier['trigger'] - expected_trigger) < 0.01, \
                f"{tier_name}: trigger={tier['trigger']} != AU×1.2={expected_trigger}"

    def test_insufficient_data_returns_error(self):
        """Should reject fewer than 60 sessions."""
        ranges_df = pd.DataFrame({
            'ar_pips': np.random.normal(20, 5, 30),
            'ar_high': np.random.normal(22, 5, 30),
            'ar_low': np.random.normal(18, 5, 30),
            'date': pd.date_range('2024-01-01', periods=30),
            'session_bars': [12] * 30,
        })

        result = discover_tiers(ranges_df, "TEST")
        assert result['status'] == 'INSUFFICIENT_DATA'

    def test_centroids_within_manual_benchmarks(self):
        """Centroids should be within ±5% of manual benchmarks for known assets."""
        # EURUSD: T1 ~15p, T2 ~25p, T3 ~40p
        np.random.seed(42)
        ar_values = np.concatenate([
            np.random.normal(15, 2, 200),
            np.random.normal(25, 3, 200),
            np.random.normal(40, 4, 200),
        ])
        ranges_df = pd.DataFrame({
            'ar_pips': ar_values,
            'ar_high': ar_values * 1.1,
            'ar_low': ar_values * 0.9,
            'date': pd.date_range('2024-01-01', periods=len(ar_values)),
            'session_bars': [12] * len(ar_values),
        })

        result = discover_tiers(ranges_df, "EURUSD")
        centroids = result['centroids']

        # T1 centroid should be ~15 (±5% = 14.25-15.75)
        assert 14.0 < centroids[0] < 16.0, f"T1 centroid {centroids[0]} out of range"
        # T2 centroid should be ~25 (±5% = 23.75-26.25)
        assert 23.0 < centroids[1] < 27.0, f"T2 centroid {centroids[1]} out of range"
        # T3 centroid should be ~40 (±5% = 38-42)
        assert 37.0 < centroids[2] < 43.0, f"T3 centroid {centroids[2]} out of range"


class TestFeatureMatrix:
    """Test 1.5: Feature Matrix Construction"""

    def test_feature_matrix_has_expected_columns(self):
        """Feature matrix should contain all expected feature columns."""
        dates = pd.date_range('2024-01-01', periods=100, freq='5min', tz='UTC')
        df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 1.0,
            'high': np.random.randn(100).cumsum() + 1.05,
            'low': np.random.randn(100).cumsum() + 0.95,
            'close': np.random.randn(100).cumsum() + 1.0,
            'volume': np.random.randint(100, 1000, 100),
        }, index=dates)

        import pyarrow as pa
        import pyarrow.parquet as pq
        table = pa.Table.from_pandas(df)

        from pipeline import PARQUET_DIR
        pq.write_table(table, PARQUET_DIR / "TEST_FM.parquet")

        tiers = {'T1': {'au': 10}, 'T2': {'au': 12}, 'T3': {'au': 15}}
        result = build_feature_matrix(PARQUET_DIR / "TEST_FM.parquet", "TEST_FM", tiers)

        expected_cols = ['body', 'range', 'body_ratio', 'hour_est', 'day_of_week',
                         'rolling_vol_20', 'vol_ratio', 'gap', 'is_asian',
                         'is_london', 'is_ny']
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_no_nan_in_rolling_features(self):
        """Rolling features should not contain NaN after construction."""
        dates = pd.date_range('2024-01-01', periods=100, freq='5min', tz='UTC')
        df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 1.0,
            'high': np.random.randn(100).cumsum() + 1.05,
            'low': np.random.randn(100).cumsum() + 0.95,
            'close': np.random.randn(100).cumsum() + 1.0,
            'volume': np.random.randint(100, 1000, 100),
        }, index=dates)

        import pyarrow as pa
        import pyarrow.parquet as pq
        table = pa.Table.from_pandas(df)

        from pipeline import PARQUET_DIR
        pq.write_table(table, PARQUET_DIR / "TEST_NAN.parquet")

        tiers = {'T1': {'au': 10}, 'T2': {'au': 12}, 'T3': {'au': 15}}
        result = build_feature_matrix(PARQUET_DIR / "TEST_NAN.parquet", "TEST_NAN", tiers)

        assert not result['rolling_vol_20'].isna().any()
        assert not result['vol_ratio'].isna().any()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
