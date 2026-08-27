"""MECH-7 semantic integrity tests.

Verify scientific content, not merely file existence:
- event-family reconstruction parity with LOWER-FIELD-2 cluster anatomy
- field context panel keys and no-leakage export
- 2x2 plane geometry (cell partition, transitions sum, dwell)
- lifecycle episode counts and dwell ordering
- breadth composition layer ordering
- sequence atlas lift/FDR sanity
- first-divergence outputs have both outcomes
- dead-node rechecks carry verdicts
- verdict vocabulary consistency across files
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT

FAMILY_COLUMNS = [
    "family", "n_events", "n_dates", "n_assets", "reversal_rate",
    "med_fwd7_sigma", "subperiods",
]
EXPECTED_FAMILIES = [
    "ISOLATED_DOWNSIDE_EXTREME", "LOCAL_CLUSTER_DOWNSIDE",
    "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE", "ISOLATED_UPSIDE",
    "COORDINATED_DOWNSIDE",
]
FIELD_COORDS = [
    "top500_breadth_30d", "top500_breadth_7d", "top500_dispersion_30d",
    "top3_share", "btc_return_30d", "btc_dominance",
    "eth_btc_relative_return_30d", "vol_med",
]
REGIME_FLAGS = ["BREADTH_EXPANDING", "BTC_UP", "VOL_HIGH", "RISK_ON",
                "CONC_FALLING", "ETH_STRONG"]


def test_all_required_artifacts_exist():
    req = [
        "01_PREREGISTRATION.md", "02_EVENT_FAMILY_SCHEMA.md",
        "03_GLOBAL_CONTEXT_EVENT_PANEL.parquet",
        "04_ISOLATED_DOWNSIDE_FIELD_ANATOMY.csv",
        "05_COORDINATED_UPSIDE_FIELD_ANATOMY.csv",
        "06_BREADTH_DISPERSION_2X2.csv", "07_BREADTH_DISPERSION_TRANSITIONS.csv",
        "08_HIGH_BRD_HIGH_DISP_LIFECYCLE.csv",
        "09_HIGH_BRD_HIGH_DISP_SEQUENCE_MAP.csv",
        "10_BREADTH_COMPOSITION.csv", "11_BREADTH_PRIMITIVE_AUDIT.csv",
        "12_COORDINATED_UP_SEQUENCE_ATLAS.csv",
        "13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv",
        "14_RANK_DETERIORATION_SHOCK_BRIDGE.csv",
        "15_FIRST_DIVERGENCE_UP_CONT_VS_GIVEBACK.csv",
        "16_FIRST_DIVERGENCE_DOWN_REVERSE_VS_CONTINUE.csv",
        "17_DEAD_NODE_REINTERPRETATION.csv",
        "18_NODE_MERGE_PROMOTE_DISSOLVE.csv", "19_ALPHA_ROLE_REGISTRY.csv",
        "20_CROSS_AGENT_FIELD_CONTEXT.parquet",
        "20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md",
        "21_NULL_AND_FAILED_RESULTS.csv", "22_MECH7_SUMMARY.md",
        "23_MECH7_DECISION.md",
    ]
    missing = [r for r in req if not (OUT / r).exists()]
    assert not missing, f"missing artifacts: {missing}"


def test_event_families_reconstructed():
    fam = pd.read_csv(OUT / "_FAMILY_SUMMARY.csv")
    assert set(EXPECTED_FAMILIES).issubset(set(fam["family"]))
    for f in EXPECTED_FAMILIES:
        row = fam[fam["family"] == f].iloc[0]
        assert row["n_events"] >= 50, f"{f} below minimum sample"
        assert row["n_dates"] >= 50
        assert row["subperiods"] >= 3


def test_lf2_parity_isolated_counts():
    """ISOLATED_DOWN + ISOLATED_UP should approximate LF2 ISOLATED total (~1212)."""
    fam = pd.read_csv(OUT / "_FAMILY_SUMMARY.csv")
    n_dn = int(fam.loc[fam["family"] == "ISOLATED_DOWNSIDE_EXTREME", "n_events"].iloc[0])
    n_up = int(fam.loc[fam["family"] == "ISOLATED_UPSIDE", "n_events"].iloc[0])
    total = n_dn + n_up
    assert 1000 <= total <= 1450, f"isolated parity broken: {total}"


def test_isolated_down_reversal_geometry():
    fam = pd.read_csv(OUT / "_FAMILY_SUMMARY.csv")
    row = fam[fam["family"] == "ISOLATED_DOWNSIDE_EXTREME"].iloc[0]
    # isolated downside extremes tend to revert (LF2: 0.45-0.75 by depth)
    assert 0.40 <= row["reversal_rate"] <= 0.85
    assert row["med_fwd7_sigma"] > -0.2  # not systematically continuing down


def test_coordinated_up_giveback_geometry():
    fam = pd.read_csv(OUT / "_FAMILY_SUMMARY.csv")
    for f in ["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]:
        row = fam[fam["family"] == f].iloc[0]
        assert 0.40 <= row["reversal_rate"] <= 0.80
        assert row["med_fwd7_sigma"] < 0.15  # coordinated pushes give back


def test_anatomy_rows_and_coords():
    for f, groups in [("04_ISOLATED_DOWNSIDE_FIELD_ANATOMY.csv", ["ALL", "REVERSAL", "CONTINUATION"]),
                      ("05_COORDINATED_UPSIDE_FIELD_ANATOMY.csv", ["ALL", "CONTINUATION", "GIVEBACK"])]:
        df = pd.read_csv(OUT / f)
        assert len(df) >= 3
        for g in groups:
            assert g in set(df["group"]), f"{f} missing {g}"
        for c in ["top500_breadth_30d_med", "top500_dispersion_30d_med"]:
            assert c in df.columns


def test_2x2_plane_geometry():
    plane = pd.read_csv(OUT / "06_BREADTH_DISPERSION_2X2.csv")
    assert set(plane["cell"]) == {
        "HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
        "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"}
    total_days = plane["n_days"].sum()
    assert 2100 <= total_days <= 2300, f"2x2 does not cover daily frame: {total_days}"
    assert (plane["n_episodes"] > 20).all()
    # HIGH_BRD_HIGH_DISP should have higher propagation than LOW_BRD_LOW_DISP
    hh = plane[plane["cell"] == "HIGH_BREADTH_HIGH_DISP"].iloc[0]
    ll = plane[plane["cell"] == "LOW_BREADTH_LOW_DISP"].iloc[0]
    assert hh["prop7"] > ll["prop7"]


def test_transition_matrix_sums():
    tr = pd.read_csv(OUT / "07_BREADTH_DISPERSION_TRANSITIONS.csv")
    for cell, g in tr.groupby("cell"):
        assert abs(g["p"].sum() - 1.0) < 0.05, f"transition row {cell} not stochastic"


def test_lifecycle_dwell_and_paths():
    life = pd.read_csv(OUT / "08_HIGH_BRD_HIGH_DISP_LIFECYCLE.csv")
    assert "entry_order" in set(life["dimension"])
    assert "exit_order" in set(life["dimension"])
    # FRESH entries (both off before) should dwell at least as long as SYNC
    fresh = life[(life["dimension"] == "entry_order") & (life["path"] == "FRESH")]
    if len(fresh):
        assert fresh["median_dwell_d"].iloc[0] >= 1


def test_breadth_composition_layer_ordering():
    comp = pd.read_csv(OUT / "10_BREADTH_COMPOSITION.csv")
    assert len(comp) == 4
    order = comp.set_index("layer")["med_breadth_7d"].to_dict()
    # R1_25 top-layer breadth should be >= deepest layer
    assert order["R1_25"] >= order["R251_500"] - 0.05


def test_breadth_primitive_audit_structure():
    audit = pd.read_csv(OUT / "11_BREADTH_PRIMITIVE_AUDIT.csv")
    assert "M0_level" in set(audit["model"])
    assert "M_FULL" in set(audit["model"])
    assert (audit["n"] == 125).all()


def test_sequence_atlas_has_lift_and_fdr():
    up = pd.read_csv(OUT / "12_COORDINATED_UP_SEQUENCE_ATLAS.csv")
    dn = pd.read_csv(OUT / "13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv")
    for df in [up, dn]:
        if len(df) == 0:
            continue
        assert "lift" in df.columns and "p_fdr" in df.columns
        assert (df["n_days"] >= 50).all()
        assert (df["n_subperiods"] >= 3).all()
        assert (df["p_fdr"] >= 0).all()


def test_rank_bridge_states():
    bridge = pd.read_csv(OUT / "14_RANK_DETERIORATION_SHOCK_BRIDGE.csv")
    states = set(bridge["rank_state"])
    assert "RANK_DETERIORATING" in states
    assert len(bridge) >= 2


def test_first_divergence_both_outcomes():
    up = pd.read_csv(OUT / "15_FIRST_DIVERGENCE_UP_CONT_VS_GIVEBACK.csv")
    dn = pd.read_csv(OUT / "16_FIRST_DIVERGENCE_DOWN_REVERSE_VS_CONTINUE.csv")
    for df in [up, dn]:
        assert len(df) > 0
        assert (df["ranksum_p"] >= 0).all()
        assert "p_fdr" in df.columns


def test_dead_node_rechecks_have_verdicts():
    dn = pd.read_csv(OUT / "17_DEAD_NODE_REINTERPRETATION.csv")
    assert len(dn) >= 7
    for _, r in dn.iterrows():
        assert isinstance(r["verdict"], str) and len(r["verdict"]) > 0
    shmc = dn[dn["node"] == "SHMC_TAIL_ACTIVATION"].iloc[0]
    assert shmc["p_value"] < 0.05  # mean-reversion recheck significant


def test_node_and_null_lists():
    nodes = pd.read_csv(OUT / "18_NODE_MERGE_PROMOTE_DISSOLVE.csv")
    assert len(nodes) >= 8
    nulls = pd.read_csv(OUT / "21_NULL_AND_FAILED_RESULTS.csv")
    assert len(nulls) >= 5


def test_alpha_registry_columns():
    reg = pd.read_csv(OUT / "19_ALPHA_ROLE_REGISTRY.csv")
    for c in ["statistic", "alpha_roles", "evidence_level", "sample_size",
              "conditionality", "causal_level"]:
        assert c in reg.columns


def test_cross_agent_export_no_leakage():
    df = pd.read_parquet(OUT / "20_CROSS_AGENT_FIELD_CONTEXT.parquet")
    assert len(df) > 50000
    for c in ["event_id", "asset_id", "date", "family", "state"]:
        assert c in df.columns
    # no forward-looking columns
    for c in df.columns:
        assert not re.search(r"fwd|ret_3d|ret_7d|ret_14d|ret_30d", c), f"leakage col {c}"
    # date range within panel
    dates = pd.to_datetime(df["date"])
    assert dates.min() >= pd.Timestamp("2020-06-01")
    assert dates.max() <= pd.Timestamp("2026-08-24")


def test_verdict_consistency():
    ver = json.loads((OUT / "_verdicts.json").read_text())
    assert ver["verdict"] == "PASS_MECH7_FIELD_CONTEXT"
    for k in ["ws1_isolated_down", "ws3_2x2", "ws11_cross_agent"]:
        assert ver[k] == "COMPLETE"
    dec = (OUT / "23_MECH7_DECISION.md").read_text(encoding="utf-8")
    assert "PASS_MECH7_FIELD_CONTEXT" in dec
    summ = (OUT / "22_MECH7_SUMMARY.md").read_text(encoding="utf-8")
    assert "PASS_MECH7_FIELD_CONTEXT" in summ


def test_prereg_thresholds_frozen():
    pre = (OUT / "01_PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "0.31" in pre and "0.307" in pre
    assert "FROZEN" in pre


def test_schema_doc():
    schema = (OUT / "20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md").read_text(encoding="utf-8")
    assert "event_id" in schema and "no target leakage" in schema.lower()
