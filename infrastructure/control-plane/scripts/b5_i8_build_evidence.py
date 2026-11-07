"""B5-I8 — execute the usability protocol and build the audit evidence bundle.

Test-only/reproduction tooling. Deterministic: no wall clock reaches a rendered
document, no network, no provider, no canonical-state write. Running it twice on
the same commit produces the same structural evidence (the wall-clock duration of
each protocol task is an OBSERVED measurement and is allowed to differ; the
deterministic replay digest excludes it).

Usage (from the repository root):

    python infrastructure/control-plane/scripts/b5_i8_build_evidence.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_IDENTITY = REPO_ROOT / "docs" / "oce-golden-system" / "OCE_B5_I8_CI_IDENTITY_v1.0.json"
sys.path.insert(0, str(REPO_ROOT / "infrastructure" / "control-plane" / "tests"))

import b5_i8_audit_support as S  # noqa: E402


def _head() -> dict:
    head = S.git("rev-parse", "HEAD").stdout.strip()
    tree = S.git("rev-parse", "HEAD^{tree}").stdout.strip()
    return {"head": head, "tree": tree}


def build() -> dict:
    identity = _head()
    results = S.run_protocol()
    accessibility = S.accessibility_checks()
    masked = S.masked_report(S.drill_report())
    planned = S.planned_nodes()
    bundle = {
        "document_id": "OCE-B5-I8-EVIDENCE-001",
        "version": "1.0",
        "stage": "AUTHORIZED_STAGE=B5-I8-IMPLEMENTATION",
        "generated_by": "infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
        "tested": identity,
        "base_sha": S.git("rev-parse", "origin/main").stdout.strip(),
        "labels": {
            "audit": S.SAME_AGENT_LABEL,
            "human_evidence": S.ATTESTATION_CLASS,
            "blind": False,
            "independent": False,
        },
        "planned": {
            "label": "EXPECTED",
            "total": len(planned),
            "floor": 40,
            "files": S.planned_files(),
            "nodes": planned,
        },
        "protocol": {
            "protocol_id": "OCE-B5-I8-USABILITY-PROTOCOL-001",
            "executed_by": S.ATTESTATION_CLASS,
            "tasks": [dict(task, executed=False) for task in S.PROTOCOL_TASKS],
            "results": results,
        },
        "accessibility": accessibility,
        "drill": {
            "disposition": masked["disposition"],
            "masked_sha256": S.sha256_bytes(S.canonical(masked).encode("utf-8")),
            "mask": list(S.DRILL_MASK),
        },
        "snapshot": {
            "observed_at": S.FIXED_OBSERVED_AT,
            "panel_digest": S.panel.canonical_digest(S.panel_document()),
        },
        "measurements": {
            "tasks_defined": {
                "value": len(S.PROTOCOL_TASKS),
                "unit": "tasks",
                "label": "OBSERVED",
                "command": "python infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
                "tested_sha": identity["head"],
                "environment": "local-win32-cpython3.11",
                "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
            },
            "tasks_completed": {
                "value": sum(1 for row in results if row["completion"]),
                "unit": "tasks",
                "label": "OBSERVED",
                "command": "python infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
                "tested_sha": identity["head"],
                "environment": "local-win32-cpython3.11",
                "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
            },
            "task_errors": {
                "value": sum(int(row["error"]) for row in results),
                "unit": "errors",
                "label": "OBSERVED",
                "command": "python infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
                "tested_sha": identity["head"],
                "environment": "local-win32-cpython3.11",
                "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
            },
            "navigation_steps_total": {
                "value": sum(int(row["navigation_steps"]) for row in results),
                "unit": "governed reads",
                "label": "OBSERVED",
                "command": "python infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
                "tested_sha": identity["head"],
                "environment": "local-win32-cpython3.11",
                "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
            },
            "time_to_first_useful_state_ms": {
                "value": max(float(row["time_to_first_useful_state_ms"]) for row in results),
                "unit": "ms",
                "label": "OBSERVED",
                "command": "python infrastructure/control-plane/scripts/b5_i8_build_evidence.py",
                "tested_sha": identity["head"],
                "environment": "local-win32-cpython3.11 (not a performance claim)",
                "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
            },
        },
        "gates": {},
        "verdict": {},
        "ci": ci_block(),
        "boundary": {
            "production_changed": False,
            "frontend_changed": False,
            "existing_test_changed": False,
            "web_view_present": False,
            "b5_i9_started": False,
            "book_6_started": False,
            "evaluation_started": False,
            "cost_usd": 0,
            "capital_authority": "none",
        },
        "limitations": [
            "SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT: one operator (the implementer) "
            "executed the protocol; no blind or independent attestation exists.",
            "G16 therefore remains OPEN; the blocker is the missing independent operator "
            "(B5I8-DF05), not a protocol failure.",
            "Time-to-first-useful-state is a local wall-clock observation on one machine; it "
            "is an OBSERVED sample, not a performance claim and not a ceiling.",
            "No browser or web-view surface exists, so no browser accessibility is claimed.",
            "Refs/pull/21/merge (7dc1248e68022b16ea3cb2b7931e22013517f3a3) was pruned by GitHub "
            "after PR #21 merged; the P0 ratification records it as a pre-merge observation and "
            "it is exempt from live commit resolution for that reason only.",
        ],
    }
    bundle["gates"] = S.gates(bundle)
    bundle["verdict"] = S.recompute_verdict(bundle)
    bundle["verdict"]["digest"] = S.verdict_digest(bundle)
    return bundle


def ci_block() -> dict:
    """Observed CI identity, or an explicit NOT_EXECUTED block before any run."""
    if CI_IDENTITY.exists():
        identity = json.loads(CI_IDENTITY.read_text(encoding="utf-8"))
        return {
            "status": "OBSERVED",
            "oce_run_id": identity["oce_run_id"],
            "github_run_id": identity["github_run_id"],
            "run_attempt": identity["run_attempt"],
            "workflow_path": identity["workflow_path"],
            "pr_number": identity["pr_number"],
            "artifact_binding": identity["artifact_name"] == "b5-i8-evidence-" + identity["oce_run_id"],
            "run_context": identity["run_context"],
            "run_id": identity["run_id"],
            "check_run_id": identity["check_run_id"],
            "job_id": identity["job_id"],
            "check_suite_id": identity["check_suite_id"],
            "artifact_id": identity["artifact_id"],
            "artifact_name": identity["artifact_name"],
            "tested_head": identity["head_sha"],
            "tested_tree": identity["tested_tree"],
            "merge_ref": identity["merge_ref"],
            "parsed_from": identity["parsed_from"],
        }
    return {
        "status": "NOT_EXECUTED",
        "run_id": None,
        "check_run_id": None,
        "job_id": None,
        "check_suite_id": None,
        "artifact_id": None,
        "artifact_name": None,
        "tested_head": None,
        "tested_tree": None,
        "merge_ref": None,
        "parsed_from": None,
    }


def main() -> int:
    bundle = build()
    S.EVIDENCE.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("wrote", S.EVIDENCE)
    print("tasks:", len(bundle["protocol"]["results"]))
    print("g16:", bundle["gates"]["G16"]["status"], "-", bundle["gates"]["G16"]["blocker"][:60])
    print("verdict:", json.dumps(bundle["verdict"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
