# Test Loader

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
﻿"""
Tests for Skill Loader — Phase 0E
"""

import pytest
from pathlib import Path
from core.skills.loader import SkillLoader


@pytest.fixture
def tmp_skills(tmp_path):
    """Create a temp skills directory with a sample skill."""
    skill_dir = tmp_path / "skills" / "observer" / "chat_response"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Chat Response Skill\n\nGenerate dynamic responses.", encoding="utf-8"
    )
    (skill_dir / "heuristics.md").write_text(
        "# Heuristics\n\nVary phrasing.", encoding="utf-8"
    )
    (skill_dir / "failures.md").write_text(
        "# Failures\n\nStatic template response.", encoding="utf-8"
    )
    return tmp_path / "skills"


class TestSkillLoader:
    def test_loads_skills(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        skills = loader.list_skills()
        assert len(skills) >= 1

    def test_get_skill(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        skill = loader.get_skill("observer", "chat_response")
        assert skill is not None
        assert skill["name"] == "chat_response"

    def test_get_skill_context(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.get_skill_context(["observer/chat_response"])
        assert "Chat Response Skill" in context
        assert "Heuristics" in context
        assert "Known Failures" in context

    def test_classify_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        relevant = loader.classify_task("Fix the chat response bug")
        assert len(relevant) >= 1

    def test_load_for_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.load_for_task("Fix the chat response")
        assert "Chat Response" in context or "chat_response" in context

    def test_load_for_irrelevant_task(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        context = loader.load_for_task("Something completely unrelated xyz123")
        # Should return empty or minimal context
        assert isinstance(context, str)

    def test_skill_count(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        assert loader.get_skill_count() >= 1

    def test_categories(self, tmp_skills):
        loader = SkillLoader(skills_dir=tmp_skills)
        cats = loader.get_categories()
        assert "observer" in cats

```

LINKS:
[[Test Manual]]
[[Api Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Ontology Core Summary]]
[[Pm2 Test Note]]
[[Test Note]]
[[Test Pattern]]
[[Citation Workflow]]
[[Failures]]
[[Heuristics]]
[[Minimal]]
[[Server]]
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
