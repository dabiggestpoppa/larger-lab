import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT


def _read(name):
    return pd.read_csv(OUT / name)


# ---------------------------------------------------------------------------
# Artifact presence (all 23 required files + verdicts)
# ---------------------------------------------------------------------------

REQUIRED = [
    "01_PREREGISTRATION.md",
    "02_FULL_STATE_LIFECYCLE.csv",
    "03_STATE_FAILURE_GEOMETRY.csv",
    "04_BROAD_SEQUENCE_ATLAS.csv",
    "05_PARTIAL_ORDER_EDGES.csv",
    "06_CONSTRAINT_GRAPH.md",
    "07_SEQUENCE_PREFIX_BRANCHING.csv",
    "08_CONSTRAINT_RESOLUTION_ENTROPY.csv",
    "09_WATERFALL_THRESHOLD_HIERARCHY.csv",
    "10_RANK_PATCH_GRAPH_NODES.csv",
    "11_RANK_PATCH_GRAPH_EDGES.csv",
    "12_PATCH_PERTURBATION_RESPONSE.csv",
    "13_PEER_FORMATION_FIELD_CONTEXT.csv",
    "14_METASTABILITY_AUDIT.csv",
    "15_TRANSFER_FLOW_PILOT.csv",
    "16_LONER_FIELD_PLACEMENT.csv",
    "17_ABSOLUTE_VS_SIGMA_AMPLITUDE.csv",
    "18_DIRECTIONAL_ASYMMETRY_FIELD.csv",
    "19_POTENTIAL_REALIZATION_REVISIT.csv",
    "20_PROMOTE_MERGE_DISSOLVE.csv",
    "21_NULL_AND_FAILED_RESULTS.csv",
    "22_CANONICAL_FIELD_MAP_UPDATE.csv",
    "23_MECH12_SUMMARY.md",
    "24_MECH12_DECISION.md",
]


@pytest.mark.parametrize("name", REQUIRED)
def test_required_artifacts_exist(name):
    assert (OUT / name).exists(), f"missing {name}"


def test_verdicts_json():
    v = json.loads((OUT / "_verdicts.json").read_text(encoding="utf-8"))
    assert v["checkpoint"] == "MECH-12"
    assert v["human_review_required"] is True
    assert v["next_checkpoint_authorized"] is False
    assert "PASS_MECH12" in v["verdict"]


# ---------------------------------------------------------------------------
# WS1: full lifecycle semantics
# ---------------------------------------------------------------------------

def test_ws1_schema_and_ranges():
    df = _read("02_FULL_STATE_LIFECYCLE.csv")
    assert {"cell", "age_band", "horizon_d", "p_stay", "p_exit",
            "p_reentry", "p_propagate", "p_tail_activation",
            "p_rank_recruitment", "p_local_stress",
            "p_local_recovery"}.issubset(df.columns)
    assert set(df["cell"]).issubset({"HIGH_BREADTH_HIGH_DISP",
                                     "HIGH_BREADTH_LOW_DISP",
                                     "LOW_BREADTH_HIGH_DISP",
                                     "LOW_BREADTH_LOW_DISP"})
    probs = ["p_stay", "p_exit", "p_reentry", "p_propagate",
             "p_tail_activation", "p_rank_recruitment",
             "p_local_stress", "p_local_recovery"]
    for c in probs:
        assert df[c].between(-0.001, 1.001).all(), f"{c} out of [0,1]"
    assert df["n_days"].min() >= 20


def test_ws1_hh_maturity_gradient():
    """MECH-10/11 earned: HH propagation RISES with age, reentry FALLS."""
    df = _read("02_FULL_STATE_LIFECYCLE.csv")
    hh = df[(df["cell"] == "HIGH_BREADTH_HIGH_DISP") &
            (df["horizon_d"] == 7)].sort_values("age_band")
    # age bands ordered AGE_1 < AGE_2_3 < AGE_4_7 < AGE_8_14 < AGE_15_PLUS
    order = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]
    hh = hh.set_index("age_band").reindex(order).dropna()
    assert len(hh) >= 4
    assert hh["p_propagate"].iloc[-1] > hh["p_propagate"].iloc[0] + 0.1
    assert hh["p_reentry"].iloc[-1] < hh["p_reentry"].iloc[0] - 0.1


def test_ws1_transition_columns():
    df = _read("02_FULL_STATE_LIFECYCLE.csv")
    for t in ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
              "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]:
        assert f"p_trans_{t}" in df.columns


# ---------------------------------------------------------------------------
# WS2: failure geometry semantics
# ---------------------------------------------------------------------------

def test_ws2_verdicts_valid():
    df = _read("03_STATE_FAILURE_GEOMETRY.csv")
    assert len(df) >= 2
    assert set(df["verdict"]).issubset({"DIFFERENT_AT_BIRTH",
                                        "DIVERGES_EARLY",
                                        "DIVERGES_LATE",
                                        "NO_STABLE_SEPARATION"})
    assert df["first_lag_d"].isin([0, 1, 3, 7]).all()


# ---------------------------------------------------------------------------
# WS3: broad sequence atlas
# ---------------------------------------------------------------------------

def test_ws3_classification_rules():
    df = _read("04_BROAD_SEQUENCE_ATLAS.csv")
    assert {"sequence", "count", "lift", "q", "n_subperiods",
            "status"}.issubset(df.columns)
    assert set(df["status"]).issubset({"COMMON_SEQUENCE", "LOCAL_SEQUENCE",
                                       "RARE_SEQUENCE", "NULL_SEQUENCE"})
    com = df[df["status"] == "COMMON_SEQUENCE"]
    if len(com):
        assert (com["count"] >= 50).all()
        assert (com["n_subperiods"] >= 3).all()
        assert (com["q"] <= 0.10).all()
    # no sequence may be self-contradictory: count >= 1
    assert (df["count"] >= 1).all()


# ---------------------------------------------------------------------------
# WS4: partial-order edges
# ---------------------------------------------------------------------------

def test_ws4_edge_classes():
    df = _read("05_PARTIAL_ORDER_EDGES.csv")
    assert len(df) >= 50
    assert set(df["edge_class"]).issubset({"REQUIRED_ORDER",
                                           "PREFERRED_ORDER",
                                           "EXCHANGEABLE", "NO_ORDER"})
    # probabilities sum ~ 1
    tot = df["p_A_before_B"] + df["p_B_before_A"] + df["p_same_window"]
    assert np.allclose(tot, 1.0, atol=1e-6)
    req = df[df["edge_class"] == "REQUIRED_ORDER"]
    if len(req):
        assert (req["n_both"] >= 50).all()
        assert (req["n_subperiods"] >= 3).all()
        assert (req["preferred_p"] >= 0.60).all()


def test_ws4_constraint_graph_md():
    txt = (OUT / "06_CONSTRAINT_GRAPH.md").read_text(encoding="utf-8")
    assert "REQUIRED_ORDER" in txt
    assert "PREFERRED_ORDER" in txt


# ---------------------------------------------------------------------------
# WS5/6: prefix branching + entropy
# ---------------------------------------------------------------------------

def test_ws5_prefix_branching():
    df = _read("07_SEQUENCE_PREFIX_BRANCHING.csv")
    assert len(df) >= 3
    assert (df["branch_entropy"] >= 0).all()
    assert (df["dominant_share"] > 0).all()


def test_ws6_entropy_verdict():
    df = _read("08_CONSTRAINT_RESOLUTION_ENTROPY.csv")
    summ = df[df["scope"].isna()]
    assert len(summ) == 1
    assert summ["verdict"].iloc[0] in {"ENTROPY_COLLAPSE",
                                       "LOCAL_ENTROPY_COLLAPSE",
                                       "NO_STABLE_COLLAPSE",
                                       "INCONCLUSIVE"}
    # cell_age rows must exist for all 4 cells
    ca = df[df["scope"] == "cell_age"]
    assert ca["cell"].nunique() == 4


# ---------------------------------------------------------------------------
# WS7: waterfall threshold hierarchy
# ---------------------------------------------------------------------------

def test_ws7_waterfall():
    df = _read("09_WATERFALL_THRESHOLD_HIERARCHY.csv")
    assert len(df) >= 7
    assert df["verdict"].iloc[0] in {"THRESHOLD_HIERARCHY_EARNED",
                                     "INVERSE_HIERARCHY",
                                     "FLAT_THRESHOLDS",
                                     "DATA_BLOCKED"}
    assert (df["n_episodes"] >= 50).all()


# ---------------------------------------------------------------------------
# WS8: rank-patch graph
# ---------------------------------------------------------------------------

def test_ws8_nodes_edges():
    nodes = _read("10_RANK_PATCH_GRAPH_NODES.csv")
    edges = _read("11_RANK_PATCH_GRAPH_EDGES.csv")
    assert len(nodes) >= 4
    assert {"patch", "internal_coherence", "false_loner_rate",
            "tail_share"}.issubset(nodes.columns)
    assert len(edges) >= 4
    assert {"patch_a", "patch_b", "same_day_spearman"}.issubset(
        edges.columns)
    # coherence should be high (patches are internally coherent per M11)
    assert nodes["internal_coherence"].mean() > 0.9


# ---------------------------------------------------------------------------
# WS9: patch perturbation response
# ---------------------------------------------------------------------------

def test_ws9_patch_perturbation():
    df = _read("12_PATCH_PERTURBATION_RESPONSE.csv")
    assert len(df) >= 20
    assert {"patch", "perturbation", "amplitude",
            "activation_prob_3d"}.issubset(df.columns)
    assert set(df["amplitude"]).issubset({"SMALL", "MEDIUM", "LARGE"})
    assert set(df["perturbation"]).issubset(
        {"brd_jump", "brd_drop", "disp_jump", "disp_drop", "btc_shock",
         "conc_shock", "vol_shock"})


# ---------------------------------------------------------------------------
# WS10: peer formation context
# ---------------------------------------------------------------------------

def test_ws10_peer_formation():
    df = _read("13_PEER_FORMATION_FIELD_CONTEXT.csv")
    assert len(df) >= 3
    assert "path_class" in df.columns
    assert df["verdict"].iloc[0] in {"FIELD_CONTEXT_DISTINCT",
                                     "FIELD_CONTEXT_FLAT",
                                     "DATA_LIMITED"}


# ---------------------------------------------------------------------------
# WS11/12: metastability + transfer flow
# ---------------------------------------------------------------------------

def test_ws11_metastability():
    df = _read("14_METASTABILITY_AUDIT.csv")
    assert len(df) == 4
    assert set(df["cell"]) == {"HIGH_BREADTH_HIGH_DISP",
                               "HIGH_BREADTH_LOW_DISP",
                               "LOW_BREADTH_HIGH_DISP",
                               "LOW_BREADTH_LOW_DISP"}
    assert set(df["verdict"]).issubset({"METASTABLE_LIKE",
                                        "TRANSIT_CORRIDOR",
                                        "ORDINARY_STATE",
                                        "INCONCLUSIVE"})


def test_ws12_transfer_flow():
    df = _read("15_TRANSFER_FLOW_PILOT.csv")
    assert len(df) == 16  # 4x4 transition matrix
    assert "probability_flux" in df.columns
    assert df["probability_flux"].sum() > 0.9


# ---------------------------------------------------------------------------
# WS13: loner placement
# ---------------------------------------------------------------------------

def test_ws13_loner_placement():
    df = _read("16_LONER_FIELD_PLACEMENT.csv")
    assert len(df) >= 2
    assert set(df["loner_class"]).issubset({"TRUE_LONER", "FALSE_LONER",
                                            "AMBIGUOUS"})
    assert df["verdict"].iloc[0] in {"DISTINCT_FIELD_PLACEMENT",
                                     "OVERLAPPING_FIELD_PLACEMENT",
                                     "INCONCLUSIVE"}
    assert (df["n_subperiods"] >= 3).all()


# ---------------------------------------------------------------------------
# WS14: absolute vs sigma
# ---------------------------------------------------------------------------

def test_ws14_abs_sigma():
    df = _read("17_ABSOLUTE_VS_SIGMA_AMPLITUDE.csv")
    assert len(df) == 4
    assert set(df["amplitude_cell"]) == {"HIGH_SIGMA_HIGH_ABS",
                                         "HIGH_SIGMA_LOW_ABS",
                                         "LOW_SIGMA_HIGH_ABS",
                                         "LOW_SIGMA_LOW_ABS"}
    assert (df["n"] > 10000).all()


# ---------------------------------------------------------------------------
# WS15: directional asymmetry
# ---------------------------------------------------------------------------

def test_ws15_directional():
    df = _read("18_DIRECTIONAL_ASYMMETRY_FIELD.csv")
    assert len(df) >= 4
    assert set(df["sign"]).issubset({"UP", "DOWN"})
    assert df["verdict"].iloc[0] in {"ASYMMETRIC_FIELD_GEOMETRY",
                                     "SYMMETRIC_FIELD_GEOMETRY",
                                     "INCONCLUSIVE"}


# ---------------------------------------------------------------------------
# WS16: potential -> realization
# ---------------------------------------------------------------------------

def test_ws16_potential_realization():
    df = _read("19_POTENTIAL_REALIZATION_REVISIT.csv")
    assert len(df) >= 5
    assert df["verdict"].iloc[0] in {"CANDIDATE_CONVERSION_PRIMITIVE",
                                     "LOCAL_CONVERSION_PATH",
                                     "NO_SINGLE_PATH",
                                     "NULL"}
    # propagation stage (outcome) must exist and be circular-checked
    assert "PROPAGATION" in df["stage"].values


# ---------------------------------------------------------------------------
# WS17: nodes / nulls / field map
# ---------------------------------------------------------------------------

def test_ws17_nodes():
    df = _read("20_PROMOTE_MERGE_DISSOLVE.csv")
    assert len(df) >= 14
    assert set(df["operation"]).issubset({"PROMOTE", "LOCAL_NODE",
                                          "DESCRIPTIVE", "MERGE",
                                          "DISSOLVE", "PARK", "EVALUATE",
                                          "KEEP", "KEEP_LOCAL"})


def test_ws17_nulls():
    df = _read("21_NULL_AND_FAILED_RESULTS.csv")
    assert len(df) >= 5
    assert {"result", "status", "note"}.issubset(df.columns)
    # key nulls preserved
    results = df["result"].tolist()
    assert any("Semi-Markov" in r for r in results)
    assert any("EARLY_DECAY" in r for r in results)


def test_ws17_field_map():
    df = _read("22_CANONICAL_FIELD_MAP_UPDATE.csv")
    assert len(df) >= 10
    assert {"node", "type", "status", "note"}.issubset(df.columns)
    # key earned nodes present
    nodes = df["node"].tolist()
    assert any("4-STATE" in n for n in nodes)
    assert any("PRICE_UP_RANK_DOWN" in n for n in nodes)


def test_summary_decision_consistency():
    s = (OUT / "23_MECH12_SUMMARY.md").read_text(encoding="utf-8")
    d = (OUT / "24_MECH12_DECISION.md").read_text(encoding="utf-8")
    v = json.loads((OUT / "_verdicts.json").read_text(encoding="utf-8"))
    assert v["verdict"] in d
    assert "human_review_required = TRUE" in s
    assert "next_checkpoint_authorized = FALSE" in s
    assert "NO STRATEGY" in s and "NO PNL" in s
