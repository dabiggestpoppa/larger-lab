#!/usr/bin/env python3
"""Regenerate the mandatory test registry (scripts/b2_registry.py) from ACTUAL
pytest collection so the gate's expected total and category assignment always
match the tests that are collected (B3-R8 / R9 rule: never hardcode a count).

Run from the repo root with the control-plane suite on PYTHONPATH exactly the
way CI runs it, so junit classnames match:

    PYTHONPATH="<repo>:<cp>/src:<cp>/scripts" python scripts/gen_mandatory_registry.py

The script runs the full suite once to produce an authoritative junit.xml and
regenerates b2_registry.py from every collected testcase id. The committed
registry is then reviewed as part of the change that adds/removes tests.
"""
from __future__ import annotations
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FILE = Path(__file__).resolve()
CP = FILE.parent.parent                       # infrastructure/control-plane
BASE_DIR = CP.parent.parent                    # repo root
REGISTRY = CP / "scripts" / "b2_registry.py"

# subprocess needs a filesystem-native cwd (Windows drive-absolute).
_NATIVE_CP = str(CP.resolve())

CATEGORY_FILES = {
    "unit": "unit-results.json",
    "postgres": "postgres-integration-results.json",
    "redis": "redis-integration-results.json",
    "scheduler": "scheduler-results.json",
    "worker": "worker-results.json",
    "api": "api-results.json",
    "po-hermes-boundary": "po-hermes-boundary-results.json",
    "adversarial": "adversarial-results.json",
    "local-lifecycle": "local-lifecycle-results.json",
    "validation-regression": "validation-regression-results.json",
    "worker-fabric-core": "worker-fabric-core-results.json",
    "worker-supervisor": "worker-supervisor-results.json",
    "sandbox-resource": "sandbox-resource-results.json",
    "representative-job": "representative-job-results.json",
    "cli-lifecycle": "cli-lifecycle-results.json",
    "outbound-session": "outbound-session-results.json",
    "end-to-end-job": "end-to-end-job-results.json",
    "fabric-pg": "fabric-pg-results.json",
}

# module-substring -> category (caught BEFORE the class-based PO/Hermes rules)
CATEGORY_RULES = [
    ("test_pg_integration", "postgres"),
    ("test_redis_integration", "redis"),
    ("test_pg_scheduler_integration", "scheduler"),
    ("test_pg_worker_integration", "worker"),
    ("test_http_api_integration", "api"),
    ("test_b3_adversarial", "adversarial"),
    ("test_b3_adversarial_closure", "adversarial"),
    ("test_b3_representative_jobs", "representative-job"),
    ("test_execution_runtime", "sandbox-resource"),
    ("test_worker_fabric", "worker-fabric-core"),
    ("test_worker_supervisor", "worker-supervisor"),
    ("test_local_lifecycle", "local-lifecycle"),
    ("test_validation_gate_regressions", "validation-regression"),
    ("test_b3_worker_cli_lifecycle", "cli-lifecycle"),
    ("test_b3_outbound_protocol_units", "outbound-session"),
    ("test_b3_outbound_protocol_service", "outbound-session"),
    ("test_b3_end_to_end_jobs", "end-to-end-job"),
    ("test_b3_worker_fabric_store_integration", "fabric-pg"),
    (".TestPOBoundary::", "po-hermes-boundary"),
    (".TestHermesBoundary::", "po-hermes-boundary"),
]

REQUIRED_ARTIFACTS = [
    "source-identity.json", "tool-versions.json", "migration-results.json",
    "test-registry.json", "junit.xml", "pytest-output.txt",
    "unit-results.json", "postgres-integration-results.json",
    "redis-integration-results.json", "scheduler-results.json",
    "worker-results.json", "api-results.json",
    "po-hermes-boundary-results.json", "adversarial-results.json",
    "local-lifecycle-results.json", "validation-regression-results.json",
    "worker-fabric-core-results.json", "worker-supervisor-results.json",
    "sandbox-resource-results.json", "representative-job-results.json",
    "cli-lifecycle-results.json", "outbound-session-results.json",
    "end-to-end-job-results.json", "fabric-pg-results.json",
    "source-cleanliness.json", "cleanup-results.json", "independent-gate.json",
    "stage-status.json", "stage-log.txt", "evidence-manifest.json",
    "validation-summary.md",
]


def category_of(node_id: str) -> str:
    for sub, cat in CATEGORY_RULES:
        if sub in node_id:
            return cat
    return "unit"


def collect_ids() -> list[str]:
    jxml = BASE_DIR / ".registry-collect.xml"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BASE_DIR), str(CP / "src"), str(CP / "scripts"),
         env.get("PYTHONPATH", "")])
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "-rs",
           "-p", "no:cacheprovider", "--junitxml", str(jxml)]
    r = subprocess.run(cmd, cwd=_NATIVE_CP, env=env, capture_output=True,
                       text=True, timeout=3600, errors="replace")
    if not jxml.exists():
        print("NO JUNIT produced; rc=%d\n%s" % (r.returncode, r.stdout[-3000:]))
        sys.exit(1)
    root = ET.parse(str(jxml)).getroot()
    suite = root.find("testsuite") or root
    ids = sorted({f"{tc.get('classname')}::{tc.get('name')}"
                  for tc in suite.iter("testcase")})
    jxml.unlink(missing_ok=True)
    return ids


def render(ids: list[str]) -> str:
    L = [
        '"""OCE mandatory test registry (B2-R8, extended for B3).',
        "",
        "Single source of truth for the mandatory test registry, category",
        "assignment, expected per-category totals, and the required evidence",
        "artifact list. Generated from ACTUAL pytest collection by",
        "scripts/gen_mandatory_registry.py (B3-R8). The gate fails if the",
        "collected total differs from this registry — adding a test requires",
        "a deliberate regeneration in the same change.",
        '"""',
        "",
        'SCHEMA_VERSION = "2.1.0"',
        'VALIDATOR_VERSION = "2.1.0"',
        'EXPECTED_REPO = "dabiggestpoppa/larger-lab"',
        'EXPECTED_BRANCH = "oce-program-build"',
        "",
        "REQUIRED_ARTIFACTS = [",
    ]
    for s in REQUIRED_ARTIFACTS:
        L.append('    "%s",' % s)
    L += ["]", "", "ARTIFACT_CATEGORY_FILE = {"]
    for k, v in CATEGORY_FILES.items():
        L.append('    "%s": "%s",' % (k, v))
    L += ["}", "", "MANDATORY_TEST_IDS = ["]
    for n in ids:
        L.append('    "%s",' % n)
    L += ["]", "", "_CATEGORY_RULES = ["]
    for sub, cat in CATEGORY_RULES:
        L.append('    ("%s", "%s"),' % (sub, cat))
    L += [
        "]",
        "",
        "def category_of(node_id):",
        '    """Deterministic category for a canonical (junit-form) node id."""',
        "    for sub, cat in _CATEGORY_RULES:",
        "        if sub in node_id:",
        "            return cat",
        '    return "unit"',
        "",
        "def expected_counts():",
        '    """Expected per-category totals derived from the mandatory registry."""',
        "    counts = {}",
        "    for nid in MANDATORY_TEST_IDS:",
        "        counts[category_of(nid)] = counts.get(category_of(nid), 0) + 1",
        "    return counts",
        "",
        "def validate_registry():",
        '    """Fail closed if the registry is malformed (duplicates/unassignable)."""',
        "    from collections import Counter",
        "    dupes = [n for n, c in Counter(MANDATORY_TEST_IDS).items() if c > 1]",
        "    if dupes:",
        "        raise AssertionError('duplicate mandatory ids: %s' % dupes)",
        "    unknown = {c for c in expected_counts() if c not in ARTIFACT_CATEGORY_FILE}",
        "    if unknown:",
        '        raise AssertionError("categories missing results file: %s" % sorted(unknown))',
        "    return expected_counts()",
        "",
        'if __name__ == "__main__":',
        "    counts = validate_registry()",
        '    print("registry OK: %d mandatory tests, %d categories" % (sum(counts.values()), len(counts)))',
        "    for c in sorted(counts):",
        '        print("  %-24s %d" % (c, counts[c]))',
        "",
    ]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    # Optional argv[1] = a junit.xml already produced by running the suite;
    # when given, reuse it instead of re-running pytest (handy on Windows
    # where the bootstrap subprocess is awkward).
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        root = ET.parse(sys.argv[1]).getroot()
        suite = root.find("testsuite") or root
        ids = sorted({f"{tc.get('classname')}::{tc.get('name')}"
                      for tc in suite.iter("testcase")})
        print("collected %d mandatory ids from supplied junit" % len(ids))
    else:
        ids = collect_ids()
        print("collected %d mandatory ids" % len(ids))
    REGISTRY.write_text(render(ids), encoding="utf-8")
    sys.path.insert(0, str(CP / "scripts"))
    import b2_registry  # type: ignore  # noqa: E402
    counts = b2_registry.validate_registry()
    print("registry OK: total=%d categories=%d" % (sum(counts.values()), len(counts)))