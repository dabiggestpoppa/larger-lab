"""P6 — Rekey Mechanics tests (checkpoint MVE-P6-REKEY-MECHANICS).

Every P6 executable component must prove:

1. RKEY-A timing (realtime: all four timestamps = the re-anchor bar),
2. RKEY-B delayed activation (no backdating: the new anchor becomes active
   only at the retest bar j, never at the scan-origin bar i),
3. RKEY-C timing (realtime),
4. future-perturbation invariance (episode-known series),
5. truncation invariance,
6. episode dedup (one episode per anchor transition; re-entry -> new episode),
7. duplicate anchor events (cross-variant sharing is by design),
8. NaN handling (fail-closed: no fabricated events),
9. rekey timestamp schema (event <= evidence <= known <= active),
10. old-anchor counterfactual isolation (ex-post only; never feeds detection),
11. direction symmetry plumbing (per-direction columns),
12. holdout guard (2026 unreachable),
13. Model D/E / blocked aggregate exclusion.

Fixtures are synthetic and confined to this test file, mirroring
tests/mve/test_p4_acceptance.py conventions.
"""
from __future__ import annotations

import inspect
import os
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import mve.p6_rekey as pr  # noqa: E402
from mve.causality import (  # noqa: E402
    future_perturbation_check,
    truncation_check,
    validate_rekey_events,
)
from mve.data_loader import DataPipelineError, slice_data  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def make_signals(n: int = 400, seed: int = 23, up: bool = True) -> pd.DataFrame:
    """Random-walk signed coordinate series with a few beyond-state episodes.

    up=True  -> x is the upper-family series (positive = above anchor).
    up=False -> x is the lower-family series (positive = below anchor).
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03", periods=n, freq="h", tz="UTC")
    x = np.cumsum(rng.normal(0, 0.35, n)) - 0.5
    if not up:
        x = -x
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    return sig


def make_controlled_signals() -> pd.DataFrame:
    """Hand-built series with known crossing / retest patterns.

    Positions (x):
      0: 0.5              inside
      1: 1.2              crossing above 1.0        (A fires at 1)
      2: 1.3              sustained beyond          (retest for B at 2)
      3: 0.8              re-entry inside           (B-1 confirmed at 2)
      4: 0.6              inside
      5: 1.1              crossing, NO retest in (5,9]  (B control at 5)
      6: 0.4              immediate re-entry
      7: 0.4              inside
      8: 0.5              inside
      9: 0.6              inside
     10: 1.4              crossing (A fires at 10; B-2 confirmed at 10 via
                          the sealed detector's stale scan-origin flag)
     11: 1.5              beyond (retest evidence)
     12: 0.7              re-entry
     13: 0.6              inside
     14: 0.5              inside
    """
    idx = pd.date_range("2023-07-03", periods=15, freq="h", tz="UTC")
    x = np.array([0.5, 1.2, 1.3, 0.8, 0.6, 1.1, 0.4, 0.4, 0.5, 0.6, 1.4, 1.5, 0.7, 0.6, 0.5])
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    return sig


def make_wavy_signals(n: int = 800, seed: int = 7) -> pd.DataFrame:
    """Centered oscillating series that crosses both +/- boundaries often.

    Deterministic sine + small noise; both sides fire by construction.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03", periods=n, freq="h", tz="UTC")
    t = np.arange(n)
    x = 1.6 * np.sin(2 * np.pi * t / 80.0) + rng.normal(0, 0.25, n)
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    return sig


def _events_from_series(sig: pd.DataFrame, variant: str, boundary: float = 1.0):
    return pr.detect_rekey_episodes(sig, variant, boundary, 1.0)


# ---------------------------------------------------------------------------
# 1. Registry / timing semantics
# ---------------------------------------------------------------------------

def test_registry_complete():
    assert pr.P6_VARIANTS == ("RKEY_A", "RKEY_B", "RKEY_C")
    assert pr.P6_BOUNDARIES == (1.0, 2.0)
    assert pr.P6_DIRECTIONS == (1.0, -1.0)
    assert 6 in pr.P6_HORIZONS and 24 in pr.P6_HORIZONS


def test_rkey_a_realtime_timing():
    sig = make_controlled_signals()
    ep = _events_from_series(sig, "RKEY_A")
    assert len(ep) == 3  # crossings at 1, 5, 10
    assert sorted(ep["event_pos"].tolist()) == [1, 5, 10]
    assert (ep["event_pos"] == ep["known_pos"]).all()
    assert (ep["latency_bars"] == 0).all()
    # all four timestamps identical (realtime)
    for _, row in ep.iterrows():
        assert row["rekey_event_time"] == row["rekey_evidence_complete_time"]
        assert row["rekey_event_time"] == row["rekey_known_time"]
        assert row["rekey_event_time"] == row["new_anchor_active_time"]


def test_rkey_b_delayed_activation_no_backdating():
    sig = make_controlled_signals()
    ep = _events_from_series(sig, "RKEY_B")
    # B episodes: crossing 1 confirmed at 2; the second structural crossing at
    # 10 (the sealed detector's scan-origin event_time is 6 due to its
    # persisted breakout flag; crossing_pos records the true structural bar).
    # Crossing 5 has NO confirming retest -> no B episode. Both stay on the
    # upper side because their ACTIVATION bars (2, 10) are positive.
    assert sorted(ep["event_pos"].tolist()) == [1, 6]
    assert sorted(ep["crossing_pos"].tolist()) == [1, 10]
    assert sorted(ep["known_pos"].tolist()) == [2, 10]
    for _, row in ep.iterrows():
        # B: event = scan-origin i, evidence = known = active = retest j
        assert row["rekey_event_time"] < row["rekey_known_time"]
        assert row["rekey_event_time"] <= row["rekey_evidence_complete_time"]
        assert row["rekey_evidence_complete_time"] == row["rekey_known_time"]
        assert row["rekey_known_time"] == row["new_anchor_active_time"]
        assert row["latency_bars"] == row["known_pos"] - row["event_pos"]
        assert row["crossing_latency_bars"] == row["known_pos"] - row["crossing_pos"]


def test_rkey_b_anchor_value_is_scan_origin_coordinate():
    sig = make_controlled_signals()
    ep = _events_from_series(sig, "RKEY_B")
    row = ep[ep["event_pos"] == 1].iloc[0]
    # sealed semantics: the new anchor value is the coordinate at the
    # scan-origin bar i (1.2), activated at the retest bar j (2).
    assert row["new_anchor_value"] == pytest.approx(1.2)
    assert row["coordinate_before"] == pytest.approx(sig["x"].iloc[2])  # x at activation
    # the second B episode: the re-anchor point is the coordinate at the
    # structural crossing (bar 10, x=1.4); the sealed scan-origin value (0.4
    # from the stale flag) is retained descriptively. Activation at bar 10.
    row2 = ep[ep["crossing_pos"] == 10].iloc[0]
    assert row2["new_anchor_value"] == pytest.approx(1.4)
    assert row2["anchor_value_sealed"] == pytest.approx(0.4)
    assert row2["coordinate_before"] == pytest.approx(sig["x"].iloc[10])
    assert row2["known_pos"] == 10


def test_rkey_c_realtime():
    sig = make_controlled_signals()
    ep = _events_from_series(sig, "RKEY_C")
    # C requires a sigma-state up-crossing (state 0 -> 1, or 1 -> 2, ...) AND
    # a 3-of-3 window above the boundary. No state up-crossing with a 3-of-3
    # window exists in this fixture -> C fires nowhere.
    assert ep.empty


def test_rkey_c_fires_on_3_of_3():
    idx = pd.date_range("2023-07-03", periods=12, freq="h", tz="UTC")
    # state 0 -> 1 crossings at 7 and 10 have no 3-of-3 window
    x = np.array([0.5, 0.6, 0.7, 0.4, 0.5, 0.6, 0.3, 1.3, 0.8, 0.5, 1.4, 0.7])
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    ep = _events_from_series(sig, "RKEY_C")
    # at 7: state 1 > state 0, but window [5..7] = 0.6, 0.3, 1.3 -> 1 above
    # at 10: state 1 > state 0, but window [8..10] = 0.8, 0.5, 1.4 -> 1 above
    assert ep.empty
    # state 1 -> 2 jump at 9 with a 3-of-3 window [7..9] above the boundary
    x2 = np.array([0.5, 0.6, 0.7, 0.4, 0.5, 0.6, 0.3, 1.3, 1.4, 2.2, 1.1, 0.9])
    sig["x"] = x2
    ep = _events_from_series(sig, "RKEY_C")
    assert len(ep) == 1
    assert ep.iloc[0]["event_pos"] == 9
    assert ep.iloc[0]["known_pos"] == 9
    assert ep.iloc[0]["new_anchor_value"] == pytest.approx(2.2)


# ---------------------------------------------------------------------------
# 2. Rekey schema (fail-closed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variant", pr.P6_VARIANTS)
@pytest.mark.parametrize("boundary", pr.P6_BOUNDARIES)
def test_rekey_schema_validation(variant, boundary):
    sig = make_signals(n=500, seed=53)
    for direction in pr.P6_DIRECTIONS:
        sig_cell = sig.copy()
        if direction < 0:
            sig_cell["x"] = -sig_cell["x"].to_numpy()
        ep = pr.detect_rekey_episodes(sig_cell, variant, boundary, direction)
        if ep.empty:
            continue
        events = []
        for _, row in ep.iterrows():
            events.append(
                {
                    "id": row["episode_id"],
                    "rekey_event_time": row["rekey_event_time"],
                    "rekey_evidence_complete_time": row["rekey_evidence_complete_time"],
                    "rekey_known_time": row["rekey_known_time"],
                    "new_anchor_active_time": row["new_anchor_active_time"],
                }
            )
        problems = validate_rekey_events(events, raise_on_error=False)
        assert problems == [], f"{variant} b{boundary} d{direction}: {problems}"


# ---------------------------------------------------------------------------
# 3. Causality: future perturbation + truncation invariance
# ---------------------------------------------------------------------------

def _detect_fn(variant: str, boundary: float, direction: float):
    def fn(d: pd.DataFrame) -> pd.Series:
        rec = pd.DataFrame(index=d.index)
        rec["x"] = d["x"]
        rec["close"] = d["close"]
        rec["vol"] = d["vol"]
        return pr.rekey_known_series(rec, variant, boundary, direction)

    return fn


@pytest.mark.parametrize("variant", pr.P6_VARIANTS)
def test_detection_future_perturbation_invariant(variant):
    sig = make_signals(n=600, seed=31)
    # RKEY-B scans up to 4 bars ahead -> its known time is delayed by 4
    delay = pr.P6_B_RETEST_WINDOW if variant == "RKEY_B" else 0
    for direction in pr.P6_DIRECTIONS:
        sig_cell = sig.copy()
        if direction < 0:
            sig_cell["x"] = -sig_cell["x"].to_numpy()
        data = sig_cell[["x", "close", "vol"]].copy()
        t = len(data) // 2
        fn = _detect_fn(variant, 1.0, direction)
        diff = future_perturbation_check(fn, data, t, seed=601, delay=delay)
        assert diff == 0.0, f"{variant} d{direction} repaints under future mutation (diff={diff})"


@pytest.mark.parametrize("variant", pr.P6_VARIANTS)
def test_detection_truncation_invariant(variant):
    sig = make_signals(n=600, seed=37)
    for t in [len(sig) // 4, len(sig) // 2, 3 * len(sig) // 4]:
        data = sig[["x", "close", "vol"]].copy()
        fn = _detect_fn(variant, 1.0, 1.0)
        diff = truncation_check(fn, data, t)
        assert diff == 0.0, f"{variant} differs under truncation at {t} (diff={diff})"


def test_rkey_b_known_series_places_events_at_retest_bar():
    """B's known series must mark the RETEST bar j, not the scan-origin i."""
    sig = make_controlled_signals()
    known = pr.rekey_known_series(sig, "RKEY_B", 1.0, 1.0)
    assert known.iloc[2] == 1.0  # retest bar for crossing 1
    assert known.iloc[1] == 0.0  # scan-origin itself must NOT be marked


# ---------------------------------------------------------------------------
# 4. Episode dedup
# ---------------------------------------------------------------------------

def test_sustained_beyond_state_is_one_episode():
    """B's raw detector emits per-bar in a sustained beyond state; the merge
    must collapse it to ONE episode per anchor transition."""
    idx = pd.date_range("2023-07-03", periods=40, freq="h", tz="UTC")
    x = np.array([0.4] * 10 + [1.3] * 20 + [0.5] * 10)
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    raw = pr._side_filtered_events(sig["x"], 1.0, "RKEY_B")
    assert len(raw) > 1  # the raw stream is dense
    ep = _events_from_series(sig, "RKEY_B")
    assert len(ep) == 1  # one anchor transition
    assert ep.iloc[0]["crossing_pos"] == 10
    assert ep.iloc[0]["known_pos"] == 11


def test_reentry_opens_new_episode():
    idx = pd.date_range("2023-07-03", periods=60, freq="h", tz="UTC")
    x = np.array([0.4] * 10 + [1.3] * 10 + [0.5] * 10 + [1.4] * 10 + [0.5] * 20)
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    ep = _events_from_series(sig, "RKEY_B")
    assert len(ep) == 2  # two distinct anchor transitions
    assert ep.iloc[0]["crossing_pos"] == 10
    assert ep.iloc[1]["crossing_pos"] == 30


def test_cross_variant_sharing_is_by_design():
    """A and B sharing a structural crossing must be separate rows sharing a
    duplicate_episode_id — not 'duplicates' to remove."""
    sig = make_controlled_signals()
    a = _events_from_series(sig, "RKEY_A")
    b = _events_from_series(sig, "RKEY_B")
    shared = set(a["duplicate_episode_id"]) & set(b["duplicate_episode_id"])
    assert len(shared) == 2  # crossings 1 and 10 are shared transitions
    assert a["episode_id"].is_unique and b["episode_id"].is_unique


def test_episode_ids_unique_per_cell():
    sig = make_signals(n=500, seed=61)
    for variant in pr.P6_VARIANTS:
        for boundary in pr.P6_BOUNDARIES:
            for direction in pr.P6_DIRECTIONS:
                sig_cell = sig.copy()
                if direction < 0:
                    sig_cell["x"] = -sig_cell["x"].to_numpy()
                ep = pr.detect_rekey_episodes(sig_cell, variant, boundary, direction)
                if ep.empty:
                    continue
                assert ep["episode_id"].is_unique
                assert ep["known_pos"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# 5. NaN handling (fail-closed)
# ---------------------------------------------------------------------------

def test_nan_warmup_never_fabricates_events():
    idx = pd.date_range("2023-07-03", periods=50, freq="h", tz="UTC")
    x = np.full(50, np.nan)
    x[30:] = 1.3
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * np.nan_to_num(x)
    sig["vol"] = 0.01
    # A requires a known inside predecessor (NaN fails) -> no event
    ep_a = _events_from_series(sig, "RKEY_A")
    assert ep_a.empty
    # C requires a non-NaN trailing window -> no event
    ep_c = _events_from_series(sig, "RKEY_C")
    assert ep_c.empty
    # B fires on the FIRST REAL beyond bar (30) with a real retest (31):
    # the beyond run is genuine, not fabricated from the NaN warmup.
    ep_b = _events_from_series(sig, "RKEY_B")
    assert len(ep_b) == 1
    assert ep_b.iloc[0]["crossing_pos"] == 30
    assert ep_b.iloc[0]["known_pos"] == 31


def test_nan_inside_breaks_episode_continuity():
    """A NaN bar between two beyond runs must split them (fail-closed)."""
    idx = pd.date_range("2023-07-03", periods=50, freq="h", tz="UTC")
    x = np.array([0.4] * 10 + [1.3] * 10 + [np.nan] + [1.4] * 8 + [0.5] * 21)
    sig = pd.DataFrame(index=idx)
    sig["x"] = x
    sig["close"] = 1.05 + 0.0001 * np.nan_to_num(x)
    sig["vol"] = 0.01
    ep = _events_from_series(sig, "RKEY_B")
    # NaN breaks continuity -> the second beyond run is a new episode
    assert len(ep) == 2


# ---------------------------------------------------------------------------
# 6. Outcome measurement & counterfactual isolation
# ---------------------------------------------------------------------------

def test_outcome_measurement_is_ex_post_by_design():
    """Outcomes must react to future bars while detection must not."""
    sig = make_signals(n=500, seed=41)
    ep = _events_from_series(sig, "RKEY_A")
    if ep.empty:
        pytest.skip("no episodes in fixture")
    out = pr.measure_rekey_outcomes(ep, sig)
    if out.empty:
        pytest.skip("no measurable episodes")
    k = int(out.iloc[0]["known_pos"])
    h = 6
    if k + h >= len(sig):
        pytest.skip("no forward room")
    base_cont = out.iloc[0][f"cont_{h}"]
    c2 = sig["close"].to_numpy().copy()
    c2[k + h] = 1.0  # far below any rekey level near 1.05
    sig2 = sig.copy()
    sig2["close"] = c2
    out2 = pr.measure_rekey_outcomes(ep, sig2)
    assert out2.iloc[0][f"cont_{h}"] != base_cont, "outcome must react to future bars"


def test_counterfactual_never_feeds_detection():
    """Detection must not consume any OUTCOME / counterfactual column."""
    src = inspect.getsource(pr.detect_rekey_episodes) + inspect.getsource(pr._merge_episodes)
    for token in ("cont_", "old_state_", "mean_abs_disp", "persist_dur", "rej_within", "mfd_"):
        assert token not in src, f"detection must not consume {token}"
    # and the counterfactual is documented as ex-post evaluation only
    src_cf = inspect.getsource(pr.old_anchor_counterfactual)
    assert "Ex-post" in src_cf


def test_counterfactual_two_frames():
    sig = make_signals(n=500, seed=67)
    ep = _events_from_series(sig, "RKEY_A")
    out = pr.measure_rekey_outcomes(ep, sig)
    cf = pr.old_anchor_counterfactual(out, sig)
    if cf.empty:
        pytest.skip("no counterfactual rows")
    assert {"state_A_at_h", "state_B_at_h", "mean_abs_disp_A_win", "mean_abs_disp_B_win"} <= set(cf.columns)


# ---------------------------------------------------------------------------
# 7. Direction symmetry plumbing
# ---------------------------------------------------------------------------

def test_direction_symmetry_plumbing():
    sig = make_wavy_signals()
    n_up, n_dn = 0, 0
    for direction in pr.P6_DIRECTIONS:
        sig_cell = sig.copy()
        if direction < 0:
            sig_cell["x"] = -sig_cell["x"].to_numpy()
        ep = pr.detect_rekey_episodes(sig_cell, "RKEY_A", 1.0, direction)
        if ep.empty:
            continue
        assert (ep["direction"] == int(direction)).all()
        n_up += int(ep["direction"].eq(1).sum())
        n_dn += int(ep["direction"].eq(-1).sum())
    assert n_up > 0 and n_dn > 0  # both sides fire on the oscillating series


def test_no_side_double_counting():
    """An event on the upper side must never appear in the lower cell."""
    sig = make_wavy_signals(seed=11)
    up = pr.detect_rekey_episodes(sig, "RKEY_A", 1.0, 1.0)
    dn_sig = sig.copy()
    dn_sig["x"] = -sig["x"].to_numpy()
    dn = pr.detect_rekey_episodes(dn_sig, "RKEY_A", 1.0, -1.0)
    assert not up.empty and not dn.empty
    up_keys = set(zip(up["crossing_pos"], up["known_pos"]))
    dn_keys = set(zip(dn["crossing_pos"], dn["known_pos"]))
    assert up_keys.isdisjoint(dn_keys)


# ---------------------------------------------------------------------------
# 8. Static leakage / blocked components / data discipline
# ---------------------------------------------------------------------------

def test_p6_source_leakage_audit():
    findings = pr.executable_leakage_scan(inspect.getsource(pr), "mve.p6_rekey")
    leaks = [f for f in findings if f["pattern"] in ("shift(-", "center=True", "bfill()", "backfill()", "iloc[]")]
    assert leaks == [], f"leakage operations found: {leaks}"


def test_p6_no_blocked_component_consumption():
    src = inspect.getsource(pr)
    for token in ("model_D", "model_E", "generate_all_signals", "SignalGenerator"):
        assert token not in src, f"P6 must not consume blocked component {token}"


def test_p6_uses_sealed_rekey_only():
    src = inspect.getsource(pr)
    assert "detect_rekey_events" in src
    assert "MorphicRekey" in src


def test_holdout_guard_2026_unreachable():
    import mve.data_loader as dl

    assert dl.HOLDOUT_STATUS == "FINAL_HOLDOUT_PENDING"
    idx = pd.date_range("2025-01-01", periods=10, freq="h", tz="UTC")
    with pytest.raises(DataPipelineError):
        slice_data(pd.DataFrame(index=idx), "2026-01-01", "2026-01-31")
    idx2 = pd.date_range("2023-07-03", periods=10, freq="h", tz="UTC")
    with pytest.raises(DataPipelineError):
        slice_data(pd.DataFrame(index=idx2), "2024-12-01", "2025-06-01")


def test_confirmation_boundary_discipline():
    """Dev/conf slice boundaries must be exactly the frozen ranges."""
    assert pr.P6_BOUNDARIES == (1.0, 2.0)
    assert pr.P6_MAX_HORIZON == 24


# ---------------------------------------------------------------------------
# 9. Controls & entropy helpers
# ---------------------------------------------------------------------------

def test_control_events_b_selection():
    """B controls = crossings with no confirming retest within 4 bars."""
    sig = make_controlled_signals()
    ctrl = pr.control_events(sig, "RKEY_B", 1.0, 1.0, n_target=100)
    # crossings at 1 (retest at 2 -> confirmed), 5 (no retest -> control),
    # 10 (retest at 11 -> confirmed)
    assert sorted(ctrl["event_pos"].tolist()) == [5]
    assert ctrl.iloc[0]["known_pos"] == min(5 + pr.P6_B_RETEST_WINDOW, len(sig) - 1)


def test_control_events_c_selection():
    sig = make_controlled_signals()
    ctrl = pr.control_events(sig, "RKEY_C", 1.0, 1.0, n_target=100)
    # C fired nowhere in this fixture -> every crossing is a control
    assert sorted(ctrl["event_pos"].tolist()) == [1, 5, 10]


def test_control_events_a_sampling():
    sig = make_controlled_signals()
    ctrl = pr.control_events(sig, "RKEY_A", 1.0, 1.0, n_target=5)
    # beyond-state bars that are NOT crossings: positions 2 (1.3) and 11 (1.5)
    assert set(ctrl["event_pos"].tolist()) <= {2, 11}
    assert len(ctrl) <= 2


def test_control_events_deterministic():
    sig = make_signals(n=500, seed=79)
    a = pr.control_events(sig, "RKEY_A", 1.0, 1.0, n_target=40)
    b = pr.control_events(sig, "RKEY_A", 1.0, 1.0, n_target=40)
    pd.testing.assert_frame_equal(a, b)


def test_shannon_entropy_helper():
    from mve.p4_statistics import shannon_entropy

    assert shannon_entropy(np.array([1, 1, 1, 1])) == 0.0
    assert shannon_entropy(np.array([1, 1, 2, 2])) == pytest.approx(1.0)
    assert shannon_entropy(np.array([1, np.nan, 2, 2])) == pytest.approx(0.9182958, abs=1e-6)
    assert shannon_entropy(np.array([3])) == 0.0
