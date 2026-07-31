# Test Pattern Crystallizer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Tests for Pattern Crystallization Engine — Phase 01 Component 2
"""

import pytest
from core.obsidian.pattern_crystallizer import PatternCrystallizer


@pytest.fixture
def tmp_pc(tmp_path):
    return PatternCrystallizer(vault_path=tmp_path / "vault")


class TestExtractPatterns:
    def test_no_patterns_empty_vault(self, tmp_pc):
        patterns = tmp_pc.extract_patterns(min_occurrences=2)
        assert patterns == []

    def test_detects_recurring_tags(self, tmp_pc, tmp_path):
        vault = tmp_path / "vault"
        writer = tmp_pc.writer
        content = {"cause": "a", "fix": "b", "result": "c", "links": []}
        writer.write_note("failures", "Bug A", content, tags=["state", "reset"])
        writer.write_note("failures", "Bug B", content, tags=["state", "keyerror"])
        patterns = tmp_pc.extract_patterns(min_occurrences=2)
        tag_patterns = [p for p in patterns if p["type"] == "recurring_tag"]
        assert len(tag_patterns) >= 1
        assert any(p["name"] == "state" for p in tag_patterns)


class TestCrystallizePattern:
    def test_crystallize(self, tmp_pc, tmp_path):
        result = tmp_pc.crystallize_pattern(
            name="Test Pattern",
            conditions=["Condition A", "Condition B"],
            result="Achieves X",
            links=["Related"],
        )
        assert result is not None
        assert result["name"] == "Test Pattern"
        assert len(result["conditions"]) == 2


class TestGetCognitivePrimitives:
    def test_get_primitives(self, tmp_pc):
        tmp_pc.crystallize_pattern(
            name="Primitive A",
            conditions=["C1"],
            result="R1",
        )
        primitives = tmp_pc.get_cognitive_primitives()
        assert len(primitives) >= 1


class TestAnalyzeCoOccurrence:
    def test_co_occurrence(self, tmp_pc):
        content = {"cause": "a", "fix": "b", "result": "c", "links": ["LinkA", "LinkB"]}
        tmp_pc.writer.write_note("doctrine", "Note A", content)
        co = tmp_pc.analyze_co_occurrence()
        assert isinstance(co, dict)

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
[[Citation Workflow]]
[[Failures]]
[[Patterns]]
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
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
