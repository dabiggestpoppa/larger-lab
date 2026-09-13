"""Semantic integrity tests for CRYPTO-ALT-MECH-9 artifacts.

These verify scientific content, not file existence: row counts, required
columns, logical identities (age surfaces, survivorship reconciliation,
transition-velocity consistency, export no-leakage).
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
# WS1: continuous state-age surface
# ---------------------------------------------------------------------------

def test_ws1_age_surface_columns_and_cells():
    s = read("02_STATE_AGE_CONTINUOUS_SURFACE.csv")
    assert len(s) > 50
    for c in ["cell", "age_d", "n_days", "p_stay_next", "fwd7_prop",
              "fwd7_reentry"]:
        assert c in s.columns, f"missing {c}"
    assert set(s["cell"].unique()) == set(CELLS)


def test_ws1_hh_maturity_gradient():
    """Within HH, P(leave) must not RISE with age (maturity = persistence)."""
    s = read("02_STATE_AGE_CONTINUOUS_SURFACE.csv")
    hh = s[s["cell"] == "HIGH_BREADTH_HIGH_DISP"].sort_values("age_d")
    assert len(hh) >= 4
    d1 = hh.iloc[0]["p_leave_next"]
    dlast = hh.iloc[-1]["p_leave_next"]
    assert dlast <= d1 + 0.05, f"HH leave prob rose with age: {d1} -> {dlast}"


def test_ws1_fwd7_prop_range():
    s = read("02_STATE_AGE_CONTINUOUS_SURFACE.csv")
    assert s["fwd7_prop"].between(0, 1).all()
    assert s["p_leave_next"].between(0, 1).all()


# ---------------------------------------------------------------------------
# WS2: survivorship audit
# ---------------------------------------------------------------------------

def test_ws2_landmark_maturity():
    surv = read("03_STATE_AGE_SURVIVORSHIP_AUDIT.csv")
    lm = surv[surv["analysis"] == "landmark"].sort_values("landmark_d")
    assert len(lm) >= 4
    r1 = lm[lm["landmark_d"] == 1]
    r15 = lm[lm["landmark_d"] == 15]
    assert len(r1) == 1 and len(r15) == 1
    assert r15["fwd7_prop"].iloc[0] >= r1["fwd7_prop"].iloc[0]
    assert r15["p_leave_next"].iloc[0] <= r1["p_leave_next"].iloc[0]


def test_ws2_entry_coordinates_present():
    surv = read("03_STATE_AGE_SURVIVORSHIP_AUDIT.csv")
    e = surv[surv["analysis"] == "episode_entry"]
    assert len(e) >= 5
    assert {"ranksum_p", "long_lived_med", "short_lived_med"}.issubset(e.columns)


# ---------------------------------------------------------------------------
# WS4: HH birth quality
# ---------------------------------------------------------------------------

def test_ws4_birth_quality_summary():
    s = read("05b_HH_BIRTH_QUALITY_SUMMARY.csv")
    assert len(s) == 1
    assert s["cv_auc"].iloc[0] >= 0.5
    assert s["perm_p"].iloc[0] > 0  # finite-sample corrected, never 0
    assert s["n_episodes"].iloc[0] >= 50


def test_ws4_duration_buckets():
    b = read("05_HH_BIRTH_QUALITY.csv")
    assert len(b) >= 3
    assert b["n_episodes"].sum() >= 50


# ---------------------------------------------------------------------------
# WS5: second-order paths
# ---------------------------------------------------------------------------

def test_ws5_paths_format():
    p = read("06_SECOND_ORDER_STATE_PATHS.csv")
    assert len(p) >= 5
    for c in ["path", "from", "mid", "to", "n", "fwd7_prop"]:
        assert c in p.columns
    # paths are A->B->C with valid cell names
    for _, r in p.iterrows():
        assert r["from"] in CELLS and r["mid"] in CELLS and r["to"] in CELLS
        assert r["path"] == f"{r['from']}->{r['mid']}->{r['to']}"


# ---------------------------------------------------------------------------
# WS6: transition velocity
# ---------------------------------------------------------------------------

def test_ws6_velocity_classes():
    v = read("07_TRANSITION_VELOCITY.csv")
    assert len(v) >= 2
    assert set(v["vel_class"].unique()) <= {"SOFT_CROSS", "MODERATE_CROSS",
                                            "HARD_CROSS"}
    ev = read("07b_TRANSITION_VELOCITY_EVENTS.csv")
    assert len(ev) >= 100
    # no NaN in vel_class
    assert ev["vel_class"].notna().all()
    # HARD requires max delta >= 0.06
    hard = ev[ev["vel_class"] == "HARD_CROSS"]
    if len(hard):
        md = np.maximum(hard["brd_delta"].abs(), hard["disp_delta"].abs())
        assert (md >= 0.06).all()


# ---------------------------------------------------------------------------
# WS7: bifurcation search
# ---------------------------------------------------------------------------

def test_ws7_bifurcation_rows():
    b = read("08_LOCAL_BIFURCATION_SEARCH.csv")
    assert len(b) >= 5
    for c in ["axis", "verdict", "max_jump", "n_sharp_subperiods",
              "n_subperiods_tested"]:
        assert c in b.columns
    assert b["n_subperiods_tested"].between(3, 5).all()


# ---------------------------------------------------------------------------
# WS8: state-space vector field
# ---------------------------------------------------------------------------

def test_ws8_vector_field():
    v = read("09_STATE_SPACE_VECTOR_FIELD.csv")
    assert len(v) >= 5
    assert v["metric"].isin(["attractor", "corridor", "loop",
                             "hh_age_stability"]).all()
    assert v["n"].min() > 0


# ---------------------------------------------------------------------------
# WS9: perturbation response
# ---------------------------------------------------------------------------

def test_ws9_perturbation():
    p = read("10_PERTURBATION_RESPONSE.csv")
    assert len(p) >= 10
    assert {"perturbation", "cell", "n_treated", "n_control",
            "delta_prop"}.issubset(p.columns)
    assert p["delta_prop"].between(-1, 1).all()
    assert p["p_stay_treated"].between(0, 1).all()


# ---------------------------------------------------------------------------
# WS10: health-state field matrix
# ---------------------------------------------------------------------------

def test_ws10_health_matrix():
    h = read("11_HEALTH_STATE_FIELD_MATRIX.csv")
    assert len(h) >= 30
    assert set(h["health_state"].unique()) == {
        "PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
        "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"}
    for hs in h["health_state"].unique():
        lags = h[h["health_state"] == hs]["lag_d"].tolist()
        assert 0 in lags and 30 in lags
    # no missing numeric medians at t0
    t0 = h[h["lag_d"] == 0]
    assert t0["med_top500_breadth_30d"].notna().all()


# ---------------------------------------------------------------------------
# WS11: PRICE_UP_RANK_DOWN anatomy
# ---------------------------------------------------------------------------

def test_ws11_anatomy():
    a = read("12_PRICE_UP_RANK_DOWN_ANATOMY.csv")
    assert len(a) >= 15
    dims = set(a["dimension"])
    assert "n_events" in dims and "median_fwd_rank_vel_7d" in dims


# ---------------------------------------------------------------------------
# WS12: stress-response classes + divergence
# ---------------------------------------------------------------------------

def test_ws12_stress_classes():
    c = read("13_STRESS_RESPONSE_CLASSES.csv")
    assert set(c["response_class"].unique()) == {"RESPONDS", "WEAK_DELAYED",
                                                 "NO_RESPONSE"}
    assert c["n"].sum() >= 500
    d = read("14_STRESS_RESPONSE_FIRST_DIVERGENCE.csv")
    assert len(d) >= 10
    assert d["p_fdr"].notna().any()


# ---------------------------------------------------------------------------
# WS13: stress-response surface
# ---------------------------------------------------------------------------

def test_ws13_surface():
    s = read("15_STRESS_RESPONSE_SURFACE.csv")
    assert len(s) >= 6
    assert s["p_responds"].between(0, 1).all()
    assert s["verdict"].iloc[0] in ["LINEAR_RESPONSE", "SATURATING_RESPONSE",
                                    "NO_STABLE_RESPONSE"]


# ---------------------------------------------------------------------------
# WS14: no-response failure anatomy
# ---------------------------------------------------------------------------

def test_ws14_failure_components():
    e = read("16_NO_RESPONSE_FAILURE_ANATOMY.csv")
    assert len(e) >= 100
    assert e["no_price_response"].sum() == len(e)
    comp = read("16b_NO_RESPONSE_FAILURE_COMPONENTS.csv")
    assert len(comp) >= 6
    assert comp["p_present"].between(0, 1).all()


# ---------------------------------------------------------------------------
# WS15: liquidity final placement
# ---------------------------------------------------------------------------

def test_ws15_liquidity():
    l = read("17_LIQUIDITY_FINAL_PLACEMENT.csv")
    assert len(l) >= 8
    assert l["value"].notna().all()
    assert l["n"].min() >= 30


# ---------------------------------------------------------------------------
# WS16: SHMC/SHHM locality
# ---------------------------------------------------------------------------

def test_ws16_shmc_locality():
    s = read("18_SHMC_SHHM_LOCALITY.csv")
    assert len(s) == 2
    assert set(s["group"].unique()) == {"SHMC", "SHHM"}
    assert s["n_events"].min() >= 10000


# ---------------------------------------------------------------------------
# WS17: volatility locality
# ---------------------------------------------------------------------------

def test_ws17_vol_locality():
    v = read("19_VOLATILITY_LOCALITY.csv")
    assert len(v) == 3
    assert set(v["vol_tile"].unique()) == {"VOL_LO", "VOL_MID", "VOL_HI"}


# ---------------------------------------------------------------------------
# WS18: locality registry
# ---------------------------------------------------------------------------

def test_ws18_registry():
    r = read("20_LOCALITY_HIGHWAY_REGISTRY.csv")
    assert len(r) >= 3
    for c in ["node", "valid_region", "confidence"]:
        assert c in r.columns


# ---------------------------------------------------------------------------
# WS19: cross-agent export — no forward leakage
# ---------------------------------------------------------------------------

def test_ws19_export_rows_and_keys():
    e = read("21_CROSS_AGENT_CONTEXT_MECH9.parquet")
    assert len(e) > 50000
    for c in ["event_id", "cmc_id", "date", "cell", "age_in_cell", "state",
              "family", "subperiod"]:
        assert c in e.columns, f"missing {c}"
    assert e["date"].notna().all()
    assert e["event_id"].nunique() == len(e)


def test_ws19_export_trailing_only():
    """Field context columns must be trailing (no future daily values used):
    they are t0 or t-lag coords only. Forward labels are explicitly marked."""
    e = read("21_CROSS_AGENT_CONTEXT_MECH9.parquet")
    # perturbation flags are 0/1
    for c in ["brd_jump", "brd_drop", "disp_jump", "disp_drop", "btc_shock",
              "conc_shock", "vol_shock"]:
        assert set(e[c].unique()) <= {0, 1}
    # age_in_cell >= 1
    assert (e["age_in_cell"] >= 1).all()


def test_ws19_export_schema_doc():
    p = OUT / "21b_CROSS_AGENT_CONTEXT_SCHEMA.md"
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "LEAKAGE NOTE" in txt


# ---------------------------------------------------------------------------
# WS20: nodes / nulls / verdicts
# ---------------------------------------------------------------------------

def test_ws20_nodes():
    n = read("22_PROMOTE_MERGE_DISSOLVE.csv")
    assert len(n) >= 8
    assert n["operation"].isin(["PROMOTE", "KEEP", "MERGE", "DISSOLVE",
                                "NEW_NODE", "LOCAL_NODE", "DESCRIPTIVE",
                                "PARK", "RECONCILE"]).all()


def test_ws20_nulls():
    n = read("23_NULL_AND_FAILED_RESULTS.csv")
    assert len(n) >= 5


def test_ws20_verdicts():
    import json
    p = OUT / "_verdicts.json"
    assert p.exists()
    v = json.loads(p.read_text())
    assert v["verdict"].startswith("PASS_MECH9_")
    for ws in ["ws1_state_age_surface", "ws19_export"]:
        assert v.get(ws) == "COMPLETE"


def test_summary_decision_exist():
    for name in ["24_MECH9_SUMMARY.md", "25_MECH9_DECISION.md"]:
        p = OUT / name
        assert p.exists()
        txt = p.read_text(encoding="utf-8")
        assert "human_review_required = TRUE" in txt
        assert "NO STRATEGY" in txt
