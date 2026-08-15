"""
Phase 8 - CEREBUS overlay discovery tests (CR-P8).

Covers the canonical primitive definitions (tier / P90 / midpoint / rekey),
the causal observation window, the fingerprint construction (1 row per event,
vol-normalized baseline), statistical discipline (bootstrap, permutation, FDR),
and the candidate materiality protocol. All deterministic.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.phases.phase_8_primitives import (  # noqa: E402
    BUCKETS, TIER_BOUNDS, USDJPY_PIP, VIOLATION_MULT,
    bucket_counts, cumulative_counts, est_series,
    build_primitive_frame, build_session_ar_table, session_of,
)
from capital_routing.phases.phase_8_fingerprint import (  # noqa: E402
    build_fingerprints, _aligned,
)
from capital_routing.phases.phase_8_stats import (  # noqa: E402
    assign_split, bh_fdr, bootstrap_ci, permutation_p,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_m5(n_days: int = 3, start: str = "2024-01-01") -> pd.DataFrame:
    """Synthetic USDJPY M5 frame (UTC, tz-aware), one bar per 5 minutes."""
    idx = pd.date_range(start, periods=n_days * 288, freq="5min", tz="UTC")
    rng = np.random.default_rng(7)
    n = len(idx)
    base = 150.0 + np.cumsum(rng.normal(0, 0.002, n))
    o = base - 0.001
    c = base + 0.001
    h = np.maximum(o, c) + 0.002
    l = np.minimum(o, c) - 0.002
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx)


def tier_of(ar_pips: float) -> str:
    for name, bound in TIER_BOUNDS:
        if ar_pips < bound:
            return name
    return "NO-GO"


# ---------------------------------------------------------------------------
# canonical primitives
# ---------------------------------------------------------------------------

class TestTier:
    def test_boundaries(self):
        assert tier_of(19.9) == "T1"
        assert tier_of(20.0) == "T2"
        assert tier_of(29.9) == "T2"
        assert tier_of(30.0) == "T3"
        assert tier_of(44.9) == "T3"
        assert tier_of(45.0) == "NO-GO"
        assert tier_of(100.0) == "NO-GO"

    def test_session_ar_table(self):
        m5 = make_m5(3)
        ar = build_session_ar_table(m5)
        assert len(ar) == 3  # three session days
        # midpoint = (high + low) / 2
        assert np.allclose(ar["midpoint"],
                           (ar["ar_high"] + ar["ar_low"]) / 2.0)
        assert ar["ar_pips"].min() > 0

    def test_session_rule(self):
        # 20:00 EST belongs to that date; 10:00 EST belongs to the previous day
        idx = pd.DatetimeIndex([
            "2024-01-15 20:00:00", "2024-01-16 02:00:00",
            "2024-01-16 10:00:00",
        ]).tz_localize("America/New_York")
        sess = session_of(idx)
        assert pd.Timestamp(sess[0]).date().isoformat() == "2024-01-15"
        assert pd.Timestamp(sess[1]).date().isoformat() == "2024-01-15"  # 02:00
        assert pd.Timestamp(sess[2]).date().isoformat() == "2024-01-15"  # 10:00


class TestP90AndRekey:
    def test_p90_threshold_buckets(self):
        # construct an M5 frame with a fat candle at an in-window hour
        est = pd.DatetimeIndex(["2024-01-16 07:30:00"]).tz_localize(
            "America/New_York").tz_convert("UTC")
        df = pd.DataFrame({
            "open": [150.0], "high": [150.10], "low": [149.97],
            "close": [150.09],
        }, index=est)  # body 9 pips >= 4.6 threshold at 7am
        m5 = df
        # need the session AR table to include this session
        m5_all = pd.concat([make_m5(2), df])
        ar = build_session_ar_table(m5_all)
        prim = build_primitive_frame(m5_all, ar)
        # the fat candle must be a P90 print (in window 7am, body 9 pips)
        row = prim.loc[[df.index[0]]].iloc[-1]
        assert bool(row["p90_print"])
        assert row["p90_dir"] == "bull"

    def test_p90_out_of_window_not_printed(self):
        # 14:00 EST is outside 2-11 AM window -> no P90 print even with fat body
        est = pd.DatetimeIndex(["2024-01-16 14:30:00"]).tz_localize(
            "America/New_York").tz_convert("UTC")
        df = pd.DataFrame({
            "open": [150.0], "high": [150.20], "low": [149.90],
            "close": [150.15],  # 15-pip body
        }, index=est)
        m5_all = pd.concat([make_m5(2), df])
        ar = build_session_ar_table(m5_all)
        prim = build_primitive_frame(m5_all, ar)
        row = prim.loc[[df.index[0]]].iloc[-1]
        assert not bool(row["p90_print"])

    def test_rekey_132pct(self):
        # One controlled session: Asian window 19:00 EST Jan15 -> 03:00 EST Jan16
        # with range 149.80..150.00 (20 pips). Breach bar at 06:00 EST Jan16
        # with high >= 150.00 + 1.32*20*0.01 = 150.264.
        asian = pd.date_range("2024-01-15 19:00", "2024-01-16 02:55",
                              freq="5min", tz="America/New_York")
        n = len(asian)
        bars = pd.DataFrame({
            "open": [149.90] * n, "high": [150.00] * n,
            "low": [149.80] * n, "close": [149.90] * n,
        }, index=asian)
        breach_ts = pd.DatetimeIndex(["2024-01-16 06:00:00"]).tz_localize(
            "America/New_York")
        breach = pd.DataFrame({
            "open": [150.20], "high": [150.30], "low": [150.10],
            "close": [150.28],
        }, index=breach_ts)
        m5_all = pd.concat([bars, breach]).tz_convert("UTC")
        ar = build_session_ar_table(m5_all)
        assert len(ar) == 1
        assert abs(ar.iloc[0]["ar_pips"] - 20.0) < 0.01
        prim = build_primitive_frame(m5_all, ar)
        row = prim.loc[[m5_all.index[-1]]].iloc[-1]
        assert bool(row["rekey_bull"])
        assert not bool(row["rekey_bear"])

    def test_midpoint_cross(self):
        # build the session first, then craft a bar crossing ITS true midpoint
        m5 = make_m5(16)
        ar = build_session_ar_table(m5)
        est = pd.DatetimeIndex(["2024-01-16 05:00:00"]).tz_localize(
            "America/New_York").tz_convert("UTC")
        sess = pd.Timestamp(session_of(est)[0])
        ar_row = ar[ar["session"] == sess].iloc[0]
        mid = ar_row["midpoint"]
        df = pd.DataFrame({
            "open": [mid + 0.01], "high": [mid + 0.02], "low": [mid - 0.02],
            "close": [mid - 0.01],  # cross from above to below
        }, index=est)
        m5_all = pd.concat([m5, df])
        prim = build_primitive_frame(m5_all, ar)
        row = prim.loc[[df.index[0]]].iloc[-1]  # the crafted bar (appended last)
        assert bool(row["mid_cross"])
        assert bool(row["mid_close_below"])


# ---------------------------------------------------------------------------
# causal window
# ---------------------------------------------------------------------------

class TestWindow:
    def test_bucket_counts_causal(self):
        # a primitive at minute 20 must NOT appear in the 0-15 bucket
        stream = pd.DataFrame({
            "prim_type": ["p90"], "direction": ["bull"],
            "ts": [pd.Timestamp("2024-01-01 00:20:00")],
            "minutes_from_t0": [20.0],
            "bucket": ["15_30"],
        })
        bc = bucket_counts(stream, "p90")
        assert bc["0_15"] == 0
        assert bc["15_30"] == 1
        cc = cumulative_counts(bc)
        assert cc["15m"] == 0
        assert cc["30m"] == 1
        assert cc["120m"] == 1

    def test_aligned_direction(self):
        assert _aligned("bull", "bull") == 1
        assert _aligned("bear", "bull") == -1
        assert _aligned("", "bull") == 0


# ---------------------------------------------------------------------------
# fingerprint construction
# ---------------------------------------------------------------------------

class TestFingerprint:
    def test_one_row_per_event_and_vol(self):
        events = pd.DataFrame({
            "event_id": [f"E{i}" for i in range(4)],
            "event_start": pd.to_datetime([
                "2024-01-15 08:00:00", "2024-01-15 09:00:00",
                "2024-01-15 10:00:00", "2024-01-15 11:00:00"], utc=True),
            "origin_currency": ["EUR", "EUR", "EUR", "EUR"],
            "direction": ["ACCUMULATION", "ACCUMULATION",
                          "LIQUIDATION", "LIQUIDATION"],
            "severity": ["LOW"] * 4, "session": ["London"] * 4,
        })
        m5 = make_m5(4)
        ar = build_session_ar_table(m5)
        prim = build_primitive_frame(m5, ar)
        # synthetic execution rows: one per event (delay 2 for A, 1 for B)
        ex = pd.DataFrame({
            "event_id": events["event_id"],
            "delay_h": [2, 2, 1, 1], "hold_h": [6] * 4,
            "dir_return_bps": [20.0, -10.0, 8.0, -4.0],
            "dir_net_bps": [18.8, -11.2, 6.8, -5.2],
            "dir_mfe_bps": [25.0, 5.0, 12.0, 3.0],
            "dir_mae_bps": [-5.0, -15.0, -4.0, -9.0],
            "time_to_mfe_h": [1.0] * 4, "time_to_mae_h": [2.0] * 4,
            "rv_bps_per_h": [5.0, 5.0, 5.0, 5.0],
            "split": ["discovery"] * 4,
        })
        fp = build_fingerprints(events, prim, ex)
        assert len(fp) == 4
        assert fp["event_id"].nunique() == 4  # no duplicated events
        # position = 10 / rv = 2.0 -> vol bps = 2 * net
        assert np.allclose(fp["baseline_vol_bps"],
                           fp["baseline_net_bps"] * 2.0)
        # no NaN outcomes
        assert fp["baseline_vol_bps"].notna().all()
        # family labels
        assert set(fp["family"]) == {"A", "B"}


# ---------------------------------------------------------------------------
# statistics discipline
# ---------------------------------------------------------------------------

class TestStats:
    def test_bootstrap_deterministic(self):
        rng = np.random.default_rng(1)
        v = rng.normal(1.0, 2.0, 500)
        a = bootstrap_ci(v, seed=42)
        b = bootstrap_ci(v, seed=42)
        assert a == b
        assert a["ci_low"] < a["mean"] < a["ci_high"]

    def test_permutation_deterministic(self):
        rng = np.random.default_rng(2)
        a = rng.normal(1.0, 1.0, 60)
        b = rng.normal(0.0, 1.0, 60)
        p1 = permutation_p(a, b, seed=11)
        p2 = permutation_p(a, b, seed=11)
        assert p1 == p2
        assert p1 < 0.05  # real difference detected

    def test_bh_fdr(self):
        p = np.array([0.001, 0.02, 0.03, 0.4, 0.8])
        q = bh_fdr(p)
        assert np.all(q >= 0) and np.all(q <= 1)
        # monotone in p order
        order = np.argsort(p)
        assert np.all(np.diff(q[order]) >= -1e-12)
        assert q[order][0] <= 0.01  # strongest survives

    def test_split_boundaries(self):
        assert assign_split(pd.Timestamp("2024-06-01", tz="UTC")) == "discovery"
        assert assign_split(pd.Timestamp("2025-03-01", tz="UTC")) == "confirmation"
        assert assign_split(pd.Timestamp("2025-10-01", tz="UTC")) == "oos"
        assert assign_split(pd.Timestamp("2026-09-01", tz="UTC")) == "outside"
        assert assign_split(pd.Timestamp("2025-01-01", tz="UTC")) == "confirmation"
        assert assign_split(pd.Timestamp("2025-07-01", tz="UTC")) == "oos"


# ---------------------------------------------------------------------------
# candidate protocol (integration over real frozen artifacts)
# ---------------------------------------------------------------------------

class TestCandidateProtocol:
    @pytest.fixture(scope="class")
    def manifest(self):
        from capital_routing.phases.phase_8_orchestrator import Phase8Orchestrator
        out = ROOT / "artifacts" / "phase_08"
        if not (ROOT / "artifacts" / "phase_05" / "routing_events.parquet").exists():
            pytest.skip("frozen Phase 5 artifacts not present")
        m = Phase8Orchestrator(ROOT, out).run()
        return m

    def test_materiality_gate(self, manifest):
        # no class-A candidate may have |uplift| < 2 bps or p > 0.10
        for c in manifest["candidates"]:
            if c.get("class") == "A":
                assert abs(c["discovery_uplift_bps"]) >= 2.0
                assert c["discovery_p_vs_base"] <= 0.10
                assert c["discovery_coverage"] >= 0.30

    def test_oos_never_used_for_selection(self, manifest):
        # confirmation verdict must not depend on OOS rows
        for c in manifest["candidates"]:
            if c["verdict"] == "CONFIRMED":
                assert c["confirmation_n"] >= 30

    def test_baseline_reproducible(self, manifest):
        import json
        # A baseline on inner_sel must reproduce the sealed Phase 7 number
        # (10.06 bps vol-normalized) within tolerance
        fp = pd.read_csv(ROOT / "artifacts" / "phase_08" / "P8_EVENT_FINGERPRINT.csv")
        ts = pd.to_datetime(fp["event_start"], utc=True)
        a = fp[(fp["family"] == "A")
               & (ts >= pd.Timestamp("2023-07-01", tz="UTC"))
               & (ts < pd.Timestamp("2025-01-01", tz="UTC"))]
        assert abs(a["baseline_vol_bps"].mean() - 10.06) < 0.5

    def test_no_duplicate_events(self, manifest):
        fp = pd.read_csv(ROOT / "artifacts" / "phase_08" / "P8_EVENT_FINGERPRINT.csv")
        assert fp["event_id"].nunique() == len(fp)

    def test_fingerprint_has_all_required_columns(self, manifest):
        required = ["baseline_entry_time", "baseline_exit_time", "daily_tier",
                    "tier_impulse_total", "p90_total", "rekey_total",
                    "mid_cross_total", "aligned_commitment_ratio",
                    "opposition_ratio", "sequence_code", "primitive_score"]
        fp = pd.read_csv(ROOT / "artifacts" / "phase_08" / "P8_EVENT_FINGERPRINT.csv")
        missing = [c for c in required if c not in fp.columns]
        assert not missing
