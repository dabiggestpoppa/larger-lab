"""Independent adversarial audit of the canonical evidence verifier (R3).

R2 closed four verifier weaknesses but disclosed five more evidence-accounting
gaps.  Each test below reproduces one of those gaps and asserts the outcome R3
must produce.  Run against the R2 runner they fail -- that is the point.

Run:

    python -m pytest \
        quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_r3_attacks.py -q

The tests are deliberately outside pytest's configured ``testpaths``: the tool
that measures the universe is not part of the universe.
"""

from __future__ import annotations

import json
import shutil
import sys
import xml.etree.ElementTree as ET
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


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _seed_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    (repo / "evidence").mkdir(parents=True)
    (repo / "evidence" / "artifact.json").write_text('{"value": 1}\n', encoding="utf-8")
    for name, body in files.items():
        (repo / name).write_text(body, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")
    return repo


def _run_one_file(repo: Path, name: str, timeout: int = 60) -> dict:
    part = {
        "index": 0,
        "files": [name],
        "intended_count": 1,
        "intended_nodes": [f"{name}::__unknown__"],
    }
    return runner.run_partition(
        repo,
        part,
        repo,
        timeout=timeout,
        min_free_bytes=0,
        max_artifact_bytes=10 * 1024 * 1024,
        baseline={},
    )


def _clone_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "canonical-p3-r1"
    target.mkdir(parents=True)
    shutil.copy2(BUNDLE_DIR / "evidence.json", target / "evidence.json")
    for junit in sorted(BUNDLE_DIR.glob("junit_*.xml")):
        shutil.copy2(junit, target / junit.name)
    return target


def _load(directory: Path) -> dict:
    return json.loads((directory / "evidence.json").read_text(encoding="utf-8"))


def _verdict(directory: Path, bundle: dict | None = None, **kwargs) -> dict:
    bundle = bundle if bundle is not None else _load(directory)
    return runner.evaluate_bundle(bundle, base_dir=directory, **kwargs)


def _assert_refused(verdict: dict, needle: str) -> None:
    assert verdict["disposition"] != runner.DISPOSITION_COMPLETE, verdict
    assert any(needle in reason for reason in verdict["reasons"]), verdict["reasons"]


# --------------------------------------------------------------------------- #
# R3-01  truncated stream must not be credited                                #
# --------------------------------------------------------------------------- #


def test_r3_01_self_truncating_test_does_not_get_a_pass(tmp_path: Path) -> None:
    """The test erases the stream mid-call; pytest then appends the pass.

    R2 credits the node: the file that survived is a *post-truncation* success,
    not evidence that the test ran to completion.  R3 must refuse it.
    """
    repo = _seed_repo(
        tmp_path,
        {
            "test_trunc.py": (
                "import os, pathlib\n"
                "def test_truncate():\n"
                "    pathlib.Path(os.environ['CANONICAL_RESULT_FILE']).write_text('')\n"
                "    assert True\n"
            )
        },
    )
    state = _run_one_file(repo, "test_trunc.py")
    errors = state.get("accounting_errors") or []
    assert errors, state
    assert any("stream" in error for error in errors), errors


# --------------------------------------------------------------------------- #
# R3-02  duplicate phase records must not collapse silently                   #
# --------------------------------------------------------------------------- #


def test_r3_02_duplicate_call_record_is_detected(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path,
        {
            "conftest.py": (
                "import json, os\n"
                "def pytest_runtest_logreport(report):\n"
                "    path = os.environ.get('CANONICAL_RESULT_FILE')\n"
                "    if path and report.when == 'call':\n"
                "        with open(path, 'a', encoding='utf-8') as handle:\n"
                "            handle.write(json.dumps({'nodeid': report.nodeid, "
                "'when': 'call', 'outcome': report.outcome}) + '\\n')\n"
            ),
            "test_dup.py": "def test_ok():\n    assert True\n",
        },
    )
    state = _run_one_file(repo, "test_dup.py")
    errors = state.get("accounting_errors") or []
    assert any("duplicate" in error for error in errors), errors


# --------------------------------------------------------------------------- #
# R3-03  self-consistent forgery must not claim independent verification      #
# --------------------------------------------------------------------------- #


def _rewrite_junit(directory: Path, part: dict) -> None:
    """Trim a JUnit artifact to the nodes the partition now claims to have run.

    A forgery that leaves the artifact alone is already caught by the R3 case
    identity binding.  To test the *anchor* instead, the forgery has to be
    internally consistent right through to the XML.
    """
    path = directory / f"junit_{part['index']}.xml"
    if not path.exists():
        return
    keep = {runner._junit_identity(node) for node in part["executed_nodes"]}
    tree = ET.parse(path)
    root = tree.getroot()
    for suite in root.iter("testsuite"):
        for case in list(suite.iter("testcase")):
            if (case.get("classname"), case.get("name")) not in keep:
                suite.remove(case)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    part["junit_sha256"] = runner._sha256_file(path)
    part["junit_bytes"] = path.stat().st_size
    part["junit_case_count"] = runner._junit_case_count(path)


def _drop_whole_file(directory: Path, bundle: dict) -> str:
    """Remove one test file entirely, keeping every remaining number consistent."""
    part = min(bundle["execution"]["partitions"], key=lambda p: len(p["files"]))
    victim_file = part["files"][0]
    victims = {
        node
        for node in bundle["collection"]["nodes"]
        if node.partition("::")[0] == victim_file
    }
    for side in ("collection", "execution"):
        bundle[side]["nodes"] = [
            node for node in bundle[side]["nodes"] if node not in victims
        ]
    bundle["collection"]["count"] = len(bundle["collection"]["nodes"])
    bundle["collection"]["digest"] = runner._digest_node_ids(bundle["collection"]["nodes"])
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    bundle["execution"]["digest"] = runner._digest_node_ids(bundle["execution"]["nodes"])
    for part in bundle["execution"]["partitions"]:
        if victim_file in part["files"]:
            part["files"] = [f for f in part["files"] if f != victim_file]
            part["outcomes"] = {
                node: value
                for node, value in part["outcomes"].items()
                if node not in victims
            }
            part["executed_nodes"] = [
                node for node in part["executed_nodes"] if node not in victims
            ]
            part["counts"] = runner._recompute_counts(part["outcomes"])
            _rewrite_junit(directory, part)
    union = {
        node: outcome
        for part in bundle["execution"]["partitions"]
        for node, outcome in part["outcomes"].items()
    }
    bundle["execution"]["counts"] = runner._recompute_counts(union)
    return victim_file


def test_r3_03_self_consistent_forgery_is_not_anchored_complete(
    tmp_path: Path,
) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    dropped = _drop_whole_file(directory, bundle)
    verdict = _verdict(directory, bundle)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE, (
        f"forgery dropped {dropped} and R2 still says {verdict['disposition']}"
    )
    assert verdict["assurance"] == "SELF_CONSISTENT_COMPLETE", verdict


def test_r3_04_self_consistent_forgery_is_refused_when_anchor_required(
    tmp_path: Path,
) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    _drop_whole_file(directory, bundle)
    verdict = _verdict(directory, bundle, require_anchor=True)
    _assert_refused(verdict, "anchor")


# --------------------------------------------------------------------------- #
# R3-05  JUnit with the right count and the wrong identities                  #
# --------------------------------------------------------------------------- #


def test_r3_05_junit_identity_mismatch_is_refused(tmp_path: Path) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    path = directory / "junit_0.xml"
    tree = ET.parse(path)
    for index, case in enumerate(tree.getroot().iter("testcase")):
        case.set("name", f"wrong_name_{index}")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    part = bundle["execution"]["partitions"][0]
    part["junit_sha256"] = runner._sha256_file(path)
    part["junit_bytes"] = path.stat().st_size
    _assert_refused(_verdict(directory, bundle), "junit")


# --------------------------------------------------------------------------- #
# R3-06  untracked files under guarded prefixes                               #
# --------------------------------------------------------------------------- #


def test_r3_06_untracked_evidence_file_is_detected(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, {"test_ok.py": "def test_ok():\n    assert True\n"})
    prefixes = ["evidence"]
    before = runner.snapshot_guarded(repo, prefixes)
    assert before, "guard baseline should cover the tracked artifact"
    (repo / "evidence" / "surprise.json").write_text("{}\n", encoding="utf-8")
    added = runner.detect_new_untracked(repo, prefixes, tracked_before=before)
    assert added == ["evidence/surprise.json"], added


# --------------------------------------------------------------------------- #
# Positive controls                                                           #
# --------------------------------------------------------------------------- #


def test_r3_07_real_bundle_is_complete_but_unanchored() -> None:
    verdict = runner.evaluate_bundle(_load(BUNDLE_DIR), base_dir=BUNDLE_DIR)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE, verdict["reasons"]
    assert verdict["assurance"] == "SELF_CONSISTENT_COMPLETE", verdict
    assert verdict["counts"] == {
        "passed": 4708,
        "failed": 0,
        "errored": 0,
        "skipped": 11,
    }


def test_r3_08_real_bundle_is_anchored_when_the_anchor_is_supplied() -> None:
    bundle = _load(BUNDLE_DIR)
    verdict = runner.evaluate_bundle(
        bundle,
        base_dir=BUNDLE_DIR,
        expected_count=bundle["collection"]["count"],
        expected_digest=bundle["collection"]["digest"],
    )
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE, verdict["reasons"]
    assert verdict["assurance"] == "ANCHORED_COMPLETE", verdict


def test_r3_09_phase_semantics_survive_for_the_real_bundle() -> None:
    """Setup/call/teardown stay distinguishable: the 11 skips are not errors."""
    verdict = runner.evaluate_bundle(_load(BUNDLE_DIR), base_dir=BUNDLE_DIR)
    assert verdict["counts"]["skipped"] == 11
    assert verdict["counts"]["errored"] == 0
    assert verdict["counts"]["failed"] == 0
