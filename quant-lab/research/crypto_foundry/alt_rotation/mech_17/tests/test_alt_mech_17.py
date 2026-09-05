"""MECH-17 placeholder smoke tests: deliverable file presence + verdict cells."""
import sys
from pathlib import Path
import pandas as pd

M17 = Path(__file__).resolve().parents[1]

def test_all_29_outputs_present():
    expected = [
        "01_PREREGISTRATION.md", "02_ROAD_SYSTEM_FREEZE_AUDIT.csv",
        "03_TRAFFIC_OBJECT_DEFINITIONS.csv", "04_FORCING_VARIANT_ATLAS.csv",
        "05_FORCING_COMPRESSION.csv", "06_CAPACITY_MAP.csv",
        "07_CONGESTION_MAP.csv", "08_EXIT_PRESSURE_REGIME_MAP.csv",
        "09_ENTROPY_DEMAND_MATRIX.csv", "10_TRANSFER_EFFICIENCY.csv",
        "11_THRESHOLD_BANDS.csv", "12_THRESHOLD_SURFACES.csv",
        "13_SATURATION_ANATOMY.csv", "14_SATURATION_SHAPE_FAMILIES.csv",
        "15_SATURATION_NODE_DRIFT.csv", "16_HYSTERESIS_PILOT.csv",
        "17_BIRTH_TRAJECTORY_STAGES.csv", "18_BIRTH_TRAJECTORY_EQUIFINALITY.csv",
        "19_ABORTED_FORMATIONS.csv", "20_2022_SHIFT_RECONSTRUCTION.csv",
        "21_2022_STRESS_ARCHETYPE.md", "22_ADAPTIVE_NODE_ROLE_ASSIGNMENT.csv",
        "23_DIRECTIONAL_GEOMETRY_LINK.csv", "24_FREE_EXTERNAL_CONTEXT.csv",
        "25_PROMOTE_MERGE_DISSOLVE.csv", "26_NULL_AND_FAILED_RESULTS.csv",
        "27_FIELD_MODEL_V1_GLOBAL_FREEZE_MAP.md", "28_MECH17_SUMMARY.md",
        "29_MECH17_DECISION.md",
    ]
    for name in expected:
        assert (M17 / name).exists(), f"missing {name}"

def test_threshold_bands_covered():
    d = pd.read_csv(M17 / "11_THRESHOLD_BANDS.csv")
    wanted = ["26-100", "101-250", "251-500", "501-750",
              "751-1000", "1001-1500", "1501-2000"]
    assert set(wanted).issubset(set(d["patch"])), "not all 7 rank patches covered"

def test_forcing_verdict_rendered():
    d = pd.read_csv(M17 / "05_FORCING_COMPRESSION.csv")
    v = d.loc[d["metric"] == "verdict", "value"].iloc[0]
    assert v != "RENDER_AFTER_REVIEW", "forcing verdict not finalized"

def test_no_nan_verdict_in_object_defs():
    d = pd.read_csv(M17 / "03_TRAFFIC_OBJECT_DEFINITIONS.csv")
    assert d["final_verdict"].notna().all()

def test_exit_pressure_bands_present():
    d = pd.read_csv(M17 / "08_EXIT_PRESSURE_REGIME_MAP.csv")
    assert d["exit_band"].isin(["OPEN_EXIT_SET", "NARROWING", "CONCENTRATED",
                                "NEAR_SINGLE_EXIT"]).all()
