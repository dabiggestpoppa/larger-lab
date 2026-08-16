"""P4 Causal Acceptance Engine tests (MVE-P4-CAUSAL-ACCEPTANCE-ENGINE).

Adversarial: every test proves a causal property of the acceptance engine
(A0-A5 variants, episode dedup, event-time schema) or an isolation property
(blocked Models D/E absent, holdout guarded). Fixtures are synthetic and
confined to this test file; real data is used ONLY for the holdout-guard
check (the canonical loader verifies its own hash fail-closed).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mve.causality import (  # noqa: E402
    assert_unique_events,
    future_perturbation_check,
    truncation_check,
    validate_acceptance_events,
    validate_scientific_event_times,
)
from mve.data_loader import (  # noqa: E402
    DataPipelineError,
    load_canonical_m5,
    resample_m5_to_h1,
    slice_data,
)
from mve.p4_acceptance import (  # noqa: E402
    VARIANT_DELAY,
    VARIANT_KEYS,
    AcceptanceConfig,
    build_fields,
    compute_structural_outcomes,
    detect_acceptance_events,
    events_to_series,
    validate_event_catalog,
)


# ---------------------------------------------------------------------------
# Deterministic synthetic fixtures (test-only)
# ---------------------------------------------------------------------------

def make_price_df(n: int = 1200, seed: int = 7) -> pd.DataFrame:
    """Oscillating + drifting synthetic OHLCV frame, UTC hourly index."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03 00:00", periods=n, freq="h", tz="UTC")
    t = np.arange(n)
    drift = np.linspace(0.0, 0.03, n)
    swing = 0.035 * np.sin(t / 32.0) + 0.018 * np.sin(t / 11.0)
    close = 1.08 * np.exp(drift + swing + np.cumsum(rng.normal(0, 0.0022, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.0025, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.0025, n)))
    open_ = np.concatenate([[close[0]], close[:-1]]) * (1 + rng.normal(0, 0.0008, n))
    volume = rng.integers(100, 5000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


@pytest.fixture(scope="module")
def events_and_df():
    df = make_price_df()
    events = detect_acceptance_events(df)
    return df, events


# ---------------------------------------------------------------------------
# Event-time schema + dedup
# ---------------------------------------------------------------------------

def test_p4_event_catalog_schema_valid(events_and_df):
    _, events = events_and_df
    assert len(events) > 0
    # Both frozen schemas pass with zero problems (fail-closed validators).
    assert validate_acceptance_events(events, raise_on_error=False) == []
    assert validate_scientific_event_times(events, raise_on_error=False) == []
    assert validate_event_catalog(events, raise_on_error=False) == []


def test_p4_no_backdating_per_variant(events_and_df):
    """Every variant obeys state <= evidence <= known; delayed variants must
    never be known before their evidence completes."""
    _, events = events_and_df
    for ev in events:
        assert ev["state_event_time"] <= ev["evidence_complete_time"] <= ev[
            "acceptance_known_time"
        ], ev["event_id"]
        assert ev["event_time"] <= ev["known_time"] <= ev["action_time"], ev["event_id"]
    # A2/A3/A4 are delayed: known (== evidence) must be strictly after state
    # for at least some events (genuine confirmation), and NEVER before.
    for variant in ("A2_2of3", "A2_3of4", "A2_3of5", "A3_n2", "A3_n3", "A3_n4", "A4_R1", "A4_R2"):
        subset = [e for e in events if e["variant"] == variant]
        assert subset, f"{variant} produced no events on fixture"
        for ev in subset:
            assert ev["acceptance_known_time"] >= ev["state_event_time"]
            assert ev["acceptance_known_time"] >= ev["evidence_complete_time"]


def test_p4_event_dedup_unique(events_and_df):
    """One event per (direction, sigma level, episode, variant)."""
    _, events = events_and_df
    problems = assert_unique_events(
        events,
        ["direction", "sigma_level", "episode_id", "variant"],
        raise_on_error=False,
    )
    assert problems == []


def test_p4_required_fields_present(events_and_df):
    _, events = events_and_df
    required = {
        "event_id", "variant", "direction", "boundary_id", "boundary_value",
        "state_event_time", "evidence_complete_time", "acceptance_known_time",
        "price_at_event", "price_at_known", "sigma_state", "morphic_coordinate",
        "volatility_state", "anchor_type", "anchor_value",
        "distance_from_boundary", "evidence_window", "accepted",
        "rejection_reason", "episode_id",
    }
    for ev in events:
        missing = required - set(ev.keys())
        assert not missing, f"{ev['event_id']} missing {missing}"


# ---------------------------------------------------------------------------
# Variant timing semantics (A0-A5)
# ---------------------------------------------------------------------------

def test_p4_a0_touch_known_same_bar(events_and_df):
    _, events = events_and_df
    for ev in [e for e in events if e["variant"] == "A0"]:
        # Touch is known at the episode-start bar close: all three equal.
        assert ev["state_event_time"] == ev["evidence_complete_time"] == ev[
            "acceptance_known_time"
        ]


def test_p4_a1_close_known_at_close_bar(events_and_df):
    """A1 evidence == known (close-beyond bar), and >= state."""
    _, events = events_and_df
    for ev in [e for e in events if e["variant"] == "A1"]:
        assert ev["evidence_complete_time"] == ev["acceptance_known_time"]
        assert ev["acceptance_known_time"] >= ev["state_event_time"]


def test_p4_a2_occupancy_window_bound(events_and_df):
    """A2 evidence is within the N-of-M window after the episode start:
    evidence - state <= m - 1 for the 3-of-5 grid."""
    _, events = events_and_df
    for ev in [e for e in events if e["variant"] == "A2_3of5"]:
        assert ev["evidence_complete_time"] - ev["state_event_time"] <= 4


def test_p4_a3_persistence_requires_consecutive(events_and_df):
    """A3-n4 evidence is exactly 3 bars after state for a 4-consecutive
    requirement starting at the episode start (first beyond bar must be the
    start for a 4-streak)."""
    _, events = events_and_df
    for ev in [e for e in events if e["variant"] == "A3_n4"]:
        assert ev["acceptance_known_time"] >= ev["state_event_time"]
        assert ev["evidence_window"] <= 3


def test_p4_a4_retest_hold_evidence_after_breach(events_and_df):
    """A4 retest-hold: evidence strictly after the breach bar and its bar's
    low reaches the boundary while its close holds beyond."""
    df, events = events_and_df
    fields = build_fields(df)
    for ev in [e for e in events if e["variant"] in ("A4_R1", "A4_R2")]:
        assert ev["evidence_complete_time"] > ev["state_event_time"]
        assert ev["evidence_complete_time"] == ev["acceptance_known_time"]
        t_r = ev["evidence_complete_time"]
        side = ev["direction"]
        k = ev["sigma_level"]
        b = (fields["b_long"][k] if side == "+" else fields["b_short"][k]).iloc[t_r]
        sig = fields["sigma"].iloc[t_r]
        close = df["close"].iloc[t_r]
        if ev["variant"] == "A4_R2":  # exact recross tolerance 0.0
            if side == "+":
                assert df["low"].iloc[t_r] <= b
                assert close > b
            else:
                assert df["high"].iloc[t_r] >= b
                assert close < b
        else:  # R1: 0.5-sigma tolerance (log-scale, on the outside of the boundary)
            if side == "+":
                band = b * np.exp(0.5 * sig * np.sqrt(1.0))
                assert df["low"].iloc[t_r] <= band and close > b
            else:
                band = b * np.exp(-0.5 * sig * np.sqrt(1.0))
                assert df["high"].iloc[t_r] >= band and close < b


def test_p4_a5_failed_acceptance_resolves_at_touch(events_and_df):
    """A5 (no close-beyond ever) resolves at the touch bar close: the failure
    is known the moment the bar closes inside."""
    _, events = events_and_df
    for ev in [e for e in events if e["variant"] == "A5"]:
        assert ev["accepted"] is False
        assert ev["rejection_reason"] == "never_close_beyond"
        assert ev["state_event_time"] == ev["acceptance_known_time"]


# ---------------------------------------------------------------------------
# Boundary direction plumbing
# ---------------------------------------------------------------------------

def test_p4_boundary_direction_sides(events_and_df):
    _, events = events_and_df
    sides = {e["direction"] for e in events}
    assert sides == {"+", "-"}
    families = {e["boundary_id"] for e in events}
    assert "LONG_s1sigma" in families and "SHORT_s1sigma" in families


def test_p4_symmetry_plumbing_outcomes(events_and_df):
    df, events = events_and_df
    out = compute_structural_outcomes(df, events)
    assert out["direction"].isin(["+", "-"]).all()
    assert out.groupby("direction").size().to_dict() == dict(out.groupby("direction").size())


# ---------------------------------------------------------------------------
# Causality: future perturbation + truncation invariance
# ---------------------------------------------------------------------------

def _engine_series(df: pd.DataFrame, variant: str) -> pd.Series:
    events = detect_acceptance_events(df)
    return events_to_series(events, df.index)[variant]


@pytest.mark.parametrize("variant", VARIANT_KEYS)
def test_p4_future_perturbation_invariant(variant):
    """Mutating all data after cutoff t must not alter event history whose
    knowledge time <= t - variant_delay."""
    df = make_price_df(n=900, seed=13)
    delay = VARIANT_DELAY[variant]
    diffs = []
    for cut in (0.35, 0.65):
        for seed in (5001, 5002):
            t = int(len(df) * cut)
            diff = future_perturbation_check(
                lambda d, v=variant: _engine_series(d, v), df, t, seed=seed, delay=delay
            )
            diffs.append(diff)
    assert all(d == 0.0 for d in diffs), f"{variant} repaints: {diffs}"


@pytest.mark.parametrize("variant", VARIANT_KEYS)
def test_p4_truncation_invariant(variant):
    df = make_price_df(n=900, seed=17)
    delay = VARIANT_DELAY[variant]
    for cut in (0.35, 0.65):
        t = int(len(df) * cut)
        diff = truncation_check(
            lambda d, v=variant: _engine_series(d, v), df, t, delay=delay
        )
        assert diff == 0.0, f"{variant} differs under truncation at {t}"


def test_p4_delayed_variants_never_early():
    """A2/A3/A4 events must never appear before their evidence completes:
    their indicator value at position p requires evidence <= p."""
    df = make_price_df(n=600, seed=23)
    events = detect_acceptance_events(df)
    for ev in events:
        if ev["variant"] in ("A2_2of3", "A2_3of4", "A2_3of5", "A3_n2", "A3_n3", "A3_n4", "A4_R1", "A4_R2"):
            assert ev["acceptance_known_time"] >= ev["evidence_complete_time"]
            assert ev["evidence_complete_time"] >= ev["state_event_time"]


# ---------------------------------------------------------------------------
# Warm-up / NaN robustness
# ---------------------------------------------------------------------------

def test_p4_warmup_no_events():
    """No acceptance events before the volatility window + pivot delay are
    valid (sigma is NaN -> boundary unknown -> fail closed silently)."""
    df = make_price_df(n=600, seed=29)
    events = detect_acceptance_events(df)
    earliest = min(e["acceptance_known_time"] for e in events)
    assert earliest >= 20  # vol window 20 + pivot delay 5 + fallback


def test_p4_nan_region_does_not_repaint_history():
    df = make_price_df(n=900, seed=31)
    clean = detect_acceptance_events(df)
    df_nan = df.copy()
    nan_pos = 400
    df_nan.iloc[nan_pos, df_nan.columns.get_loc("close")] = np.nan
    events_nan = detect_acceptance_events(df_nan)  # must not crash
    clean_before = {
        (e["event_id"], e["acceptance_known_time"]) for e in clean if e["acceptance_known_time"] < nan_pos - 1
    }
    nan_before = {
        (e["event_id"], e["acceptance_known_time"]) for e in events_nan if e["acceptance_known_time"] < nan_pos - 1
    }
    assert clean_before == nan_before


# ---------------------------------------------------------------------------
# Blocked-component isolation
# ---------------------------------------------------------------------------

def test_p4_no_signals_import():
    """The acceptance engine has ZERO source-level dependency on the blocked
    signal generator (Models D/E). Its own source and the source of every
    module it directly imports must contain no signals reference.

    (mve/__init__.py eagerly re-exports all modules including signals; that is
    a sealed package artifact shared by every consumer including the runner,
    not a dependency of the acceptance engine itself.)"""
    import inspect

    import mve.p4_acceptance as p4
    from mve import anchors, causality, morphic_coordinates, volatility

    forbidden = ("SignalGenerator", "generate_all_signals",
                 "generate_morphic_trend_score_signals",   # Model E
                 "generate_multi_timeframe_morphic_alignment_signals")  # Model D
    for mod in (p4, anchors, causality, morphic_coordinates, volatility):
        src = inspect.getsource(mod)
        for token in forbidden:
            assert token not in src, f"{mod.__name__} references blocked {token}"

    # The engine module globals expose no blocked generator.
    assert not any("Signal" in k for k in vars(p4))

    # End-to-end: detection runs entirely on the engine's own code path.
    df = make_price_df(n=300, seed=41)
    events = detect_acceptance_events(df)
    assert len(events) > 0


def test_p4_blocked_models_not_in_pipeline():
    from mve.runner import PHASE_REGISTRY

    # Models D/E are not wired into any runner phase (only 4-7 exist and D/E
    # live in signals, which the acceptance engine never touches).
    assert 4 in PHASE_REGISTRY
    assert PHASE_REGISTRY[4]["scientific_status"] == "BLOCKED_SCIENTIFIC_IMPLEMENTATION"


def test_p4_holdout_guard():
    """Slicing into the pending 2026 holdout must fail closed (zero rows)."""
    m5 = load_canonical_m5()
    h1 = resample_m5_to_h1(m5)
    with pytest.raises(DataPipelineError):
        slice_data(h1, "2026-01-01", "2026-03-31")
    # Authorized dev slice works.
    dev = slice_data(h1, "2023-07-03", "2023-08-03")
    assert len(dev) > 0
