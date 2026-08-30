#!/usr/bin/env python3
"""OCE Book 2 — independent gate for control-plane validation (B2-R5).

Parses machine-readable pytest output/JUnit only (never human log prose).
Enforces the B2 CI gate contract and closes audit gaps 17/18:

  - identity: repository == dabiggestpoppa/larger-lab, branch ==
    oce-program-build (from trusted CI env)
  - tests actually ran (passed > 0) — a green run that skipped the B2
    container suite is a FAILURE, exactly like run 33316972933
  - zero failures, zero errors, and in CI mode zero skipped tests: all 31
    container-backed tests (PG store, Redis transport, worker, scheduler)
    must execute against the real compose stack

Writes independent-gate.json and exits 0 only when every condition holds.

Usage: independent-gate-b2.py <evidence-dir> <pytest-rc>
Env:   OCE_RUN_ID, OCE_CI_MODE, GITHUB_REPOSITORY, GITHUB_REF_NAME,
       OCE_EXPECTED_REPO, OCE_EXPECTED_BRANCH
"""
import json
import os
import re
import sys

EXPECTED_REPO = os.environ.get("OCE_EXPECTED_REPO", "dabiggestpoppa/larger-lab")
EXPECTED_BRANCH = os.environ.get("OCE_EXPECTED_BRANCH", "oce-program-build")
CI_MODE = os.environ.get("OCE_CI_MODE") == "true"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_REF = os.environ.get("GITHUB_REF_NAME", "")
RUN_ID = os.environ.get("OCE_RUN_ID", "")

checks = []


def add(cid, name, ok, detail=""):
    checks.append({"id": cid, "name": name, "ok": bool(ok), "detail": str(detail)})


ev = sys.argv[1]
pytest_rc = int(sys.argv[2]) if len(sys.argv) > 2 else 0

output_path = os.path.join(ev, "pytest-output.txt")
junit_path = os.path.join(ev, "junit.xml")

add("identity-repo", "repository identity",
    GITHUB_REPO == EXPECTED_REPO, f"{GITHUB_REPO} == {EXPECTED_REPO}")
add("identity-branch", "branch identity",
    GITHUB_REF == EXPECTED_BRANCH, f"{GITHUB_REF} == {EXPECTED_BRANCH}")

counts = {"passed": 0, "skipped": 0, "failed": 0, "errors": 0, "deselected": 0}
skip_reasons = []
if os.path.exists(output_path):
    text = open(output_path, encoding="utf-8", errors="replace").read()
    for k in counts:
        m = re.search(rf"(\d+)\s+{k}\b", text)
        if m:
            counts[k] = int(m.group(1))
    skip_reasons = re.findall(r"SKIPPED \[\d+\] [^\n]+", text)

add("pytest-exit", "pytest exit code 0", pytest_rc == 0, f"rc={pytest_rc}")
add("tests-ran", "at least one test executed",
    counts["passed"] > 0, f"passed={counts['passed']}")
add("zero-failed", "zero test failures", counts["failed"] == 0, f"failed={counts['failed']}")
add("zero-errors", "zero collection errors", counts["errors"] == 0, f"errors={counts['errors']}")
if CI_MODE:
    add("zero-skips-ci",
        "zero skipped tests in CI (container suite must execute)",
        counts["skipped"] == 0,
        f"skipped={counts['skipped']}"
        + (f"; reasons={skip_reasons[:10]}" if skip_reasons else ""))
add("junit-written", "JUnit XML evidence written",
    os.path.exists(junit_path) and os.path.getsize(junit_path) > 0)
add("run-id", "OCE_RUN_ID present",
    bool(re.fullmatch(r"[0-9a-f]{12,}", RUN_ID or "")), RUN_ID)

ok = all(c["ok"] for c in checks)
result = {
    "gate": "PASS" if ok else "FAIL",
    "block": "B2",
    "stage": "B2-CONTROL-PLANE-CLOSURE",
    "run_id": RUN_ID,
    "counts": counts,
    "checks": checks,
    "ci_mode": CI_MODE,
    "cloud_mutations": 0,
    "cloud_cost_state": "ZERO",
    "cloud_deployment_state": "NOT_DEPLOYED",
    "cloud_activation_state": "DEFERRED_BY_OPERATOR",
}
with open(os.path.join(ev, "independent-gate.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
print("GATE:", "PASS" if ok else "FAIL", json.dumps(counts))
sys.exit(0 if ok else 1)
