from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    return pd.read_csv(ROOT / name)


def test_ws11_waterfall_repair():
    df = _load("13_WATERFALL_REVALIDATION.csv")
    row = df.loc[df["subtype"] == "ORDERLY_SHALLOW_TO_DEEP"].iloc[0]
    assert row["n_subperiods"] >= 3
    assert row["max_cycle_share"] <= 0.5
    assert row["verdict"] == "NAMED_SUBTYPE"


def test_ledger_has_waterfall_repair():
    df = _load("03_MECH13_CORRECTION_LEDGER.csv")
    repair = df.loc[df["artifact"] == "10_WATERFALL_SUBTYPE_MATRIX"]
    assert not repair.empty
    assert "REPAIR" in str(repair.iloc[0]["status"])


def test_ws20_dar_au_not_nan():
    df = _load("22_DISTURBANCE_ABSORPTION_RESIDUAL.csv")
    dar = df.loc[df["framing"] == "DISTURBANCE_ABSORPTION_RESIDUAL"].iloc[0]
    auc = float(dar["heldout_auc_durable_importance"])
    assert math.isfinite(auc)


def test_ws12_heldout_patch_specific_completed():
    # regression guard: the held-out patch-specific comparison previously
    # crashed (positional .loc on a merged frame) and the NaN was mislabeled
    # PATCH_SPECIFIC_RESPONSES. It must now complete with finite AUCs.
    df = _load("14_COMMON_FORCING_MODEL.csv")
    row = df.iloc[0]
    assert math.isfinite(float(row["heldout_auc_common_offset"]))
    assert math.isfinite(float(row["heldout_auc_patch_specific"]))
    assert not str(row["verdict"]).startswith("INCONCLUSIVE")


def test_ws15_axis_correlation_computed():
    # regression guard: axis rho was NaN (spearmanr over pairs with missing
    # tail entropy), and the NaN silently defaulted the verdict to COUPLED.
    # The correlation must now be computed on complete pairs.
    df = _load("17_SPATIAL_TEMPORAL_CONSTRAINT_RECHECK.csv")
    row = df.iloc[0]
    assert math.isfinite(float(row["axis_spearman"]))
    assert int(row["n_complete_pairs"]) > 1000
    assert str(row["verdict"]) in (
        "INDEPENDENT_CONSTRAINT_DIMENSIONS", "COUPLED_CONSTRAINT_DIMENSIONS")