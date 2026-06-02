# Test Error Intelligence

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Tests for Error Intelligence System — Phase 01 Component 1
"""

import pytest
from core.obsidian.error_intelligence import ErrorIntelligence, ERROR_CATEGORIES, ERROR_PATTERNS


@pytest.fixture
def tmp_ei(tmp_path):
    return ErrorIntelligence(vault_path=tmp_path / "vault")


SAMPLE_KEYERROR = """
Traceback (most recent call last):
  File "trading.py", line 42, in execute_trade
    entry_price = state['price']
KeyError: 'price'
"""

SAMPLE_IMPORTERROR = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    from core.semantic.interpret import interpret
ModuleNotFoundError: No module named 'core.semantic.interpret'
"""


class TestClassifyError:
    def test_classify_keyerror(self, tmp_ei):
        category, cause = tmp_ei.classify_error(SAMPLE_KEYERROR)
        assert category == "data_validation"
        assert "key" in cause.lower() or "dictionary" in cause.lower()

    def test_classify_importerror(self, tmp_ei):
        category, cause = tmp_ei.classify_error(SAMPLE_IMPORTERROR)
        assert category == "import_error"

    def test_classify_unknown(self, tmp_ei):
        category, cause = tmp_ei.classify_error("Some random error text")
        assert category == "unknown"

    def test_classify_routing(self, tmp_ei):
        category, cause = tmp_ei.classify_error("routing consensus failed")
        assert category == "routing"


class TestIndexError:
    def test_index_creates_note(self, tmp_ei, tmp_path):
        result = tmp_ei.index_error(
            traceback=SAMPLE_KEYERROR,
            context="Trade execution failed",
            fix_applied="Added key validation",
            result="Trade executes correctly",
        )
        assert result is not None
        assert "error_type" in result
        assert result["error_type"] == "KeyError"
        assert result["category"] == "data_validation"

    def test_index_auto_classifies(self, tmp_ei):
        result = tmp_ei.index_error(traceback=SAMPLE_KEYERROR)
        assert result["category"] == "data_validation"

    def test_index_with_custom_category(self, tmp_ei):
        result = tmp_ei.index_error(
            traceback=SAMPLE_KEYERROR,
            category="execution",
        )
        assert result["category"] == "execution"


class TestFindSimilarErrors:
    def test_find_similar(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        results = tmp_ei.find_similar_errors("KeyError")
        assert len(results) >= 1

    def test_find_by_tag(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        results = tmp_ei.find_similar_errors("data_validation")
        assert len(results) >= 1


class TestGetErrorPatterns:
    def test_patterns(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test")
        tmp_ei.index_error(SAMPLE_IMPORTERROR, context="test")
        patterns = tmp_ei.get_error_patterns()
        assert patterns["total_errors"] >= 2
        assert "by_category" in patterns
        assert "by_type" in patterns


class TestGetPreventionRules:
    def test_prevention_rules(self, tmp_ei):
        tmp_ei.index_error(SAMPLE_KEYERROR, context="test", fix_applied="Validate keys")
        rules = tmp_ei.get_prevention_rules()
        assert len(rules) >= 1


class TestErrorCategories:
    def test_all_categories_valid(self):
        assert "routing" in ERROR_CATEGORIES
        assert "memory" in ERROR_CATEGORIES
        assert "execution" in ERROR_CATEGORIES
        assert "import_error" in ERROR_CATEGORIES

    def test_error_patterns_complete(self):
        assert "KeyError" in ERROR_PATTERNS
        assert "ImportError" in ERROR_PATTERNS
        assert "ModuleNotFoundError" in ERROR_PATTERNS

```

LINKS:
[[Cg 4 Execution Intelligence]]
[[Cg 5 Continuity Intelligence]]
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
[[Cal]]
[[Citation Workflow]]
[[Patterns]]
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
[[Memory]]
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
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
