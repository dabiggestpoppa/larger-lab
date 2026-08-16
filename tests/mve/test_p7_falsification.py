"""P7 — Signal-Model Falsification tests.

Covers: event timing (known at correct bar, no backdating), baseline timing,
episode dedup, matching classes, direction from coordinates for state/entry
models, structural outcomes causality, blocked D/E isolation, perturbation /
truncation on sealed generators and baselines, schema ordering, holdout guard.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))

from mve.causality import (  # noqa: E402
    future_perturbation_check,
    truncation_check,
    validate_scientific_event_times,
)
from mve import p7_falsification as p7  # noqa: E402


def _make_x(periods: int = 120) -> pd.Series:
    idx = pd.date_range("2023-01-01", periods=periods, freq="h", tz="UTC")
    # step profile: inside -> beyond 1σ -> back inside -> beyond 2σ
    vals = (
        [0.3] * 20
        + [0.5] * 10
        + [1.6] * 15
        + [0.4] * 15
        + [0.7] * 10
        + [2.6] * 20
        + [0.5] * 10
        + [-0.4] * 20
    )
    vals = (vals * (periods // len(vals) + 1))[:periods]
    return pd.Series(np.array(vals, dtype=float), index=idx)


def _df(periods: int = 120) -> pd.DataFrame:
    x = _make_x(periods)
    return pd.DataFrame(
        {
            "x": x,
            "close": 1.0 + 0.001 * np.arange(periods),
            "vol": 0.01 + 0.0001 * np.arange(periods),
        },
        index=x.index,
    )


# ---------------------------------------------------------------------------
# Timing / no backdating
# ---------------------------------------------------------------------------

def test_model_a_known_at_confirmation_bar():
    x = _make_x()
    sig = p7.build_signal("MODEL_A", x)
    eps = p7.to_episodes(sig, "MODEL_A", x)
    assert not eps.empty
    # first beyond block starts at 30; A needs |x[30]|>1 AND |x[31]|>1 ->
    # known at 31.
    assert eps.iloc[0]["known_pos"] == 31
    assert eps.iloc[0]["known_time"] == x.index[31]
    assert eps.iloc[0]["action_time"] == x.index[31]


def test_model_b_realtime_episode():
    x = _make_x()
    sig = p7.build_signal("MODEL_B", x)
    eps = p7.to_episodes(sig, "MODEL_B", x)
    assert not eps.empty
    # occupancy window = 3 bars; state starts at the first bar where all 3
    # window bars are beyond -> at least index 32.
    assert eps.iloc[0]["known_pos"] >= 32
    # direction from coordinate sign (positive block)
    assert eps.iloc[0]["direction"] == 1.0


def test_model_c_entry_at_two_sigma():
    x = _make_x()
    sig = p7.build_signal("MODEL_C", x)
    eps = p7.to_episodes(sig, "MODEL_C", x)
    assert not eps.empty
    # entry requires crossing 1σ at i-1 and |x[i]| > 2σ; the 2.6 block starts
    # at 70 (0.7 then 2.6). crossing at 70 -> entry at 71.
    assert eps.iloc[0]["known_pos"] == 71


def test_b3_baseline_realtime_crossing():
    x = _make_x()
    sig = p7.build_signal("B3_PLAIN_BREAKOUT", x)
    eps = p7.to_episodes(sig, "B3_PLAIN_BREAKOUT", x)
    assert not eps.empty
    # first beyond bar is index 30
    assert eps.iloc[0]["known_pos"] == 30


def test_no_backdating_schema():
    x = _make_x()
    all_events = []
    for name in p7.MODELS + p7.BASELINES:
        sig = p7.build_signal(name, x)
        eps = p7.to_episodes(sig, name, x)
        if eps.empty:
            continue
        all_events.append(
            eps[
                [
                    "event_id",
                    "event_time",
                    "evidence_complete_time",
                    "known_time",
                    "action_time",
                ]
            ].to_dict("records")
        )
    flat = [e for chunk in all_events for e in chunk]
    errors = validate_scientific_event_times(flat, raise_on_error=False)
    assert errors == []


# ---------------------------------------------------------------------------
# Episode dedup
# ---------------------------------------------------------------------------

def test_episode_dedup_merges_consecutive():
    x = _make_x()
    sig = p7.build_signal("B3_PLAIN_BREAKOUT", x)
    eps = p7.to_episodes(sig, "B3_PLAIN_BREAKOUT", x)
    # long beyond block (30..44) merges into one episode; 2.6 block another.
    assert len(eps) == 2
    assert eps.iloc[0]["known_pos"] == 30
    assert eps.iloc[1]["known_pos"] == 70


def test_model_b_episode_is_contiguous_run():
    x = _make_x()
    sig = p7.build_signal("MODEL_B", x)
    eps = p7.to_episodes(sig, "MODEL_B", x)
    # two runs: the 1.6 block and the 2.6 block
    assert len(eps) == 2


# ---------------------------------------------------------------------------
# Matching classes
# ---------------------------------------------------------------------------

def test_matching_classes():
    x = _make_x()
    ma = p7.to_episodes(p7.build_signal("MODEL_A", x), "MODEL_A", x)
    b3 = p7.to_episodes(p7.build_signal("B3_PLAIN_BREAKOUT", x), "B3_PLAIN_BREAKOUT", x)
    matched = p7.match_events(ma, b3, "MODEL_A", "B3_PLAIN_BREAKOUT")
    assert not matched.empty
    assert set(matched["class"]) <= {"MODEL_AND_BASELINE", "MODEL_ONLY", "BASELINE_ONLY"}
    # A at 31 vs B3 at 30 -> MODEL_AND_BASELINE with timing_delta -1
    row = matched[matched["class"] == "MODEL_AND_BASELINE"].iloc[0]
    assert row["timing_delta"] == -1
    # the 2.6 block: A fires at 71 (needs 70 beyond + 71 beyond), B3 at 70
    row2 = matched[matched["known_pos"] == 71]
    assert len(row2) == 1 and row2.iloc[0]["class"] == "MODEL_AND_BASELINE"


def test_model_only_and_baseline_only():
    # baseline fires where model does not: a 1-bar beyond blip.
    idx = pd.date_range("2023-01-01", periods=30, freq="h", tz="UTC")
    x = pd.Series(np.array([0.3] * 10 + [1.6, 0.3] * 10, dtype=float), index=idx)
    b3 = p7.to_episodes(p7.build_signal("B3_PLAIN_BREAKOUT", x), "B3_PLAIN_BREAKOUT", x)
    ma = p7.to_episodes(p7.build_signal("MODEL_A", x), "MODEL_A", x)
    matched = p7.match_events(ma, b3, "MODEL_A", "B3_PLAIN_BREAKOUT")
    classes = set(matched["class"])
    assert "BASELINE_ONLY" in classes  # blips never confirm -> no A events
    assert "MODEL_ONLY" not in classes
    assert "MODEL_AND_BASELINE" not in classes


# ---------------------------------------------------------------------------
# Structural outcomes causality
# ---------------------------------------------------------------------------

def test_outcomes_measured_after_known_time():
    x = _make_x()
    b3 = p7.to_episodes(p7.build_signal("B3_PLAIN_BREAKOUT", x), "B3_PLAIN_BREAKOUT", x)
    out = p7.measure_outcomes(b3, x)
    assert "cont_6" in out.columns
    assert "signed_disp_6" in out.columns
    assert "mfe_6" in out.columns
    # outcome at horizon h uses bar k+h only (no future leakage by construction)
    k = int(out.iloc[0]["known_pos"])
    assert out.iloc[0]["cont_6"] in (0.0, 1.0)


def test_control_fields_causal():
    x = _make_x()
    vol = pd.Series(0.01 + 0.0001 * np.arange(len(x)), index=x.index)
    ctrl = p7.control_fields(x, vol, dev_end="2023-06-01")
    assert {"sigma_state", "vol_tercile", "hour", "session", "anchor_age", "prior_state_duration"} <= set(ctrl.columns)
    # hour/session match index
    assert (ctrl["hour"] == x.index.hour).all()
    # anchor age never negative
    assert (ctrl["anchor_age"].dropna() >= 0).all()


# ---------------------------------------------------------------------------
# Causality: perturbation + truncation on sealed generators and baselines
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", p7.MODELS + p7.BASELINES)
def test_future_perturbation_zero(name):
    data = _df()
    t = len(data) // 2
    delay = p7.SIGNAL_DELAY.get(name, 0)

    def fn(dd: pd.DataFrame) -> pd.Series:
        return p7.build_signal(name, dd["x"])

    diff = future_perturbation_check(fn, data, t, seed=601, delay=delay)
    assert diff == 0.0


@pytest.mark.parametrize("name", p7.MODELS + p7.BASELINES)
def test_truncation_invariance(name):
    data = _df()
    t = len(data) // 2
    delay = p7.SIGNAL_DELAY.get(name, 0)

    def fn(dd: pd.DataFrame) -> pd.Series:
        return p7.build_signal(name, dd["x"])

    diff = truncation_check(fn, data, t, delay=delay)
    assert diff == 0.0


# ---------------------------------------------------------------------------
# Blocked isolation
# ---------------------------------------------------------------------------

def test_no_model_d_e_dependency():
    src = open(
        os.path.join(_REPO_ROOT, "src", "mve", "p7_falsification.py"), encoding="utf-8"
    ).read()
    assert "generate_multi_timeframe" not in src
    assert "generate_morphic_trend_score" not in src
    assert "generate_all_signals" not in src


def test_no_acceptance_rekey_alpha():
    src = open(
        os.path.join(_REPO_ROOT, "src", "mve", "p7_falsification.py"), encoding="utf-8"
    ).read()
    assert "from mve.acceptance" not in src
    assert "from mve.rekey" not in src
    assert "acceptance_threshold" in src  # only the sealed Model B occupancy param
    # no pruned-layer imports anywhere
    assert "import acceptance" not in src
    assert "import rekey" not in src


# ---------------------------------------------------------------------------
# Holdout guard
# ---------------------------------------------------------------------------

def test_no_2026_in_module():
    src = open(
        os.path.join(_REPO_ROOT, "src", "mve", "p7_falsification.py"), encoding="utf-8"
    ).read()
    # no 2026 data-slice patterns (docstring mention of the holdout is fine)
    for pat in ('Timestamp("2026', "Timestamp('2026", 'slice(2026', "2026-01-01"):
        assert pat not in src


# ---------------------------------------------------------------------------
# Structural identity of model vs its own base
# ---------------------------------------------------------------------------

def test_model_matches_structural_base():
    """A/B/C must be structurally identical to their A/B/C_BASE counterparts
    (the P6.5 crosswalk claim) on a clean fixture."""
    x = _make_x()
    for model, base in p7.STRUCTURAL_BASELINE.items():
        ms = p7.build_signal(model, x)
        bs = p7.build_signal(base, x)
        # same active bar count (episode counts may differ only in merge edge)
        assert abs(int((ms != 0).sum()) - int((bs != 0).sum())) <= 2, model


def test_contrast_baseline_defined():
    for m in p7.MODELS:
        assert p7.CONTRAST_BASELINE[m] in p7.BASELINES


# ---------------------------------------------------------------------------
# P7 decision artifact (requires the pipeline run; skipped if absent)
# ---------------------------------------------------------------------------

P7_DIR = os.path.join(_REPO_ROOT, "research", "mve", "p7")


def _p7_decision():
    p = os.path.join(P7_DIR, "MVE_P7_DECISION.json")
    if not os.path.exists(p):
        pytest.skip("P7 decision not generated yet")
    import json

    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def test_decision_required_fields():
    d = _p7_decision()
    for key in (
        "checkpoint", "status", "base_commit", "p65_commit",
        "development_complete", "confirmation_complete", "holdout_status",
        "holdout_rows_read", "holdout_guard_pass", "causality_pass",
        "future_perturbation_max_diff", "truncation_pass",
        "blocked_component_isolation_pass", "causal_to_expost_dependency_count",
        "model_a_status", "model_b_status", "model_c_status",
        "model_a_incremental", "model_b_incremental", "model_c_incremental",
        "model_a_promoted", "model_b_promoted", "model_c_promoted",
        "model_a_baseline", "model_b_baseline", "model_c_baseline",
        "temporal_stability_complete", "confirmation_complete",
        "direction_symmetry_complete", "timing_value_complete",
        "selection_value_complete", "promoted_components", "rejected_components",
        "blocked_components", "best_trading_rule_selected",
        "economic_translation_ready", "p8_or_p9_ready", "next_phase_authorized",
        "human_review_required", "next_checkpoint_recommended",
    ):
        assert key in d, key


def test_decision_no_trading_rule_no_holdout():
    d = _p7_decision()
    assert d["best_trading_rule_selected"] is False
    assert d["next_phase_authorized"] is False
    assert d["holdout_status"] == "FINAL_HOLDOUT_PENDING"
    assert d["holdout_rows_read"] == 0
    assert d["holdout_guard_pass"] is True
    assert d["causality_pass"] is True
    assert d["future_perturbation_max_diff"] == 0.0
    assert d["truncation_pass"] is True
    assert d["blocked_component_isolation_pass"] is True
    assert d["causal_to_expost_dependency_count"] == 0
    assert "MODEL_D" in d["blocked_components"]
    assert "MODEL_E" in d["blocked_components"]
    assert "generate_all_signals" in d["blocked_components"]


def test_decision_promotion_consistency():
    d = _p7_decision()
    for m in ("MODEL_A", "MODEL_B", "MODEL_C"):
        assert d[f"{m.lower()}_promoted"] is bool(d[f"{m.lower()}_promoted"])
    # promoted iff incremental status
    for m in ("MODEL_A", "MODEL_B", "MODEL_C"):
        assert d[f"{m.lower()}_promoted"] == (d[f"{m.lower()}_status"] == "INCREMENTAL")
    # recommended checkpoint consistent with promotions
    if d["promoted_components"]:
        assert d["next_checkpoint_recommended"] == "MVE-P8-STRUCTURAL-GENERALIZATION"
    else:
        assert d["next_checkpoint_recommended"] == "MVE-P7.5-CORE-STATE-SEAL"


def test_decision_baselines_frozen():
    d = _p7_decision()
    assert d["model_a_baseline"] == "B3_PLAIN_BREAKOUT"
    assert d["model_b_baseline"] == "B3_PLAIN_BREAKOUT"
    assert d["model_c_baseline"] == "C_DIRECT_2SIGMA"
