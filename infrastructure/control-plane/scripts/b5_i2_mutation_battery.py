"""B5-I2 deterministic mutation battery harness (governed reproducibility tooling).

AUTHORIZED_STAGE=B5-I2-POST-MERGE-REPRODUCIBILITY-REPAIR.

Publishes the formerly local, unpublished `.b5i2_mutation_battery.py` scratch
runner as deterministic, fail-closed repository tooling.  Contract:

- the repository root is resolved from THIS FILE's location — no
  machine-specific absolute paths, no home-directory or host assumptions;
- the frozen B5-I2 implementation is copied into an isolated temporary tree
  and mutated ONLY there; the caller's tracked worktree is never written and
  the temporary state is always cleaned up (context-managed);
- a green control is proven first: the committed B5-I2 inventory must be
  exactly FROZEN_NODE_FLOOR (24) unique nodes, executed with zero
  failures/errors/skips — otherwise the run fails before any mutation;
- each of the 11 frozen mutations M1..M9 (M7a/M7b/M7c) is applied to exactly
  one target through a unique patch anchor (anchor must occur exactly once;
  a no-op change is refused), and must produce at least one INTENDED failure
  (an expected discriminating node id, or the documented failure class) —
  a mutation that stays green fails the run;
- pristine bytes are restored after every mutation and the control is
  re-proven green at the end;
- the canonical result is byte-deterministic JSON (sorted keys, no
  timestamps, no temp paths, no host names, no durations, no environment-
  dependent observations) and the process exits nonzero on any incomplete,
  vacuous, duplicated, skipped or non-discriminating run.

Usage:
    python infrastructure/control-plane/scripts/b5_i2_mutation_battery.py \
        [--output PATH] [--raw-output PATH] [--verify PATH] [--timeout SECONDS]

Exit codes: 0 = battery green and verification (if requested) matched;
1 = any harness/battery/inventory/control failure; 2 = canonical output did
not match the committed evidence artifact byte-for-byte.
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
# Frozen identity constants (B5-I2)
# ---------------------------------------------------------------------------

SCHEMA_ID = "oce.b5-i2.reproducibility-result"
SCHEMA_VERSION = "1.0.0"

#: The exact merge commit that landed B5-I2 on main — the implementation
#: identity this battery is executed against.  Hard-pinned historical fact.
MERGED_B5_I2_SHA = "e3e38e83866fd6b1897531b0149c568a16b80177"

CONTROL_PLANE_DIR = "infrastructure/control-plane"
TEST_FILE = "infrastructure/control-plane/tests/test_console_contracts.py"
PACK = "infrastructure/control-plane/contracts/console-contract.json"
MODULE = "infrastructure/control-plane/src/oce_control/console_contracts.py"
SCHEMA = "infrastructure/control-plane/contracts/job-envelope.schema.json"
HARNESS_PATH = "infrastructure/control-plane/scripts/b5_i2_mutation_battery.py"

#: Frozen I-1 floor: the committed B5-I2 inventory is exactly this many
#: unique test nodes.  Anything else (23, 25, duplicates) fails closed.
FROZEN_NODE_FLOOR = 24

_PYTEST = [sys.executable, "-m", "pytest"]
_COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__", ".pytest_cache", ".mypy_cache", "*.pyc",
    ".runtime", "*.egg-info",
)


class HarnessError(Exception):
    """Any fail-closed harness condition (inventory, control, discrimination)."""


class MutationError(HarnessError):
    """A mutation could not be applied as specified (anchor/no-op/target)."""


# ---------------------------------------------------------------------------
# The 11 frozen mutations (M1..M9, M7a/M7b/M7c)
#
# `expected` lists are the historically observed discriminating full node IDs;
# `output_pattern` documents the failure CLASS that additionally satisfies
# discrimination when the environment cannot even import the mutated module
# (e.g. M8's forbidden `import requests` on an interpreter without requests).
# ---------------------------------------------------------------------------

_M3_M5_NODES = [
    "infrastructure/control-plane/tests/test_console_contracts.py::TestGovernedInvokeSurfaces::test_submit_through_pack_is_the_governed_operation",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestGovernedInvokeSurfaces::test_submit_without_authority_yields_schema_valid_denial",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestGovernedInvokeSurfaces::test_cancel_and_retry_are_single_governed_operations",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestCanonicalStateAgreement::test_projected_job_agrees_verbatim_with_governed_state",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestDeterminism::test_identical_inputs_produce_byte_identical_projections",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestEvidenceIdentityBinding::test_evidence_manifest_binds_to_schema_and_operation",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestEvidenceIdentityBinding::test_denial_envelope_from_governed_authority_is_rendered_verbatim",
]
_M6_NODES = [
    "infrastructure/control-plane/tests/test_console_contracts.py::TestGovernedInvokeSurfaces::test_submit_through_pack_is_the_governed_operation",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestGovernedInvokeSurfaces::test_cancel_and_retry_are_single_governed_operations",
    "infrastructure/control-plane/tests/test_console_contracts.py::TestCanonicalStateAgreement::test_projected_job_agrees_verbatim_with_governed_state",
]
_CLOSURE_NODE = (
    "infrastructure/control-plane/tests/test_console_contracts.py::TestDeterminism::"
    "test_module_import_closure_has_no_llm_hosting_or_broker_dependencies"
)

MUTATIONS: list[dict[str, Any]] = [
    {
        "id": "M1",
        "name": "M1-pack-changed-python-did-not",
        "target": PACK,
        "kind": "text",
        "description": "pack refusal wording altered; Python untouched",
        "anchor": "refused before any side effect",
        "replacement": "refused before side effect",
        "expected": [
            "infrastructure/control-plane/tests/test_console_contracts.py::TestContractPack::test_pack_identity_is_pinned_in_this_test_file",
        ],
        "output_pattern": None,
    },
    {
        "id": "M2",
        "name": "M2-py-weakened-refusal-guard",
        "target": MODULE,
        "kind": "text",
        "description": "read_surface entry/kind guard disabled (unknown surface not refused)",
        "anchor": 'if entry is None or entry["kind"] != "read":',
        "replacement": "if False:",
        "expected": [
            "infrastructure/control-plane/tests/test_console_contracts.py::TestUnsupportedOperationRefusal::test_unknown_read_surface_refused_before_side_effects",
            "infrastructure/control-plane/tests/test_console_contracts.py::TestUnsupportedOperationRefusal::test_non_vacuous_negative_control_weakened_guard_admits",
        ],
        "output_pattern": None,
    },
    {
        "id": "M3",
        "name": "M3-py-wrong-authority-owner",
        "target": MODULE,
        "kind": "text",
        "description": "jobs.submit rebound to api.cancel_job inside dispatch",
        "anchor": ('        return api.submit_job(\n'
                   '            grant_id=request["grant_id"],'),
        "replacement": ('        return api.cancel_job(\n'
                        '            grant_id=request["grant_id"],'),
        "expected": _M3_M5_NODES,
        "output_pattern": None,
    },
    {
        "id": "M4",
        "name": "M4-py-read-kind-as-invoke-allowed",
        "target": MODULE,
        "kind": "text",
        "description": "invoke kind guard weakened: read-surface ids admitted as invoke",
        "anchor": 'if entry is None or entry["kind"] != "invoke":',
        "replacement": "if entry is None:",
        "expected": [
            "infrastructure/control-plane/tests/test_console_contracts.py::TestUnsupportedOperationRefusal::test_read_surface_id_used_as_invoke_is_refused",
        ],
        "output_pattern": None,
    },
    {
        "id": "M5",
        "name": "M5-py-submit-bypasses-dispatcher",
        "target": MODULE,
        "kind": "text",
        "description": "jobs.submit returns fabricated response; api.submit_job never called",
        "anchor": (
            '    if surface == "jobs.submit":\n'
            '        return api.submit_job(\n'
            '            grant_id=request["grant_id"],\n'
            '            actor_id=request["actor_id"],\n'
            '            job_type=request["job_type"],\n'
            '            payload=request["payload"],\n'
            '            **{k: request[k] for k in ("resource_scope", "environment", "priority") if k in request},\n'
            "        )"
        ),
        "replacement": (
            '    if surface == "jobs.submit":\n'
            '        return APIResponse(True, "success", {"job_id": "f" * 32})'
        ),
        "expected": _M3_M5_NODES,
        "output_pattern": None,
    },
    {
        "id": "M6",
        "name": "M6-py-fabricated-status",
        "target": MODULE,
        "kind": "text",
        "description": "projection fabricates unknown status 'completed'",
        "anchor": "    return {f: job_dict[f] for f in JOB_ENVELOPE_PROJECTED_FIELDS}",
        "replacement": (
            '    doc = {f: job_dict[f] for f in JOB_ENVELOPE_PROJECTED_FIELDS}\n'
            '    doc["status"] = "completed"\n'
            "    return doc"
        ),
        "expected": _M6_NODES,
        "output_pattern": None,
    },
    {
        "id": "M7a",
        "name": "M7a-schema-field-added",
        "target": SCHEMA,
        "kind": "schema",
        "description": "job-envelope schema gains an extra optional property",
        "op": {"op": "add_prop", "key": "rogue_field"},
        "anchor": "rogue_field",
        "expected": [
            "infrastructure/control-plane/tests/test_console_contracts.py::TestCanonicalStateAgreement::test_projected_job_agrees_verbatim_with_governed_state",
        ],
        "output_pattern": None,
    },
    {
        "id": "M7b",
        "name": "M7b-schema-field-removed",
        "target": SCHEMA,
        "kind": "schema",
        "description": "job-envelope schema loses property 'lease'",
        "op": {"op": "remove_prop", "key": "lease"},
        "anchor": "lease",
        "expected": _M6_NODES,
        "output_pattern": None,
    },
    {
        "id": "M7c",
        "name": "M7c-schema-field-renamed",
        "target": SCHEMA,
        "kind": "schema",
        "description": "job-envelope schema renames 'job_type' -> 'jobKind'",
        "op": {"op": "rename_prop", "old": "job_type", "new": "jobKind"},
        "anchor": "job_type",
        "expected": _M6_NODES,
        "output_pattern": None,
    },
    {
        "id": "M8",
        "name": "M8-forbidden-static-import",
        "target": MODULE,
        "kind": "text",
        "description": "module source gains 'import requests' (banned root)",
        "anchor": "from .schema_validator import validate",
        "replacement": "from .schema_validator import validate\n\nimport requests  # B5I2-MUTATION",
        "expected": [_CLOSURE_NODE],
        # Failure class: either the AST closure assertion names the banned
        # root, or the interpreter cannot import it at all (ModuleNotFoundError).
        "output_pattern": r"requests",
    },
    {
        "id": "M9",
        "name": "M9-dynamic-import-escape",
        "target": MODULE,
        "kind": "text",
        "description": "module source gains a __import__ call-form escape",
        "anchor": "\ndef validate_evidence_manifest(",
        "replacement": (
            '\n\ndef _b5i2_escape():  # B5I2-MUTATION\n'
            '    return __import__("json")\n'
            "\n\ndef validate_evidence_manifest("
        ),
        "expected": [_CLOSURE_NODE],
        "output_pattern": r"__import__|dynamic import",
    },
]


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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise HarnessError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def resolve_repo_root() -> Path:
    """Deterministic repository-root resolution from this file's location."""
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / ".git").exists() and (candidate / CONTROL_PLANE_DIR).is_dir():
            return candidate
    raise HarnessError("repository root not resolvable from harness location")


# ---------------------------------------------------------------------------
# Mutation application (fail-closed: unique anchor, no no-op, exact restore)
# ---------------------------------------------------------------------------

def apply_mutation(tree: Path, mutation: dict[str, Any]) -> None:
    """Apply ONE mutation inside the isolated tree. Raises MutationError on
    a missing/duplicated anchor, a failed precondition, or a no-op."""
    target = tree / mutation["target"]
    if not target.is_file():
        raise MutationError(f"{mutation['id']}: target missing in tree: {mutation['target']}")
    text, newline = _read_norm(target)

    if mutation["kind"] == "text":
        anchor, replacement = mutation["anchor"], mutation["replacement"]
        if anchor == replacement:
            raise MutationError(f"{mutation['id']}: replacement equals anchor (no-op mutation)")
        occurrences = text.count(anchor)
        if occurrences != 1:
            raise MutationError(
                f"{mutation['id']}: anchor occurs {occurrences}x in "
                f"{mutation['target']} (must occur exactly once)")
        mutated = text.replace(anchor, replacement)
    elif mutation["kind"] == "schema":
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MutationError(f"{mutation['id']}: schema does not parse: {exc}") from None
        props = doc.get("properties")
        if not isinstance(props, dict):
            raise MutationError(f"{mutation['id']}: schema has no properties object")
        op = mutation["op"]
        if op["op"] == "add_prop":
            if op["key"] in props:
                raise MutationError(f"{mutation['id']}: property already present: {op['key']}")
            props[op["key"]] = {"type": "string"}
        elif op["op"] == "remove_prop":
            if op["key"] not in props:
                raise MutationError(f"{mutation['id']}: property absent: {op['key']}")
            props.pop(op["key"])
        elif op["op"] == "rename_prop":
            if op["old"] not in props:
                raise MutationError(f"{mutation['id']}: property absent: {op['old']}")
            if op["new"] in props:
                raise MutationError(f"{mutation['id']}: target name already present: {op['new']}")
            props[op["new"]] = props.pop(op["old"])
        else:
            raise MutationError(f"{mutation['id']}: unknown schema op: {op['op']}")
        mutated = json.dumps(doc, indent=2) + "\n"
    else:
        raise MutationError(f"{mutation['id']}: unknown mutation kind: {mutation['kind']}")

    if mutated == text:
        raise MutationError(f"{mutation['id']}: mutation changed nothing (no-op refused)")
    _write_norm(target, mutated, newline)


def restore_pristine(tree: Path, target_rel: str, pristine: bytes) -> None:
    (tree / target_rel).write_bytes(pristine)


# ---------------------------------------------------------------------------
# Pytest execution (deterministic subset: no environment data is serialized)
# ---------------------------------------------------------------------------

def _pytest_env() -> dict[str, str]:
    import os
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONHASHSEED"] = "0"
    return env


def _run_cmd(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           errors="replace", timeout=timeout, env=_pytest_env())
    except subprocess.TimeoutExpired:
        raise HarnessError(f"command timed out after {timeout}s: {' '.join(cmd[:4])}...") from None
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def collect_nodes(tree: Path, test_relpath: str, timeout: int) -> tuple[list[str], Optional[int]]:
    rc, out = _run_cmd(
        [*_PYTEST, test_relpath, "--collect-only", "-q", "-o", "addopts="],
        tree, timeout)
    nodes: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if test_relpath + "::" in line:
            nodes.append(line[line.index(test_relpath):])
    m = re.search(r"^(\d+) tests? collected", out, re.M)
    declared = int(m.group(1)) if m else None
    if rc not in (0, 5):
        raise HarnessError(f"collection failed (exit {rc})")
    return nodes, declared


def run_tests(tree: Path, test_relpath: str, junit_path: Path, timeout: int) -> dict[str, Any]:
    rc, out = _run_cmd(
        [*_PYTEST, test_relpath, "-q", "--tb=line", "-rfE",
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

def prove_control(tree: Path, test_relpath: str, expected_nodes: int,
                  timeout: int, phase: str) -> list[str]:
    nodes, declared = collect_nodes(tree, test_relpath, timeout)
    unique = sorted(set(nodes))
    problems: list[str] = []
    if declared is None:
        problems.append("collection summary line missing")
    elif declared != len(nodes):
        problems.append(f"pytest reported {declared} collected; parsed {len(nodes)}")
    if len(unique) != expected_nodes:
        problems.append(
            f"unique inventory {len(unique)} != required {expected_nodes} frozen B5-I2 nodes")
    if len(nodes) != len(unique):
        dupes = sorted({n for n in nodes if nodes.count(n) > 1})
        problems.append(f"duplicate node ids: {dupes}")
    if problems:
        # Fail fast on inventory problems BEFORE executing anything: a wrong
        # or duplicated inventory is already a terminal, fail-closed state.
        raise HarnessError(
            f"control proof ({phase}) inventory failed: " + "; ".join(problems))

    run = run_tests(tree, test_relpath, tree / f".junit-{phase}.xml", timeout)
    t = run["totals"]
    if run["returncode"] != 0:
        problems.append(f"control {phase} not green (exit {run['returncode']})")
    if t["tests"] != expected_nodes:
        problems.append(f"executed {t['tests']} != required {expected_nodes}")
    for key in ("failures", "errors"):
        if t[key]:
            problems.append(f"control {phase}: {key}={t[key]}")
    if t["skipped"]:
        problems.append(f"control {phase}: skipped={t['skipped']} (zero-skip law)")
    if problems:
        raise HarnessError(f"control proof ({phase}) failed: " + "; ".join(problems))
    return unique


# ---------------------------------------------------------------------------
# Battery execution (isolated temp tree; caller worktree never written)
# ---------------------------------------------------------------------------

def _snapshot_tracked(root: Path) -> Optional[str]:
    try:
        return _git(root, "status", "--porcelain", "--untracked-files=no")
    except HarnessError:
        return None


def execute_battery(
    *,
    source_root: Path,
    copy_paths: list[str],
    test_relpath: str,
    expected_node_count: int,
    mutations: list[dict[str, Any]],
    timeout: int,
) -> dict[str, Any]:
    """Run control -> 11 mutations -> control in an isolated temp copy.

    Returns the canonical core result. Raises HarnessError/MutationError on
    any incomplete, vacuous or non-discriminating state.
    """
    for rel in copy_paths:
        if not (source_root / rel).exists():
            raise HarnessError(f"copy source missing: {rel}")

    tracked_before = _snapshot_tracked(source_root)

    with tempfile.TemporaryDirectory(prefix="b5i2-repro-", ignore_cleanup_errors=True) as td:
        tree = Path(td) / "tree"
        for rel in copy_paths:
            src = source_root / rel
            dst = tree / rel
            if src.is_dir():
                shutil.copytree(src, dst, ignore=_COPY_IGNORE, symlinks=False)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        pristine: dict[str, bytes] = {}
        for m in mutations:
            target = tree / m["target"]
            if not target.is_file():
                raise HarnessError(f"mutation target absent in isolated copy: {m['target']}")
            pristine[m["target"]] = target.read_bytes()

        # 1) Green control + frozen inventory BEFORE any mutation.
        baseline_nodes = prove_control(tree, test_relpath, expected_node_count,
                                       timeout, "baseline")

        # 2) Every mutation must discriminate; restore pristine bytes after each.
        outcomes: list[dict[str, Any]] = []
        for m in mutations:
            apply_mutation(tree, m)
            if (tree / m["target"]).read_bytes() == pristine[m["target"]]:
                raise MutationError(f"{m['id']}: tree unchanged after apply (no-op)")
            run = run_tests(tree, test_relpath, tree / f".junit-{m['id']}.xml", timeout)
            observed = run["failing_nodes"]
            node_match = any(
                any(exp in node for node in observed)
                for exp in m["expected"]
            )
            class_match = bool(m["output_pattern"]) and bool(
                re.search(m["output_pattern"], run["output"], re.IGNORECASE))
            discriminated = run["returncode"] != 0 and (node_match or class_match)
            restore_pristine(tree, m["target"], pristine[m["target"]])
            if (tree / m["target"]).read_bytes() != pristine[m["target"]]:
                raise HarnessError(f"{m['id']}: restore failed (pristine bytes not recovered)")
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
                "outcome": "DISCRIMINATED" if discriminated else "NOT_DISCRIMINATED",
            })
            if not discriminated:
                raise HarnessError(
                    f"{m['id']} did not discriminate: exit={run['returncode']} "
                    f"observed={observed} expected={m['expected']} "
                    f"class={m['output_pattern']!r}")

        # 3) Restore proof: control green again after the full battery.
        prove_control(tree, test_relpath, expected_node_count, timeout, "restored")

    tracked_after = _snapshot_tracked(source_root)
    worktree_unchanged = (tracked_before is not None
                          and tracked_before == tracked_after)

    return {
        "baseline_nodes": baseline_nodes,
        "outcomes": outcomes,
        "caller_tracked_worktree_unmodified": worktree_unchanged,
    }


# ---------------------------------------------------------------------------
# Canonical artifact
# ---------------------------------------------------------------------------

def canonical_json(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def build_canonical(core: dict[str, Any], root: Path) -> dict[str, Any]:
    test_blob = _git(root, "rev-parse", f"HEAD:{TEST_FILE}")
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
            "outcome": out["outcome"],
        })
    return {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "implementation": {
            "merged_b5_i2_sha": MERGED_B5_I2_SHA,
            "test_file": TEST_FILE,
            "test_file_blob_sha": test_blob,
            "harness_path": HARNESS_PATH,
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
    parser = argparse.ArgumentParser(description="B5-I2 deterministic mutation battery harness")
    parser.add_argument("--output", help="write the canonical result JSON to this path")
    parser.add_argument("--raw-output",
                        help="write env-dependent raw observations (observed failures) to this path")
    parser.add_argument("--verify", help="canonical output must byte-match this committed artifact")
    parser.add_argument("--timeout", type=int, default=600,
                        help="per-pytest-invocation timeout in seconds")
    args = parser.parse_args(argv)

    root = resolve_repo_root()

    core = execute_battery(
        source_root=root,
        copy_paths=[CONTROL_PLANE_DIR],
        test_relpath=TEST_FILE,
        expected_node_count=FROZEN_NODE_FLOOR,
        mutations=MUTATIONS,
        timeout=args.timeout,
    )
    doc = build_canonical(core, root)
    text = canonical_json(doc)

    if not core["caller_tracked_worktree_unmodified"]:
        print("HARNESS FAILURE: caller tracked worktree changed during the run",
              file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)

    if args.raw_output:
        raw = {
            "note": "environment-dependent observations; not canonical authority",
            "observations": [
                {k: o[k] for k in ("id", "matched_by", "observed_failures",
                                   "returncode", "outcome")}
                for o in core["outcomes"]
            ],
        }
        Path(args.raw_output).write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    if args.verify:
        committed = Path(args.verify)
        if not committed.is_file():
            print(f"VERIFY FAILURE: committed artifact missing: {args.verify}", file=sys.stderr)
            return 2
        if committed.read_bytes() != text.encode("utf-8"):
            print(f"VERIFY FAILURE: canonical output does not byte-match {args.verify}",
                  file=sys.stderr)
            return 2

    print(
        f"BATTERY VERDICT: ALL_DISCRIMINATED — control {FROZEN_NODE_FLOOR}/{FROZEN_NODE_FLOOR} "
        f"green, {len(core['outcomes'])}/{len(MUTATIONS)} mutations discriminated, "
        "restored control green, caller worktree unmodified",
        file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
