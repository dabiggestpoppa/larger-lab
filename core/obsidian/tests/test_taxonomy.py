"""
Tests for Taxonomy — Phase 0H
"""

import pytest
from pathlib import Path
from core.obsidian.taxonomy import Taxonomy, REQUIRED_DIRS, CATEGORY_RULES


@pytest.fixture
def tmp_taxonomy(tmp_path):
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return Taxonomy(vault_path=vault)


class TestValidate:
    def test_missing_directories_detected(self, tmp_taxonomy, tmp_path):
        issues = tmp_taxonomy.validate()
        missing = [i for i in issues if i["type"] == "missing_directory"]
        # Should detect all required dirs as missing
        assert len(missing) == len(REQUIRED_DIRS)

    def test_orphan_file_detected(self, tmp_taxonomy, tmp_path):
        # Create a file in vault root
        orphan = tmp_path / "test-vault" / "orphan.md"
        orphan.write_text("# Orphan\nSome content", encoding="utf-8")
        issues = tmp_taxonomy.validate()
        orphans = [i for i in issues if i["type"] == "orphan_file"]
        assert len(orphans) == 1

    def test_unknown_directory_detected(self, tmp_taxonomy, tmp_path):
        unknown = tmp_path / "test-vault" / "unknown_dir"
        unknown.mkdir()
        issues = tmp_taxonomy.validate()
        unknowns = [i for i in issues if i["type"] == "unknown_directory"]
        assert len(unknowns) == 1


class TestEnforce:
    def test_creates_missing_directories(self, tmp_taxonomy, tmp_path):
        actions = tmp_taxonomy.enforce()
        assert len(actions) > 0
        # Verify directories were created
        for dir_name in REQUIRED_DIRS:
            assert (tmp_path / "test-vault" / dir_name).exists()


class TestGetCategoryForNote:
    def test_classifies_failure(self, tmp_taxonomy):
        cat = tmp_taxonomy.get_category_for_note("Bug Report", "This error failed because of a traceback")
        assert cat == "failures"

    def test_classifies_heuristic(self, tmp_taxonomy):
        cat = tmp_taxonomy.get_category_for_note("Quick Rule", "This is a heuristic pattern")
        assert cat == "heuristics"

    def test_classifies_skill(self, tmp_taxonomy):
        cat = tmp_taxonomy.get_category_for_note("How To Guide", "This skill procedure shows how to")
        assert cat == "skills"

    def test_default_is_doctrine(self, tmp_taxonomy):
        cat = tmp_taxonomy.get_category_for_note("Random Note", "Some general content")
        assert cat == "doctrine"


class TestGetStats:
    def test_empty_vault(self, tmp_taxonomy):
        stats = tmp_taxonomy.get_stats()
        assert stats["total"] == 0

    def test_counts_notes(self, tmp_taxonomy, tmp_path):
        vault = tmp_path / "test-vault"
        (vault / "failures").mkdir(parents=True, exist_ok=True)
        (vault / "failures" / "bug1.md").write_text("# Bug", encoding="utf-8")
        (vault / "failures" / "bug2.md").write_text("# Bug", encoding="utf-8")
        (vault / "doctrine").mkdir(parents=True, exist_ok=True)
        (vault / "doctrine" / "doc1.md").write_text("# Doc", encoding="utf-8")
        stats = tmp_taxonomy.get_stats()
        assert stats["total"] == 3
        assert stats["failures"] == 2
        assert stats["doctrine"] == 1
