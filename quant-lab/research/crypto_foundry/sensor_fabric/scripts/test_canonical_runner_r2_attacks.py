"""Independent adversarial audit of the canonical verifier (P3-CANONICAL-R2).

R1's audit reproduced four verifier weaknesses and preserved them as
counterexamples: forged aggregate counts, forged digests, a consistently
shrunken universe, and JUnit that disagrees with the result stream all still
verified `COMPLETE`.  This suite is the R2 counterpart.  It performs the same
four forgeries and asserts the opposite outcome -- the verdict must not be
`COMPLETE`, and it must name the reason.

These tests are deliberately independent of the runner's own self-tests and of
the R1 audit suite.  They attack the *verifier*, not the execution path, and
they never modify the historical bundle: every mutation is applied to a
throwaway copy under `tmp_path`.

Run:

    python -m pytest \
        quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_r2_attacks.py -q
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

# The four R1 counterexamples, plus every adjacent forgery the repair must also
# refuse.  Each entry is (name, reasons_substring) and is used only for naming.
EXPECTED_REASONS = {
    "counts": "counts",
    "digest": "digest",
    "coverage": "coverage",
    "junit": "junit",
}


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _clone_bundle(tmp_path: Path) -> Path:
    """Copy the real bundle's evidence and JUnit files into a scratch directory."""
    target = tmp_path / "canonical-p3-r1"
    target.mkdir(parents=True)
    shutil.copy2(BUNDLE_DIR / "evidence.json", target / "evidence.json")
    for junit in sorted(BUNDLE_DIR.glob("junit_*.xml")):
        shutil.copy2(junit, target / junit.name)
    return target


def _load(directory: Path) -> dict:
    return json.loads((directory / "evidence.json").read_text(encoding="utf-8"))


def _save(directory: Path, bundle: dict) -> None:
    (directory / "evidence.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )


def _verdict(directory: Path, bundle: dict | None = None) -> dict:
    bundle = bundle if bundle is not None else _load(directory)
    return runner.evaluate_bundle(bundle, base_dir=directory)


def _assert_refused(verdict: dict, needle: str) -> None:
    assert verdict["disposition"] != runner.DISPOSITION_COMPLETE, verdict
    assert any(needle in reason for reason in verdict["reasons"]), verdict["reasons"]


# --------------------------------------------------------------------------- #
# 0. Positive control -- the committed bundle must still verify                #
# --------------------------------------------------------------------------- #


def test_r2_00_real_bundle_still_verifies_complete() -> None:
    verdict = _verdict(BUNDLE_DIR)
    assert verdict["disposition"] == runner.DISPOSITION_COMPLETE, verdict["reasons"]
    assert verdict["reasons"] == []
    assert verdict["counts"] == {
        "passed": 4708,
        "failed": 0,
        "errored": 0,
        "skipped": 11,
    }


# --------------------------------------------------------------------------- #
# V01 -- forged aggregate counts                                              #
# --------------------------------------------------------------------------- #


def test_r2_01_forged_total_pass_count_is_refused(tmp_path: Path) -> None:
    """R1 case 27: `counts.passed = 4719` verified COMPLETE."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    bundle["execution"]["counts"] = {
        "passed": 4719,
        "failed": 0,
        "errored": 0,
        "skipped": 0,
    }
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["counts"])


def test_r2_02_forged_partition_counts_are_refused(tmp_path: Path) -> None:
    """A per-partition total inflated to match a forged total must not pass."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    part = bundle["execution"]["partitions"][0]
    part["counts"] = {
        key: value + 1 for key, value in part["counts"].items() if key == "passed"
    }
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["counts"])


def test_r2_03_a_dropped_outcome_is_refused(tmp_path: Path) -> None:
    """Erasing one node's outcome must not leave the totals authoritative."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    part = bundle["execution"]["partitions"][0]
    victim = sorted(part["outcomes"])[0]
    del part["outcomes"][victim]
    part["executed_nodes"] = [n for n in part["executed_nodes"] if n != victim]
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["counts"])


# --------------------------------------------------------------------------- #
# V02 -- forged digests                                                       #
# --------------------------------------------------------------------------- #


def test_r2_04_forged_collection_digest_is_refused(tmp_path: Path) -> None:
    """R1 case 28: `collection.digest` randomized verified COMPLETE."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    bundle["collection"]["digest"] = "0" * 64
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["digest"])


def test_r2_05_forged_execution_digest_is_refused(tmp_path: Path) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    bundle["execution"]["digest"] = "1" * 64
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["digest"])


def test_r2_06_forged_collection_count_is_refused(tmp_path: Path) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    bundle["collection"]["count"] = 4718
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["counts"])


def test_r2_07_forged_unique_count_is_refused(tmp_path: Path) -> None:
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    bundle["execution"]["unique_count"] = 4718
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["counts"])


# --------------------------------------------------------------------------- #
# V03 -- consistently reduced test universe                                   #
# --------------------------------------------------------------------------- #


def test_r2_08_shrunken_universe_is_refused(tmp_path: Path) -> None:
    """R1 case 29: a node dropped from BOTH sides verified COMPLETE."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    victim = sorted(bundle["collection"]["nodes"])[0]
    bundle["collection"]["nodes"] = [
        node for node in bundle["collection"]["nodes"] if node != victim
    ]
    bundle["execution"]["nodes"] = [
        node for node in bundle["execution"]["nodes"] if node != victim
    ]
    bundle["collection"]["count"] = len(bundle["collection"]["nodes"])
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["coverage"])


def test_r2_09_shrunken_universe_with_recomputed_digests_is_refused(
    tmp_path: Path,
) -> None:
    """The same forgery, made consistent: digests recomputed to match.

    This is the case the R1 audit called inherently undetectable without an
    external anchor.  The partition-level intent is that anchor: the node is
    still inside the partition that was asked to execute it.
    """
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    victim = sorted(bundle["collection"]["nodes"])[0]
    for side, key in (("collection", "nodes"), ("execution", "nodes")):
        bundle[side][key] = [node for node in bundle[side][key] if node != victim]
    bundle["collection"]["count"] = len(bundle["collection"]["nodes"])
    bundle["collection"]["digest"] = runner._digest_node_ids(bundle["collection"]["nodes"])
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    bundle["execution"]["digest"] = runner._digest_node_ids(bundle["execution"]["nodes"])
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["coverage"])


def test_r2_10_partition_boundary_breach_is_refused(tmp_path: Path) -> None:
    """A node executed by a partition that never intended to run it."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    part = bundle["execution"]["partitions"][0]
    ghost = "quant-lab/tests/ghost.py::test_ghost"
    part["executed_nodes"] = sorted(part["executed_nodes"] + [ghost])
    part["outcomes"][ghost] = "passed"
    part["counts"]["passed"] += 1
    bundle["execution"]["nodes"] = bundle["execution"]["nodes"] + [ghost]
    bundle["execution"]["unique_count"] = len(bundle["execution"]["nodes"])
    bundle["execution"]["digest"] = runner._digest_node_ids(bundle["execution"]["nodes"])
    bundle["execution"]["counts"]["passed"] += 1
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["coverage"])


def test_r2_11_external_anchor_disagreement_is_refused(tmp_path: Path) -> None:
    """A supplied universe anchor must be honoured, not ignored."""
    directory = _clone_bundle(tmp_path)
    verdict = runner.evaluate_bundle(
        _load(directory), base_dir=directory, expected_digest="f" * 64
    )
    _assert_refused(verdict, EXPECTED_REASONS["digest"])


# --------------------------------------------------------------------------- #
# V04 -- JUnit / result-stream disagreement                                   #
# --------------------------------------------------------------------------- #


def test_r2_12_emptied_junit_is_refused(tmp_path: Path) -> None:
    """R1 case 26: emptying a JUnit file still verified COMPLETE."""
    directory = _clone_bundle(tmp_path)
    (directory / "junit_0.xml").write_text(
        '<testsuites><testsuite name="pytest" tests="0" errors="0" failures="0" '
        'skipped="0"></testsuite></testsuites>',
        encoding="utf-8",
    )
    _assert_refused(_verdict(directory), EXPECTED_REASONS["junit"])


def test_r2_13_junit_count_disagreement_with_fresh_digest_is_refused(
    tmp_path: Path,
) -> None:
    """A JUnit shrink with the recorded hash updated must still be refused."""
    directory = _clone_bundle(tmp_path)
    bundle = _load(directory)
    path = directory / "junit_0.xml"
    tree = ET.parse(path)
    root = tree.getroot()
    removed = 0
    for suite in root.iter("testsuite"):
        for case in list(suite.iter("testcase"))[:25]:
            suite.remove(case)
            removed += 1
    tree.write(path, encoding="utf-8", xml_declaration=True)
    part = bundle["execution"]["partitions"][0]
    part["junit_sha256"] = runner._sha256_file(path)
    part["junit_bytes"] = path.stat().st_size
    assert removed == 25
    _assert_refused(_verdict(directory, bundle), EXPECTED_REASONS["junit"])


def test_r2_14_missing_junit_is_refused(tmp_path: Path) -> None:
    directory = _clone_bundle(tmp_path)
    (directory / "junit_1.xml").unlink()
    _assert_refused(_verdict(directory), EXPECTED_REASONS["junit"])


def test_r2_15_junit_case_count_matches_executed_nodes(tmp_path: Path) -> None:
    """Guard the repair against over-firing: the real counts are consistent."""
    bundle = _load(BUNDLE_DIR)
    for part in bundle["execution"]["partitions"]:
        junit = BUNDLE_DIR / f"junit_{part['index']}.xml"
        cases = sum(1 for _ in ET.parse(junit).getroot().iter("testcase"))
        assert cases == len(part["executed_nodes"])
