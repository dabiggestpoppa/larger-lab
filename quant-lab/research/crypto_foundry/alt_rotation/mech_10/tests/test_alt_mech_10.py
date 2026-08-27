"""Semantic integrity tests for CRYPTO-ALT-MECH-10 artifacts.

These verify scientific content, not file existence: mechanism-decomposition
verdicts, conditional landmarks, 4-state delivery clocks, health-state
geometry, perturbation results, route-gate verdicts, placement verdicts, and
the export no-leakage contract.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]

CELLS = ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
         "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]


def read(name):
    p = OUT / name
    if not p.exists():
        pytest.fail(f"missing artifact {name}")
    if name.endswith(".parquet"):
        return pd.read_parquet(p)
    return pd.read_csv(p)


# ---------------------------------------------------------------------------
# WS1: state-age mechanism decomposition
# ---------------------------------------------------------------------------

def test_ws1_verdict_is_classified():
    d = read("02b_STATE_AGE_MECHANISM_VERDICT.csv")
    v = str(d["verdict"].iloc[0])
    allowed = {"BIRTH", "SELECTION", "MATURATION", "BIRTH_AND_SELECTION",
               "SELECTION_AND_MATURATION", "BIRTH_AND_MATURATION", "MIXED",
               "UNRESOLVED"}
    assert v in allowed, f"unexpected verdict {v}"


def test_ws1_has_three_component_evidence():
    t = read("02_STATE_AGE_MECHANISM_DECOMPOSITION.csv")
    cols = {"component", "measure", "long_med", "short_med", "p",
            "verdict"}
    assert cols <= set(t.columns), f"missing {cols - set(t.columns)}"
    comps = set(t["component"])
    assert {"BIRTH_QUALITY", "SURVIVAL_SELECTION",
            "WITHIN_STATE_MATURATION"} <= comps


# ---------------------------------------------------------------------------
# WS2: conditional landmarks
# ---------------------------------------------------------------------------

def test_ws2_landmark_ages_and_prob_ranges():
    lm = read("03_CONDITIONAL_LANDMARKS.csv")
    assert len(lm) >= 8  # >= 2 landmark ages per cell
    assert set(lm["cell"].unique()) == set(CELLS)
    for c in ["p_stay_1d", "p_stay_7d", "p_prop_7d", "p_reentry_7d"]:
        assert lm[c].dropna().between(0, 1).all(), f"{c} out of range"


def test_ws2_hh_maturity_gradient_preserved():
    lm = read("03_CONDITIONAL_LANDMARKS.csv")
    hh = lm[lm["cell"] == "HIGH_BREADTH_HIGH_DISP"].sort_values(
        "landmark_age")
    assert len(hh) >= 3
    assert hh["p_prop_7d"].iloc[-1] > hh["p_prop_7d"].iloc[0]
    assert hh["p_reentry_7d"].iloc[-1] < hh["p_reentry_7d"].iloc[0]


# ---------------------------------------------------------------------------
# WS3: 4-state temporal delivery clocks
# ---------------------------------------------------------------------------

def test_ws3_cells_and_clocks():
    d = read("04_4STATE_TEMPORAL_DELIVERY.csv")
    assert set(d["cell"].unique()) == set(CELLS)
    assert {"clock", "median_latency_d", "p_by_7d",
            "p_by_30d"} <= set(d.columns)
    for c in ["p_by_7d", "p_by_30d", "p_by_3d"]:
        assert d[c].dropna().between(0, 1).all(), f"{c} out of range"


def test_ws3_propagation_clock_uses_distinct_horizons():
    """30D probabilities must differ from the 7D ones (genuine fwd30
    columns, not a 7D copy). Conditional-on-survival windows need not be
    monotone, but they must be computed separately."""
    d = read("04_4STATE_TEMPORAL_DELIVERY.csv")
    prop = d[(d["cell"] == "HIGH_BREADTH_HIGH_DISP") &
             (d["clock"] == "PROPAGATION")]
    assert len(prop) >= 1
    r = prop.iloc[0]
    assert r["p_by_30d"] != r["p_by_7d"]
    assert r["p_by_14d"] != r["p_by_7d"]


# ---------------------------------------------------------------------------
# WS4: exit hazards + age-conditional exit geometry
# ---------------------------------------------------------------------------

def test_ws4_exit_hazards_rows():
    h = read("05_4STATE_EXIT_HAZARDS.csv")
    assert len(h) > 10
    assert {"cell", "h_d", "hazard", "n_at_risk",
            "cumulative_incidence"} <= set(h.columns)
    assert h["hazard"].dropna().between(0, 1).all()
    assert set(h["cell"].unique()) == set(CELLS)


def test_ws4_age_exit_geometry_destinations():
    g = read("06_AGE_CONDITIONAL_EXIT_GEOMETRY.csv")
    assert {"cell", "age_band", "exit_to", "n", "p_exit_dest"} <= set(
        g.columns)
    assert g["p_exit_dest"].dropna().between(0, 1).all()
    # destinations must be drawn from the 4-state vocabulary
    assert set(g["exit_to"]) <= set(CELLS)
    # each cell must have multiple age bands
    assert g.groupby("cell")["age_band"].nunique().min() >= 2


# ---------------------------------------------------------------------------
# WS5: route into state x age
# ---------------------------------------------------------------------------

def test_ws5_route_by_age_exists():
    r = read("07_ROUTE_INTO_STATE_BY_AGE.csv")
    assert {"route", "age_band", "n_days", "fwd7_prop"} <= set(r.columns)
    assert r["n_days"].sum() > 500
    assert r["fwd7_prop"].dropna().between(0, 1).all()
    # multiple age bands present within at least one route
    assert r.groupby("route")["age_band"].nunique().max() >= 2


# ---------------------------------------------------------------------------
# WS6/7/8: PRICE_RECOVERY_RANK_DECAY geometry
# ---------------------------------------------------------------------------

def test_ws6_prd_matrix_has_field_coords():
    m = read("08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv")
    assert len(m) >= 5  # t0 + post lags
    assert {"lag_d", "n_events", "med_top500_breadth_30d",
            "med_top500_dispersion_30d", "med_btc_return_30d"} <= set(
                m.columns)


def test_ws7_prd_vs_pru_has_fdr():
    c = read("09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv")
    assert len(c) > 5
    assert {"axis", "var", "rank_decay_med", "rank_recovery_med", "diff",
            "p", "p_fdr"} <= set(c.columns)
    assert c["p_fdr"].notna().any()  # FDR computed, not all NaN


def test_ws8_prd_subtypes_exist():
    s = read("10_PRICE_UP_RANK_DOWN_SUBTYPES.csv")
    assert {"subtype", "n", "p_price_relapse",
            "median_fwd_rank_vel_30d"} <= set(s.columns)
    assert s["n"].sum() >= 100


# ---------------------------------------------------------------------------
# WS9: health-state transitions
# ---------------------------------------------------------------------------

def test_ws9_health_transition_matrix():
    t = read("11_HEALTH_STATE_TRANSITIONS.csv")
    assert {"from_state", "to_state", "horizon_d", "n", "p"} <= set(
        t.columns)
    assert t["p"].dropna().between(0, 1).all()
    states = {"PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
              "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"}
    assert set(t["from_state"]) <= states
    assert t["horizon_d"].nunique() >= 3  # 3/7/14/30D horizons


# ---------------------------------------------------------------------------
# WS10/11: stress response process + sequences
# ---------------------------------------------------------------------------

def test_ws10_stress_process_has_lags():
    p = read("12_STRESS_RESPONSE_PROCESS.csv")
    assert {"lag_d", "dimension", "var", "responds_med", "no_resp_med",
            "p_fdr"} <= set(p.columns)
    assert p["lag_d"].nunique() >= 4  # t0 through +7 at least


def test_ws11_sequences_min_count():
    s = read("13_STRESS_RESPONSE_SEQUENCES.csv")
    assert {"sequence", "n", "subperiods"} <= set(s.columns)
    assert (s["n"] >= 50).any(), "no sequence clears the >=50 naming bar"
    assert s["n"].sum() >= 100


# ---------------------------------------------------------------------------
# WS12: stall-and-rot
# ---------------------------------------------------------------------------

def test_ws12_stall_rot_phenotypes():
    a = read("14_STALL_AND_ROT_ANATOMY.csv")
    assert {"dimension", "value"} <= set(a.columns)
    flat = a[a["dimension"] == "PHENOTYPE_FLAT_n"]["value"].iloc[0]
    dec = a[a["dimension"] == "PHENOTYPE_DECLINING_n"]["value"].iloc[0]
    assert float(flat) >= 25 and float(dec) >= 150


# ---------------------------------------------------------------------------
# WS13: perturbation response age-conditional
# ---------------------------------------------------------------------------

def test_ws13_perturbation_by_age_rows():
    p = read("15_PERTURBATION_RESPONSE_AGE_CONDITIONAL.csv")
    assert {"perturbation", "hh_age_band", "n_treated", "n_control",
            "delta_prop"} <= set(p.columns)
    # HH at multiple ages must be present
    assert p["hh_age_band"].nunique() >= 2
    # both perturbation families present
    assert p["perturbation"].nunique() >= 2
    # probability columns bounded
    for c in ["delta_stay", "delta_prop"]:
        assert p[c].dropna().between(-1, 1).all(), f"{c} out of range"


# ---------------------------------------------------------------------------
# WS14: permission -> realization
# ---------------------------------------------------------------------------

def test_ws14_perm_real_has_order_arms():
    t = read("16_PERMISSION_REALIZATION_TEST.csv")
    assert {"move_type", "n_days", "median_tail_latency_d", "fwd7_prop",
            "p_tail_by_7d"} <= set(t.columns)
    orders = set(t["move_type"])
    assert {"BREADTH_FIRST", "DISPERSION_FIRST", "SIMULTANEOUS"} <= orders
    assert t["n_days"].sum() >= 300


# ---------------------------------------------------------------------------
# WS15: local route-gate depth
# ---------------------------------------------------------------------------

def test_ws15_gate_verdicts():
    g = read("17_LOCAL_ROUTE_GATE_DEPTH.csv")
    assert {"axis", "verdict", "subperiod_stable", "age_shifts"} <= set(
        g.columns)
    allowed = {"STABLE_GATE", "SHIFTING_GATE", "SMOOTH", "INCONCLUSIVE"}
    assert set(g["verdict"]) <= allowed
    # dispersion and breadth must be adjudicated, not skipped
    axes = set(g["axis"])
    assert "top500_dispersion_30d" in axes
    assert "top500_breadth_30d" in axes


# ---------------------------------------------------------------------------
# WS16-19: final placement verdicts
# ---------------------------------------------------------------------------

def test_ws16_transition_velocity_placement():
    t = read("18_TRANSITION_VELOCITY_FINAL_PLACEMENT.csv")
    assert t["verdict"].iloc[0] in {"PARK_TRANSITION_VELOCITY", "LOCAL_ROLE"}
    # if LOCAL_ROLE, the underlying p must be < 0.05
    if t["verdict"].iloc[0] == "LOCAL_ROLE":
        p = t["hh_tv_lo_vs_hi_p"].iloc[0]
        assert p == p and p < 0.05


def test_ws17_birth_quality_placement():
    b = read("19_HH_BIRTH_QUALITY_FINAL_PLACEMENT.csv")
    assert {"bq_tile", "n", "p_long_lived", "verdict"} <= set(b.columns)
    assert b["verdict"].iloc[0] in {"PARK_HH_BIRTH_QUALITY",
                                    "DESCRIPTIVE_ROLE", "LOCAL_ROLE"}


def test_ws18_shmc_placement_exists():
    s = read("20_SHMC_SHHM_LOCAL_PLACEMENT.csv")
    assert {"group", "age_band", "n", "p_cell_HH", "p_cell_LL"} <= set(
        s.columns)
    assert s["n"].sum() > 50
    assert s["group"].nunique() >= 2  # SHMC and SHHM


def test_ws19_volatility_depth_rows():
    v = read("21_VOLATILITY_LOCAL_ROLE_DEPTH.csv")
    assert {"vol_tile", "hh_age_band", "n", "fwd7_prop"} <= set(v.columns)
    assert v["vol_tile"].nunique() >= 2
    assert v["hh_age_band"].nunique() >= 2


# ---------------------------------------------------------------------------
# WS20: temporal locality highway map
# ---------------------------------------------------------------------------

def test_ws20_highway_map_rows():
    m = read("22_TEMPORAL_LOCALITY_HIGHWAY_MAP.csv")
    assert {"node", "state", "state_age", "delivery_clock",
            "exit_clock"} <= set(m.columns)
    assert len(m) >= 5


# ---------------------------------------------------------------------------
# WS21: promote/merge/dissolve + nulls
# ---------------------------------------------------------------------------

def test_ws21_node_operations_valid():
    n = read("23_PROMOTE_MERGE_DISSOLVE.csv")
    assert {"node", "operation", "status"} <= set(n.columns)
    assert set(n["operation"]) <= {"PROMOTE", "MERGE", "DISSOLVE", "PARK",
                                   "NEW_NODE", "KEEP", "CLASSIFY",
                                   "LOCAL_NODE", "DESCRIPTIVE"}


def test_ws21_nulls_present():
    z = read("24_NULL_AND_FAILED_RESULTS.csv")
    assert {"result", "status"} <= set(z.columns)
    assert len(z) >= 6


# ---------------------------------------------------------------------------
# Summary / decision consistency
# ---------------------------------------------------------------------------

def test_summary_and_decision_agree_on_verdict():
    import json
    with open(OUT / "_verdicts.json") as fh:
        v = json.load(fh)
    for name in ["25_MECH10_SUMMARY.md", "26_MECH10_DECISION.md"]:
        txt = (OUT / name).read_text(encoding="utf-8")
        assert v["verdict"] in txt, f"{name} missing verdict {v['verdict']}"
    assert v["verdict"].startswith("PASS_MECH10")


def test_summary_mentions_mechanism_decomposition():
    txt = (OUT / "25_MECH10_SUMMARY.md").read_text(encoding="utf-8")
    assert ("BIRTH" in txt) or ("SELECTION" in txt) or (
        "MATURATION" in txt)
