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

Structure. This module is the SINGLE OWNER of the test-baseline contract: which
artifact is the baseline, the command that produces it, the canonical-digest rule,
and whether a parsed artifact may be published at all::

    pytest --junitxml -> ARTIFACT_RELATIVE_PATH (inside the repository)
                      -> read_test_evidence()  artifact-level facts; raises
                      -> TestEvidence          the sole carrier of one baseline
                      -> check_baseline()      the sole publishability policy
                         |- emit()             refuses to publish an unverified one
                         `- decide_gate()      records that verdict in the package
    verify_citation()  re-derives a published citation from the bytes ON DISK, so
                       a stale citation blocks instead of verifying

The TESTED TREE is derived from Git under the rule declared below
(`TESTED_TREE_PATHS`), never typed in by hand: a hand-declared tree is the same
self-reporting defect the artifact exists to forbid.

`scenarios/g8_emit_evidence.py` owns PRESENTATION (the receipt and its prose) and
the declared tree (`TESTED_SHA`); it keeps no copy of any rule declared here, and
no other module may re-decide whether an artifact is acceptable.
"""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


class UnverifiableTestEvidence(RuntimeError):
    """Raised when a test-result artifact cannot certify the claimed baseline."""


#: the suite identity every authoritative artifact must carry. pytest names the
#: root <testsuite> after the invocation; the archive requires the suite to be
#: the stress-suite `tests` package, not an unrelated or partial collection.
REQUIRED_SUITE_IDENTITY_PREFIXES = ("tests", "pytest")

#: The paths that define the CODE tree under test. The TESTED TREE is the newest
#: commit that changed any of them, which is what the baseline certifies: a later
#: commit that touches only docs or evidence cannot move the identity of the code
#: the artifact was measured on, so the package stays reproducible from any later
#: commit instead of depending on a hand-bumped constant. Declared once here; the
#: harness (conftest) and the emitter both ask Git this same question.
TESTED_TREE_PATHS = ("stress-suite/engine", "stress-suite/scenarios",
                     "stress-suite/tests")
#: the `git` invocation that resolves it, declared next to the rule it implements
TESTED_TREE_GIT_ARGS = ("log", "-1", "--format=%H", "--", *TESTED_TREE_PATHS)

#: The suite command the mission names as authoritative. It is the command the
#: artifact's own record cites, and the prefix of the artifact-producing command.
PACKAGE_DIR = "stress-suite"
AUTHORITATIVE_TEST_COMMAND = (
    f"cd {PACKAGE_DIR} && PYTHONIOENCODING=utf-8 python -m pytest tests -q")

#: The ONE declared location of the baseline artifact. It must lie inside the
#: repository so a reviewer anywhere can obtain the exact bytes the baseline was
#: read from and resolve the citation without trusting the generator (R-G8-07).
#: The location is declared once, here: the reader admits no other path, `emit`
#: refuses to publish an artifact from any other path, and the receipt cites this
#: one. Callers validate against the declaration rather than restating it.
ARTIFACT_PATH_IN_PACKAGE = "evidence/G8_TEST_RESULTS.xml"
ARTIFACT_RELATIVE_PATH = f"{PACKAGE_DIR}/{ARTIFACT_PATH_IN_PACKAGE}"
#: the same command that writes the declared artifact, run from the package
#: directory; derived so the two can never drift apart
ARTIFACT_COMMAND = (f"{AUTHORITATIVE_TEST_COMMAND} "
                    f"--junitxml={ARTIFACT_PATH_IN_PACKAGE}")

#: Attributes JUnit's writer stamps per RUN rather than per RESULT. They are why a
#: raw artifact digest cannot be reproduced by re-running: the bytes differ even
#: when every test outcome is identical. This rule names exactly what the
#: canonical form removes, so `artifact_digest` (raw, checkable against the
#: committed bytes) and `artifact_canonical_digest` (re-derivable by re-running)
#: keep distinct declared meanings and neither redefines "content digest".
#:
#: STRESS-G8ARCH5: a rule is a VERSIONED DEFINITION, not a label. The published
#: name resolves in `CANONICALIZATION_RULES` below, `canonical_junit_bytes`
#: implements the fields of that same object, and the receipt publishes the
#: DEFINITION's fingerprint. A definition therefore cannot move while the name
#: stays put, which is how a published digest could silently change meaning: the
#: label would still read the same while the bytes it describes did not.
CANONICALIZATION_RULES: Dict[str, Mapping[str, Any]] = {
    "JUNIT_XML_MINUS_VOLATILE_ATTRS_V1": {
        "strips_attributes": ("time", "timestamp", "hostname"),
        "sorts_attributes": True,
    },
}

#: Prose about each rule, kept OUT of the definition ON PURPOSE (STRESS-G8ARCH6).
#: A note is documentation, not semantics: hashing it would make a typo fix move
#: the pinned fingerprint and therefore demand a new rule NAME, which inverts the
#: point of pinning a name to its definition. The definition holds behaviour only,
#: so the fingerprint answers exactly one question -- has the meaning changed?
CANONICALIZATION_RULE_NOTES: Dict[str, str] = {
    "JUNIT_XML_MINUS_VOLATILE_ATTRS_V1":
        ("strips the attributes JUnit stamps per RUN and orders attributes "
         "deterministically. Newline identity is STRUCTURAL rather than "
         "configured -- the serializer normalises character data and escapes "
         "CR/LF inside attribute values, so the canonical bytes cannot contain a "
         "raw CR -- which is why there is no newline-normalisation step to "
         "declare here: an unimplemented declaration would be a description, not "
         "a rule"),
}

#: the versioned name this package publishes; the name IS the version
ARTIFACT_CANONICALIZATION_RULE = "JUNIT_XML_MINUS_VOLATILE_ATTRS_V1"

#: the declared rule a citation must satisfy, stated once so the reader, the
#: verifier and the receipt cannot describe it differently (STRESS-G8ARCH4).
CITATION_RULE = ("the cited path must resolve inside the declared tree and its "
                 "on-disk raw and canonical digests must equal the published ones, "
                 "and it must record the tree the caller declares")


def _ordered(element: ET.Element) -> ET.Element:
    """Rebuild an element with its attributes in sorted order, so the canonical
    bytes do not depend on the order the parser happened to see them in."""
    clone = ET.Element(element.tag,
                       {k: element.attrib[k] for k in sorted(element.attrib)})
    clone.text, clone.tail = element.text, element.tail
    for child in element:
        clone.append(_ordered(child))
    return clone


def canonical_rule(name: str = ARTIFACT_CANONICALIZATION_RULE) -> Mapping[str, Any]:
    """The DEFINITION a published rule NAME stands for.

    An unknown name refuses rather than defaulting: a digest whose declared rule
    cannot be resolved is not a documented digest."""
    try:
        return CANONICALIZATION_RULES[name]
    except KeyError:
        raise UnverifiableTestEvidence(
            f"unknown canonicalization rule {name!r}: a published rule name must "
            f"resolve to a declared definition (declared: "
            f"{sorted(CANONICALIZATION_RULES)})")


def canonical_rule_fingerprint(
        name: str = ARTIFACT_CANONICALIZATION_RULE) -> str:
    """A digest of the rule's DECLARED DEFINITION, published beside its name so a
    reader can tell whether the meaning behind a fixed label has moved."""
    definition = canonical_rule(name)
    body = {k: definition[k] for k in sorted(definition)}
    return hashlib.sha256(
        json.dumps({"name": name, **body}, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def canonical_junit_bytes(blob: bytes) -> bytes:
    """The canonical form of a JUnit artifact under
    `ARTIFACT_CANONICALIZATION_RULE`. Two runs over the same tree produce the same
    canonical bytes; the raw bytes legitimately differ.

    Every declared field of the rule is IMPLEMENTED here, because a declaration
    that does not drive the implementation is a description, not a definition."""
    rule = canonical_rule()
    root = ET.fromstring(blob)
    for element in root.iter():
        for attribute in rule["strips_attributes"]:
            element.attrib.pop(attribute, None)
    canonical = _ordered(root) if rule["sorts_attributes"] else root
    return ET.tostring(canonical, encoding="utf-8")


def canonical_artifact_digest(blob: bytes) -> str:
    return hashlib.sha256(canonical_junit_bytes(blob)).hexdigest()


@dataclass(frozen=True)
class TestEvidence:
    """The measured result of one authoritative suite run."""

    artifact_path: str
    artifact_digest: str
    artifact_bytes: int
    artifact_canonical_digest: str
    repo_relative_path: str
    #: the tree the citation is relative to. Machine-local, so it is deliberately
    #: NOT serialised: the receipt publishes the repo-relative path only, and this
    #: field is what lets a caller re-derive that citation from disk.
    repo_root: str
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
    #: (test, recorded reason) for every skip, so a partial run is NAMED in the
    #: record rather than smoothed into a bare `skipped` count (STRESS-G8ARCH4).
    skipped_cases: tuple[tuple[str, str], ...] = ()

    @property
    def measured_full(self) -> int:
        return self.collected

    @property
    def in_tree(self) -> bool:
        """Whether the artifact lives inside the tree the caller declared. A
        baseline whose artifact is outside the tree cannot be re-checked by a
        reviewer and is not evidence (review finding R-G8-07)."""
        return bool(self.repo_relative_path)

    @property
    def honest_baseline(self) -> bool:
        """Only a clean, complete artifact certifies a baseline."""
        return (self.failed == 0 and self.errors == 0
                and self.collected == self.passed + self.skipped)

    def to_dict(self) -> Dict[str, Any]:
        return {
            # the CITATION is repo-relative: a machine-local path is not evidence
            # and would make the receipt non-portable, so it is not serialised.
            "artifact_path": self.repo_relative_path or self.artifact_path,
            "artifact_path_scope": ("REPO_RELATIVE" if self.in_tree
                                    else "OUTSIDE_DECLARED_TREE"),
            "artifact_canonicalization_rule": ARTIFACT_CANONICALIZATION_RULE,
            "artifact_canonicalization_rule_fingerprint":
                canonical_rule_fingerprint(),
            "artifact_canonical_digest": self.artifact_canonical_digest,
            "artifact_digest_semantics": (
                "artifact_digest is the RAW sha256 of the artifact as produced, so "
                "it changes with run timings; artifact_canonical_digest applies "
                "the declared rule above and is re-derivable by re-running."),
            "artifact_digest": self.artifact_digest,
            "artifact_bytes": self.artifact_bytes,
            "authoritative_test_command": self.command,
            "suite_identity": self.suite_identity,
            "tested_sha": self.tested_sha,
            "python_version": self.python_version,
            "pytest_version": self.pytest_version,
            "collected": self.collected, "passed": self.passed,
            "failed": self.failed, "skipped": self.skipped,
            "errors": self.errors,
            # no exit_status: it cannot be observed from a JUnit document, so
            # publishing one could only publish a claim (STRESS-G8ARCH4)
            "skipped_cases": [{"test": name, "reason": reason or "not recorded"}
                              for name, reason in self.skipped_cases],
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


def _repo_relative(path: Path, repo_root: str | Path) -> str:
    """The artifact's path relative to the declared tree, or "" when it lies
    outside that tree. Resolution is realpath-based so a symlinked temp directory
    cannot smuggle an artifact in."""
    try:
        return path.resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return ""


def read_test_evidence(
    artifact: str | Path,
    *,
    expected_tested_sha: str,
    repo_root: Optional[str | Path] = None,
    expected_suite_identity: str = "tests",
    command: str = AUTHORITATIVE_TEST_COMMAND,
    python_version: str = "",
    pytest_version: str = "",
    expected_artifact_digest: Optional[str] = None,
    expected_artifact_bytes: Optional[int] = None,
) -> TestEvidence:
    """Parse a JUnit XML artifact into a certifiable TestEvidence record.

    Refuses: absent, empty, unparsable, non-`testsuite` documents; documents with
    no test cases; documents whose suite identity does not match; documents
    produced against a different tree; documents whose bytes changed since the
    run; documents that lie OUTSIDE the declared tree (`repo_root`), which a
    reviewer could not obtain; and any document reporting failures or errors.

    STRESS-G8ARCH4: this reader accepts no exit-status CLAIM. The producing
    process's exit code cannot be observed from a JUnit document, so a
    caller-supplied integer could only be a self-report -- and the old default of
    0 read an unobserved outcome as a favourable one. The refusal it drove is
    already driven by facts MEASURED from the artifact (`failed`, `errors`,
    `collected == passed + skipped`), which is strictly stronger evidence, so the
    record now publishes no exit status at all instead of an assumed success.
    Skips are the one honest exception, so they are NAMED rather than counted:
    `skipped_cases` carries each skipped test and its recorded reason.

    When `repo_root` is given, the returned record carries the artifact's
    repo-relative citation, which is the path the receipt publishes.
    """
    path = Path(artifact)
    if not path.is_file():
        raise UnverifiableTestEvidence(
            f"test artifact {path} does not exist; a test baseline cannot be "
            "certified without the artifact the authoritative command produced")
    relative = ""
    if repo_root is not None:
        relative = _repo_relative(path, repo_root)
        if not relative:
            raise UnverifiableTestEvidence(
                f"test artifact {path} is not inside the declared tree "
                f"{Path(repo_root).resolve()}; a baseline cited at a "
                "machine-local path cannot be obtained or re-checked by a "
                "reviewer, so it is refused rather than published")
        if relative != ARTIFACT_RELATIVE_PATH:
            # one declared location: an artifact inside the tree but somewhere
            # else would publish a citation the authoritative command never
            # writes, so the receipt and the command would disagree
            raise UnverifiableTestEvidence(
                f"test artifact {path} resolves to {relative!r} inside the "
                f"declared tree, but the authoritative build publishes "
                f"{ARTIFACT_RELATIVE_PATH!r}. Produce it with "
                f"`{ARTIFACT_COMMAND}` so the receipt cites a path a reviewer "
                "can resolve")
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
    failed = sum(1 for c in cases if c.find("failure") is not None)
    errors = sum(1 for c in cases if c.find("error") is not None)
    skipped_nodes = [c for c in cases if c.find("skipped") is not None]
    skipped = len(skipped_nodes)
    skipped_cases: List[tuple[str, str]] = []
    for node in skipped_nodes:
        case_class = str(node.get("classname", ""))
        case_name = str(node.get("name", "")) or "UNNAMED"
        skipped_el = node.find("skipped")
        reason = "" if skipped_el is None else str(skipped_el.get("message", ""))
        skipped_cases.append(
            (f"{case_class}::{case_name}" if case_class else case_name, reason))
    passed = collected - failed - errors - skipped

    if failed or errors:
        raise UnverifiableTestEvidence(
            f"refusing to archive a failing baseline: artifact {path} reports "
            f"{failed} failure(s) and {errors} error(s)" )
    if collected != len(cases):
        raise UnverifiableTestEvidence(
            f"malformed test artifact {path}: <testsuite tests={collected}> does "
            f"not match the {len(cases)} recorded <testcase> elements")

    return TestEvidence(
        artifact_path=relative or str(path), artifact_digest=digest,
        artifact_bytes=len(blob),
        artifact_canonical_digest=canonical_artifact_digest(blob),
        repo_relative_path=relative,
        repo_root=str(Path(repo_root).resolve()) if repo_root is not None else "",
        command=command, suite_identity=suite_identity, tested_sha=expected_tested_sha,
        python_version=python_version, pytest_version=pytest_version,
        collected=collected, passed=passed, failed=failed, skipped=skipped,
        errors=errors, skipped_cases=tuple(skipped_cases))


def check_baseline(test_evidence: TestEvidence, *, tested_sha: str) -> Dict[str, Any]:
    """The baseline plus its verifiability verdict: the SOLE policy for whether a
    baseline may be published or rested on.

    Consumers do not restate any part of it — `emit` refuses to publish an
    unverified baseline and `decide_gate` records this verdict in the package.
    """
    problems = []
    if not test_evidence.in_tree:
        problems.append(
            f"the bound artifact is cited at {test_evidence.artifact_path!r}, "
            "which is outside the declared tree, so the citation could not be "
            "resolved by a reviewer")
    elif test_evidence.repo_relative_path != ARTIFACT_RELATIVE_PATH:
        problems.append(
            f"the bound artifact resolves to "
            f"{test_evidence.repo_relative_path!r}, not the declared evidence "
            f"path {ARTIFACT_RELATIVE_PATH!r}")
    if not test_evidence.honest_baseline:
        problems.append(
            f"artifact reports collected={test_evidence.collected} "
            f"passed={test_evidence.passed} skipped={test_evidence.skipped} "
            f"failed={test_evidence.failed} errors={test_evidence.errors}")
    if not tested_sha:
        # STRESS-G8ARCH4: an UNDECLARED tree used to skip the comparison below,
        # which read an unknown tree as 'any tree will do'. UNKNOWN is not
        # favourable: a package that names no tree is not verified, it is unbound.
        problems.append(
            "no tree was declared for this baseline: the caller must name the tree "
            "the package is archived for, because a missing declaration cannot "
            "stand in for evidence")
    elif test_evidence.tested_sha != tested_sha:
        problems.append(
            f"artifact was produced against {test_evidence.tested_sha}, not "
            f"{tested_sha}")
    return {"verified": not problems, "problems": problems,
            "collected_full": test_evidence.collected,
            "declared_tested_sha": tested_sha,
            "artifact_bound_tested_sha": test_evidence.tested_sha,
            "artifact_digest": test_evidence.artifact_digest,
            "artifact_canonical_digest": test_evidence.artifact_canonical_digest,
            "artifact_path": test_evidence.artifact_path,
            "artifact_in_tree": test_evidence.in_tree,
            "authoritative_test_command": test_evidence.command,
            "suite_identity": test_evidence.suite_identity,
            "tested_sha": test_evidence.tested_sha}


def verify_citation(citation: Mapping[str, Any], *, repo_root: str | Path,
                    expected_tested_sha: str) -> Dict[str, Any]:
    """Re-derive a PUBLISHED citation from the bytes on disk.

    A package may not merely assert that its baseline is checkable. The citation a
    receipt publishes is evidence only while the bytes at the cited repo-relative
    path still resolve inside the declared tree, still hash to the published raw
    and canonical digests, and still record the tree the caller is resting on.
    Anything else is a STALE CITATION, and a stale citation must BLOCK rather than
    verify (STRESS-G8ARCH2): publishing a digest that no longer describes the tree
    is exactly the self-reporting defect R-G8-07 forbids.

    `read_test_evidence` is reused for the path, scope and tree rules, so they are
    not restated here; `expected_tested_sha` is the tree the CALLER rests on, and a
    citation recorded against any other tree is refused rather than reconciled.

    STRESS-G8ARCH4: `expected_tested_sha` is REQUIRED and may not be empty. It used
    to default to "", on which the check silently fell back to the citation's own
    recorded tree -- i.e. it verified the evidence against the evidence's own
    self-report, the very defect this function exists to forbid. An omitted or
    empty declaration now refuses instead of degrading to a weaker check.
    """
    problems: List[str] = []
    path = str(citation.get("artifact_path", ""))
    scope = str(citation.get("artifact_path_scope", ""))
    if not expected_tested_sha:
        problems.append(
            "no tree was declared for this citation: it cannot be re-derived "
            "against its own recorded tree, because that would trust the "
            "evidence's self-report")
        return {"verified": False, "problems": problems, "artifact_path": path,
                "recorded_tested_sha": "",
                "citation_rule": CITATION_RULE}
    if scope != "REPO_RELATIVE":
        problems.append(
            f"the citation is scoped {scope or 'UNKNOWN'!r}: a location outside "
            "the declared tree cannot be resolved by a reviewer")
    if not path:
        problems.append("the citation names no artifact path")
        return {"verified": False, "problems": problems, "artifact_path": "",
                "recorded_tested_sha": "", "citation_rule": CITATION_RULE}
    try:
        evidence = read_test_evidence(Path(repo_root) / path,
                                      expected_tested_sha=expected_tested_sha,
                                      repo_root=repo_root)
    except UnverifiableTestEvidence as exc:
        problems.append(f"stale citation: {exc}")
        return {"verified": False, "problems": problems, "artifact_path": path,
                "recorded_tested_sha": "", "citation_rule": CITATION_RULE}
    if evidence.artifact_digest != citation.get("artifact_digest"):
        problems.append(
            f"stale citation: the bytes at {path} hash to "
            f"{evidence.artifact_digest}, but the package publishes "
            f"{citation.get('artifact_digest')}")
    if evidence.artifact_canonical_digest != citation.get("artifact_canonical_digest"):
        problems.append(
            f"stale citation: the canonical digest of {path} is "
            f"{evidence.artifact_canonical_digest}, but the package publishes "
            f"{citation.get('artifact_canonical_digest')}")
    if evidence.tested_sha != citation.get("tested_sha", evidence.tested_sha):
        problems.append(
            f"stale citation: {path} records tree {evidence.tested_sha}, but the "
            f"package publishes {citation.get('tested_sha')}")
    return {"verified": not problems, "problems": problems,
            "artifact_path": path,
            "recorded_tested_sha": evidence.tested_sha,
            "artifact_digest": evidence.artifact_digest,
            "artifact_canonical_digest": evidence.artifact_canonical_digest,
            "citation_rule": CITATION_RULE}


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
