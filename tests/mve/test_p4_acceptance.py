"""P4 — Causal Acceptance Engine tests (checkpoint MVE-P4-CAUSAL-ACCEPTANCE-ENGINE).

Every P4 executable component must prove:

1. future-perturbation invariance (event detection),
2. truncation invariance (event detection),
3. acceptance timestamp schema (state <= evidence <= known),
4. blocked-component isolation (no Model D/E consumption),
5. static-leakage audit (no shift(-1)/centered/backfill in executable code),
6. causal -> ex-post separation (outcome measurement is deliberately ex-post
   and never feeds back into detection).

Fixtures are synthetic and confined to this test file (never the research
path), mirroring tests/mve/test_causality.py conventions.
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

import mve.p4_acceptance as pa  # noqa: E402
import mve.p4_statistics as ps  # noqa: E402
from mve.causality import (  # noqa: E402
    future_perturbation_check,
    truncation_check,
    validate_acceptance_events,
)
from mve.data_loader import DataPipelineError, slice_data  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def make_signals(n: int = 400, seed: int = 23, boundary: float = 1.0) -> pd.DataFrame:
    """Random-walk coordinate signals with intrabar extreme overshoot.

    Adds close/vol so outcome measurement (fixed boundary price level) works.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03", periods=n, freq="h", tz="UTC")
    x = np.cumsum(rng.normal(0, 0.35, n)) - 0.5
    fields = pd.DataFrame(index=idx)
    fields["x_close_up"] = x
    fields["x_extreme_up"] = x + 0.25
    fields["x_close_lo"] = -x
    fields["x_extreme_lo"] = -(x - 0.25)
    sig = pa.per_boundary_signals(fields, boundary, 1.0)
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    return sig


def make_controlled_signals() -> pd.DataFrame:
    """Hand-built series with known touch/close-beyond patterns.

    Positions:
      0: x=0.5  x_ext=0.9                 (no touch)
      1: x=1.2  x_ext=1.4  -> touch, close beyond     (A0/A1 accepted)
      2: x=0.8  x_ext=1.1  -> touch, close inside     (A0 accepted, A1 rejected)
      3: x=0.3  x_ext=0.5
      4: x=1.1  x_ext=1.2  -> touch, close beyond
      5: x=1.3  x_ext=1.5  -> touch, close beyond
      6: x=0.7  x_ext=0.9
      7: x=1.2  x_ext=1.3  -> touch, close beyond
      8: x=0.6  x_ext=0.8
      9: x=0.4  x_ext=0.7
    """
    idx = pd.date_range("2023-07-03", periods=10, freq="h", tz="UTC")
    x = np.array([0.5, 1.2, 0.8, 0.3, 1.1, 1.3, 0.7, 1.2, 0.6, 0.4])
    x_ext = np.array([0.9, 1.4, 1.1, 0.5, 1.2, 1.5, 0.9, 1.3, 0.8, 0.7])
    fields = pd.DataFrame(index=idx)
    fields["x_close_up"] = x
    fields["x_extreme_up"] = x_ext
    fields["x_close_lo"] = -x
    fields["x_extreme_lo"] = -x_ext
    sig = pa.per_boundary_signals(fields, 1.0, 1.0)
    sig["close"] = 1.05 + 0.0001 * x
    sig["vol"] = 0.01
    return sig


# ---------------------------------------------------------------------------
# 1. Variant registry / semantics
# ---------------------------------------------------------------------------

def test_variant_registry_complete():
    assert pa.P4_VARIANTS[0] == "A0_TOUCH"
    assert pa.P4_VARIANTS[1] == "A1_CLOSE"
    assert set(pa.A2_GRID) == {"A2_2OF3", "A2_3OF4", "A2_3OF5"}
    assert set(pa.A3_GRID) == {"A3_PERS_2", "A3_PERS_3", "A3_PERS_4"}
    assert "A4_RETEST_HOLD" in pa.P4_VARIANTS


def test_a0_touch_semantics():
    sig = make_controlled_signals()
    ep = pa.detect_acceptance_episodes(sig, "A0_TOUCH", 1.0, 1.0)
    # every touch bar is an accepted A0 episode at its own bar
    touch_pos = np.where(sig["touch"].to_numpy())[0]
    assert sorted(ep["event_pos"].tolist()) == sorted(touch_pos.tolist())
    assert (ep["accepted"]).all()
    assert (ep["acceptance_pos"] == ep["event_pos"]).all()
    assert (ep["rejection_pos"] == -1).all()


def test_a1_close_semantics():
    sig = make_controlled_signals()
    ep = pa.detect_acceptance_episodes(sig, "A1_CLOSE", 1.0, 1.0)
    beyond = sig["beyond"].to_numpy()
    for _, row in ep.iterrows():
        t0 = row["event_pos"]
        if beyond[t0]:
            assert row["accepted"] and row["acceptance_pos"] == t0
        else:
            assert not row["accepted"] and row["resolution"] == "REJECTED"
            assert row["rejection_pos"] == t0


def test_a3_persistence_runs():
    """Persistence 2 accepts only on 2 consecutive beyond closes; a dip breaks."""
    sig = make_controlled_signals()
    ep = pa.detect_acceptance_episodes(sig, "A3_PERS_2", 1.0, 1.0)
    acc_pos = ep.loc[ep["accepted"], "acceptance_pos"].tolist()
    # positions 4,5 are consecutive beyond -> acceptance at 5
    assert 5 in acc_pos
    # the beyond run that starts at 1 breaks when bar 2 closes inside -> REJECTED
    rej = ep[ep["resolution"] == "REJECTED"]
    assert len(rej) >= 1
    assert rej.iloc[0]["rejection_pos"] == 2
    # a lone beyond close at 7 (run never reaches 2) is not accepted
    assert 7 not in acc_pos


def test_a4_retest_hold_requires_retest():
    """A break that holds without a retest must not be accepted by A4."""
    sig = make_controlled_signals()
    ep = pa.detect_acceptance_episodes(sig, "A4_RETEST_HOLD", 1.0, 1.0)
    accepted = ep[ep["accepted"]]
    assert len(accepted) == 1
    assert accepted.iloc[0]["acceptance_pos"] == 7
    rejected = ep[ep["resolution"] == "REJECTED"]
    assert len(rejected) == 1
    assert rejected.iloc[0]["rejection_pos"] == 3


def test_unknown_variant_rejected():
    sig = make_signals()
    with pytest.raises(ValueError):
        pa.detect_acceptance_episodes(sig, "A9_BOGUS", 1.0, 1.0)


# ---------------------------------------------------------------------------
# 2. Acceptance timestamp schema (fail-closed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variant", pa.P4_VARIANTS)
def test_acceptance_schema_validation(variant):
    sig = make_signals()
    ep = pa.detect_acceptance_episodes(sig, variant, 1.0, 1.0)
    if ep.empty:
        return
    events = []
    for _, row in ep.iterrows():
        events.append(
            {
                "id": row["episode_id"],
                "state_event_time": row["event_time"],
                "evidence_complete_time": row["evidence_complete_time"],
                "acceptance_known_time": row["acceptance_known_time"],
            }
        )
    problems = validate_acceptance_events(events, raise_on_error=False)
    assert problems == [], f"{variant}: {problems}"
    for ev in events:
        assert ev["state_event_time"] <= ev["evidence_complete_time"] <= ev["acceptance_known_time"]


# ---------------------------------------------------------------------------
# 3. Causality: future perturbation + truncation invariance of detection
# ---------------------------------------------------------------------------

def _detect_fn(variant: str, boundary: float = 1.0):
    def fn(d: pd.DataFrame) -> pd.Series:
        # Recompute signals from (possibly mutated) coordinates so the check is
        # meaningful: beyond/touch must be derived inside the component.
        rec = pd.DataFrame(index=d.index)
        rec["x"] = d["x"]
        rec["x_ext"] = d["x_ext"]
        rec["beyond"] = rec["x"] >= boundary
        rec["touch"] = rec["x_ext"] >= boundary
        return pa.acceptance_known_series(rec, variant, boundary, 1.0)

    return fn


@pytest.mark.parametrize("variant", pa.P4_VARIANTS)
def test_detection_future_perturbation_invariant(variant):
    sig = make_signals(n=500, seed=31)
    data = sig[["x", "x_ext"]].copy()
    t = len(data) // 2
    fn = _detect_fn(variant)
    diff = future_perturbation_check(fn, data, t, seed=601)
    assert diff == 0.0, f"{variant} repaints under future mutation (diff={diff})"


@pytest.mark.parametrize("variant", pa.P4_VARIANTS)
def test_detection_truncation_invariant(variant):
    sig = make_signals(n=500, seed=37)
    data = sig[["x", "x_ext"]].copy()
    for t in [len(data) // 4, len(data) // 2, 3 * len(data) // 4]:
        fn = _detect_fn(variant)
        diff = truncation_check(fn, data, t)
        assert diff == 0.0, f"{variant} differs under truncation at {t} (diff={diff})"


def test_outcome_measurement_is_ex_post_by_design():
    """Outcomes must react to future bars (that is the object of study) while
    detection must not. This test documents the causal -> ex-post separation."""
    sig = make_signals(n=500, seed=41)
    ep = pa.detect_acceptance_episodes(sig, "A1_CLOSE", 1.0, 1.0)
    out = pa.measure_outcomes(ep, sig)
    if out.empty:
        pytest.skip("no accepted episodes in fixture")
    k = int(out.iloc[0]["acceptance_pos"])
    h = 6
    if k + h >= len(sig):
        pytest.skip("no forward room")
    base_cont = out.iloc[0][f"cont_{h}"]
    # mutate ONLY the future close at k+h (cont is measured vs the fixed level)
    c2 = sig["close"].to_numpy().copy()
    c2[k + h] = 1.0  # far below any boundary level near 1.05
    sig2 = sig.copy()
    sig2["close"] = c2
    out2 = pa.measure_outcomes(ep, sig2)
    assert out2.iloc[0][f"cont_{h}"] != base_cont, "outcome must react to future bars"


# ---------------------------------------------------------------------------
# 4. Event dedup
# ---------------------------------------------------------------------------

def test_episode_dedup_unique():
    sig = make_signals()
    for variant in pa.P4_VARIANTS:
        for boundary in pa.P4_BOUNDARIES:
            for direction in pa.P4_DIRECTIONS:
                ep = pa.detect_acceptance_episodes(sig, variant, boundary, direction)
                if ep.empty:
                    continue
                assert ep["episode_id"].is_unique, f"{variant} b{boundary} d{direction} dup ids"
                assert ep["event_pos"].is_unique, f"{variant} b{boundary} d{direction} dup starts"


def test_no_duplicate_acceptance_per_episode():
    sig = make_signals()
    for variant in pa.P4_VARIANTS:
        ep = pa.detect_acceptance_episodes(sig, variant, 1.0, 1.0)
        acc = ep[ep["accepted"]]
        assert acc["acceptance_pos"].is_unique, f"{variant} duplicate acceptance bars"


# ---------------------------------------------------------------------------
# 5. Static leakage audit (executable P4 sources)
# ---------------------------------------------------------------------------

def test_p4_acceptance_source_leakage_audit():
    """Executable operations in the P4 engine must contain no leakage ops."""
    findings = pa.executable_leakage_scan(inspect.getsource(pa), "mve.p4_acceptance")
    leaks = [f for f in findings if f["pattern"] in ("shift(-", "center=True", "bfill()", "backfill()", "iloc[]")]
    assert leaks == [], f"leakage operations found: {leaks}"


def test_p4_no_blocked_component_consumption():
    src = inspect.getsource(pa) + inspect.getsource(ps)
    for token in ("model_D", "model_E", "generate_all_signals", "SignalGenerator"):
        assert token not in src, f"P4 must not consume blocked component {token}"


def test_p4_statistics_source_leakage_audit():
    findings = pa.executable_leakage_scan(inspect.getsource(ps), "mve.p4_statistics")
    leaks = [f for f in findings if f["pattern"] in ("shift(-", "center=True", "bfill()", "backfill()", "iloc[]")]
    assert leaks == [], f"leakage operations found: {leaks}"


# ---------------------------------------------------------------------------
# 6. Determinism
# ---------------------------------------------------------------------------

def test_detection_deterministic():
    sig = make_signals()
    a = pa.detect_acceptance_episodes(sig, "A2_3OF5", 1.0, 1.0)
    b = pa.detect_acceptance_episodes(sig, "A2_3OF5", 1.0, 1.0)
    pd.testing.assert_frame_equal(a, b)


# ---------------------------------------------------------------------------
# 7. Data discipline: holdout guard
# ---------------------------------------------------------------------------

def test_holdout_guard_2026_unreachable():
    """The P4 pipeline must not be able to slice into 2026 (final holdout)."""
    import mve.data_loader as dl

    assert dl.HOLDOUT_STATUS == "FINAL_HOLDOUT_PENDING"
    idx = pd.date_range("2025-01-01", periods=10, freq="h", tz="UTC")
    with pytest.raises(DataPipelineError):
        slice_data(pd.DataFrame(index=idx), "2026-01-01", "2026-01-31")
    idx2 = pd.date_range("2023-07-03", periods=10, freq="h", tz="UTC")
    with pytest.raises(DataPipelineError):
        slice_data(pd.DataFrame(index=idx2), "2024-12-01", "2025-06-01")


# ---------------------------------------------------------------------------
# 8. Statistics helpers
# ---------------------------------------------------------------------------

def test_wilson_ci_sanity():
    p, lo, hi = ps.wilson_ci(50, 100)
    assert abs(p - 0.5) < 1e-12
    assert lo < p < hi
    assert lo > 0.4 and hi < 0.6


def test_bh_fdr_monotone_and_bounded():
    rng = np.random.default_rng(11)
    p = rng.uniform(0, 1, 40)
    q = ps.bh_fdr(p)
    assert (q >= 0).all() and (q <= 1).all()
    order = np.argsort(q)
    assert np.all(np.diff(q[order]) >= -1e-12)


def test_likelihood_ratio_test():
    assert ps.likelihood_ratio_test(100, 100, 1) == pytest.approx(1.0)
    assert ps.likelihood_ratio_test(100, 110, 1) == pytest.approx(0.0015654, abs=1e-4)
    assert ps.likelihood_ratio_test(100, 90, 1) == pytest.approx(1.0)  # full better


def test_logistic_regression_recovers_coefficient():
    rng = np.random.default_rng(5)
    X = rng.normal(0, 1, (2000, 1))
    logit = 0.7 * X[:, 0]
    p = 1.0 / (1.0 + np.exp(-logit))
    y = (rng.random(2000) < p).astype(float)
    fit = ps.fit_logistic(X, y)
    # slope should be close to 0.7 (Wald z strongly significant)
    assert fit["converged"]
    slope = fit["coef"][1]
    assert abs(slope - 0.7) < 0.15
    assert fit["p"][1] < 1e-6


def test_kaplan_meier_bounds():
    times = np.array([2, 3, 5, 7, 10, 24, 24, 24])
    events = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    km = ps.kaplan_meier(times, events)
    assert (km["survival"] <= 1.0).all() and (km["survival"] >= 0.0).all()
    assert (km["hazard"].dropna() >= 0.0).all()
    assert km["survival"].is_monotonic_decreasing


def test_transition_matrix_row_sums():
    rng = np.random.default_rng(3)
    f = rng.integers(0, 4, 500)
    t = rng.integers(0, 4, 500)
    tm = ps.transition_matrix(f, t)
    row_sums = tm.drop(columns="N").sum(axis=1)
    # empty rows (no observations) sum to 0; populated rows must sum to 1
    assert np.allclose(row_sums[row_sums.index.isin(np.unique(f))], 1.0, atol=1e-9)
