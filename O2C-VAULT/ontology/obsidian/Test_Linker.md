# Test Linker

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
﻿"""
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
        note = tmp_linker.writer.get_note("failures", "State Reset Bug")
        content = note["content"] if isinstance(note, dict) else note
        assert "[[Price KeyError Bug]]" not in content

    def test_auto_link_writes(self, tmp_linker):
        additions = tmp_linker.auto_link(dry_run=False)
        if "State Reset Bug" in additions:
            note = tmp_linker.writer.get_note("failures", "State Reset Bug")
            # Should now have links to related notes
            assert note is not None and "LINKS:
[[Telegram Gateway]]
[[Semantic State]]
[[Interpreter]]
[[Vault Writer]]
[[Test Vault Writer]]
[[Test Taxonomy]]
[[Test Pattern Crystallizer]]
[[Test Note Standard]]
[[Test Memory Distiller]]
[[Test Error Intelligence]]
[[Test Context Injector]]
[[Test Compressor]]
[[Taxonomy]]
[[Pattern Crystallizer]]
[[Note Standard]]
[[Memory Distiller]]
[[Live Sync]]
[[Linker]]
[[Knowledge Importer]]
[[Error Intelligence]]
[[Compressor]]
[[Vault]]
[[Task Intent Analyzer]]
[[Task Executor]]
[[Semantic Retrieval]]
[[Runtime Awareness]]
[[Report Return]]
[[Primary Observer]]
[[Pattern Distillation]]
[[Observer State]]
[[Observer Session]]
[[Observer Lifecycle]]
[[Observer Conversation Runtime]]
[[Graph Traversal]]
[[Event Awareness]]
[[Continuity Memory]]
[[Context Distiller]]
[[Command Router]]
[[Chat Log]]
[[Autonomous Orchestrator]]
[[Workflow Memory]]
[[Workflow Distiller]]
[[Trace Feedback]]
[[Trace Collector]]
[[Topology Learning]]
[[Test Loader]]
[[Test Journal]]
[[Temporal Graph]]
[[Task Classifier]]
[[Synthesizer]]
[[Structural Anchor]]
[[Spawn Replay]]
[[Spawn Registry]]
[[Spawn Planner]]
[[Spawn Blueprint]]
[[Runtime Heartbeat]]
[[Routing Learning]]
[[Routing Consensus]]
[[Recovery Persistence]]
[[Persistent Scheduler]]
[[Persistent Runtime]]
[[Pattern Memory]]
[[Passive Awareness]]
[[Operational Scoring]]
[[Operational Replay]]
[[Operational Drift Detect]]
[[Openrouter Gateway]]
[[Observer Specialization]]
[[Observer Registry]]
[[Observer Persistence]]
[[Observer Evolution]]
[[Observer Consensus]]
[[Observability Stress]]
[[Multi Agent Coordinator]]
[[Model Selector]]
[[Metrics]]
[[Long Horizon Memory]]
[[Loader]]
[[Journal]]
[[Indicators]]
[[Failure Analyzer]]
[[Execution Boundary]]
[[Event Schema]]
[[Environmental Monitor]]
[[Dormant State Manager]]
[[Data Fetcher]]
[[Continuity Preserver]]
[[Context Injector]]
[[Consensus Replay]]
[[Consensus Memory]]
[[Complexity Scorer]]
[[Capability Matcher]]
[[Autonomous Repair]]
[[Attractor Analysis]]
[[Agent Spawner]]
[[Agent Lifecycle]]
[[Adaptation Engine]]
[[Two Plays Engine]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V5]]
[[Symmetry Trap V4]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Engine]]
[[Stall Harvest Cfd Engine]]
[[Shared]]
[[P90 Strategy]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine]]
[[Naut Asset Config]]
[[Dual Engine]]
[[Dmr Strategy]]
[[Diag V5]]
[[Diag Option B]]
[[Debug Trace]]
[[Debug St]]
[[Debug One Day]]
[[Debug Days]]
[[Constraint Anchor Engine]]
[[Cerebus Resolution Engine]]
[[Blind Chain V3]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V2 Debug]]
[[Blind Chain Exact]]
[[Blind Chain Engine]]
[[Blind Chain Diag]]
[[Blind Chain Debug]]
[[Atomic Sym Trap]]
[[Symmetry Trap Monte Carlo]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap]]
[[St Batch Runner]]
[[St Batch2 Runner]]
[[Run Top5 Backtest Mc]]
[[Run St Multi Asset]]
[[Run Majors Backtest]]
[[P90 Usdchf Backtest]]
[[P90 Trace Trades]]
[[P90 Gap Check]]
[[P90 Engine Dmr]]
[[P90 Engine]]
[[P90 Dmr Overlay Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Backtest]]
[[P90 Count Ews]]
[[P90 Backtest]]
[[Dmr Standalone Backtest]]
[[Convergence Indicator]]
[[Asset Configs]]
[[Failures]]
[[Citation Workflow]]
[[Test Pattern]]
[[Test Note]]
[[Sage Audit Environment Utilization]]
[[Pm2 Test Note]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Test]]
[[Api Test Note]]
[[Test Manual]]" in note["content"]


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

```