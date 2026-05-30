"""
Tests for Vault Writer — Phase 0A
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from core.obsidian.vault_writer import VaultWriter, VALID_CATEGORIES


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return vault


@pytest.fixture
def writer(tmp_vault):
    """Create a VaultWriter with temp vault."""
    return VaultWriter(vault_path=tmp_vault)


class TestVaultWriterInit:
    def test_creates_vault_structure(self, tmp_vault):
        writer = VaultWriter(vault_path=tmp_vault)
        for dir_path in ["failures", "doctrine", "skills", "agents/quant"]:
            assert (tmp_vault / dir_path).is_dir()

    def test_default_vault_path(self):
        writer = VaultWriter()
        assert writer.vault_path.exists()


class TestWriteNote:
    def test_write_basic_note(self, writer, tmp_vault):
        content = {
            "cause": "entry_price cleared before archival",
            "fix": "snapshot before reset",
            "result": "trade continuity restored",
            "links": ["Trading Systems", "State Machines"],
        }
        path = writer.write_note("failures", "State Reset Bug", content)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "# State Reset Bug" in text
        assert "CAUSE:" in text
        assert "entry_price cleared before archival" in text
        assert "FIX:" in text
        assert "snapshot before reset" in text
        assert "RESULT:" in text
        assert "trade continuity restored" in text
        assert "[[Trading Systems]]" in text
        assert "[[State Machines]]" in text

    def test_write_note_with_tags(self, writer):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        path = writer.write_note("failures", "Tagged Bug", content, tags=["state", "reset"])
        text = path.read_text(encoding="utf-8")
        assert "#state" in text
        assert "#reset" in text

    def test_write_note_with_subcategory(self, writer, tmp_vault):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        path = writer.write_note("agents", "Quant Agent Report", content, subcategory="quant")
        assert path.exists()
        assert "agents" in str(path) and "quant" in str(path)

    def test_invalid_category_raises(self, writer):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        with pytest.raises(ValueError, match="Invalid category"):
            writer.write_note("invalid_category", "Test", content)

    def test_minimal_content(self, writer):
        content = {"cause": "something broke"}
        path = writer.write_note("failures", "Minimal Bug", content)
        text = path.read_text(encoding="utf-8")
        assert "# Minimal Bug" in text
        assert "CAUSE:" in text
        assert "FIX:" not in text  # No fix provided, should not appear

    def test_sanitize_filename(self, writer):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        path = writer.write_note("failures", "Bug: State/Reset @#$%", content)
        assert path.exists()
        # Special chars should be removed
        assert "@" not in path.name
        assert "#" not in path.name


class TestGetNote:
    def test_get_existing_note(self, writer):
        content = {"cause": "test cause", "fix": "test fix", "result": "test result", "links": []}
        writer.write_note("failures", "Readable Bug", content)
        text = writer.get_note("failures", "Readable Bug")
        assert text is not None
        assert "test cause" in text

    def test_get_nonexistent_note(self, writer):
        result = writer.get_note("failures", "Does Not Exist")
        assert result is None


class TestListNotes:
    def test_list_all_notes(self, writer):
        content = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "Bug A", content)
        writer.write_note("failures", "Bug B", content)
        writer.write_note("doctrine", "Doctrine A", content)
        notes = writer.list_notes()
        assert len(notes) == 3

    def test_list_category_notes(self, writer):
        content = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "Bug A", content)
        writer.write_note("failures", "Bug B", content)
        writer.write_note("doctrine", "Doctrine A", content)
        notes = writer.list_notes("failures")
        assert len(notes) == 2


class TestNoteExists:
    def test_exists(self, writer):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        writer.write_note("failures", "Existing Bug", content)
        assert writer.note_exists("failures", "Existing Bug") is True

    def test_not_exists(self, writer):
        assert writer.note_exists("failures", "Nonexistent Bug") is False


class TestUpdateNote:
    def test_update_existing(self, writer):
        content1 = {"cause": "old cause", "fix": "old fix", "result": "old result", "links": []}
        writer.write_note("failures", "Updatable Bug", content1)

        content2 = {"cause": "new cause", "fix": "new fix", "result": "new result", "links": []}
        path = writer.update_note("failures", "Updatable Bug", content2)
        text = path.read_text(encoding="utf-8")
        assert "new cause" in text
        assert "old cause" not in text


class TestDeleteNote:
    def test_delete_existing(self, writer):
        content = {"cause": "test", "fix": "test", "result": "test", "links": []}
        writer.write_note("failures", "Deletable Bug", content)
        assert writer.note_exists("failures", "Deletable Bug")
        result = writer.delete_note("failures", "Deletable Bug")
        assert result is True
        assert not writer.note_exists("failures", "Deletable Bug")

    def test_delete_nonexistent(self, writer):
        result = writer.delete_note("failures", "Nonexistent Bug")
        assert result is False


class TestValidCategories:
    def test_all_expected_categories(self):
        expected = {"failures", "doctrine", "skills", "agents", "memory", "ontology",
                     "graphs", "journals", "execution", "heuristics", "routing", "architecture"}
        assert expected.issubset(set(VALID_CATEGORIES))
