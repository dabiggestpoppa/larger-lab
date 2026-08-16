"""
CR-RISK-BLOCK-II-INTERMEDIATE-SEAL tests.

Locks the seal's integrity invariants: all required artifacts exist; the
decision carries the mandated false flags (best allocation / best heat
policy / best size / DD-adaptive / Kelly / hybrid / deployment / MT5 / R7
authorization) and the expected R7 readiness label; the 890/482/3 truth
reconciles with R6; single/multi-position DD shares sum to 1; the corrected
MC table has zero duplicate keys and H0 is DOMINATED in block-MC 50/50
space; the R5/R6 findings locks match the frozen decisions; component
classifications are explicit (episode budget REDUNDANT, dynamic sizing
DEFERRED); alpha is untouched.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
_SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, _SRC)

import capital_routing
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.phases.phase_r6_common import load_r6_inputs

ROOT = Path(__file__).resolve().parents[1]
B2 = ROOT / "artifacts" / "risk_block2"
B1 = ROOT / "artifacts" / "risk_block1"
R5 = B2 / "r5"
R6 = B2 / "r6"

REQUIRED = [
    "CR_RISK_BLOCK2_INTERMEDIATE_PROTOCOL.md",
    "CR_RISK_BLOCK2_INPUT_HASH_MANIFEST.json",
    "CR_RISK_BLOCK2_R5_FINDINGS_LOCK.json",
    "CR_RISK_BLOCK2_R6_FINDINGS_LOCK.json",
    "CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv",
    "CR_RISK_BLOCK2_SUPPORTED_DESIGN_REGION.csv",
    "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv",
    "CR_RISK_BLOCK2_EDGE_RETENTION_WARNING.json",
    "CR_RISK_BLOCK2_PORTFOLIO_ARCHITECTURE.md",
    "CR_RISK_BLOCK2_R7_NECESSITY_ASSESSMENT.md",
    "CR_RISK_BLOCK2_EVIDENCE_STATUS_MATRIX.csv",
    "CR_RISK_BLOCK2_REPORT.md",
    "CR_RISK_BLOCK2_DECISION.json",
]


def _decision() -> dict:
    return json.loads((B2 / "CR_RISK_BLOCK2_DECISION.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def load():
    return load_r6_inputs(ROOT)


# ---------------------------------------------------------------------------
# 1. artifacts present
# ---------------------------------------------------------------------------

def test_all_required_artifacts_present():
    for name in REQUIRED:
        assert (B2 / name).exists(), name


# ---------------------------------------------------------------------------
# 2. decision flags
# ---------------------------------------------------------------------------

def test_decision_flags_all_false_except_pass():
    d = _decision()
    for k in ["best_allocation_selected", "best_heat_policy_selected",
              "best_size_selected", "dd_adaptive_authorized",
              "kelly_authorized", "hybrid_authorized", "deployment_authorized",
              "mt5_authorized", "r7_authorized", "r7_scientifically_justified"]:
        assert d[k] is False, k
    assert d["block2_intermediate_seal_pass"] is True
    assert d["status"] == "PASS"
    assert d["human_review_required"] is True
    assert d["r7_ready"] is True
    assert d["r7_readiness_label"] == \
        "R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT"
    assert d["next_checkpoint_recommended"] == \
        "CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL"
    assert d["base_commit"] == "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"


def test_decision_commit_chain():
    d = _decision()
    assert d["r5_commit"] == "150a93dec8edf2997652cd20724298fe9927c0dc"
    assert d["r6_substantive_commit"] == \
        "1e8cc01fe34bf44418eb367fc35f885d7579691c"
    assert d["r6_correction_commit"] == \
        "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"
    assert d["block1_seal_commit"] == \
        "8ca072d0d939acf581770a99ce45b333deddd8c"
    assert d["r5_accepted"] and d["r6_accepted"] and d["r6_correction_accepted"]


# ---------------------------------------------------------------------------
# 3. event / episode / concurrency truth
# ---------------------------------------------------------------------------

def test_events_episodes_concurrency_reconcile(load):
    d = _decision()
    r6d = json.loads((R6 / "R6_DECISION.json").read_text(encoding="utf-8"))
    assert d["total_events"] == 890 == len(load["ba"]["tb"])
    assert d["episode_count"] == 482
    assert d["max_concurrency"] == 3
    assert d["total_events"] == r6d["total_events"]
    assert d["episode_count"] == r6d["episode_count"]
    assert d["max_concurrency"] == r6d["max_concurrency"]


def test_dd_shares_sum_to_one():
    d = _decision()
    single = d["single_position_loss_share"]
    multi = d["multi_position_loss_share"]
    assert abs(single + multi - 1.0) < 1e-6
    assert 0.80 < single < 0.90  # ~84.7% single-position
    assert 0.10 < multi < 0.20


# ---------------------------------------------------------------------------
# 4. corrected MC / frontier
# ---------------------------------------------------------------------------

def test_corrected_mc_zero_duplicates():
    mc = pd.read_csv(R6 / "R6_HEAT_POLICY_MONTE_CARLO.csv")
    g = mc.groupby(["policy_id", "scheme", "w_A_pct", "f_pct"]).size()
    assert (g > 1).sum() == 0
    assert "iid" in set(mc["scheme"])


def test_h0_blockmc50_dominated():
    d = _decision()
    nd = pd.read_csv(R6 / "R6_NONDOMINATED_HEAT_FRONTIER.csv")
    h0 = nd[(nd.regime == "blockmc_50") & (nd.policy_id == "H0")
            & (nd.f_pct == 1.0)]
    assert len(h0) == 1
    assert h0["status"].iloc[0] == "DOMINATED"
    assert d["h0_corrected_frontier_status"] == "DOMINATED"


# ---------------------------------------------------------------------------
# 5. findings locks match frozen decisions
# ---------------------------------------------------------------------------

def test_r5_findings_lock_matches_r5_decision():
    lock = json.loads((B2 / "CR_RISK_BLOCK2_R5_FINDINGS_LOCK.json").read_text(
        encoding="utf-8"))
    r5d = json.loads((R5 / "R5_DECISION.json").read_text(encoding="utf-8"))
    for fam in ["A", "B"]:
        for k in ["mean_R", "PF", "WR", "breach_1R", "max_dd_at_f1_solo_pct"]:
            assert lock[f"{fam}_quality_status"][k] == \
                r5d[f"{fam}_quality_status"][k], (fam, k)
    assert lock["best_allocation_selected"] is False
    assert lock["B_capital_limiter_confirmed"] is True


def test_r6_findings_lock_matches_r6_decision():
    lock = json.loads((B2 / "CR_RISK_BLOCK2_R6_FINDINGS_LOCK.json").read_text(
        encoding="utf-8"))
    r6d = json.loads((R6 / "R6_DECISION.json").read_text(encoding="utf-8"))
    assert lock["total_events"] == r6d["total_events"] == 890
    assert lock["episode_count"] == r6d["episode_count"] == 482
    assert lock["max_concurrency"] == r6d["max_concurrency"] == 3
    assert lock["best_heat_policy_selected"] is False
    assert lock["corrected_mc"]["duplicate_policy_scheme_alloc_f_keys"] == 0
    assert lock["corrected_mc"]["h0_blockmc_50_f1_status"] == "DOMINATED"


# ---------------------------------------------------------------------------
# 6. classifications
# ---------------------------------------------------------------------------

def test_component_classifications_explicit():
    cls = pd.read_csv(B2 / "CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv")
    by = dict(zip(cls["component"], cls["classification"]))
    assert by["static_family_allocation"] == "SUPPORTED"
    assert by["simple_gross_heat_cap_H1"] == "SUPPORTED"
    assert by["same_direction_cap_H2"] == "SUPPORTED_BUT_NOT_INCREMENTAL"
    assert by["b_family_cap_H3"] == "SUPPORTED_NOT_REQUIRED"
    assert by["episode_budget_H4"] == "REDUNDANT"
    assert by["combined_H5"] == "OPTIONAL"
    for c in ["dd_adaptive_R7", "kelly_R8", "hybrid_R9", "deployment", "mt5"]:
        assert by[c] == "DEFERRED", c
    # every row carries a non-empty evidence string
    assert (cls["evidence"].astype(str).str.len() > 2).all()


def test_complexity_pruning_complete():
    cp = pd.read_csv(B2 / "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv")
    dec = dict(zip(cp["policy_family"], cp["pruning_decision"]))
    assert dec["H1 gross cap"] == "ADOPT"
    assert dec["H4 episode budget"] == "PRUNE_REDUNDANT"
    assert dec["H2 same-direction"] == "PRUNE_REDUNDANT"
    assert "KEEP_SECONDARY" in dec["H3 B-family"]
    assert "DEFERRED" in dec["DD-adaptive / Kelly / hybrid"]


def test_supported_design_region_has_no_winner():
    sdr = pd.read_csv(B2 / "CR_RISK_BLOCK2_SUPPORTED_DESIGN_REGION.csv")
    # references only - no single production point
    assert {"50/50", "70/30", "100/0 A"} <= set(sdr["component"])
    assert "0.25% - 2.00%" in set(sdr["component"])
    d = _decision()
    assert d["best_allocation_selected"] is False


# ---------------------------------------------------------------------------
# 7. no new science: alpha untouched
# ---------------------------------------------------------------------------

def test_alpha_untouched(load):
    sealed = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    assert np.allclose(
        load["ba"]["tb"]["pnl_bps"].to_numpy(),
        sealed["pnl_bps"].to_numpy(), atol=1e-6)
    assert np.allclose(
        load["ba"]["tb"]["risk_unit_bps"].to_numpy(),
        sealed["risk_unit_bps"].to_numpy(), atol=1e-9)


def test_manifest_hashes_inputs():
    m = json.loads((B2 / "CR_RISK_BLOCK2_INPUT_HASH_MANIFEST.json").read_text(
        encoding="utf-8"))
    import hashlib
    for k, v in m["inputs"].items():
        p = ROOT / v["path"]
        assert p.exists(), v["path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == v["sha256"], k
    assert m["r6_correction_commit"] == \
        "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"
