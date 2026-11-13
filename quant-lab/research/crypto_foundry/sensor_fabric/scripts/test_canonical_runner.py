"""Attack the canonical runner: every infrastructure failure must be loud.

Each scenario below is a way a regression run has actually lied in this
repository's history, or could.  The assertion is always the same shape: the
verdict must NOT be COMPLETE, and it must name the reason.  A runner that can be
talked into COMPLETE by a timeout, a crash or a missing partition is worse than
no runner, because it converts uncertainty into a green number.

These tests live beside the runner (outside pytest's configured ``testpaths``)
so the canonical universe is not polluted by the tool that measures it.  Run
them explicitly:

    python -m pytest quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner.py -q
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import canonical_runner as runner  # noqa: E402


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _clean_bundle() -> dict:
    nodes = ["a.py::test_one", "a.py::test_two"]
    part = {
        "index": 0,
        "files": ["a.py"],
        "intended_count": 2,
        "status": "ok",
        "timed_out": False,
        "infrastructure_error": None,
        "exit_code": 0,
        "executed_nodes": nodes,
        "outcomes": {node: "passed" for node in nodes},
        "counts": {"passed": 2, "failed": 0, "errored": 0, "skipped": 0},
    }
    return {
        "run_id": "synthetic",
        "interrupted": False,
        "collection": {
            "nodes": nodes,
            "count": 2,
            "digest": runner._digest_node_ids(nodes),
            "duplicates": [],
            "malformed_count": 0,
            "collection_errors": [],
        },
        "execution": {
            "nodes": nodes,
            "duplicate_executions": [],
            "counts": {"passed": 2, "failed": 0, "errored": 0, "skipped": 0},
            "partitions": [part],
            "unimplemented_partitions": [],
        },
        "restoration": {"attempted": False, "verified": True, "paths": [], "failed": []},
        "tree": {"clean_after": True, "dirty_paths": []},
    }


def _write_test_file(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def _run_partition_on(directory: Path, timeout: int = 60) -> dict:
    nodes, _ = runner.parse_node_ids(
        f"{[p.name for p in directory.glob('test_*.py')][0]}::__collected__"
    )
    part = {
        "index": 0,
        "files": sorted(p.name for p in directory.glob("test_*.py")),
        "intended_count": len(nodes),
        "intended_nodes": nodes,
    }
    return runner.run_partition(
        directory,
        part,
        directory,
        timeout=timeout,
        min_free_bytes=0,
        max_artifact_bytes=10 * 1024 * 1024,
        baseline={},
    )


# --------------------------------------------------------------------------- #
# 0. Positive control — the runner can in fact say COMPLETE                    #
# --------------------------------------------------------------------------- #


def test_clean_run_is_complete() -> None:
    verdict = runner.evaluate_bundle(_clean_bundle())
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE
    assert verdict["test_outcome"] == "GREEN"
    assert verdict["reasons"] == []


# --------------------------------------------------------------------------- #
# 1. Missing partition                                                        #
# --------------------------------------------------------------------------- #


def test_missing_partition_is_not_complete() -> None:
    bundle = _clean_bundle()
    bundle["execution"]["partitions"].append(
        {
            "index": 1,
            "files": ["b.py"],
            "intended_count": 3,
            "status": "pending",
            "timed_out": False,
            "infrastructure_error": None,
            "exit_code": None,
            "executed_nodes": [],
            "counts": {"passed": 0, "failed": 0, "errored": 0, "skipped": 0},
        }
    )
    bundle["execution"]["unimplemented_partitions"] = [1]
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] != runner.DISPOSITION_COMPLETE
    assert any("unimplemented" in reason for reason in verdict["reasons"])


# --------------------------------------------------------------------------- #
# 2. Duplicate node                                                           #
# --------------------------------------------------------------------------- #


def test_duplicate_node_is_not_complete() -> None:
    bundle = _clean_bundle()
    bundle["collection"]["duplicates"] = ["a.py::test_one"]
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert any("duplicate_collected" in reason for reason in verdict["reasons"])


def test_duplicate_execution_is_not_complete() -> None:
    bundle = _clean_bundle()
    bundle["execution"]["duplicate_executions"] = ["a.py::test_one"]
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] != runner.DISPOSITION_COMPLETE
    assert any("duplicate_executions" in reason for reason in verdict["reasons"])


# --------------------------------------------------------------------------- #
# 3. Unexpected extra test                                                    #
# --------------------------------------------------------------------------- #


def test_extra_executed_node_is_not_complete() -> None:
    bundle = _clean_bundle()
    bundle["execution"]["nodes"] = bundle["execution"]["nodes"] + ["ghost.py::test_new"]
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["extra_count"] == 1


# --------------------------------------------------------------------------- #
# 4. Early process crash                                                      #
# --------------------------------------------------------------------------- #


def test_collection_crash_is_infrastructure_not_failure(tmp_path: Path) -> None:
    _write_test_file(tmp_path, "test_broken.py", "def test_ok(:\n    pass\n")
    state = _run_partition_on(tmp_path)
    assert state["status"] in ("infrastructure_error", "timeout")
    assert state["infrastructure_error"] is not None


# --------------------------------------------------------------------------- #
# 5. Timeout                                                                  #
# --------------------------------------------------------------------------- #


def test_timeout_is_distinguished_from_failure(tmp_path: Path) -> None:
    _write_test_file(
        tmp_path,
        "test_slow.py",
        "import time\n\n\ndef test_slow():\n    time.sleep(10)\n",
    )
    state = _run_partition_on(tmp_path, timeout=2)
    assert state["timed_out"] is True
    assert state["status"] == "timeout"
    assert "exceeded" in (state["infrastructure_error"] or "")


# --------------------------------------------------------------------------- #
# 6. Missing JUnit artifact                                                   #
# --------------------------------------------------------------------------- #


def test_missing_junit_is_infrastructure(tmp_path: Path, monkeypatch) -> None:
    _write_test_file(tmp_path, "test_ok.py", "def test_ok():\n    assert True\n")

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(*args, **kwargs):  # noqa: ANN001
        return _Proc()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    state = _run_partition_on(tmp_path)
    assert state["status"] == "infrastructure_error"
    assert "result stream" in (state["infrastructure_error"] or "") or (
        "JUnit" in (state["infrastructure_error"] or "")
    )


# --------------------------------------------------------------------------- #
# 7. Corrupt result artifact                                                  #
# --------------------------------------------------------------------------- #


def test_corrupt_evidence_bundle_is_not_complete(tmp_path: Path) -> None:
    bad = tmp_path / "evidence.json"
    bad.write_text("{not json", encoding="utf-8")
    exit_code = runner.main(["verify", str(bad)])
    assert exit_code != 0


def test_corrupt_result_stream_is_flagged(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    results.write_text("this is not json\n", encoding="utf-8")
    records = runner._read_results(results)
    assert records and records[0]["outcome"] == "error"
    assert records[0]["when"] == "corrupt"


# --------------------------------------------------------------------------- #
# 8. Disk exhaustion                                                          #
# --------------------------------------------------------------------------- #


def test_low_free_space_refuses_to_start(tmp_path: Path) -> None:
    # --allow-dirty so the free-space gate is what refuses, not the clean-tree
    # gate that legitimately runs first.
    exit_code = runner.main(
        [
            "run",
            "--min-free-bytes",
            str(10**15),
            "--allow-dirty",
        ]
    )
    assert exit_code == 4


def test_partition_with_insufficient_free_space_is_infrastructure(tmp_path: Path) -> None:
    _write_test_file(tmp_path, "test_ok.py", "def test_ok():\n    assert True\n")
    part = {"index": 0, "files": ["test_ok.py"], "intended_count": 1, "intended_nodes": []}
    state = runner.run_partition(
        tmp_path,
        part,
        tmp_path,
        timeout=60,
        min_free_bytes=10**15,
        max_artifact_bytes=1024,
        baseline={},
    )
    assert state["status"] == "infrastructure_error"
    assert "free space" in (state["infrastructure_error"] or "")


# --------------------------------------------------------------------------- #
# 9. Evidence mutation by a non-hermetic test                                 #
# --------------------------------------------------------------------------- #


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "evidence").mkdir(parents=True)
    (repo / "evidence" / "artifact.json").write_text('{"value": 1}\n', encoding="utf-8")
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed"],
    ):
        subprocess.run(command, cwd=repo, check=True, capture_output=True)
    return repo


def test_evidence_mutation_is_detected_and_restored(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    assert baseline == {"evidence/artifact.json": runner._sha256_file(repo / "evidence/artifact.json")}

    (repo / "evidence" / "artifact.json").write_text('{"value": 999}\n', encoding="utf-8")
    modified = runner.detect_modifications(repo, baseline)
    assert modified == ["evidence/artifact.json"]

    restoration = runner.restore_and_verify(repo, modified, baseline)
    assert restoration["verified"] is True
    assert runner.detect_modifications(repo, baseline) == []


def test_unrestorable_mutation_fails_verification(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    missing = repo / "evidence" / "artifact.json"
    missing.unlink()
    restoration = runner.restore_and_verify(repo, [], baseline)
    assert restoration["verified"] is True  # nothing attempted

    bundle = _clean_bundle()
    bundle["restoration"] = {"attempted": True, "verified": False, "paths": ["x"], "failed": ["x"]}
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INFRA
    assert "evidence_restoration_unverified" in verdict["reasons"]


# --------------------------------------------------------------------------- #
# 10. Interrupted execution                                                   #
# --------------------------------------------------------------------------- #


def test_interrupted_run_is_not_complete() -> None:
    bundle = _clean_bundle()
    bundle["interrupted"] = True
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INTERRUPTED
    assert "interrupted" in verdict["reasons"]


# --------------------------------------------------------------------------- #
# 11. Incomplete checkout                                                     #
# --------------------------------------------------------------------------- #


def test_incomplete_checkout_is_dirty(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    state = runner.tree_state(repo, ignore_prefixes=())
    assert state["clean_before"] is True

    (repo / "evidence" / "artifact.json").unlink()
    state = runner.tree_state(repo, ignore_prefixes=())
    assert state["clean_before"] is False
    assert any("artifact.json" in line for line in state["dirty_paths"])


def test_dirty_worktree_prevents_acceptance() -> None:
    bundle = _clean_bundle()
    bundle["tree"] = {"clean_after": False, "dirty_paths": [" D evidence/x.json"]}
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INFRA
    assert "worktree_not_clean_after_run" in verdict["reasons"]


# --------------------------------------------------------------------------- #
# Parser and partitioning invariants                                          #
# --------------------------------------------------------------------------- #


def test_parser_keeps_malformed_lines_visible() -> None:
    text = "\n".join(
        [
            "quant-lab/tests/test_a.py::test_one",
            "quant-lab/tests/test_a.py::TestCls::test_two[param]",
            "9 tests collected in 0.12s",
            "some weird :: line",
        ]
    )
    nodes, malformed = runner.parse_node_ids(text)
    assert "quant-lab/tests/test_a.py::test_one" in nodes
    assert "quant-lab/tests/test_a.py::TestCls::test_two[param]" in nodes
    assert malformed == ["some weird :: line"]


def test_partitions_are_disjoint_and_cover_every_node() -> None:
    nodes = [f"f{index}.py::test_{index}" for index in range(20)]
    parts = runner.partition(nodes, 4)
    seen: list[str] = []
    for part in parts:
        seen.extend(part["intended_nodes"])
    assert sorted(seen) == sorted(nodes)
    assert len(seen) == len(set(seen))
    assert [part["intended_count"] for part in parts] == [5, 5, 5, 5]


def test_partitioning_is_deterministic() -> None:
    nodes = [f"f{index}.py::test_{index}" for index in range(17)]
    first = runner.partition(nodes, 3)
    second = runner.partition(nodes, 3)
    assert first == second


def test_counts_are_not_mistaken_for_coverage() -> None:
    """A green run that dropped nodes must still be non-COMPLETE."""
    bundle = _clean_bundle()
    bundle["collection"]["nodes"] = bundle["collection"]["nodes"] + ["b.py::test_three"]
    bundle["collection"]["count"] = 3
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["test_outcome"] == "GREEN"
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["missing_count"] == 1


# --------------------------------------------------------------------------- #
# Command surface                                                             #
# --------------------------------------------------------------------------- #


def test_verify_accepts_a_clean_bundle(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(_clean_bundle()), encoding="utf-8")
    assert runner.main(["verify", str(path)]) == 0


def test_verify_of_missing_bundle_fails(tmp_path: Path) -> None:
    assert runner.main(["verify", str(tmp_path / "absent.json")]) != 0


def test_collect_reports_the_measured_universe() -> None:
    exit_code = runner.main(["collect", "--workers", "2"])
    assert exit_code == 0
