"""B5-I6 deterministic mutation battery harness (X1 governed reproducibility tooling).

AUTHORIZED_STAGE=B5-I6-POST-MERGE-CLOSURE-X1-AUTHORITATIVE-EXECUTION.

Publishes a sanitized, deterministic, fail-closed mutation battery for the
exact final B5-I6 implementation (the formerly EXTERNAL, unpublished 11/11
battery recorded in ledger section 17.4 could not be reproduced from the
repository; per the authorized closure mission this harness is published in
the corrective branch rather than pretending the scratch battery exists).

Contract (modeled on the governed B5-I2 battery,
``b5_i2_mutation_battery.py``):

- the target tree is resolved from ``--target-tree`` (fail-closed against
  ``--require-head``); no machine-specific paths, no home/host assumptions;
- the target's B5-I6 surface is copied into an isolated temporary tree and
  mutated ONLY there; the caller's tracked worktree is never written and the
  temporary state is always cleaned up (context-managed);
- the isolated tree receives its own single-commit ``git init`` so the
  release-manifest tool's ``git rev-parse HEAD`` works inside the sandbox
  (the manifest tests are part of the control surface);
- a green control is proven FIRST: the committed inventory must be exactly
  FROZEN_NODE_FLOOR (27) unique nodes across the four B5-I6 suites, executed
  with zero failures/errors/skips — otherwise the run fails before any
  mutation;
- each of the 11 frozen mutations M1..M11 is applied to exactly one target
  through a unique patch anchor (anchor must occur exactly once; a no-op
  change is refused) and must produce at least one INTENDED failing node;
  a mutation that stays green fails the run;
- pristine bytes are restored after every mutation (byte-hash verified in
  the outcome record) and the control is re-proven green at the end;
- the canonical result is byte-deterministic JSON (sorted keys, no
  timestamps, no temp paths, no host names, no durations); environment-
  dependent observations (observed failing nodes, return codes) go to the
  separate ``--raw-output`` document;
- the process exits nonzero on any incomplete, vacuous, duplicated, skipped
  or non-discriminating run.

Usage:
    python infrastructure/control-plane/scripts/b5_i6_mutation_battery.py \\
        --target-tree PATH [--require-head SHA] \\
        [--output PATH] [--raw-output PATH] [--timeout SECONDS]

Exit codes: 0 = battery green (control 27/27 before and after, 11/11
discriminated, restores verified); 1 = any harness/battery/inventory/
control/discrimination/restore/identity failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Frozen identity constants (B5-I6 X1)
# ---------------------------------------------------------------------------

SCHEMA_ID = "oce.b5-i6.mutation-battery-result"
SCHEMA_VERSION = "1.0.0"

CONTROL_PLANE_DIR = "infrastructure/control-plane"
CONSOLE_DIR = "infrastructure/console"
COPY_PATHS = [CONTROL_PLANE_DIR, CONSOLE_DIR]

TEST_FILES = [
    "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py",
    "infrastructure/control-plane/tests/test_b5_i6_console_restart.py",
    "infrastructure/control-plane/tests/test_b5_i6_fail_closed.py",
    "infrastructure/control-plane/tests/test_b5_i6_deploy_pkg.py",
]

#: Frozen B5-I6 floor (acceptance matrix): the committed inventory across the
#: four suites is exactly this many unique test nodes. Anything else fails
#: closed before any mutation runs.
FROZEN_NODE_FLOOR = 27

_M = "B5I6-MUTATION"

# Each mutation weakens ONE load-bearing invariant of the final B5-I6
# implementation. Anchors were verified to occur EXACTLY ONCE in their target
# file (fail-closed re-verified at apply time anyway).
MUTATIONS: list[dict[str, Any]] = [
    {
        "id": "M1",
        "name": "M1-consent-gate-bypass",
        "target": "infrastructure/console/src/oce_console/session_store.py",
        "kind": "text",
        "description": "F-6 consent gate disabled: consent-less replay admitted",
        "anchor": "if consent is not True:",
        "replacement": f"if consent is not True and False:  # {_M}",
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py"
            "::TestConsentReplay::test_replay_without_consent_refused_before_actions",
        ],
        "output_pattern": None,
    },
    {
        "id": "M2",
        "name": "M2-append-only-prefix-guard-deleted",
        "target": "infrastructure/console/src/oce_console/session_store.py",
        "kind": "text",
        "description": "append-only prefix law deleted: prior actions may be rewritten",
        "anchor": (
            "            if (len(new_actions) < len(old_actions)\n"
            "                    or new_actions[:len(old_actions)] != old_actions):"
        ),
        "replacement": f"            if False:  # {_M}",
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_console_restart.py"
            "::TestRestartIdentity::test_non_append_rewrite_refused_and_completion_is_terminal",
        ],
        "output_pattern": None,
    },
    {
        "id": "M3",
        "name": "M3-partial-by-construction-broken",
        "target": "infrastructure/console/src/oce_console/session_store.py",
        "kind": "text",
        "description": "non-complete saves mint status=complete: a crash can leave a false completion",
        "anchor": "            status = SESSION_STATUS_PARTIAL",
        "replacement": f"            status = SESSION_STATUS_COMPLETE  # {_M}",
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_console_restart.py"
            "::TestConsoleCrash::test_session_record_marked_partial_on_crash",
        ],
        "output_pattern": None,
    },
    {
        "id": "M4",
        "name": "M4-completed-session-replayable",
        "target": "infrastructure/console/src/oce_console/session_store.py",
        "kind": "text",
        "description": "completion-terminal guard on resume deleted: a completed session is replayed",
        "anchor": (
            '        if record.get("status") == SESSION_STATUS_COMPLETE:\n'
            '            raise DrillRefusal("session_already_complete",\n'
            '                               "a completed session is never replayed")'
        ),
        "replacement": (
            f'        if record.get("status") == SESSION_STATUS_COMPLETE:  # {_M}\n'
            "            pass"
        ),
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py"
            "::TestConsentReplay::test_consented_replay_is_idempotent_and_no_duplicate_effect",
        ],
        "output_pattern": None,
    },
    {
        "id": "M5",
        "name": "M5-console-enacts-engine-recovery",
        "target": "infrastructure/console/src/oce_console/drill.py",
        "kind": "text",
        "description": "G8 bypass: the console drill module references the engine's real lease-recovery verb",
        "anchor": "def validate_session_record(record: dict) -> None:",
        "replacement": (
            f"def _b5i6_console_enacts_recovery():  # {_M}\n"
            "    return recover_abandoned_leases()\n"
            "\n"
            "\n"
            "def validate_session_record(record: dict) -> None:"
        ),
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py"
            "::TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting",
        ],
        "output_pattern": None,
    },
    {
        "id": "M6",
        "name": "M6-drill-pass-claim-guard-deleted",
        "target": "infrastructure/console/src/oce_console/drill.py",
        "kind": "text",
        "description": "DRILL_PASS claim guard deleted: a report is minted without the engine duplicate-effect sequence",
        "anchor": '    if disposition == "DRILL_PASS":',
        "replacement": f"    if False:  # {_M}",
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py"
            "::TestAdversarialControls::test_bypassed_authority_detected",
        ],
        "output_pattern": None,
    },
    {
        "id": "M7",
        "name": "M7-catalog-guard-deleted",
        "target": "infrastructure/console/src/oce_console/drill.py",
        "kind": "text",
        "description": "G5 catalog guard deleted: an unknown drill step is admitted",
        "anchor": (
            "        if unknown:\n"
            '            raise DrillRefusal("playbook_unknown_step", str(sorted(set(unknown))))'
        ),
        "replacement": (
            f"        if False:  # {_M}\n"
            '            raise DrillRefusal("playbook_unknown_step", str(sorted(set(unknown))))'
        ),
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py"
            "::TestFailClosed::test_unsupported_drill_operation_refused",
        ],
        "output_pattern": None,
    },
    {
        "id": "M8",
        "name": "M8-denial-summarized-green",
        "target": "infrastructure/console/src/oce_console/kernel.py",
        "kind": "text",
        "description": "denial-as-success: a denied governed response is summarized as plain OK",
        "anchor": "            state = STATE_DEGRADED",
        "replacement": f"            state = STATE_OK  # {_M}",
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_fail_closed.py"
            "::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry",
        ],
        "output_pattern": None,
    },
    {
        "id": "M9",
        "name": "M9-missing-identity-fabricated-green",
        "target": "infrastructure/console/src/oce_console/kernel.py",
        "kind": "text",
        "description": "gap fabrication: a non-envelope (401 detail) body projects as OK instead of UNVERIFIABLE",
        "anchor": (
            "        return {\n"
            '            "state": STATE_UNVERIFIABLE,\n'
            '            "reason": "envelope_fields_missing",\n'
            '            "raw": response,\n'
            "        }"
        ),
        "replacement": (
            "        return {\n"
            f'            "state": STATE_OK,  # {_M}\n'
            '            "reason": "envelope_fields_missing",\n'
            '            "raw": response,\n'
            "        }"
        ),
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_fail_closed.py"
            "::TestDenialRendering::test_missing_identity_renders_unverifiable_never_ok",
        ],
        "output_pattern": None,
    },
    {
        "id": "M10",
        "name": "M10-tamper-hash-check-skipped",
        "target": "infrastructure/console/packaging/make_release_manifest.py",
        "kind": "text",
        "description": "tampered install admitted: per-file sha256 comparison skipped by the verifier",
        "anchor": '        if actual_sha != entry["sha256"]:',
        "replacement": f'        if False and actual_sha != entry["sha256"]:  # {_M}',
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_deploy_pkg.py"
            "::TestReleaseManifest::test_tampered_install_file_fails_verification",
        ],
        "output_pattern": None,
    },
    {
        "id": "M11",
        "name": "M11-manifest-wallclock-nondeterminism",
        "target": "infrastructure/console/packaging/make_release_manifest.py",
        "kind": "text",
        "description": "determinism broken: the release manifest embeds a wall-clock nonce",
        "anchor": "    manifest = {",
        "replacement": (
            "    manifest = {\n"
            f'        "wallclock_nonce": __import__("time").time_ns(),  # {_M}'
        ),
        "expected": [
            "infrastructure/control-plane/tests/test_b5_i6_deploy_pkg.py"
            "::TestReleaseManifest::test_manifest_is_deterministic_byte_identical",
        ],
        "output_pattern": None,
    },
]

_PYTEST = [sys.executable, "-m", "pytest"]
_COPY_IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", "*.pyc",
    ".runtime", "*.egg-info",
)


class HarnessError(Exception):
    """Any fail-closed harness condition (inventory, control, identity)."""


class MutationError(Exception):
    """A mutation could not be applied, verified or restored."""


# ---------------------------------------------------------------------------
# File helpers (newline-preserving, byte-exact restore)
# ---------------------------------------------------------------------------

def _read_norm(path: Path) -> tuple[str, str]:
    """Return (text with \\n newlines, dominant newline of the raw file)."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8").replace("\r\n", "\n"), newline


def _write_norm(path: Path, text: str, newline: str) -> None:
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise HarnessError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def resolve_target_tree(value: Optional[str]) -> Path:
    if value:
        target = Path(value).resolve()
        if not (target / CONTROL_PLANE_DIR).is_dir() or not (target / CONSOLE_DIR).is_dir():
            raise HarnessError(f"--target-tree lacks required directories: {target}")
        return target
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / CONTROL_PLANE_DIR).is_dir() and (candidate / CONSOLE_DIR).is_dir():
            return candidate
    raise HarnessError("target tree not resolvable from harness location")


# ---------------------------------------------------------------------------
# Mutation application (fail-closed: unique anchor, no no-op, exact restore)
# ---------------------------------------------------------------------------

def apply_mutation(tree: Path, mutation: dict[str, Any]) -> None:
    """Apply ONE mutation inside the isolated tree."""
    target = tree / mutation["target"]
    if not target.is_file():
        raise MutationError(f"{mutation['id']}: target missing in tree: {mutation['target']}")
    text, newline = _read_norm(target)
    anchor, replacement = mutation["anchor"], mutation["replacement"]
    if anchor == replacement:
        raise MutationError(f"{mutation['id']}: replacement equals anchor (no-op mutation)")
    occurrences = text.count(anchor)
    if occurrences != 1:
        raise MutationError(
            f"{mutation['id']}: anchor occurs {occurrences}x in "
            f"{mutation['target']} (must occur exactly once)")
    mutated = text.replace(anchor, replacement)
    if mutated == text:
        raise MutationError(f"{mutation['id']}: mutation changed nothing (no-op refused)")
    _write_norm(target, mutated, newline)


def restore_pristine(tree: Path, target_rel: str, pristine: bytes) -> None:
    (tree / target_rel).write_bytes(pristine)


# ---------------------------------------------------------------------------
# Pytest execution (deterministic subset: no environment data serialized)
# ---------------------------------------------------------------------------

def _pytest_env() -> dict[str, str]:
    import os
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONHASHSEED"] = "0"
    return env


def _purge_bytecode(tree: Path) -> None:
    """Delete bytecode caches under the ISOLATED tree before every pytest run.

    Timestamp-based .pyc validation uses second-granularity mtime plus size:
    a mutation that changes neither could otherwise execute STALE bytecode
    and wrongly stay green. Purging makes every run compile current source.
    """
    for pycache in tree.rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)


def _run_cmd(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           errors="replace", timeout=timeout, env=_pytest_env())
    except subprocess.TimeoutExpired:
        raise HarnessError(f"command timed out after {timeout}s: {' '.join(cmd[:4])}...") from None
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def collect_nodes(tree: Path, timeout: int) -> tuple[list[str], Optional[int]]:
    _purge_bytecode(tree)
    rc, out = _run_cmd(
        [*_PYTEST, *TEST_FILES, "--collect-only", "-q", "-o", "addopts="],
        tree, timeout)
    nodes: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        for tf in TEST_FILES:
            if tf + "::" in line:
                nodes.append(line[line.index(tf):])
                break
    m = re.search(r"^(\d+) tests? collected", out, re.M)
    declared = int(m.group(1)) if m else None
    if rc not in (0, 5):
        raise HarnessError(f"collection failed (exit {rc})")
    return nodes, declared


def run_tests(tree: Path, junit_path: Path, timeout: int) -> dict[str, Any]:
    _purge_bytecode(tree)
    rc, out = _run_cmd(
        [*_PYTEST, *TEST_FILES, "-q", "--tb=line", "-rfE",
         "-o", "addopts=", f"--junitxml={junit_path}"],
        tree, timeout)
    failing: list[str] = []
    for line in out.splitlines():
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            parts = line.split()
            if len(parts) >= 2:
                failing.append(parts[1])
    totals = {"tests": -1, "failures": -1, "errors": -1, "skipped": -1}
    if junit_path.is_file():
        import xml.etree.ElementTree as ET
        root = ET.parse(junit_path).getroot()
        suites = [s for s in root.iter("testsuite") if s.get("name")]
        if not suites:
            suites = list(root.iter("testsuite"))
        totals = {k: sum(int(s.get(k) or 0) for s in suites)
                  for k in ("tests", "failures", "errors", "skipped")}
    return {
        "returncode": rc,
        "failing_nodes": sorted(set(failing)),
        "totals": totals,
        "output": out,
    }


# ---------------------------------------------------------------------------
# Control proof (inventory == frozen floor, zero skips, all green)
# ---------------------------------------------------------------------------

def prove_control(tree: Path, timeout: int, phase: str,
                  junit_root: Path) -> list[str]:
    nodes, declared = collect_nodes(tree, timeout)
    unique = sorted(set(nodes))
    problems: list[str] = []
    if declared is None:
        problems.append("collection summary line missing")
    elif declared != len(nodes):
        problems.append(f"pytest reported {declared} collected; parsed {len(nodes)}")
    if len(unique) != FROZEN_NODE_FLOOR:
        problems.append(
            f"unique inventory {len(unique)} != required {FROZEN_NODE_FLOOR} frozen B5-I6 nodes")
    if len(nodes) != len(unique):
        dupes = sorted({n for n in nodes if nodes.count(n) > 1})
        problems.append(f"duplicate node ids: {dupes}")
    missing_files = [tf for tf in TEST_FILES if not (tree / tf).is_file()]
    if missing_files:
        problems.append(f"suite files missing in tree: {missing_files}")
    if problems:
        raise HarnessError(
            f"control proof ({phase}) inventory failed: " + "; ".join(problems))

    run = run_tests(tree, junit_root / f"junit-{phase}.xml", timeout)
    t = run["totals"]
    if run["returncode"] != 0:
        problems.append(f"control {phase} not green (exit {run['returncode']})")
    if t["tests"] != FROZEN_NODE_FLOOR:
        problems.append(f"executed {t['tests']} != required {FROZEN_NODE_FLOOR}")
    for key in ("failures", "errors"):
        if t[key]:
            problems.append(f"control {phase}: {key}={t[key]}")
    if t["skipped"]:
        problems.append(f"control {phase}: skipped={t['skipped']} (zero-skip law)")
    if problems:
        raise HarnessError(f"control proof ({phase}) failed: " + "; ".join(problems))
    return unique


def _snapshot_tracked(root: Path) -> Optional[str]:
    try:
        return _git(root, "status", "--porcelain", "--untracked-files=no")
    except HarnessError:
        return None


def _init_sandbox_git(tree: Path) -> None:
    """Give the isolated tree its own single-commit repository so the
    release-manifest tool's ``git rev-parse HEAD`` works inside the sandbox
    (the manifest nodes are part of the B5-I6 control surface)."""
    _git(tree, "init", "-q")
    ident = ["-c", "user.email=battery@srra.local", "-c",
             "user.name=OCE B5-I6 Mutation Battery",
             "-c", "commit.gpgsign=false",
             "-c", "core.autocrlf=false"]
    subprocess.run(["git", "-C", str(tree), *ident, "add", "-A"],
                   capture_output=True, text=True, check=True)
    r = subprocess.run(
        ["git", "-C", str(tree), *ident, "commit", "-q",
         "-m", "B5-I6 mutation battery control tree"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise HarnessError(f"sandbox git commit failed: {r.stderr.strip()}")


# ---------------------------------------------------------------------------
# Battery execution (isolated temp tree; caller worktree never written)
# ---------------------------------------------------------------------------

def execute_battery(
    *,
    target_root: Path,
    timeout: int,
) -> tuple[dict[str, Any], Path]:
    """Run control -> 11 mutations -> control in an isolated temp copy.

    Returns (canonical core result, tempdir path for raw artifact reading).
    The tempdir is REMOVED by the caller context — raw observations must be
    extracted before cleanup, so this returns them inside core instead of a
    live path: (doc-shaped core, junit root is internal-only).
    """
    for rel in COPY_PATHS:
        if not (target_root / rel).exists():
            raise HarnessError(f"copy source missing: {rel}")

    tracked_before = _snapshot_tracked(target_root)

    with tempfile.TemporaryDirectory(prefix="b5i6-mut-", ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        tree = tmp / "tree"
        junit_root = tmp / "junit"
        junit_root.mkdir()
        for rel in COPY_PATHS:
            src = target_root / rel
            dst = tree / rel
            if src.is_dir():
                shutil.copytree(src, dst, ignore=_COPY_IGNORE, symlinks=False)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        _init_sandbox_git(tree)

        pristine: dict[str, bytes] = {}
        for m in MUTATIONS:
            target = tree / m["target"]
            if not target.is_file():
                raise HarnessError(f"mutation target absent in isolated copy: {m['target']}")
            pristine[m["target"]] = target.read_bytes()

        # 1) Green control + frozen inventory BEFORE any mutation.
        baseline_nodes = prove_control(tree, timeout, "baseline", junit_root)

        # 2) Every mutation must discriminate; restore pristine bytes after.
        outcomes: list[dict[str, Any]] = []
        for m in MUTATIONS:
            pristine_sha = _sha256_bytes(pristine[m["target"]])
            apply_mutation(tree, m)
            if _sha256_file(tree / m["target"]) == pristine_sha:
                raise MutationError(f"{m['id']}: tree unchanged after apply (no-op)")
            run = run_tests(tree, junit_root / f"junit-{m['id']}.xml", timeout)
            observed = run["failing_nodes"]
            node_match = any(
                any(exp in node for node in observed)
                for exp in m["expected"]
            )
            class_match = bool(m["output_pattern"]) and bool(
                re.search(m["output_pattern"], run["output"], re.IGNORECASE))
            discriminated = run["returncode"] != 0 and (node_match or class_match)
            restore_pristine(tree, m["target"], pristine[m["target"]])
            restored_sha = _sha256_file(tree / m["target"])
            if restored_sha != pristine_sha:
                raise HarnessError(
                    f"{m['id']}: restore failed (pristine bytes not recovered)")
            outcomes.append({
                "id": m["id"],
                "name": m["name"],
                "target": m["target"],
                "description": m["description"],
                "expected_discriminator": sorted(m["expected"]),
                "output_pattern": m["output_pattern"],
                "matched_by": ("node" if node_match else
                               "failure_class" if class_match else "NONE"),
                "observed_failures": observed,
                "returncode": run["returncode"],
                "pristine_sha256": pristine_sha,
                "restored_sha256": restored_sha,
                "restore_verified": restored_sha == pristine_sha,
                "outcome": "DISCRIMINATED" if discriminated else "NOT_DISCRIMINATED",
            })
            if not discriminated:
                raise HarnessError(
                    f"{m['id']} did not discriminate: exit={run['returncode']} "
                    f"observed={observed} expected={m['expected']} "
                    f"class={m['output_pattern']!r}")

        # 3) Restore proof: control green again after the full battery.
        restored_nodes = prove_control(tree, timeout, "restored", junit_root)
        if restored_nodes != baseline_nodes:
            raise HarnessError("restored control inventory differs from baseline")

    tracked_after = _snapshot_tracked(target_root)
    worktree_unchanged = (tracked_before is not None
                          and tracked_before == tracked_after)

    core = {
        "baseline_nodes": baseline_nodes,
        "outcomes": outcomes,
        "caller_tracked_worktree_unmodified": worktree_unchanged,
    }
    return core, tmp


# ---------------------------------------------------------------------------
# Canonical artifacts
# ---------------------------------------------------------------------------

def canonical_json(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def build_canonical(core: dict[str, Any], target_root: Path) -> dict[str, Any]:
    test_blob = _git(target_root, "rev-parse", f"HEAD:{TEST_FILES[0]}")
    harness_sha = _sha256_file(Path(__file__).resolve())
    baseline = {
        "collected": FROZEN_NODE_FLOOR,
        "unique_nodes": FROZEN_NODE_FLOOR,
        "nodes": core["baseline_nodes"],
        "passed": FROZEN_NODE_FLOOR,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "control_green": True,
        "restore_control_green": True,
    }
    mutations = []
    for out in core["outcomes"]:
        mutations.append({
            "id": out["id"],
            "name": out["name"],
            "target": out["target"],
            "description": out["description"],
            "expected_discriminator": out["expected_discriminator"],
            "pristine_sha256": out["pristine_sha256"],
            "restored_sha256": out["restored_sha256"],
            "restore_verified": out["restore_verified"],
            "outcome": out["outcome"],
        })
    return {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "implementation": {
            "test_files": list(TEST_FILES),
            "first_test_file_blob_sha": test_blob,
            "harness_path": "infrastructure/control-plane/scripts/b5_i6_mutation_battery.py",
            "harness_sha256": harness_sha,
        },
        "baseline": baseline,
        "mutations": mutations,
        "mutation_count": len(mutations),
        "discriminated_count": sum(1 for m in mutations if m["outcome"] == "DISCRIMINATED"),
        "unresolved_mutations": 0,
        "skipped_mutations": 0,
        "caller_tracked_worktree_unmodified": core["caller_tracked_worktree_unmodified"],
        "verdict": "ALL_DISCRIMINATED",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="B5-I6 deterministic mutation battery harness (X1)")
    parser.add_argument("--target-tree",
                        help="repository tree holding the final B5-I6 implementation")
    parser.add_argument("--require-head",
                        help="fail unless the target tree HEAD equals this SHA")
    parser.add_argument("--output", help="canonical result JSON output path")
    parser.add_argument("--raw-output",
                        help="environment-dependent observations output path")
    parser.add_argument("--timeout", type=int, default=600,
                        help="per-pytest-invocation timeout in seconds")
    args = parser.parse_args(argv)

    try:
        target_root = resolve_target_tree(args.target_tree)
        if args.require_head:
            head = _git(target_root, "rev-parse", "HEAD")
            if head != args.require_head:
                print(f"HARNESS FAILURE: target HEAD {head} != required "
                      f"{args.require_head}", file=sys.stderr)
                return 1
        core, _ = execute_battery(target_root=target_root, timeout=args.timeout)
        if not core["caller_tracked_worktree_unmodified"]:
            print("HARNESS FAILURE: caller tracked worktree changed during the run",
                  file=sys.stderr)
            return 1
        doc = build_canonical(core, target_root)
        text = canonical_json(doc)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(text)
        if args.raw_output:
            raw = {
                "note": "environment-dependent observations; not canonical authority",
                "target_head": _git(target_root, "rev-parse", "HEAD"),
                "target_tree": _git(target_root, "rev-parse", "HEAD^{tree}"),
                "observations": [
                    {k: o[k] for k in ("id", "matched_by", "observed_failures",
                                       "returncode", "outcome", "restore_verified")}
                    for o in core["outcomes"]
                ],
            }
            Path(args.raw_output).write_text(
                json.dumps(raw, indent=2, sort_keys=True) + "\n",
                encoding="utf-8", newline="\n")
        return 0
    except (HarnessError, MutationError) as exc:
        print(f"HARNESS FAILURE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
