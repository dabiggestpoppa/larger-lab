"""
PM2 Tests — PO Agent Coordination (P2.4)

Tests for AgentCoordinator: registration, selection, concurrent execution,
graceful POAgent fallback, and statistics.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAgentCoordinatorCore:
    """Core agent coordination tests."""

    def test_default_agents_registered(self):
        """Should have analyst, researcher, coder by default."""
        from oce.backend.po_agents import AgentCoordinator
        coord = AgentCoordinator()
        agents = coord.list_agents()
        names = [a["name"] for a in agents]
        assert "analyst" in names
        assert "researcher" in names
        assert "coder" in names

    def test_register_custom_agent(self):
        """Should register a custom agent spec."""
        from oce.backend.po_agents import AgentCoordinator, AgentSpec
        coord = AgentCoordinator()
        spec = AgentSpec(
            name="planner",
            role="Task planning",
            capabilities=["planning", "decomposition"],
        )
        coord.register_agent(spec)
        agents = coord.list_agents()
        assert any(a["name"] == "planner" for a in agents)

    def test_deregister_agent(self):
        """Should remove an agent from the registry."""
        from oce.backend.po_agents import AgentCoordinator
        coord = AgentCoordinator()
        coord.deregister_agent("coder")
        agents = coord.list_agents()
        assert not any(a["name"] == "coder" for a in agents)

    def test_select_coder_for_code_query(self):
        """Should select coder for code-related queries."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="t1", agent_name="", prompt="implement a sorting algorithm")
        selected = coord._select_agent(task)
        assert selected is not None
        assert selected.name == "coder"

    def test_select_researcher_for_search_query(self):
        """Should select researcher for search queries."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="t2", agent_name="", prompt="find information about quantum computing")
        selected = coord._select_agent(task)
        assert selected is not None
        assert selected.name == "researcher"

    def test_select_analyst_as_default(self):
        """Should default to analyst for ambiguous queries."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="t3", agent_name="", prompt="hello there")
        selected = coord._select_agent(task)
        assert selected is not None
        assert selected.name == "analyst"


class TestAgentCoordinatorConcurrent:
    """Concurrent task execution tests."""

    @pytest.mark.asyncio
    async def test_coordinate_single_task(self):
        """Should coordinate a single task (with simulated POAgent fallback)."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="ct1", agent_name="", prompt="analyze the data")
        result = await coord.coordinate(task)
        assert result.task_id == "ct1"
        assert result.status in ("complete", "error")

    @pytest.mark.asyncio
    async def test_coordinate_concurrent_tasks(self):
        """Should execute multiple tasks concurrently."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator(max_concurrent=2)
        tasks = [
            AgentTask(task_id=f"cc{i}", agent_name="", prompt=f"task {i}")
            for i in range(4)
        ]
        results = await coord.coordinate_concurrent(tasks)
        assert len(results) == 4
        for r in results:
            assert r.status in ("complete", "error")


class TestAgentCoordinatorHelpers:
    """Helper method tests."""

    def test_select_agent_for_query(self):
        """Public select_agent_for_query should return agent name."""
        from oce.backend.po_agents import AgentCoordinator
        coord = AgentCoordinator()
        assert coord.select_agent_for_query("write code") == "coder"
        assert coord.select_agent_for_query("research topic") == "researcher"
        assert coord.select_agent_for_query("hello") == "analyst"

    def test_get_stats(self):
        """Should return coordination statistics."""
        from oce.backend.po_agents import AgentCoordinator
        coord = AgentCoordinator()
        stats = coord.get_stats()
        assert stats["registered_agents"] >= 3
        assert "analyst" in stats["agent_names"]
        assert stats["total_tasks"] == 0

    def test_get_task(self):
        """Should retrieve task by ID."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="gt1", agent_name="", prompt="test")
        coord._tasks["gt1"] = task
        assert coord.get_task("gt1") is not None
        assert coord.get_task("nonexistent") is None

    def test_list_tasks(self):
        """Should list all tasks."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        coord._tasks["lt1"] = AgentTask(task_id="lt1", agent_name="", prompt="a")
        coord._tasks["lt2"] = AgentTask(task_id="lt2", agent_name="", prompt="b")
        tasks = coord.list_tasks()
        assert len(tasks) == 2
