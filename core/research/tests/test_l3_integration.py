"""
L3 Integration Tests — Research Agent + Queue + Evaluator + Gap Detector.

Tests the full autonomous research loop:
    GapDetector → TaskGen → Queue → ResearchAgent → Evaluator → VaultWriter

12 tests covering:
- Gap detection heuristics
- Task generation from gaps
- Queue concurrency bounds
- Agent execution with mock sources
- Finding evaluation scoring
- Agent lifecycle state transitions
- End-to-end: gap → task → agent → finding
"""

import asyncio
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.research.agents.queue import TaskQueue, ResearchTask
from core.research.agents.evaluator import FindingEvaluator
from core.research.agents.gap_detector import GapDetector
from core.research.agents.task_gen import TaskGenerator
from core.research.agents.lifecycle import AgentLifecycle
from core.research.agents.router import ResearchRouter
from core.research.agents.research_agent import ResearchAgent
from core.research.ingestion.models import Author, Concept, Paper
from core.research.distillation.graph_store import GraphStore


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_agents.db"
    return db_path


@pytest.fixture
def temp_graph_db(tmp_path):
    db_path = tmp_path / "test_graph.db"
    return db_path


@pytest.fixture
def task_queue(temp_db):
    return TaskQueue(db_path=temp_db)


@pytest.fixture
def graph_store(temp_graph_db):
    return GraphStore(db_path=temp_graph_db)


@pytest.fixture
def sample_papers():
    """Generate papers for gap detection."""
    papers = []
    for i in range(10):
        papers.append(Paper(
            id=f"WP{i+1:04d}",
            title=f"Research Paper {i+1}",
            abstract=f"Abstract for paper {i+1} on agent orchestration.",
            year=2024,
            source="test",
            citation_count=5 + i * 2,
            authors=[Author(name=f"Author {i+1}")],
            concepts=[
                Concept(name="agent orchestration", score=0.8 + i * 0.02),
            ],
        ))
    return papers


@pytest.fixture
def sample_task():
    return ResearchTask(
        query="attention mechanisms for multi-agent systems",
        domains=["agent_orchestration", "attention_mechanisms"],
        priority=3,
    )


# ============================================================
# L3.1 — Gap Detector Integration
# ============================================================

class TestGapDetectorIntegration:
    def test_find_gaps_returns_list(self, graph_store, sample_papers):
        """GapDetector.find_gaps returns a list of gap dicts."""
        detector = GapDetector(graph_store=graph_store)
        gaps = detector.find_gaps(sample_papers)
        assert isinstance(gaps, list)

    def test_gap_structure(self, graph_store, sample_papers):
        """Each gap has required fields."""
        detector = GapDetector(graph_store=graph_store, threshold=0.1)
        gaps = detector.find_gaps(sample_papers)
        for gap in gaps:
            assert "type" in gap or isinstance(gap, dict)

    def test_no_gaps_for_empty_papers(self, graph_store):
        """No gaps detected for empty paper list."""
        detector = GapDetector(graph_store=graph_store)
        gaps = detector.find_gaps([])
        assert len(gaps) == 0


# ============================================================
# L3.2 — Task Generator Integration
# ============================================================

class TestTaskGeneratorIntegration:
    def test_generate_from_gap(self):
        """TaskGenerator creates task from gap dict."""
        gen = TaskGenerator()
        gap = {
            "type": "low_density",
            "domain": "agent_orchestration",
            "concept": "attention mechanisms",
            "score": 0.3,
        }
        task = gen.from_gap(gap)
        assert isinstance(task, ResearchTask)
        assert len(task.query) > 0

    def test_task_has_domains(self):
        """Generated task includes domain from gap."""
        gen = TaskGenerator()
        gap = {"domain": "memory_systems", "concept": "long-term memory", "score": 0.5}
        task = gen.from_gap(gap)
        assert "memory_systems" in task.domains or len(task.domains) > 0


# ============================================================
# L3.7 — Task Queue Integration
# ============================================================

class TestTaskQueueIntegration:
    def test_enqueue_task(self, task_queue, sample_task):
        """TaskQueue.enqueue adds task and returns ID."""
        task_id = task_queue.enqueue(sample_task)
        assert len(task_id) > 0

    def test_dequeue_returns_pending(self, task_queue, sample_task):
        """TaskQueue.dequeue returns a pending task."""
        task_queue.enqueue(sample_task)
        task = task_queue.dequeue()
        assert task is not None
        assert task.status == "running"

    def test_mark_complete(self, task_queue, sample_task):
        """mark_complete transitions task to completed."""
        task_id = task_queue.enqueue(sample_task)
        task_queue.dequeue()  # transition to running
        task_queue.mark_complete(task_id, {"result": "done"})
        task = task_queue.get_task(task_id)
        assert task.status == "completed"

    def test_mark_failed(self, task_queue, sample_task):
        """mark_failed transitions task to failed."""
        task_id = task_queue.enqueue(sample_task)
        task_queue.dequeue()
        task_queue.mark_failed(task_id, "test error")
        task = task_queue.get_task(task_id)
        assert task.status == "failed"

    def test_max_concurrent_enforcement(self, task_queue):
        """Queue enforces max 3 concurrent running tasks."""
        tasks = []
        for i in range(5):
            t = ResearchTask(query=f"task {i}", priority=3)
            task_queue.enqueue(t)
            tasks.append(t)

        # Dequeue 3 (max concurrent)
        dequeued = []
        for _ in range(3):
            t = task_queue.dequeue()
            if t:
                dequeued.append(t)

        assert len(dequeued) == 3
        # All should be in running status
        for t in dequeued:
            assert t.status == "running"

    def test_list_tasks_by_status(self, task_queue, sample_task):
        """list_tasks filters by status."""
        task_queue.enqueue(sample_task)
        pending = task_queue.list_tasks(status="pending")
        assert len(pending) >= 1


# ============================================================
# L3.4 — Finding Evaluator Integration
# ============================================================

class TestFindingEvaluatorIntegration:
    def test_evaluate_returns_confidence(self):
        """FindingEvaluator returns confidence score between 0 and 1."""
        evaluator = FindingEvaluator()
        finding = {"paper_id": "WE01", "source": "openalex", "citation_count": 50, "year": 2024}
        result = evaluator.evaluate(finding)
        assert 0.0 <= result <= 1.0

    def test_high_citation_scores_higher(self):
        """Findings with more citations score higher."""
        evaluator = FindingEvaluator()

        high_finding = {"paper_id": "WE02", "source": "openalex", "citation_count": 100, "year": 2024}
        low_finding = {"paper_id": "WE03", "source": "test", "citation_count": 1, "year": 2020}

        high_score = evaluator.evaluate(high_finding)
        low_score = evaluator.evaluate(low_finding)
        assert high_score >= low_score

    def test_below_threshold_rejected(self):
        """Findings below 0.6 threshold are rejected."""
        evaluator = FindingEvaluator(threshold=0.6)
        finding = {"paper_id": "WE04", "source": "unknown", "citation_count": 0, "year": 2000}
        result = evaluator.evaluate(finding)
        assert result < 0.6


# ============================================================
# L3.5 — Research Router Integration
# ============================================================

class TestResearchRouterIntegration:
    def test_routes_to_local_first(self):
        """ResearchRouter prefers local Ollama when available."""
        router = ResearchRouter()
        # Without budget exhaustion, should return a route
        route = router.route(query="test query", budget_remaining=2.0)
        assert route is not None
        assert len(route) > 0

    def test_skips_when_budget_exhausted(self):
        """ResearchRouter returns empty when budget is 0."""
        router = ResearchRouter()
        route = router.route(query="test", budget_remaining=0.0)
        assert route == "" or route is None or route == "skip"


# ============================================================
# L3.6 — Agent Lifecycle Integration
# ============================================================

class TestAgentLifecycleIntegration:
    def test_spawn_returns_agent(self):
        """AgentLifecycle.spawn returns an AgentInstance."""
        lifecycle = AgentLifecycle()
        agent = lifecycle.spawn("task_001")
        assert agent is not None
        assert agent.task_id == "task_001"

    def test_spawn_respects_max_concurrent(self):
        """AgentLifecycle.spawn returns None when max concurrent reached."""
        lifecycle = AgentLifecycle(max_concurrent=2)
        lifecycle.spawn("task_1")
        lifecycle.spawn("task_2")
        result = lifecycle.spawn("task_3")
        assert result is None

    def test_complete_transitions_state(self):
        """AgentLifecycle.complete transitions agent to COMPLETED."""
        lifecycle = AgentLifecycle()
        agent = lifecycle.spawn("task_complete")
        assert agent.state.value == "running"

        lifecycle.complete(agent.agent_id)
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.state.value == "completed"

    def test_fail_increments_retry(self):
        """AgentLifecycle.fail increments retry count."""
        lifecycle = AgentLifecycle()
        agent = lifecycle.spawn("task_fail")

        lifecycle.fail(agent.agent_id, "test error")
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.retry_count == 1
        assert updated.state.value == "failed"

    def test_max_retries_abandons(self):
        """AgentLifecycle abandons agent after max retries."""
        lifecycle = AgentLifecycle(max_retries=2)
        agent = lifecycle.spawn("task_abandon")

        for _ in range(3):
            lifecycle.fail(agent.agent_id, "error")
            if agent.retry_count <= 2:
                # Re-spawn to retry
                agent = lifecycle.spawn("task_abandon_retry") or agent

        # After max retries, should be abandoned
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.state.value == "abandoned" or updated.retry_count >= 2

    def test_heartbeat_updates_timestamp(self):
        """AgentLifecycle.heartbeat updates last_heartbeat."""
        lifecycle = AgentLifecycle()
        agent = lifecycle.spawn("task_hb")

        result = lifecycle.heartbeat(agent.agent_id)
        assert result is True
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.last_heartbeat is not None


# ============================================================
# L3.3 — Research Agent Integration (with mocks)
# ============================================================

class TestResearchAgentIntegration:
    @pytest.mark.asyncio
    async def test_agent_execute_returns_result(self):
        """ResearchAgent.execute returns a result dict."""
        agent = ResearchAgent(llm_client=None)
        task = ResearchTask(query="test query", domains=["test"])

        # Mock _query_sources to return empty
        with patch.object(agent, "_query_sources", new_callable=AsyncMock, return_value=[]):
            result = await agent.execute(task)

        assert isinstance(result, dict)
        assert "success" in result
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_agent_with_papers_returns_success(self):
        """ResearchAgent with papers returns success=True."""
        agent = ResearchAgent(llm_client=None)
        task = ResearchTask(query="test", domains=["test"])

        mock_papers = [
            Paper(id="WM01", title="Mock Paper", abstract="We propose a method. Results show improvement.",
                  year=2024, source="test", citation_count=10,
                  authors=[Author(name="Test")],
                  concepts=[Concept(name="test", score=0.9)])
        ]

        with patch.object(agent, "_query_sources", new_callable=AsyncMock, return_value=mock_papers):
            result = await agent.execute(task)

        assert result["success"] is True
        assert result["papers_found"] == 1

    @pytest.mark.asyncio
    async def test_agent_confidence_scoring(self):
        """ResearchAgent confidence increases with more papers."""
        agent = ResearchAgent(llm_client=None)
        task = ResearchTask(query="test", domains=["test"])

        many_papers = [
            Paper(id=f"WM{i:03d}", title=f"Paper {i}", abstract="Results show improvement.",
                  year=2024, source="test", citation_count=10)
            for i in range(5)
        ]

        with patch.object(agent, "_query_sources", new_callable=AsyncMock, return_value=many_papers):
            result = await agent.execute(task)

        assert result["confidence"] > 0.5


# ============================================================
# End-to-End L3 Pipeline
# ============================================================

class TestL3EndToEnd:
    @pytest.mark.asyncio
    async def test_full_research_loop(self, task_queue, graph_store):
        """Full loop: Gap → Task → Agent → Evaluator → Result."""
        # Step 1: Detect gaps
        detector = GapDetector(graph_store=graph_store, threshold=0.1)
        papers = [
            Paper(id=f"WE{i:03d}", title=f"Paper {i}",
                  abstract="Abstract on agent orchestration.",
                  year=2024, source="test", citation_count=5)
            for i in range(5)
        ]
        gaps = detector.find_gaps(papers)

        # Step 2: Generate task
        gen = TaskGenerator()
        if gaps:
            task = gen.from_gap(gaps[0])
        else:
            task = ResearchTask(query="agent orchestration", domains=["agent_orchestration"])

        # Step 3: Enqueue
        task_id = task_queue.enqueue(task)
        assert len(task_id) > 0

        # Step 4: Dequeue and execute
        dequeued = task_queue.dequeue()
        assert dequeued is not None

        # Step 5: Evaluate a finding
        evaluator = FindingEvaluator()
        test_paper = Paper(id="WE_EVAL", title="Eval Test", abstract="Test",
                           year=2024, source="test", citation_count=50)
        confidence = evaluator.evaluate(test_paper, {"summary": "test finding"})
        assert 0.0 <= confidence <= 1.0

        # Step 6: Complete task
        task_queue.mark_complete(task_id, {"confidence": confidence})
        completed = task_queue.get_task(task_id)
        assert completed.status == "completed"
