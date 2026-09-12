"""Test-evidence capture for freeze manifests (P1-R1-I0).

Runs a command, parses its output into machine-readable counts, and emits a
freeze-evidence block or raises. Fail-closed by design:

- the command must exit 0 (any failure -> FreezeEvidenceError);
- output must match an expected pattern supplied by the caller;
- the captured commit must match the caller's expectation;
- no results are ever fabricated: the numbers come from the run itself.

Stdlib only (no pytest JSON plugin dependency, per operator directive).

Usage::

    evidence = capture_test_evidence(
        command=["python", "-m", "pytest", "qcae/tests", "-q"],
        success_pattern=PYTEST_Q_PASS,
        expected_commit=git_head_commit(),
    )
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence

__all__ = [
    "FreezeEvidenceError",
    "TestEvidence",
    "PYTEST_Q_PASS",
    "PYTEST_Q_FAIL",
    "capture_test_evidence",
    "git_head_commit",
    "write_test_results_block",
]


class FreezeEvidenceError(Exception):
    """Test evidence could not be captured truthfully; freeze must not emit PASS."""


@dataclass(frozen=True)
class TestEvidence:
    collected: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    command: List[str]
    evidence_label: str = "LOCAL TEST EVIDENCE"
    executed_at: str = ""
    tested_commit: str = ""

    def as_manifest_block(self) -> dict:
        return {
            "collected": self.collected,
            "passed": self.passed,
            "passed_is_placeholder": False,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": round(self.duration_seconds, 3),
            "command": self.command,
            "evidence_label": self.evidence_label,
            "executed_at": self.executed_at,
            "tested_commit": self.tested_commit,
        }


#: "559 passed in 2.15s" (pytest -q, all green)
PYTEST_Q_PASS = re.compile(
    r"^(?P<passed>\d+) passed(?: in (?P<seconds>[\d.]+)s)?\s*$", re.MULTILINE
)
#: "2 failed, 557 passed, 1 skipped in 3.10s" (pytest -q, mixed)
#: Also tolerates trailing non-count parts ("1 warning", "12 deselected")
#: that follow a warnings-summary section (spec §12 robustness list).
PYTEST_Q_FAIL = re.compile(
    r"^(?P<summary>(?:\d+ (?:failed|passed|skipped|errors?|warnings?|deselected)(?:, )?)+)"
    r"(?: in (?P<seconds>[\d.]+)s)?\s*$",
    re.MULTILINE,
)
_SUMMARY_PART = re.compile(r"(?P<n>\d+) (?P<kind>failed|passed|skipped|errors?|warnings?|deselected)")
#: summary parts that are not test outcomes
_IGNORED_KINDS = {"warning", "warnings", "deselected"}


def git_head_commit(repo_cwd: Optional[str] = None) -> str:
    """Full sha of the current HEAD commit."""
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        check=True, cwd=repo_cwd,
    ).stdout.strip()
    return out


def _parse_pytest_q(output: str) -> dict:
    """Parse a pytest -q summary line into counts.

    Raises FreezeEvidenceError when no recognizable summary exists — a run
    that cannot be parsed cannot be reported as evidence.
    """
    match = PYTEST_Q_FAIL.search(output) or PYTEST_Q_PASS.search(output)
    if not match:
        raise FreezeEvidenceError(
            "could not parse pytest summary from output; refusing to fabricate "
            f"test evidence. Output tail: {output[-400:]!r}"
        )
    if match.groupdict().get("summary"):
        counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
        for m in _SUMMARY_PART.finditer(match.group("summary")):
            kind = "error" if m.group("kind") in ("error", "errors") else m.group("kind")
            if kind in _IGNORED_KINDS:
                continue  # warnings/deselected are not test outcomes
            counts[kind] = int(m.group("n"))
        if counts["error"]:
            raise FreezeEvidenceError(
                f"pytest reported {counts['error']} collection errors; not freeze evidence"
            )
        return counts, _seconds(match)
    counts = {"passed": int(match.group("passed")), "failed": 0, "skipped": 0, "error": 0}
    return counts, _seconds(match)


def _seconds(match: re.Match) -> float:
    raw = match.groupdict().get("seconds")
    return float(raw) if raw else 0.0


def capture_test_evidence(
    command: Sequence[str],
    success_pattern: "re.Pattern[str]",
    expected_commit: str,
    cwd: Optional[str] = None,
    timeout_seconds: int = 600,
    evidence_label: str = "LOCAL TEST EVIDENCE",
) -> TestEvidence:
    """Run the command and capture truthful results, or raise (fail closed).

    ``success_pattern`` is the caller's declaration of what a passing run
    looks like in output terms; a run that exits 0 but doesn't match is
    treated as a capture failure, not a pass.
    """
    started = time.monotonic()
    # stdin detached + isolated env so a nested pytest run cannot inherit the
    # caller's capture machinery or wait on interactive input (Windows
    # nested-pytest deadlock guard).
    env = {k: v for k, v in __import__('os').environ.items()
           if k not in ('PYTEST_CURRENT_TEST', 'PYTEST_VERSION')}
    result = subprocess.run(
        list(command), capture_output=True, text=True, cwd=cwd,
        timeout=timeout_seconds, stdin=subprocess.DEVNULL, env=env,
    )
    duration = time.monotonic() - started
    output_tail = (result.stdout + "\n" + result.stderr)[-2000:]
    if result.returncode != 0:
        raise FreezeEvidenceError(
            f"test command {command} exited {result.returncode}; not freeze evidence. "
            f"Tail: {output_tail!r}"
        )
    if not success_pattern.search(result.stdout):
        raise FreezeEvidenceError(
            f"test output did not match expected success pattern; refusing to "
            f"fabricate evidence. Tail: {output_tail!r}"
        )
    counts, parsed_seconds = _parse_pytest_q(result.stdout)
    if parsed_seconds:
        duration = parsed_seconds
    actual_commit = git_head_commit(cwd)
    if actual_commit != expected_commit:
        raise FreezeEvidenceError(
            f"tested commit {actual_commit[:12]}… differs from expected "
            f"{expected_commit[:12]}…; refusing to attribute results to the wrong commit"
        )
    if counts["failed"] or counts.get("error"):
        raise FreezeEvidenceError(f"test run reports failures: {counts}")
    from datetime import datetime, timezone

    return TestEvidence(
        collected=counts["passed"] + counts["failed"] + counts["skipped"],
        passed=counts["passed"],
        failed=counts["failed"],
        skipped=counts["skipped"],
        duration_seconds=duration,
        command=list(command),
        evidence_label=evidence_label,
        executed_at=datetime.now(timezone.utc).isoformat(),
        tested_commit=actual_commit,
    )


def write_test_results_block(evidence: TestEvidence, target_path: str) -> dict:
    """Return the canonical ``test_results`` manifest block for a freeze."""
    return evidence.as_manifest_block()
