# Test Taxonomy

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
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

```

LINKS:
[[Test Manual]]
[[Api Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Pm2 Test Note]]
[[Sage Audit Environment Utilization]]
[[Test Note]]
[[Test Pattern]]
[[Action]]
[[Bug Report]]
[[Citation Workflow]]
[[Failures]]
[[Gates Taxonomy]]
[[Heuristics]]
[[Issue Taxonomy]]
[[Skill]]
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
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
