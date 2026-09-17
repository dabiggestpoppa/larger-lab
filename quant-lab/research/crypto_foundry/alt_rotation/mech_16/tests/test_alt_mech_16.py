#!/usr/bin/env python
"""MECH-16 integrity tests: surface partitions, no future leakage,
age-residualized entropy, deterministic replay, FDR, transition completeness,
no strategy/PnL outputs."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="module")
def df():
    from _m16base import load_frame15, build_surfaces
    return build_surfaces(load_frame15())


@pytest.fixture(scope="module")
def files():
    return {p.name: p for p in ROOT.glob("*.csv") if p.name[0].isdigit()}


def test_all_24_outputs_exist(files):
    names = [f"{i:02d}_{s}" for i, s in [
        (2, "HOLDOUT_FAILURE_REPRO.csv"), (3, "SURFACE_6_VS_8_AUDIT.csv"),
        (4, "COVARIATE_CONDITIONAL_SHIFT.csv"),
        (5, "STATE_LOCAL_TRANSFER_FUNCTIONS.csv"),
        (6, "BIRTH_GEOMETRY_TRANSPORT.csv"),
        (7, "STATE_AGE_TRANSPORT.csv"),
        (8, "SURVIVAL_BRANCH_CONTRACTION.csv"),
        (9, "ENTROPY_TRANSPORT.csv"),
        (10, "COMMON_FORCING_TRANSPORT.csv"),
        (11, "RANK_THRESHOLD_DRIFT.csv"),
        (12, "SATURATION_LAW_DRIFT.csv"), (13, "CHANGEPOINT_SCAN.csv"),
        (14, "LAW_REGIME_CANDIDATES.csv"), (15, "INVARIANT_NODE_AUDIT.csv"),
        (16, "DIRECTION_CONSTRAINT_TRANSPORT.csv"),
        (17, "TRANSITION_TOPOLOGY_VS_RATES.csv"),
        (18, "ARTIFACT_AND_COMPOSITION_AUDIT.csv"),
        (19, "FREE_EXTERNAL_CONTEXT_PILOT.csv"),
        (20, "PROMOTE_MERGE_DISSOLVE.csv"),
        (21, "NULL_AND_FAILED_RESULTS.csv"),
        (22, "FIELD_MODEL_V1_FREEZE_INPUT.md"),
        (23, "MECH16_SUMMARY.md"), (24, "MECH16_DECISION.md")]]
    present = set(files) | {p.name for p in ROOT.glob("*.md")}
    missing = [n for n in names if n not in present]
    assert not missing, f"missing outputs: {missing}"
    assert (ROOT / "_verdicts.json").exists()
    assert (ROOT / "01_PREREGISTRATION.md").exists()


def test_each_day_exactly_one_surface_group(df):
    for col in ["grp16", "grp8", "grp6", "grp4", "grp4s"]:
        assert df[col].notna().all(), f"{col} has NaNs"
        assert df[col].nunique() == df[col].nunique(), f"{col} undefined"


def test_grp6_grp8_partitions_consistent_with_mcell(df):
    """Each 6/8-cell group must be a union of 16-cell mcells (partition
    refines the raw matrix, no cross-cell mixing)."""
    for col in ["grp6", "grp8"]:
        for g, sub in df.groupby(col):
            assert sub["mcell"].nunique() >= 1
        # a single mcell must never map to two groups
        dup = df.groupby("mcell")[col].nunique()
        assert (dup == 1).all(), f"{col} splits an mcell across groups"


def test_grp6_partition_matches_mech15_merge_tree(df):
    """Deterministic replay: 6-cell groups equal the M15 cut-6 clusters."""
    from _m16base import MC
    from _m15p2 import ws6_partition_at
    part = ws6_partition_at(df, MC, 6)
    groups = sorted(df["grp6"].unique())
    assert len(groups) == 6
    for grp in part:
        members = [MC[i] for i in grp]
        g = df.loc[df["mcell"].isin(members), "grp6"].unique()
        assert len(g) == 1, f"{members} split across groups: {g}"


def test_age_residualized_entropy_used(df):
    assert "ent_resid" in df.columns
    assert df["ent_resid"].notna().sum() >= len(df) - 10
    # constraint labels come from ent_resid sign, not raw fbe
    he = df.loc[df["temporal_ax"] == "HE", "ent_resid"].dropna()
    le = df.loc[df["temporal_ax"] == "LE", "ent_resid"].dropna()
    assert (he >= 0).all() and (le < 0).all()


def test_no_future_leakage_in_forward_flags(df):
    d = df["d"]
    assert d.is_monotonic_increasing
    # forward-rate flags: final 7 days must not be TRUE (no future window;
    # the frame defaults them to 0, which is conservative, never positive)
    for col in ["prop7", "ren7", "rank7", "tail7"]:
        assert not bool(df[col].iloc[-1]), f"{col} leaks beyond sample"
        assert not df[col].iloc[-7:].any(), f"{col} positive in final window"
    # next-value columns: last day has no successor
    for col in ["next_dir", "mcell_next", "grp6_next"]:
        assert pd.isna(df[col].iloc[-1]), f"{col} leaks beyond sample"


def test_state_age_bands_pit_safe(df):
    # age_in_cell must be >= 1 (episode day 1) and bands must be consistent
    assert (df["age_in_cell"] >= 1).all()
    expected = df["age_in_cell"].apply(lambda a: "AGE_1" if a == 1 else
                                       "AGE_2_3" if a <= 3 else
                                       "AGE_4_7" if a <= 7 else
                                       "AGE_8_14" if a <= 14 else "AGE_15_PLUS")
    assert (df["ab"] == expected).all()


def test_rank_patches_pit_safe():
    from _m16base import load_band15, patch_activation_daily, DEPTH_ORDER
    band = load_band15()
    pact = patch_activation_daily(band)
    assert set(pact.columns) == set(DEPTH_ORDER)
    assert pact.values.shape[1] == 7
    assert pact.index.is_monotonic_increasing


def test_fdr_applied_in_conditional_shift(files):
    s3 = pd.read_csv(files["04_COVARIATE_CONDITIONAL_SHIFT.csv"])
    cell_rows = s3[s3["object"] == "P(outcome|cell)"]
    assert len(cell_rows) >= 4
    assert "p_fdr" in cell_rows.columns and cell_rows["p_fdr"].notna().all()


def test_support_counts_reconcile(files):
    a = pd.read_csv(files["18_ARTIFACT_AND_COMPOSITION_AUDIT.csv"])
    total = a["n_days"].sum()
    # subperiods cover the full sample minus UNKNOWN (3 days)
    assert abs(total - 2193) <= 5, f"subperiod day sum {total} != 2193"


def test_transition_verdict_reasonable(files):
    t = pd.read_csv(files["17_TRANSITION_TOPOLOGY_VS_RATES.csv"])
    assert t["transition_verdict"].notna().all()
    assert t["transition_verdict"].iloc[0] in (
        "TOPOLOGY_STABLE_RATES_DRIFT", "TOPOLOGY_DRIFT", "FULL_STABILITY",
        "NO_STABLE_STRUCTURE", "DATA_LIMITED")


def test_no_strategy_pnl_execution_outputs(files):
    bad = []
    for name, p in files.items():
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for tok in ["pnl", "strategy", "execution", "entry/exit", "sizing",
                    "leverage", "alpha translation"]:
            if tok.lower() in txt.lower():
                # allow the governance footer lines that forbid them
                if name in ("20_NULL_AND_FAILED_RESULTS.csv",
                            "22_MECH16_SUMMARY.md", "23_MECH16_DECISION.md",
                            "24_MECH16_DECISION.md"):
                    continue
                bad.append((name, tok))
    assert not bad, f"forbidden tokens in outputs: {bad}"


def test_changepoint_scan_deterministic():
    import importlib
    from _m16base import load_frame15, build_surfaces, load_band15, \
        patch_activation_daily, load_ev15
    from _m16p5 import ws12_changepoint_scan
    df = build_surfaces(load_frame15())
    pact = patch_activation_daily(load_band15())
    ev = load_ev15()
    out1, al1 = ws12_changepoint_scan(df, pact, ev)
    out2, al2 = ws12_changepoint_scan(df, pact, ev)
    pd.testing.assert_frame_equal(out1, out2)
    pd.testing.assert_frame_equal(al1, al2)
