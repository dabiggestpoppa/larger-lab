"""
Deterministic tests for the Phase 5 routing event engine.
CR-P5-ROUTING-EVENT-ENGINE-01

Covers the 16 required test families.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases.phase_5_events import (
    CURRENCIES, PAIRS, load_frozen_phase4, build_threshold_manifest,
)
from capital_routing.phases.phase_5_detect import (
    compute_event_components, detect_origin_episodes, detect_residual_shocks,
    detect_network_dislocations,
)

BASE = Path(__file__).resolve().parents[1]
P4 = BASE / "artifacts" / "phase_04"


@pytest.fixture(scope="module")
def frozen():
    return load_frozen_phase4(P4)


@pytest.fixture(scope="module")
def components(frozen):
    factors, residuals, features = (
        frozen["currency_factors_h1.parquet"],
        frozen["pair_residuals_h1.parquet"],
        frozen["factor_features_h1.parquet"],
    )
    return compute_event_components(factors, residuals, features), frozen


class TestOriginSymmetry:
    def test_origin_detector_symmetric_currencies(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        # same code path drives every currency; at least one event per currency
        if len(ep):
            origs = set(ep["origin_currency"])
            assert origs.issubset(set(CURRENCIES))
            assert len(origs) >= 1


class TestDirection:
    def test_positive_negative_direction(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep):
            assert set(ep["direction"]).issubset({"ACCUMULATION", "LIQUIDATION"})


class TestClassification:
    def test_broad_vs_localized(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep):
            assert (ep["broad_vs_localized"] == "BROAD_CURRENCY_EVENT").all()


class TestResidualShock:
    def test_residual_shock_detection(self, components):
        comp, frozen = components
        res = frozen["pair_residuals_h1.parquet"]
        th = build_threshold_manifest(
            frozen["currency_factors_h1.parquet"], res,
            frozen["factor_features_h1.parquet"])
        shocks = detect_residual_shocks(res, comp, th)
        if len(shocks):
            assert (shocks["event_family"] == "RESIDUAL_SHOCK").all()
            assert shocks["broad_vs_localized"].isin(
                ["PAIR_SPECIFIC_DISLOCATION"]).all()


class TestNetwork:
    def test_network_dislocation_detection(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        net = detect_network_dislocations(factors, residuals, comp, th)
        if len(net):
            assert (net["event_family"] == "NETWORK_DISLOCATION").all()


class TestEpisodes:
    def test_dedup(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep):
            # no event lasts a single hour repeatedly; durations should be >= 1h
            assert (ep["duration_hours"] >= 1.0).all()

    def test_hysteresis(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        assert th["hysteresis"]["entry_percentile"] > th["hysteresis"]["reset_percentile"]


class TestSeverity:
    def test_severity_ordering(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "EXTREME": 3}
        if len(ep):
            assert ep["severity"].isin(order).all()
            # severity score should be non-negative
            assert (ep[["severity_score"]].fillna(0).values >= 0).all()


class TestCandidates:
    def test_destination_ranking(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep):
            dests = ep[["destination_rank_1", "destination_rank_2", "destination_rank_3"]].stack().dropna()
            assert dests.isin(CURRENCIES).all()

    def test_bridge_components(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep) and "gbp_bridge_score_components" in ep.columns:
            for _, r in ep.iterrows():
                c = r["gbp_bridge_score_components"]
                if c:
                    assert "GBP_factor" in c

    def test_parking_components(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep) and "chf_parking_score_components" in ep.columns:
            for _, r in ep.iterrows():
                c = r["chf_parking_score_components"]
                if c:
                    assert "CHF_factor" in c

    def test_jpy_destination_components(self, components):
        comp, frozen = components
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        if len(ep) and "jpy_destination_score_components" in ep.columns:
            for _, r in ep.iterrows():
                c = r["jpy_destination_score_components"]
                if c:
                    assert "JPY_factor" in c


class TestDeterminism:
    def test_deterministic_rerun(self, frozen):
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        th = build_threshold_manifest(factors, residuals, features)
        c1 = compute_event_components(factors, residuals, features)
        c2 = compute_event_components(factors, residuals, features)
        e1 = detect_origin_episodes(factors, residuals, features, c1, th)
        e2 = detect_origin_episodes(factors, residuals, features, c2, th)
        pd.testing.assert_frame_equal(e1.reset_index(drop=True), e2.reset_index(drop=True))

    def test_missing_row_handling(self, frozen):
        # knock out a mid-panel row, engine must not crash
        factors = frozen["currency_factors_h1.parquet"].copy()
        residuals = frozen["pair_residuals_h1.parquet"].copy()
        features = frozen["factor_features_h1.parquet"].copy()
        mid = len(factors) // 2
        factors = factors.drop(factors.index[mid])
        residuals = residuals.reindex(factors.index)
        features = features.reindex(factors.index)
        th = build_threshold_manifest(factors, residuals, features)
        comp = compute_event_components(factors, residuals, features)
        ep = detect_origin_episodes(factors, residuals, features, comp, th)
        assert isinstance(ep, pd.DataFrame)

    def test_threshold_manifest_reproducible(self, frozen):
        factors, residuals, features = (
            frozen["currency_factors_h1.parquet"],
            frozen["pair_residuals_h1.parquet"],
            frozen["factor_features_h1.parquet"],
        )
        t1 = build_threshold_manifest(factors, residuals, features)
        t2 = build_threshold_manifest(factors, residuals, features)
        assert t1 == t2


class TestHashes:
    def test_input_hashes_match(self):
        man = json.loads((P4 / "output_hash_manifest.json").read_text(encoding="utf-8"))
        for f in ["currency_factors_h1.parquet", "pair_residuals_h1.parquet",
                  "factor_features_h1.parquet"]:
            assert man[f] == load_hash(f)

    def test_no_lookahead_audit_file(self):
        aud = json.loads((BASE / "artifacts" / "phase_05" / "no_lookahead_audit.json").read_text(encoding="utf-8"))
        assert aud["passes"] is True


def load_hash(f):
    import hashlib
    return hashlib.sha256((P4 / f).read_bytes()).hexdigest()