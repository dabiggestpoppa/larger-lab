"""P1-FREEZE — generate the amendment-aware P1 freeze manifest (spec §24).

Local-test evidence is labeled truthfully; no CI status is claimed.
Run:  python qcae/implementation/tools/p1_freeze_manifest.py
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
from qcae.core.evidence import EvidenceArtifact, ScopeDimensions  # noqa: E402
from qcae.core.evidence.object_model import EvidenceObjectType, FreshnessState  # noqa: E402
from qcae.core.ports.lineage import LineageEdgeType  # noqa: E402
from qcae.core.receipts import CapabilityReceipt, ReceiptState, ReceiptEvidenceRef  # noqa: E402
from qcae.core.knowledge import (  # noqa: E402
    NegativeKnowledge,
    NegativeKnowledgeType,
    PositiveKnowledge,
    ReconsiderationCondition,
)
from qcae.core.amendments.a001.external_registry import (  # noqa: E402
    ExternalLifecycleRole,
    ExternalRegistry,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SCHEMA_VERSION  # noqa: E402
from qcae.infrastructure.persistence.store_factory import SQLITE_VERSION  # noqa: E402
from qcae.infrastructure.artifact_store import DIGEST_ALGORITHM  # noqa: E402

P1_COMMITS = [
    "a53b401b", "d5e8882e", "6890f852", "93b7a1ea", "090e7edc", "f113c396",
    "01a31a69", "3aaddeea", "07475b2d", "e59632e7", "a498a955", "70c6b306",
    "e8cfb720", "04983524", "55ba326d", "772ab794", "da69813d", "ba9c3e35",
]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True, cwd=REPO_ROOT).stdout.strip()


def _commit_subject(sha: str) -> str:
    return _git("log", "-1", "--format=%s", sha)


def schema_snapshot(cls) -> dict:
    from dataclasses import fields

    return {
        "object_type": cls.object_type(),
        "schema_version": cls.SCHEMA_VERSION,
        "fields": [f.name for f in fields(cls)],
    }


def main() -> None:
    record_classes = [
        EvidenceArtifact,
        ScopeDimensions,
        ReceiptEvidenceRef,
        CapabilityReceipt,
        ReconsiderationCondition,
        NegativeKnowledge,
        PositiveKnowledge,
    ]
    enum_vocabs = {
        "evidence_object_types": [m.value for m in EvidenceObjectType],
        "freshness_states": [m.value for m in FreshnessState],
        "lineage_edge_types": [m.value for m in LineageEdgeType],
        "receipt_states": [m.value for m in ReceiptState],
        "negative_knowledge_types": [m.value for m in NegativeKnowledgeType],
        "external_registries": [m.value for m in ExternalRegistry],
        "external_lifecycle_roles": [m.value for m in ExternalLifecycleRole],
    }
    phase_commits = [
        {"sha": sha, "subject": _commit_subject(sha)} for sha in P1_COMMITS
    ]
    manifest = {
        "manifest_version": 1,
        "phase": "P1",
        "phase_title": "Evidence + Registry Spine",
        "canon_version": "0.1",
        "qcae_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head_commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "active_amendments": ["A-001 (Research Mesh Boundary and Economic Experience v1.0)"],
        "adr_refs": [
            "qcae/implementation/decisions/ADR-0006-persistence-engine.md",
        ],
        "persistence": {
            "engine": "SQLite (Python stdlib sqlite3)",
            "engine_version": sqlite3_version(),
            "metadata_schema_version": SCHEMA_VERSION,
            "journal_mode": "WAL",
            "transaction_model": "BEGIN IMMEDIATE unit-of-work, rollback on failure",
            "artifact_store": {
                "algorithm": DIGEST_ALGORITHM,
                "layout": "<root>/sha256/<2>/<2>/<full-digest>",
                "integrity": "digest verified on every retrieval",
            },
            "analytics_snapshots": "deferred (Parquet/DuckDB) until a phase justifies",
        },
        "domain_schema_snapshots": [schema_snapshot(c) for c in record_classes],
        "domain_schema_snapshot_digest": None,
        "vocabularies": enum_vocabs,
        "vocabulary_digest": None,
        "registry_types": [
            "EvidenceRepository", "LifecycleLogRepository", "LineageRepository",
            "NegativeKnowledgeRepository", "PositiveKnowledgeRepository",
            "ReceiptRepository", "RegistryQuery(decision-reuse)",
            "ExternalRegistryRefRepository",
        ],
        "cross_registry_semantics": {
            "owner_domains": ["research-mesh:*", "institution:*"],
            "lifecycle_roles": ["OBSERVE", "SUBMIT"],
            "owner_rewrite": "rejected (ownership laundering guard)",
            "external_evidence_in_receipts": "supporting only; executable proof must be QCAE-owned",
        },
        "append_supersede_law": {
            "update_statements_on_factual_tables": 0,
            "enforcement_test": "test_store_contains_no_update_path (AST-based)",
            "freshness_changes": "append-only freshness_log; current = latest entry",
        },
        "migration_evidence": {
            "mechanism_proof": "v1->v2 TEST_V1_TO_V2 with ledger provenance",
            "rollback_on_failure": "verified",
            "backward_and_skip_refusal": "verified",
        },
        "backup_restore_evidence": {
            "covers": ["metadata db", "raw artifacts", "schema version", "lineage"],
            "verification": "manifest digests verified before restore declares success",
        },
        "test_command": "python -m pytest qcae/tests -q",
        "test_results": None,
        "evidence_label": "LOCAL TEST EVIDENCE",
        "known_failures_outside_qcae": [
            "tests/forge/phase_00/test_extension_docs.py (2 pre-existing failures "
            "on this branch, unrelated to QCAE; present before P0 work)"
        ],
        "phase_commits": phase_commits,
        "prior_freezes": [
            "qcae/implementation/P0-freeze-manifest.json",
            "qcae/implementation/P0-A001-freeze-manifest.json",
            "qcae/implementation/P0-A001-freeze-addendum.json",
        ],
        "deferred_items": [
            {"item": "Semantic/vector retrieval (15.9) deferred; structured retrieval only",
             "severity": "MINOR", "owner": "build-agent", "trigger": "when discovery volume demands"},
            {"item": "RepositoryRegistry tables deferred until P3/P4 produce repository objects",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P3 discovery vertical slice"},
            {"item": "Analytics snapshots (Parquet/DuckDB) deferred per ADR-0006",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P9 quant validation"},
            {"item": "SqliteRegistryQuery freshness lookup reaches into the lifecycle log "
                     "connection; refactor to a port method when P2 jobs need it",
             "severity": "MINOR", "owner": "build-agent", "trigger": "P2 job runtime"},
        ],
        "blockers": [],
        "evidence_refs": {
            "progress_ledger": "qcae/QCAE_IMPLEMENTATION_PROGRESS.md",
            "p1_tests": [
                "qcae/tests/unit/test_p1_evidence_model.py",
                "qcae/tests/unit/test_p1_artifact_store.py",
                "qcae/tests/unit/test_p1_sqlite_store.py",
                "qcae/tests/unit/test_p1_lineage.py",
                "qcae/tests/unit/test_p1_receipt.py",
                "qcae/tests/unit/test_p1_knowledge.py",
                "qcae/tests/unit/test_p1_registry_retrieval.py",
                "qcae/tests/unit/test_p1_cross_registry.py",
                "qcae/tests/unit/test_p1_unit_of_work.py",
                "qcae/tests/unit/test_p1_migrations.py",
                "qcae/tests/unit/test_p1_backup_restore.py",
                "qcae/tests/unit/test_p1_adversarial.py",
            ],
            "architecture_guards": "qcae/tests/architecture/test_p0_dependency_guards.py",
        },
    }
    manifest["domain_schema_snapshot_digest"] = sha256_of(manifest["domain_schema_snapshots"])
    manifest["vocabulary_digest"] = sha256_of(enum_vocabs)
    out = REPO_ROOT / "qcae" / "implementation" / "P1-freeze-manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"snapshots: {len(manifest['domain_schema_snapshots'])} records, "
          f"{len(enum_vocabs)} vocabularies, {len(P1_COMMITS)} phase commits")


def sqlite3_version() -> str:
    return SQLITE_VERSION


if __name__ == "__main__":
    main()
