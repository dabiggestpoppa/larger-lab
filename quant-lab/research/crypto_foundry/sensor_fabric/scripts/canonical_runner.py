#!/usr/bin/env python3
"""Hermetic canonical regression runner for the Sensor Fabric repository.

Why this exists
---------------
Repeated validation attempts on this repository failed operationally rather
than scientifically: sparse/incomplete checkouts, host disk exhaustion, tests
that rewrite tracked evidence, memory pressure from whole-suite runs, and no
accounting that the executed tests were the collected tests.  A green number
from such a run means nothing.

What it guarantees
------------------
1. The universe is *collected*, never invented: node IDs come from pytest.
2. The universe is partitioned deterministically (whole files, disjoint).
3. Every intended node is executed at most once, and the executed set is
   compared against the collected set exactly (missing / extra / duplicate).
4. Tracked evidence under the guarded prefixes is snapshotted, checked after
   each partition, restored, and the restoration is verified by re-hash.
5. Resource limits (free space, workers, timeout, artifact size) are enforced
   before and during execution.
6. Infrastructure failure is distinguished from test failure: a timeout, a
   crash, a missing JUnit file or a missing result stream is INCOMPLETE_INFRA,
   not a red test.
7. A run with any missing node never reports COMPLETE.

Deliberate non-goals
--------------------
It does not skip slow tests to produce a green result, does not clean the
worktree destructively, and does not touch any worktree other than the one it
is told to own.

Usage
-----
    python canonical_runner.py collect --workers 4
    python canonical_runner.py run --workers 4
    python canonical_runner.py verify <evidence.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

NODE_REQUIRED = "::"
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[4]
EVIDENCE_TREE = "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/canonical_runs"
#: The known mutation surface is the evidence trees, not all of ``research``.
#: Hashing 5,161 tracked research files (many of them large parquet) made the
#: safety mechanism itself the bottleneck, and every side-effecting writer in
#: this suite lives under ``evidence/``.
DEFAULT_GUARD_PREFIXES: tuple[str, ...] = (
    "quant-lab/research/crypto_foundry/sensor_fabric/evidence",
)
DEFAULT_MIN_FREE_BYTES = 2 * 1024**3
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_MAX_ARTIFACT_BYTES = 64 * 1024**2

DISPOSITION_COMPLETE = "COMPLETE"
DISPOSITION_COVERAGE = "INCOMPLETE_COVERAGE"
DISPOSITION_INFRA = "INCOMPLETE_INFRA"
DISPOSITION_INTERRUPTED = "INTERRUPTED"
DISPOSITION_REFUSED = "REFUSED_PRECONDITION"


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_node_ids(node_ids: Iterable[str]) -> str:
    return _sha256_text("\n".join(sorted(node_ids)))


def _git(cwd: Path, *args: str, timeout: int = 300) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout.decode("utf-8", "replace")


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(str(path)).free


def _chunks(items: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


# --------------------------------------------------------------------------- #
# Environment and ownership                                                   #
# --------------------------------------------------------------------------- #


def probe_environment(cwd: Path) -> dict[str, Any]:
    import platform

    pytest_version = "unknown"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            cwd=str(cwd),
            capture_output=True,
            timeout=120,
        )
        pytest_version = proc.stdout.decode("utf-8", "replace").strip() or "unknown"
    except Exception as exc:  # pragma: no cover - diagnostic only
        pytest_version = f"unavailable: {exc}"

    return {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "pytest": pytest_version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "cwd": str(cwd),
        "free_bytes_before": _free_bytes(cwd),
    }


def assert_ownership(cwd: Path, expect_branch: str | None) -> dict[str, Any]:
    """Refuse to operate on a worktree this runner does not own.

    A canonical runner that writes into a sibling agent's checkout is how one
    workstream silently corrupts another's evidence.  Ownership is proven from
    Git itself, not from a flag the caller typed.
    """
    toplevel = Path(_git(cwd, "rev-parse", "--show-toplevel").strip()).resolve()
    resolved = cwd.resolve()
    if toplevel != resolved:
        raise SystemExit(
            f"refusing: {resolved} is not a worktree root (git root is {toplevel})"
        )
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if expect_branch is not None and branch != expect_branch:
        raise SystemExit(
            f"refusing: worktree is on branch {branch!r}, expected {expect_branch!r}"
        )
    registered = [
        line.removeprefix("worktree ")
        for line in _git(cwd, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    resolved_registered = [str(Path(item).resolve()) for item in registered]
    if str(resolved) not in resolved_registered:
        raise SystemExit(f"refusing: {resolved} is not a registered worktree")
    return {
        "worktree": str(resolved),
        "branch": branch,
        "commit": _git(cwd, "rev-parse", "HEAD").strip(),
        "registered_worktrees": resolved_registered,
    }


def tree_state(cwd: Path, ignore_prefixes: Sequence[str]) -> dict[str, Any]:
    """Porcelain state, excluding our own evidence output and bytecode caches."""
    raw = _git(cwd, "status", "--porcelain").splitlines()
    dirty = []
    for line in raw:
        if not line.strip():
            continue
        path = line[3:].strip()
        if path.startswith("-> "):
            path = path[3:].strip()
        if any(path.startswith(prefix) for prefix in ignore_prefixes):
            continue
        if "__pycache__" in path or path.endswith(".pyc"):
            continue
        dirty.append(line)
    return {"clean_before": not dirty, "dirty_paths": dirty}


# --------------------------------------------------------------------------- #
# Collection                                                                  #
# --------------------------------------------------------------------------- #


def parse_node_ids(text: str) -> tuple[list[str], list[str]]:
    """Extract pytest node IDs from collector output.

    Anything that looks like a node ID but does not name a ``.py`` file is
    reported as malformed rather than silently dropped, so a parser change in
    pytest can never shrink the universe unnoticed.
    """
    nodes: list[str] = []
    malformed: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or NODE_REQUIRED not in line:
            continue
        if line.startswith(("=", "-", "ERROR", "WARNING", "warning")):
            continue
        head, _, tail = line.partition(NODE_REQUIRED)
        if not tail:
            continue
        if not head.endswith(".py"):
            malformed.append(line)
            continue
        nodes.append(line)
    return nodes, malformed


def collect(cwd: Path, extra_args: Sequence[str] = ()) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
        *extra_args,
    ]
    started = time.time()
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    nodes, malformed = parse_node_ids(text)

    seen: set[str] = set()
    duplicates: list[str] = []
    unique: list[str] = []
    for node in nodes:
        if node in seen:
            duplicates.append(node)
            continue
        seen.add(node)
        unique.append(node)

    collection_errors = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("ERROR") or " error" in line.lower()
    ]

    groups: dict[str, int] = {}
    for node in unique:
        path = node.partition("::")[0]
        group = str(Path(path).parent)
        groups[group] = groups.get(group, 0) + 1

    return {
        "collected_at": _now(),
        "duration_seconds": round(time.time() - started, 2),
        "exit_code": proc.returncode,
        "count": len(unique),
        "nodes": unique,
        "digest": _digest_node_ids(unique),
        "duplicates": duplicates,
        "malformed": malformed[:50],
        "malformed_count": len(malformed),
        "collection_errors": collection_errors[:20],
        "groups": dict(sorted(groups.items())),
    }


def partition(nodes: Sequence[str], workers: int) -> list[dict[str, Any]]:
    """Deterministic, disjoint, balanced partitioning by whole test file.

    Whole files (not split files) keep a partition's side effects attributable
    to one process, which is what makes evidence mutation diagnosable.
    """
    if workers < 1:
        raise SystemExit("refusing: --workers must be >= 1")

    by_file: dict[str, list[str]] = {}
    for node in nodes:
        by_file.setdefault(node.partition("::")[0], []).append(node)

    ordered = sorted(by_file.items(), key=lambda item: (-len(item[1]), item[0]))
    bins: list[list[str]] = [[] for _ in range(workers)]
    loads = [0] * workers
    for path, members in ordered:
        target = min(range(workers), key=lambda index: (loads[index], index))
        bins[target].append(path)
        loads[target] += len(members)

    partitions = []
    for index, files in enumerate(bins):
        intended = [node for node in nodes if node.partition("::")[0] in set(files)]
        partitions.append(
            {
                "index": index,
                "files": sorted(files),
                "intended_count": len(intended),
                "intended_nodes": sorted(intended),
            }
        )
    return partitions


# --------------------------------------------------------------------------- #
# Evidence containment                                                        #
# --------------------------------------------------------------------------- #


MAX_GUARD_FILES = 2000


def snapshot_untracked(cwd: Path, prefixes: Sequence[str]) -> list[str]:
    """Untracked files under the guarded prefixes (respecting .gitignore)."""
    raw = _git(cwd, "ls-files", "--others", "--exclude-standard", "-z", "--", *prefixes)
    return sorted(path for path in raw.split("\0") if path.strip())


def detect_new_untracked(
    cwd: Path,
    prefixes: Sequence[str],
    *,
    tracked_before: Sequence[str] | dict[str, str] | None = None,
    untracked_before: Sequence[str] = (),
    exclude_prefixes: Sequence[str] = (),
) -> list[str]:
    """New untracked files under guarded prefixes.

    The guard is fail-closed but non-destructive: it reports additions and
    never deletes anything.  The runner's own output tree is excluded, because
    the bundle is written there during the run by design.
    """
    known = set(untracked_before) | set(tracked_before or ())
    return [
        path
        for path in snapshot_untracked(cwd, prefixes)
        if path not in known
        and not any(path.startswith(prefix) for prefix in exclude_prefixes)
    ]


def snapshot_guarded(cwd: Path, prefixes: Sequence[str]) -> dict[str, str]:
    tracked = [
        path
        for path in _git(cwd, "ls-files", "-z", "--", *prefixes).split("\0")
        if path.strip()
    ]
    if len(tracked) > MAX_GUARD_FILES:
        raise SystemExit(
            f"refusing: guard prefixes cover {len(tracked)} tracked files, above the "
            f"{MAX_GUARD_FILES}-file ceiling; tighten --guard-prefixes rather than "
            "turning the containment guard into the bottleneck"
        )
    hashes: dict[str, str] = {}
    for path in tracked:
        candidate = cwd / path
        if candidate.exists():
            hashes[path] = _sha256_file(candidate)
    return hashes


def detect_modifications(cwd: Path, baseline: dict[str, str]) -> list[str]:
    modified = []
    for path, digest in baseline.items():
        candidate = cwd / path
        if not candidate.exists() or _sha256_file(candidate) != digest:
            modified.append(path)
    return sorted(modified)


def restore_and_verify(cwd: Path, paths: Sequence[str], baseline: dict[str, str]) -> dict[str, Any]:
    """Restore from Git, then prove the bytes match the baseline again."""
    if not paths:
        return {"attempted": False, "verified": True, "paths": [], "failed": []}
    for chunk in _chunks(list(paths), 40):
        _git(cwd, "checkout", "--", *chunk)
    still_wrong = [
        path
        for path in paths
        if (not (cwd / path).exists())
        or _sha256_file(cwd / path) != baseline.get(path, "")
    ]
    return {
        "attempted": True,
        "verified": not still_wrong,
        "paths": list(paths),
        "failed": still_wrong,
    }


# --------------------------------------------------------------------------- #
# Partition execution                                                         #
# --------------------------------------------------------------------------- #


def _read_results(path: Path) -> list[dict[str, Any]]:
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"nodeid": None, "when": "corrupt", "outcome": "error"})
    return records


PHASE_ORDER = ("setup", "call", "teardown")
SENTINEL_KEY = "record_type"
SENTINEL_VALUE = "session_end"


def _split_stream(
    records: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Separate test reports from the session sentinel that closes the stream."""
    reports: list[dict[str, Any]] = []
    sentinel: dict[str, Any] | None = None
    for record in records:
        if record.get(SENTINEL_KEY) == SENTINEL_VALUE:
            sentinel = record
            continue
        reports.append(record)
    return reports, sentinel


def _account_node(
    records: Sequence[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Derive one node's outcome from its phase reports, refusing to guess.

    R3: a pass is only a pass when the ``call`` phase says so.  Duplicate phase
    reports, unknown phases, and a missing ``call`` phase are accounting errors
    rather than a silent promotion.  Skips stay distinguishable: pytest reports
    a skipped test by failing the ``setup`` phase, never by omitting a pass.
    """
    issues: list[str] = []
    phases: dict[str, str | None] = {}
    for record in records:
        when = record.get("when")
        if when not in PHASE_ORDER:
            issues.append(f"unexpected_report_phase:{when}")
            continue
        if when in phases:
            issues.append(f"duplicate_phase_report:{when}")
            continue
        phases[when] = record.get("outcome")

    setup = phases.get("setup")
    call = phases.get("call")
    teardown = phases.get("teardown")

    if "failed" in (setup, teardown):
        outcome = "error"
    elif call == "passed":
        outcome = "passed"
    elif call == "failed":
        outcome = "failed"
    elif call == "skipped":
        outcome = "skipped"
    elif call is None and "skipped" in (setup, teardown):
        outcome = "skipped"
    elif call is None:
        issues.append("missing_call_phase")
        outcome = "error"
    else:
        issues.append(f"unexpected_call_outcome:{call}")
        outcome = "error"
    return outcome, issues


def _outcome_for(records: Sequence[dict[str, Any]]) -> tuple[str, int]:
    """Backwards-compatible wrapper: outcome plus the skipped-report count."""
    outcome, _ = _account_node(records)
    skipped = sum(1 for record in records if record.get("outcome") == "skipped")
    return outcome, skipped


def run_partition(
    cwd: Path,
    part: dict[str, Any],
    run_dir: Path,
    *,
    timeout: int,
    min_free_bytes: int,
    max_artifact_bytes: int,
    baseline: dict[str, str],
    extra_args: Sequence[str] = (),
) -> dict[str, Any]:
    index = part["index"]
    results_path = run_dir / f"results_{index}.jsonl"
    junit_path = run_dir / f"junit_{index}.xml"
    for stale in (results_path, junit_path):
        if stale.exists():
            stale.unlink()

    state: dict[str, Any] = {
        "index": index,
        "files": part["files"],
        "intended_count": part["intended_count"],
        "intended_nodes": part["intended_nodes"],
        "status": "pending",
        "timed_out": False,
        "infrastructure_error": None,
        "exit_code": None,
        "executed_nodes": [],
        "outcomes": {},
        "counts": {"passed": 0, "failed": 0, "errored": 0, "skipped": 0},
        "duration_seconds": 0.0,
        "junit_sha256": None,
        "junit_bytes": None,
        "junit_case_count": None,
        "record_count": 0,
        "stream": {},
        "accounting_errors": [],
        "free_bytes_before": _free_bytes(cwd),
        "free_bytes_after": None,
        "modified_paths": [],
        "restoration": {"attempted": False, "verified": True, "paths": [], "failed": []},
    }

    if state["free_bytes_before"] < min_free_bytes:
        state["status"] = "infrastructure_error"
        state["infrastructure_error"] = (
            f"free space {state['free_bytes_before']} < required {min_free_bytes}"
        )
        return state

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CANONICAL_RESULT_FILE"] = str(results_path)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SCRIPTS_DIR), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "-p",
        "canonical_pytest_plugin",
        *part["files"],
        f"--junitxml={junit_path}",
        *extra_args,
    ]

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
        state["exit_code"] = proc.returncode
    except subprocess.TimeoutExpired:
        state["timed_out"] = True
        state["status"] = "timeout"
    state["duration_seconds"] = round(time.time() - started, 1)
    state["free_bytes_after"] = _free_bytes(cwd)

    records, sentinel = _split_stream(_read_results(results_path))
    per_node: dict[str, list[dict[str, Any]]] = {}
    corrupt = 0
    for record in records:
        nodeid = record.get("nodeid")
        if not nodeid:
            corrupt += 1
            continue
        per_node.setdefault(nodeid, []).append(record)

    accounting: list[str] = []
    if corrupt:
        accounting.append(f"corrupt_result_records:{corrupt}")

    state["record_count"] = len(records)
    state["stream"] = {
        "records": len(records),
        "sentinel_present": sentinel is not None,
        "sentinel_reports": (sentinel or {}).get("reports"),
        "sentinel_nodes": (sentinel or {}).get("nodes"),
    }

    outcomes: dict[str, str] = {}
    for node, node_reports in sorted(per_node.items()):
        outcome, issues = _account_node(node_reports)
        outcomes[node] = outcome
        accounting.extend(f"{node}: {issue}" for issue in issues)

    if sentinel is None:
        accounting.append(
            "stream_sentinel_missing: the result stream was never closed by a "
            "session, so it may be truncated"
        )
    else:
        written = sentinel.get("reports")
        seen_nodes = sentinel.get("nodes")
        if written is not None and written != len(records):
            accounting.append(
                f"stream_report_count_mismatch: {len(records)} reports survived but "
                f"the session wrote {written}"
            )
        if seen_nodes is not None and seen_nodes != len(per_node):
            accounting.append(
                f"stream_node_count_mismatch: {len(per_node)} node identities "
                f"survived but the session saw {seen_nodes}"
            )

    state["executed_nodes"] = sorted(per_node)
    state["outcomes"] = outcomes
    state["accounting_errors"] = accounting
    for outcome in state["outcomes"].values():
        key = {
            "passed": "passed",
            "failed": "failed",
            "error": "errored",
            "skipped": "skipped",
        }.get(outcome, "errored")
        state["counts"][key] += 1

    if junit_path.exists():
        state["junit_bytes"] = junit_path.stat().st_size
        state["junit_sha256"] = _sha256_file(junit_path)
        state["junit_case_count"] = _junit_case_count(junit_path)

    # Infrastructure vs test failure is decided here, not by a red number.
    if state["timed_out"]:
        state["status"] = "timeout"
        state["infrastructure_error"] = f"partition exceeded {timeout}s"
    elif state["exit_code"] in (2, 3, 4, 5):
        state["status"] = "infrastructure_error"
        state["infrastructure_error"] = (
            f"pytest exit {state['exit_code']} (interrupted/usage/no-tests/collect) "
            "is an infrastructure condition, not a test verdict"
        )
    elif not results_path.exists():
        state["status"] = "infrastructure_error"
        state["infrastructure_error"] = "no result stream produced by the plugin"
    elif not junit_path.exists():
        state["status"] = "infrastructure_error"
        state["infrastructure_error"] = "no JUnit artifact produced"
    elif state["junit_bytes"] is not None and state["junit_bytes"] > max_artifact_bytes:
        state["status"] = "infrastructure_error"
        state["infrastructure_error"] = (
            f"JUnit artifact {state['junit_bytes']} exceeds {max_artifact_bytes}"
        )
    else:
        state["status"] = "ok"

    # Detect producer side effects now, against the PRE-run baseline.  Restoration
    # happens once, after every partition finishes, so parallel workers can never
    # restore a file another partition is still writing.
    state["modified_paths"] = detect_modifications(cwd, baseline)
    return state


# --------------------------------------------------------------------------- #
# Verdict                                                                     #
# --------------------------------------------------------------------------- #


_COUNT_KEYS = ("passed", "failed", "errored", "skipped")

_OUTCOME_TO_COUNT = {
    "passed": "passed",
    "failed": "failed",
    "error": "errored",
    "skipped": "skipped",
}


def _recompute_counts(outcomes: dict[str, str]) -> dict[str, int]:
    """Recompute pytest-style totals from a per-node outcome map."""
    counts = {key: 0 for key in _COUNT_KEYS}
    for outcome in outcomes.values():
        counts[_OUTCOME_TO_COUNT.get(outcome, "errored")] += 1
    return counts


def _junit_cases(path: Path) -> list[tuple[str | None, str | None]] | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    return [
        (case.get("classname"), case.get("name"))
        for case in root.iter("testcase")
    ]


def _junit_case_count(path: Path) -> int | None:
    cases = _junit_cases(path)
    return None if cases is None else len(cases)


def _junit_identity(node: str) -> tuple[str, str]:
    """Rebuild the ``(classname, name)`` pytest's JUnit writer uses for a node.

    pytest mangles a node ID by replacing the path separator with a dot, dropping
    the ``.py`` suffix, joining class segments, and leaving the final segment --
    including any parametrisation, spaces and punctuation -- verbatim as the case
    name.  This is verified against the committed bundle, where the derived set
    and the observed set are equal for all 4,719 cases.
    """
    head, *rest = node.split("::")
    path = head[:-3] if head.endswith(".py") else head
    classname = ".".join([path.replace("/", "."), *rest[:-1]]) if rest else path.replace("/", ".")
    return classname, (rest[-1] if rest else "")


def _node_file(node: str) -> str:
    return node.partition("::")[0]


def _reconcile_evidence(
    bundle: dict[str, Any],
    *,
    base_dir: Path | None,
    expected_count: int | None,
    expected_digest: str | None,
    require_anchor: bool = False,
) -> dict[str, Any]:
    """Recompute every published aggregate from the evidence it summarises.

    R2 closes the four R1 counterexamples: nothing a bundle *says* about itself
    is accepted when it can be derived from what the bundle *contains*.  Three
    independent authorities are consulted, in increasing order of strength:

    1. the bundle's own node lists (V02: digests and counts),
    2. the per-partition outcome maps and partition file intent (V01, V03),
    3. the JUnit artifacts and, when supplied, an external universe anchor
       (V04, V03).

    A bundle that agrees with all three is internally consistent.  It is not
    thereby *true* -- only an anchor recorded outside the bundle can establish
    that -- which is why `expected_count`/`expected_digest` exist.
    """
    integrity: list[str] = []
    coverage: list[str] = []
    infrastructure: list[str] = []
    summary: dict[str, Any] = {}

    collection = bundle.get("collection", {}) or {}
    execution = bundle.get("execution", {}) or {}
    coll_nodes = list(collection.get("nodes", []) or [])
    exec_nodes = list(execution.get("nodes", []) or [])

    # -- V02: digests and counts are recomputed, never trusted -------------
    if collection.get("count") is not None and collection["count"] != len(coll_nodes):
        integrity.append(
            "counts_reconciliation_failed: collection.count="
            f"{collection['count']} but {len(coll_nodes)} nodes are listed"
        )
    if collection.get("digest") and collection["digest"] != _digest_node_ids(coll_nodes):
        integrity.append(
            "digest_reconciliation_failed: collection.digest does not match the listed nodes"
        )
    if (
        execution.get("unique_count") is not None
        and execution["unique_count"] != len(exec_nodes)
    ):
        integrity.append(
            "counts_reconciliation_failed: execution.unique_count="
            f"{execution['unique_count']} but {len(exec_nodes)} nodes are listed"
        )
    if execution.get("digest") and execution["digest"] != _digest_node_ids(exec_nodes):
        integrity.append(
            "digest_reconciliation_failed: execution.digest does not match the listed nodes"
        )

    # -- V01: totals are recomputed from per-node outcomes -----------------
    partitions = execution.get("partitions", []) or []
    union: dict[str, str] = {}
    duplicated: list[str] = []
    for part in partitions:
        index = part.get("index")
        outcomes = part.get("outcomes") or {}
        recomputed = _recompute_counts(outcomes)
        recorded = part.get("counts")
        if recorded is not None and dict(recorded) != recomputed:
            integrity.append(
                f"counts_reconciliation_failed: partition {index} records {recorded} "
                f"but its outcomes sum to {recomputed}"
            )
        executed = part.get("executed_nodes")
        if executed is not None and sorted(executed) != sorted(outcomes):
            coverage.append(
                f"coverage_reconciliation_failed: partition {index} executed_nodes "
                "disagree with its per-node outcomes"
            )
        for node in outcomes:
            if node in union:
                duplicated.append(node)
            else:
                union[node] = outcomes[node]

        # -- V03: a partition may only account for the files it ran --------
        intended = part.get("intended_nodes")
        if intended is not None:
            stray = sorted(set(outcomes) - set(intended))
            if stray:
                coverage.append(
                    f"coverage_reconciliation_failed: partition {index} executed "
                    f"{len(stray)} node(s) it never intended, e.g. {stray[0]}"
                )
            if part.get("intended_count") is not None and part["intended_count"] != len(
                intended
            ):
                integrity.append(
                    f"counts_reconciliation_failed: partition {index} "
                    f"intended_count={part['intended_count']} but {len(intended)} "
                    "intended nodes"
                )
        else:
            files = set(part.get("files") or [])
            foreign = sorted(
                node for node in outcomes if files and _node_file(node) not in files
            )
            if foreign:
                coverage.append(
                    f"coverage_reconciliation_failed: partition {index} accounts for "
                    f"{len(foreign)} node(s) from files it did not run, e.g. {foreign[0]}"
                )

    if union and sorted(union) != sorted(exec_nodes):
        outcome_only = len(set(union) - set(exec_nodes))
        node_only = len(set(exec_nodes) - set(union))
        coverage.append(
            "coverage_reconciliation_failed: execution nodes disagree with the "
            f"per-node outcomes ({outcome_only} outcome-only, {node_only} node-only)"
        )
    if duplicated:
        coverage.append(
            f"coverage_reconciliation_failed: {len(duplicated)} node(s) reported by "
            "more than one partition"
        )
    if union:
        totals = _recompute_counts(union)
        recorded_totals = execution.get("counts")
        if recorded_totals is not None and dict(recorded_totals) != totals:
            integrity.append(
                f"counts_reconciliation_failed: execution.counts {recorded_totals} "
                f"but the per-node outcomes sum to {totals}"
            )
        summary["recomputed_counts"] = totals

    # -- V03: an external universe anchor, when supplied -------------------
    if expected_count is not None:
        summary["external_anchor_count"] = expected_count
        if expected_count != len(coll_nodes):
            integrity.append(
                f"digest_reconciliation_failed: external anchor count "
                f"{expected_count} != {len(coll_nodes)} collected"
            )
    if expected_digest is not None:
        summary["external_anchor_digest_checked"] = True
        if expected_digest != _digest_node_ids(coll_nodes):
            integrity.append(
                "digest_reconciliation_failed: external anchor digest does not "
                "match the collected nodes"
            )

    # -- V04: JUnit must agree with the result stream ----------------------
    if base_dir is not None:
        for part in partitions:
            recorded_sha = part.get("junit_sha256")
            if not recorded_sha:
                continue
            index = part.get("index")
            junit = Path(base_dir) / f"junit_{index}.xml"
            if not junit.exists():
                infrastructure.append(
                    f"junit_missing: partition {index} declares a JUnit artifact "
                    "that is not present"
                )
                continue
            if _sha256_file(junit) != recorded_sha:
                infrastructure.append(
                    f"junit_digest_mismatch: partition {index} JUnit bytes differ "
                    "from the recorded sha256"
                )
                continue
            cases = _junit_case_count(junit)
            executed = part.get("executed_nodes") or []
            if cases is None:
                infrastructure.append(
                    f"junit_unreadable: partition {index} JUnit artifact cannot be parsed"
                )
            elif cases != len(executed):
                infrastructure.append(
                    f"junit_case_count_mismatch: partition {index} JUnit reports "
                    f"{cases} cases but {len(executed)} nodes were executed"
                )
            else:
                observed = sorted(_junit_cases(junit) or [])
                expected = sorted(_junit_identity(node) for node in executed)
                if observed != expected:
                    mismatched = sum(1 for a, b in zip(observed, expected) if a != b)
                    infrastructure.append(
                        f"junit_identity_mismatch: partition {index} reports the "
                        f"expected case count but {mismatched} case identit(ies) do "
                        "not map to the executed node IDs"
                    )

    # -- R3: result-stream accounting reported by the producer -------------
    for part in partitions:
        index = part.get("index")
        errors = part.get("accounting_errors") or []
        if errors:
            coverage.append(
                f"accounting_failed: partition {index} reports {len(errors)} stream "
                f"accounting error(s), e.g. {errors[0]}"
            )
        stream = part.get("stream") or {}
        if stream:
            if not stream.get("sentinel_present"):
                coverage.append(
                    f"accounting_failed: partition {index} result stream has no "
                    "session sentinel and may be truncated"
                )
            recorded = part.get("record_count")
            if (
                recorded is not None
                and stream.get("sentinel_reports") is not None
                and recorded != stream["sentinel_reports"]
            ):
                coverage.append(
                    f"accounting_failed: partition {index} kept {recorded} report(s) "
                    f"of {stream['sentinel_reports']} written"
                )

    # -- R3: untracked additions under guarded prefixes --------------------
    untracked_added = (bundle.get("tree", {}) or {}).get("untracked_added") or []
    if untracked_added:
        infrastructure.append(
            f"untracked_evidence_added: {len(untracked_added)} new untracked file(s) "
            f"under guarded prefixes, e.g. {untracked_added[0]}"
        )

    # -- R3: assurance level -------------------------------------------------
    anchored = False
    recorded_anchor = bundle.get("universe_anchor") or {}
    if recorded_anchor.get("digest"):
        anchored = recorded_anchor["digest"] == _digest_node_ids(coll_nodes)
        summary["recorded_anchor_checked"] = True
    if expected_count is not None or expected_digest is not None:
        anchored = anchored or (
            expected_digest is None or expected_digest == _digest_node_ids(coll_nodes)
        ) and (expected_count is None or expected_count == len(coll_nodes))
        summary["external_anchor_checked"] = True
    summary["anchored"] = bool(anchored)
    if require_anchor and not anchored:
        integrity.append(
            "anchor_required: the bundle is self-consistent but carries no usable "
            "external universe anchor, so independent completeness is unproven"
        )

    return {
        "reasons": [*integrity, *coverage, *infrastructure],
        "integrity": integrity,
        "coverage": coverage,
        "infrastructure": infrastructure,
        "summary": summary,
    }


def evaluate_bundle(
    bundle: dict[str, Any],
    *,
    base_dir: Path | str | None = None,
    expected_count: int | None = None,
    expected_digest: str | None = None,
    require_anchor: bool = False,
) -> dict[str, Any]:
    """Pure verdict function: the only place COMPLETE can be produced.

    R2: the verdict is no longer a read of the bundle's own summary fields.  All
    derived numbers are recomputed from the evidence they claim to summarise, so
    a forged total, a forged digest, a silently shrunken universe or a JUnit
    artifact that disagrees with the result stream cannot verify as COMPLETE.
    """
    reasons: list[str] = []
    reconciliation = _reconcile_evidence(
        bundle,
        base_dir=Path(base_dir) if base_dir is not None else None,
        expected_count=expected_count,
        expected_digest=expected_digest,
        require_anchor=require_anchor,
    )
    reasons.extend(reconciliation["reasons"])

    collected = set(bundle.get("collection", {}).get("nodes", []))
    executed = set(bundle.get("execution", {}).get("nodes", []))
    missing = sorted(collected - executed)
    extra = sorted(executed - collected)

    duplicates = bundle.get("collection", {}).get("duplicates", [])
    duplicate_executions = bundle.get("execution", {}).get("duplicate_executions", [])
    collection_errors = bundle.get("collection", {}).get("collection_errors", [])
    malformed_count = bundle.get("collection", {}).get("malformed_count", 0)

    partitions = bundle.get("execution", {}).get("partitions", [])
    timed_out = [p["index"] for p in partitions if p.get("timed_out")]
    infra = [
        (p["index"], p.get("infrastructure_error"))
        for p in partitions
        if p.get("status") in ("infrastructure_error", "timeout")
    ]
    unimplemented = bundle.get("execution", {}).get("unimplemented_partitions", [])

    restoration = bundle.get("restoration", {})
    restoration_ok = restoration.get("verified", False)
    tree = bundle.get("tree", {})
    tree_clean_after = tree.get("clean_after", False)

    if collection_errors:
        reasons.append(f"collection_errors: {collection_errors[:3]}")
    if malformed_count:
        reasons.append(f"malformed_node_lines: {malformed_count}")
    if unimplemented:
        reasons.append(f"unimplemented_partitions: {unimplemented}")
    if timed_out:
        reasons.append(f"partition_timeout: {timed_out}")
    if infra:
        reasons.append(f"infrastructure_failures: {infra}")
    if duplicates:
        reasons.append(f"duplicate_collected_nodes: {len(duplicates)}")
    if duplicate_executions:
        reasons.append(f"duplicate_executions: {len(duplicate_executions)}")
    if missing:
        reasons.append(f"missing_nodes: {len(missing)}")
    if extra:
        reasons.append(f"extra_nodes: {len(extra)}")
    if not restoration_ok:
        reasons.append("evidence_restoration_unverified")
    if not tree_clean_after:
        reasons.append("worktree_not_clean_after_run")
    if bundle.get("interrupted"):
        reasons.append("interrupted")

    counts = bundle.get("execution", {}).get("counts", {})
    test_outcome = "RED" if (counts.get("failed") or counts.get("errored")) else "GREEN"

    if bundle.get("interrupted"):
        disposition = DISPOSITION_INTERRUPTED
    elif any(
        (
            collection_errors,
            malformed_count,
            unimplemented,
            timed_out,
            infra,
            not restoration_ok,
            not tree_clean_after,
            reconciliation["infrastructure"],
        )
    ):
        disposition = DISPOSITION_INFRA
    elif (
        duplicates
        or duplicate_executions
        or missing
        or extra
        or reconciliation["integrity"]
        or reconciliation["coverage"]
    ):
        disposition = DISPOSITION_COVERAGE
    else:
        disposition = DISPOSITION_COMPLETE

    if disposition != DISPOSITION_COMPLETE:
        assurance = "NOT_COMPLETE"
    elif reconciliation["summary"].get("anchored"):
        assurance = "ANCHORED_COMPLETE"
    else:
        assurance = "SELF_CONSISTENT_COMPLETE"

    return {
        "disposition": disposition,
        "assurance": assurance,
        "test_outcome": test_outcome,
        "reasons": reasons,
        "missing_nodes": missing[:100],
        "missing_count": len(missing),
        "extra_nodes": extra[:100],
        "extra_count": len(extra),
        "counts": counts,
        "reconciliation": reconciliation["summary"],
    }


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def run_canonical(args: argparse.Namespace) -> int:
    cwd = Path(args.worktree).resolve() if args.worktree else REPO_ROOT
    ownership = assert_ownership(cwd, args.expect_branch)
    state = tree_state(cwd, ignore_prefixes=(EVIDENCE_TREE,))
    if not state["clean_before"] and not args.allow_dirty:
        print(
            json.dumps(
                {
                    "disposition": DISPOSITION_REFUSED,
                    "reasons": ["worktree_not_clean_before_run"],
                    "dirty_paths": state["dirty_paths"][:20],
                },
                indent=2,
            )
        )
        return 3

    free_before = _free_bytes(cwd)
    if free_before < args.min_free_bytes:
        print(
            json.dumps(
                {
                    "disposition": DISPOSITION_REFUSED,
                    "reasons": [
                        f"free space {free_before} < required {args.min_free_bytes}"
                    ],
                },
                indent=2,
            )
        )
        return 4

    run_id = args.run_id or (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    )
    run_dir = cwd / EVIDENCE_TREE / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    guarded = snapshot_guarded(cwd, args.guard_prefixes)
    write_json(run_dir / "guard_baseline.json", guarded)
    untracked_before = snapshot_untracked(cwd, args.guard_prefixes)

    environment = probe_environment(cwd)
    collection = collect(cwd, args.extra)
    write_json(run_dir / "collection.json", collection)

    partitions = partition(collection["nodes"], args.workers)
    for part in partitions:
        write_json(run_dir / f"partition_{part['index']}.json", part)

    bundle: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _now(),
        "finished_at": None,
        "ownership": ownership,
        "environment": environment,
        "limits": {
            "min_free_bytes": args.min_free_bytes,
            "workers": args.workers,
            "partition_timeout_seconds": args.timeout,
            "max_artifact_bytes": args.max_artifact_bytes,
            "guard_prefixes": list(args.guard_prefixes),
        },
        "collection": {
            key: collection[key]
            for key in (
                "count",
                "digest",
                "duplicates",
                "malformed_count",
                "collection_errors",
                "groups",
                "exit_code",
            )
        }
        | {"nodes": collection["nodes"]},
        "execution": {
            "nodes": [],
            "duplicate_executions": [],
            "counts": {"passed": 0, "failed": 0, "errored": 0, "skipped": 0},
            "partitions": [],
            "unimplemented_partitions": [],
        },
        "universe_anchor": (
            {"count": args.expect_count, "digest": args.expect_digest}
            if (args.expect_count is not None or args.expect_digest is not None)
            else {}
        ),
        "restoration": {"verified": True, "paths": [], "attempted": False},
        "tree": {"clean_after": True, "dirty_paths": [], "untracked_added": []},
        "interrupted": False,
    }

    executed_nodes: list[str] = []
    seen_executed: set[str] = set()
    duplicate_executions: list[str] = []
    all_modified: list[str] = []

    def record(part: dict[str, Any]) -> dict[str, Any]:
        return run_partition(
            cwd,
            part,
            run_dir,
            timeout=args.timeout,
            min_free_bytes=args.min_free_bytes,
            max_artifact_bytes=args.max_artifact_bytes,
            baseline=guarded,
            extra_args=args.extra,
        )

    try:
        if args.workers > 1:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                results = list(pool.map(record, partitions))
        else:
            results = [record(part) for part in partitions]
    except KeyboardInterrupt:
        bundle["interrupted"] = True
        bundle["finished_at"] = _now()
        verdict = evaluate_bundle(bundle)
        write_json(run_dir / "evidence.json", bundle | {"verdict": verdict})
        print(json.dumps(verdict, indent=2))
        return 130

    for result in results:
        executed_nodes.extend(result["executed_nodes"])
        for node in result["executed_nodes"]:
            if node in seen_executed:
                duplicate_executions.append(node)
            seen_executed.add(node)
        for key, value in result["counts"].items():
            bundle["execution"]["counts"][key] += value
        all_modified.extend(result["modified_paths"])
        bundle["execution"]["partitions"].append(
            {key: value for key, value in result.items() if key != "intended_nodes"}
        )

    bundle["execution"]["nodes"] = sorted(seen_executed)
    bundle["execution"]["duplicate_executions"] = sorted(set(duplicate_executions))
    bundle["execution"]["digest"] = _digest_node_ids(seen_executed)
    bundle["execution"]["unique_count"] = len(seen_executed)

    restoration_paths = sorted(set(all_modified))
    if restoration_paths:
        bundle["restoration"] = restore_and_verify(cwd, restoration_paths, guarded)
    else:
        bundle["restoration"] = {
            "attempted": False,
            "verified": True,
            "paths": [],
            "failed": [],
        }

    after = tree_state(cwd, ignore_prefixes=(EVIDENCE_TREE,))
    bundle["tree"] = {
        "clean_after": after["clean_before"],
        "dirty_paths": after["dirty_paths"],
        "untracked_added": detect_new_untracked(
            cwd,
            args.guard_prefixes,
            tracked_before=guarded,
            untracked_before=untracked_before,
            exclude_prefixes=(EVIDENCE_TREE,),
        ),
    }
    bundle["finished_at"] = _now()
    bundle["environment"] = environment | {"free_bytes_after": _free_bytes(cwd)}

    verdict = evaluate_bundle(bundle)
    write_json(run_dir / "evidence.json", bundle | {"verdict": verdict})
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["disposition"] == DISPOSITION_COMPLETE else 1


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.evidence)
    if not path.exists():
        print(
            json.dumps(
                {
                    "disposition": DISPOSITION_INFRA,
                    "reasons": [f"evidence bundle not found: {path}"],
                },
                indent=2,
            )
        )
        return 2
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {
                    "disposition": DISPOSITION_INFRA,
                    "reasons": [f"corrupt evidence bundle: {exc}"],
                },
                indent=2,
            )
        )
        return 2
    verdict = evaluate_bundle(
        bundle,
        base_dir=path.parent,
        expected_count=args.expect_count,
        expected_digest=args.expect_digest,
        require_anchor=args.require_anchor,
    )
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["disposition"] == DISPOSITION_COMPLETE else 1


def cmd_collect(args: argparse.Namespace) -> int:
    cwd = Path(args.worktree).resolve() if args.worktree else REPO_ROOT
    assert_ownership(cwd, args.expect_branch)
    collection = collect(cwd, args.extra)
    partitions = partition(collection["nodes"], args.workers)
    print(
        json.dumps(
            {
                "count": collection["count"],
                "digest": collection["digest"],
                "duplicates": len(collection["duplicates"]),
                "malformed_count": collection["malformed_count"],
                "collection_errors": collection["collection_errors"][:5],
                "groups": len(collection["groups"]),
                "workers": args.workers,
                "partition_sizes": [part["intended_count"] for part in partitions],
            },
            indent=2,
        )
    )
    if args.out:
        write_json(
            Path(args.out),
            {"collection": collection, "partitions": partitions},
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--worktree", default=None)
        target.add_argument("--expect-branch", default=None)
        target.add_argument("--workers", type=int, default=1)
        target.add_argument("--extra", nargs=argparse.REMAINDER, default=[])

    collect_parser = sub.add_parser("collect", help="collect the canonical universe")
    common(collect_parser)
    collect_parser.add_argument("--out", default=None)
    collect_parser.set_defaults(func=cmd_collect)

    run_parser = sub.add_parser("run", help="execute the canonical universe")
    common(run_parser)
    run_parser.add_argument("--run-id", default=None)
    run_parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    run_parser.add_argument("--min-free-bytes", type=int, default=DEFAULT_MIN_FREE_BYTES)
    run_parser.add_argument(
        "--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES
    )
    run_parser.add_argument("--guard-prefixes", nargs="+", default=list(DEFAULT_GUARD_PREFIXES))
    run_parser.add_argument("--allow-dirty", action="store_true")
    run_parser.add_argument(
        "--expect-count",
        type=int,
        default=None,
        help="external universe anchor recorded into the bundle at run time",
    )
    run_parser.add_argument(
        "--expect-digest",
        default=None,
        help="external universe anchor recorded into the bundle at run time",
    )
    run_parser.set_defaults(func=run_canonical)

    verify_parser = sub.add_parser("verify", help="re-evaluate an evidence bundle")
    verify_parser.add_argument("evidence")
    verify_parser.add_argument(
        "--expect-count",
        type=int,
        default=None,
        help="external universe anchor: the collected node count to require",
    )
    verify_parser.add_argument(
        "--expect-digest",
        default=None,
        help="external universe anchor: the collection digest to require",
    )
    verify_parser.add_argument(
        "--require-anchor",
        action="store_true",
        help=(
            "refuse a self-consistent bundle that carries no external universe "
            "anchor"
        ),
    )
    verify_parser.set_defaults(func=cmd_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
