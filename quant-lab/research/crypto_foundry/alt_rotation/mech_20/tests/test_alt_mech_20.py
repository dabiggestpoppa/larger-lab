"""ALT_MECH_20 smoke tests - fast CSV-level checks.

Terrain research ONLY (AGENT 1). No PnL / strategy / execution.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

REQUIRED = [f"{i:02d}_{name}" for i, name in [
    (1, "PREREGISTRATION.md"), (2, "RESPONSE_LAW_DECOMPOSITION.csv"),
    (3, "SATURATION_RESPONSE_COORDS.csv"), (4, "RESPONSE_GAIN_STATE.csv"),
    (5, "CEILING_ROLE.csv"), (6, "SLOPE_CEILING_SURFACE.csv"),
    (7, "SATURATION_POSITION_BY_RESPONSE.csv"), (8, "SATURATION_FAILURE_MATCHED.csv"),
    (9, "SATURATION_FAILURE_TRANSITIONS.csv"), (10, "SATURATION_TO_DELIVERY.csv"),
    (11, "CAPACITY_INTERPRETATION.csv"), (12, "CAPACITY_RESPONSE_LAW.csv"),
    (13, "GLOBAL_LOCAL_CAPACITY_NOTE.md"), (14, "THRESHOLD_TRANSFER_2X2.csv"),
    (15, "THRESHOLD_TRANSFER_INTERACTION.csv"), (16, "REALIZATION_CORE.csv"),
    (17, "REALIZATION_RELATIONS.csv"), (18, "REALIZATION_CONSTRAINT_NETWORK.csv"),
    (19, "REALIZATION_MINIMAL_SETS.csv"), (20, "REALIZATION_EQUIFINALITY.csv"),
    (21, "BIRTH_FAILURE_DEEP.csv"), (22, "LOAD_RESOLUTION_MISMATCH.csv"),
    (23, "BIRTH_FAILURE_SURFACE.csv"), (24, "BIRTH_RECOVERY_PATH.csv"),
    (25, "THRESHOLD_INVERSION_MATERIALITY.csv"), (26, "THRESHOLD_INVERSION_POST_AUDIT.csv"),
    (27, "THRESHOLD_INVERSION_FUNCTION.csv"), (28, "HYSTERESIS_RECONCILIATION.csv"),
    (29, "HYSTERESIS_SURVIVAL_MAP.csv"), (30, "FORCING_FUNCTIONAL_DIMENSIONS.csv"),
    (31, "FORCING_FUNCTIONAL_MAP.csv"), (32, "FORCING_TEMPORAL_SCALES.csv"),
    (33, "FORCING_INTERACTION_DEEP.csv"), (34, "2022_ERA_HYPOTHESES.csv"),
    (35, "RESPONSE_GAIN_CHANGEPOINTS.csv"), (36, "PRE_TRANSITION_POST_LAW.csv"),
    (37, "NEW_BASELINE_VS_SCAR.csv"), (38, "REEXCURSION_ANATOMY.csv"),
    (39, "SURFACE_VS_LAW_GENERALIZATION.csv"), (40, "RESPONSE_LAW_STATE_PROPOSAL.md"),
    (41, "OLD_NODE_RECONNECTION.csv"), (42, "PROMOTE_PARK_DISSOLVE.csv"),
    (43, "NULL_AND_FAILED_RESULTS.csv"), (44, "GLOBAL_FIELD_MODEL_V1_FINAL_FREEZE_INPUT.md"),
    (45, "MECH20_SUMMARY.md"), (46, "MECH20_DECISION.md"),
]]


def test_all_required_deliverables_present():
    missing = [r for r in REQUIRED if not (OUT / r).exists()]
    assert not missing, f"missing: {missing}"


def test_decision_and_summary_exist():
    assert (OUT / "46_MECH20_DECISION.md").exists()
    assert (OUT / "45_MECH20_SUMMARY.md").exists()


def test_realization_core_transfer_dominant():
    d = pd.read_csv(OUT / "16_REALIZATION_CORE.csv")
    singles = d[d["single"] == True]
    assert len(singles) >= 4
    best = singles.loc[singles["heldout_auc"].idxmax()]
    assert best["best_combo"] == "TRANSFER"
    assert best["heldout_auc"] > 0.7


def test_capacity_absorptive():
    d = pd.read_csv(OUT / "12_CAPACITY_RESPONSE_LAW.csv")
    assert (d["verdict"] == "ABSORPTIVE_CAPACITY").any()
    hi = d[d["load_band"] == "HIGH_LOAD"].sort_values("capacity_band")
    rates = hi["delivery_rate"].to_numpy()
    assert len(rates) >= 2 and rates[0] > rates[-1]


def test_gain_state_continuous():
    d = pd.read_csv(OUT / "04_RESPONSE_GAIN_STATE.csv")
    assert (d["verdict"] == "CONTINUOUS_GAIN_COORDINATE").all()
    ac = d[d["probe"] == "autocorr_lag1"]["value"].iloc[0]
    assert ac > 0.9


def test_inversion_demoted_artifact():
    d = pd.read_csv(OUT / "25_THRESHOLD_INVERSION_MATERIALITY.csv")
    overall = d[d["probe"] == "OVERALL"]
    assert len(overall) == 1
    z = overall["standardized_gap_z"].iloc[0]
    assert z < 0.3  # materiality gate: sub-0.3 sigma gap = artifact
    assert (d["verdict"] == "COMPOSITION_ARTIFACT").all()
