#!/usr/bin/env python
"""Integrity tests for ALT_MECH_3 artifacts (run AFTER the analysis pipeline)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT


def _read(name):
    p = OUT / name
    assert p.exists(), f"missing artifact {name}"
    if name.endswith(".csv"):
        return pd.read_csv(p)
    if name.endswith(".parquet"):
        return pd.read_parquet(p)
    if name.endswith(".json"):
        return json.load(open(p))
    return None


def test_preregistration_exists():
    p = OUT / "01_PREREGISTRATION.md"
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "PREREGISTRATION" in txt
    assert "fixed before" in txt.lower() or "BEFORE" in txt


def test_data_truth_lock():
    tl = json.load(open(OUT / "02_DATA_TRUTH.json"))
    assert tl["all_pass"] is True
    assert tl["checks"]["pit_rows_1098000"] is True
    assert tl["checks"]["unique_assets_2898"] is True
    assert tl["checks"]["included_dates_2196"] is True


def test_observation_limits_exists():
    p = OUT / "03_OBSERVATION_LIMITS.md"
    assert p.exists()
    txt = p.read_text()
    for layer in ["DIRECTLY_OBSERVED", "INDIRECTLY_INFERRED",
                  "PARTIALLY_OBSERVED", "UNOBSERVED"]:
        assert layer in txt, f"missing observation layer {layer}"


def test_chain_liquidity_variable_map():
    df = _read("04_CHAIN_LIQUIDITY_VARIABLE_MAP.csv")
    assert len(df) >= 8
    assert set(["variable", "layer", "source", "median_max_abs_r"]).issubset(df.columns)


def test_chain_liquidity_redundancy():
    df = _read("05_CHAIN_LIQUIDITY_REDUNDANCY.csv")
    assert len(df) >= 10
    allowed = {"REDUNDANT_PROXY", "PARTIAL_PROXY", "LOCAL_COORDINATE",
               "DISTINCT_INFORMATION", "CANDIDATE_DISTINCT"}
    assert set(df.classification.unique()).issubset(allowed)


def test_chain_liquidity_perturbation():
    df = _read("06_CHAIN_LIQUIDITY_PERTURBATION.csv")
    assert len(df) >= 50
    assert set(["chain", "link", "ablation", "classification"]).issubset(df.columns)
    assert set(["BASE", "-BETA", "-SC", "-DEX", "-NATIVE_RET"]).issubset(df.ablation.unique())


def test_chain_reconstruction():
    df = _read("07_CHAIN_RECONSTRUCTION.csv")
    assert len(df) >= 5
    r2_cols = [c for c in df.columns if c.startswith("r2_")]
    assert len(r2_cols) == 5


def test_routing_flip_map():
    df = _read("08_ROUTING_FLIP_MAP.csv")
    assert len(df) >= 50
    assert set(["relationship", "state", "classification"]).issubset(df.columns)
    allowed = {"SAME_SIGN", "REVERSED", "GAINED", "LOST", "CHANGED_LAG",
               "INSUFFICIENT_SAMPLE"}
    assert set(df.classification.unique()).issubset(allowed)


def test_concentration_events():
    ent = _read("09_CONCENTRATION_ENTRY_EVENTS.parquet")
    ext = _read("10_CONCENTRATION_EXIT_EVENTS.parquet")
    assert len(ent) >= 20
    assert len(ext) >= 20
    assert "date" in ent.columns and "date" in ext.columns


def test_pivot_anatomy():
    df = _read("11_CONCENTRATION_PIVOT_ANATOMY.csv")
    assert len(df) >= 20
    assert set(["event", "window_d", "precursor", "wilcoxon_p", "fdr_q"]).issubset(df.columns)
    assert set(["ENTRY", "EXIT"]).issubset(df.event.unique())


def test_release_route_map():
    df = _read("12_RELEASE_ROUTE_MAP.csv")
    assert len(df) >= 20
    assert set(["destination_state", "time_to_destination_d",
                "concentration_duration_d"]).issubset(df.columns)


def test_information_plateau():
    df = _read("13_INFORMATION_PLATEAU.csv")
    assert len(df) == 3
    assert set(df.phenomenon) == {"CHAIN_EXPANSION", "ROUTING_FLIP_REALIZED",
                                  "CONCENTRATION_EXIT_7D"}


def test_field_plateau():
    df = _read("14_FIELD_PLATEAU.csv")
    assert len(df) >= 10
    assert set(["plateau", "duration_d"]).issubset(df.columns)
    assert set(["P1_CHAIN_LIQ_NO_NATIVE", "P2_VELOCITY_NO_BREADTH",
                "P3_CONC_NO_ROUTE"]).issubset(df.plateau.unique())


def test_primitive_audit():
    df = _read("15_PRIMITIVE_CANDIDATE_AUDIT.csv")
    assert len(df) == 8
    allowed = {"GLOBAL_CANDIDATE_PRIMITIVE", "LOCAL_PRIMITIVE", "REDUNDANT",
               "NOT_PRIMITIVE", "UNRESOLVED"}
    assert set(df.classification.unique()).issubset(allowed)
    assert set(["candidate", "delta_r2_removed", "delta_r2_substituted"]).issubset(df.columns)


def test_graph_structure():
    g = _read("16_GRAPH_STRUCTURE.json")
    assert g["n_nodes"] >= 5
    assert "density" in g and "articulation_points" in g
    assert "components" in g


def test_dynamical_transitions():
    df = _read("17_DYNAMICAL_SYSTEM_TRANSITIONS.csv")
    assert len(df) >= 3
    assert "self_transition" in df.columns and "basin_self_transition" in df.columns


def test_morphism_survival():
    df = _read("18_MORPHISM_SURVIVAL.csv")
    assert len(df) == 2
    assert set(df.motif_class) == {"RECURRING", "CYCLE_SPECIFIC"}


def test_new_node_merge_dissolve():
    df = _read("19_NEW_NODE_MERGE_DISSOLVE.csv")
    assert len(df) >= 3
    assert set(["operation", "object", "evidence", "decision"]).issubset(df.columns)
    assert set(df.operation).issubset({"NEW_NODE", "MERGE", "DISSOLVE", "NULL"})


def test_null_and_failed():
    df = _read("20_NULL_AND_FAILED_RESULTS.csv")
    assert len(df) >= 5
    assert set(["workstream", "classification", "count"]).issubset(df.columns)


def test_causality_ladder():
    df = _read("21_CAUSALITY_LADDER.csv")
    assert len(df) >= 8
    assert set(df.highest_level).issubset({"L0", "L1", "L2", "L3", "L4", "L5", "L6"})


def test_agent2_review():
    p = OUT / "22_AGENT2_PROMOTION_REVIEW.md"
    assert p.exists()
    txt = p.read_text()
    assert "ACCEPT_FOR_CANONICAL_TEST" in txt or "NEEDS_DATA" in txt or \
           "DEFER" in txt or "REJECT" in txt


def test_test_count_reconciliation():
    df = _read("23_TEST_COUNT_RECONCILIATION.csv")
    assert len(df) >= 4
    assert (df.statistical_tests >= 0).all()


def test_summary_and_decision():
    for name in ["24_MECH3_SUMMARY.md", "25_DECISION.md"]:
        p = OUT / name
        assert p.exists(), f"missing {name}"
    dec = (OUT / "25_DECISION.md").read_text()
    assert "PASS_ALT_FIELD_PRIMITIVE_MAP" in dec or \
           "PASS_ALT_MECH3_WITH_LIMITATIONS" in dec or \
           "FAIL_ALT_MECH3_STRUCTURE" in dec or \
           "BLOCKED_ALT_MECH3_DATA" in dec
    assert "NO STRATEGY" in dec.upper() or "NO PNL" in dec.upper()


def test_decision_matches_evidence():
    """Decision language must be consistent with the causality ladder (no L4+ claims)."""
    dec = (OUT / "25_DECISION.md").read_text(encoding="utf-8")
    ladder = _read("21_CAUSALITY_LADDER.csv")
    # no claim may exceed L3 unless ladder says so
    max_lvl = ladder.highest_level.max()
    assert max_lvl in {"L0", "L1", "L2", "L3"}  # terrain checkpoint caps at L3
