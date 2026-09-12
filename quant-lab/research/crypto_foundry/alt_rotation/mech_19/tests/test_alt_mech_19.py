#!/usr/bin/env python
"""ALT_MECH_19 smoke tests (CSV-level; fast, no recompute).

Asserts the MECH-19 deliverables exist and that the headline, decision-grade
results hold. Terrain research only.
"""
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent.parent   # mech_19/


def load(name):
    return pd.read_csv(HERE / name)


def have_csvs():
    need = [f"{i:02d}_{x}" for i, x in []]
    names = [
        "02_PRESSURE_CONCENTRATION_ANATOMY.csv", "03_CONCENTRATION_PHASES.csv",
        "04_ROUTE_COMMITMENT.csv", "05_PRUNING_VS_CONCENTRATION.csv",
        "06_POST_RESOLUTION_PATHS.csv", "07_FORCING_PRIMITIVES_DEEP.csv",
        "08_FORCING_SIGNATURES.csv", "09_FORCING_COOCCURRENCE.csv",
        "10_FORCING_INTERACTIONS.csv", "11_FORCING_ROUTE_MAP.csv",
        "12_SATURATION_MECHANISM.csv", "13_RESPONSE_NODE_COUPLING.csv",
        "14_RESPONSE_COORDINATE_PILOT.csv", "15_SATURATION_BY_ROUTE.csv",
        "16_SATURATION_WITHOUT_DELIVERY.csv", "17_THRESHOLD_INVERSION_ANATOMY.csv",
        "18_THRESHOLD_INVERSION_SPECIES.csv", "19_DEEP_HYSTERESIS_MAP.csv",
        "20_HYSTERESIS_BOUNDARIES.csv", "21_BIRTH_FAILURE_MECHANISM.csv",
        "22_LOAD_COMMITMENT_MISMATCH.csv", "23_BIRTH_RECOVERY.csv",
        "24_POTENTIAL_REALIZATION_CONSTRAINTS.csv", "25_CONSTRAINT_COMBINATION_LATTICE.csv",
        "26_FAILURE_MOTIF_DECOMPOSITION.csv", "27_REALIZATION_GEOMETRY.csv",
        "28_2022_UNCLAMPED_REPAIR.csv", "29_2022_EVENT_REESTIMATE.csv",
        "30_SURFACE_VS_LAW_RECOVERY.csv", "31_STRUCTURAL_SCAR.csv",
        "32_2022_REEXCURSIONS.csv", "33_2022_EVENT_END.csv",
        "34_2022_PRECEDENCE_MAP.csv", "35_GLOBAL_LAW_HIERARCHY.csv",
        "36_PROMOTE_MERGE_DISSOLVE.csv", "37_NULL_AND_FAILED_RESULTS.csv",
    ]
    for n in names:
        assert (HERE / n).exists(), n
    # narrative
    for n in ["01_PREREGISTRATION.md", "38_GLOBAL_LAW_FREEZE_MAP.md",
              "39_MECH19_SUMMARY.md", "40_MECH19_DECISION.md"]:
        assert (HERE / n).exists(), n


def test_unclamped_repair_preserves_flattening():
    d = load("28_2022_UNCLAMPED_REPAIR.csv")
    f = d[d.response == "FIELD"]
    pre = f[(f.window == "PRE2021") & (f.fit == "UNCLAMPED")].slope.iloc[0]
    dur = f[(f.window == "DURING_2022") & (f.fit == "UNCLAMPED")].slope.iloc[0]
    post = f[(f.window == "POST2022") & (f.fit == "UNCLAMPED")].slope.iloc[0]
    assert dur < 0.5 * pre, (pre, dur)
    assert post < pre, (pre, post)  # residual flattening persists
    # clamp was minor, not the driver
    cee_d = f[(f.window == "DURING_2022") & (f.fit == "CLAMPED")].ceiling.iloc[0]
    cee_u = f[(f.window == "DURING_2022") & (f.fit == "UNCLAMPED")].ceiling.iloc[0]
    assert cee_u - cee_d < 0.2, (cee_d, cee_u)


def test_structural_scar_on_slope():
    d = load("31_STRUCTURAL_SCAR.csv")
    assert d.verdict.str.contains("STRUCTURAL_SCAR").any()
    slope = d[d.variable == "slope_FIELD"].displacement.iloc[0]
    assert slope > 1.0


def test_realization_is_parallel_not_sequential():
    h = load("35_GLOBAL_LAW_HIERARCHY.csv")
    assert h.hierarchy_verdict.iloc[0] in ("PARALLEL_CONSTRAINT_SYSTEM", "HYBRID")
    # lattice: threshold+transfer should deliver well above base
    lt = load("25_CONSTRAINT_COMBINATION_LATTICE.csv")
    tt = lt[lt.subset.isin(["THRESHOLD+TRANSFER", "THRESHOLD+TRANSFER+NON_SATURATED"])]
    assert len(tt) and tt.deliver_rate.min() > 0.6


def test_birth_failure_open_route_set():
    d = load("21_BIRTH_FAILURE_MECHANISM.csv")
    ent = d[d.coordinate == "exit_entropy"]
    live = d[d.coordinate == "n_live_exits"]
    assert ent.aborted_mean.iloc[0] > ent.viable_mean.iloc[0]
    assert live.aborted_mean.iloc[0] > live.viable_mean.iloc[0]


def test_saturation_without_delivery_not_exit_concentration():
    d = load("16_SATURATION_WITHOUT_DELIVERY.csv")
    p1 = d[d.variable == "exit_pressure_p1"]
    te = d[d.variable == "transfer_efficiency"]
    assert abs(p1["diff"].iloc[0]) < 0.1      # exit concentration ≈ equal
    assert te["diff"].iloc[0] < -0.2          # transfer impaired


def test_event_reestimate_boundaries_present():
    d = load("29_2022_EVENT_REESTIMATE.csv")
    assert d.stage.isin(["DEVIATION_ONSET", "PEAK_DISTORTION"]).all() or len(d) >= 6
    on = d[d.stage == "DEVIATION_ONSET"].date.iloc[0]
    assert str(on) >= "2021-11-01"


if __name__ == "__main__":
    have_csvs()
    test_unclamped_repair_preserves_flattening()
    test_structural_scar_on_slope()
    test_realization_is_parallel_not_sequential()
    test_birth_failure_open_route_set()
    test_saturation_without_delivery_not_exit_concentration()
    test_event_reestimate_boundaries_present()
    print("ALL MECH-19 TESTS PASS")