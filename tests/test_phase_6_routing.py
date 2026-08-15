"""
Deterministic tests for the Phase 6 forward routing study.
CR-P6-FORWARD-ROUTING-STUDY-01

Covers the 15 required test families (brief section 35):
  1. forward horizon indexing        2. event-bar exclusion
  3. no threshold recomputation      4. development/holdout split frozen
  5. holdout not used in selection   6. destination ranking
  7. overlap sensitivity deterministic 8. bootstrap deterministic (fixed seed)
  9. FDR correct                     10. residual decay
 11. MFE/MAE horizon bounds          12. pair-return orientation
 13. symmetric origin analysis       14. subperiod assignment
 15. candidate freeze reproducible
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases import phase_6_analysis as an
from capital_routing.phases import phase_6_events as ev6
from capital_routing.phases import phase_6_outcomes as oc
from capital_routing.phases import phase_6_stats as st

CURR = ["EUR", "GBP", "USD", "CHF", "JPY"]
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURGBP",
         "EURJPY", "GBPJPY", "CHFJPY", "EURCHF", "GBPCHF"]
BASE = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# synthetic fixtures
# ---------------------------------------------------------------------------


def _hourly(n: int = 24, start: str = "2024-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="h", tz="UTC")


def _mk_comp(idx: pd.DatetimeIndex, value: float = 0.0) -> pd.DataFrame:
    cols = ([f"{c}_factor" for c in CURR]
            + [f"{c}_rank" for c in CURR]
            + [f"{c}_volatility" for c in CURR])
    df = pd.DataFrame(value, index=idx, columns=cols)
    return df


def _mk_panel(idx: pd.DatetimeIndex) -> pd.DataFrame:
    cols = [f"{p}_close" for p in PAIRS]
    df = pd.DataFrame(1.0, index=idx, columns=cols)
    return df


def _mk_events(ts_list) -> pd.DataFrame:
    return pd.DataFrame([{
        "event_id": f"E{i}", "event_start": str(ts),
        "event_family": "BROAD_CURRENCY_EVENT", "origin_currency": "EUR",
        "direction": "LIQUIDATION", "severity": "LOW", "session": "London",
    } for i, ts in enumerate(ts_list)])


# ---------------------------------------------------------------------------
# 1. forward horizon indexing
# ---------------------------------------------------------------------------


class TestForwardHorizonIndexing:
    def test_window_bounds_exclusive_start(self):
        grid = _hourly(24).values.astype("int64")
        ts_ns = int(pd.Timestamp("2024-01-01 05:00", tz="UTC").value)
        s, e = oc._window_bounds(grid, ts_ns, 4)
        # first bar strictly after 05:00 is 06:00 -> index 6; last bar <= 09:00 -> 9
        assert s == 6
        assert e == 9

    def test_window_bounds_empty_when_no_bars(self):
        grid = _hourly(10).values.astype("int64")
        ts_ns = int(pd.Timestamp("2024-01-01 09:00", tz="UTC").value)
        s, e = oc._window_bounds(grid, ts_ns, 4)
        assert s > e  # no forward bars available


# ---------------------------------------------------------------------------
# 2. event timestamp excluded from future return
# ---------------------------------------------------------------------------


class TestEventBarExclusion:
    def test_event_bar_not_in_forward_window(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        comp.loc[idx[5], "EUR_factor"] = 999.0  # huge factor AT the event bar
        events = _mk_events([idx[5]])
        panel = _mk_panel(idx)
        out = oc.build_forward_outcomes(events, comp, panel, horizons=[1, 2],
                                        horizons_optional=[])
        # forward window starts at idx[6]; the 999 at idx[5] must be excluded
        assert out.loc[0, "EUR_forward_1"] == pytest.approx(0.0)
        assert out.loc[0, "EUR_forward_2"] == pytest.approx(0.0)

    def test_next_bar_enters_window(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        comp.loc[idx[6], "EUR_factor"] = 5.0  # first bar after the event
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, _mk_panel(idx),
                                        horizons=[1], horizons_optional=[])
        assert out.loc[0, "EUR_forward_1"] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# 3. no event threshold recomputation
# ---------------------------------------------------------------------------


class TestNoThresholdRecomputation:
    def test_hash_mismatch_refuses_frozen_input(self, tmp_path, monkeypatch):
        f = tmp_path / "routing_events.parquet"
        pd.DataFrame({"x": [1]}).to_parquet(f)
        monkeypatch.setitem(ev6.PHASE5_INPUT_HASHES,
                            "routing_events.parquet", "0" * 64)
        with pytest.raises(ValueError, match="hash mismatch"):
            ev6.load_frozen_phase5(tmp_path)

    def test_committed_phase5_artifacts_match_frozen_hashes(self):
        # The committed artifacts must hash-match the frozen constants; the
        # Phase 5 threshold manifest is loaded as-is and never recomputed.
        frames = ev6.load_frozen_phase5(BASE / "artifacts" / "phase_05")
        assert len(frames["routing_events.parquet"]) == 8076
        assert isinstance(frames["threshold_manifest.json"], dict)
        assert "origin_factor_p95_threshold" in frames["threshold_manifest.json"]


# ---------------------------------------------------------------------------
# 4. development/holdout split frozen
# ---------------------------------------------------------------------------


class TestSplitFrozen:
    def test_split_boundaries_match_brief(self):
        assert ev6.DEVELOPMENT_START == pd.Timestamp("2023-07-01", tz="UTC")
        assert ev6.DEVELOPMENT_END == pd.Timestamp("2025-06-30 23:59:59", tz="UTC")
        assert ev6.HOLDOUT_START == pd.Timestamp("2025-07-01", tz="UTC")
        assert ev6.HOLDOUT_END == pd.Timestamp("2026-05-31 23:59:59", tz="UTC")

    def test_split_manifest_frozen_on_disk(self):
        p = BASE / "artifacts" / "phase_06" / "split_manifest.json"
        assert p.exists(), "run the pipeline before this test"
        m = json.loads(p.read_text(encoding="utf-8"))
        assert m["frozen_before_discovery"] is True
        assert m["holdout"]["start"] == str(ev6.HOLDOUT_START)


# ---------------------------------------------------------------------------
# 5. holdout not used during candidate selection
# ---------------------------------------------------------------------------


class TestHoldoutNotUsedInSelection:
    def test_candidate_selection_uses_development_only(self):
        dev_row = {
            "split": "development", "origin_currency": "EUR",
            "direction": "LIQUIDATION", "currency": "JPY", "horizon_h": 4,
            "n": 200, "effect": 0.5, "dest_prob": 0.3,
            "ci_low": 0.1, "ci_high": 0.9, "p": 1e-6, "q": 0.02,
        }
        hold_row = {
            "split": "holdout", "origin_currency": "EUR",
            "direction": "LIQUIDATION", "currency": "USD", "horizon_h": 4,
            "n": 200, "effect": 0.99, "dest_prob": 0.9,
            "ci_low": 0.5, "ci_high": 1.0, "p": 1e-9, "q": 0.0,
        }
        dev = pd.DataFrame([dev_row, hold_row])
        ev_long = _mk_long_with_signs("EUR", "LIQUIDATION", "JPY", 4)
        cand = an.freeze_candidates(dev, ev_long)
        assert len(cand) == 1
        assert cand[0]["destination"] == "JPY"
        assert all(c["destination"] != "USD" for c in cand)


def _mk_long_with_signs(origin, direction, currency, h, n=10) -> pd.DataFrame:
    rows = []
    for sub in ["2023H2", "2024H1", "2024H2", "2025H1"]:
        for _ in range(n):
            rows.append({
                "origin_currency": origin, "direction": direction,
                "currency": currency, "horizon_h": h, "subperiod": sub,
                "split": "development", "forward": 1.0,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. destination ranking correct
# ---------------------------------------------------------------------------


class TestDestinationRanking:
    def test_strongest_forward_currency_wins(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        comp.loc[idx[6], "JPY_factor"] = 10.0
        comp.loc[idx[6], "EUR_factor"] = 1.0
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, _mk_panel(idx),
                                        horizons=[1], horizons_optional=[])
        assert out.loc[0, "destination_1"] == "JPY"

    def test_currency_rank_helper(self):
        cum = np.array([2.0, 5.0, -1.0, 3.0, 0.0])
        assert oc._currency_rank(cum, 1) == 1.0   # GBP strongest
        assert oc._currency_rank(cum, 2) == 5.0   # USD weakest
        assert oc._currency_rank(cum, 0) == 3.0   # EUR third


# ---------------------------------------------------------------------------
# 7. overlapping-event sensitivity deterministic
# ---------------------------------------------------------------------------


class TestOverlapSensitivity:
    def test_deterministic_and_reduces_count(self):
        idx = _hourly(24)
        events = _mk_events(list(idx[::1]))
        m1 = st.non_overlapping_mask(events, 6)
        m2 = st.non_overlapping_mask(events, 6)
        np.testing.assert_array_equal(m1, m2)
        assert int(m1.sum()) < len(events)

    def test_cooldown_monotonic(self):
        idx = _hourly(24)
        events = _mk_events(list(idx))
        n6 = int(st.non_overlapping_mask(events, 6).sum())
        n24 = int(st.non_overlapping_mask(events, 24).sum())
        assert n24 <= n6


# ---------------------------------------------------------------------------
# 8. bootstrap deterministic with fixed seed
# ---------------------------------------------------------------------------


class TestBootstrapDeterministic:
    def test_same_seed_identical(self):
        x = np.random.default_rng(0).normal(size=200)
        a = st.bootstrap_ci(x, n_boot=100, seed=42)
        b = st.bootstrap_ci(x, n_boot=100, seed=42)
        assert a == b

    def test_different_seed_differs(self):
        x = np.random.default_rng(0).normal(size=200)
        a = st.bootstrap_ci(x, n_boot=100, seed=42)
        c = st.bootstrap_ci(x, n_boot=100, seed=1)
        assert a != c


# ---------------------------------------------------------------------------
# 9. FDR implementation correct
# ---------------------------------------------------------------------------


class TestFDR:
    def test_benjamini_hochberg_manual_example(self):
        p = np.array([0.01, 0.02, 0.03, 0.4, 0.9])
        q = st.bh_fdr(p)
        np.testing.assert_allclose(q, [0.05, 0.05, 0.05, 0.5, 0.9], atol=1e-9)

    def test_all_significant_small(self):
        p = np.array([1e-6, 2e-6, 3e-6, 4e-6])
        q = st.bh_fdr(p)
        assert (q <= 0.05).all()
        assert (q > 0).all()


# ---------------------------------------------------------------------------
# 10. residual decay correct
# ---------------------------------------------------------------------------


class TestResidualDecay:
    def test_half_life_measured(self):
        idx = _hourly(30)
        comp = pd.DataFrame(index=idx)
        comp["EURUSD_residual"] = 0.0
        comp.loc[idx[5], "EURUSD_residual"] = 1.0   # shock at T
        comp.loc[idx[6], "EURUSD_residual"] = 0.3   # halved by +1h
        comp.loc[idx[7], "EURUSD_residual"] = 0.1
        res_ev = pd.DataFrame([{
            "event_id": "R1", "origin_currency": "EURUSD",
            "event_ts": idx[5], "event_start": str(idx[5]),
        }])
        out = an.residual_decay_analysis(res_ev, comp)
        row = out[out["pair"] == "EURUSD"].iloc[0]
        assert row["median_half_life_h"] == pytest.approx(1.0)
        assert row["mean_residual_T"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 11. MFE/MAE horizon bounds correct
# ---------------------------------------------------------------------------


class TestMFEMAEBounds:
    def test_factor_mfe_mae_are_path_extrema(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        # EUR factor path: +1, +2, -3, +1 (cumulative 1,3,0,1) over +1..+4h
        comp.loc[idx[6], "EUR_factor"] = 1.0
        comp.loc[idx[7], "EUR_factor"] = 2.0
        comp.loc[idx[8], "EUR_factor"] = -3.0
        comp.loc[idx[9], "EUR_factor"] = 1.0
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, _mk_panel(idx),
                                        horizons=[4], horizons_optional=[])
        r = out.iloc[0]
        assert r["EUR_forward_4"] == pytest.approx(1.0)    # 1+2-3+1
        assert r["EUR_mfe_4"] == pytest.approx(3.0)        # peak cumulative
        assert r["EUR_mae_4"] == pytest.approx(0.0)        # min cumulative

    def test_pair_mfe_mae_within_horizon(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        panel = _mk_panel(idx)
        # EURUSD closes: rise, rise, fall, rise
        base = 1.0
        panel.loc[idx[5], "EURUSD_close"] = base
        panel.loc[idx[6], "EURUSD_close"] = base * 1.01
        panel.loc[idx[7], "EURUSD_close"] = base * 1.03
        panel.loc[idx[8], "EURUSD_close"] = base * 1.01
        panel.loc[idx[9], "EURUSD_close"] = base * 1.02
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, panel,
                                        horizons=[4], horizons_optional=[])
        r = out.iloc[0]
        assert r["EURUSD_return_4"] == pytest.approx(np.log(1.02), rel=1e-6)
        assert r["EURUSD_mfe_4"] == pytest.approx(np.log(1.03), rel=1e-6)
        assert r["EURUSD_mae_4"] == pytest.approx(np.log(1.01), rel=1e-6)


# ---------------------------------------------------------------------------
# 12. pair-return orientation correct
# ---------------------------------------------------------------------------


class TestPairReturnOrientation:
    def test_positive_close_path_gives_positive_return(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        panel = _mk_panel(idx)
        panel.loc[idx[5], "GBPUSD_close"] = 1.30
        panel.loc[idx[6], "GBPUSD_close"] = 1.31
        panel.loc[idx[7], "GBPUSD_close"] = 1.32
        panel.loc[idx[8], "GBPUSD_close"] = 1.33
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, panel,
                                        horizons=[2], horizons_optional=[])
        r = out.iloc[0]
        assert r["GBPUSD_return_2"] == pytest.approx(np.log(1.32 / 1.30), rel=1e-6)
        assert r["GBPUSD_return_2"] > 0

    def test_negative_close_path_gives_negative_return(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        panel = _mk_panel(idx)
        panel.loc[idx[5], "EURUSD_close"] = 1.10
        panel.loc[idx[6], "EURUSD_close"] = 1.09
        panel.loc[idx[7], "EURUSD_close"] = 1.08
        events = _mk_events([idx[5]])
        out = oc.build_forward_outcomes(events, comp, panel,
                                        horizons=[2], horizons_optional=[])
        assert out.iloc[0]["EURUSD_return_2"] == pytest.approx(np.log(1.08 / 1.10), rel=1e-6)
        assert out.iloc[0]["EURUSD_return_2"] < 0


# ---------------------------------------------------------------------------
# 13. symmetric origin analysis
# ---------------------------------------------------------------------------


class TestSymmetricOriginAnalysis:
    def test_long_outcomes_cover_all_five_currencies(self):
        idx = _hourly(12)
        comp = _mk_comp(idx)
        events = _mk_events([idx[5], idx[6]])
        out = oc.build_forward_outcomes(events, comp, _mk_panel(idx),
                                        horizons=[1, 4], horizons_optional=[])
        ev = events.copy()
        ev["event_ts"] = pd.to_datetime(ev["event_start"], utc=True)
        ev["severity"] = "LOW"
        ev["session"] = "London"
        ev["regime_dispersion"] = "LOW_DISPERSION"
        ev["regime_vol"] = "LOW_VOL"
        ev["network_state"] = "CONSISTENT"
        ev["factor_vol_mean"] = 1.0
        ev = ev.merge(out, on="event_id", how="left")
        long_out = an.build_long_factor_outcomes(ev, horizons=[1, 4])
        # every event has rows for all 5 currencies at each horizon (symmetric path)
        for eid in events["event_id"]:
            for h in [1, 4]:
                sub = long_out[(long_out["event_id"] == eid) & (long_out["horizon_h"] == h)]
                assert set(sub["currency"]) == set(CURR)
                assert len(sub) == 5


# ---------------------------------------------------------------------------
# 14. subperiod assignment correct
# ---------------------------------------------------------------------------


class TestSubperiodAssignment:
    @pytest.mark.parametrize("ts,expected", [
        ("2023-07-01", "2023H2"),
        ("2023-12-31", "2023H2"),
        ("2024-01-01", "2024H1"),
        ("2024-07-01", "2024H2"),
        ("2025-01-01", "2025H1"),
        ("2025-06-30", "2025H1"),
        ("2025-07-01", "HOLDOUT"),
        ("2026-05-31", "HOLDOUT"),
        ("2023-06-30", "OUTSIDE"),
    ])
    def test_boundaries(self, ts, expected):
        t = pd.Timestamp(ts, tz="UTC")
        assert ev6.assign_subperiod(t) == expected


# ---------------------------------------------------------------------------
# exported parquet column naming (brief contract: horizon suffix "h")
# ---------------------------------------------------------------------------


class TestExportedColumnNaming:
    def test_parquet_columns_follow_brief_contract(self):
        import pyarrow.parquet as pq

        p = BASE / "artifacts" / "phase_06" / "event_forward_currency_factors.parquet"
        assert p.exists(), "run the pipeline before this test"
        names = pq.read_schema(p).names
        assert "destination_1h" in names
        assert "EUR_forward_1h" in names
        assert "EUR_forward_48h" in names
        assert "JPY_rank_change_48h" in names
        p2 = BASE / "artifacts" / "phase_06" / "event_forward_pair_returns.parquet"
        assert p2.exists(), "run the pipeline before this test"
        names2 = pq.read_schema(p2).names
        assert "EURUSD_return_4h" in names2
        assert "EURUSD_rv_24h" in names2


# ---------------------------------------------------------------------------
# 15. candidate freeze reproducible
# ---------------------------------------------------------------------------


class TestCandidateFreezeReproducible:
    def test_freeze_is_deterministic(self):
        dev = pd.DataFrame([{
            "split": "development", "origin_currency": "EUR",
            "direction": "LIQUIDATION", "currency": "JPY", "horizon_h": 6,
            "n": 300, "effect": 0.3, "dest_prob": 0.25,
            "ci_low": 0.05, "ci_high": 0.55, "p": 1e-4, "q": 0.01,
        }, {
            "split": "development", "origin_currency": "GBP",
            "direction": "ACCUMULATION", "currency": "CHF", "horizon_h": 48,
            "n": 120, "effect": 0.2, "dest_prob": 0.22,
            "ci_low": 0.0, "ci_high": 0.5, "p": 1e-3, "q": 0.05,
        }])
        ev_long = pd.concat([
            _mk_long_with_signs("EUR", "LIQUIDATION", "JPY", 6),
            _mk_long_with_signs("GBP", "ACCUMULATION", "CHF", 48),
        ], ignore_index=True)
        a = an.freeze_candidates(dev, ev_long)
        b = an.freeze_candidates(dev, ev_long)
        assert a == b
        assert len(a) == 2
        # criteria enforced
        for c in a:
            assert c["dev_n"] >= an.MIN_CANDIDATE_N
            assert abs(c["dev_effect"]) >= an.MIN_CANDIDATE_EFFECT
            assert c["dev_q"] <= an.CANDIDATE_Q
            assert c["subperiod_same_sign_count"] >= an.MIN_SUBPERIOD_SIGN
