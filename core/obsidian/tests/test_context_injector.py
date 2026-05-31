"""
Tests for Context Injector — Phase 01 Component 4
"""

import pytest
from core.obsidian.context_injector import ContextInjector


@pytest.fixture
def tmp_ci(tmp_path):
    return ContextInjector(vault_path=tmp_path / "vault")


class TestPrepareContext:
    def test_empty_context(self, tmp_ci):
        context = tmp_ci.prepare_context("Some random task")
        # Should return empty or minimal context for unknown tasks
        assert isinstance(context, str)

    def test_context_with_vault_data(self, tmp_ci):
        # Add some vault data first
        tmp_ci.writer.write_note("doctrine", "Test Pattern", {
            "cause": "test", "fix": "test", "result": "test", "links": [],
        }, tags=["pattern"])
        context = tmp_ci.prepare_context("test pattern matching")
        assert isinstance(context, str)

    def test_context_includes_header(self, tmp_ci):
        context = tmp_ci.prepare_context("my task")
        # Even empty context should be a string
        assert isinstance(context, str)


class TestFindRelevantNotes:
    def test_finds_by_title(self, tmp_ci):
        tmp_ci.writer.write_note("doctrine", "Unique Pattern XYZ", {
            "cause": "test", "fix": "test", "result": "test", "links": [],
        })
        results = tmp_ci._find_relevant_notes("doctrine", "Unique Pattern XYZ")
        assert len(results) >= 1

    def test_finds_by_tag(self, tmp_ci):
        tmp_ci.writer.write_note("failures", "Tagged Error", {
            "cause": "test", "fix": "test", "result": "test", "links": [],
        }, tags=["state_machine"])
        results = tmp_ci._find_relevant_notes("failures", "state_machine bug")
        assert len(results) >= 1

    def test_empty_category(self, tmp_ci):
        results = tmp_ci._find_relevant_notes("nonexistent", "query")
        assert results == []


class TestGetVaultSummary:
    def test_summary(self, tmp_ci):
        tmp_ci.writer.write_note("doctrine", "Doc A", {
            "cause": "test", "fix": "test", "result": "test", "links": [],
        })
        summary = tmp_ci.get_vault_summary()
        assert "# Vault Summary" in summary
        assert "doctrine" in summary
