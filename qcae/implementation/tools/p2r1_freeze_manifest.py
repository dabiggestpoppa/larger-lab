"""P2-R1-FREEZE — superseding repair manifest with real captured evidence.

History-preserving repair (P1-R1 convention):

- ``P2-freeze-manifest.json``   = the ORIGINAL freeze artifact, unchanged;
- ``P2-R1-freeze-manifest.json`` = THIS superseding manifest, which records
  the original freeze commit + digest, the operator-review trigger, the
  C07R repair commits, and fresh fail-closed test evidence captured from an
  actual full-suite run at the tested commit.

Fail-closed contract: refuses to emit unless the suite passes at the
expected commit and the output parses; counts are never hardcoded.

Run:  python qcae/implementation/tools/p2r1_freeze_manifest.py [expected_head_sha]
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

__all__ = ["build_manifest", "main"]

ORIGINAL_P2_FREEZE = "qcae/implementation/P2-freeze-manifest.json"

#: Commits of the original P2 build (I0..T01), preserved as history.
P2_ORIGINAL_COMMITS = [
    "ab0098c5",  # P2-I0: ADR-0008 + ADR-0009 + ledger transition
    "52be767f",  # P2-C01: runtime domain + state machines + step graph
    "534f7864",  # P2-C02: durable runtime store
    "766efa0d",  # P2-C03: durable queue + token-guarded leases
    "cb047e4a",  # P2-C04: identity + policy engine + authority provider
    "e1936d06",  # P2-C05: approval + escalation workflow
    "fbe93cef",  # P2-C06: Context Packet + worker contracts
    "21bc4466",  # P2-C07: orchestrator engine (REVIEWED HEAD)
    "0603b882",  # P2-C08: budget enforcement
    "38e6ca66",  # P2-C09: SecretProvider + redaction
    "c531e12f",  # P2-C10: standalone runtime service
    "49f6fdbc",  # P2-C11: composition factory + CLI
    "61488273",  # P2-C12: migration v3->v4 + backup/restore
    "afdbaa84",  # P2-T01: adversarial runtime qualification
    "8022b61d",  # P2-FREEZE: manifest generator
    "4cca8729",  # P2-FREEZE: original freeze artifact + ledger (SUPERSEDED)
]

#: The operator-directed C07R repair tranche + coverage closure.
P2_R1_REPAIR_COMMITS = [
    "425ac5f6",  # C07R1: job-scoped atomic queue claim
    "3b5aaed0",  # C07R2: durable idempotency/execution semantics
    "bfead6f6",  # C07R3: atomic job submission transaction
    "acf31b6f",  # C07R4: store-owned event/checkpoint identity allocation
    "cb1cede4",  # C07RT: combined crash/concurrency/adversarial suite
    "6ea6dcef",  # C11 gap closure: events/recover/decide + durable CLI sessions
    "ac0dd3c2",  # directive-coverage closure: budget race/policy-change/etc.
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout.strip()


def _original_freeze_digest() -> str:
    data = (REPO_ROOT / ORIGINAL_P2_FREEZE).read_bytes()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def build_manifest(tested_commit: str, evidence: dict) -> dict:
    return {
        "phase": "P2-R1 — Runtime Repair + Freeze Truth Repair (superseding)",
        "supersedes": {
            "original_freeze_artifact": ORIGINAL_P2_FREEZE,
            "original_freeze_commit": "4cca8729",
            "original_freeze_digest": _original_freeze_digest(),
            "relationship": (
                "superseding repair manifest; original P2 freeze artifact is "
                "preserved unchanged as historical truth"
            ),
        },
        "operator_review_trigger": (
            "Operator review of P2 C07 (accepted in concept, repair required): "
            "job-scoped lease claiming, idempotency crash window, atomic "
            "submission, event/store abstraction; P3 NOT authorized"
        ),
        "canon_version": "0.1",
        "active_amendments": ["A-001 v1.0"],
        "branch": "qcae-capability-acquisition-engine",
        "head_commit": tested_commit,
        "tested_commit": tested_commit,
        "phase_commits": {
            "original_p2_build": P2_ORIGINAL_COMMITS,
            "repair_tranche": P2_R1_REPAIR_COMMITS,
        },
        "adr_refs": [
            "qcae/implementation/decisions/ADR-0006-persistence-architecture.md",
            "qcae/implementation/decisions/ADR-0007-repository-identity-vs-revision-identity.md",
            "qcae/implementation/decisions/ADR-0008-p2-runtime-state-vocabulary.md",
            "qcae/implementation/decisions/ADR-0009-policy-vs-authority-vocabularies.md",
        ],
        "prior_freeze_refs": [
            "qcae/implementation/P1-R1-freeze-manifest.json",
            ORIGINAL_P2_FREEZE + " (historical, superseded by this manifest)",
        ],
        "repairs": {
            "c07r1_job_scoped_atomic_claim": {
                "defect": "global claim-then-filter could strand another job's READY step until TTL",
                "repair": "eligibility enforced inside the atomic claim selection; lost races fall through",
                "tests": "qcae/tests/unit/test_p2_c07r1_scoped_claim.py",
            },
            "c07r2_durable_execution_semantics": {
                "defect": "worker executed before completion marker; crash window allowed silent re-execution",
                "repair": (
                    "durable ExecutionRecords RESERVED/EXECUTING/COMMITTED/FAILED/ABANDONED with "
                    "result payloads; ReplaySafety classes; NON_REPLAY_SAFE ambiguity escalates, never reruns; "
                    "orchestrator claims at-least-once + durable dedup, never exactly-once"
                ),
                "tests": "qcae/tests/unit/test_p2_c07r2_execution_semantics.py (crash windows A-G)",
            },
            "c07r3_atomic_submission": {
                "defect": "submit() performed separate writes despite 'atomic' claim",
                "repair": "single BEGIN IMMEDIATE..COMMIT via RuntimeTransaction; failure injection rolls back all",
                "tests": "qcae/tests/unit/test_p2_c07r3_atomic_submit.py",
            },
            "c07r4_store_owned_identity": {
                "defect": "orchestrator accessed store._conn and derived event ids from row counts",
                "repair": (
                    "store allocates event_seq + collision-safe event_id and checkpoint ids; "
                    "orchestrator holds no counters; architecture guard forbids ._conn/table knowledge"
                ),
                "tests": (
                    "qcae/tests/unit/test_p2_c07r4_event_allocation.py + "
                    "test_p0_dependency_guards.py::TestRuntimeStoreBoundary"
                ),
            },
        },
        "persistence": {
            "engine": "SQLite (stdlib sqlite3)",
            "metadata_schema_version": 4,
            "artifact_hash_algorithm": "sha256",
            "migration_v3_to_v4": {
                "migration_id": "P2-0004-runtime-governance-tables",
                "evidence": "qcae/tests/unit/test_p2_migration_backup.py::TestMigrationV3ToV4",
            },
        },
        "vocabularies": {
            "job_states": [
                "CREATED", "QUEUED", "RUNNING", "WAITING", "WAITING_APPROVAL",
                "RETRY_PENDING", "SUCCEEDED", "FAILED", "CANCELLED", "BLOCKED",
            ],
            "step_states": [
                "PENDING", "READY", "RUNNING", "WAITING_POLICY", "WAITING_INPUT",
                "RETRY_SCHEDULED", "SUCCEEDED", "PARTIAL", "FAILED", "CANCELLED",
                "STALE",
            ],
            "failure_classes": [
                "TRANSIENT", "PERMANENT", "POLICY_DENIED", "APPROVAL_REQUIRED",
                "BUDGET_EXHAUSTED", "INVALID_INPUT", "DEPENDENCY_FAILED", "UNKNOWN",
            ],
            "execution_states": ["RESERVED", "EXECUTING", "COMMITTED", "FAILED", "ABANDONED"],
            "replay_safety_classes": ["REPLAY_SAFE", "IDEMPOTENCY_AWARE", "NON_REPLAY_SAFE"],
            "policy_decisions": ["ALLOW", "DENY", "REQUIRE_APPROVAL",
                                 "ALLOW_WITH_CONSTRAINTS"],
            "authority_outcomes": ["GRANT", "DENY", "REQUEST_MORE_EVIDENCE"],
            "approval_states": ["GRANTED", "DENIED", "EXPIRED"],
            "worker_result_status": [
                "SUCCESS", "PARTIAL", "FAILED", "BLOCKED_POLICY", "BLOCKED_INPUT",
                "INCONCLUSIVE", "RETRYABLE", "CANCELLED",
            ],
            "budget_states": ["ACTIVE", "EXHAUSTED", "EXCEEDED"],
            "budget_dimensions": [
                "attempts", "tool_calls", "network_requests",
                "sandbox_executions", "wall_clock_seconds", "artifact_bytes",
                "cost_units",
            ],
        },
        "queue_lease_semantics": {
            "claim": (
                "atomic, eligibility-scoped (job_id/eligible_step_ids inside the "
                "claim); guarded upsert; one active owner per step; empty "
                "eligibility creates no claim rows"
            ),
            "ack": "token-guarded; owner-only; single ack",
            "recovery": "expired/unacked claims reclaimed on restart",
            "priority": "not_before ASC; priority never bypasses policy state",
        },
        "event_semantics": {
            "identity": "store-allocated, collision-safe, unique-index guarded",
            "order": "durable monotonic event_seq; append-only; never rewritten",
            "emitter_access": "orchestrator knows no _conn/table names (guard enforced)",
        },
        "secret_provider_semantics": {
            "handles_not_values": True,
            "audit_records_values": False,
            "production_class_denied_by_default": True,
            "redaction": "centralized Redactor on failure paths",
        },
        "a001_compliance": {
            "research_mesh_boundary": "no Research Mesh implementation in qcae/core or runtime (guard-enforced)",
            "external_registry_ownership": "external owner domains preserved; refs are references, not authority",
            "economic_experience": "no runtime/marketplace authority granted by economic records",
            "fallback_research_budget": "A-001 fallback research cannot grow runtime authority",
        },
        "cli_commands": [
            "job list", "job status", "job events", "job run", "job resume",
            "job cancel", "approval list", "approval decide", "recover",
            "identity",
        ],
        "test_command": ["python", "-m", "pytest", "qcae/tests", "-q"],
        "test_results": evidence,
        "evidence_label": "LOCAL TEST EVIDENCE",
        "migration_evidence": {
            "test": "test_p2_migration_backup.py::TestMigrationV3ToV4",
            "result": "v3 migrates to v4; P1 registry rows preserved; runtime/governance tables additive",
        },
        "crash_recovery_evidence": {
            "tests": [
                "test_p2_recovery.py::TestCrashRecovery",
                "test_p2_c07r2_execution_semantics.py::TestCrashWindows",
                "test_p2_c07rt_repair_qualification.py::TestCombinedFlows",
            ],
            "result": (
                "completed steps never repeated; expired leases recovered; "
                "NON_REPLAY_SAFE ambiguity escalated; authority rechecked after restart"
            ),
        },
        "backup_restore_evidence": {
            "test": "test_p2_migration_backup.py::TestBackupRestoreRuntime",
            "result": "jobs/steps/checkpoints/budgets/approvals restored exactly; stale leases recoverable",
        },
        "architecture_guard_evidence": {
            "core_stdlib_only": "qcae/tests/architecture/test_p0_dependency_guards.py",
            "engine_confined_to_infrastructure": "governance/interfaces use ports only",
            "runtime_store_boundary": "TestRuntimeStoreBoundary forbids ._conn/table knowledge in orchestration",
            "oce_absent": "runtime identity reports OCE_ABSENT; no OCE import anywhere in qcae/",
        },
        "known_external_failures": [
            "tests/forge/phase_00/test_extension_docs.py: 2 pre-existing failures "
            "external to qcae/ (documented since P1; unchanged)",
        ],
        "deferred_items": [
            "heartbeat-based lease liveness (single-process P2 model uses restart-based recovery)",
            "HTTP API surface (QcaeApp is the stable boundary; thin adapters later)",
            "OCE governance migration (P12; provider seam in place)",
        ],
        "blockers": [],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    manifest = build_manifest(head, ev.as_manifest_block())
    out = REPO_ROOT / "qcae" / "implementation" / "P2-R1-freeze-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    print(f"freeze manifest written: {out}")
    print(f"tested commit: {head}")
    print(f"tests: {ev.collected} collected, {ev.passed} passed, "
          f"{ev.failed} failed, {ev.skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
