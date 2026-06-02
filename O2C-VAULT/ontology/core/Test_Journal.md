# Test Journal

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
﻿"""
Tests for Execution Journal — Phase 0F
"""

import pytest
from pathlib import Path
from core.execution.journal import ExecutionJournal


@pytest.fixture
def tmp_journal(tmp_path):
    return ExecutionJournal(
        agent_name="TestAgent",
        task="Test task",
        vault_path=tmp_path / "vault",
    )


class TestLogStep:
    def test_log_success(self, tmp_journal):
        tmp_journal.log_step("step1", "success", details="Done")
        assert len(tmp_journal.steps) == 1
        assert tmp_journal.steps[0]["step"] == "step1"
        assert tmp_journal.steps[0]["result"] == "success"

    def test_log_failure(self, tmp_journal):
        tmp_journal.log_step("step2", "failed", details="Error")
        assert len(tmp_journal._failures) == 1
        assert "step2" in tmp_journal._failures

    def test_multiple_steps(self, tmp_journal):
        tmp_journal.log_step("a", "success")
        tmp_journal.log_step("b", "failed")
        tmp_journal.log_step("c", "success")
        assert len(tmp_journal.steps) == 3
        assert len(tmp_journal._successes) == 2
        assert len(tmp_journal._failures) == 1


class TestLogCorrection:
    def test_log_correction(self, tmp_journal):
        tmp_journal.log_correction("failed_step", "retry with timeout", "success")
        assert len(tmp_journal._corrections) == 1
        assert tmp_journal._corrections[0]["failed_step"] == "failed_step"


class TestSummarize:
    def test_summary(self, tmp_journal):
        tmp_journal.log_step("a", "success")
        tmp_journal.log_step("b", "failed")
        tmp_journal.log_step("c", "success")
        summary = tmp_journal.summarize()
        assert summary["agent"] == "TestAgent"
        assert summary["total_steps"] == 3
        assert summary["successes"] == 2
        assert summary["failures"] == 1
        assert summary["success_rate"] == 0.67


class TestToMarkdown:
    def test_markdown_output(self, tmp_journal):
        tmp_journal.log_step("load", "success", "Data loaded")
        tmp_journal.log_step("process", "failed", "Parse error")
        tmp_journal.log_correction("process", "retry", "success")
        md = tmp_journal.to_markdown()
        assert "# Agent Execution Report" in md
        assert "TestAgent" in md
        assert "Failures" in md
        assert "Corrections" in md
        assert "| Step | Result |" in md


class TestCompressAndSave:
    def test_saves_to_vault(self, tmp_journal, tmp_path):
        tmp_journal.log_step("test", "success")
        result = tmp_journal.compress_and_save()
        assert result is not None
        assert "path" in result


class TestToJson:
    def test_json_output(self, tmp_journal):
        tmp_journal.log_step("test", "success")
        json_str = tmp_journal.to_json()
        assert "TestAgent" in json_str
        assert "test" in json_str

```

LINKS:
[[Test Manual]]
[[Api Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Ontology Core Summary]]
[[Pm2 Test Note]]
[[Test Note]]
[[Test Pattern]]
[[Citation Workflow]]
[[Failures]]
[[Morandi Journal]]
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
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
