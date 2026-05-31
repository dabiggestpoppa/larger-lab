"""
Tests for Memory Distillation Layer — Phase 01 Component 3
"""

import pytest
from core.obsidian.memory_distiller import MemoryDistiller


@pytest.fixture
def tmp_md(tmp_path):
    return MemoryDistiller(vault_path=tmp_path / "vault")


class TestDistillSession:
    def test_distill_basic(self, tmp_md):
        entries = [
            {"step": "load_data", "result": "success", "details": "Loaded CSV"},
            {"step": "process", "result": "failed", "details": "Parse error"},
            {"step": "retry", "result": "success", "details": "Retry succeeded"},
        ]
        result = tmp_md.distill_session(agent_name="TestAgent", task="Test task", journal_entries=entries)
        assert result is not None
        assert result["agent"] == "TestAgent"
        assert result["total_steps"] == 3
        assert result["successes"] == 2
        assert result["failures"] == 1

    def test_distill_all_success(self, tmp_md):
        entries = [
            {"step": "a", "result": "success"},
            {"step": "b", "result": "success"},
        ]
        result = tmp_md.distill_session(agent_name="A", task="T", journal_entries=entries)
        assert result["successes"] == 2
        assert result["failures"] == 0

    def test_distill_with_corrections(self, tmp_md):
        entries = [
            {"step": "a", "result": "failed"},
            {"step": "correction", "result": "correction", "details": "Fixed A"},
        ]
        result = tmp_md.distill_session(agent_name="A", task="T", journal_entries=entries)
        assert result["corrections"] == 1


class TestDistillFromVault:
    def test_distill_empty_vault(self, tmp_md):
        result = tmp_md.distill_from_vault(days=7)
        assert result is not None
        assert result["days"] == 7
        assert result["executions_analyzed"] == 0
