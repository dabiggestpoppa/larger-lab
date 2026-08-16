"""P6.5 — Structural Pruning Seal tests.

These tests enforce the SEAL, not science:

- acceptance / RKEY-A / RKEY-B predictive roles remain pruned,
- RKEY-C is not promoted,
- Model D / Model E / generate_all_signals remain excluded,
- no P6.5 code reads 2026 (holdout untouched),
- the dependency graph is complete and every eligible model has a baseline,
- no science grid executes and no best-trading-rule is selected,
- P7 remains unauthorized.

They import only the P6.5 pipeline's builder functions (no heavy data load).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))
sys.path.insert(0, os.path.join(_REPO_ROOT, "research", "mve", "p65_tools"))

import run_p65  # noqa: E402


P65_DIR = os.path.join(_REPO_ROOT, "research", "mve", "p65")


def _load(name: str):
    with open(os.path.join(P65_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Pruning locks
# ---------------------------------------------------------------------------

def test_acceptance_pruned():
    lock = _load("MVE_P65_PRUNING_LOCK.json")
    assert lock["acceptance_predictive_layer"] == "PRUNED"
    assert "DESCRIPTIVE_ONLY" in lock["acceptance_role"]


def test_rkey_a_b_pruned():
    lock = _load("MVE_P65_PRUNING_LOCK.json")
    assert lock["rkey_a_predictive_layer"] == "PRUNED"
    assert lock["rkey_b_predictive_layer"] == "PRUNED"


def test_rkey_c_not_promoted():
    lock = _load("MVE_P65_PRUNING_LOCK.json")
    assert lock["rkey_c_predictive_layer"] == "INSUFFICIENT_N"
    disposition = open(os.path.join(P65_DIR, "MVE_P65_RKEY_C_DISPOSITION.md"), encoding="utf-8").read()
    assert "ARCHIVE_INSUFFICIENT_N" in disposition
    assert "not promoted to P7" in disposition


def test_rkey_state_maintenance_not_required():
    lock = _load("MVE_P65_PRUNING_LOCK.json")
    assert "NOT_REQUIRED" in lock["rkey_state_maintenance_role"]


# ---------------------------------------------------------------------------
# Blocked components
# ---------------------------------------------------------------------------

def test_model_d_excluded():
    status = _load("MVE_P65_BLOCKED_COMPONENT_STATUS.json")
    assert status["MODEL_D"]["status"] == "BLOCKED_LOGIC_SPEC"


def test_model_e_excluded():
    status = _load("MVE_P65_BLOCKED_COMPONENT_STATUS.json")
    assert status["MODEL_E"]["status"] == "BLOCKED_LOGIC_SPEC"


def test_generate_all_signals_blocked():
    status = _load("MVE_P65_BLOCKED_COMPONENT_STATUS.json")
    assert status["generate_all_signals"]["status"] == "BLOCKED_AGGREGATE"
    # mechanical evidence: the aggregate calls Model E
    assert status["generate_all_signals"]["reason"].find("generate_morphic_trend_score_signals") >= 0


def test_eligibility_blocks_d_e():
    import pandas as pd

    elig = pd.read_csv(os.path.join(P65_DIR, "MVE_P65_MODEL_ELIGIBILITY.csv"))
    for model in ("MODEL_D", "MODEL_E"):
        row = elig[elig["model"] == model].iloc[0]
        assert row["eligibility"] == "BLOCKED_LOGIC_SPEC"


# ---------------------------------------------------------------------------
# Dependency graph completeness
# ---------------------------------------------------------------------------

def test_dependency_graph_complete():
    graph = _load("MVE_P65_STRUCTURAL_DEPENDENCY_GRAPH.json")
    components = {n["component"] for n in graph["nodes"]}
    required = {
        "acceptance",
        "rekey/RKEY_A",
        "rekey/RKEY_B",
        "rekey/RKEY_C",
        "signals/model_A_escape",
        "signals/model_B_breakout",
        "signals/model_C_recursive",
        "signals/model_D_mtf",
        "signals/model_E_trend_score",
    }
    assert required <= components
    # every node must carry inputs and causal status
    for n in graph["nodes"]:
        assert n["causal_status"]
        assert isinstance(n["inputs"], list)


def test_models_consume_only_coordinates():
    import pandas as pd

    mat = pd.read_csv(os.path.join(P65_DIR, "MVE_P65_MODEL_INPUT_MATRIX.csv"))
    for model in ("MODEL_A", "MODEL_B", "MODEL_C"):
        rows = mat[mat["model"] == model]
        assert not rows.empty
        # no pruned/blocked dependency survives for A/B/C
        assert not rows["pruned_dependency"].any()
        assert not rows["blocked_dependency"].any()
        assert rows["survives_pruning"].all()


def test_every_eligible_model_has_baseline():
    import pandas as pd

    elig = pd.read_csv(os.path.join(P65_DIR, "MVE_P65_MODEL_ELIGIBILITY.csv"))
    cross = pd.read_csv(os.path.join(P65_DIR, "MVE_P65_BASELINE_CROSSWALK.csv"))
    eligible = set(elig[elig["eligibility"] == "ELIGIBLE_BUT_REDUCIBLE_BASELINE_REQUIRED"]["model"])
    baseline_models = set(cross["model"])
    assert eligible <= baseline_models
    for model in eligible:
        row = cross[cross["model"] == model].iloc[0]
        assert row["required_P7_baseline"] != "N/A"
        assert row["required_P7_baseline"]


# ---------------------------------------------------------------------------
# No science grid / no trading rule / P7 unauthorized
# ---------------------------------------------------------------------------

def test_decision_required_fields():
    d = _load("MVE_P65_DECISION.json")
    assert d["new_science_performed"] is False
    assert d["best_trading_rule_selected"] is False
    assert d["p7_authorized"] is False
    assert d["holdout_status"] == "FINAL_HOLDOUT_PENDING"
    assert d["holdout_rows_read"] == 0
    assert d["causality_nonregression_pass"] is True
    assert d["future_perturbation_max_diff"] == 0.0
    assert d["truncation_pass"] is True
    assert d["causal_to_expost_dependency_count"] == 0
    assert "MODEL_D" in d["blocked_components"]
    assert "MODEL_E" in d["blocked_components"]
    assert "generate_all_signals" in d["blocked_components"]


def test_p7_not_auto_authorized():
    d = _load("MVE_P65_DECISION.json")
    assert d["p7_authorized"] is False
    assert d["next_checkpoint_recommended"] == "MVE-P7-SIGNAL-MODEL-FALSIFICATION"


def test_no_science_grid_execution():
    """The pipeline writes no frozen-params/grid artifact (seal, not science)."""
    d = _load("MVE_P65_DECISION.json")
    assert d["new_science_performed"] is False
    assert not os.path.exists(os.path.join(P65_DIR, "MVE_P65_DEVELOPMENT_FROZEN_PARAMS.json"))


# ---------------------------------------------------------------------------
# Holdout / leakage guards
# ---------------------------------------------------------------------------

def test_no_2026_data_read():
    d = _load("MVE_P65_DECISION.json")
    assert d["holdout_rows_read"] == 0
    audit = _load("MVE_P65_CAUSALITY_NONREGRESSION.json")
    assert audit["6_holdout_guard"]["pass"] is True
    assert audit["6_holdout_guard"]["violations"] == []


def test_causality_nonregression_zero():
    audit = _load("MVE_P65_CAUSALITY_NONREGRESSION.json")
    assert audit["1_future_perturbation"]["all_zero"] is True
    assert audit["1_future_perturbation"]["max_diff"] == 0.0
    assert audit["2_truncation_invariance"]["all_zero"] is True
    assert audit["2_truncation_invariance"]["max_diff"] == 0.0
    assert audit["5_causal_to_expost_dependency"]["count"] == 0
    assert audit["3_blocked_component_isolation"]["models_D_E_consumed"] is False
    assert audit["3_blocked_component_isolation"]["generate_all_signals_consumed"] is False
    assert audit["4_static_leakage"]["blocked"] == []
    assert audit["4_static_leakage"]["pass"] is True


def test_leakage_scan_no_unknowns():
    audit = _load("MVE_P65_CAUSALITY_NONREGRESSION.json")
    findings = audit["4_static_leakage"]["findings"]
    for f in findings:
        assert f["classification"] in ("CAUSAL", "EX_POST_ONLY", "BLOCKED")


def test_bounded_nonregression_measured_models():
    audit = _load("MVE_P65_CAUSALITY_NONREGRESSION.json")
    measured = set(audit["1_future_perturbation"]["measured_models"])
    assert {"MODEL_A", "MODEL_B", "MODEL_C"} <= measured


# ---------------------------------------------------------------------------
# Builder-level unit tests (no data load)
# ---------------------------------------------------------------------------

def test_dependency_graph_builder():
    graph = run_p65.build_dependency_graph()
    assert graph["summary"]["total_nodes"] >= 14
    assert graph["summary"]["surviving_nodes"] > 0


def test_model_input_matrix_builder():
    graph = run_p65.build_dependency_graph()
    mat = run_p65.build_model_input_matrix(graph)
    assert set(mat["model"]) == set(run_p65.MODELS)


def test_baseline_crosswalk_covers_models():
    cross = run_p65.build_baseline_crosswalk()
    assert set(cross["model"]) == set(run_p65.MODELS)


def test_pruning_lock_consistent():
    lock = run_p65.build_pruning_lock()
    assert lock["acceptance_predictive_layer"] == "PRUNED"
    assert lock["rkey_c_predictive_layer"] == "INSUFFICIENT_N"


def test_signal_fn_contract():
    """The nonregression wrappers consume only the coordinate series."""
    import pandas as pd

    idx = pd.date_range("2023-01-01", periods=60, freq="h", tz="UTC")
    df = pd.DataFrame(
        {"x": np.sin(np.linspace(0, 6, 60)) * 1.5, "close": 1.0, "vol": 0.01},
        index=idx,
    )
    for model in ("MODEL_A", "MODEL_B", "MODEL_C"):
        fn = run_p65._signal_fn(model)
        out = fn(df)
        assert len(out) == len(df)
        assert set(out.unique()) <= {-1, 0, 1}
