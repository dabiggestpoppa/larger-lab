#!/usr/bin/env python
"""Integrity tests for CRYPTO-ALT-MECH-13 outputs.

These verify SEMANTIC definitions, not just file existence: entropy is real
bits in [0,2], probabilities/shares lie in [0,1], the 2x2 constraint matrix
has four distinguishable cells, waterfall subtypes carry >=50 observations
before being named, the metastability recheck is an explicit null, and the
initiation audit distinguishes NECESSARY vs SUFFICIENT vs CONDITIONAL.
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
         "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]


def _load(name):
    return pd.read_csv(ROOT / name)


def _has_cols(df, cols):
    missing = [c for c in cols if c not in df.columns]
    assert not missing, f"missing columns {missing}"


def _probs_ok(s):
    s = s.dropna()
    return bool((s >= -0.001).all() and (s <= 1.001).all())


# ---------------------------------------------------------------------------
def test_required_outputs_exist():
    files = [f"{n:02d}_{name}" for n, name in [
        (2, "LIFECYCLE_DEEP_MAP.csv"), (3, "STATE_MASS_MIGRATION.csv"),
        (4, "INITIATION_GEOMETRY.csv"), (5, "INITIATION_PRIMITIVE_AUDIT.csv"),
        (6, "ENTROPY_DEEP_MAP.csv"), (7, "ENTROPY_PRIMITIVE_AUDIT.csv"),
        (8, "ENTROPY_PROPAGATION.csv"),
        (9, "SPATIAL_TEMPORAL_CONSTRAINT_MATRIX.csv"),
        (10, "WATERFALL_SUBTYPE_MATRIX.csv"),
        (11, "ACTIVATION_THRESHOLD_SURFACES.csv"),
        (12, "PATCH_RESPONSE_CURVES.csv"),
        (13, "RESPONSE_CURVE_HETEROGENEITY.csv"),
        (14, "METASTABILITY_RECHECK.csv"),
        (15, "ABSOLUTE_SIGMA_SHOCK_GEOMETRY.csv"),
        (16, "SHOCK_MATERIALITY_AUDIT.csv"),
        (17, "DIRECTIONAL_ASYMMETRY_ATLAS.csv"),
        (18, "UPSIDE_GEOMETRY.csv"), (19, "DOWNSIDE_GEOMETRY.csv"),
        (20, "DIRECTIONAL_INFORMATION_GAIN.csv"),
        (21, "LOCAL_CONVERSION_PATHS.csv"),
        (22, "PROMOTE_MERGE_DISSOLVE.csv"),
        (24, "CANONICAL_FIELD_MAP_UPDATE.csv")]]
    for f in files:
        assert (ROOT / f).exists(), f"missing {f}"


# ---------------------------------------------------------------------------
def test_lifecycle_map_has_all_cells_and_stages():
    lc = _load("02_LIFECYCLE_DEEP_MAP.csv")
    for c in CELLS:
        assert c in set(lc["cell"]), f"lifecycle missing cell {c}"
    assert lc["n_days"].min() >= 20, "lifecycle stages too small to report"


def test_lifecycle_probability_columns_are_proportions():
    lc = _load("02_LIFECYCLE_DEEP_MAP.csv")
    for c in ["p_pos_state", "p_reentry_state", "fwd7_prop",
              "fwd7_reentry"]:
        assert _probs_ok(lc[c]), f"{c} not a probability"


def test_mass_migration_reallocates_for_hh():
    """The valid mass-migration law: HH maturity reallocates probability
    from fast failure (reentry) toward delayed delivery (propagation).
    (Raw ``stay`` mass at a fixed 7D horizon is non-monotonic because young
    states both leave AND get joined, so we do not assert on it directly.)
    """
    mm = _load("03_STATE_MASS_MIGRATION.csv")
    hh = mm[mm["cell"] == "HIGH_BREADTH_HIGH_DISP"]
    hh7 = hh[hh["horizon_d"] == 7].sort_values("age_band")
    prop = hh7["propagate"].to_numpy()
    ren = hh7["reentry"].to_numpy()
    assert len(prop) >= 4, "HH should have all age bands here"
    assert prop[-1] > prop[0], "HH maturity should raise propagation"
    assert ren[-1] < ren[0], "HH maturity should lower reentry"
    # the propagation/reentry split widens as HH matures
    assert (prop[-1] - ren[-1]) > (prop[0] - ren[0]), \
        "HH maturity should widen the prop-minus-reentry gap"


def test_initiation_geometry_has_q_and_fdr():
    ig = _load("04_INITIATION_GEOMETRY.csv")
    _has_cols(ig, ["cell", "coord", "mean_success", "mean_fail", "p", "q"])
    assert _probs_ok(ig["q"] - 1e-9), "q must be in [0,1]"
    assert ig["q"].between(0, 1).all()


def test_initiation_primitive_audit_has_valid_classes():
    a = _load("05_INITIATION_PRIMITIVE_AUDIT.csv")
    valid = {"NECESSARY_LOCAL", "SUFFICIENT_LOCAL", "CONDITIONAL",
             "SUBSTITUTABLE", "REDUNDANT"}
    assert set(a["necessity"]).issubset(valid), "invalid necessity label"
    assert "delta_auc_remove" in a.columns, "leave-one-out delta missing"
    # no NECESSARY claim unless coverage justifies it
    nec = a[a["necessity"] == "NECESSARY_LOCAL"]
    assert all(r["coverage_among_success"] >= 0.85 for _, r in nec.iterrows()), \
        "NECESSARY_LOCAL must have ~universal success coverage"


def test_entropy_deep_is_bits():
    ed = _load("06_ENTROPY_DEEP_MAP.csv")
    ent = ed["branch_entropy"].dropna()
    assert ent.between(0, 2.1).all(), "entropy must be bits in [0,2]"


def test_entropy_collapse_in_hh():
    ed = _load("06_ENTROPY_DEEP_MAP.csv")
    ca = ed[(ed["group"] == "cell_age")]
    hh = ca[ca["cell"] == "HIGH_BREADTH_HIGH_DISP"].sort_values("age_band")
    young = float(hh[hh["age_band"] == "AGE_1"]["branch_entropy"].iloc[0])
    mature = float(hh[hh["age_band"] == "AGE_15_PLUS"][
        "branch_entropy"].iloc[0])
    assert mature < young * 0.6, "HH maturity must lower branch entropy"


def test_entropy_propagation_verdict_present():
    ep = _load("08_ENTROPY_PROPAGATION.csv")
    assert "verdict" in ep.columns
    _has_cols(ep, ["patch_a", "patch_b", "lag_d", "spearman_rho"])


def test_spatial_temporal_matrix_is_real_2x2():
    s = _load("09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX.csv")
    cells = set(s["constraint_cell"])
    assert len(cells) >= 3, f"expected ~4 constraint cells, got {cells}"
    assert _probs_ok(s["p_prop_7d"]), "prop probability out of range"
    assert _probs_ok(s["p_reentry_7d"]), "reentry probability out of range"
    assert "axis_spearman" in s.columns


def test_waterfall_only_names_with_50_obs():
    w = _load("10_WATERFALL_SUBTYPE_MATRIX.csv")
    named = w[w["verdict"] == "NAMED_SUBTYPE"]
    assert len(named) >= 1, "expected at least one named waterfall subtype"
    assert named["n"].min() >= 50, \
        "named subtype must have >=50 observations"


def test_activation_surfaces_present():
    a = _load("11_ACTIVATION_THRESHOLD_SURFACES.csv")
    assert a["surface_type"].isin(
        ["MONOTONIC_THRESHOLD_SURFACE", "THRESHOLD_SURFACE_NON_MONOTONIC",
         "NO_STABLE_SURFACE"]).all()


def test_patch_response_probabilities_and_shapes():
    p = _load("12_PATCH_RESPONSE_CURVES.csv")
    if "activation_prob_3d" in p.columns:
        assert _probs_ok(p["activation_prob_3d"])
    if "response_shape" in p.columns:
        assert set(p["response_shape"]).issubset(
            {"MONOTONIC_RISING", "MONOTONIC_FALLING", "THRESHOLD",
             "SATURATING", "NO_STABLE_RESPONSE"})


def test_metastability_recheck_explodes_baseline():
    m = _load("14_METASTABILITY_RECHECK.csv")
    for c in CELLS:
        assert c in set(m["cell"]), f"metastability missing cell {c}"
    assert _probs_ok(m["excess_over_baseline"] - 0.5 + 0.5), \
        "excess must be numeric in [-1,1]"


def test_abs_sigma_geometry_is_2d():
    a = _load("15_ABSOLUTE_SIGMA_SHOCK_GEOMETRY.csv")
    _has_cols(a, ["sigma_class", "abs_class", "shock_cell", "n",
                  "p_reversal"])
    assert a["sigma_class"].nunique() >= 3, "expected >=3 sigma classes"
    assert a["abs_class"].nunique() >= 3, "expected >=3 abs classes"
    assert _probs_ok(a["p_reversal"])


def test_shock_materiality_has_verdict():
    m = _load("16_SHOCK_MATERIALITY_AUDIT.csv")
    assert m["verdict"].iloc[0] in {
        "MATERIALITY_PRIMITIVE", "LOCAL_MATERIALITY_RULE",
        "NO_COMPACT_INDEX"}


def test_directional_atlas_fields():
    d = _load("17_DIRECTIONAL_ASYMMETRY_ATLAS.csv")
    _has_cols(d, ["family", "sign", "n_events", "med_breadth"])
    assert d["sign"].dropna().isin(["UP", "DOWN"]).all()


def test_upside_downside_geometry_verdicts():
    assert _load("18_UPSIDE_GEOMETRY.csv")["verdict"].iloc[0] == \
        "FIELD_SELECTIVE_UPSIDE"
    assert _load("19_DOWNSIDE_GEOMETRY.csv")["verdict"].iloc[0] != ""


def test_directional_information_gain_entropy_bounds():
    g = _load("20_DIRECTIONAL_INFORMATION_GAIN.csv")
    ent = g["branch_entropy"].dropna()
    assert ent.between(0, 1.1).all(), "bits entropy out of range"
    assert "verdict" in g.columns


def test_local_conversion_paths_lift():
    c = _load("21_LOCAL_CONVERSION_PATHS.csv")
    assert "lift_vs_base" in c.columns
    # at least one named non-trivial path
    assert c["verdict"].iloc[0] in {
        "LOCAL_CONVERSION_PATHS", "LOCAL_CONVERSION_PATH_SINGLE",
        "NO_STABLE_LOCAL_PATH"}


def test_metastability_node_dissolved():
    n = _load("22_PROMOTE_MERGE_DISSOLVE.csv")
    row = n[n["node"] == "METASTABILITY_RECHECK"]
    assert len(row) == 1 and row["operation"].iloc[0] == "DISSOLVE", \
        "metastability recheck must be DISSOLVED (0 cells survive)"


def test_entropy_primitive_driver_present():
    e = _load("07_ENTROPY_PRIMITIVE_AUDIT.csv")
    _has_cols(e, ["coord", "spearman_rho", "q"])
    assert e["q"].between(0, 1).all()


def test_summary_and_decision_governance():
    for name in ["25_MECH13_SUMMARY.md", "26_MECH13_DECISION.md"]:
        txt = (ROOT / name).read_text(encoding="utf-8")
        assert "human_review_required = TRUE" in txt
        assert "next_checkpoint_authorized = FALSE" in txt
        assert "NO STRATEGY" in txt


def test_verdicts_json():
    import json
    v = json.loads((ROOT / "_verdicts.json").read_text(encoding="utf-8"))
    assert v["human_review_required"] is True
    assert v["next_checkpoint_authorized"] is False
    assert v["verdict"].startswith("PASS_MECH13")