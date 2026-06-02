# Test Compressor

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Tests for Compressor — Phase 0B
"""

import pytest
from core.obsidian.compressor import compress_trace, extract_signal, is_noise, filter_noise


SAMPLE_TRACEBACK = """
Traceback (most recent call last):
  File "trading.py", line 42, in execute_trade
    entry_price = get_entry()
  File "trading.py", line 15, in get_entry
    return state['price']
KeyError: 'price'
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    run_trader()
KeyError: 'price'
"""


class TestCompressTrace:
    def test_basic_compression(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Trade execution failed during entry",
            fix_applied="Added price validation before entry",
            result="Trade executes correctly with validation",
        )
        assert "CAUSE:" in result
        assert "Trade execution failed during entry" in result
        assert "KeyError: 'price'" in result
        assert "FIX:" in result
        assert "Added price validation before entry" in result
        assert "RESULT:" in result
        assert "Trade executes correctly with validation" in result

    def test_extracts_error_links(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
            fix_applied="Fix",
            result="Done",
        )
        assert "[[KeyError]]" in result

    def test_no_fix_provided(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
        )
        assert "Pending verification" in result

    def test_fix_attempts_fallback(self):
        result = compress_trace(
            traceback=SAMPLE_TRACEBACK,
            context="Test",
            fix_attempts=["tried A", "tried B", "tried C"],
        )
        assert "tried C" in result  # Last attempt

    def test_deduplicates_signals(self):
        result = compress_trace(
            traceback="KeyError: 'x'\nKeyError: 'x'\nKeyError: 'x'",
            context="Test",
            fix_applied="Fix",
            result="Done",
        )
        # Should only appear once
        assert result.count("KeyError: 'x'") == 1


class TestExtractSignal:
    def test_extract_labeled_sections(self):
        text = """CAUSE:
Something broke
FIX:
Applied fix
RESULT:
Working now
LINKS:
[[Telegram Gateway]]
[[Semantic State]]
[[Interpreter]]
[[Vault Writer]]
[[Test Vault Writer]]
[[Test Taxonomy]]
[[Test Pattern Crystallizer]]
[[Test Note Standard]]
[[Test Memory Distiller]]
[[Test Linker]]
[[Test Error Intelligence]]
[[Test Context Injector]]
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
[[Citation Workflow]]
[[Cal]]
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
[[Test Manual]]
[[ErrorType]]
"""
        result = extract_signal(text)
        assert result["cause"] == "Something broke"
        assert result["fix"] == "Applied fix"
        assert result["result"] == "Working now"
        assert "ErrorType" in result["links"]

    def test_empty_input(self):
        result = extract_signal("")
        assert result["cause"] == ""
        assert result["links"] == []


class TestIsNoise:
    def test_traceback_header(self):
        assert is_noise("Traceback (most recent call last):") is True

    def test_file_line(self):
        assert is_noise('  File "test.py", line 10, in func') is True

    def test_signal_line(self):
        assert is_noise("KeyError: 'price'") is False

    def test_empty_line(self):
        assert is_noise("   ") is True


class TestFilterNoise:
    def test_removes_noise(self):
        lines = [
            "Traceback (most recent call last):",
            "KeyError: 'price'",
            "",
            "FIX: applied patch",
        ]
        result = filter_noise(lines)
        assert "KeyError: 'price'" in result
        assert "FIX: applied patch" in result
        assert "Traceback" not in "\n".join(result)

```