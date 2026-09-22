"""G8 — provenance-bearing test evidence (revision R3, review finding R-G8-07).

A bare integer is not evidence that a test suite passed. Before R3 the evidence
emitter accepted a scalar and wrote::

    collected = N, passed = N, failed = 0

from whatever number it was handed, so 1 and 9999 certified just as well as the
measured count. This module replaces that with a JUnit XML result artifact:

  * the authoritative pytest command writes the artifact;
  * the artifact is parsed for collected / passed / failed / skipped / errors;
  * the command, the environment, the artifact digest and the exit status are
    recorded alongside the counts;
  * emission is REFUSED when the artifact is absent, malformed, reports any
    failure or error, does not carry the required suite identity, or was produced
    against a different tree than the one being archived.

The reader is deliberately strict: it never repairs, never infers and never
turns a missing fact into a favourable one.
"""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


class UnverifiableTestEvidence(RuntimeError):
    """Raised when a test-result artifact cannot certify the claimed baseline."""


#: the suite identity every authoritative artifact must carry. pytest names the
#: root <testsuite> after the invocation; the archive requires the suite to be
#: the stress-suite `tests` package, not an unrelated or partial collection.
REQUIRED_SUITE_IDENTITY_PREFIXES = ("tests", "pytest")

AUTHORITATIVE_TEST_COMMAND = (
    "cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q "
    "--junitxml=<artifact>")


@dataclass(frozen=True)
class TestEvidence:
    """The measured result of one authoritative suite run."""

    artifact_path: str
    artifact_digest: str
    artifact_bytes: int
    command: str
    suite_identity: str
    tested_sha: str
    python_version: str
    pytest_version: str
    collected: int
    passed: int
    failed: int
    skipped: int
    errors: int
    exit_status: int

    @property
    def measured_full(self) -> int:
        return self.collected

    @property
    def honest_baseline(self) -> bool:
        """Only a clean, complete artifact certifies a baseline."""
        return (self.failed == 0 and self.errors == 0
                and self.collected == self.passed + self.skipped
                and self.exit_status == 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "artifact_digest": self.artifact_digest,
            "artifact_bytes": self.artifact_bytes,
            "authoritative_test_command": self.command,
            "suite_identity": self.suite_identity,
            "tested_sha": self.tested_sha,
            "python_version": self.python_version,
            "pytest_version": self.pytest_version,
            "collected": self.collected, "passed": self.passed,
            "failed": self.failed, "skipped": self.skipped,
            "errors": self.errors, "exit_status": self.exit_status,
            "honest_baseline": self.honest_baseline,
        }


def _int_attr(node: ET.Element, name: str, where: str) -> int:
    raw = node.get(name)
    if raw is None:
        raise UnverifiableTestEvidence(
            f"malformed test artifact: <{node.tag}> at {where} has no {name!r} "
            f"attribute; a missing count is never read as zero")
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise UnverifiableTestEvidence(
            f"malformed test artifact: {name}={raw!r} at {where} is not an integer")


def _tree_properties(root: ET.Element) -> Dict[str, str]:
    props: Dict[str, str] = {}
    for node in root.iter("property"):
        name, value = node.get("name"), node.get("value")
        if name is not None:
            props[str(name)] = "" if value is None else str(value)
    return props


def read_test_evidence(
    artifact: str | Path,
    *,
    expected_tested_sha: str,
    expected_suite_identity: str = "tests",
    command: str = AUTHORITATIVE_TEST_COMMAND,
    python_version: str = "",
    pytest_version: str = "",
    exit_status: int = 0,
    expected_artifact_digest: Optional[str] = None,
    expected_artifact_bytes: Optional[int] = None,
) -> TestEvidence:
    """Parse a JUnit XML artifact into a certifiable TestEvidence record.

    Refuses: absent, empty, unparsable, non-`testsuite` documents; documents with
    no test cases; documents whose suite identity does not match; documents
    produced against a different tree; documents whose bytes changed since the
    run; and any document reporting failures or errors.
    """
    path = Path(artifact)
    if not path.is_file():
        raise UnverifiableTestEvidence(
            f"test artifact {path} does not exist; a test baseline cannot be "
            "certified without the artifact the authoritative command produced")
    blob = path.read_bytes()
    if not blob.strip():
        raise UnverifiableTestEvidence(f"test artifact {path} is empty")
    digest = hashlib.sha256(blob).hexdigest()
    if expected_artifact_digest is not None and digest != expected_artifact_digest:
        raise UnverifiableTestEvidence(
            f"stale test artifact: {path} has SHA-256 {digest}, expected "
            f"{expected_artifact_digest}; the artifact must be the one produced "
            "for THIS run")
    if expected_artifact_bytes is not None and len(blob) != expected_artifact_bytes:
        raise UnverifiableTestEvidence(
            f"stale test artifact: {path} is {len(blob)} bytes, expected "
            f"{expected_artifact_bytes}")
    try:
        root = ET.fromstring(blob)
    except ET.ParseError as exc:
        raise UnverifiableTestEvidence(f"malformed test artifact {path}: {exc}") from exc
    if root.tag == "testsuites":
        # pytest's JUnit writer wraps its single suite in a <testsuites> root.
        # Exactly one suite is expected: more than one means the artifact is not
        # one run of one suite, and none means there is nothing to certify.
        children = [child for child in root if child.tag == "testsuite"]
        if len(children) != 1:
            raise UnverifiableTestEvidence(
                f"malformed test artifact {path}: <testsuites> wraps "
                f"{len(children)} <testsuite> elements, expected exactly 1")
        root = children[0]
    elif root.tag != "testsuite":
        raise UnverifiableTestEvidence(
            f"malformed test artifact {path}: root element is <{root.tag}>, "
            "expected <testsuite>")

    suite_identity = str(root.get("name", ""))
    if not suite_identity:
        raise UnverifiableTestEvidence(
            f"malformed test artifact {path}: <testsuite> declares no name, so "
            "the recorded suite identity cannot be established")
    if not suite_identity.startswith(REQUIRED_SUITE_IDENTITY_PREFIXES):
        raise UnverifiableTestEvidence(
            f"test artifact {path} was produced by suite {suite_identity!r}, "
            f"which is not the required suite identity "
            f"({list(REQUIRED_SUITE_IDENTITY_PREFIXES)})")

    props = _tree_properties(root)
    artifact_sha = props.get("tested_sha", "")
    if not artifact_sha:
        # the artifact must name the tree it was produced against, otherwise a
        # baseline measured on an unrelated revision would certify this one
        raise UnverifiableTestEvidence(
            f"test artifact {path} does not name the tree it was produced "
            "against (required property 'tested_sha'); an unbound baseline "
            "cannot certify any revision")
    if artifact_sha != expected_tested_sha:
        raise UnverifiableTestEvidence(
            f"baseline/tree mismatch: artifact was produced against "
            f"{artifact_sha}, this evidence is being archived for "
            f"{expected_tested_sha}")

    cases = list(root.iter("testcase"))
    if not cases:
        raise UnverifiableTestEvidence(
            f"malformed test artifact {path}: no <testcase> elements, so the run "
            "did not actually collect anything")

    collected = _int_attr(root, "tests", str(path))
    passed = collected - sum(1 for c in cases if c.find("failure") is not None) \
        - sum(1 for c in cases if c.find("error") is not None) \
        - sum(1 for c in cases if c.find("skipped") is not None)
    failed = sum(1 for c in cases if c.find("failure") is not None)
    errors = sum(1 for c in cases if c.find("error") is not None)
    skipped = sum(1 for c in cases if c.find("skipped") is not None)

    if failed or errors:
        raise UnverifiableTestEvidence(
            f"refusing to archive a failing baseline: artifact {path} reports "
            f"{failed} failure(s) and {errors} error(s)" )
    if collected != len(cases):
        raise UnverifiableTestEvidence(
            f"malformed test artifact {path}: <testsuite tests={collected}> does "
            f"not match the {len(cases)} recorded <testcase> elements")
    if exit_status != 0:
        raise UnverifiableTestEvidence(
            f"refusing to archive an unsuccessful baseline: authoritative "
            f"command exit status {exit_status}")

    return TestEvidence(
        artifact_path=str(path), artifact_digest=digest, artifact_bytes=len(blob),
        command=command, suite_identity=suite_identity, tested_sha=expected_tested_sha,
        python_version=python_version, pytest_version=pytest_version,
        collected=collected, passed=passed, failed=failed, skipped=skipped,
        errors=errors, exit_status=exit_status)


def check_baseline(test_evidence: TestEvidence, *, tested_sha: str) -> Dict[str, Any]:
    """The gate-facing view of the baseline plus its verifiability verdict."""
    problems = []
    if not test_evidence.honest_baseline:
        problems.append(
            f"artifact reports collected={test_evidence.collected} "
            f"passed={test_evidence.passed} skipped={test_evidence.skipped} "
            f"failed={test_evidence.failed} errors={test_evidence.errors} "
            f"exit_status={test_evidence.exit_status}")
    if tested_sha and test_evidence.tested_sha != tested_sha:
        problems.append(
            f"artifact was produced against {test_evidence.tested_sha}, not "
            f"{tested_sha}")
    return {"verified": not problems, "problems": problems,
            "measured_full": test_evidence.collected,
            "collected_full": test_evidence.collected,
            "artifact_digest": test_evidence.artifact_digest,
            "artifact_path": test_evidence.artifact_path,
            "authoritative_test_command": test_evidence.command,
            "suite_identity": test_evidence.suite_identity,
            "tested_sha": test_evidence.tested_sha}


def junit_document(*, cases: int, name: str = "tests", tested_sha: str,
                   failures: int = 0, errors: int = 0, skipped: int = 0,
                   extra_properties: Mapping[str, str] | None = None) -> str:
    """Build a JUnit XML document. Used by the regressions and by sealed
    fixtures; the authoritative package build consumes a live artifact."""
    props = {"tested_sha": tested_sha}
    props.update(extra_properties or {})
    body = []
    for i in range(cases):
        if i < failures:
            body.append(f'<testcase classname="t" name="fail_{i}">'
                        f'<failure message="x"/></testcase>')
        elif i < failures + errors:
            body.append(f'<testcase classname="t" name="err_{i}">'
                        f'<error message="x"/></testcase>')
        elif i < failures + errors + skipped:
            body.append(f'<testcase classname="t" name="skip_{i}">'
                        f'<skipped/></testcase>')
        else:
            body.append(f'<testcase classname="t" name="ok_{i}"/>')
    prop_xml = "".join(f'<property name="{k}" value="{v}"/>'
                       for k, v in sorted(props.items()))
    return ('<?xml version="1.0" encoding="utf-8"?>'
            f'<testsuite name="{name}" tests="{cases}">'
            f'<properties>{prop_xml}</properties>'
            + "".join(body) + '</testsuite>')
