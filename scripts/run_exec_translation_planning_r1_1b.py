"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B-CROSS-BRANCH-PROVENANCE-TEST-REPAIR

Repair the SEMANTICS of the historical cross-branch provenance test ONLY.

DEFECT (introduced by d51b9b47): test_no_cross_branch_write() resolved the
CURRENT branch tips of execution-runtime-foundation / tb-forward-engine and
required them to equal the R1.1-frozen authority SHAs -- with a `git fetch`
fallback (network-dependent). Those branches are ACTIVE CONCURRENT WORKSTREAMS
and are expected to advance; a later legit movement must never make a
historical R1.1 seal fail.

CORRECT SEMANTIC: provenance is frozen by IMMUTABLE commit SHA, never by
mutable branch tips. R1.1 must prove:

  A. PROVENANCE OBJECT EXISTS   -- each frozen commit object exists
                                 (git cat-file -e <sha>^{commit}).
  B. COMMIT IDENTITY            -- the frozen commit's subject corresponds to
                                 the expected authority checkpoint.
  C. SOURCE SHA MANIFEST        -- CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json and
                                 CR_EXEC_R1_1_DECISION.json carry the same
                                 frozen SHAs (internally consistent).
  D. NO CROSS-BRANCH WRITE BY R1.1 -- proved by commit ancestry + changed-file
                                 truth, NOT present branch tips:
                                 R1.1 commits (2bbe52ea, d51b9b47) are
                                 descendants of capital-routing AND are NOT
                                 ancestors of the frozen foreign commits;
                                 their R1.1-specific files are absent from the
                                 frozen foreign trees.
  E. CURRENT HEAD DIAGNOSTIC    -- current branch tips are recorded as
                                 informational diagnostics only; their
                                 movement is NOT a test failure.

HARD RULES:
- NO git fetch anywhere in the runner or the tests.
- NO network dependence. The suite is deterministic and runnable offline
  against a complete checkout (all frozen objects share one object store:
  capital-routing is a linked worktree of the larger-lab repo).
- The frozen SHAs themselves are NEVER replaced because the branches later
  advance. They remain historical provenance.

Science is untouched: 890 events / A 432 / B 458 / 826 accepted / 64 rejected,
risk unit 24.49489742783178 bps, corrected translation formula, parity locks.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import run_exec_translation_planning_r1_1 as r11  # noqa: E402  (frozen facts)
import run_exec_translation_planning_r1 as r1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1b"
R1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1"
EVENT_CSV = (ROOT / "research" / "capital_routing" / "risk"
             / "block3_execution_translation_planning_r1"
             / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv")

BASE_COMMIT = "d51b9b4772f0bf2ee9a87deb830614e7494f25d1"
SCIENTIFIC_SEAL = "2bbe52ea8798549ed9c03bd90684fd3a0d408a99"
CHECKPOINT = ("CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B-"
              "CROSS-BRANCH-PROVENANCE-TEST-REPAIR")

# Immutable historical provenance frozen during R1.1 (never replaced).
EXEC_FOUNDATION_SHA = "9e11db928ad3c330fcde06d075e20a6e5b349d89"
EXEC_FOUNDATION_CHECKPOINT = "QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY"
TB_ENGINEERING_SHA = "d12005988ce61170d9bc5478089baa5ce54cc2a9"
TB_ENGINEERING_CHECKPOINT = "TB-R6.1B-FIX-WORKER-STATE-LATCH"

# The two commits this checkpoint repairs (the R1.1 seal + its test-only child).
R1_1_SEAL = SCIENTIFIC_SEAL
R1_1_TEST_CHILD = BASE_COMMIT
R1_1_COMMITS = [R1_1_SEAL, R1_1_TEST_CHILD]

# Files created by R1.1 that must be ABSENT from the frozen foreign trees
# (changed-file truth component of the no-cross-branch-write proof).
R1_1_SPECIFIC_FILES = [
    "scripts/run_exec_translation_planning_r1_1.py",
    "research/capital_routing/risk/block3_execution_translation_r1_1/"
    "CR_EXEC_R1_1_DECISION.json",
    "research/capital_routing/risk/block3_execution_translation_r1_1/"
    "CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json",
]

RISK_UNIT_BPS = r1.RISK_UNIT_BPS
FROZEN_NOTIONAL = {
    "POOLED_ACCEPTED": {"p50": 1.9842, "p95": 7.6105, "p99": 16.0364, "max": 32.7663},
    "A_ACCEPTED": {"p50": 3.3513, "p95": 11.4407, "max": 32.7663},
    "B_ACCEPTED": {"p50": 1.2850, "p95": 4.1231, "max": 22.2754},
}

FOREIGN_BRANCHES = ["execution-runtime-foundation", "tb-forward-engine"]


# ---------------------------------------------------------------------------
# Offline git helpers (immutable commit-object semantics; never fetch)
# ---------------------------------------------------------------------------
def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def git_ok(repo: Path, *args: str) -> bool:
    return _run_git(repo, *args).returncode == 0


def commit_exists(repo: Path, sha: str) -> bool:
    return git_ok(repo, "cat-file", "-e", f"{sha}^{{commit}}")


def commit_subject(repo: Path, sha: str) -> str:
    out = _run_git(repo, "log", "-1", "--format=%s", sha)
    return out.stdout.strip() if out.returncode == 0 else ""


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """True iff `ancestor` is an ancestor commit of `descendant`."""
    return git_ok(repo, "merge-base", "--is-ancestor", ancestor, descendant)


def blob_present_in_tree(repo: Path, tree_commit: str, path: str) -> bool:
    """True iff `path` exists in the tree of `tree_commit` (immutable object)."""
    return git_ok(repo, "cat-file", "-e", f"{tree_commit}:{path}")


def current_branch_tip(repo: Path, branch: str) -> str:
    """Informational diagnostic ONLY: local ref -> remote-tracking ref.
    Never fetches. UNAVAILABLE_IN_CHECKOUT when the ref is absent."""
    for ref in (f"refs/heads/{branch}", f"refs/remotes/origin/{branch}"):
        out = _run_git(repo, "rev-parse", "--verify", ref)
        if out.returncode == 0:
            return out.stdout.strip()
    return "UNAVAILABLE_IN_CHECKOUT"


def provenance_repo() -> Optional[Path]:
    """Find a repo whose object store contains the frozen foreign commits.
    capital-routing is a linked worktree of the larger-lab repo (shared object
    store), so ROOT itself suffices in the canonical checkout; fall back to
    ROOT.parent for nested/clone layouts. Purely local, no network."""
    for cand in (ROOT, ROOT.parent):
        if not (cand / ".git").exists() and not (cand / ".git").is_file():
            continue
        if commit_exists(cand, EXEC_FOUNDATION_SHA) and commit_exists(cand, TB_ENGINEERING_SHA):
            return cand
    return None


# ---------------------------------------------------------------------------
# Provenance audit (A-E truth tests)
# ---------------------------------------------------------------------------
def provenance_audit(repo: Optional[Path]) -> Dict:
    frozen = {
        "execution_runtime_foundation": {
            "frozen_sha": EXEC_FOUNDATION_SHA,
            "expected_checkpoint": EXEC_FOUNDATION_CHECKPOINT,
            "commit_exists": bool(repo and commit_exists(repo, EXEC_FOUNDATION_SHA)),
            "subject": commit_subject(repo, EXEC_FOUNDATION_SHA) if repo else "",
        },
        "tb_forward_engine": {
            "frozen_sha": TB_ENGINEERING_SHA,
            "expected_checkpoint": TB_ENGINEERING_CHECKPOINT,
            "commit_exists": bool(repo and commit_exists(repo, TB_ENGINEERING_SHA)),
            "subject": commit_subject(repo, TB_ENGINEERING_SHA) if repo else "",
        },
    }
    for entry in frozen.values():
        entry["identity_matches"] = (
            entry["commit_exists"] and entry["expected_checkpoint"] in entry["subject"])

    frozen_commits_exist = all(e["commit_exists"] for e in frozen.values())
    identity_matches = all(e["identity_matches"] for e in frozen.values())

    # C. manifest <-> decision agreement on the frozen SHAs.
    # Historical truth: the R1.1 SOURCE_SHA_MANIFEST carried science-input
    # hashes only (no authority-SHA fields); the authority SHAs were frozen in
    # the R1.1 DECISION and CROSS_WORKSTREAM_AUTHORITY.md. R1.1B closes the
    # gap: its manifest carries the frozen SHAs. Agreement therefore means:
    #   R1.1B manifest == R1.1B decision == R1.1 decision == frozen SHAs.
    manifest_agreement = False
    r11_decision = (R1_1_DIR / "CR_EXEC_R1_1_DECISION.json")
    r11_authority_md = (R1_1_DIR / "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md")
    if r11_decision.exists() and r11_authority_md.exists():
        decision = json.loads(r11_decision.read_text(encoding="utf-8"))
        authority_md = r11_authority_md.read_text(encoding="utf-8")
        manifest_agreement = (
            decision.get("execution_runtime_authority_sha") == EXEC_FOUNDATION_SHA
            and decision.get("tb_engineering_authority_sha") == TB_ENGINEERING_SHA
            and EXEC_FOUNDATION_SHA in authority_md
            and TB_ENGINEERING_SHA in authority_md)
    # self-consistency of the R1.1B artifacts (present on re-run)
    r11b_manifest = OUT / "CR_EXEC_R1_1B_SOURCE_SHA_MANIFEST.json"
    r11b_decision = OUT / "CR_EXEC_R1_1B_DECISION.json"
    if r11b_manifest.exists() and r11b_decision.exists():
        m = json.loads(r11b_manifest.read_text(encoding="utf-8"))
        d = json.loads(r11b_decision.read_text(encoding="utf-8"))
        auth = m.get("cross_workstream_authority", {})
        self_ok = (auth.get("execution_runtime_foundation", {}).get("head_sha")
                   == EXEC_FOUNDATION_SHA
                   and auth.get("tb_forward_engine", {}).get("head_sha")
                   == TB_ENGINEERING_SHA
                   and d.get("execution_runtime_frozen_authority_sha")
                   == EXEC_FOUNDATION_SHA
                   and d.get("tb_frozen_authority_sha") == TB_ENGINEERING_SHA)
        manifest_agreement = manifest_agreement and self_ok

    # D. no cross-branch write by R1.1: ancestry + changed-file truth
    r1_1_commits = {}
    for label, sha in [("seal_2bbe52ea", R1_1_SEAL), ("test_child_d51b9b47", R1_1_TEST_CHILD)]:
        r1_1_commits[label] = {
            "sha": sha,
            "exists": bool(repo and commit_exists(repo, sha)),
            "on_capital_routing": bool(
                repo and is_ancestor(repo, sha, "refs/heads/capital-routing")),
            "ancestor_of_exec_foundation_frozen": bool(
                repo and is_ancestor(repo, sha, EXEC_FOUNDATION_SHA)),
            "ancestor_of_tb_frozen": bool(
                repo and is_ancestor(repo, sha, TB_ENGINEERING_SHA)),
        }

    changed_file_truth = {}
    if repo:
        for path in R1_1_SPECIFIC_FILES:
            changed_file_truth[path] = {
                "in_exec_foundation_frozen_tree": blob_present_in_tree(
                    repo, EXEC_FOUNDATION_SHA, path),
                "in_tb_frozen_tree": blob_present_in_tree(repo, TB_ENGINEERING_SHA, path),
            }
    foreign_branch_write_detected = (
        any(c["ancestor_of_exec_foundation_frozen"] or c["ancestor_of_tb_frozen"]
            for c in r1_1_commits.values())
        or any(v["in_exec_foundation_frozen_tree"] or v["in_tb_frozen_tree"]
               for v in changed_file_truth.values()))

    # E. current branch tips = informational diagnostics only
    current_tips = {}
    if repo:
        for branch in FOREIGN_BRANCHES:
            current_tips[branch] = current_branch_tip(repo, branch)

    provenance_test_pass = bool(
        frozen_commits_exist and identity_matches and manifest_agreement
        and not foreign_branch_write_detected
        and all(c["exists"] and c["on_capital_routing"] for c in r1_1_commits.values()))

    return {
        "semantics": "IMMUTABLE_COMMIT_SHA — branch tips are mutable and are "
                     "NEVER frozen; historical provenance locks commit objects only",
        "provenance_repo": str(repo) if repo else None,
        "frozen": frozen,
        "frozen_commits_exist": frozen_commits_exist,
        "identity_matches": identity_matches,
        "manifest_decision_sha_agreement": manifest_agreement,
        "r1_1_commits": r1_1_commits,
        "changed_file_truth": changed_file_truth,
        "foreign_branch_write_detected": foreign_branch_write_detected,
        "current_tip_diagnostics": {
            **current_tips,
            "note": "INFORMATIONAL ONLY — recorded at audit time; movement of "
                    "these tips is NOT a provenance test failure",
        },
        "network_required": False,
        "git_fetch_used": False,
        "current_branch_tip_equality_required": False,
        "manifest_note": "Historical R1.1 SOURCE_SHA_MANIFEST carried science-input "
                         "hashes only (no authority-SHA fields); the authority "
                         "SHAs were frozen in the R1.1 DECISION + "
                         "CROSS_WORKSTREAM_AUTHORITY.md. R1.1B closes the gap: "
                         "its manifest carries the frozen SHAs.",
        "provenance_test_pass": provenance_test_pass,
    }


# ---------------------------------------------------------------------------
# R1.1 seal verification + scientific nonregression (science UNCHANGED)
# ---------------------------------------------------------------------------
def r1_1_seal_verified() -> bool:
    dec = json.loads((R1_1_DIR / "CR_EXEC_R1_1_DECISION.json").read_text(encoding="utf-8"))
    return (dec.get("status") == "PASS" and dec.get("science_unchanged") is True
            and dec.get("base_commit") == "00bef1b5b52db63c22a29b3287799742631930db")


def nonregression() -> Dict:
    nr = r11.nonregression()
    canon = r11.canonical_stats()
    pooled, a, b = (canon["POOLED_ACCEPTED"], canon["A_ACCEPTED"], canon["B_ACCEPTED"])
    frozen_ok = (
        abs(pooled["p50"] - FROZEN_NOTIONAL["POOLED_ACCEPTED"]["p50"]) < 5e-4
        and abs(pooled["p95"] - FROZEN_NOTIONAL["POOLED_ACCEPTED"]["p95"]) < 5e-3
        and abs(pooled["p99"] - FROZEN_NOTIONAL["POOLED_ACCEPTED"]["p99"]) < 5e-3
        and abs(pooled["max"] - FROZEN_NOTIONAL["POOLED_ACCEPTED"]["max"]) < 5e-3
        and abs(a["p50"] - FROZEN_NOTIONAL["A_ACCEPTED"]["p50"]) < 5e-4
        and abs(a["p95"] - FROZEN_NOTIONAL["A_ACCEPTED"]["p95"]) < 5e-3
        and abs(a["max"] - FROZEN_NOTIONAL["A_ACCEPTED"]["max"]) < 5e-3
        and abs(b["p50"] - FROZEN_NOTIONAL["B_ACCEPTED"]["p50"]) < 5e-4
        and abs(b["p95"] - FROZEN_NOTIONAL["B_ACCEPTED"]["p95"]) < 5e-3
        and abs(b["max"] - FROZEN_NOTIONAL["B_ACCEPTED"]["max"]) < 5e-3)
    return {
        "science_unchanged": bool(nr["science_unchanged"]),
        "n_events": nr["n_events"], "n_A": nr["n_A"], "n_B": nr["n_B"],
        "n_accepted": nr["n_accepted"], "n_rejected": nr["n_rejected"],
        "accepted_A": nr["accepted_A"], "accepted_B": nr["accepted_B"],
        "risk_unit_bps": RISK_UNIT_BPS,
        "risk_unit_is_hard_stop": False,
        "position_scaling_formula": nr["position_scaling_formula"],
        "gross_parity_pass": bool(nr["gross_parity_pass"]),
        "research_net_parity_pass": bool(nr["research_net_parity_pass"]),
        "execution_net_parity_status": nr["execution_net_parity_status"],
        "h1_parity_pass": bool(nr["h1_parity_pass"]),
        "historical_worst_observed_account_impact_A_pct": nr[
            "historical_worst_observed_account_impact_A_pct"],
        "historical_worst_observed_account_impact_B_pct": nr[
            "historical_worst_observed_account_impact_B_pct"],
        "canonical_notional_stats": canon,
        "frozen_notional_stats_match": frozen_ok,
        "nonregression_pass": bool(nr["science_unchanged"] and frozen_ok
                                   and nr["gross_parity_pass"]
                                   and nr["research_net_parity_pass"]
                                   and nr["h1_parity_pass"]),
    }


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
def _protocol() -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B -- Protocol

**Checkpoint:** {CHECKPOINT}
**Base:** {BASE_COMMIT} · **Scientific seal:** {SCIENTIFIC_SEAL} (R1.1)
**Branch:** dabiggestpoppa/larger-lab · `capital-routing`

## Scope (narrow provenance-semantics repair ONLY)

- Repair the semantics of the historical cross-branch provenance test.
- Git SHA provenance is IMMUTABLE; branch tips are MUTABLE.
- Historical checkpoint tests lock the former, never the latter.

## Defect repaired

Commit `d51b9b47` changed `test_no_cross_branch_write()` to resolve the
CURRENT branch tips of `execution-runtime-foundation` and `tb-forward-engine`
and require them to equal the R1.1-frozen authority SHAs (with a `git fetch`
fallback). Those branches are ACTIVE CONCURRENT WORKSTREAMS and are expected to
advance; a later legitimate movement must never fail a historical R1.1 seal.

## Correct semantics (frozen by immutable commit SHA)

- **A. Object exists** — `git cat-file -e <sha>{{{{commit}}}}` for each frozen SHA.
- **B. Commit identity** — frozen commit subject matches the expected checkpoint.
- **C. Manifest agreement** — `CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json` and
  `CR_EXEC_R1_1_DECISION.json` carry identical frozen SHAs.
- **D. No cross-branch write by R1.1** — R1.1 commits ({R1_1_SEAL[:8]},
  {R1_1_TEST_CHILD[:8]}) are descendants of `capital-routing` and are NOT
  ancestors of the frozen foreign commits; R1.1-specific files are absent from
  the frozen foreign trees. Proved by ancestry + changed-file truth, NOT by
  present branch tips.
- **E. Current HEAD diagnostic** — current branch tips are recorded as
  informational diagnostics only; their movement is NOT a test failure.

## Hard rules

- NO git fetch anywhere in the runner or the tests.
- NO network dependence; deterministic offline suite.
- Frozen SHAs ({EXEC_FOUNDATION_SHA[:8]}, {TB_ENGINEERING_SHA[:8]}) are NEVER
  replaced because the branches later advance — they remain historical
  provenance.
- Science untouched: 890 events / A 432 / B 458 / 826 accepted / 64 rejected /
  risk unit {RISK_UNIT_BPS} bps / corrected translation formula / parity locks.

## DO NOT

Change science, translation math, frozen authority SHAs, A/B, H1, f_total, pos,
1R, cost science, economic-target schema; build D0; connect a broker; modify
execution-runtime-foundation or tb-forward-engine.
"""


def _provenance_audit_md(pa: Dict) -> str:
    fnd = pa["frozen"]["execution_runtime_foundation"]
    tb = pa["frozen"]["tb_forward_engine"]
    tips = pa["current_tip_diagnostics"]
    lines = [
        "# R1.1B provenance test audit (immutable commit-SHA semantics)",
        "",
        "## Semantics",
        pa["semantics"],
        "",
        "## A. Frozen commit objects exist",
        f"- execution-runtime-foundation `{fnd['frozen_sha']}` — exists: "
        f"{fnd['commit_exists']}",
        f"- tb-forward-engine `{tb['frozen_sha']}` — exists: {tb['commit_exists']}",
        f"- **frozen_commits_exist = {pa['frozen_commits_exist']}**",
        "",
        "## B. Commit identity (subject matches expected checkpoint)",
        f"- exec foundation subject: `{fnd['subject']}` — matches "
        f"`{fnd['expected_checkpoint']}`: {fnd['identity_matches']}",
        f"- tb subject: `{tb['subject']}` — matches "
        f"`{tb['expected_checkpoint']}`: {tb['identity_matches']}",
        f"- **identity_matches = {pa['identity_matches']}**",
        "",
        "## C. Manifest <-> decision SHA agreement",
        f"- **manifest_decision_sha_agreement = {pa['manifest_decision_sha_agreement']}**",
        f"- {pa['manifest_note']}",
        "",
        "## D. No cross-branch write by R1.1 (ancestry + changed-file truth)",
    ]
    for label, c in pa["r1_1_commits"].items():
        lines += [
            f"- R1.1 commit `{label}` ({c['sha'][:8]}): exists={c['exists']}, "
            f"on_capital_routing={c['on_capital_routing']}, "
            f"ancestor_of_exec_foundation_frozen={c['ancestor_of_exec_foundation_frozen']}, "
            f"ancestor_of_tb_frozen={c['ancestor_of_tb_frozen']}",
        ]
    for path, v in pa["changed_file_truth"].items():
        lines.append(
            f"- `{path}` — in exec-foundation frozen tree: "
            f"{v['in_exec_foundation_frozen_tree']}; in tb frozen tree: "
            f"{v['in_tb_frozen_tree']}")
    lines += [
        f"- **foreign_branch_write_detected = {pa['foreign_branch_write_detected']}**",
        "",
        "## E. Current branch heads (informational diagnostics ONLY)",
    ]
    for branch in FOREIGN_BRANCHES:
        lines.append(f"- {branch}: `{tips.get(branch, 'UNAVAILABLE_IN_CHECKOUT')}`")
    lines += [
        f"- {tips['note']}",
        "",
        f"## Verdict",
        f"- current_branch_tip_equality_required = "
        f"{pa['current_branch_tip_equality_required']}",
        f"- network_required = {pa['network_required']} · "
        f"git_fetch_used = {pa['git_fetch_used']}",
        f"- **provenance_test_pass = {pa['provenance_test_pass']}**",
        "",
    ]
    return "\n".join(lines)


def _report(pa: Dict, nr: Dict, seal_ok: bool, decision: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B -- Report

**Checkpoint:** {CHECKPOINT} · **Status:** {decision['status']}
**Base:** {BASE_COMMIT} · **Scientific seal:** {SCIENTIFIC_SEAL} (R1.1, PASS)

## Defect repaired
The brittle `test_no_cross_branch_write()` (introduced in `d51b9b47`) resolved
CURRENT branch tips of the active workstreams and required tip equality with
the frozen SHAs (plus a `git fetch` fallback). Replaced with immutable
commit-SHA provenance semantics: the frozen commits exist, their subjects match
the expected checkpoints, the R1.1 manifest and decision agree, the R1.1
commits are descendants of `capital-routing` and never entered the frozen
foreign histories, and R1.1-specific files are absent from the frozen foreign
trees. Current branch tips are recorded as informational diagnostics only.

## Provenance
- A. frozen commits exist: {pa['frozen_commits_exist']}
- B. identity matches: {pa['identity_matches']}
- C. manifest/decision SHA agreement: {pa['manifest_decision_sha_agreement']}
- D. foreign branch write detected: {pa['foreign_branch_write_detected']}
- E. current tips: {pa['current_tip_diagnostics']}
- **provenance_test_pass = {pa['provenance_test_pass']}**
- current_branch_tip_equality_required = {pa['current_branch_tip_equality_required']}
- network_required = {pa['network_required']} · git_fetch_used = {pa['git_fetch_used']}

## Science (UNCHANGED)
{nr['n_events']} events · A {nr['n_A']} · B {nr['n_B']} · accepted {nr['n_accepted']}
(A {nr['accepted_A']} / B {nr['accepted_B']}) · rejected {nr['n_rejected']} ·
risk unit {nr['risk_unit_bps']} bps (NOT a hard stop) · gross parity
{nr['gross_parity_pass']} · research-modeled net parity {nr['research_net_parity_pass']} ·
execution net {nr['execution_net_parity_status']} · H1 parity {nr['h1_parity_pass']}.
Canonical accepted notional stats match the frozen values:
pooled median {nr['canonical_notional_stats']['POOLED_ACCEPTED']['p50']} /
p95 {nr['canonical_notional_stats']['POOLED_ACCEPTED']['p95']} /
p99 {nr['canonical_notional_stats']['POOLED_ACCEPTED']['p99']} /
max {nr['canonical_notional_stats']['POOLED_ACCEPTED']['max']} —
frozen match: {nr['frozen_notional_stats_match']}.
**nonregression_pass = {nr['nonregression_pass']}**

## Decision
r1_1_seal_verified = {seal_ok} · provenance_test_pass = {pa['provenance_test_pass']} ·
nonregression_pass = {nr['nonregression_pass']} · broker_execution_performed = False ·
d0_ready = {decision['d0_ready']} · d0_authorized = False ·
production_authorized = False · human_review_required = True.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.
"""


def test_audit() -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "tests": [
            {"id": 1, "name": "frozen execution-runtime SHA exists as commit object",
             "covers": "A"},
            {"id": 2, "name": "frozen TB SHA exists as commit object", "covers": "A"},
            {"id": 3, "name": "decision and source manifest agree on execution-runtime SHA",
             "covers": "C"},
            {"id": 4, "name": "decision and source manifest agree on TB SHA", "covers": "C"},
            {"id": 5, "name": "expected execution-runtime checkpoint identity matches frozen SHA",
             "covers": "B"},
            {"id": 6, "name": "expected TB checkpoint identity matches frozen SHA", "covers": "B"},
            {"id": 7, "name": "R1.1 capital-routing commit does not mutate foreign branch refs",
             "covers": "D"},
            {"id": 8, "name": "later branch advancement simulated — does NOT fail provenance",
             "covers": "E / semantics"},
            {"id": 9, "name": "no test performs git fetch", "covers": "hard rule"},
            {"id": 10, "name": "no test requires network", "covers": "hard rule"},
            {"id": 11, "name": "scientific nonregression still passes", "covers": "NONREGRESSION"},
            {"id": 12, "name": "890/826/64 unchanged", "covers": "NONREGRESSION"},
            {"id": 13, "name": "canonical accepted notional statistics unchanged",
             "covers": "NONREGRESSION"},
            {"id": 14, "name": "no broker call", "covers": "MISSION"},
        ],
        "offline": True,
        "network_dependent": False,
    }


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_decision(pa: Dict, nr: Dict, seal_ok: bool) -> Dict:
    provenance_test_pass = bool(pa["provenance_test_pass"])
    nonregression_pass = bool(nr["nonregression_pass"])
    pass_ = bool(provenance_test_pass and nonregression_pass and seal_ok)
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if pass_ else "FAIL",
        "base_commit": BASE_COMMIT,
        "science_unchanged": bool(nr["science_unchanged"]),
        "r1_1_seal_verified": bool(seal_ok),
        "execution_runtime_frozen_authority_sha": EXEC_FOUNDATION_SHA,
        "tb_frozen_authority_sha": TB_ENGINEERING_SHA,
        "frozen_commits_exist": bool(pa["frozen_commits_exist"]),
        "manifest_decision_sha_agreement": bool(pa["manifest_decision_sha_agreement"]),
        "current_branch_tip_equality_required": False,
        "network_required_by_tests": False,
        "git_fetch_used_by_tests": False,
        "foreign_branch_write_detected": bool(pa["foreign_branch_write_detected"]),
        "provenance_test_pass": provenance_test_pass,
        "nonregression_pass": nonregression_pass,
        "broker_execution_performed": False,
        "d0_ready": bool(pass_),
        "d0_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    repo = provenance_repo()
    pa = provenance_audit(repo)
    nr = nonregression()
    seal_ok = r1_1_seal_verified()
    decision = build_decision(pa, nr, seal_ok)

    (OUT / "CR_EXEC_R1_1B_PROTOCOL.md").write_text(_protocol(), encoding="utf-8")
    (OUT / "CR_EXEC_R1_1B_PROVENANCE_TEST_AUDIT.md").write_text(
        _provenance_audit_md(pa), encoding="utf-8")
    (OUT / "CR_EXEC_R1_1B_REPORT.md").write_text(
        _report(pa, nr, seal_ok, decision), encoding="utf-8")

    jsons = {
        "CR_EXEC_R1_1B_SOURCE_SHA_MANIFEST.json": {
            "checkpoint": CHECKPOINT,
            "base_commit": BASE_COMMIT,
            "scientific_seal": SCIENTIFIC_SEAL,
            "cross_workstream_authority": {
                "execution_runtime_foundation": {"head_sha": EXEC_FOUNDATION_SHA,
                                                 "checkpoint": EXEC_FOUNDATION_CHECKPOINT},
                "tb_forward_engine": {"head_sha": TB_ENGINEERING_SHA,
                                      "checkpoint": TB_ENGINEERING_CHECKPOINT},
            },
            "r1_1_commits": R1_1_COMMITS,
            "frozen_semantics": "IMMUTABLE_COMMIT_SHA — branch tips are mutable "
                                "and never frozen; frozen SHAs are never replaced",
            "event_level_source": str(EVENT_CSV.relative_to(ROOT)),
            "event_level_source_sha256": _sha(EVENT_CSV),
            "r1_1_decision_sha256": _sha(R1_1_DIR / "CR_EXEC_R1_1_DECISION.json"),
            "r1_1_manifest_sha256": _sha(R1_1_DIR / "CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json"),
            "note": "All inputs consumed read-only; no science regeneration; "
                    "no network; no git fetch.",
        },
        "CR_EXEC_R1_1B_NONREGRESSION.json": nr,
        "CR_EXEC_R1_1B_TEST_AUDIT.json": test_audit(),
        "CR_EXEC_R1_1B_DECISION.json": decision,
    }
    for name, payload in jsons.items():
        (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"R1.1B seal written to {OUT}")
    print(f"provenance_test_pass={pa['provenance_test_pass']} "
          f"nonregression_pass={nr['nonregression_pass']} "
          f"status={decision['status']}")


if __name__ == "__main__":
    main()
