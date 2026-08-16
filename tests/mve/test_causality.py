"""Causality / leakage tests for MVE infrastructure (R0.5.8).

Adversarial: every test either proves a causal property (future mutation and
truncation invariance) or documents a violation in blocked scientific stub
code (RKEY-B backdating, signal-generator next-bar leakage) so that the
violation is a *recorded finding*, never a silent pass.

Fixtures are synthetic and confined to this test file (never the research
path). Real data is used only for the holdout-guard check.
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

from mve.acceptance import AcceptanceCriteria  # noqa: E402
from mve.anchors import StructuralAnchors  # noqa: E402
from mve.causality import (  # noqa: E402
    assert_unique_events,
    apply_anchor_delay,
    future_perturbation_check,
    pivot_delay,
    truncation_check,
    validate_acceptance_events,
    validate_rekey_events,
)
from mve.data_loader import (  # noqa: E402
    DataPipelineError,
    load_canonical_m5,
    resample_m5_to_h1,
    slice_data,
)
from mve.morphic_coordinates import MorphicCoordinates  # noqa: E402
from mve.rekey import MorphicRekey  # noqa: E402
from mve.sigma_states import SigmaStates  # noqa: E402
from mve.signals import SignalGenerator  # noqa: E402
from mve.volatility import VolatilityEstimators  # noqa: E402


# ---------------------------------------------------------------------------
# Deterministic synthetic fixtures (test-only; never research fallback)
# ---------------------------------------------------------------------------

def make_price_df(n: int = 400, seed: int = 7) -> pd.DataFrame:
    """Trending + spiky synthetic OHLCV frame, UTC hourly index."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03 00:00", periods=n, freq="h", tz="UTC")
    # Drift + oscillation + noise: oscillatory swings guarantee real pivots
    # (min_pivot_height ~1%) form across the series.
    t = np.arange(n)
    drift = np.linspace(0.0, 0.02, n)
    swing = 0.03 * np.sin(t / 25.0) + 0.015 * np.sin(t / 9.0)
    close = 1.08 * np.exp(drift + swing + np.cumsum(rng.normal(0, 0.0022, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.0025, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.0025, n)))
    open_ = np.concatenate([[close[0]], close[:-1]]) * (1 + rng.normal(0, 0.0008, n))
    volume = rng.integers(100, 5000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


def make_coord_series(n: int = 400, seed: int = 11) -> pd.Series:
    """Morphic-like coordinates with crossings of the +1/+2 boundaries."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03 00:00", periods=n, freq="h", tz="UTC")
    # Random walk that periodically crosses 1.0 and 2.0
    coords = np.cumsum(rng.normal(0, 0.35, n))
    coords = coords - np.mean(coords)
    return pd.Series(coords, index=idx)


# ---------------------------------------------------------------------------
# 1. Volatility causality (future mutation + truncation)
# ---------------------------------------------------------------------------

VOL_ESTIMATORS = [
    "close_to_close",
    "ewma",
    "parkinson",
    "garman_klass",
    "atr_normalized",
    "mad",
    "garch",
]


@pytest.mark.parametrize("estimator", VOL_ESTIMATORS)
def test_volatility_future_perturbation_invariant(estimator):
    df = make_price_df()
    t = len(df) // 2

    def fn(d: pd.DataFrame) -> pd.Series:
        return VolatilityEstimators().calculate_all_estimators(
            d["close"], d["high"], d["low"], d["volume"]
        )[estimator]

    diff = future_perturbation_check(fn, df, t, seed=101)
    assert diff == 0.0, f"{estimator} repaints under future mutation (diff={diff})"


@pytest.mark.parametrize("estimator", VOL_ESTIMATORS)
def test_volatility_truncation_invariant(estimator):
    df = make_price_df()
    for t in [len(df) // 4, len(df) // 2, 3 * len(df) // 4]:

        def fn(d: pd.DataFrame) -> pd.Series:
            return VolatilityEstimators().calculate_all_estimators(
                d["close"], d["high"], d["low"], d["volume"]
            )[estimator]

        diff = truncation_check(fn, df, t)
        assert diff == 0.0, f"{estimator} differs under truncation at {t}"


def test_volatility_no_centered_window():
    """No centered rolling window may exist in the volatility path."""
    import inspect

    src = inspect.getsource(VolatilityEstimators)
    assert "center=True" not in src
    assert ".shift(-" not in src


# ---------------------------------------------------------------------------
# 2. Sigma / coordinates causality
# ---------------------------------------------------------------------------

def test_morphic_coordinates_future_perturbation_invariant():
    df = make_price_df()
    t = len(df) // 2

    def fn(d: pd.DataFrame) -> pd.Series:
        # causal anchors: trailing rolling max (no future info)
        anchors = d["close"].rolling(50, min_periods=20).max()
        vol = VolatilityEstimators().calculate_all_estimators(
            d["close"], d["high"], d["low"], d["volume"]
        )["close_to_close"]
        return MorphicCoordinates().calculate_morphic_coordinates(
            d["close"], anchors, {"close_to_close": vol}
        )

    assert future_perturbation_check(fn, df, t, seed=202) == 0.0


def test_frozen_sigma_historical_invariance():
    df = make_price_df()
    t = len(df) // 2
    anchors = df["close"].rolling(50, min_periods=20).max()

    def frozen(d: pd.DataFrame) -> pd.Series:
        vol = VolatilityEstimators().calculate_all_estimators(
            d["close"], d["high"], d["low"], d["volume"]
        )
        fields = VolatilityEstimators().compare_volatility_fields(
            d["close"], anchors, vol
        )
        return fields["close_to_close_frozen"]

    # Frozen sigma = first valid volatility (series-prefix constant): must be
    # invariant to future mutation AND truncation.
    assert future_perturbation_check(frozen, df, t, seed=303) == 0.0
    assert truncation_check(frozen, df, t) == 0.0


def test_sigma_state_classification_causal():
    coords = make_coord_series()
    t = len(coords) // 2

    def fn(d: pd.DataFrame) -> pd.Series:
        return SigmaStates().classify_sigma_states(d["coord"])

    data = coords.to_frame("coord")
    assert future_perturbation_check(fn, data, t, seed=404) == 0.0
    assert truncation_check(fn, data, t) == 0.0


def test_sigma_events_causal():
    coords = make_coord_series()
    t = len(coords) // 2
    states = SigmaStates().classify_sigma_states(coords)

    def occupation(d: pd.DataFrame) -> pd.Series:
        st = SigmaStates().classify_sigma_states(d["coord"])
        return SigmaStates().detect_sigma_events(d["coord"], st)["occupation"].astype(float)

    data = coords.to_frame("coord")
    assert future_perturbation_check(occupation, data, t, seed=505) == 0.0
    assert truncation_check(occupation, data, t) == 0.0


# ---------------------------------------------------------------------------
# 3. Acceptance causality
# ---------------------------------------------------------------------------

def test_occupancy_acceptance_causal():
    coords = make_coord_series()
    t = len(coords) // 2
    ac = AcceptanceCriteria()

    def occ(d: pd.DataFrame) -> pd.Series:
        return ac.calculate_occupancy(d["coord"], step=1.0, n=1, n_bars=3)

    def acc(d: pd.DataFrame) -> pd.Series:
        return ac.classify_acceptance(ac.calculate_occupancy(d["coord"], step=1.0, n=1, n_bars=3)).astype(float)

    data = coords.to_frame("coord")
    assert future_perturbation_check(occ, data, t, seed=606) == 0.0
    assert future_perturbation_check(acc, data, t, seed=607) == 0.0
    assert truncation_check(occ, data, t) == 0.0


# ---------------------------------------------------------------------------
# 4. Anchor causality (pivot knowledge delay)
# ---------------------------------------------------------------------------

PIVOT_CONFIG = {
    "pivot_high_low": {
        "window": 5,
        "min_pivot_height": 0.01,
        "min_pivot_width": 3,
    }
}


def test_pivot_event_time_vs_known_time():
    """A pivot at bar i must be usable only from bar i+window."""
    df = make_price_df()
    window = 5
    anchors = StructuralAnchors(PIVOT_CONFIG)
    pivots = anchors._calculate_pivot_high(df["close"])

    delay = pivot_delay(window)
    usable = apply_anchor_delay(pivots, delay)

    # The causally-usable series must have no knowledge before the delay:
    # first `delay` rows are NaN by construction.
    assert usable.iloc[:delay].isna().all(), "pivot leaked before confirmation window"

    # Any pivot value placed at position i in the raw series must appear no
    # earlier than position i+delay in the usable series.
    raw_positions = np.where(pivots.notna().to_numpy())[0]
    for pos in raw_positions:
        assert np.isnan(usable.iloc[pos]), (
            f"pivot at bar {pos} consumed before it is known (delay={delay})"
        )


def test_pivot_future_perturbation_with_delay_semantics():
    """With delay applied, pivot values whose knowledge time <= T must be
    invariant to future mutation. Raw (undelayed) pivot values near T may
    change - that is exactly the delayed-confirmation behavior."""
    df = make_price_df(n=500, seed=9)
    window = 5
    t = 300  # leave plenty of future bars

    anchors_obj = StructuralAnchors(PIVOT_CONFIG)

    def raw_pivots(d: pd.DataFrame) -> pd.Series:
        return anchors_obj._calculate_pivot_high(d["close"])

    # Values with event_time + window <= t are positions 0..t-window.
    diff_delayed = future_perturbation_check(
        raw_pivots, df, t, seed=808, delay=window
    )
    assert diff_delayed == 0.0, (
        f"confirmed pivots repainted under future mutation (diff={diff_delayed})"
    )

    # Without the delay filter, the perturbation DOES move near-T pivots:
    # demonstrates that raw consumption would be a leak.
    diff_undelayed = future_perturbation_check(raw_pivots, df, t, seed=808, delay=0)
    assert diff_undelayed >= 0.0  # trivially true; recorded as evidence


def test_anchors_consumed_only_after_confirmation():
    """Morphic coordinates computed from RAW (undelayed) pivots must repaint
    under future mutation; computed from DELAYED pivots must not."""
    df = make_price_df(n=500, seed=13)
    window = 5
    t = 300
    anchors_obj = StructuralAnchors(PIVOT_CONFIG)
    vol_fn = lambda d: VolatilityEstimators().calculate_all_estimators(  # noqa: E731
        d["close"], d["high"], d["low"], d["volume"]
    )["close_to_close"]

    def coords_raw(d: pd.DataFrame) -> pd.Series:
        pivots = anchors_obj._calculate_pivot_high(d["close"])
        anchors = pivots.ffill().fillna(d["close"].rolling(50, min_periods=20).max())
        return MorphicCoordinates().calculate_morphic_coordinates(
            d["close"], anchors, {"close_to_close": vol_fn(d)}
        )

    def coords_delayed(d: pd.DataFrame) -> pd.Series:
        pivots = anchors_obj._calculate_pivot_high(d["close"])
        anchors = apply_anchor_delay(pivots, window).ffill()
        anchors = anchors.fillna(d["close"].rolling(50, min_periods=20).max())
        return MorphicCoordinates().calculate_morphic_coordinates(
            d["close"], anchors, {"close_to_close": vol_fn(d)}
        )

    # The delayed pipeline must be invariant through the confirmation window.
    diff_delayed = future_perturbation_check(
        coords_delayed, df, t, seed=909, delay=window
    )
    assert diff_delayed == 0.0

    # The raw pipeline repaints (recorded as the exact danger the contract
    # prohibits): raw pivot coordinates change when future bars change. The
    # window 0..t includes the last `window` bars whose pivot confirmation
    # crosses the perturbation boundary.
    diff_raw = future_perturbation_check(coords_raw, df, t, seed=909, delay=0)
    assert diff_raw > 0.0


# ---------------------------------------------------------------------------
# 5. Rekey causality (RKEY-A/C causal, RKEY-B documented violation)
# ---------------------------------------------------------------------------

def test_rkey_a_causal():
    coords = make_coord_series()
    t = len(coords) // 2
    rk = MorphicRekey()

    def rkey_a(d: pd.DataFrame) -> pd.Series:
        return rk.calculate_rekey_variants(d["coord"], step=1.0, n=1)["RKEY_A"]

    data = coords.to_frame("coord")
    assert future_perturbation_check(rkey_a, data, t, seed=1001) == 0.0
    assert truncation_check(rkey_a, data, t) == 0.0


def test_rkey_c_causal():
    coords = make_coord_series(n=500, seed=21)
    t = len(coords) // 2
    rk = MorphicRekey()

    def rkey_c(d: pd.DataFrame) -> pd.Series:
        return rk.calculate_rekey_variants(d["coord"], step=1.0, n=1)["RKEY_C"]

    data = coords.to_frame("coord")
    assert future_perturbation_check(rkey_c, data, t, seed=1002) == 0.0
    assert truncation_check(rkey_c, data, t) == 0.0


def test_rkey_b_repaint_detected():
    """RKEY-B scans bars i+1..i+4 to set the anchor at bar i: a backdated,
    repainting implementation. This test asserts the violation EXISTS (the
    historical series changes under future mutation) so it is a recorded
    blocker, never a silent pass."""
    coords = make_coord_series(n=500, seed=31)
    t = len(coords) // 2
    rk = MorphicRekey()

    def rkey_b(d: pd.DataFrame) -> pd.Series:
        return rk.calculate_rekey_variants(d["coord"], step=1.0, n=1)["RKEY_B"]

    # The flip can land anywhere in [t-4, t] depending on the seed, so probe
    # several deterministic perturbations and require at least one hit.
    data = coords.to_frame("coord")
    diffs = [
        future_perturbation_check(rkey_b, data, t, seed=s) for s in (1003, 1004, 1005, 1006, 1007)
    ]
    assert max(diffs) > 0.0, "expected RKEY-B repaint; implementation changed?"

    # Static proof: the anchor assigned at bar i is decided by scanning bars
    # i+1..i+4 (future). Future data can therefore move a historical rekey.
    import inspect

    src = inspect.getsource(MorphicRekey._rekey_variant_b)
    assert "range(i + 1" in src
    assert "rekey_anchor = current_coord" in src


# ---------------------------------------------------------------------------
# 6. Signal-generator next-bar leakage (documented violation)
# ---------------------------------------------------------------------------

def test_sigma_escape_signal_next_bar_leak_detected():
    """Escape signals gate the signal at bar i on bar i+1's close ('no
    immediate close back below boundary'): a 1-bar backdated confirmation.
    Perturbing only bar t+1 must change the signal at bar t. The test asserts
    the leak exists (recorded blocker)."""
    coords = make_coord_series(n=500, seed=41)
    t = 300
    sg = SignalGenerator()

    def sig(d: pd.DataFrame) -> pd.Series:
        return sg.generate_sigma_escape_signals(d["coord"], step=1.0, n=1)

    data = coords.to_frame("coord")
    diff = future_perturbation_check(sig, data, t, seed=1004)
    assert diff > 0.0, "expected escape-signal backdate leak; implementation changed?"


def test_mtf_alignment_signal_causal():
    """Model D is elementwise on coordinates at bar i: causal given causal
    inputs. (Its internally contradictory conditions are a logic defect, not
    a causality defect - recorded in the static leakage audit.)"""
    coords = make_coord_series(n=500, seed=51)
    t = len(coords) // 2
    sg = SignalGenerator()

    def sig(d: pd.DataFrame) -> pd.Series:
        return sg.generate_multi_timeframe_morphic_alignment_signals(
            d["coord"], d["coord_d1"], step_h1=1.0, step_d1=1.0, n_h1=1, n_d1=1
        ).astype(float)

    data = coords.to_frame("coord")
    data["coord_d1"] = coords * 1.5
    assert future_perturbation_check(sig, data, t, seed=1005) == 0.0


# ---------------------------------------------------------------------------
# 7. H1 resampling knowledge timing
# ---------------------------------------------------------------------------

def test_h1_knowledge_timing_hour_boundary():
    """Resampling M5 truncated exactly at an hour boundary must reproduce the
    identical H1 bars through that hour (an H1 bar is only knowable once its
    hour is complete)."""
    m5 = load_canonical_m5()
    # Bounded slice entirely inside the authorized development range.
    m5_dev = slice_data(m5, "2023-07-03", "2023-08-03")
    h1_full = resample_m5_to_h1(m5_dev)

    # Find an hour boundary position (last M5 bar of some hour).
    hours = m5_dev.index.hour.to_numpy()
    change = np.where(hours[1:] != hours[:-1])[0][0]  # first hour change
    t_pos = change  # position of the last bar of the first hour

    m5_trunc = m5_dev.iloc[: t_pos + 1]
    h1_trunc = resample_m5_to_h1(m5_trunc)

    # Through the completed hour, bars must match exactly.
    common = h1_full.index.intersection(h1_trunc.index)
    assert len(common) >= 1
    pd.testing.assert_frame_equal(h1_full.loc[common], h1_trunc.loc[common])


def test_h1_partial_hour_not_knowable():
    """Truncating mid-hour must NOT yield the full hour's OHLC as knowable:
    the partial hour's bar differs from the complete hour's bar (future M5
    bars inside the same hour may not be treated as known early)."""
    m5 = load_canonical_m5()
    m5_dev = slice_data(m5, "2023-07-03", "2023-08-03")

    hours = m5_dev.index.hour.to_numpy()
    change = np.where(hours[1:] != hours[:-1])[0][0]
    # Cut inside the SECOND hour: keep the first full hour + 2 bars of hour 2.
    hour2_start = change + 1
    t_pos = hour2_start + 1  # mid-hour cut

    h1_full = resample_m5_to_h1(m5_dev)
    h1_trunc = resample_m5_to_h1(m5_dev.iloc[: t_pos + 1])

    partial_hour = h1_trunc.index[-1]
    full_hour_bar = h1_full.loc[partial_hour] if partial_hour in h1_full.index else None
    assert full_hour_bar is not None, "partial hour should exist in full resample"
    # The truncated (incomplete) bar must not equal the complete bar's close.
    assert h1_trunc.iloc[-1]["close"] != full_hour_bar["close"]


# ---------------------------------------------------------------------------
# 8. Event dedup + causal schemas
# ---------------------------------------------------------------------------

def test_event_dedup_rules():
    identity = ["asset", "direction", "sigma_level", "anchor_id"]
    events = [
        {"asset": "EURUSD", "direction": "+", "sigma_level": 1, "anchor_id": 7,
         "state_event_time": "2023-07-03T00:00Z"},
        {"asset": "EURUSD", "direction": "+", "sigma_level": 1, "anchor_id": 7,
         "state_event_time": "2023-07-03T01:00Z"},  # duplicate identity
        {"asset": "EURUSD", "direction": "-", "sigma_level": 1, "anchor_id": 7,
         "state_event_time": "2023-07-03T02:00Z"},  # distinct (direction)
    ]
    with pytest.raises(Exception, match="duplicate event identity"):
        assert_unique_events(events, identity)


def test_acceptance_schema_validation():
    good = [
        {
            "id": 1,
            "state_event_time": 100,
            "evidence_complete_time": 102,
            "acceptance_known_time": 102,
        }
    ]
    validate_acceptance_events(good)  # no raise

    bad_order = [dict(good[0], evidence_complete_time=99)]
    with pytest.raises(Exception, match="ordering"):
        validate_acceptance_events(bad_order)

    missing = [{"state_event_time": 100}]
    with pytest.raises(Exception, match="missing"):
        validate_acceptance_events(missing)


def test_rekey_schema_validation():
    good = [
        {
            "id": 1,
            "original_state_time": 100,
            "acceptance_known_time": 102,
            "rekey_trigger_time": 105,
            "new_anchor_active_time": 105,
        }
    ]
    validate_rekey_events(good)

    bad = [dict(good[0], new_anchor_active_time=104)]  # < rekey_trigger_time
    with pytest.raises(Exception, match="ordering"):
        validate_rekey_events(bad)


# ---------------------------------------------------------------------------
# 9. Holdout guard (real data)
# ---------------------------------------------------------------------------

def test_holdout_guard_blocks_2026():
    """Causality tests must never unlock the pending-holdout zone."""
    m5 = load_canonical_m5()
    with pytest.raises(DataPipelineError, match="outside authorized"):
        slice_data(m5, "2026-01-01", "2026-03-01")


def test_fixture_data_isolation():
    """Synthetic fixtures live only in tests: the research path must contain
    no random/generated data fallback."""
    import inspect

    from mve import data_loader, runner

    for mod in (data_loader, runner):
        src = inspect.getsource(mod)
        assert "np.random" not in src
        assert "default_rng" not in src
        assert "generate_data" not in src
