"""
CRYPTO-MECH-1 test suite.

Covers: causal timestamp alignment, no future matching, basis orientation,
event segmentation, resolution classification, censoring, funding alignment,
OI alignment limits, BTC/ETH lead-lag, AMM price orientation, time-epoch
classification, bootstrap reproducibility, null permutation reproducibility,
future perturbation invariance.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MECH1 = os.path.dirname(HERE)
sys.path.insert(0, MECH1)
sys.path.insert(0, os.path.join(MECH1, "analysis"))

from mech_analysis import (  # noqa: E402
    align_causal, amm_pilot_anatomy, build_basis_series, cross_asset_state,
    desc_stats, funding_anatomy, future_perturbation_invariance,
    null_ar1_mean_reversion, null_block_shuffle_resolution,
    null_unconditional_future_basis, null_vol_matched_random,
    oi_snapshot_anatomy, resolution_survival, segment_dislocations,
    time_epoch_anatomy, bucket_hour, parse_ts, SEED,
)
from mech_decision import determine_mech1_decision, MechDecisionInput  # noqa: E402


def make_candle(ts, close, high=None, low=None, open_=None, volume=1.0):
    return {"venue": "test", "market_id": "TEST", "instrument_id": "TEST",
            "event_time_utc": ts, "close": close,
            "high": high or close, "low": low or close,
            "open": open_ or close, "volume": volume}


class TestTimestampHelpers(unittest.TestCase):
    def test_parse_iso(self):
        dt = parse_ts("2026-01-25T14:00:00+00:00")
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.tzinfo.utcoffset(dt).total_seconds(), 0)

    def test_parse_naive_becomes_utc(self):
        dt = parse_ts("2026-01-25T14:00:00")
        self.assertIsNotNone(dt)

    def test_bucket_hour(self):
        self.assertEqual(bucket_hour("2026-01-25T14:37:00+00:00"),
                         "2026-01-25T14:00:00+00:00")


class TestCausalAlignment(unittest.TestCase):
    def test_no_future_matching(self):
        # A at 10:00; B only at 11:00 (future) -> unmatched, not matched to future
        a = [make_candle("2026-01-25T10:00:00+00:00", 100.0)]
        b = [make_candle("2026-01-25T11:00:00+00:00", 105.0)]
        res = align_causal(a, b)
        self.assertEqual(len(res.matched), 0)
        self.assertEqual(res.unmatched_a, 1)

    def test_same_bucket_match(self):
        a = [make_candle("2026-01-25T10:00:00+00:00", 100.0)]
        b = [make_candle("2026-01-25T10:00:00+00:00", 99.0)]
        res = align_causal(a, b)
        self.assertEqual(len(res.matched), 1)
        # basis = 10000*ln(100/99) > 0
        self.assertGreater(res.matched[0]["basis_bps"], 0)

    def test_nearest_prior_within_staleness(self):
        a = [make_candle("2026-01-25T10:00:00+00:00", 100.0)]
        b = [make_candle("2026-01-25T09:00:00+00:00", 99.0)]
        res = align_causal(a, b, max_staleness_hours=2.0)
        self.assertEqual(len(res.matched), 1)
        self.assertEqual(res.matched[0]["staleness_hours"], 1.0)

    def test_staleness_exceeds_max(self):
        a = [make_candle("2026-01-25T10:00:00+00:00", 100.0)]
        b = [make_candle("2026-01-25T08:00:00+00:00", 99.0)]
        res = align_causal(a, b, max_staleness_hours=1.0)
        self.assertEqual(len(res.matched), 0)


class TestBasisOrientation(unittest.TestCase):
    def test_basis_sign(self):
        # perp above spot -> positive basis
        series = build_basis_series(
            [make_candle("2026-01-25T10:00:00+00:00", 100.0)],
            [make_candle("2026-01-25T10:00:00+00:00", 99.0)])
        self.assertGreater(series[0]["basis_bps"], 0)
        # perp below spot -> negative basis
        series = build_basis_series(
            [make_candle("2026-01-25T10:00:00+00:00", 99.0)],
            [make_candle("2026-01-25T10:00:00+00:00", 100.0)])
        self.assertLess(series[0]["basis_bps"], 0)

    def test_basis_magnitude(self):
        series = build_basis_series(
            [make_candle("2026-01-25T10:00:00+00:00", 100.0)],
            [make_candle("2026-01-25T10:00:00+00:00", 99.0)])
        self.assertAlmostEqual(series[0]["basis_bps"], 100.5033585, places=3)


class TestDislocationSegmentation(unittest.TestCase):
    def _series(self):
        rows = []
        for i in range(200):
            ts = f"2026-01-{25 + i // 24:02d}T{(i % 24):02d}:00:00+00:00"
            if 100 <= i <= 110:
                basis = 100.0  # elevated (above p90 = 1.0)
            elif 111 <= i <= 130:
                basis = 0.1    # below p_normal (0.5) -> resolves
            else:
                basis = 0.5    # baseline (p75=0.5 < p90=1.0)
            rows.append({"event_time_utc": ts, "bucket": ts,
                         "basis_bps": basis, "perp_close": 100.0,
                         "spot_close": 100.0})
        return rows

    def test_segmentation_finds_episode(self):
        series = self._series()
        eps, bands = segment_dislocations(series, 90.0, 75.0)
        self.assertGreaterEqual(len(eps), 1)
        self.assertLessEqual(bands["p_normal"], bands["p_elevated"])
        self.assertGreater(eps[0]["peak_basis_bps"], bands["p_elevated"])

    def test_resolved_classification(self):
        series = self._series()
        eps, _ = segment_dislocations(series, 90.0, 75.0)
        self.assertTrue(any(e.get("resolved") for e in eps))

    def test_censored_episode(self):
        # elevated run to end of series (never returns inside normal) -> censored
        rows = []
        for i in range(100):
            ts = f"2026-01-{25 + i // 24:02d}T{(i % 24):02d}:00:00+00:00"
            if i < 90:
                basis = 0.5
            else:
                basis = 100.0 + i  # distinct elevated values > p90
            rows.append({"event_time_utc": ts, "bucket": ts,
                         "basis_bps": basis, "perp_close": 100.0,
                         "spot_close": 100.0})
        eps, _ = segment_dislocations(rows, 90.0, 75.0)
        self.assertTrue(any(not e.get("resolved") for e in eps))
        self.assertTrue(any(e.get("classification") == "CENSORED" for e in eps))

    def test_deterministic(self):
        series = self._series()
        eps1, _ = segment_dislocations(series, 90.0, 75.0)
        eps2, _ = segment_dislocations(series, 90.0, 75.0)
        self.assertEqual(len(eps1), len(eps2))
        self.assertEqual([e["start_time"] for e in eps1],
                         [e["start_time"] for e in eps2])


class TestSurvival(unittest.TestCase):
    def test_survival_monotone(self):
        episodes = [
            {"resolved": True, "duration_hours": 2.0},
            {"resolved": True, "duration_hours": 5.0},
            {"resolved": False},
        ]
        curve = resolution_survival(episodes, max_hours=10.0)
        pts = [c for c in curve if "t_hours" in c]
        self.assertGreater(len(pts), 0)
        surv = [c["p_not_resolved"] for c in pts]
        for a, b in zip(surv, surv[1:]):
            self.assertGreaterEqual(a + 1e-9, b)


class TestFundingAnatomy(unittest.TestCase):
    def test_funding_stats(self):
        recs = [{"funding_rate": 0.0001 + i * 1e-7, "premium": 0.0002 + i * 2e-7,
                 "event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00"}
                for i in range(24)]
        fa = funding_anatomy(recs, "T")
        self.assertEqual(fa["n"], 24)
        self.assertAlmostEqual(fa["funding_rate_bps"]["p50"], 1.0115, places=1)
        self.assertAlmostEqual(fa["corr_funding_premium"], 1.0, places=3)

    def test_oi_snapshot_limitation(self):
        recs = [{"mark_price": 100.0, "index_price": 100.1,
                 "open_interest": 5.0}]
        oa = oi_snapshot_anatomy(recs, "T")
        self.assertTrue(oa["snapshot_only"])
        self.assertIn("NOT available", oa["limitation"])
        self.assertLess(oa["mark_index_basis_bps"], 0)


class TestCrossAsset(unittest.TestCase):
    def test_cross_corr(self):
        btc = [{"bucket": f"2026-01-25T{i:02d}:00:00+00:00",
                "event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00",
                "basis_bps": 10.0 + i} for i in range(50)]
        eth = [{"bucket": f"2026-01-25T{i:02d}:00:00+00:00",
                "event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00",
                "basis_bps": 10.0 + i * 2} for i in range(50)]
        out = cross_asset_state(btc, eth, "basis_bps", "t")
        self.assertEqual(out["n_common"], 50)
        self.assertAlmostEqual(out["corr"], 1.0, places=6)

    def test_lead_lag_keys(self):
        btc = [{"bucket": f"2026-01-25T{i:02d}:00:00+00:00",
                "event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00",
                "basis_bps": float(i)} for i in range(50)]
        eth = [{"bucket": f"2026-01-25T{i:02d}:00:00+00:00",
                "event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00",
                "basis_bps": float(i)} for i in range(50)]
        out = cross_asset_state(btc, eth, "basis_bps", "t")
        self.assertIn("0", out.get("cross_corr_by_lag", {}))


class TestAMMPilot(unittest.TestCase):
    def test_orientation_token0_asset(self):
        # token0 = asset (WBTC), price_token0_per_token1 = WBTC/USD directly
        swaps = [{"event_time_utc": "2026-08-14T17:06:00+00:00",
                  "amount0": -2438494262, "amount1": 1295331943044047602,
                  "price_token0_per_token1": 63017.0,
                  "price_token1_per_token0": 1.587e-05,
                  "sqrt_price_x96": 1, "tick": 1, "liquidity": 1}]
        perp = [make_candle("2026-08-14T17:05:00+00:00", 63000.0)]
        out = amm_pilot_anatomy(swaps, perp, "T", pool_token0_is_asset=True)
        self.assertEqual(out["n_swaps"], 1)
        self.assertEqual(out["evidence_class"], "PILOT_MECHANISM_EVIDENCE")
        self.assertGreater(out["basis_stats"]["median"], 0)  # AMM above perp

    def test_orientation_token1_asset(self):
        # token1 = asset (WETH), price_token1_per_token0 = ETH/USD -> invert
        swaps = [{"event_time_utc": "2026-08-14T17:06:00+00:00",
                  "amount0": -2438494262, "amount1": 1295331943044047602,
                  "price_token0_per_token1": 0.00053094,
                  "price_token1_per_token0": 1883.45,
                  "sqrt_price_x96": 1, "tick": 1, "liquidity": 1}]
        perp = [make_candle("2026-08-14T17:05:00+00:00", 1880.0)]
        out = amm_pilot_anatomy(swaps, perp, "T", pool_token0_is_asset=False)
        self.assertEqual(out["n_swaps"], 1)
        self.assertGreater(out["basis_stats"]["median"], 0)


class TestNullModels(unittest.TestCase):
    def _basis_series(self):
        rows = []
        for i in range(200):
            ts = f"2026-01-{25 + i // 24:02d}T{(i % 24):02d}:00:00+00:00"
            rows.append({"event_time_utc": ts, "bucket": ts, "basis_bps": float(i % 30)})
        return rows

    def test_unconditional(self):
        rows = self._basis_series()
        out = null_unconditional_future_basis(rows, (1, 4))
        self.assertEqual(len(out), 2)

    def test_vol_matched_reproducible(self):
        rows = self._basis_series()
        a = null_vol_matched_random(rows, n_perm=50, seed=SEED)
        b = null_vol_matched_random(rows, n_perm=50, seed=SEED)
        self.assertEqual(a["null_mean_decay_pct"], b["null_mean_decay_pct"])

    def test_block_shuffle_reproducible(self):
        eps = [{"resolved": i % 2 == 0} for i in range(20)]
        a = null_block_shuffle_resolution(eps, n_perm=50, seed=SEED)
        b = null_block_shuffle_resolution(eps, n_perm=50, seed=SEED)
        self.assertEqual(a["null_mean"], b["null_mean"])

    def test_ar1(self):
        rows = self._basis_series()
        out = null_ar1_mean_reversion(rows, 4)
        self.assertIn("phi", out)


class TestFuturePerturbation(unittest.TestCase):
    def test_truncation_invariance(self):
        recs = [make_candle(f"2026-01-25T{i:02d}:00:00+00:00", 100.0 + i)
                for i in range(20)]
        out = future_perturbation_invariance(
            lambda r: [{"event_time_utc": x["event_time_utc"], "close": x["close"]}
                       for x in r],
            recs, "2026-01-25T10:00:00+00:00")
        self.assertTrue(out["equal"])
        self.assertGreater(out["truncated_rows"], 0)


class TestDecisionEngine(unittest.TestCase):
    def test_pass_when_all_met(self):
        inp = MechDecisionInput(
            freeze_verified=True,
            causal_violations=[],
            segmentation_reproducible=True,
            basis_anatomy_rows=10,
            funding_anatomy_rows=10,
            oi_anatomy_present=True,
            cross_asset_present=True,
            null_models_completed=[
                "unconditional_future_basis_change",
                "random_timestamps_matched_by_volatility_regime",
                "shuffled_event_labels_preserving_time_blocks",
                "ar1_mean_reversion_expectation"],
            amm_findings_labelled=True,
            amm_evidence_class="PILOT_MECHANISM_EVIDENCE",
            negative_mechanisms_retained=True,
            strategy_pnl_computed=False,
            optimization_performed=False,
            mechanism_registry_present=True,
            unsupported_alpha_claim=False,
        )
        out = determine_mech1_decision(inp)
        self.assertEqual(out.decision, "PASS_MECHANISM_ANATOMY")

    def test_fail_closed_freeze(self):
        inp = MechDecisionInput(freeze_verified=False, freeze_reason="hash mismatch")
        out = determine_mech1_decision(inp)
        self.assertNotEqual(out.decision, "PASS_MECHANISM_ANATOMY")
        self.assertTrue(any("freeze" in b for b in out.blocking_issues))

    def test_fail_closed_null_missing(self):
        inp = MechDecisionInput(
            freeze_verified=True,
            basis_anatomy_rows=10,
            funding_anatomy_rows=10,
            oi_anatomy_present=True,
            cross_asset_present=True,
            null_models_completed=["ar1_mean_reversion_expectation"],
            amm_findings_labelled=True,
            segmentation_reproducible=True,
            negative_mechanisms_retained=True,
            mechanism_registry_present=True,
        )
        out = determine_mech1_decision(inp)
        self.assertTrue(any("null" in b for b in out.blocking_issues))

    def test_fail_closed_pnl(self):
        inp = MechDecisionInput(
            freeze_verified=True, basis_anatomy_rows=10,
            funding_anatomy_rows=10, oi_anatomy_present=True,
            cross_asset_present=True,
            null_models_completed=[
                "unconditional_future_basis_change",
                "random_timestamps_matched_by_volatility_regime",
                "shuffled_event_labels_preserving_time_blocks",
                "ar1_mean_reversion_expectation"],
            amm_findings_labelled=True, segmentation_reproducible=True,
            negative_mechanisms_retained=True,
            strategy_pnl_computed=True, optimization_performed=False,
            mechanism_registry_present=True, unsupported_alpha_claim=False,
        )
        out = determine_mech1_decision(inp)
        self.assertTrue(any("PnL" in b for b in out.blocking_issues))


class TestTimeEpoch(unittest.TestCase):
    def test_epoch_partition(self):
        series = [{"event_time_utc": f"2026-01-25T{i:02d}:00:00+00:00",
                   "basis_bps": float(i)} for i in range(24)]
        out = time_epoch_anatomy(series, "basis_bps", "T")
        labels = {r["label"] for r in out}
        self.assertIn("T_h0", labels)
        self.assertTrue(any("weekend" in r["label"] for r in out))
        self.assertTrue(any("weekday" in r["label"] for r in out))


if __name__ == "__main__":
    unittest.main()
