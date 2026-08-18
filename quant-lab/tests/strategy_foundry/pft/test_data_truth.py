"""PFT-B2 data truth tests.

Deterministic unit tests for loading/validation, session measurement,
expected-closure logic, H1 resampling, panel partition labels, and
audit helpers. Uses synthetic frames only; the big repository data is
audited by run_b2_audit.py, not by unit tests.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from strategy_foundry.pft.data import audits
from strategy_foundry.pft.data import loading, panel as panel_mod, sessions


# ---------------------------------------------------------------------------
# Loading + OHLC quarantine
# ---------------------------------------------------------------------------


class TestLoading:
    def _write_csv(self, tmp_path, text):
        p = tmp_path / "x.csv"
        p.write_text(text, encoding="utf-8")
        return p

    def test_clean_ohlc_loads(self, tmp_path):
        p = self._write_csv(tmp_path, (
            "time,open,high,low,close,volume\n"
            "2023-01-02 00:00:00,1.00,1.02,0.99,1.01,10\n"
            "2023-01-02 00:05:00,1.01,1.03,1.00,1.02,12\n"
        ))
        res = loading.load_canonical(p)
        assert len(res.frame) == 2
        assert res.ohlc_violations == 0
        assert res.dropped_rows == 0
        assert str(res.frame.index.tz) == "UTC"

    def test_ohlc_violation_quarantined_not_repaired(self, tmp_path):
        p = self._write_csv(tmp_path, (
            "time,open,high,low,close\n"
            "2023-01-02 00:00:00,1.00,0.98,0.99,1.01\n"  # high < open: violation
            "2023-01-02 00:05:00,1.01,1.03,1.00,1.02\n"
        ))
        res = loading.load_canonical(p)
        assert res.ohlc_violations == 1
        assert len(res.frame) == 1
        assert len(res.quarantine) == 1

    def test_nat_rows_dropped(self, tmp_path):
        p = self._write_csv(tmp_path, (
            "time,open,high,low,close\n"
            "garbage,1.00,1.02,0.99,1.01\n"
            "2023-01-02 00:05:00,1.01,1.03,1.00,1.02\n"
        ))
        res = loading.load_canonical(p)
        assert res.na_rows == 1
        assert len(res.frame) == 1

    def test_invariant_must_hold_for_all_rows(self, tmp_path):
        p = self._write_csv(tmp_path, (
            "timestamp,open,high,low,close\n"
            "2023-01-02 00:00:00,1.00,1.02,0.99,1.01\n"
            "2023-01-02 00:05:00,1.01,1.00,1.02,1.02\n"  # low > close: violation
        ))
        res = loading.load_canonical(p)
        assert res.ohlc_violations == 1


# ---------------------------------------------------------------------------
# Session measurement + expected closure
# ---------------------------------------------------------------------------


class TestSessions:
    def _fx_frame(self):
        idx = pd.date_range("2023-01-02", periods=24 * 5, freq="h", tz="UTC")
        return pd.DataFrame({"close": np.arange(len(idx)) + 100.0}, index=idx)

    def test_measure_weekday_only(self):
        s = sessions.measure_session_structure(self._fx_frame())
        assert s["weekend_fraction"] == 0.0
        assert s["median_bars_per_day"] == 24.0

    def test_weekend_fraction_measured(self):
        idx = pd.date_range("2023-01-01", periods=7 * 24, freq="h", tz="UTC")
        frame = pd.DataFrame({"close": np.arange(len(idx))}, index=idx)
        s = sessions.measure_session_structure(frame)
        assert abs(s["weekend_fraction"] - 2 / 7) < 1e-9

    def test_expected_closed_weekday_rule(self):
        rule = sessions.derive_expected_closed(
            {"median_bars_per_day": 23}, weekday_closed_utc_hours={0},
            weekend_start_utc=5 * 24, weekend_end_utc=7 * 24)
        assert sessions.is_expected_closed(pd.Timestamp("2023-01-03 00:00", tz="UTC"), rule)
        assert not sessions.is_expected_closed(pd.Timestamp("2023-01-03 01:00", tz="UTC"), rule)
        # Saturday
        assert sessions.is_expected_closed(pd.Timestamp("2023-01-07 12:00", tz="UTC"), rule)

    def test_expected_closed_fx_weekend(self):
        rule = sessions.derive_expected_closed(
            {"median_bars_per_day": 288}, weekday_closed_utc_hours=set(),
            weekend_start_utc=5 * 24, weekend_end_utc=6 * 24 + 22)
        assert not sessions.is_expected_closed(pd.Timestamp("2023-01-06 23:00", tz="UTC"), rule)  # Fri open
        assert sessions.is_expected_closed(pd.Timestamp("2023-01-07 00:00", tz="UTC"), rule)      # Sat closed
        assert not sessions.is_expected_closed(pd.Timestamp("2023-01-08 22:00", tz="UTC"), rule)  # Sun 22:00 open

    def test_derive_weekday_closed_from_histogram(self):
        hist = {h: 100 for h in range(24)}
        hist[0] = 5
        closed = sessions.derive_weekday_closed(hist, min_fraction=0.10)
        assert closed == [0]


# ---------------------------------------------------------------------------
# H1 resampling + panel
# ---------------------------------------------------------------------------


class TestPanel:
    def test_resample_ohlc_aggregation(self):
        idx = pd.date_range("2023-01-02 00:00", periods=12, freq="5min", tz="UTC")
        frame = pd.DataFrame({
            "open": [1.0 + 0.01 * i for i in range(12)],
            "high": [1.0 + 0.02 * i for i in range(12)],
            "low": [0.99 + 0.01 * i for i in range(12)],
            "close": [1.0 + 0.01 * i for i in range(12)],
            "volume": [1] * 12,
        }, index=idx)
        h1 = panel_mod.resample_h1(frame)
        assert len(h1) == 1
        row = h1.iloc[0]
        assert row["open"] == 1.0
        assert row["close"] == pytest.approx(1.11)
        assert row["high"] == pytest.approx(1.22)
        assert row["low"] == pytest.approx(0.99)
        assert row["volume"] == 12

    def test_partition_of(self):
        assert panel_mod.partition_of(pd.Timestamp("2024-06-01", tz="UTC")) == "DEVELOPMENT"
        assert panel_mod.partition_of(pd.Timestamp("2025-06-01", tz="UTC")) == "CONFIRMATION"
        assert panel_mod.partition_of(pd.Timestamp("2026-03-01", tz="UTC")) == "HOLDOUT"

    def test_panel_tags_stale_and_partition(self):
        idx = pd.date_range("2023-01-02", periods=10, freq="h", tz="UTC")
        frames = {a: pd.DataFrame(
            {"open": np.ones(10), "high": np.ones(10) + 0.1, "low": np.ones(10) - 0.1,
             "close": np.ones(10), "volume": np.ones(10)}, index=idx)
            for a in ("W", "E", "C", "I")}
        # Punch a hole in W at hour 3.
        frames["W"] = frames["W"].drop(idx[3])
        rule = sessions.derive_expected_closed(
            {"median_bars_per_day": 24}, set(), 5 * 24, 7 * 24)
        panel = panel_mod.build_panel(frames, {a: rule for a in frames},
                                      idx[0], idx[-1])
        assert not panel.loc[idx[3], "W.observed"]
        assert panel.loc[idx[3], "W.missing_reason"] == "UNEXPECTED_MISSING"
        assert panel.loc[idx[3], "W.price_origin"] == "CARRIED_STALE"
        assert panel.loc[idx[3], "W.stale_age_hours"] == 1.0
        assert panel.loc[idx[4], "W.stale_age_hours"] == 0.0  # observed bar resets the clock
        assert (panel["partition"] == "DEVELOPMENT").all()

    def test_panel_expected_closed_tag(self):
        idx = pd.date_range("2023-01-02", periods=48, freq="h", tz="UTC")  # Mon+Tue, no weekend
        frames = {a: pd.DataFrame(
            {"open": np.ones(48), "high": np.ones(48) + 0.1, "low": np.ones(48) - 0.1,
             "close": np.ones(48), "volume": np.ones(48)}, index=idx)
            for a in ("W", "E", "C", "I")}
        # E has no bar at hour 0 (weekday-closed per rule) and no bar at hour 5 (unexpected).
        frames["E"] = frames["E"].drop([idx[0], idx[5]])
        rule = sessions.derive_expected_closed(
            {"median_bars_per_day": 23}, weekday_closed_utc_hours={0},
            weekend_start_utc=5 * 24, weekend_end_utc=7 * 24)
        panel = panel_mod.build_panel(frames, {a: rule for a in frames}, idx[0], idx[-1])
        assert panel.loc[idx[0], "E.missing_reason"] == "EXPECTED_CLOSED"
        assert panel.loc[idx[5], "E.missing_reason"] == "UNEXPECTED_MISSING"
        assert panel.loc[idx[1], "E.missing_reason"] == ""


# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------


class TestAudits:
    def test_triangular_parity_identity(self):
        idx = pd.date_range("2023-01-02", periods=100, freq="5min", tz="UTC")
        # Construct E, C, EC such that r_EC == r_E + r_C exactly.
        e_close = 1.10 + np.cumsum(np.random.RandomState(0).normal(0, 1e-4, len(idx)))
        c_close = 1.30 + np.cumsum(np.random.RandomState(1).normal(0, 1e-4, len(idx)))
        ec_close = e_close * c_close
        e = pd.DataFrame({"close": e_close}, index=idx)
        c = pd.DataFrame({"close": c_close}, index=idx)
        ec = pd.DataFrame({"close": ec_close}, index=idx)
        out, stats, extremes = audits.triangular_parity(e, c, ec)
        assert stats["n"] == 99
        assert abs(stats["mean"]) < 1e-9
        assert stats["abs_residual_gt_1e_3"] == 0

    def test_extreme_event_rows_never_deleted(self):
        idx = pd.date_range("2023-01-02", periods=500, freq="h", tz="UTC")
        close = 100.0 + np.cumsum(np.random.RandomState(7).normal(0, 0.01, len(idx)))
        close[250] = close[249] * 1.05  # one extreme move
        frame = pd.DataFrame({"close": close}, index=idx)
        rows = audits.extreme_event_rows(frame, threshold_quantile=0.99)
        assert rows
        assert all(r["flag"] == "UNRESOLVED" for r in rows)

    def test_cross_series_identity_same_series(self):
        idx = pd.date_range("2023-01-02", periods=200, freq="h", tz="UTC")
        close = 1.0 + np.cumsum(np.random.RandomState(3).normal(0, 1e-4, len(idx)))
        a = pd.DataFrame({"close": close}, index=idx)
        res = audits.cross_series_identity(a, a.copy())
        assert res["return_corr"] == pytest.approx(1.0, abs=1e-6)

    def test_coverage_rows_counts(self):
        idx = pd.date_range("2023-01-02", periods=24, freq="h", tz="UTC")
        frames = {a: pd.DataFrame(
            {"open": np.ones(24), "high": np.ones(24) + 0.1, "low": np.ones(24) - 0.1,
             "close": np.ones(24), "volume": np.ones(24)}, index=idx)
            for a in ("W", "E", "C", "I")}
        rule = sessions.derive_expected_closed({"median_bars_per_day": 24}, set(),
                                               5 * 24, 7 * 24)
        panel = panel_mod.build_panel(frames, {a: rule for a in frames}, idx[0], idx[-1])
        rows = audits.coverage_rows(panel, ["W", "E"])
        assert rows[0]["total_canonical_slots"] == 24
        assert rows[0]["valid_observed"] == 24


# ---------------------------------------------------------------------------
# Emitted B2 artifacts validate against schemas (when present)
# ---------------------------------------------------------------------------


class TestB2Artifacts:
    QUANT_LAB = Path(__file__).resolve().parents[3]
    OUT_DIR = QUANT_LAB / "research" / "strategy_foundry" / "pft" / "shared" / "data_truth"

    def test_decision_schema(self):
        path = self.OUT_DIR / "DECISION.json"
        if not path.exists():
            pytest.skip("B2 artifacts not emitted")
        from strategy_foundry.pft.governance.decisions import validate_decision_dict

        data = json.loads(path.read_text(encoding="utf-8"))
        assert validate_decision_dict(data) == []
        assert data["data_truth_pass"] is True
        assert data["economic_pnl_computed"] is False

    def test_hash_manifest_complete(self):
        path = self.OUT_DIR / "INPUT_HASH_MANIFEST.json"
        if not path.exists():
            pytest.skip("B2 artifacts not emitted")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["hash_algorithm"] == "sha256"
        assert len(data["raw_files"]) >= 9
        assert len(data["normalized_h1_series"]) == 5
        assert len(data["synchronized_panel"]) == 64

    def test_panel_covers_development_and_partitions(self):
        path = self.OUT_DIR / "SYNC_PANEL_H1.parquet"
        if not path.exists():
            pytest.skip("B2 artifacts not emitted")
        panel = pd.read_parquet(path)
        assert len(panel) > 20000
        assert set(panel["partition"].unique()) == {"DEVELOPMENT", "CONFIRMATION", "HOLDOUT"}
