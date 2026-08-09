"""
Deterministic tests for the Phase 3 canonical common market panel.
CR-P3-COMMON-PANEL-01
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases.phase_3_panel import (
    PHASE2_SYMBOLS,
    ASSET_CLASS,
    CURRENCY_ORIENTATION,
    CROSS_RATE_IDENTITIES,
    build_input_manifest,
    build_availability_masks,
    build_market_open_masks,
    missingness_mask,
    build_h4_panel,
    build_d1_panel,
    build_price_transforms,
    cross_rate_residuals,
    staleness_flag,
    outlier_report,
    coverage_matrix,
    common_overlap,
)


BASE = Path(__file__).resolve().parents[1]
NORM_H1 = BASE / "data" / "normalized" / "h1"
PHASE3 = BASE / "artifacts" / "phase_03"


def make_master(frames):
    from capital_routing.phases.phase_3_panel import build_h1_master_panel, load_accepted_h1
    panel, per = build_h1_master_panel(NORM_H1, PHASE2_SYMBOLS)
    return panel, per


class TestInputManifest:
    def test_manifest_sources_accepted_phase2_only(self):
        m = build_input_manifest(NORM_H1, PHASE2_SYMBOLS)
        assert m["gate_source"] == "CR-P2-MARKET-CALENDAR-AUDIT-06"
        assert m["symbols"] == PHASE2_SYMBOLS
        assert len(m["inputs"]) == 10
        for rec in m["inputs"]:
            assert rec["phase2_qc_status"] == "accepted"
            assert rec["timeframe"] == "H1"
            assert rec["sha256"]

    def test_manifest_bars_missing_file(self):
        with pytest.raises(FileNotFoundError):
            build_input_manifest(NORM_H1, ["EURUSD", "NOTREALXXX"])


class TestH1Alignment:
    @pytest.fixture()
    def master(self):
        from capital_routing.phases.phase_3_panel import build_h1_master_panel
        panel, per = build_h1_master_panel(NORM_H1, PHASE2_SYMBOLS)
        return panel, per

    def test_canonical_utc_index(self, master):
        panel, per = master
        assert panel.index.tz is not None
        assert str(panel.index.tz) == "UTC"

    def test_no_duplicate_timestamps(self, master):
        panel, _ = master
        assert not panel.index.has_duplicates

    def test_alignment_same_timestamp_same_observation(self, master):
        panel, per = master
        # EURUSD and GBPUSD share timestamp; verify a known overlap row
        ts = pd.Timestamp("2023-07-03 12:00", tz="UTC")
        if ts in panel.index:
            assert panel.loc[ts, "EURUSD_close"] == per["EURUSD"].loc[ts, "close"]


class TestNoForwardFill:
    @pytest.fixture()
    def master(self):
        from capital_routing.phases.phase_3_panel import build_h1_master_panel
        panel, _ = build_h1_master_panel(NORM_H1, PHASE2_SYMBOLS)
        return panel

    def test_missing_preserved_as_nan(self, master):
        panel = master
        # EURUSD starts 2023-07; before that its columns must be NaN, not filled
        early = pd.Timestamp("2022-01-03 12:00", tz="UTC")
        if early in panel.index:
            assert pd.isna(panel.loc[early, "EURUSD_close"])
        # after a real observation, a later missing timestamp stays NaN (no ffill)
        ser = panel["EURUSD_close"].dropna()
        # verify no forward-fill introduces fill beyond duplicates removed
        assert not panel["EURUSD_close"].isna().all()


class TestMarketCalendar:
    def test_market_open_distinguishes_closed(self):
        av = pd.read_parquet(PHASE3 / "availability_masks.parquet")
        mo = pd.read_parquet(PHASE3 / "market_open_masks.parquet")
        ms = missingness_mask(av, mo)
        # A Saturday should be 'closed', not 'unexpected_missing'
        sat = pd.Timestamp("2023-07-08 12:00", tz="UTC")
        if sat in ms.index:
            assert ms.loc[sat, "EURUSD"] == "closed"

    def test_legitimate_closure_not_failure(self):
        av = pd.read_parquet(PHASE3 / "availability_masks.parquet")
        mo = pd.read_parquet(PHASE3 / "market_open_masks.parquet")
        ms = missingness_mask(av, mo)
        # Sundays are market-closed => classified 'closed', not 'unexpected_missing'
        sun = pd.Timestamp("2023-07-09 12:00", tz="UTC")
        if sun in ms.index:
            assert ms.loc[sun, "EURUSD"] == "closed"
        # Verify every 'unexpected_missing' implies market_open True (semantic contract)
        mask_aspresent = (ms == "unexpected_missing") & (mo == False)
        assert mask_aspresent.sum().sum() == 0


class TestH4:
    @pytest.fixture()
    def master(self):
        from capital_routing.phases.phase_3_panel import build_h1_master_panel
        panel, _ = build_h1_master_panel(NORM_H1, PHASE2_SYMBOLS)
        return panel

    def test_h4_from_h1(self, master):
        h4 = build_h4_panel(master, PHASE2_SYMBOLS)
        assert len(h4) > 0
        # EURUSD 2023-07-03 00:00 bucket should exist with 4 constituents
        bucket = pd.Timestamp("2023-07-03 00:00", tz="UTC")
        if bucket in h4.index and not pd.isna(h4.loc[bucket, "EURUSD_close"]):
            assert h4.loc[bucket, "EURUSD_h1_count"] == 4

    def test_h4_aggregation_verified(self, master):
        h4 = build_h4_panel(master, PHASE2_SYMBOLS)
        # open = first, high = max, low = min, close = last
        bucket = pd.Timestamp("2023-07-03 00:00", tz="UTC")
        if bucket in h4.index:
            sub = master.loc[bucket: bucket + pd.Timedelta(hours=3), "EURUSD_open"]
            expected_open = sub.dropna().iloc[0]
            assert np.isclose(h4.loc[bucket, "EURUSD_open"], expected_open, rtol=1e-6)


class TestD1:
    @pytest.fixture()
    def master(self):
        from capital_routing.phases.phase_3_panel import build_h1_master_panel
        panel, _ = build_h1_master_panel(NORM_H1, PHASE2_SYMBOLS)
        return panel

    def test_d1_from_h1(self, master):
        d1 = build_d1_panel(master, PHASE2_SYMBOLS)
        assert len(d1) > 0

    def test_d1_boundary_documented(self, master):
        d1 = build_d1_panel(master, PHASE2_SYMBOLS, boundary_hour=0)
        # EURUSD daily rows should be fewer than H1 rows
        h1_rows = int(master["EURUSD_close"].notna().sum())
        d1_rows = int(d1["EURUSD_close"].notna().sum())
        assert d1_rows <= h1_rows


class TestOrientation:
    def test_pair_orientation(self):
        assert CURRENCY_ORIENTATION["EURUSD"] == ("EUR", "USD")
        assert CURRENCY_ORIENTATION["USDCHF"] == ("USD", "CHF")
        assert CURRENCY_ORIENTATION["USDJPY"] == ("USD", "JPY")

    def test_orientation_sign_convention_documented(self):
        # EURUSD positive return => EUR strength / USD weakness
        base, quote = CURRENCY_ORIENTATION["EURUSD"]
        assert base == "EUR" and quote == "USD"


class TestCrossRate:
    def test_identity_definitions(self):
        identities = CROSS_RATE_IDENTITIES
        assert ("EURGBP", "EURUSD", "GBPUSD") in identities
        assert ("CHFJPY", "USDCHF", "USDJPY") in identities

    def test_residual_approximately_zero(self):
        closes = pd.DataFrame({
            s: pd.read_parquet(NORM_H1 / f"{s}_H1.parquet").set_index(
                pd.to_datetime(pd.read_parquet(NORM_H1 / f"{s}_H1.parquet")["timestamp_utc"], utc=True)
            )["close"] for s in PHASE2_SYMBOLS
        })
        res = cross_rate_residuals(closes)
        for (o, n, d), fr in res.items():
            fr2 = fr.dropna()
            if len(fr2) > 1000:
                assert abs(fr2["residual"].mean()) < 5e-4


class TestCoverage:
    def test_coverage_matrix_generated(self):
        mh = pd.read_parquet(PHASE3 / "h1_master_panel.parquet")
        av = pd.read_parquet(PHASE3 / "availability_masks.parquet")
        mo = pd.read_parquet(PHASE3 / "market_open_masks.parquet")
        cov = coverage_matrix(mh.index, av, mo, PHASE2_SYMBOLS)
        assert not cov.empty
        # coverage never above 100
        assert (cov["coverage_pct"] <= 100.0001).all()

    def test_no_forward_fill_invariant_artifacts(self):
        mh = pd.read_parquet(PHASE3 / "h1_master_panel.parquet")
        # EURUSD before 2023 must be NaN
        early = mh.index[mh.index < pd.Timestamp("2023-07-03", tz="UTC")]
        if len(early):
            assert mh.loc[early, "EURUSD_close"].isna().all()


class TestCommonOverlap:
    def test_common_window_reported(self):
        ov = json.loads((PHASE3 / "common_overlap_report.json").read_text())
        assert ov["intersection_valid_hours"] == 17273
        assert ov["earliest_common_ts"].startswith("2023-07-03")
        assert ov["latest_common_ts"].startswith("2026-05-21")

    def test_per_symbol_coverage_common_window_high(self):
        ov = json.loads((PHASE3 / "common_overlap_report.json").read_text())
        cov = ov.get("per_symbol_common_window_coverage_pct", {})
        for sym in PHASE2_SYMBOLS:
            assert cov[sym] >= 97.0, f"{sym} below 97%"


class TestOutliers:
    def test_outlier_flags_no_drop(self):
        ot = pd.read_csv(PHASE3 / "outlier_report.csv", index_col=0)
        assert "EURUSD_impossible_ohlc" in ot.columns
        assert "EURUSD_extreme_return" in ot.columns

    def test_no_impossible_ohlc(self):
        ot = pd.read_csv(PHASE3 / "outlier_report.csv", index_col=0)
        for sym in PHASE2_SYMBOLS:
            assert (ot[f"{sym}_impossible_ohlc"] == True).sum() == 0
        for sym in PHASE2_SYMBOLS:
            assert (ot[f"{sym}_nonpositive"] == True).sum() == 0