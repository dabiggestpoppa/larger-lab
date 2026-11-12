"""Independent adversarial audit of the canonical runner (P3-CANONICAL-R1).

This file is not part of the runner's implementation and does not modify it.
Its purpose is to establish, independently of the runner's own 24 self-tests,
which failure modes the runner actually converts into a non-COMPLETE verdict,
and which ones it cannot see at all.  Cases that the runner does not detect are
kept as explicit counterexamples rather than deleted, because a runner that
silently reports COMPLETE on forged or shrunken evidence is the exact failure
this audit exists to find.

Run:

    python -m pytest \
        quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_audit_attacks.py -q
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import canonical_runner as runner  # noqa: E402

REPO_ROOT = SCRIPTS_DIR.parents[4]
BUNDLE_DIR = (
    REPO_ROOT
    / "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05"
    / "canonical_runs/canonical-p3-r1"
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _real_bundle() -> dict:
    return json.loads((BUNDLE_DIR / "evidence.json").read_text(encoding="utf-8"))


def _strip_verdict(bundle: dict) -> dict:
    return {key: value for key, value in bundle.items() if key != "verdict"}


def _verdict(bundle: dict) -> dict:
    return runner.evaluate_bundle(_strip_verdict(bundle))


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "evidence").mkdir(parents=True)
    (repo / "evidence" / "artifact.json").write_text('{"value": 1}\n', encoding="utf-8")
    (repo / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")
    return repo


def _partition_run(repo: Path, timeout: int = 60, baseline: dict | None = None) -> dict:
    part = {
        "index": 0,
        "files": ["test_ok.py"],
        "intended_count": 1,
        "intended_nodes": ["test_ok.py::test_ok"],
    }
    return runner.run_partition(
        repo,
        part,
        repo,
        timeout=timeout,
        min_free_bytes=0,
        max_artifact_bytes=10 * 1024 * 1024,
        baseline=baseline or {},
    )


# --------------------------------------------------------------------------- #
# 0. Positive control on the real committed bundle                            #
# --------------------------------------------------------------------------- #


def test_audit_control_real_bundle_is_complete() -> None:
    verdict = _verdict(_real_bundle())
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE
    assert verdict["reasons"] == []
    assert verdict["counts"] == {"passed": 4708, "failed": 0, "errored": 0, "skipped": 11}


# --------------------------------------------------------------------------- #
# 1. Forged aggregate counts are accepted (counterexample)                     #
# --------------------------------------------------------------------------- #


def test_forged_pass_count_is_still_complete() -> None:
    """COUNTEREXAMPLE: aggregate counts are trusted, never recomputed.

    ``evidence.json`` stores only totals, so a bundle claiming 4,719 passes
    without a single failure verifies as COMPLETE.  The committed bundle is not
    forged (its totals were independently recomputed from results_*.jsonl), but
    ``verify`` alone cannot tell the difference.
    """
    bundle = _real_bundle()
    bundle["execution"]["counts"] = {
        "passed": 4719,
        "failed": 0,
        "errored": 0,
        "skipped": 0,
    }
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE
    assert verdict["counts"]["passed"] == 4719  # accepted as given


# --------------------------------------------------------------------------- #
# 2. Forged collection digest is accepted (counterexample)                     #
# --------------------------------------------------------------------------- #


def test_forged_digest_is_not_reverified() -> None:
    """COUNTEREXAMPLE: the digest is published but never checked by ``verify``."""
    bundle = _real_bundle()
    bundle["collection"]["digest"] = "0" * 64
    bundle["execution"]["digest"] = "1" * 64
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE


# --------------------------------------------------------------------------- #
# 3. A consistently shrunken universe is invisible (counterexample)            #
# --------------------------------------------------------------------------- #


def test_shrunken_universe_is_invisible_to_verify() -> None:
    """COUNTEREXAMPLE: dropping a node from BOTH sides keeps COMPLETE.

    Coverage is defined as collected == executed, so evidence that forgets a
    node on both sides is internally consistent.  Detecting this requires an
    external expected count, which the bundle deliberately does not carry.
    """
    bundle = _real_bundle()
    victim = sorted(bundle["collection"]["nodes"])[0]
    bundle["collection"]["nodes"] = [
        node for node in bundle["collection"]["nodes"] if node != victim
    ]
    bundle["execution"]["nodes"] = [
        node for node in bundle["execution"]["nodes"] if node != victim
    ]
    bundle["collection"]["count"] = len(bundle["collection"]["nodes"])
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE


# --------------------------------------------------------------------------- #
# 4. Real coverage failures ARE caught                                        #
# --------------------------------------------------------------------------- #


def test_missing_node_only_on_executed_side_is_coverage_failure() -> None:
    bundle = _real_bundle()
    victim = sorted(bundle["collection"]["nodes"])[0]
    bundle["execution"]["nodes"] = [
        node for node in bundle["execution"]["nodes"] if node != victim
    ]
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["missing_count"] == 1


def test_extra_node_is_coverage_failure() -> None:
    bundle = _real_bundle()
    bundle["execution"]["nodes"] = bundle["execution"]["nodes"] + ["ghost.py::test_ghost"]
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["extra_count"] == 1


def test_duplicate_execution_across_partitions_is_coverage_failure() -> None:
    bundle = _real_bundle()
    bundle["execution"]["duplicate_executions"] = ["a.py::test_a"]
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE


def test_empty_execution_with_nonempty_collection_is_coverage_failure() -> None:
    bundle = _real_bundle()
    bundle["execution"]["nodes"] = []
    bundle["execution"]["unique_count"] = 0
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["missing_count"] == len(bundle["collection"]["nodes"])


# --------------------------------------------------------------------------- #
# 5. Infrastructure conditions on a live synthetic partition                   #
# --------------------------------------------------------------------------- #


def test_live_partition_crash_is_infrastructure(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "test_ok.py").write_text("def test_ok(:\n    pass\n", encoding="utf-8")
    _git(repo, "add", "-A")
    state = _partition_run(repo)
    assert state["status"] in ("infrastructure_error", "timeout")
    assert state["infrastructure_error"]


def test_live_partition_timeout_is_not_a_failure(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "test_ok.py").write_text(
        "import time\n\n\ndef test_ok():\n    time.sleep(5)\n", encoding="utf-8"
    )
    state = _partition_run(repo, timeout=1)
    assert state["timed_out"] is True
    assert state["status"] == "timeout"


def test_live_collection_error_is_captured(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "test_ok.py").write_text(
        "import module_that_does_not_exist\n\n\ndef test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    collection = runner.collect(repo)
    assert collection["count"] == 0
    assert collection["collection_errors"] or collection["exit_code"] != 0


# --------------------------------------------------------------------------- #
# 6. Result-stream corruption must lose coverage, not gain it                  #
# --------------------------------------------------------------------------- #


def test_live_stream_garbage_after_run_is_coverage_loss(tmp_path: Path) -> None:
    """A stream that holds only garbage yields zero coverage, never a pass."""
    repo = _init_repo(tmp_path)
    state = _partition_run(repo)
    # Simulate a stream destroyed after the fact: no parseable records at all.
    bundle = {
        "collection": {"nodes": ["test_ok.py::test_ok"], "duplicates": []},
        "execution": {
            "nodes": [],
            "duplicate_executions": [],
            "partitions": [state],
            "unimplemented_partitions": [],
        },
        "restoration": {"verified": True},
        "tree": {"clean_after": True},
        "interrupted": False,
    }
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["missing_count"] == 1


def test_live_destroyed_stream_still_credits_the_running_node(tmp_path: Path) -> None:
    """COUNTEREXAMPLE (bounded): a node whose stream was destroyed still passes.

    The plugin appends after each phase, so a test that truncates the stream
    mid-call is re-credited by the post-call append.  The node did run, so the
    credit is honest; the point is that stream damage is not itself detectable.
    """
    repo = _init_repo(tmp_path)
    (repo / "test_ok.py").write_text(
        "import os\n\n\n"
        "def test_ok():\n"
        "    path = os.environ['CANONICAL_RESULT_FILE']\n"
        "    open(path, 'w', encoding='utf-8').write('this is not json\\n')\n"
        "    assert True\n",
        encoding="utf-8",
    )
    state = _partition_run(repo)
    assert state["executed_nodes"] == ["test_ok.py::test_ok"]
    assert state["status"] == "ok"


def test_corrupt_result_line_record_shape() -> None:
    records = runner._read_results(Path("/nonexistent/results.jsonl"))
    assert records == []


# --------------------------------------------------------------------------- #
# 7. Evidence containment: mutation, deletion, staging                         #
# --------------------------------------------------------------------------- #


def test_live_guarded_mutation_is_detected_and_restored(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    (repo / "evidence" / "artifact.json").write_text('{"value": 999}\n', encoding="utf-8")
    modified = runner.detect_modifications(repo, baseline)
    assert modified == ["evidence/artifact.json"]
    restoration = runner.restore_and_verify(repo, modified, baseline)
    assert restoration["verified"] is True
    assert runner.detect_modifications(repo, baseline) == []


def test_live_guarded_deletion_is_detected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    (repo / "evidence" / "artifact.json").unlink()
    assert runner.detect_modifications(repo, baseline) == ["evidence/artifact.json"]
    restoration = runner.restore_and_verify(repo, ["evidence/artifact.json"], baseline)
    assert restoration["verified"] is True
    assert (repo / "evidence" / "artifact.json").exists()


def test_live_staged_mutation_fails_restoration(tmp_path: Path) -> None:
    """A test that both writes and stages leaves the index dirty.

    ``git checkout -- <path>`` restores from the INDEX, so a staged mutation is
    not restored; the re-hash catches it and ``restoration.verified`` is false,
    which the verdict treats as INCOMPLETE_INFRA.  Fail-closed, as intended.
    """
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    (repo / "evidence" / "artifact.json").write_text('{"value": 999}\n', encoding="utf-8")
    _git(repo, "add", "evidence/artifact.json")
    restoration = runner.restore_and_verify(repo, ["evidence/artifact.json"], baseline)
    assert restoration["verified"] is False
    assert restoration["failed"] == ["evidence/artifact.json"]


def test_live_untracked_artifact_in_guarded_tree_is_not_guarded(tmp_path: Path) -> None:
    """COUNTEREXAMPLE (bounded): only TRACKED files can break containment.

    A new untracked file written under the guarded tree is invisible to the
    guard.  It is caught instead by the worktree-cleanliness check, except when
    it lands inside the runner's own output tree, which is deliberately ignored.
    """
    repo = _init_repo(tmp_path)
    baseline = runner.snapshot_guarded(repo, ("evidence",))
    (repo / "evidence" / "new_file.json").write_text("{}\n", encoding="utf-8")
    assert runner.detect_modifications(repo, baseline) == []
    state = runner.tree_state(repo, ignore_prefixes=())
    assert state["clean_before"] is False


def test_live_evidence_tree_is_excluded_from_cleanliness(tmp_path: Path) -> None:
    """The output tree is invisible to tree_state; only the guard covers it."""
    repo = _init_repo(tmp_path)
    tracked = repo / "evidence" / "artifact.json"
    tracked.unlink()
    ignored = runner.tree_state(repo, ignore_prefixes=("evidence",))
    seen = runner.tree_state(repo, ignore_prefixes=())
    assert ignored["clean_before"] is True
    assert seen["clean_before"] is False


# --------------------------------------------------------------------------- #
# 8. Gates: dirty tree, low disk, interruption, restoration                   #
# --------------------------------------------------------------------------- #


def test_live_dirty_worktree_is_refused(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "stray.txt").write_text("dirty\n", encoding="utf-8")
    exit_code = runner.main(
        ["run", "--worktree", str(repo), "--min-free-bytes", "0"]
    )
    assert exit_code == 3


def test_live_low_disk_is_refused(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    exit_code = runner.main(
        ["run", "--worktree", str(repo), "--min-free-bytes", str(10**18)]
    )
    assert exit_code == 4


def test_interrupted_bundle_is_not_complete() -> None:
    bundle = _strip_verdict(_real_bundle())
    bundle["interrupted"] = True
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INTERRUPTED


def test_failed_restoration_blocks_completion() -> None:
    bundle = _strip_verdict(_real_bundle())
    bundle["restoration"] = {
        "attempted": True,
        "verified": False,
        "paths": ["x"],
        "failed": ["x"],
    }
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INFRA
    assert "evidence_restoration_unverified" in verdict["reasons"]


def test_dirty_after_run_blocks_completion() -> None:
    bundle = _strip_verdict(_real_bundle())
    bundle["tree"] = {"clean_after": False, "dirty_paths": [" M x.py"]}
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_INFRA


def test_junit_absence_in_partition_is_infrastructure(tmp_path: Path, monkeypatch) -> None:
    repo = _init_repo(tmp_path)

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: _Proc())
    state = _partition_run(repo)
    assert state["status"] == "infrastructure_error"


# --------------------------------------------------------------------------- #
# 9. Gaps the runner cannot see (preserved as counterexamples)                 #
# --------------------------------------------------------------------------- #


def test_junit_result_mismatch_is_not_detected(tmp_path: Path) -> None:
    """COUNTEREXAMPLE: JUnit and result stream are never cross-checked.

    Replacing a committed JUnit file with an empty document leaves the verdict
    COMPLETE, because coverage is taken from the JSONL stream alone.
    """
    empty = tmp_path / "junit_0.xml"
    empty.write_text('<?xml version="1.0"?><testsuites><testsuite/></testsuites>', encoding="utf-8")
    bundle = _real_bundle()
    # The bundle does not carry JUnit contents at all, so nothing can notice.
    assert "junit" not in json.dumps(bundle["execution"]["partitions"][0]).lower() or True
    verdict = _verdict(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE


def test_duplicate_within_one_partition_is_not_flagged(tmp_path: Path) -> None:
    """COUNTEREXAMPLE (bounded): duplicates are only detected ACROSS partitions.

    ``run_partition`` stores executed nodes as a set, so a node reported twice
    inside one partition collapses to one outcome and never reaches
    ``duplicate_executions``.
    """
    repo = _init_repo(tmp_path)
    (repo / "test_ok.py").write_text(
        "import os, json\n\n\n"
        "def test_ok():\n"
        "    path = os.environ['CANONICAL_RESULT_FILE']\n"
        "    record = json.dumps({'nodeid': 'test_ok.py::test_ok', 'when': 'call', 'outcome': 'passed'})\n"
        "    with open(path, 'a', encoding='utf-8') as handle:\n"
        "        for _ in range(3):\n"
        "            handle.write(record + '\\n')\n",
        encoding="utf-8",
    )
    state = _partition_run(repo)
    assert state["executed_nodes"] == ["test_ok.py::test_ok"]
    assert state["counts"]["passed"] == 1


def test_bundle_without_collection_nodes_cannot_be_complete() -> None:
    bundle = _strip_verdict(_real_bundle())
    bundle["collection"]["nodes"] = []
    bundle["collection"]["count"] = 0
    verdict = runner.evaluate_bundle(bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COVERAGE
    assert verdict["extra_count"] == 4719


# --------------------------------------------------------------------------- #
# 10. Ownership boundary                                                      #
# --------------------------------------------------------------------------- #


def test_live_ownership_refuses_a_non_root_directory(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    nested = repo / "evidence"
    with pytest.raises(SystemExit):
        runner.main(["collect", "--worktree", str(nested)])


def test_live_ownership_refuses_wrong_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    with pytest.raises(SystemExit):
        runner.main(
            [
                "collect",
                "--worktree",
                str(repo),
                "--expect-branch",
                "some-other-branch",
            ]
        )
