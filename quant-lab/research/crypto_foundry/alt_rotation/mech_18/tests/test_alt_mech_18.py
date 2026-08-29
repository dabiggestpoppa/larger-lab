"""MECH-18 placeholder smoke tests: deliverable file presence + key verdict cells."""
from pathlib import Path
import pandas as pd

M18 = Path(__file__).resolve().parents[1]


def test_all_35_outputs_present():
    expected = [
        "01_PREREGISTRATION.md", "02_EDGE_REGISTRY.csv", "03_EDGE_HAZARDS.csv",
        "04_EXIT_AVAILABILITY_PRESSURE.csv", "05_ENTROPY_HIERARCHY.csv",
        "06_ENTROPY_DECAY.csv", "07_ROUTE_DEFORMATION.csv",
        "08_FORCING_PRIMITIVES.csv", "09_FORCING_HIERARCHY.csv",
        "10_ROUTE_SPECIFIC_FORCING.csv", "11_THRESHOLD_DEPENDENCIES.csv",
        "12_THRESHOLD_HIERARCHY.csv", "13_RESPONSE_FINGERPRINTS.csv",
        "14_SATURATION_DATA_COLLAPSE.csv", "15_RESPONSE_DIMENSIONALITY.csv",
        "16_SATURATION_NODE_DYNAMICS.csv", "17_GLOBAL_HYSTERESIS_RECHECK.csv",
        "18_MEMORY_VARIABLES.csv", "19_MEMORY_KERNEL_PILOT.csv",
        "20_BIRTH_VIABILITY_MAP.csv", "21_VIABILITY_BOUNDARIES.csv",
        "22_ABORTED_FORMATION_MECHANISM.csv",
        "23_POTENTIAL_REALIZATION_RECONSTRUCTION.csv",
        "24_POTENTIAL_REALIZATION_HIERARCHY.csv", "25_2022_EVENT_BOUNDARIES.csv",
        "26_2022_SNAPBACK.csv", "27_2022_VARIABLE_STRIP.csv",
        "28_2022_END_MECHANISM.csv", "29_2022_RESIDUE.csv",
        "30_REGIME_ROUTE_LAW_TABLE.csv", "31_PROMOTE_MERGE_DISSOLVE.csv",
        "32_NULL_AND_FAILED_RESULTS.csv", "33_GLOBAL_LAW_FREEZE_MAP.md",
        "34_MECH18_SUMMARY.md", "35_MECH18_DECISION.md",
    ]
    for name in expected:
        assert (M18 / name).exists(), f"missing {name}"


def test_edge_registry_covers_both_resolutions():
    d = pd.read_csv(M18 / "02_EDGE_REGISTRY.csv")
    assert {"6CELL", "8CELL"}.issubset(set(d["resolution"]))
    assert "edge_class" in d.columns
    assert len(d) >= 60, "edge registry too thin"


def test_2022_event_detected_data_defined():
    d = pd.read_csv(M18 / "25_2022_EVENT_BOUNDARIES.csv")
    assert "verdict" not in d.columns, "event detection failed (NO_EVENT_BLOCK_FOUND)"
    stages = set(d["stage"])
    assert "PEAK_DISTORTION" in stages and "DEVIATION_ONSET" in stages
    peak = d.loc[d["stage"] == "PEAK_DISTORTION", "date"].iloc[0]
    assert "2022" in str(peak), f"peak not in 2022: {peak}"


def test_data_collapse_verdict_rendered():
    d = pd.read_csv(M18 / "14_SATURATION_DATA_COLLAPSE.csv")
    v = d.loc[d["patch"] == "POOLED", "verdict"].iloc[0]
    assert isinstance(v, str) and v not in ("", "NaN"), "data-collapse verdict missing"


def test_promote_merge_dissolve_finalized():
    d = pd.read_csv(M18 / "31_PROMOTE_MERGE_DISSOLVE.csv")
    assert len(d) >= 15
    assert "PROMOTE" in set(d["action"]) and "DISSOLVE" in set(d["action"])


def test_no_placeholder_verdicts():
    d = pd.read_csv(M18 / "32_NULL_AND_FAILED_RESULTS.csv")
    for name in ["02_EDGE_REGISTRY.csv", "10_ROUTE_SPECIFIC_FORCING.csv",
                 "14_SATURATION_DATA_COLLAPSE.csv", "30_REGIME_ROUTE_LAW_TABLE.csv"]:
        row = d.loc[d["file"] == name]
        assert len(row) == 1, f"{name} missing from nulls table"
