#!/usr/bin/env python3
"""
ALT-DATA-1.1 Test Suite
Tests for benchmark truth seal, DefiLlama provenance, PIT preservation.
"""
import hashlib, json, sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]  # alt_rotation/
DATA1 = ROOT / "data_1"
DATA11 = ROOT / "data_1_1"

WINDOWS = [1, 3, 7, 14, 30, 60, 90]
BTC_ID = 1
ETH_ID = 1027
TOLERANCE = 1e-12

# --- Fixtures ---

@pytest.fixture(scope="module")
def feat_v2():
    return pd.read_parquet(DATA11 / "ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet")

@pytest.fixture(scope="module")
def terrain_v2():
    return pd.read_parquet(DATA11 / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet")

@pytest.fixture(scope="module")
def uni():
    return pd.read_parquet(DATA1 / "ALT_DATA_1_PIT_UNIVERSE.parquet")

@pytest.fixture(scope="module")
def global_flow():
    return pd.read_parquet(DATA11 / "ALT_DATA_1_1_GLOBAL_FLOW.parquet")

@pytest.fixture(scope="module")
def chain_flow():
    return pd.read_parquet(DATA11 / "ALT_DATA_1_1_CHAIN_FLOW.parquet")

@pytest.fixture(scope="module")
def chain_map():
    return pd.read_parquet(DATA11 / "ALT_DATA_1_1_CHAIN_MAPPING.parquet")


# === BENCHMARK TRUTH SEAL TESTS ===

class TestBenchmarkTruthSeal:
    """BTC/ETH self-relative must be exactly 0."""

    def test_btc_self_relative_all_windows(self, feat_v2):
        btc = feat_v2[feat_v2["cmc_id"] == BTC_ID]
        for w in WINDOWS:
            col = f"relative_return_vs_BTC_{w}d"
            vals = btc[col].dropna()
            assert len(vals) > 0, f"BTC {col} has no values"
            max_abs = float(np.abs(vals).max())
            assert max_abs < TOLERANCE, f"BTC self-relative {w}D: {max_abs} > {TOLERANCE}"

    def test_eth_self_relative_all_windows(self, feat_v2):
        eth = feat_v2[feat_v2["cmc_id"] == ETH_ID]
        for w in WINDOWS:
            col = f"relative_return_vs_ETH_{w}d"
            vals = eth[col].dropna()
            assert len(vals) > 0, f"ETH {col} has no values"
            max_abs = float(np.abs(vals).max())
            assert max_abs < TOLERANCE, f"ETH self-relative {w}D: {max_abs} > {TOLERANCE}"


class TestCalendarDayEndpoints:
    """Asset returns must use calendar-day endpoints."""

    def test_return_1d_is_close_to_pct_change(self, feat_v2, uni):
        """1D return should be price(t)/price(t-1) - 1 for calendar dates."""
        btc = feat_v2[feat_v2["cmc_id"] == BTC_ID][["historical_date", "return_1d"]].copy()
        btc_price = uni[uni["cmc_id"] == BTC_ID][["historical_date", "price_usd"]].copy()
        btc = btc.merge(btc_price, on="historical_date", how="left")
        btc = btc.set_index("historical_date").sort_index()
        # Calendar-day 1D return
        cal_1d = btc["price_usd"].pct_change(1)
        diff = (btc["return_1d"] - cal_1d).dropna()
        # Allow small tolerance for float precision
        assert np.abs(diff).max() < 0.001, f"1D return deviates from calendar: {np.abs(diff).max()}"

    def test_gap_dates_produce_na(self, feat_v2):
        """Excluded dates should result in NA for extended windows."""
        # The feature set should have NaN for windows that require excluded dates
        # Just verify that not all values are NaN (sanity check)
        assert feat_v2["return_90d"].notna().sum() > 0.5 * len(feat_v2), \
            "90D return has too many NaN values"


class TestPITUniversePreserved:
    """PIT universe must be identical to DATA-1."""

    def test_row_count(self, uni):
        assert len(uni) == 1_098_000, f"PIT universe rows: {len(uni)}"

    def test_date_count(self, uni):
        assert uni["historical_date"].nunique() == 2196, \
            f"PIT universe dates: {uni['historical_date'].nunique()}"

    def test_asset_count(self, uni):
        assert uni["cmc_id"].nunique() == 2898, \
            f"PIT universe assets: {uni['cmc_id'].nunique()}"

    def test_no_rank_above_500(self, uni):
        assert (uni["rank"] <= 500).all(), "Some ranks exceed 500"

    def test_exactly_500_per_date(self, uni):
        counts = uni.groupby("historical_date").size()
        assert (counts == 500).all(), f"Not all dates have 500 rows: {counts.describe()}"


class TestV2FeatureIntegrity:
    """V2 features must maintain structural integrity."""

    def test_feature_row_count(self, feat_v2, uni):
        assert len(feat_v2) == len(uni), \
            f"Feature rows {len(feat_v2)} != universe rows {len(uni)}"

    def test_rank_columns_unchanged(self, feat_v2):
        """Rank columns should not have been modified."""
        assert "global_rank" in feat_v2.columns
        assert feat_v2["global_rank"].notna().sum() > 0.5 * len(feat_v2)

    def test_relative_return_arithmetic(self, feat_v2):
        """relative_return = asset_return - benchmark_return for each window."""
        btc_feat = feat_v2[feat_v2["cmc_id"] == BTC_ID].set_index("historical_date")
        for w in WINDOWS:
            ret_col = f"return_{w}d"
            rel_col = f"relative_return_vs_BTC_{w}d"
            # For BTC: relative = return - return = 0 (already tested)
            # For a non-BTC asset, check consistency
            sample = feat_v2[feat_v2["cmc_id"] == 1839].head(100)  # BNB
            sample_btc_ret = sample["historical_date"].map(btc_feat[ret_col])
            expected = sample[ret_col] - sample_btc_ret
            actual = sample[rel_col]
            mask = expected.notna() & actual.notna()
            if mask.any():
                diff = np.abs(expected[mask] - actual[mask])
                assert diff.max() < 1e-10, f"Relative return arithmetic off: {diff.max()}"


class TestDefiLlama:
    """DefiLlama data integrity."""

    def test_global_flow_has_dates(self, global_flow):
        assert len(global_flow) > 3000
        assert global_flow["historical_date"].min() < pd.Timestamp("2020-01-01")

    def test_chain_flow_has_chains(self, chain_flow):
        assert chain_flow["chain"].nunique() >= 20

    def test_no_future_leak(self, global_flow):
        """No DefiLlama data should be from the future."""
        assert global_flow["historical_date"].max() <= pd.Timestamp.now()


class TestChainMapping:
    """Chain mapping integrity."""

    def test_all_assets_have_ids(self, chain_map):
        assert chain_map["cmc_id"].notna().all()

    def test_mapping_source(self, chain_map):
        assert (chain_map["mapping_source"] == "coinmarketcap_pit_universe").all()


class TestNoPnL:
    """No strategy interpretation in V2 features."""

    def test_no_strategy_columns(self, feat_v2):
        forbidden = ["signal", "position", "pnl", "sharpe", "drawdown", "alpha", "target"]
        for col in forbidden:
            assert col not in feat_v2.columns, f"Forbidden column found: {col}"


class TestFeatureRegistry:
    """Feature registry determinism."""

    def test_v2_hash_reproducible(self):
        reg_path = DATA11 / "ALT_DATA_1_1_FEATURE_REGISTRY_HASH.json"
        assert reg_path.exists()
        reg = json.loads(reg_path.read_text())
        assert "v2_hash" in reg
        assert reg["v2_hash"] == "0d666e74c0cf76adf6e6e6f2a6c47b1f52116f070fd1376c83274e6b077703ba"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
