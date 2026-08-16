"""
CR-RISK-BLOCK1-FOUNDATION-SEAL — invariant / sanity tests.

Covers the seal outputs: probabilities in [0,1], frontier f values match R4,
non-overlapping ordered profile bands, no best size, Block II locked, Kelly
unauthorized, no strategy changes, arithmetic account translation, family-B
capital-limiting classification, profile DD ranges mapped from real frontier
rows, and provenance hashes present in the manifest.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "artifacts" / "risk_block1"

PROFILE_ORDER = ["RM-S0_PRESERVATION", "RM-S1_CONSERVATIVE", "RM-S2_BALANCED",
                 "RM-S3_GROWTH", "RM-S4_FULL_PRESS_RESEARCH"]


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(B / name)


def _decision() -> dict:
    return json.loads((B / "BLOCK1_DECISION.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. probabilities in [0,1]
# ---------------------------------------------------------------------------

def test_frontier_probabilities_in_unit_interval():
    lm = _load("BLOCK1_STATIC_FRONTIER.csv")
    prob_cols = [c for c in lm.columns if c.startswith("P_")]
    assert prob_cols, "no probability columns found"
    for c in prob_cols:
        assert lm[c].between(0.0, 1.0).all(), f"{c} outside [0,1]"


def test_prop_constraint_probabilities_in_unit_interval():
    pr = _load("BLOCK1_PROP_CONSTRAINT_MAP.csv")
    for c in ["P_dd_ge_10", "P_dd_ge_15", "P_dd_ge_20"]:
        assert pr[c].between(0.0, 1.0).all()


def test_profile_probabilities_in_unit_interval():
    bands = _load("BLOCK1_RM_PROFILE_LIBRARY.csv")
    for c in ["rep_P_dd_ge_20", "rep_P_dd_ge_40", "rep_P_dd_ge_50"]:
        assert bands[c].between(0.0, 1.0).all(), c


# ---------------------------------------------------------------------------
# 2. static f values match R4 ladder exactly
# ---------------------------------------------------------------------------

def test_frontier_f_values_match_r4_ladder():
    lm = _load("BLOCK1_STATIC_FRONTIER.csv")
    ladder = _load("R4_STATIC_RISK_LADDER.csv")
    ladder = ladder[ladder["book"] == "A+B"]
    for _, r in lm.iterrows():
        src = ladder[ladder["f_pct"] == r["f_pct"]].iloc[0]
        assert src["cagr"] == pytest.approx(r["cagr"], rel=1e-12)
        assert src["max_dd"] == pytest.approx(r["historical_max_dd"], rel=1e-12)
        assert src["worst_day_pct"] == pytest.approx(r["worst_day_pct"], rel=1e-12)
        assert src["calmar"] == pytest.approx(r["calmar"], rel=1e-12)


def test_frontier_landmark_f_set_is_subset_of_r4_ladder():
    lm = _load("BLOCK1_STATIC_FRONTIER.csv")
    ladder = _load("R4_STATIC_RISK_LADDER.csv")
    ladder = ladder[ladder["book"] == "A+B"]
    assert set(lm["f_pct"]) <= set(ladder["f_pct"])


# ---------------------------------------------------------------------------
# 3-4. profile bands non-overlapping, ordered, mapped to real rows
# ---------------------------------------------------------------------------

def test_profile_bands_non_overlapping():
    bands = _load("BLOCK1_RM_PROFILE_LIBRARY.csv")
    bands = bands.sort_values("f_band_min").reset_index(drop=True)
    for i in range(len(bands) - 1):
        assert bands.loc[i, "f_band_max"] < bands.loc[i + 1, "f_band_min"], \
            f"band {i} overlaps band {i + 1}"


def test_profile_bands_ordered_by_risk_intensity():
    bands = _load("BLOCK1_RM_PROFILE_LIBRARY.csv")
    order = {p: i for i, p in enumerate(PROFILE_ORDER)}
    bands = bands.sort_values("f_band_min").reset_index(drop=True)
    ranks = [order[p] for p in bands["profile"]]
    assert ranks == sorted(ranks), "profile risk intensity not ordered"
    # and representative f strictly increasing
    reps = bands["representative_f_pct"].tolist()
    assert all(b < a for b, a in zip(reps, reps[1:]))


def test_profile_bands_all_five_present():
    bands = _load("BLOCK1_RM_PROFILE_LIBRARY.csv")
    assert set(bands["profile"]) == set(PROFILE_ORDER)


def test_profile_dd_ranges_map_to_r4_frontier_rows():
    bands = _load("BLOCK1_RM_PROFILE_LIBRARY.csv")
    ladder = _load("R4_STATIC_RISK_LADDER.csv")
    ladder = ladder[ladder["book"] == "A+B"]
    for _, b in bands.iterrows():
        in_band = ladder[(ladder["f_pct"] >= b["f_band_min"])
                         & (ladder["f_pct"] <= b["f_band_max"])]
        assert len(in_band) > 0
        lo = in_band["max_dd"].min() * 100
        hi = in_band["max_dd"].max() * 100
        lo_s, hi_s = (float(x) for x in b["historical_max_dd_range_pct"].split(".."))
        assert lo == pytest.approx(lo_s, abs=0.05)
        assert hi == pytest.approx(hi_s, abs=0.05)


# ---------------------------------------------------------------------------
# 5-8. no best size, Block II locked, Kelly locked, no strategy change
# ---------------------------------------------------------------------------

def test_no_best_size_selected():
    d = _decision()
    assert d["best_size_selected"] is False
    # no field anywhere suggesting a chosen size
    assert "best_size" not in {k.lower() for k in d.keys()}


def test_block2_locked_and_kelly_unauthorized():
    d = _decision()
    assert d["block_2_cleared"] is False
    assert d["kelly_authorized"] is False
    assert d["dynamic_sizing_authorized"] is False
    assert d["family_allocation_authorized"] is False
    assert d["cluster_sizing_authorized"] is False
    assert d["dd_adaptive_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False


def test_no_strategy_changes():
    d = _decision()
    assert d["alpha_changed"] is False
    assert d["entry_changed"] is False
    assert d["exit_changed"] is False
    assert d["trade_management_changed"] is False


# ---------------------------------------------------------------------------
# 9. account translation arithmetic
# ---------------------------------------------------------------------------

def test_account_translation_arithmetic():
    tr = _load("BLOCK1_ACCOUNT_TRANSLATION.csv")
    for _, r in tr.iterrows():
        f = r["f_pct"] / 100.0
        assert r["dollar_1R"] == pytest.approx(f * r["account_usd"], rel=1e-9)
        assert r["minus_1R_usd"] == pytest.approx(-r["dollar_1R"], rel=1e-9)
        assert r["minus_3R_usd"] == pytest.approx(-3.0 * r["dollar_1R"], rel=1e-9)
        assert r["minus_2R_usd"] == pytest.approx(-2.0 * r["dollar_1R"], rel=1e-9)
        assert r["typical_2pos_gross_risk_usd"] == pytest.approx(
            2.0 * r["dollar_1R"], rel=1e-9)
        assert r["minus_3_66R_A_worst_usd"] == pytest.approx(
            -3.6553836279681793 * r["dollar_1R"], rel=1e-6)
        assert r["expected_event_gain_usd"] == pytest.approx(
            0.3492859038844105 * r["dollar_1R"], rel=1e-6)


# ---------------------------------------------------------------------------
# 10. family B capital-limiting matches underlying data
# ---------------------------------------------------------------------------

def test_family_b_capital_limiting_matches_data():
    ff = _load("R4_FAMILY_RISK_FRONTIER.csv")
    assert (ff["capital_limiting"] == "B").all()
    for _, r in ff.iterrows():
        assert r["max_dd_B"] >= r["max_dd_A"] - 1e-12
    d = _decision()
    assert "B" in d["family_capital_limiter"]


# ---------------------------------------------------------------------------
# 11. risk-unit lock consistency
# ---------------------------------------------------------------------------

def test_risk_unit_lock_matches_ledger():
    ledger = _load("R1_EVENT_RISK_LEDGER.csv")
    rR = ledger["pnl_bps"] / ledger["risk_unit_bps"]
    a_w = float(rR[ledger["family"] == "A"].min())
    b_w = float(rR[ledger["family"] == "B"].min())
    d = _decision()["risk_unit"]
    assert d["A_worst_R"] == pytest.approx(a_w, rel=1e-9)
    assert d["B_worst_R"] == pytest.approx(b_w, rel=1e-9)
    assert d["is_stop"] is False
    # account mapping documented
    lock = (B / "BLOCK1_RISK_UNIT_LOCK.md").read_text(encoding="utf-8")
    assert "NOT A STOP" in lock.upper()
    assert "account_return" in lock


# ---------------------------------------------------------------------------
# 12. provenance: no abbreviated SHAs, hashes present
# ---------------------------------------------------------------------------

def test_manifest_has_no_abbreviated_shas():
    m = json.loads((B / "BLOCK1_INPUT_HASH_MANIFEST.json").read_text(encoding="utf-8"))
    for k, v in m["prior_checkpoints"].items():
        assert isinstance(v, str) and len(v) == 40, f"{k} abbreviated: {v}"
    assert len(m["git_sha_at_generation"]) == 40


def test_manifest_artifact_hashes_present():
    m = json.loads((B / "BLOCK1_INPUT_HASH_MANIFEST.json").read_text(encoding="utf-8"))
    assert len(m["artifact_hashes"]) >= 60
    for k, v in m["artifact_hashes"].items():
        assert len(v) == 64, f"{k} not sha256"
        assert (B / k).exists(), f"{k} missing from artifacts dir"


def test_evidence_matrix_statuses_valid():
    ev = _load("BLOCK1_EVIDENCE_STATUS_MATRIX.csv")
    valid = {"VALIDATED", "VALIDATED DESCRIPTIVE", "VALIDATED DESCRIPTIVE OBSERVATION",
             "VALIDATED DESCRIPTIVE STATIC RESULT", "HYPOTHESIS_ONLY", "NOT TESTED",
             "REJECTED", "REJECTED (no material improvement)"}
    assert set(ev["status"]) <= valid, set(ev["status"]) - valid
    # every key concept present
    concepts = set(ev["concept"])
    for c in ["STATIC RISK FRONTIER", "-1R HARD STOP", "KELLY / FRACTIONAL KELLY",
              "DD-ADAPTIVE SIZING"]:
        assert any(c in x for x in concepts), c


def test_decision_required_keys_present():
    d = _decision()
    for k in ["checkpoint", "status", "block1_foundation_sealed",
              "risk_unit_locked", "exposure_truth_locked", "loss_anatomy_locked",
              "profit_anatomy_locked", "static_frontier_locked",
              "edge_degradation_locked", "tail_risk_locked", "family_risk_locked",
              "rm_profile_library_created", "alpha_changed", "entry_changed",
              "exit_changed", "trade_management_changed", "best_size_selected",
              "kelly_authorized", "dynamic_sizing_authorized",
              "family_allocation_authorized", "cluster_sizing_authorized",
              "dd_adaptive_authorized", "deployment_authorized", "mt5_authorized",
              "block_2_cleared", "human_review_required",
              "next_checkpoint_recommended", "stop"]:
        assert k in d, f"missing decision key {k}"
    assert d["status"] == "PASS"
    assert d["block1_foundation_sealed"] is True
    assert d["human_review_required"] is True
