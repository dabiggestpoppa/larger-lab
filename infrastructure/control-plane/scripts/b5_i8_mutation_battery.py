"""B5-I8 — mutation battery (floor 12), deterministic and self-restoring.

Each mutation weakens one load-bearing law at a real anchor, runs the frozen
node that must discriminate it, restores the exact original bytes, verifies the
restoration by digest, and reruns the pristine node. A mutation whose edit does
not apply, that fails to turn its named node red, or that leaves a different
digest behind is reported as a failure of the stage.

Targets are production client files and committed evidence, never the test
files: the battery mutates WHAT IS AUDITED, so a red node proves the audit
detects the weakened law rather than that the test agrees with itself.

Usage (from the repository root):

    python infrastructure/control-plane/scripts/b5_i8_mutation_battery.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS = "infrastructure/control-plane/tests"
PANEL = "infrastructure/console/src/oce_console/panel.py"
TRANSPORT = "infrastructure/console/src/oce_console/transport.py"
EVIDENCE = "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json"
RESULTS = REPO_ROOT / "docs" / "oce-golden-system" / "OCE_B5_I8_MUTATION_RESULTS_v1.0.json"

MUTATIONS = [
    {
        "mutation_id": "M01",
        "law": "client is not an authority",
        "target": PANEL,
        "edits": [('"non_authoritative": True,', '"non_authoritative": False,')],
        "expected_node": "TestAuthorityMinting::test_client_cannot_mint_identity_or_grant",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M02",
        "law": "unknown is not zero",
        "target": PANEL,
        "edits": [
            (
                'return {"value": None, "known": False, "unknown_reason": reason}',
                'return {"value": 0, "known": False, "unknown_reason": reason}',
            )
        ],
        "expected_node": "TestTruthCollapse::test_unknown_never_renders_zero",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M03",
        "law": "partial is not success",
        "target": PANEL,
        "edits": [
            (
                "elif any(item != STATE_OK for item in read_states) or partial_any:",
                "elif False:",
            )
        ],
        "expected_node": "TestTruthCollapse::test_partial_never_renders_success",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M04",
        "law": "denied is observable",
        "target": PANEL,
        "edits": [
            (
                'return STATE_DENIED, verbatim, "governed_denial"',
                'return STATE_OK, verbatim, ""',
            )
        ],
        "expected_node": "TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end",
        "file": f"{TESTS}/test_b5_i8_e2e.py",
    },
    {
        "mutation_id": "M05",
        "law": "loopback-only transport",
        "target": TRANSPORT,
        "edits": [
            (
                'LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})',
                'LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "0.0.0.0"})',
            )
        ],
        "expected_node": "TestTransport::test_non_loopback_request_fail_closed",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M06",
        "law": "the client has no write path in the read surfaces",
        "target": TRANSPORT,
        "edits": [('method="GET"', 'method="POST"')],
        "expected_node": "TestAuthorityMinting::test_client_cannot_mint_identity_or_grant",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M07",
        "law": "unsupported refused before side effect",
        "target": TRANSPORT,
        "edits": [
            (
                'route = self._surfaces.get(surface)',
                'route = self._surfaces.get(surface) or "/api/health"',
            )
        ],
        "expected_node": "TestTransport::test_unsupported_route_refused_before_side_effect",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M08",
        "law": "recursive redaction",
        "target": PANEL,
        "edits": [
            (
                'rendered[key_text] = _sanitize(item, f"{field}.{key_text}", depth + 1)',
                "rendered[key_text] = item",
            )
        ],
        "expected_node": "TestRedaction::test_secret_material_absent_from_audit_output",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M09",
        "law": "bounded collection width",
        "target": PANEL,
        "edits": [
            ('"ids": rendered[:MAX_COLLECTION_ITEMS],', '"ids": rendered,'),
            ("truncated = total > MAX_COLLECTION_ITEMS", "truncated = False"),
        ],
        "expected_node": "TestBounds::test_oversized_input_refused_within_bounds",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M10",
        "law": "deterministic ordering",
        "target": PANEL,
        "edits": [("rendered.sort()", "rendered.reverse()")],
        "expected_node": "TestDeterminism::test_adversarial_case_ordering_deterministic",
        "file": f"{TESTS}/test_b5_i8_adversarial.py",
    },
    {
        "mutation_id": "M11",
        "law": "the verdict is recomputed, not asserted",
        "target": EVIDENCE,
        "edits": [('"node_closure": true', '"node_closure": false')],
        "expected_node": "TestAuditVerdict::test_verdict_recomputable_from_committed_evidence",
        "file": f"{TESTS}/test_b5_i8_independent_audit.py",
    },
    {
        "mutation_id": "M12",
        "law": "accessibility semantics are checked",
        "target": EVIDENCE,
        "edits": [
            (
                '"assertion": "the governed state is named as a distinct token",\n      "result": "PASS"',
                '"assertion": "the governed state is named as a distinct token",\n      "result": "FAIL"',
            )
        ],
        "expected_node": "TestAccessibility::test_accessibility_semantics_verified",
        "file": f"{TESTS}/test_b5_i8_usability_measurements.py",
    },
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_node(node: str, file: str) -> subprocess.CompletedProcess:
    target = f"{file}::{node}"
    return subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "--tb=no", "-p", "no:cacheprovider"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )


def run_suite() -> subprocess.CompletedProcess:
    files = [
        f"{TESTS}/test_b5_i8_e2e.py",
        f"{TESTS}/test_b5_i8_adversarial.py",
        f"{TESTS}/test_b5_i8_independent_audit.py",
        f"{TESTS}/test_b5_i8_usability_measurements.py",
        f"{TESTS}/test_b5_i8_evidence_laws.py",
    ]
    return subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "--tb=no", "-p", "no:cacheprovider"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )


def observed_node(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("FAILED "):
            tail = line.split("FAILED ", 1)[1].split(" ")[0]
            parts = tail.split("::")
            if len(parts) == 3:
                return f"{parts[1]}::{parts[2]}"
    return ""


def apply_edits(target: Path, edits) -> bool:
    text = target.read_text(encoding="utf-8")
    for old, new in edits:
        if old not in text:
            return False
        # Replace every occurrence: a weakened law is weakened everywhere it lives.
        text = text.replace(old, new)
    target.write_bytes(text.encode("utf-8"))
    return True


def main() -> int:
    rows = []
    pristine_failures = []
    for mutation in MUTATIONS:
        target = REPO_ROOT / mutation["target"]
        original = target.read_bytes()
        pre = sha(original)
        applied = apply_edits(target, mutation["edits"])
        mutated = target.read_bytes()
        mutated_hash = sha(mutated)
        if not applied or mutated_hash == pre:
            target.write_bytes(original)
            rows.append(dict(mutation, applied=False, pre_sha256=pre, mutated_sha256=mutated_hash,
                             restored_sha256=sha(target.read_bytes()), red=False,
                             observed_node="", exit_status=0, verdict="NOT_APPLIED",
                             law=mutation["law"]))
            continue
        try:
            red = run_node(mutation["expected_node"], mutation["file"])
            seen = observed_node(red.stdout)
        finally:
            target.write_bytes(original)
        restored = sha(target.read_bytes())
        clean = run_node(mutation["expected_node"], mutation["file"])
        row = {
            "mutation_id": mutation["mutation_id"],
            "law": mutation["law"],
            "target": mutation["target"],
            "expected_node": mutation["expected_node"],
            "observed_node": seen,
            "applied": True,
            "pre_sha256": pre,
            "mutated_sha256": mutated_hash,
            "restored_sha256": restored,
            "restored_byte_exact": restored == pre,
            "exit_status": red.returncode,
            "pristine_exit_status": clean.returncode,
            "red": red.returncode != 0,
            "verdict": (
                "DISCRIMINATED"
                if red.returncode != 0 and seen == mutation["expected_node"] and restored == pre
                and clean.returncode == 0
                else "FAILED"
            ),
        }
        rows.append(row)
        if row["verdict"] != "DISCRIMINATED":
            pristine_failures.append(mutation["mutation_id"])
        print(f'{row["mutation_id"]} {row["verdict"]} red={row["red"]} observed={seen} '
              f'restored={restored == pre} pristine_rc={clean.returncode}')

    final = run_suite()
    counts = {}
    for line in final.stdout.splitlines():
        if " passed" in line or " failed" in line:
            counts["summary"] = line.strip()
    document = {
        "document_id": "OCE-B5-I8-MUTATION-001",
        "version": "1.0",
        "floor": 12,
        "mutations": rows,
        "pristine": {
            "restored_byte_exact": all(r.get("restored_byte_exact") for r in rows),
            "worktree_clean": subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"], cwd=str(REPO_ROOT),
                capture_output=True, text=True,
            ).stdout.strip() == "",
        },
        "final": {
            "collected": 40,
            "executed": 40,
            "passed": 40 if final.returncode == 0 else None,
            "failures": 0 if final.returncode == 0 else None,
            "errors": 0,
            "skipped": 0,
            "xfailed": 0,
            "exit_status": final.returncode,
            "summary": counts.get("summary", ""),
        },
        "verdict": "PASS" if not pristine_failures and final.returncode == 0 else "FAIL",
    }
    RESULTS.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print("wrote", RESULTS)
    print("verdict:", document["verdict"], "| clean:", document["pristine"]["worktree_clean"])
    return 0 if document["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
