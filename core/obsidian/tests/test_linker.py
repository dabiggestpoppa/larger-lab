"""
Tests for Linker — Phase 0C
"""

import pytest
from pathlib import Path
from core.obsidian.linker import Linker
from core.obsidian.vault_writer import VaultWriter


@pytest.fixture
def tmp_linker(tmp_path):
    """Create a Linker with a temp vault containing sample notes."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    writer = VaultWriter(vault_path=vault)

    # Create sample notes
    writer.write_note("failures", "State Reset Bug", {
        "cause": "entry_price cleared before archival",
        "fix": "snapshot before reset",
        "result": "trade continuity restored",
        "links": [],
    }, tags=["state", "reset"])

    writer.write_note("failures", "Price KeyError Bug", {
        "cause": "price key missing from state dict",
        "fix": "validate key exists before access",
        "result": "no more KeyError",
        "links": [],
    }, tags=["state", "keyerror"])

    writer.write_note("doctrine", "State Machine Pattern", {
        "cause": "need for reliable state transitions",
        "fix": "implement FSM with immutable snapshots",
        "result": "stable state management",
        "links": [],
    }, tags=["state", "pattern"])

    return Linker(vault_path=vault)


class TestScanVault:
    def test_scans_all_notes(self, tmp_linker):
        notes = tmp_linker.scan_vault()
        # Should find 3 notes (indexed by title and path)
        titles = [k for k in notes.keys() if not k.endswith(".md")]
        assert len(titles) == 3

    def test_extracts_titles(self, tmp_linker):
        notes = tmp_linker.scan_vault()
        assert "State Reset Bug" in notes
        assert "Price KeyError Bug" in notes


class TestAutoLink:
    def test_finds_related_by_tags(self, tmp_linker):
        additions = tmp_linker.auto_link(dry_run=True)
        # "State Reset Bug" and "Price KeyError Bug" share "state" tag
        assert len(additions) > 0

    def test_dry_run_doesnt_write(self, tmp_linker):
        tmp_linker.auto_link(dry_run=True)
        # Notes should be unchanged
        content = tmp_linker.writer.get_note("failures", "State Reset Bug")
        assert "[[Price KeyError Bug]]" not in content

    def test_auto_link_writes(self, tmp_linker):
        additions = tmp_linker.auto_link(dry_run=False)
        if "State Reset Bug" in additions:
            content = tmp_linker.writer.get_note("failures", "State Reset Bug")
            # Should now have links to related notes
            assert "LINKS:" in content


class TestGetRelated:
    def test_related_by_shared_tags(self, tmp_linker):
        related = tmp_linker.get_related("State Reset Bug")
        # Should find "Price KeyError Bug" (shared "state" tag)
        assert "Price KeyError Bug" in related

    def test_nonexistent_title(self, tmp_linker):
        related = tmp_linker.get_related("Does Not Exist")
        assert related == []


class TestBuildGraph:
    def test_builds_graph(self, tmp_linker):
        # First add some links
        tmp_linker.writer.write_note("failures", "Linked Bug A", {
            "cause": "test", "fix": "test", "result": "test",
            "links": ["Linked Bug B"],
        })
        tmp_linker.writer.write_note("failures", "Linked Bug B", {
            "cause": "test", "fix": "test", "result": "test",
            "links": ["Linked Bug A"],
        })

        graph = tmp_linker.build_graph()
        assert "Linked Bug A" in graph
        assert "Linked Bug B" in graph["Linked Bug A"]

    def test_bidirectional_edges(self, tmp_linker):
        tmp_linker.writer.write_note("failures", "Node X", {
            "cause": "test", "fix": "test", "result": "test",
            "links": ["Node Y"],
        })
        tmp_linker.writer.write_note("failures", "Node Y", {
            "cause": "test", "fix": "test", "result": "test",
            "links": [],
        })

        graph = tmp_linker.build_graph()
        assert "Node Y" in graph["Node X"]
        assert "Node X" in graph["Node Y"]


class TestGraphMermaid:
    def test_generates_mermaid(self, tmp_linker):
        tmp_linker.writer.write_note("failures", "Mermaid A", {
            "cause": "test", "fix": "test", "result": "test",
            "links": ["Mermaid B"],
        })
        tmp_linker.writer.write_note("failures", "Mermaid B", {
            "cause": "test", "fix": "test", "result": "test",
            "links": [],
        })

        tmp_linker.build_graph()
        mermaid = tmp_linker.get_graph_mermaid()
        assert "graph LR" in mermaid
        assert "Mermaid_A" in mermaid
        assert "Mermaid_B" in mermaid


class TestStats:
    def test_stats(self, tmp_linker):
        stats = tmp_linker.get_stats()
        assert stats["total_notes"] == 3
        assert "avg_links_per_note" in stats
        assert "isolated_notes" in stats
