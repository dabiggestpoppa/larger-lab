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
DEFAULT_GUARD_PREFIXES: tuple[str, ...] = ("quant-lab/research",)
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


def snapshot_guarded(cwd: Path, prefixes: Sequence[str]) -> dict[str, str]:
    tracked = [
        path
        for path in _git(cwd, "ls-files", "-z", "--", *prefixes).split("\0")
        if path.strip()
    ]
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


def _outcome_for(records: Sequence[dict[str, Any]]) -> tuple[str, int]:
    """Collapse per-phase reports into one outcome, pytest-style."""
    failed = error = skipped = 0
    for record in records:
        when = record.get("when")
        outcome = record.get("outcome")
        if outcome == "failed":
            if when in ("setup", "collect"):
                error += 1
            else:
                failed += 1
        elif outcome == "error":
            error += 1
        elif outcome == "skipped":
            skipped += 1
    if error:
        return "error", skipped
    if failed:
        return "failed", skipped
    if skipped and not failed and not error:
        return "skipped", skipped
    return "passed", skipped


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

    records = _read_results(results_path)
    per_node: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        nodeid = record.get("nodeid")
        if not nodeid:
            continue
        per_node.setdefault(nodeid, []).append(record)

    state["executed_nodes"] = sorted(per_node)
    state["outcomes"] = {
        node: _outcome_for(reports)[0] for node, reports in sorted(per_node.items())
    }
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


def evaluate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Pure verdict function: the only place COMPLETE can be produced."""
    reasons: list[str] = []

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
        )
    ):
        disposition = DISPOSITION_INFRA
    elif duplicates or duplicate_executions or missing or extra:
        disposition = DISPOSITION_COVERAGE
    else:
        disposition = DISPOSITION_COMPLETE

    return {
        "disposition": disposition,
        "test_outcome": test_outcome,
        "reasons": reasons,
        "missing_nodes": missing[:100],
        "missing_count": len(missing),
        "extra_nodes": extra[:100],
        "extra_count": len(extra),
        "counts": counts,
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
        "restoration": {"verified": True, "paths": [], "attempted": False},
        "tree": {"clean_after": True, "dirty_paths": []},
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
    bundle["tree"] = {"clean_after": after["clean_before"], "dirty_paths": after["dirty_paths"]}
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
    verdict = evaluate_bundle(bundle)
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
    run_parser.set_defaults(func=run_canonical)

    verify_parser = sub.add_parser("verify", help="re-evaluate an evidence bundle")
    verify_parser.add_argument("evidence")
    verify_parser.set_defaults(func=cmd_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
