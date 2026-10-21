"""P2-R3-FREEZE — superseding operator-loop repair manifest + acceptance evidence.

History-preserving chain (P1-R1 / P2-R1 / P2-R2 convention):

- ``P2-freeze-manifest.json``    = original freeze artifact, unchanged;
- ``P2-R1-freeze-manifest.json`` = C07R structural repair manifest, unchanged;
- ``P2-R2-freeze-manifest.json`` = governance-wiring repair manifest, unchanged;
- ``P2-R3-freeze-manifest.json`` = THIS superseding manifest for the
  operator-loop/recovery/identity closure tranche, plus
  ``P2-R3-operator-acceptance.json`` recording machine-readable results of
  the five operator acceptance journeys.

Fail-closed contract: refuses to emit unless the full suite passes at the
expected commit and the output parses; counts are never hardcoded.

Run:  python qcae/implementation/tools/p2r3_freeze_manifest.py [expected_head_sha]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from qcae.implementation.tools.test_evidence import (  # noqa: E402
    FreezeEvidenceError,
    PYTEST_Q_PASS,
    capture_test_evidence,
    git_head_commit,
)

__all__ = ["build_manifest", "build_acceptance", "main"]

ORIGINAL_P2_FREEZE = "qcae/implementation/P2-freeze-manifest.json"
P2_R1_FREEZE = "qcae/implementation/P2-R1-freeze-manifest.json"
P2_R2_FREEZE = "qcae/implementation/P2-R2-freeze-manifest.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout.strip()


def _file_digest(relpath: str) -> str:
    data = (REPO_ROOT / relpath).read_bytes()
    return "sha256:" + hashlib.sha256(data).hexdigest()


#: Preserved history: original P2 build, R1 structural repairs, R2 wiring.
P2_ORIGINAL_COMMITS = [
    "ab0098c5", "52be767f", "534f7864", "766efa0d", "cb047e4a", "e1936d06",
    "fbe93cef", "21bc4466", "0603b882", "38e6ca66", "c531e12f", "49f6fdbc",
    "61488273", "afdbaa84", "8022b61d", "4cca8729",
]
P2_R1_COMMITS = [
    "425ac5f6", "3b5aaed0", "bfead6f6", "acf31b6f", "cb1cede4",
    "6ea6dcef", "ac0dd3c2", "ea493b8e", "a8b20a6c",
]
P2_R2_COMMITS = [
    "30cebe27", "407b7de9", "7f6bccb7", "e93f41dd", "3a7783ea",
    "4b88cbd7", "f1e02304", "8e8b9431", "4395aaa8", "a11d380a",
]

#: The operator-loop closure tranche (P2-R3, this manifest's subject).
P2_R3_COMMITS = [
    "07626a08",  # C01: job lifecycle truth
    "7ac5b80f",  # C02: worker availability before lease
    "66abe540",  # C03: one recovery law + active-lease protection
    "50256c6b",  # C04: identity binding into claim/execute
    "f3ceec59",  # C05: CLI typed errors + recovery convergence
    "c7fa5744",  # A01: operator acceptance harness
    "205b7b46",  # T01: adversarial qualification
    "6f0218c0",  # I0: findings + repair law recorded in ledger
]


def build_manifest(tested_commit: str, evidence: dict, acceptance: dict) -> dict:
    return {
        "phase": "P2-R3 — Operator Loop + Recovery + Identity Closure (superseding)",
        "supersedes": {
            "original_freeze_artifact": ORIGINAL_P2_FREEZE,
            "original_freeze_commit": "4cca8729",
            "original_freeze_digest": _file_digest(ORIGINAL_P2_FREEZE),
            "r1_freeze_artifact": P2_R1_FREEZE,
            "r1_freeze_digest": _file_digest(P2_R1_FREEZE),
            "r2_freeze_artifact": P2_R2_FREEZE,
            "r2_freeze_digest": _file_digest(P2_R2_FREEZE),
            "relationship": (
                "superseding repair manifest; the original P2 freeze and the "
                "P2-R1/P2-R2 repair manifests are preserved unchanged as "
                "historical truth"
            ),
        },
        "operator_review_trigger": (
            "Post-freeze live operator testing of P2-R2 head a11d380a: the "
            "1000-test suite passed while the real operator journey was "
            "broken — submit/run never finalized the job (finding A), no "
            "worker was registered so `job run` stranded a lease with a raw "
            "traceback (B), recovery deleted claims without reconciling "
            "steps and split across three disagreeing surfaces (C), recovery "
            "could force-expire ACTIVE leases (D), and unregistered id-* "
            "principals gained execution authority via policy string-match (E)"
        ),
        "canon_version": "0.1",
        "active_amendments": ["A-001 v1.0"],
        "branch": "qcae-capability-acquisition-engine",
        "head_commit": tested_commit,
        "tested_commit": tested_commit,
        "phase_commits": {
            "original_p2_build": P2_ORIGINAL_COMMITS,
            "p2_r1_structural_repairs": P2_R1_COMMITS,
            "p2_r2_governance_wiring": P2_R2_COMMITS,
            "p2_r3_operator_loop_closure": P2_R3_COMMITS,
        },
        "adr_refs": [
            "qcae/implementation/decisions/ADR-0006-persistence-architecture.md",
            "qcae/implementation/decisions/ADR-0007-repository-identity-vs-revision-identity.md",
            "qcae/implementation/decisions/ADR-0008-p2-runtime-state-vocabulary.md",
            "qcae/implementation/decisions/ADR-0009-policy-vs-authority-vocabularies.md",
        ],
        "prior_freeze_refs": [
            "qcae/implementation/P1-R1-freeze-manifest.json",
            ORIGINAL_P2_FREEZE + " (historical)",
            P2_R1_FREEZE + " (historical)",
            P2_R2_FREEZE + " (historical, superseded by this manifest)",
        ],
        "repairs": {
            "c01_job_lifecycle_truth": {
                "finding": "A — submit left the snapshot CREATED; JOB_SUCCEEDED unreachable in the natural flow",
                "repair": (
                    "submission commits the durable snapshot QUEUED with "
                    "JOB_CREATED + JOB_QUEUED exactly once and returns the "
                    "committed truth; a granted lease promotes the job "
                    "RUNNING (only when executable work actually runs); the "
                    "finalizer is reachable from any live state and emits "
                    "JOB_SUCCEEDED exactly once; empty graphs refused"
                ),
                "tests": "qcae/tests/unit/test_p2r3_c01_job_lifecycle.py",
            },
            "c02_worker_availability_before_lease": {
                "finding": "B — lease -> RUNNING -> missing worker -> raw traceback stranded the lease",
                "repair": (
                    "typed WorkerUnavailableError raised BEFORE any claim, "
                    "state mutation, attempt, budget, or STEP_STARTED; per-"
                    "step coverage (covered work proceeds while uncovered "
                    "steps stay READY); CLI renders WORKER_UNAVAILABLE as "
                    "exit 3 with structured output and no traceback; no "
                    "default production worker added (P3 supplies workers)"
                ),
                "tests": (
                    "qcae/tests/unit/test_p2r3_c02_worker_availability.py"
                ),
            },
            "c03_single_recovery_law": {
                "finding": "C/D — claim deletion without step reconciliation; three disagreeing surfaces; active leases stolen",
                "repair": (
                    "OrchestratorEngine.recover_leased_steps is the ONE "
                    "authoritative law: TTL-expired claims are released "
                    "(job-scoped) and their steps reconciled — READY if "
                    "replay-safe, COMMITTED finalized without replay, "
                    "NON_REPLAY_SAFE ambiguity escalates to WAITING_INPUT; "
                    "orphan RUNNING steps are explicitly classified; active "
                    "leases survive recover/resume; global recover and job "
                    "resume both delegate to this law"
                ),
                "tests": "qcae/tests/unit/test_p2r3_c03_recovery_law.py",
            },
            "c04_identity_binding": {
                "finding": "E — unregistered id-* principals matched policy by string; claim/execute principals unbound",
                "repair": (
                    "identity provider wired at the composition root; "
                    "require_worker_identity refuses unknown principals "
                    "BEFORE any claim row exists; execute_step enforces "
                    "claim-principal == execution-principal (no A-claim/"
                    "B-execute swap); identity semantics proven across restart"
                ),
                "tests": "qcae/tests/unit/test_p2r3_c04_identity_binding.py",
            },
            "c05_cli_typed_errors_and_recovery_convergence": {
                "finding": "expected operator errors surfaced as raw tracebacks; recovery surfaces disagreed",
                "repair": (
                    "stable exit codes (2 rejected/unknown, 3 worker "
                    "unavailable, 4 budget exhausted) with structured "
                    "stderr; unexpected programming errors still traceback; "
                    "job_resume and global recover delegate to the same law"
                ),
                "tests": "qcae/tests/unit/test_p2r3_c05_cli_typed_errors.py",
            },
        },
        "persistence": {
            "engine": "SQLite (stdlib sqlite3)",
            "metadata_schema_version": 4,
            "artifact_hash_algorithm": "sha256",
            "recovery_expiry": "TTL-checked only; force-expire reserved for governed internal paths",
        },
        "operator_acceptance_evidence": {
            "artifact": "qcae/implementation/P2-R3-operator-acceptance.json",
            "summary": acceptance,
        },
        "test_command": ["python", "-m", "pytest", "qcae/tests", "-q"],
        "test_results": evidence,
        "evidence_label": "LOCAL TEST EVIDENCE",
        "architecture_guard_evidence": {
            "core_stdlib_only": "qcae/tests/architecture/test_p0_dependency_guards.py",
            "engine_confined_to_infrastructure": True,
            "runtime_store_boundary": "orchestrator knows no _conn/table names",
            "interface_boundary": "TestInterfaceBoundary (no private reach-ins)",
            "oce_absent": "runtime reports OCE_ABSENT; no OCE import in qcae/",
        },
        "known_external_failures": [
            "tests/forge/phase_00/test_extension_docs.py: 2 pre-existing failures "
            "external to qcae/ (documented since P1; unchanged)",
        ],
        "deferred_design_debt": {
            "classification": "MINOR / DESIGN_DEBT_PARKED",
            "items": [
                "OrchestratorEngine decomposition (~850 lines, one owner per concern)",
                "QcaeApp vs LocalRuntimeService facade consolidation",
                "freeze-generator parameterization/deduplication across phases",
                "Permissive/FailClosed test gates moved out of the production module",
            ],
            "trigger": "P10 Agent Orchestration preparation, or earlier only if P3-P5 provide evidence it is needed",
        },
        "blockers": [],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def build_acceptance(tested_commit: str) -> dict:
    """Machine-readable operator acceptance evidence (directive §13).

    Recorded from the committed acceptance suite (qcae/tests/acceptance/
    test_p2_operator_loop.py), which exercises the real surface: persisted
    SQLite reopened across process boundaries and the CLI via subprocess.
    """
    return {
        "evidence_label": "LOCAL TEST EVIDENCE",
        "source_suite": "qcae/tests/acceptance/test_p2_operator_loop.py",
        "tested_commit": tested_commit,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "journeys": {
            "A_lifecycle_and_restart": {
                "submit_result": "durable snapshot QUEUED; JOB_CREATED + JOB_QUEUED each exactly once",
                "lifecycle_states": ["QUEUED", "RUNNING", "SUCCEEDED"],
                "event_sequence_law": (
                    "first granted lease -> RUNNING; final success -> "
                    "SUCCEEDED with exactly one JOB_SUCCEEDED; STEP_STARTED "
                    "for s-1 exactly once across the restart"
                ),
                "no_step_repeats_after_restart": True,
                "test": "TestJourneyA_CompleteLifecycle",
            },
            "B_no_worker_safety": {
                "result": "typed WORKER_UNAVAILABLE, CLI exit 3, structured stderr, no traceback",
                "lease_mutation": "none",
                "attempt_mutation": "none (attempt stays 0)",
                "budget_mutation": "none",
                "step_state_after": "READY",
                "active_claims_after": 0,
                "test": "TestJourneyB_NoWorkerSafety",
            },
            "C_active_lease_then_expired_recovery": {
                "active_lease_protection": (
                    "recover before TTL: zero steps recovered, lease token "
                    "and owner unchanged"
                ),
                "expired_lease_recovery": (
                    "after TTL: claim released, step reconciled READY, "
                    "re-claimable; job completes SUCCEEDED"
                ),
                "committed_step_not_repeated": True,
                "test": "TestJourneyC_CrashRecovery",
            },
            "D_identity_fail_closed": {
                "result": (
                    "unregistered id-attacker refused before lease (exit 2, "
                    "'unknown identity', no traceback); zero claim rows"
                ),
                "durable_truth": "policy/identity state unchanged by the refused request",
                "test": "TestJourneyD_IdentityFailClosed",
            },
            "E_approval_round_trip": {
                "result": (
                    "REQUIRE_APPROVAL -> durable request + WAITING_POLICY; "
                    "operator DENY -> immutable denial, step stays "
                    "WAITING_POLICY, worker never ran; APPROVAL_REQUESTED "
                    "and APPROVAL_DENIED events present"
                ),
                "worker_executions": 0,
                "test": "TestJourneyE_ApprovalRoundTrip",
            },
        },
    }


def main(expected_head: str | None = None) -> int:
    head = git_head_commit(str(REPO_ROOT))
    if expected_head and head != expected_head:
        print(f"FAIL: head {head} != expected {expected_head}", file=sys.stderr)
        return 2
    try:
        ev = capture_test_evidence(
            command=["python", "-m", "pytest", "qcae/tests", "-q"],
            success_pattern=PYTEST_Q_PASS,
            expected_commit=head,
            cwd=str(REPO_ROOT),
        )
    except FreezeEvidenceError as exc:
        print(f"FAIL: freeze evidence refused: {exc}", file=sys.stderr)
        return 3
    acceptance = build_acceptance(head)
    manifest = build_manifest(head, ev.as_manifest_block(), {
        "artifact": "qcae/implementation/P2-R3-operator-acceptance.json",
        "journeys": sorted(acceptance["journeys"]),
        "evidence_label": acceptance["evidence_label"],
    })
    impl = REPO_ROOT / "qcae" / "implementation"
    out = impl / "P2-R3-freeze-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    acc = impl / "P2-R3-operator-acceptance.json"
    acc.write_text(json.dumps(acceptance, indent=2, sort_keys=False), encoding="utf-8")
    print(f"freeze manifest written: {out}")
    print(f"acceptance evidence written: {acc}")
    print(f"tested commit: {head}")
    print(f"tests: {ev.collected} collected, {ev.passed} passed, "
          f"{ev.failed} failed, {ev.skipped} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
