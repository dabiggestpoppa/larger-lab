"""MECH-11 semantic integrity tests. Verify definitions, not just existence."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT


def _read(name):
    p = OUT / name
    assert p.exists(), f"missing artifact {name}"
    if name.endswith(".csv"):
        return pd.read_csv(p)
    if name.endswith(".parquet"):
        return pd.read_parquet(p)
    return p.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# WS1 — multi-scale delivery lattice
# --------------------------------------------------------------------------

def test_lattice_exists_and_schema():
    d = _read("02_MULTI_SCALE_DELIVERY_LATTICE.csv")
    assert set(["cell", "age_band", "clock"]).issubset(d.columns)
    assert len(d) > 50
    assert set(["p_by_1d", "p_by_7d", "p_by_14d", "p_by_30d"]).issubset(
        d.columns)
    # probabilities in [0,1]
    ps = d[[c for c in d.columns if c.startswith("p_by_")]]
    assert (ps.values >= -1e-9).all() and (ps.values <= 1 + 1e-9).all()


def test_lattice_has_clock_families():
    d = _read("02_MULTI_SCALE_DELIVERY_LATTICE.csv")
    clocks = set(d["clock"])
    assert "STATE_EXIT" in clocks and "PROPAGATION" in clocks
    assert "REENTRY" in clocks and "RANK_RECRUITMENT" in clocks
    assert any(c.startswith("ARRIVAL_") for c in clocks)


def test_lattice_monotonic_exit():
    """P(exit within h) should be non-decreasing in h for each cell x age."""
    d = _read("02_MULTI_SCALE_DELIVERY_LATTICE.csv")
    ex = d[d["clock"] == "STATE_EXIT"]
    hs = ["p_by_1d", "p_by_2d", "p_by_3d", "p_by_5d", "p_by_7d"]
    for (cell, ab), g in ex.groupby(["cell", "age_band"]):
        if len(g) != 1:
            continue
        vals = [g[c].iloc[0] for c in hs]
        assert all(vals[i] <= vals[i + 1] + 1e-9 for i in range(len(vals) - 1)), \
            f"exit not monotone {cell} {ab}"


# --------------------------------------------------------------------------
# WS2 — sequence grammar
# --------------------------------------------------------------------------

def test_sequence_grammar_schema():
    d = _read("03_SEQUENCE_GRAMMAR.csv")
    assert set(["sequence", "count", "n_subperiods", "status"]).issubset(
        d.columns)
    assert len(d) > 0
    assert set(d["status"]).issubset({"COMMON", "LOCAL", "RARE", "NULL"})


def test_sequence_common_bar():
    """COMMON requires >=50 obs and >=3 subperiods."""
    d = _read("03_SEQUENCE_GRAMMAR.csv")
    com = d[d["status"] == "COMMON"]
    if len(com):
        assert (com["count"] >= 50).all()
        assert (com["n_subperiods"] >= 3).all()


# --------------------------------------------------------------------------
# WS3 — semi-Markov audit
# --------------------------------------------------------------------------

def test_semi_markov_schema():
    d = _read("04_SEMI_MARKOV_AUDIT.csv")
    assert "verdict" in d.columns
    assert d["verdict"].iloc[0] in {"SEMI_MARKOV_EARNED",
                                    "MARKOV_SUFFICIENT", "INCONCLUSIVE"}
    assert "logloss_markov" in d.columns and "logloss_semi" in d.columns


# --------------------------------------------------------------------------
# WS4 — competing risk
# --------------------------------------------------------------------------

def test_competing_risk_verdict():
    d = _read("05b_COMPETING_RISK_VERDICT.csv")
    assert len(d) >= 1
    assert d["verdict"].iloc[0] in {"MASS_SHIFT_EARNED", "NO_SHIFT"}


def test_competing_risk_schema():
    d = _read("05_COMPETING_RISK_CLOCKS.csv")
    assert "cell" in d.columns and "age_band" in d.columns
    assert "ci_any_30d" in d.columns
    assert (d["ci_any_30d"] <= 1 + 1e-9).all()


# --------------------------------------------------------------------------
# WS5 — perturbation amplitude
# --------------------------------------------------------------------------

def test_perturbation_amplitude_schema():
    d = _read("06_PERTURBATION_AMPLITUDE.csv")
    assert set(["perturbation", "amplitude", "n"]).issubset(d.columns)
    assert set(d["amplitude"]).issubset({"SMALL", "MEDIUM", "LARGE"})
    assert (d["n"] >= 15).all()


# --------------------------------------------------------------------------
# WS6 — propagation radius
# --------------------------------------------------------------------------

def test_radius_schema():
    d = _read("07_PROPAGATION_RADIUS.csv")
    assert "event_type" in d.columns and "verdict" in d.columns
    assert set(d["verdict"]).issubset({"LOCAL", "REGIONAL", "BROAD_FIELD",
                                       "DATA_LIMITED"})


# --------------------------------------------------------------------------
# WS7 — rank-depth sequences
# --------------------------------------------------------------------------

def test_depth_sequences():
    d = _read("08_RANK_DEPTH_SEQUENCES.csv")
    assert "horizon_d" in d.columns and "verdict" in d.columns
    assert d["verdict"].iloc[0] in {"WATERFALL", "DEEP_FIRST", "SIMULTANEOUS",
                                    "FRAGMENTED", "NO_STABLE_ORDER"}
    # probabilities sum to ~1 across the four patterns (minus NONE)
    for _, r in d.iterrows():
        tot = (r["pct_waterfall"] + r["pct_deep_first"]
               + r["pct_simultaneous"] + r["pct_fragmented"]
               + r["pct_none"])
        assert abs(tot - 1.0) < 1e-6


# --------------------------------------------------------------------------
# WS8/9 — patch geometry / coupling
# --------------------------------------------------------------------------

def test_patch_geometry():
    d = _read("09_RANK_PATCH_GEOMETRY.csv")
    assert set(["patch", "internal_corr_ppos", "false_loner_rate"]).issubset(
        d.columns)
    # UPPER_CORE should carry the highest false-loner rate (LF5 audit: 32.7%)
    uc = d[d["patch"] == "UPPER_CORE"]
    assert len(uc) == 1
    assert uc["false_loner_rate"].iloc[0] > 0.25
    assert uc["internal_corr_ppos"].iloc[0] > 0.5


def test_patch_coupling():
    d = _read("10_PATCH_COUPLING.csv")
    assert set(["patch_a", "patch_b", "corr_same_day"]).issubset(d.columns)
    assert len(d) == 10  # C(5,2)
    assert (d["corr_same_day"] > 0.8).all()  # adjacent ppos strongly sync


# --------------------------------------------------------------------------
# WS10 — loner field context
# --------------------------------------------------------------------------

def test_loner_context():
    d = _read("11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv")
    assert set(d["loner_class"]) == {"TRUE_LONER", "FALSE_LONER"}
    # FALSE loner should be embedded in higher breadth (LF5: false loners
    # are assets within 1 sigma of peers -> field-wide moves)
    t = d[d["loner_class"] == "TRUE_LONER"].iloc[0]
    f = d[d["loner_class"] == "FALSE_LONER"].iloc[0]
    assert f["med_top500_breadth_30d"] > t["med_top500_breadth_30d"]


# --------------------------------------------------------------------------
# WS11 — sigma recovery lattice
# --------------------------------------------------------------------------

def test_sigma_lattice():
    d = _read("12_SIGMA_RECOVERY_FIELD_LATTICE.csv")
    assert set(d["sigma_class"]) == {"2s", "3s", "4s+"}
    assert "verdict" in d.columns
    # amplitude gradient: p_EARLY rises with sigma class
    assert d["p_EARLY"].is_monotonic_increasing


# --------------------------------------------------------------------------
# WS12 — health definition reconciliation
# --------------------------------------------------------------------------

def test_health_reconciliation():
    d = _read("13_HEALTH_DEFINITION_RECONCILIATION.csv")
    assert "finding" in d.columns and "verdict" in d.columns
    assert len(d) >= 4


# --------------------------------------------------------------------------
# WS13 — health transition lattice
# --------------------------------------------------------------------------

def test_health_transition_lattice():
    d = _read("14_HEALTH_TRANSITION_LATTICE.csv")
    assert set(["t0_state", "horizon_d", "n"]).issubset(d.columns)
    assert set(d["horizon_d"]).issubset({3, 7, 14, 30})
    # PRD population exists at every horizon
    prd = d[d["t0_state"] == "PRICE_RECOVERY_RANK_DECAY"]
    assert len(prd) >= 3


# --------------------------------------------------------------------------
# WS14 — failure mirrors
# --------------------------------------------------------------------------

def test_failure_mirrors():
    d = _read("15_FAILURE_MIRROR_ANALYSIS.csv")
    if len(d):
        assert "verdict" in d.columns
        assert d["verdict"].iloc[0] in {"EARLY_DIVERGENCE", "COINCIDENT",
                                        "NO_MIRROR_DATA"}


# --------------------------------------------------------------------------
# WS15 — SHMC/SHHM placement
# --------------------------------------------------------------------------

def test_shmc_placement():
    d = _read("16_SHMC_SHHM_SEQUENCE_PLACEMENT.csv")
    assert set(d["group"]) == {"SHMC", "SHHM"}
    assert "verdict" in d.columns
    # SHHM should dominate HH, SHMC should not (MECH-10 locality)
    shmc = d[d["group"] == "SHMC"].set_index("cell")["pct_of_group"]
    shhm = d[d["group"] == "SHHM"].set_index("cell")["pct_of_group"]
    assert shhm["HIGH_BREADTH_HIGH_DISP"] > shmc["HIGH_BREADTH_HIGH_DISP"]
    assert shmc["LOW_BREADTH_LOW_DISP"] > shhm["LOW_BREADTH_LOW_DISP"]


# --------------------------------------------------------------------------
# WS16 — volatility clock
# --------------------------------------------------------------------------

def test_vol_clock():
    d = _read("17_VOLATILITY_CLOCK_ROLE.csv")
    assert set(["cell", "vol_class", "verdict"]).issubset(d.columns)
    assert set(d["vol_class"]) == {"VOL_LO", "VOL_MID", "VOL_HI"}


# --------------------------------------------------------------------------
# WS17 — chain activity
# --------------------------------------------------------------------------

def test_chain_overlay():
    d = _read("18_CHAIN_ACTIVITY_OVERLAY.csv")
    assert set(["sensor", "status"]).issubset(d.columns)
    assert set(d["sensor"]).issubset({"DEX_VOL", "TVL_VELOCITY",
                                      "STABLECOIN_ACTIVITY"})


# --------------------------------------------------------------------------
# Registry / governance
# --------------------------------------------------------------------------

def test_field_map():
    d = _read("19_CANONICAL_LOCAL_FIELD_MAP.csv")
    assert "node" in d.columns and "status" in d.columns
    assert len(d) >= 8


def test_nodes_and_nulls():
    d = _read("20_PROMOTE_MERGE_DISSOLVE.csv")
    assert "node" in d.columns and "operation" in d.columns
    n = _read("21_NULL_AND_FAILED_RESULTS.csv")
    assert "result" in n.columns and "status" in n.columns
    assert len(n) >= 5


def test_summary_decision_governance():
    s = _read("22_MECH11_SUMMARY.md")
    dec = _read("23_MECH11_DECISION.md")
    assert "human_review_required = TRUE" in s
    assert "next_checkpoint_authorized = FALSE" in s
    assert "NO STRATEGY" in dec and "NO PNL" in dec
    assert "PASS_MECH11" in dec


def test_preregistration_locked():
    pr = _read("01_PREREGISTRATION.md")
    assert "human_review_required = TRUE" in pr
    assert "next_checkpoint_authorized = FALSE" in pr
    assert ">=50" in pr


def test_verdicts_json():
    import json
    p = OUT / "_verdicts.json"
    assert p.exists()
    v = json.loads(p.read_text(encoding="utf-8"))
    assert v["checkpoint"] == "MECH-11"
    assert v["human_review_required"] is True
    assert v["next_checkpoint_authorized"] is False
