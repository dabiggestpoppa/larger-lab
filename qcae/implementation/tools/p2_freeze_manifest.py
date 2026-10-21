"""P2-FREEZE — freeze manifest with real machine-readable test evidence (§43).

Emits ``P2-freeze-manifest.json``: phase vocabularies, commit ledger, ADRs,
schema version, migration/crash-recovery/backup evidence references, and the
test-results block captured from an actual full-suite run via the fail-closed
helper (P1-R1 mechanism). Fail-closed contract: refuses to emit unless the
suite passes at the expected commit and results parse; counts are never
hardcoded.

Run:  python qcae/implementation/tools/p2_freeze_manifest.py [expected_head_sha]
"""

from __future__ import annotations

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

P2_COMMITS = [
    "ab0098c5",  # P2-I0: ADR-0008 + ADR-0009 + ledger transition
    "52be767f",  # P2-C01: runtime domain + state machines + step graph
    "534f7864",  # P2-C02: durable runtime store (jobs/steps/events/checkpoints)
    "766efa0d",  # P2-C03: durable queue + token-guarded leases
    "cb047e4a",  # P2-C04: identity + policy engine + authority provider
    "e1936d06",  # P2-C05: approval + escalation workflow
    "fbe93cef",  # P2-C06: Context Packet + worker contracts + test workers
    "21bc4466",  # P2-C07: orchestrator engine: retry/checkpoint/recovery
    "0603b882",  # P2-C08: budget enforcement + conservation law
    "38e6ca66",  # P2-C09: SecretProvider + redaction
    "c531e12f",  # P2-C10: standalone runtime service
    "49f6fdbc",  # P2-C11: composition factory + application service + CLI
    "61488273",  # P2-C12: migration v3->v4 + backup/restore runtime coverage
    "afdbaa84",  # P2-T01: adversarial runtime qualification
]

P1R1_FREEZE_REF = "qcae/implementation/P1-R1-freeze-manifest.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout.strip()


def build_manifest(tested_commit: str, evidence: dict) -> dict:
    return {
        "phase": "P2 — Job Runtime + Local Governance",
        "canon_version": "0.1",
        "active_amendments": ["A-001 v1.0"],
        "head_commit": tested_commit,
        "tested_commit": tested_commit,
        "phase_commits": P2_COMMITS,
        "adr_refs": [
            "qcae/implementation/decisions/ADR-0008-p2-runtime-state-vocabulary.md",
            "qcae/implementation/decisions/ADR-0009-policy-vs-authority-vocabularies.md",
        ],
        "prior_freeze_refs": [
            P1R1_FREEZE_REF,
            "qcae/implementation/P1-freeze-manifest.json (historical, superseded by P1-R1)",
        ],
        "persistence": {
            "engine": "SQLite (stdlib sqlite3)",
            "engine_version": "3.x (stdlib)",
            "metadata_schema_version": 4,
            "artifact_hash_algorithm": "sha256",
            "migration_v3_to_v4": {
                "migration_id": V3_TO_V4_ID,
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
            "policy_decisions": ["ALLOW", "DENY", "REQUIRE_APPROVAL",
                                 "ALLOW_WITH_CONSTRAINTS"],
            "authority_outcomes": ["GRANT", "DENY", "REQUEST_MORE_EVIDENCE"],
            "worker_result_status": [
                "SUCCESS", "PARTIAL", "FAILED", "BLOCKED_POLICY", "BLOCKED_INPUT",
                "INCONCLUSIVE", "RETRYABLE", "CANCELLED",
            ],
            "event_types": [
                "JOB_CREATED", "JOB_QUEUED", "STEP_READY", "STEP_LEASED",
                "STEP_STARTED", "CHECKPOINT_WRITTEN", "STEP_SUCCEEDED",
                "STEP_FAILED", "RETRY_SCHEDULED", "APPROVAL_REQUESTED",
                "APPROVAL_GRANTED", "APPROVAL_DENIED", "JOB_SUCCEEDED",
                "JOB_FAILED", "JOB_CANCELLED",
            ],
            "budget_dimensions": [
                "attempts", "tool_calls", "network_requests",
                "sandbox_executions", "wall_clock_seconds", "artifact_bytes",
                "cost_units",
            ],
            "escalation_triggers": [
                "LEGAL_AMBIGUITY", "SECURITY_AMBIGUITY", "PRIVATE_DATA_EGRESS",
                "PRODUCTION_CREDENTIAL_REQUEST", "HARD_CONTRADICTION",
                "MATERIAL_CONTRACT_CHANGE", "FORK_VENDOR_COMMITMENT",
                "PRODUCTION_AUTHORITY", "CAPITAL_AUTHORITY", "IRREVERSIBLE_ACTION",
                "BUDGET_INCREASE",
            ],
        },
        "queue_lease_semantics": {
            "claim": "guarded upsert; only one active owner per step",
            "ack": "token-guarded; owner-only; single ack",
            "recovery": "expired/unacked claims reclaimed on restart",
            "priority": "not_before ASC; priority never bypasses policy state",
        },
        "secret_provider_semantics": {
            "handles_not_values": True,
            "audit_records_values": False,
            "production_class_denied_by_default": True,
            "redaction": "centralized Redactor on failure paths",
        },
        "cli_commands": [
            "job list", "job status", "job run", "job resume", "job cancel",
            "approval list", "identity",
        ],
        "test_command": ["python", "-m", "pytest", "qcae/tests", "-q"],
        "test_results": evidence,
        "evidence_label": "LOCAL TEST EVIDENCE",
        "migration_evidence": {
            "test": "test_p2_migration_backup.py::TestMigrationV3ToV4",
            "result": "v3 database migrates to v4; P1 registry rows preserved; runtime tables additive",
        },
        "crash_recovery_evidence": {
            "test": "test_p2_recovery.py::TestCrashRecovery + test_p2_adversarial.py restart cases",
            "result": "completed steps never repeated; expired leases recovered; authority rechecked",
        },
        "backup_restore_evidence": {
            "test": "test_p2_migration_backup.py::TestBackupRestoreRuntime",
            "result": "jobs/steps/checkpoints/budgets/approvals restored exactly; stale leases recoverable",
        },
        "architecture_guard_evidence": {
            "core_stdlib_only": "qcae/tests/architecture/test_p0_dependency_guards.py",
            "engine_confined_to_infrastructure": "governance/interfaces use ports only",
            "oce_absent": "runtime identity reports OCE_ABSENT; no OCE import anywhere in qcae/",
        },
        "known_external_failures": [
            "tests/forge/phase_00/test_extension_docs.py: 2 pre-existing failures "
            "external to qcae/ (documented since P1; unchanged)",
        ],
        "deferred_items": [
            "heartbeat-based lease liveness (single-process P2 model uses restart-based recovery)",
            "HTTP API surface (application service QcaeApp is the stable boundary; Book V 13.7 allows thin adapters later)",
            "OCE governance migration (P12; provider seam already in place)",
        ],
        "blockers": [],
        "operator_review_trigger": "P2 phase completion per operator directive; P3 NOT started",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


V3_TO_V4_ID = "P2-0004-runtime-governance-tables"


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
    out = REPO_ROOT / "qcae" / "implementation" / "P2-freeze-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    print(f"freeze manifest written: {out}")
    print(f"tested commit: {head}")
    print(f"tests: {ev.collected} collected, {ev.passed} passed, "
          f"{ev.failed} failed, {ev.skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
