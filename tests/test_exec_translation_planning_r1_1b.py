"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B-CROSS-BRANCH-PROVENANCE-TEST-REPAIR tests.

Immutable commit-SHA provenance semantics (branch tips are MUTABLE and never
frozen; historical checkpoint tests lock commit objects only):

1.  frozen execution-runtime SHA exists as commit object
2.  frozen TB SHA exists as commit object
3.  decision and source manifest agree on execution-runtime SHA
4.  decision and source manifest agree on TB SHA
5.  expected execution-runtime checkpoint identity matches frozen SHA
6.  expected TB checkpoint identity matches frozen SHA
7.  R1.1 capital-routing commit does not mutate foreign branch refs
8.  later branch advancement is simulated and does NOT fail provenance
9.  no test performs git fetch
10. no test requires network
11. scientific nonregression still passes
12. 890/826/64 unchanged
13. canonical accepted notional statistics unchanged
14. no broker call

All provenance checks run against the local object store (no fetch, no
network). capital-routing is a linked worktree of the larger-lab repo, so the
frozen foreign commits share one object store. In a checkout that genuinely
lacks those objects the cross-branch tests skip rather than fetch.
"""
from __future__ import annotations

import ast
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

import run_exec_translation_planning_r1_1b as r11b  # noqa: E402
import run_exec_translation_planning_r1_1 as r11  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1b"
R1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1"
R1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1"
EVENT_CSV = R1_DIR / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv"

RISK_UNIT_BPS = 24.49489742783178
EXEC_FOUNDATION_FROZEN = "9e11db928ad3c330fcde06d075e20a6e5b349d89"
EXEC_FOUNDATION_CHECKPOINT = "QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY"
TB_ENGINEERING_FROZEN = "d12005988ce61170d9bc5478089baa5ce54cc2a9"
TB_ENGINEERING_CHECKPOINT = "TB-R6.1B-FIX-WORKER-STATE-LATCH"
R1_1_SEAL = "2bbe52ea8798549ed9c03bd90684fd3a0d408a99"
R1_1_TEST_CHILD = "d51b9b4772f0bf2ee9a87deb830614e7494f25d1"

FROZEN_NOTIONAL = {
    "POOLED_ACCEPTED": {"p50": 1.9842, "p95": 7.6105, "p99": 16.0364, "max": 32.7663},
    "A_ACCEPTED": {"p50": 3.3513, "p95": 11.4407, "max": 32.7663},
    "B_ACCEPTED": {"p50": 1.2850, "p95": 4.1231, "max": 22.2754},
}

ARTIFACTS = [
    "CR_EXEC_R1_1B_PROTOCOL.md", "CR_EXEC_R1_1B_PROVENANCE_TEST_AUDIT.md",
    "CR_EXEC_R1_1B_SOURCE_SHA_MANIFEST.json", "CR_EXEC_R1_1B_NONREGRESSION.json",
    "CR_EXEC_R1_1B_TEST_AUDIT.json", "CR_EXEC_R1_1B_REPORT.md",
    "CR_EXEC_R1_1B_DECISION.json",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_EXEC_R1_1B_DECISION.json").read_text(encoding="utf-8"))


def _manifest() -> dict:
    return json.loads((OUT / "CR_EXEC_R1_1B_SOURCE_SHA_MANIFEST.json")
                      .read_text(encoding="utf-8"))


def _provenance_repo_or_skip() -> Path:
    repo = r11b.provenance_repo()
    if repo is None:
        pytest.skip("frozen cross-branch commits unavailable in this checkout")
    return repo


def test_artifacts_present():
    for name in ARTIFACTS:
        assert (OUT / name).exists(), f"missing artifact {name}"


# --- 1/2: frozen commit objects exist (immutable provenance) -----------------
def test_frozen_exec_runtime_sha_exists():
    repo = _provenance_repo_or_skip()
    assert r11b.commit_exists(repo, EXEC_FOUNDATION_FROZEN)


def test_frozen_tb_sha_exists():
    repo = _provenance_repo_or_skip()
    assert r11b.commit_exists(repo, TB_ENGINEERING_FROZEN)


# --- 3/4: manifest <-> decision SHA agreement --------------------------------
def test_manifest_and_decision_agree_exec_runtime():
    d, m = _decision(), _manifest()
    auth = m["cross_workstream_authority"]["execution_runtime_foundation"]
    assert auth["head_sha"] == EXEC_FOUNDATION_FROZEN
    assert d["execution_runtime_frozen_authority_sha"] == EXEC_FOUNDATION_FROZEN
    assert auth["head_sha"] == d["execution_runtime_frozen_authority_sha"]
    # and the historical R1.1 decision carries the same frozen SHA
    r11_dec = json.loads((R1_1_DIR / "CR_EXEC_R1_1_DECISION.json")
                         .read_text(encoding="utf-8"))
    assert r11_dec["execution_runtime_authority_sha"] == EXEC_FOUNDATION_FROZEN


def test_manifest_and_decision_agree_tb():
    d, m = _decision(), _manifest()
    auth = m["cross_workstream_authority"]["tb_forward_engine"]
    assert auth["head_sha"] == TB_ENGINEERING_FROZEN
    assert d["tb_frozen_authority_sha"] == TB_ENGINEERING_FROZEN
    assert auth["head_sha"] == d["tb_frozen_authority_sha"]
    r11_dec = json.loads((R1_1_DIR / "CR_EXEC_R1_1_DECISION.json")
                         .read_text(encoding="utf-8"))
    assert r11_dec["tb_engineering_authority_sha"] == TB_ENGINEERING_FROZEN


# --- 5/6: commit identity (subject matches expected checkpoint) --------------
def test_exec_runtime_checkpoint_identity_matches_frozen_sha():
    repo = _provenance_repo_or_skip()
    subject = r11b.commit_subject(repo, EXEC_FOUNDATION_FROZEN)
    assert EXEC_FOUNDATION_CHECKPOINT in subject


def test_tb_checkpoint_identity_matches_frozen_sha():
    repo = _provenance_repo_or_skip()
    subject = r11b.commit_subject(repo, TB_ENGINEERING_FROZEN)
    assert TB_ENGINEERING_CHECKPOINT in subject


# --- 7: no cross-branch write by R1.1 (ancestry + changed-file truth) --------
def test_r1_1_commits_do_not_mutate_foreign_branch_refs():
    repo = _provenance_repo_or_skip()
    pa = r11b.provenance_audit(repo)
    # R1.1 commits are descendants of capital-routing
    for sha in (R1_1_SEAL, R1_1_TEST_CHILD):
        assert r11b.is_ancestor(repo, sha, "refs/heads/capital-routing")
    # R1.1 commits are NOT ancestors of the frozen foreign commits
    for sha in (R1_1_SEAL, R1_1_TEST_CHILD):
        assert not r11b.is_ancestor(repo, sha, EXEC_FOUNDATION_FROZEN)
        assert not r11b.is_ancestor(repo, sha, TB_ENGINEERING_FROZEN)
    # R1.1-specific files are absent from the frozen foreign trees
    for path, truth in pa["changed_file_truth"].items():
        assert not truth["in_exec_foundation_frozen_tree"], path
        assert not truth["in_tb_frozen_tree"], path
    assert pa["foreign_branch_write_detected"] is False
    assert pa["provenance_test_pass"] is True
    # the decision confirms the same
    assert _decision()["foreign_branch_write_detected"] is False


# --- 8: later branch advancement simulated -> provenance still passes --------
def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    out = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True)
    if check and out.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out


def _mkcommit(repo: Path, msg: str) -> str:
    _git(repo, "commit", "--allow-empty", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_later_branch_advancement_does_not_fail_provenance(tmp_path):
    """Fixture: a seal freezes a foreign SHA; the foreign branch later
    advances (and even merges the seal). The OLD tip-equality semantics fail;
    the R1.1B immutable frozen-SHA semantics keep passing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "commit", "--allow-empty", "-m", "base")
    _git(repo, "branch", "foreign")
    _git(repo, "checkout", "-q", "-b", "capital")
    seal = _mkcommit(repo, "SEAL")  # the R1.1 seal commit
    frozen_foreign = _git(repo, "rev-parse", "foreign").stdout.strip()  # frozen at seal time

    # foreign workstream advances (as active concurrent workstreams do)
    _git(repo, "checkout", "-q", "foreign")
    new_tip = _mkcommit(repo, "R2 advance")
    assert new_tip != frozen_foreign

    # OLD (defective) semantics: current tip equality required -> FAILS
    assert frozen_foreign != new_tip

    # NEW (R1.1B) semantics: immutable frozen SHA + ancestry -> PASSES
    assert r11b.commit_exists(repo, frozen_foreign)
    assert not r11b.is_ancestor(repo, seal, frozen_foreign)
    assert r11b.is_ancestor(repo, frozen_foreign, new_tip)  # tip moved; frozen object untouched

    # even if the foreign branch later MERGES the seal, the frozen-history
    # check stays valid: the frozen commit's history is immutable
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge seal", seal)
    assert not r11b.is_ancestor(repo, seal, frozen_foreign)


# --- 9/10: no fetch / no network in the provenance suite ---------------------
def _assert_no_fetch_or_network(files) -> None:
    banned = {"fetch", "http", "https", "socket", "urllib", "requests"}
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "run":
                for el in node.args:
                    if not isinstance(el, ast.List):
                        continue
                    for item in el.elts:
                        if isinstance(item, ast.Constant) and isinstance(item.value, str):
                            assert item.value.strip().lower() not in banned, \
                                f"forbidden subprocess argument {item.value!r} in {f.name}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in banned, \
                        f"forbidden import {alias.name} in {f.name}"


def _provenance_sources() -> list:
    return [
        ROOT / "tests" / "test_exec_translation_planning_r1_1.py",
        ROOT / "tests" / "test_exec_translation_planning_r1_1b.py",
        ROOT / "scripts" / "run_exec_translation_planning_r1_1b.py",
    ]


def test_no_test_performs_git_fetch():
    _assert_no_fetch_or_network(_provenance_sources())
    d = _decision()
    assert d["git_fetch_used_by_tests"] is False


def test_no_test_requires_network():
    _assert_no_fetch_or_network(_provenance_sources())
    d = _decision()
    assert d["network_required_by_tests"] is False
    assert d["current_branch_tip_equality_required"] is False


# --- 11/12/13: scientific nonregression (science UNCHANGED) ------------------
def test_scientific_nonregression_passes():
    nr = json.loads((OUT / "CR_EXEC_R1_1B_NONREGRESSION.json").read_text(encoding="utf-8"))
    assert nr["science_unchanged"] is True
    assert nr["risk_unit_bps"] == RISK_UNIT_BPS
    assert nr["risk_unit_is_hard_stop"] is False
    assert nr["gross_parity_pass"] is True
    assert nr["research_net_parity_pass"] is True
    assert nr["execution_net_parity_status"] == "BROKER_DEPENDENT_UNRESOLVED"
    assert nr["h1_parity_pass"] is True
    assert nr["frozen_notional_stats_match"] is True
    assert nr["nonregression_pass"] is True
    assert _decision()["nonregression_pass"] is True
    assert _decision()["science_unchanged"] is True


def test_counts_unchanged():
    nr = json.loads((OUT / "CR_EXEC_R1_1B_NONREGRESSION.json").read_text(encoding="utf-8"))
    assert nr["n_events"] == 890
    assert nr["n_A"] == 432 and nr["n_B"] == 458
    assert nr["n_accepted"] == 826 and nr["n_rejected"] == 64
    assert nr["accepted_A"] == 371 and nr["accepted_B"] == 455
    # recomputed directly from event-level source truth (not stale prose)
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]
    assert len(df) == 890
    assert len(acc) == 826
    assert len(acc[acc["family"] == "A"]) == 371
    assert len(acc[acc["family"] == "B"]) == 455
    assert len(df[df["status"] != "ACCEPT_FULL"]) == 64


def test_canonical_notional_statistics_unchanged():
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]
    groups = {"POOLED_ACCEPTED": acc,
              "A_ACCEPTED": acc[acc["family"] == "A"],
              "B_ACCEPTED": acc[acc["family"] == "B"]}
    for label, sub in groups.items():
        s = sub["notional_multiple_equity"]
        frozen = FROZEN_NOTIONAL[label]
        assert abs(np.percentile(s, 50) - frozen["p50"]) < 5e-4, label
        assert abs(np.percentile(s, 95) - frozen["p95"]) < 5e-3, label
        assert abs(s.max() - frozen["max"]) < 5e-3, label
    p = FROZEN_NOTIONAL["POOLED_ACCEPTED"]
    assert abs(np.percentile(acc["notional_multiple_equity"], 99) - p["p99"]) < 5e-3


# --- 14: no broker call ------------------------------------------------------
def test_no_broker_call():
    d = _decision()
    assert d["broker_execution_performed"] is False
    eco = json.loads((R1_1_DIR / "CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA.json")
                     .read_text(encoding="utf-8"))
    field_names = [f["name"] for f in eco["fields"]]
    for bad in ["broker lot", "margin", "order type", "fill mode", "slippage"]:
        assert bad not in field_names, f"broker field {bad} leaked into pure output"


# --- decision fields ---------------------------------------------------------
def test_decision_fields():
    d = _decision()
    assert d["checkpoint"] == r11b.CHECKPOINT
    assert d["status"] == "PASS"
    assert d["base_commit"] == "d51b9b4772f0bf2ee9a87deb830614e7494f25d1"
    assert d["r1_1_seal_verified"] is True
    assert d["execution_runtime_frozen_authority_sha"] == EXEC_FOUNDATION_FROZEN
    assert d["tb_frozen_authority_sha"] == TB_ENGINEERING_FROZEN
    assert d["frozen_commits_exist"] is True
    assert d["manifest_decision_sha_agreement"] is True
    assert d["current_branch_tip_equality_required"] is False
    assert d["network_required_by_tests"] is False
    assert d["git_fetch_used_by_tests"] is False
    assert d["foreign_branch_write_detected"] is False
    assert d["provenance_test_pass"] is True
    assert d["nonregression_pass"] is True
    assert d["broker_execution_performed"] is False
    assert d["d0_ready"] is True
    assert d["d0_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0"
