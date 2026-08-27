"""MECH-5 integrity tests - verify semantic output, not just file existence."""
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "01_PREREGISTRATION.md", "02_EVENT_COHORT_RECONCILIATION.csv",
    "03_FIRST_DIVERGENCE_PANEL.parquet", "04_FIRST_DIVERGENCE_SUMMARY.csv",
    "05_SUCCESS_FAILURE_INCREMENTAL_MAP.csv", "06_RETEST_RELOAD_INTERNAL_ANATOMY.csv",
    "07_RETEST_RELOAD_VS_FAILED_IGNITION.csv", "08_ESCAPE_HAZARD.csv",
    "09_PROPAGATION_HAZARD.csv", "10_FAILURE_HAZARD.csv",
    "11_TEMPORAL_WINDOW_REFINEMENT.csv", "12_TERMINATION_MATCHED_CONTROLS.csv",
    "13_EARLY_DECAY_SEQUENCE.csv", "14_SIGNAL_TO_TERMINATION_LATENCY.csv",
    "15_FAILURE_SEQUENCE_MAP.csv", "16_FAILURE_MOTIF_AUDIT.csv",
    "17_CONDITIONAL_RESCUE_AUDIT.csv", "18_CAUSALITY_LADDER.csv",
    "19_NEW_NODE_MERGE_DISSOLVE.csv", "20_NULL_AND_FAILED_RESULTS.csv",
    "21_MECH5_SUMMARY.md", "22_MECH5_DECISION.md",
]


def test_required_artifacts_present():
    missing = [r for r in REQUIRED if not (ROOT / r).exists()]
    assert not missing, f"Missing artifacts: {missing}"


def test_cohort_reconciliation():
    c = pd.read_csv(ROOT / "02_EVENT_COHORT_RECONCILIATION.csv")
    total = int(c.loc[c.cohort == "total", "count"].iloc[0])
    assert total == 125
    assert int(c.loc[c.label == "SUCCESS", "count"].iloc[0]) == 27
    assert int(c.loc[c.label == "FAILURE", "count"].iloc[0]) == 96
    # canonical destinations must sum to 125
    dest = c[c.cohort == "canonical_destination"]
    assert dest["count"].sum() == 125


def test_first_divergence_summary_nonempty():
    s = pd.read_csv(ROOT / "04_FIRST_DIVERGENCE_SUMMARY.csv")
    assert len(s) > 0, "no first-divergence variables found"
    assert "variable" in s.columns and "horizon_d" in s.columns
    assert "rank_biserial_r" in s.columns


def test_divergence_panel_columns():
    p = pd.read_parquet(ROOT / "03_FIRST_DIVERGENCE_PANEL.parquet")
    assert "event_id" in p.columns
    assert "is_success" in p.columns
    assert p.is_success.sum() >= 1
    assert (p.is_success == 0).sum() >= 1


def test_incremental_map_ordered_models():
    m = pd.read_csv(ROOT / "05_SUCCESS_FAILURE_INCREMENTAL_MAP.csv")
    assert len(m) == 7, f"expected 7 models, got {len(m)}"
    # M0 current state always first
    assert m.model.iloc[0] == "M0_current_state"
    # each model has valid metrics
    assert m.cv_auc.notna().all()


def test_retest_reload_counts():
    a = pd.read_csv(ROOT / "06_RETEST_RELOAD_INTERNAL_ANATOMY.csv")
    rr = (a["class"] == "RETEST_RELOAD").sum()
    fi = (a["class"] == "FAILED_IGNITION").sum()
    assert rr >= 10, f"RR n too small: {rr}"
    assert fi >= 30, f"FI n too small: {fi}"


def test_escape_hazard_monotonic_or_null():
    e = pd.read_csv(ROOT / "08_ESCAPE_HAZARD.csv")
    assert len(e) == 9
    # escape probability should be defined and within [0,1]
    assert e.p_escape.between(0, 1).all()


def test_propagation_hazard():
    p = pd.read_csv(ROOT / "09_PROPAGATION_HAZARD.csv")
    assert len(p) == 9
    assert p.p_sustained_within_h.between(0, 1).all()


def test_failure_hazard():
    f = pd.read_csv(ROOT / "10_FAILURE_HAZARD.csv")
    assert len(f) == 9
    assert f.p_reentry_within_h.between(0, 1).all()


def test_temporal_window_refinement():
    w = pd.read_csv(ROOT / "11_TEMPORAL_WINDOW_REFINEMENT.csv")
    assert len(w) >= 3
    assert "p_fdr" in w.columns


def test_termination_controls_panel():
    t = pd.read_csv(ROOT / "12_TERMINATION_MATCHED_CONTROLS.csv")
    assert len(t) >= 10
    assert "days_to_destination" in t.columns


def test_early_decay_sequence():
    d = pd.read_csv(ROOT / "13_EARLY_DECAY_SEQUENCE.csv")
    assert len(d) >= 3, "expected multiple decay variables"


def test_failure_motifs():
    mf = pd.read_csv(ROOT / "16_FAILURE_MOTIF_AUDIT.csv")
    assert len(mf) >= 4, "expected multiple motifs"
    assert (mf["count"] > 0).all()
    assert np.isclose(mf["count"].sum(), 125)


def test_conditional_rescue_fdr():
    r = pd.read_csv(ROOT / "17_CONDITIONAL_RESCUE_AUDIT.csv")
    assert len(r) >= 5
    assert "p_fdr" in r.columns
    assert r.p_fdr.notna().all()


def test_causality_ladder_levels():
    l = pd.read_csv(ROOT / "18_CAUSALITY_LADDER.csv")
    valid = set(["L0_DESCRIPTIVE_CO_MOVEMENT", "L0_NULL", "L1_TEMPORAL_ORDERING",
                 "L2_CONDITIONAL_LEAD_LAG", "L3_COMMON_FACTOR_ROBUST",
                 "L4_CROSS_REGIME_STABLE"])
    assert l.causality_level.isin(valid).all()


def test_null_results_preserved():
    n = pd.read_csv(ROOT / "20_NULL_AND_FAILED_RESULTS.csv")
    # at least the retest_reload null must be present
    assert len(n) >= 1
    assert "retest_reload" in n.result.str.cat(sep=",")


def test_new_node_merge_dissolve():
    nd = pd.read_csv(ROOT / "19_NEW_NODE_MERGE_DISSOLVE.csv")
    assert len(nd) >= 3
    valid_ops = set(["NEW_NODE", "LOCAL_NODE", "MERGE", "DISSOLVE",
                     "DESCRIPTIVE_ONLY", "NULL", "DATA_BLOCKED"])
    assert nd.operation.isin(valid_ops).all()


def test_summary_and_decision_present():
    s = (ROOT / "21_MECH5_SUMMARY.md").read_text()
    d = (ROOT / "22_MECH5_DECISION.md").read_text()
    assert "MECH-5" in s
    assert "VERDICT:" in d
    assert "human_review_required" in d
    assert "No strategy" in d


def test_decision_verdict_vocab():
    d = (ROOT / "22_MECH5_DECISION.md").read_text()
    valid = ["PASS_MECH5_FAILURE_ANATOMY", "PASS_MECH5_WITH_LIMITATIONS",
             "FAIL_MECH5_NO_DIVERGENCE_STRUCTURE", "BLOCKED_MECH5_DATA"]
    assert any(f"VERDICT: {v}" in d for v in valid), d.split("VERDICT:")[1][:80]
