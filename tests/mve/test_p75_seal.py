"""MVE-P7.5-CORE-STATE-SEAL tests.

Seal checkpoint tests: the core-state wrapper must be a deterministic,
causal reproduction of the sealed P7 pipeline field, must consume NO pruned
or blocked science, must never touch 2026, and must contain no strategy/PnL
logic.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mve import core_state  # noqa: E402
import mve.p4_acceptance as pa  # noqa: E402
from mve.volatility import VolatilityEstimators  # noqa: E402
from mve.causality import future_perturbation_check, truncation_check  # noqa: E402

P75_DIR = os.path.join(REPO_ROOT, "research", "mve", "p75")
PERTURB_SEED = 701


def _synthetic_h1(n: int = 240, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-07-03", periods=n, freq="h", tz="UTC")
    close = 1.08 + np.cumsum(rng.normal(0, 0.0003, n))
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 0.0005,
            "low": close - 0.0005,
            "close": close,
            "volume": rng.integers(100, 900, n),
        },
        index=idx,
    )


def _sealed_reference(h1: pd.DataFrame) -> dict:
    """Reproduce the sealed P7 field construction on a synthetic frame."""
    vol = VolatilityEstimators().calculate_all_estimators(
        h1["close"], h1["high"], h1["low"], h1["volume"]
    )["close_to_close"].astype(float)
    trail_hi = (
        h1["close"]
        .rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS)
        .max()
        .shift(1)
    )
    trail_lo = (
        h1["close"]
        .rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS)
        .min()
        .shift(1)
    )
    coord = pa.coordinate_fields(h1, trail_hi, trail_lo, vol)
    sig = pa.per_boundary_signals(coord, 1.0, 1.0)
    return {"vol": vol, "trail_hi": trail_hi.astype(float), "trail_lo": trail_lo.astype(float), "x": sig["x"].astype(float)}


def _ref_sigma(x: pd.Series) -> pd.Series:
    xv = x.to_numpy(dtype=float)
    out = np.full(len(xv), np.nan, dtype=float)
    for i in range(len(xv)):
        xi = xv[i]
        if np.isnan(xi):
            continue
        s = np.sign(xi) * np.floor(abs(xi) / core_state.STEP)
        out[i] = s if s != 0 else 0.0
    return pd.Series(out, index=x.index)


def _src() -> str:
    with open(core_state.__file__, encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# schema
# --------------------------------------------------------------------------

def test_core_state_schema_complete():
    h1 = _synthetic_h1()
    cs = core_state.build_core_state(h1)
    for field in core_state.CORE_STATE_SCHEMA:
        assert field in cs.columns, f"missing schema field {field}"
    assert len(cs) == len(h1)


def test_core_state_known_time_is_index():
    cs = core_state.build_core_state(_synthetic_h1())
    assert (cs["causal_known_time"] == cs.index).all()
    assert (cs["timestamp"] == cs.index).all()


# --------------------------------------------------------------------------
# parity vs sealed pipeline
# --------------------------------------------------------------------------

def test_parity_anchor_vol_coord_sigma():
    h1 = _synthetic_h1(n=400, seed=5)
    ref = _sealed_reference(h1)
    cs = core_state.build_core_state(h1)

    def _diff(a: pd.Series, b: pd.Series) -> float:
        m = a.notna() & b.notna()
        assert m.any(), "no overlapping valid rows for parity"
        return float((a[m] - b[m]).abs().max())

    assert _diff(cs["anchor_up"], ref["trail_hi"]) <= 1e-9
    assert _diff(cs["anchor_lo"], ref["trail_lo"]) <= 1e-9
    assert _diff(cs["volatility_estimate"], ref["vol"]) <= 1e-9
    assert _diff(cs["coordinate"], ref["x"]) <= 1e-9
    assert _diff(cs["sigma_state"], _ref_sigma(ref["x"])) <= 1e-9
    assert _diff(cs["sigma_band"], pd.Series(np.floor(np.abs(ref["x"].to_numpy())), index=ref["x"].index)) <= 1e-9


def test_core_state_deterministic():
    h1 = _synthetic_h1()
    a = core_state.build_core_state(h1)
    b = core_state.build_core_state(h1)
    pd.testing.assert_frame_equal(a, b)


# --------------------------------------------------------------------------
# causality: future perturbation + truncation
# --------------------------------------------------------------------------

def test_future_perturbation_zero():
    h1 = _synthetic_h1(n=240)
    data = h1[["open", "high", "low", "close", "volume"]].copy()
    t = len(data) // 2
    for col in ("coordinate", "sigma_state", "anchor_up", "volatility_estimate"):
        def fn(dd: pd.DataFrame, _c=col) -> pd.Series:
            return core_state.build_core_state(dd)[_c]
        diff = future_perturbation_check(fn, data, t, seed=PERTURB_SEED)
        assert diff == 0.0, f"{col}: future perturbation diff {diff}"


def test_truncation_zero():
    h1 = _synthetic_h1(n=240)
    data = h1[["open", "high", "low", "close", "volume"]].copy()
    t = len(data) // 2
    for col in ("coordinate", "sigma_state", "anchor_up", "volatility_estimate"):
        def fn(dd: pd.DataFrame, _c=col) -> pd.Series:
            return core_state.build_core_state(dd)[_c]
        diff = truncation_check(fn, data, t)
        assert diff == 0.0, f"{col}: truncation diff {diff}"


# --------------------------------------------------------------------------
# exclusion locks
# --------------------------------------------------------------------------

def test_acceptance_science_excluded():
    src = _src()
    for tok in ("detect_acceptance_episodes", "acceptance_known_series", "measure_outcomes", "measure_failed_outcomes"):
        assert tok not in src, f"core_state.py must not reference pruned acceptance science: {tok}"


def test_rekey_predictive_excluded():
    # exclusion is code-level: no import of the rekey module, no call into it
    src = _src()
    assert "mve.p6_rekey" not in src
    assert "from mve.p6_rekey" not in src
    assert "def rekey" not in src
    assert "rekey_episode" not in src
    assert "new_anchor" not in src


def test_models_abc_excluded():
    src = _src()
    assert "mve.signals" not in src, "core_state.py must not import signals (Models A-E)"
    assert "from mve.signals" not in src
    # code-level: no signal-builder call or import of the model wrappers
    assert "build_signal" not in src
    assert "MODEL_A" not in src and "MODEL_B" not in src and "MODEL_C" not in src


def test_models_d_e_and_aggregate_excluded():
    src = _src()
    assert "MODEL_D" not in src and "MODEL_E" not in src
    assert "generate_all_signals" not in src


def test_no_strategy_or_pnl_logic():
    src = _src()
    # code-level strategy/PnL primitives (prose docstring is descriptive)
    for tok in ("backtest", "stop_loss", "take_profit", "position_size", "kelly", "entry_price", "def entry", "def exit", "sizing"):
        assert tok not in src.lower(), f"core_state.py must not contain strategy/PnL logic: {tok}"


# --------------------------------------------------------------------------
# holdout guard
# --------------------------------------------------------------------------

def test_holdout_guard_artifact():
    path = os.path.join(P75_DIR, "MVE_P75_HOLDOUT_GUARD.json")
    if not os.path.exists(path):
        pytest.skip("P7.5 artifacts not generated yet")
    with open(path, encoding="utf-8") as fh:
        guard = json.load(fh)
    assert guard["status"] == "FINAL_HOLDOUT_PENDING"
    assert guard["rows_read"] == 0
    assert guard["rows_2026_in_field"] == 0
    assert guard["guard_pass"] is True


def test_pipeline_truncates_before_computation():
    # run_p75.py must truncate the field at 2025-12-31 before building the
    # core state (2026 never read).
    rp = os.path.join(REPO_ROOT, "research", "mve", "p75_tools", "run_p75.py")
    with open(rp, encoding="utf-8") as fh:
        src = fh.read()
    trunc_line = 'h1.loc[h1.index <= pd.Timestamp(CONF_END, tz="UTC")]'
    assert trunc_line in src
    assert src.index("CONF_END") < src.index("core_state.build_core_state")


# --------------------------------------------------------------------------
# registry / decision integrity
# --------------------------------------------------------------------------

def test_falsification_registry_integrity():
    path = os.path.join(P75_DIR, "MVE_P75_FALSIFICATION_REGISTRY.csv")
    if not os.path.exists(path):
        pytest.skip("P7.5 artifacts not generated yet")
    reg = pd.read_csv(path)
    assert len(reg) == 9
    status = dict(zip(reg["component"], reg["status"]))
    assert status["P4 acceptance (all variants)"] == "REJECTED_REDUNDANT"
    assert status["RKEY-A"] == "REJECTED_REDUNDANT"
    assert status["RKEY-B"] == "REJECTED_REDUNDANT"
    assert status["RKEY-C"] == "ARCHIVED_INSUFFICIENT_N"
    assert status["Model A"] == "REJECTED_REDUNDANT"
    assert status["Model B"] == "REJECTED_REDUNDANT"
    assert status["Model C"] == "ARCHIVED_CONDITIONAL_NOT_INCREMENTAL"
    assert status["Model D"] == "BLOCKED_LOGIC_SPEC"
    assert status["Model E"] == "BLOCKED_LOGIC_SPEC"
    assert reg["reopen_condition"].notna().all()


def test_decision_no_promotion_flags():
    path = os.path.join(P75_DIR, "MVE_P75_DECISION.json")
    if not os.path.exists(path):
        pytest.skip("P7.5 artifacts not generated yet")
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    assert d["predictive_alpha_validated"] is False
    assert d["standalone_strategy_validated"] is False
    assert d["economic_translation_ready"] is False
    assert d["new_science_performed"] is False
    assert d["best_trading_rule_selected"] is False
    assert d["p8_authorized"] is False
    assert d["holdout_status"] == "FINAL_HOLDOUT_PENDING"
    assert d["holdout_rows_read"] == 0
    assert d["mve_p75_core_state_seal_pass"] is True


def test_parity_artifact():
    path = os.path.join(P75_DIR, "MVE_P75_CORE_PARITY.json")
    if not os.path.exists(path):
        pytest.skip("P7.5 artifacts not generated yet")
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    assert p["pass"] is True
    assert p["max_diff"] == 0.0
    assert set(p["checks"]) == {"anchor_up", "anchor_lo", "volatility", "coordinate", "sigma_state", "sigma_band"}


def test_causality_audit_artifact():
    path = os.path.join(P75_DIR, "MVE_P75_CAUSALITY_AUDIT.json")
    if not os.path.exists(path):
        pytest.skip("P7.5 artifacts not generated yet")
    with open(path, encoding="utf-8") as fh:
        a = json.load(fh)
    assert a["1_future_perturbation"]["all_zero"] is True
    assert a["2_truncation_invariance"]["all_zero"] is True
    assert a["4_blocked_component_isolation"]["pass"] is True
    assert len(a["5_static_leakage"]["blocked"]) == 0
    assert a["6_causal_to_expost_dependency"]["count"] == 0
