"""P1-R1-I0 — freeze-evidence capture tests (spec §12 items 1–4)."""

from __future__ import annotations

import re

import pytest

from qcae.implementation.tools import test_evidence
from qcae.implementation.tools.test_evidence import (
    FreezeEvidenceError,
    PYTEST_Q_FAIL,
    capture_test_evidence,
    git_head_commit,
)


class TestParsing:
    def test_parses_all_green_summary(self) -> None:
        counts, _ = test_evidence._parse_pytest_q("559 passed in 2.15s\n")
        assert counts == {"passed": 559, "failed": 0, "skipped": 0, "error": 0}

    def test_parses_mixed_summary(self) -> None:
        counts, _ = test_evidence._parse_pytest_q("2 failed, 557 passed, 1 skipped in 3.10s\n")
        assert counts == {"passed": 557, "failed": 2, "skipped": 1, "error": 0}

    def test_unparseable_output_refused(self) -> None:
        with pytest.raises(FreezeEvidenceError, match="could not parse"):
            test_evidence._parse_pytest_q("something went wrong, no summary here")

    def test_error_summary_refused(self) -> None:
        with pytest.raises(FreezeEvidenceError, match="collection errors"):
            test_evidence._parse_pytest_q("3 errors in 0.5s\n")


class TestFailClosed:
    def _run(self, monkeypatch, returncode=0, stdout="559 passed in 1.00s\n",
             commit="a" * 40, expected="a" * 40):
        import subprocess

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompleted(returncode, stdout))
        monkeypatch.setattr(test_evidence, "git_head_commit", lambda cwd=None: commit)
        return capture_test_evidence(
            command=["python", "-m", "pytest", "-q"],
            success_pattern=PYTEST_Q_FAIL,
            expected_commit=expected,
        )

    def test_real_passing_run_captured(self, monkeypatch) -> None:
        evidence = self._run(monkeypatch)
        assert evidence.passed == 559
        assert evidence.failed == 0
        assert evidence.evidence_label == "LOCAL TEST EVIDENCE"
        block = evidence.as_manifest_block()
        assert block["passed_is_placeholder"] is False
        assert block["command"] == ["python", "-m", "pytest", "-q"]

    def test_failed_command_cannot_create_pass(self, monkeypatch) -> None:
        with pytest.raises(FreezeEvidenceError, match="exited 1"):
            self._run(monkeypatch, returncode=1, stdout="2 failed, 557 passed in 1s\n")

    def test_failing_counts_cannot_create_pass(self, monkeypatch) -> None:
        with pytest.raises(FreezeEvidenceError, match="reports failures"):
            self._run(monkeypatch, stdout="2 failed, 557 passed in 1s\n")

    def test_unparseable_output_cannot_create_pass(self, monkeypatch) -> None:
        with pytest.raises(FreezeEvidenceError, match="did not match expected success"):
            self._run(monkeypatch, stdout="garbage output")

    def test_commit_mismatch_refused(self, monkeypatch) -> None:
        with pytest.raises(FreezeEvidenceError, match="differs from expected"):
            self._run(monkeypatch, commit="b" * 40, expected="a" * 40)


class _FakeCompleted:
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


class TestRealCapture:
    def test_actual_capture_end_to_end(self) -> None:
        """The helper captures a real pytest run truthfully (spec item 1).

        Targets a small fixed module: invoking the whole suite from inside a
        test would recurse (suite contains this test). The full-suite capture
        happens in the freeze generator, outside pytest.
        """
        head = git_head_commit()
        evidence = capture_test_evidence(
            command=["python", "-m", "pytest", "qcae/tests/unit/test_p0_serialization.py", "-q"],
            success_pattern=PYTEST_Q_FAIL,
            expected_commit=head,
            timeout_seconds=120,
        )
        assert evidence.failed == 0
        assert evidence.passed > 0
        assert evidence.tested_commit == head
        assert evidence.command[-2].endswith("test_p0_serialization.py")
        block = evidence.as_manifest_block()
        assert set(block) == {
            "collected", "passed", "passed_is_placeholder", "failed", "skipped",
            "duration_seconds", "command", "evidence_label", "executed_at",
            "tested_commit",
        }
