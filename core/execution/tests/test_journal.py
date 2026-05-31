"""
Tests for Execution Journal — Phase 0F
"""

import pytest
from pathlib import Path
from core.execution.journal import ExecutionJournal


@pytest.fixture
def tmp_journal(tmp_path):
    return ExecutionJournal(
        agent_name="TestAgent",
        task="Test task",
        vault_path=tmp_path / "vault",
    )


class TestLogStep:
    def test_log_success(self, tmp_journal):
        tmp_journal.log_step("step1", "success", details="Done")
        assert len(tmp_journal.steps) == 1
        assert tmp_journal.steps[0]["step"] == "step1"
        assert tmp_journal.steps[0]["result"] == "success"

    def test_log_failure(self, tmp_journal):
        tmp_journal.log_step("step2", "failed", details="Error")
        assert len(tmp_journal._failures) == 1
        assert "step2" in tmp_journal._failures

    def test_multiple_steps(self, tmp_journal):
        tmp_journal.log_step("a", "success")
        tmp_journal.log_step("b", "failed")
        tmp_journal.log_step("c", "success")
        assert len(tmp_journal.steps) == 3
        assert len(tmp_journal._successes) == 2
        assert len(tmp_journal._failures) == 1


class TestLogCorrection:
    def test_log_correction(self, tmp_journal):
        tmp_journal.log_correction("failed_step", "retry with timeout", "success")
        assert len(tmp_journal._corrections) == 1
        assert tmp_journal._corrections[0]["failed_step"] == "failed_step"


class TestSummarize:
    def test_summary(self, tmp_journal):
        tmp_journal.log_step("a", "success")
        tmp_journal.log_step("b", "failed")
        tmp_journal.log_step("c", "success")
        summary = tmp_journal.summarize()
        assert summary["agent"] == "TestAgent"
        assert summary["total_steps"] == 3
        assert summary["successes"] == 2
        assert summary["failures"] == 1
        assert summary["success_rate"] == 0.67


class TestToMarkdown:
    def test_markdown_output(self, tmp_journal):
        tmp_journal.log_step("load", "success", "Data loaded")
        tmp_journal.log_step("process", "failed", "Parse error")
        tmp_journal.log_correction("process", "retry", "success")
        md = tmp_journal.to_markdown()
        assert "# Agent Execution Report" in md
        assert "TestAgent" in md
        assert "Failures" in md
        assert "Corrections" in md
        assert "| Step | Result |" in md


class TestCompressAndSave:
    def test_saves_to_vault(self, tmp_journal, tmp_path):
        tmp_journal.log_step("test", "success")
        path = tmp_journal.compress_and_save()
        assert path.exists()


class TestToJson:
    def test_json_output(self, tmp_journal):
        tmp_journal.log_step("test", "success")
        json_str = tmp_journal.to_json()
        assert "TestAgent" in json_str
        assert "test" in json_str
