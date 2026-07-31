# Test Vault Writer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Tests for Vault Writer — Phase 0A
"""

import pytest
from pathlib import Path

from core.obsidian.vault_writer import VaultWriter, VALID_CATEGORIES


@pytest.fixture
def tmp_vault(tmp_path):
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return vault


@pytest.fixture
def writer(tmp_vault):
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
        content = {"cause": "entry_price cleared", "fix": "snapshot", "result": "restored", "links": ["Systems"]}
        result = writer.write_note("failures", "State Reset Bug", content)
        assert result["title"] == "State Reset Bug"
        assert result["category"] == "failures"
        assert (tmp_vault / result["path"]).exists()
        text = (tmp_vault / result["path"]).read_text(encoding="utf-8")
        assert "# State Reset Bug" in text
        assert "CAUSE:" in text
        assert "[[Systems]]" in text

    def test_write_note_with_tags(self, writer):
        content = {"cause": "t", "fix": "t", "result": "t", "links": []}
        result = writer.write_note("failures", "Tagged", content, tags=["state", "reset"])
        assert result["tags"] == ["state", "reset"]

    def test_write_note_with_subcategory(self, writer, tmp_vault):
        content = {"cause": "t", "fix": "t", "result": "t", "links": []}
        result = writer.write_note("agents", "Quant Report", content, subcategory="quant")
        assert "agents" in result["path"] and "quant" in result["path"]
        assert (tmp_vault / result["path"]).exists()

    def test_invalid_category_raises(self, writer):
        with pytest.raises(ValueError, match="Invalid category"):
            writer.write_note("invalid", "Test", {"cause": "t"})

    def test_minimal_content(self, writer):
        result = writer.write_note("failures", "Minimal", {"cause": "broke"})
        text = (writer.vault_path / result["path"]).read_text(encoding="utf-8")
        assert "CAUSE:" in text
        assert "FIX:" not in text

    def test_sanitize_filename(self, writer):
        result = writer.write_note("failures", "Bug: @#$%", {"cause": "t"})
        assert "@" not in result["path"]
        assert "#" not in result["path"]

    def test_write_returns_metadata(self, writer):
        result = writer.write_note("failures", "Meta", {"cause": "t"})
        assert all(k in result for k in ["id", "title", "path", "category", "modified"])


class TestGetNote:
    def test_get_existing_note(self, writer):
        writer.write_note("failures", "Readable", {"cause": "test cause", "fix": "f", "result": "r", "links": []})
        note = writer.get_note("failures", "Readable")
        assert note is not None
        assert note["title"] == "Readable"
        assert "test cause" in note["content"]

    def test_get_nonexistent_note(self, writer):
        assert writer.get_note("failures", "Nope") is None

    def test_get_note_with_subcategory(self, writer):
        writer.write_note("agents", "Sub", {"cause": "t", "fix": "f", "result": "r", "links": []}, subcategory="quant")
        note = writer.get_note("agents", "Sub", subcategory="quant")
        assert note is not None


class TestListNotes:
    def test_list_all_notes(self, writer):
        c = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "A", c)
        writer.write_note("failures", "B", c)
        writer.write_note("doctrine", "C", c)
        assert len(writer.list_notes()) == 3

    def test_list_category_filter(self, writer):
        c = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "A", c)
        writer.write_note("doctrine", "B", c)
        notes = writer.list_notes(category="failures")
        assert len(notes) == 1
        assert notes[0]["category"] == "failures"

    def test_list_returns_metadata(self, writer):
        writer.write_note("failures", "Meta", {"cause": "t", "fix": "f", "result": "r", "links": ["X"]}, tags=["t"])
        notes = writer.list_notes()
        assert len(notes) == 1
        n = notes[0]
        assert "id" in n and "title" in n and "category" in n
        assert "t" in n["tags"] and "X" in n["links"]


class TestSearchNotes:
    def test_search_by_title(self, writer):
        c = {"cause": "t", "fix": "f", "result": "r", "links": []}
        writer.write_note("failures", "UniqueXYZ", c)
        writer.write_note("failures", "Other", c)
        results = writer.search_notes(query="UniqueXYZ")
        assert len(results) == 1

    def test_search_by_content(self, writer):
        writer.write_note("failures", "Content", {"cause": "needle_in_haystack", "fix": "f", "result": "r", "links": []})
        results = writer.search_notes(query="needle_in_haystack")
        assert len(results) >= 1

    def test_search_with_category(self, writer):
        c = {"cause": "shared", "fix": "f", "result": "r", "links": []}
        writer.write_note("failures", "F", c)
        writer.write_note("doctrine", "D", c)
        results = writer.search_notes(query="shared", category="failures")
        assert all(n["category"] == "failures" for n in results)


class TestListCategories:
    def test_list_categories(self, writer):
        cats = writer.list_categories()
        assert "failures" in cats and "doctrine" in cats and "skills" in cats


class TestUpdateNote:
    def test_update_existing(self, writer):
        writer.write_note("failures", "UpdateMe", {"cause": "old", "fix": "old", "result": "old", "links": []})
        result = writer.update_note("failures", "UpdateMe", {"cause": "new", "fix": "new", "result": "new", "links": []})
        note = writer.get_note("failures", "UpdateMe")
        assert "new" in note["content"]
        assert "old" not in note["content"]


class TestDeleteNote:
    def test_delete_existing(self, writer):
        writer.write_note("failures", "DeleteMe", {"cause": "t", "fix": "f", "result": "r", "links": []})
        assert writer.delete_note("failures", "DeleteMe") is True
        assert writer.get_note("failures", "DeleteMe") is None

    def test_delete_nonexistent(self, writer):
        assert writer.delete_note("failures", "Nope") is False


class TestNoteExists:
    def test_exists(self, writer):
        writer.write_note("failures", "Exists", {"cause": "t", "fix": "f", "result": "r", "links": []})
        assert writer.note_exists("failures", "Exists") is True

    def test_not_exists(self, writer):
        assert writer.note_exists("failures", "Nope") is False

```

LINKS:
[[Agents]]
[[Test Manual]]
[[Api Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Oc2 Vault Access Guide]]
[[Ontology Core Summary]]
[[Pm2 Test Note]]
[[Sage Audit Environment Utilization]]
[[Test Note]]
[[Test Pattern]]
[[Vault Distillation 20260531 0245]]
[[Citation Workflow]]
[[Failures]]
[[Minimal]]
[[Skill]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
