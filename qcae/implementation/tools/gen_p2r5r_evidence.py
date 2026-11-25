"""P2-R5R evidence generator (runs at the tested commit; no hardcoded results).

Each block is a separate pytest invocation whose exit status and parsed
counts are recorded verbatim. Nothing is relabeled: a block's numbers are the
numbers that run produced, and ``ok`` is derived from its exit code.

Usage:  python qcae/implementation/tools/gen_p2r5r_evidence.py <out.json>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKS = [
    ("operator_loop", ["qcae/tests/acceptance/test_p2_operator_loop.py"]),
    ("grant_journey", ["qcae/tests/acceptance/test_p2_grant_journey.py"]),
    ("process_crash", ["qcae/tests/acceptance/test_p2_process_crash.py"]),
    ("schema_r5r", ["qcae/tests/unit/test_p2r5r_c01_schema_matrix.py"]),
    ("binding_r5r", ["qcae/tests/unit/test_p2r5r_c02_grant_binding.py"]),
    ("boundary_r5r", ["qcae/tests/unit/test_p2r5r_c03_provider_boundary.py"]),
    ("backup_r5r", ["qcae/tests/unit/test_p2r5r_c04_backup_disaster.py"]),
    ("typed_r5r", ["qcae/tests/unit/test_p2r5r_c05_typed_outcomes.py"]),
    ("schema_r1", ["qcae/tests/unit/test_p2r5r_r1_schema_custody.py"]),
    ("constraint_r1", ["qcae/tests/unit/test_p2r5r_r1_constraint_guard.py"]),
    ("p3_r4_regression", ["qcae/tests/unit", "-k", "p3_"]),
    ("crash_after_lease", [
        "qcae/tests/unit/test_p2_c07rt_repair_qualification.py::TestCombinedFlows::"
        "test_crash_after_lease_resume_does_not_repeat_committed",
    ]),
    ("topology", ["qcae/tests/unit/test_p0_topology.py"]),
    ("r2_custody_seal", ["qcae/tests/unit/test_p2r5r_r2_custody_seal.py"]),
    ("full_qcae", ["qcae/tests"]),
]

_COUNT = re.compile(r"(\d+) (passed|failed|error|errors|skipped)")


def _run(targets: list) -> dict:
    cmd = [sys.executable, "-m", "pytest", *targets, "-q"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    tail = (proc.stdout or "").strip().splitlines()
    summary = tail[-1] if tail else ""
    counts = {kind: int(n) for n, kind in _COUNT.findall(summary)}
    return {
        "command": " ".join(["python", "-m", "pytest", *targets, "-q"]),
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "counts": counts,
        "summary_line": summary,
    }


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "P2-R5R-test-evidence.json")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    evidence = {
        "phase": "P2-R5R",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tested_commit": head,
        "environment": "local developer machine (no CI available for this repo)",
        "blocks": {},
    }
    failure = False
    for name, targets in BLOCKS:
        result = _run(targets)
        evidence["blocks"][name] = result
        print(f"{name}: {result['summary_line']} (exit {result['exit_code']})")
        failure = failure or not result["ok"]
    totals = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for result in evidence["blocks"].values():
        for kind, n in result["counts"].items():
            key = "errors" if kind.startswith("error") else kind
            totals[key] = totals.get(key, 0) + n
    evidence["all_blocks_green"] = not failure
    evidence["note"] = (
        "Per-block counts are the actual counts each invocation printed; "
        "no aggregate is copied into a per-file block."
    )
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0 if not failure else 1


if __name__ == "__main__":
    raise SystemExit(main())
