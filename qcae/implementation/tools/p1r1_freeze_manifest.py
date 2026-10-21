"""P1-R1-FREEZE — superseding freeze manifest with real test evidence (§1, §2).

Emits ``P1-R1-freeze-manifest.json`` referencing the original P1 freeze,
embedding machine-readable test results captured from an actual full-suite
run via the fail-closed helper, and recording the repair relationship.

Fail-closed contract: the generator refuses to emit a manifest unless the
full QCAE suite passes at the expected commit and the results parse. It
never hardcodes counts.

Run:  python qcae/implementation/tools/p1r1_freeze_manifest.py [expected_head_sha]
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from qcae.core.serialization import sha256_of  # noqa: E402
from qcae.implementation.tools.test_evidence import (  # noqa: E402
    FreezeEvidenceError,
    PYTEST_Q_FAIL,
    capture_test_evidence,
    git_head_commit,
)

__all__ = ["build_manifest", "main"]

P1R1_REPAIR_COMMITS = [
    "34d256bf",  # P1-R1-I0: fail-closed test-evidence capture
    "9a990a85",  # P1-R1-C01: CapabilityRegistry ports + SQLite persistence
    "53106b1f",  # P1-R1-C02: provider-neutral RepositoryRecord + RepositoryRegistry
    "e3059465",  # P1-R1-C03: capability-graph relationship persistence
    "31e5ba20",  # P1-R1-C03: illegal-endpoint test fix
    "7d541a97",  # P1-R1-C04: decision-reuse capability/candidate inventory
    "1817ed57",  # P1-R1-C05: backup/restore registry-table coverage
    "a8ea1014",  # P1-R1-T01: identity-law/adversarial suite
    # continuation (operator directive: reviewed head 31e5ba20)
    "a69baaa8",  # P1-R1-C03R: repository identity vs revision split (ADR-0007) + migration v3
    "2dd94b85",  # P1-R1-C03R2: revision-sensitive IMPLEMENTS edge qualification
    "47f8f067",  # P1-R1-C04R: decision reuse + A-F internal-first findings
    "0a3bd46b",  # P1-R1-C05R: backup/restore carries revision history
    "d9a92e5f",  # P1-R1-T01R: parser robustness fixtures + candidate identity rule
]

TEST_COMMAND = ["python", "-m", "pytest", "qcae/tests", "-q"]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True, cwd=REPO_ROOT).stdout.strip()


def _commit_subject(sha: str) -> str:
    return _git("log", "-1", "--format=%s", sha)


def _original_freeze_refs() -> dict:
    manifest_path = REPO_ROOT / "qcae" / "implementation" / "P1-freeze-manifest.json"
    blob = _git("rev-parse", "HEAD:qcae/implementation/P1-freeze-manifest.json")
    # locate the commit that introduced the original P1 freeze manifest
    freeze_commit = _git(
        "log", "--format=%h", "--diff-filter=A", "--",
        "qcae/implementation/P1-freeze-manifest.json")
    return {
        "manifest_path": "qcae/implementation/P1-freeze-manifest.json",
        "introduced_in_commit": freeze_commit.splitlines()[0],
        "manifest_git_blob_sha256_ref": blob,
        "manifest_content_digest_sha256": __import__("hashlib").sha256(
            manifest_path.read_bytes()).hexdigest(),
        "preserved_unchanged": True,
    }


def build_manifest(expected_head: str, test_results: dict) -> dict:
    repair_commits = [
        {"sha": sha, "subject": _commit_subject(sha)} for sha in P1R1_REPAIR_COMMITS
    ]
    manifest = {
        "manifest_version": 1,
        "type": "SUPERSEDING_FREEZE_MANIFEST",
        "phase": "P1-R1",
        "phase_title": "Registry Completion + Freeze Truth Repair",
        "canon_version": "0.1",
        "qcae_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head_commit": expected_head,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "original_freeze": {
            "phase": "P1",
            "artifact": "qcae/implementation/P1-freeze-manifest.json",
            "refs": _original_freeze_refs(),
            "defects_identified_by_operator": [
                "test_results was null (no actual test evidence embedded)",
                "canonical progress status said 'P1 — IN BUILD' although P1 was frozen",
                "CapabilityRegistry and RepositoryRegistry persistence absent "
                "from the durable spine despite P1 scope",
            ],
        },
        "repair_relationship": {
            "type": "SUPERSEDES_FREEZE_RECORD_OF",
            "scope": "freeze bookkeeping + registry substrate completion; "
                     "all accepted P1 subsystems unchanged (evidence model, "
                     "artifact store, metadata persistence, lineage, receipts, "
                     "knowledge, cross-registry refs, unit-of-work, migrations, "
                     "backup/restore)",
            "history_policy": "original P1 freeze manifest is preserved byte-for-byte; "
                              "this artifact supersedes its bookkeeping only",
        },
        "operator_review_trigger": {
            "directive": "P1-R1 work-session prompt (reviewed head bbbe05a7); "
                         "continuation directive (reviewed head 31e5ba20) for the "
                         "repository identity/revision repair",
            "review_date": "2026-09-12",
        },
        "repair_commits": repair_commits,
        "test_results": test_results,
        "deferred_items_removed": [
            {
                "item": "RepositoryRegistry substrate (was deferred in original P1 manifest)",
                "resolution": "implemented in P1-R1-C02; P3 populates and uses the "
                              "registry — P1 supplies the durable substrate",
            }
        ],
        "deferred_items_remaining": [
            {"item": "Semantic/vector retrieval (15.9) deferred; structured retrieval only",
             "severity": "MINOR", "owner": "build-agent",
             "trigger": "when discovery volume demands"},
            {"item": "Analytics snapshots (Parquet/DuckDB) deferred per ADR-0006",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P9 quant validation"},
            {"item": "SqliteRegistryQuery freshness lookup reaches into the lifecycle log "
                     "connection; refactor to a port method when P2 jobs need it",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P2 job runtime"},
            {"item": "RepositoryRegistry observation timestamps rely on caller-supplied "
                     "first_seen_at/last_observed_at; a monotonic observed_sequence "
                     "column can replace the tie-break chain if P3 needs stricter "
                     "ordering guarantees",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P3 discovery"},
        ],
        "known_failures_outside_qcae": [
            "tests/forge/phase_00/test_extension_docs.py (2 pre-existing failures "
            "on this branch, unrelated to QCAE; present before P0 work)"
        ],
        "blockers": [],
        "schema_version": "v3 (repository_revision table added by ADR-0007 migration)",
        "evidence_refs": {
            "progress_ledger": "qcae/QCAE_IMPLEMENTATION_PROGRESS.md",
            "adr_refs": [
                "qcae/implementation/decisions/ADR-0006-persistence-engine.md",
                "qcae/implementation/decisions/ADR-0007-repository-identity-vs-revision-identity.md",
            ],
            "p1r1_tests": [
                "qcae/tests/unit/test_p1r1_freeze_evidence.py",
                "qcae/tests/unit/test_p1r1_freeze_evidence_robustness.py",
                "qcae/tests/unit/test_p1r1_capability_registry.py",
                "qcae/tests/unit/test_p1r1_repository_registry.py",
                "qcae/tests/unit/test_p1r1_relationships.py",
                "qcae/tests/unit/test_p1r1_decision_reuse.py",
                "qcae/tests/unit/test_p1r1_decision_reuse_full.py",
                "qcae/tests/unit/test_p1r1_backup_restore.py",
                "qcae/tests/unit/test_p1r1_identity_law.py",
            ],
            "architecture_guards": "qcae/tests/architecture/test_p0_dependency_guards.py",
            "migration_evidence": "qcae/tests/unit/test_p1_migrations.py (v1->v2) + "
                                  "test_p1r1_repository_registry.py (v2->v3 back-fill)",
        },
    }
    return manifest


def main() -> int:
    expected_head = (
        sys.argv[1] if len(sys.argv) > 1 else git_head_commit(str(REPO_ROOT))
    )
    try:
        evidence = capture_test_evidence(
            command=TEST_COMMAND,
            success_pattern=PYTEST_Q_FAIL,
            expected_commit=expected_head,
            cwd=str(REPO_ROOT),
            timeout_seconds=900,
        )
    except FreezeEvidenceError as exc:
        print(f"FREEZE REFUSED (fail-closed): {exc}", file=sys.stderr)
        return 1
    manifest = build_manifest(evidence.tested_commit, evidence.as_manifest_block())
    out = REPO_ROOT / "qcae" / "implementation" / "P1-R1-freeze-manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tr = manifest["test_results"]
    print(f"wrote {out}")
    print(f"tests: {tr['passed']} passed / {tr['failed']} failed / "
          f"{tr['skipped']} skipped in {tr['duration_seconds']}s at "
          f"{tr['tested_commit'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
