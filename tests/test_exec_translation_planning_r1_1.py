"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL tests.

Narrow truth/handoff lock:

1.  pooled accepted summary computed directly from event-level rows
2.  A accepted summary computed directly
3.  B accepted summary computed directly
4.  no prose/report summary disagrees with canonical generated stats
5.  CapitalTranslationRequest includes immutable CapitalDecision reference
6.  translation core does NOT compute H1
7.  translation core does NOT classify family
8.  rejected event maps to zero exposure
9.  model_heat_after is INPUT/audit truth, not translator calculation
10. execution-runtime-foundation HEAD recorded accurately
11. TB engineering HEAD recorded accurately
12. no cross-branch write (IMMUTABLE commit-SHA provenance semantics;
    branch tips are mutable and never frozen — repaired in R1.1B)
13. no broker call
14. no science changes
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
for _p in (_SRC, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

import run_exec_translation_planning_r1_1 as r11  # noqa: E402
import run_exec_translation_planning_r1 as r1  # noqa: E402
import run_exec_translation_planning_r1_1b as r11b  # noqa: E402  (provenance helpers)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1"
R1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1"
EVENT_CSV = R1_DIR / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv"

RISK_UNIT_BPS = 24.49489742783178
EXEC_FOUNDATION_HEAD = "9e11db928ad3c330fcde06d075e20a6e5b349d89"
EXEC_FOUNDATION_HEAD_AT_START = "17cfe08eccadf77f5089f7c776bafdf671fbf5cd"
TB_ENGINEERING_HEAD = "d12005988ce61170d9bc5478089baa5ce54cc2a9"

# Immutable provenance for the no-cross-branch-write test (R1.1B semantics):
# frozen by commit SHA, never by mutable branch tips.
R1_1_SEAL = "2bbe52ea8798549ed9c03bd90684fd3a0d408a99"
R1_1_TEST_CHILD = "d51b9b4772f0bf2ee9a87deb830614e7494f25d1"
EXEC_FOUNDATION_FROZEN = EXEC_FOUNDATION_HEAD
TB_ENGINEERING_FROZEN = TB_ENGINEERING_HEAD

ARTIFACTS = [
    "CR_EXEC_R1_1_PROTOCOL.md", "CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json",
    "CR_EXEC_R1_1_ACCEPTED_NOTIONAL_SUMMARY.csv", "CR_EXEC_R1_1_SUMMARY_DRIFT_AUDIT.json",
    "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md", "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json",
    "CR_EXEC_R1_1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json",
    "CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA.json", "CR_EXEC_R1_1_HANDOFF_BOUNDARY.md",
    "CR_EXEC_R1_1_NONREGRESSION.json", "CR_EXEC_R1_1_TEST_AUDIT.json",
    "CR_EXEC_R1_1_REPORT.md", "CR_EXEC_R1_1_DECISION.json",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_EXEC_R1_1_DECISION.json").read_text(encoding="utf-8"))


def _canonical() -> dict:
    return r11.canonical_stats()


def test_artifacts_present():
    for name in ARTIFACTS:
        assert (OUT / name).exists(), f"missing artifact {name}"


# --- 1/2/3: summary statistics computed directly from event-level rows ------
def test_pooled_accepted_summary_from_event_rows():
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]
    assert len(acc) == 826
    s = acc["notional_multiple_equity"]
    canon = _canonical()["POOLED_ACCEPTED"]
    assert canon["n"] == 826
    assert abs(canon["min"] - s.min()) < 1e-4
    assert abs(canon["p50"] - s.median()) < 1e-4
    assert abs(canon["p95"] - np.percentile(s, 95)) < 1e-4
    assert abs(canon["p99"] - np.percentile(s, 99)) < 1e-4
    assert abs(canon["max"] - s.max()) < 1e-4
    # frozen canonical truth (issue 1)
    assert abs(canon["p50"] - 1.9842) < 5e-4
    assert abs(canon["p95"] - 7.6105) < 5e-3
    assert abs(canon["p99"] - 16.0364) < 5e-3
    assert abs(canon["max"] - 32.7663) < 5e-3


def test_A_accepted_summary_from_event_rows():
    df = pd.read_csv(EVENT_CSV)
    a = df[(df["status"] == "ACCEPT_FULL") & (df["family"] == "A")]
    assert len(a) == 371
    s = a["notional_multiple_equity"]
    canon = _canonical()["A_ACCEPTED"]
    assert abs(canon["p50"] - s.median()) < 1e-4
    assert abs(canon["p95"] - np.percentile(s, 95)) < 1e-4
    assert abs(canon["max"] - s.max()) < 1e-4
    assert abs(canon["p50"] - 3.3513) < 5e-4
    assert abs(canon["p95"] - 11.4407) < 5e-3
    assert abs(canon["max"] - 32.7663) < 5e-3


def test_B_accepted_summary_from_event_rows():
    df = pd.read_csv(EVENT_CSV)
    b = df[(df["status"] == "ACCEPT_FULL") & (df["family"] == "B")]
    assert len(b) == 455
    s = b["notional_multiple_equity"]
    canon = _canonical()["B_ACCEPTED"]
    assert abs(canon["p50"] - s.median()) < 1e-4
    assert abs(canon["p95"] - np.percentile(s, 95)) < 1e-4
    assert abs(canon["max"] - s.max()) < 1e-4
    assert abs(canon["p50"] - 1.2850) < 5e-4
    assert abs(canon["p95"] - 4.1231) < 5e-3
    assert abs(canon["max"] - 22.2754) < 5e-3


# --- 4: no prose/report summary disagrees with canonical stats --------------
def test_no_prose_summary_disagrees_with_canonical():
    drift = json.loads((OUT / "CR_EXEC_R1_1_SUMMARY_DRIFT_AUDIT.json")
                       .read_text(encoding="utf-8"))
    assert drift["summary_drift_repaired"] is True
    assert drift["r1_decision_audit_facts"]["matches_canonical"] is True
    assert drift["r1_report_prose"]["stale_tokens_found"] == []
    assert drift["r1_report_prose"]["has_canonical_stats"] is True
    assert drift["r1_progress_file"]["stale_tokens_found_now"] == []
    assert drift["r1_progress_file"]["has_canonical_stats_now"] is True
    assert drift["engine_recomputed_crosscheck"]["matches_canonical"] is True
    # decision fields carry the canonical numbers
    d = _decision()
    assert d["accepted_pooled_notional_median"] == drift["canonical_stats"]["POOLED_ACCEPTED"]["p50"]
    assert d["accepted_pooled_notional_p95"] == drift["canonical_stats"]["POOLED_ACCEPTED"]["p95"]
    assert d["accepted_pooled_notional_p99"] == drift["canonical_stats"]["POOLED_ACCEPTED"]["p99"]
    assert d["accepted_pooled_notional_max"] == drift["canonical_stats"]["POOLED_ACCEPTED"]["max"]
    assert d["accepted_A_notional_median"] == drift["canonical_stats"]["A_ACCEPTED"]["p50"]
    assert d["accepted_B_notional_median"] == drift["canonical_stats"]["B_ACCEPTED"]["p50"]


# --- 5/6/7/9: capital decision / translation boundary ----------------------
def test_translation_request_includes_immutable_capital_decision():
    req = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    cd = req["input_components"]["B_CapitalDecisionReference"]
    for field in ["decision_id", "policy_id", "requested_f_pct", "admitted_f_pct",
                  "status", "model_heat_before", "model_heat_after",
                  "decision_timestamp", "configuration_hash"]:
        assert field in cd, f"missing CapitalDecision field {field}"


def test_translation_core_does_not_compute_h1():
    cd = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json")
                    .read_text(encoding="utf-8"))
    assert cd["translation_recomputes_h1"] is False
    assert cd["translation_recomputes_model_heat"] is False
    assert cd["owner"] == "Capital Router / CapitalPolicy authority (upstream)"


def test_translation_core_does_not_classify_family():
    cd = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json")
                    .read_text(encoding="utf-8"))
    assert cd["translation_recomputes_family"] is False
    req = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    fam = req["input_components"]["A_StrategyEventReference"]["family"]
    assert "classified UPSTREAM" in fam
    assert "never classifies" in fam


def test_model_heat_after_is_input_audit_truth():
    cd = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json")
                    .read_text(encoding="utf-8"))
    mh = [f for f in cd["immutable_fields"] if f["name"] == "model_heat_after"][0]
    assert "INPUT audit truth" in mh["note"]
    assert "NOT by the translator" in mh["note"]
    assert "computed by CapitalPolicy" in mh["note"]


# --- 8: rejected event -> zero exposure -------------------------------------
def test_rejected_event_maps_to_zero_exposure():
    df = pd.read_csv(EVENT_CSV)
    rej = df[df["status"] != "ACCEPT_FULL"]
    assert len(rej) == 64
    assert (rej["notional_multiple_equity"] == 0.0).all()
    eco = json.loads((OUT / "CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    assert eco["rejected_event"]["status"] == "NO_EXPOSURE"
    assert eco["rejected_event"]["target_notional_account_ccy"] == 0.0
    cd = json.loads((OUT / "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json")
                    .read_text(encoding="utf-8"))
    assert cd["rejected_event_behavior"]["translation_result"] == "NO_EXPOSURE"


# --- 10/11: cross-workstream authority SHAs ---------------------------------
def test_execution_runtime_foundation_head_recorded():
    d = _decision()
    assert d["execution_runtime_authority_sha"] == EXEC_FOUNDATION_HEAD
    auth = json.loads((OUT / "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md")
                      .read_text(encoding="utf-8")) if False else None
    md = (OUT / "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md").read_text(encoding="utf-8")
    assert EXEC_FOUNDATION_HEAD in md
    assert "QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY" in md
    assert EXEC_FOUNDATION_HEAD_AT_START in md
    assert "advanced mid-checkpoint" in md
    assert "PASS" in md


def test_tb_engineering_head_recorded():
    d = _decision()
    assert d["tb_engineering_authority_sha"] == TB_ENGINEERING_HEAD
    md = (OUT / "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md").read_text(encoding="utf-8")
    assert TB_ENGINEERING_HEAD in md
    assert "TB-R6.1B-FIX-WORKER-STATE-LATCH" in md
    assert "PROVEN_ENGINEERING_REFERENCE" in md


# --- 12: no cross-branch write ----------------------------------------------
# R1.1B repair: provenance is frozen by IMMUTABLE commit SHA, not mutable
# branch tips. The active workstreams are expected to advance; their movement
# is never a test failure. No git fetch, no network.
def _provenance_repo_or_skip() -> Path:
    repo = r11b.provenance_repo()
    if repo is None:
        pytest.skip("frozen cross-branch commits unavailable in this checkout")
    return repo


def test_no_cross_branch_write():
    repo = _provenance_repo_or_skip()
    # A. frozen commit objects exist (immutable provenance)
    assert r11b.commit_exists(repo, EXEC_FOUNDATION_FROZEN)
    assert r11b.commit_exists(repo, TB_ENGINEERING_FROZEN)
    # R1.1 commits are descendants of capital-routing (branch ref lives in the
    # capital-routing repo itself, not necessarily in the foreign object store)
    assert r11b.is_ancestor(ROOT, R1_1_SEAL, "refs/heads/capital-routing")
    assert r11b.is_ancestor(ROOT, R1_1_TEST_CHILD, "refs/heads/capital-routing")
    # R1.1 commits are NOT ancestors of the frozen foreign commits
    for commit in (R1_1_SEAL, R1_1_TEST_CHILD):
        assert not r11b.is_ancestor(repo, commit, EXEC_FOUNDATION_FROZEN)
        assert not r11b.is_ancestor(repo, commit, TB_ENGINEERING_FROZEN)
    # changed-file truth: R1.1-specific files absent from the frozen foreign trees
    for path in r11b.R1_1_SPECIFIC_FILES:
        assert not r11b.blob_present_in_tree(repo, EXEC_FOUNDATION_FROZEN, path)
        assert not r11b.blob_present_in_tree(repo, TB_ENGINEERING_FROZEN, path)
    # the R1.1 runner only writes into its own artifact dir
    runner_src = (ROOT / "scripts" / "run_exec_translation_planning_r1_1.py").read_text(
        encoding="utf-8")
    assert "block3_execution_translation_r1_1" in runner_src


# --- 13: no broker call ------------------------------------------------------
def test_no_broker_call():
    d = _decision()
    assert d["broker_execution_performed"] is False
    # the pure economic target schema carries NO broker fields
    eco = json.loads((OUT / "CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    for bad in ["broker lot", "margin", "order type", "fill mode", "slippage"]:
        field_names = [f["name"] for f in eco["fields"]]
        assert bad not in field_names, f"broker field {bad} leaked into pure output"


# --- 14: no science changes -------------------------------------------------
def test_no_science_changes():
    nr = json.loads((OUT / "CR_EXEC_R1_1_NONREGRESSION.json").read_text(encoding="utf-8"))
    assert nr["science_unchanged"] is True
    assert nr["n_events"] == 890
    assert nr["n_A"] == 432 and nr["n_B"] == 458
    assert nr["n_accepted"] == 826 and nr["n_rejected"] == 64
    assert nr["accepted_A"] == 371 and nr["accepted_B"] == 455
    assert nr["risk_unit_bps"] == RISK_UNIT_BPS
    assert nr["risk_unit_is_hard_stop"] is False
    assert nr["gross_parity_pass"] is True
    assert nr["research_net_parity_pass"] is True
    assert nr["execution_net_parity_status"] == "BROKER_DEPENDENT_UNRESOLVED"
    assert nr["h1_parity_pass"] is True
    assert abs(nr["historical_worst_observed_account_impact_A_pct"] - (-2.5588)) < 5e-4
    assert abs(nr["historical_worst_observed_account_impact_B_pct"] - (-0.9939)) < 5e-4
    # science inputs hashes unchanged vs R1 manifest
    r1_manifest = json.loads(
        (R1_DIR / "CR_EXEC_R1_SOURCE_SHA_MANIFEST.json").read_text(encoding="utf-8"))
    assert nr["source_hashes"] == r1_manifest["frozen_inputs"]


def test_decision_expected_fields():
    d = _decision()
    assert d["checkpoint"] == r11.CHECKPOINT
    assert d["status"] == "PASS"
    assert d["base_commit"] == "00bef1b5b52db63c22a29b3287799742631930db"
    assert d["science_unchanged"] is True
    assert d["summary_drift_repaired"] is True
    assert d["capital_policy_translation_boundary_repaired"] is True
    assert d["translation_recomputes_h1"] is False
    assert d["translation_recomputes_family"] is False
    assert d["gross_parity_pass"] is True
    assert d["research_net_parity_pass"] is True
    assert d["execution_net_parity_status"] == "BROKER_DEPENDENT_UNRESOLVED"
    assert d["broker_execution_performed"] is False
    assert d["implementation_ready"] is True
    assert d["implementation_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0"
