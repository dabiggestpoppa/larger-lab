"""
PO Agent Coordination — manages sub-agent spawning and coordination.

Provides the interface for PO to coordinate multiple specialized agents
(e.g., code agent, research agent, analysis agent) through OCE's
existing agent infrastructure.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_agents")


@dataclass
class AgentSpec:
    """Specification for a sub-agent."""

    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    model: str = "po"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    """A task assigned to a sub-agent."""

    task_id: str
    agent_name: str
    prompt: str
    status: str = "pending"  # pending, running, complete, error, cancelled
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class CoordinationResult:
    """Result of agent coordination."""

    task_id: str
    agent: str
    status: str
    result: Any = None
    error: str = ""
    duration_ms: float = 0.0


class AgentCoordinator:
    """Coordinates multiple sub-agents for complex tasks."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._agents: Dict[str, AgentSpec] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default agent types."""
        self.register_agent(AgentSpec(
            name="analyst",
            role="Analysis and reasoning",
            capabilities=["reasoning", "analysis", "summarization"],
        ))
        self.register_agent(AgentSpec(
            name="researcher",
            role="Research and information retrieval",
            capabilities=["search", "retrieval", "synthesis"],
        ))
        self.register_agent(AgentSpec(
            name="coder",
            role="Code generation and execution",
            capabilities=["code_generation", "code_review", "execution"],
        ))

    def register_agent(self, spec: AgentSpec):
        """Register a new agent type."""
        self._agents[spec.name] = spec

    def deregister_agent(self, name: str):
        """Remove an agent type."""
        self._agents.pop(name, None)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {"name": a.name, "role": a.role, "capabilities": a.capabilities}
            for a in self._agents.values()
        ]

    async def coordinate(self, task: AgentTask) -> CoordinationResult:
        """
        Assign a task to the best available agent and execute.

        Uses simple capability matching to select the right agent.
        """
        start = time.monotonic()

        # Find best agent
        best_agent = self._select_agent(task)
        if not best_agent:
            return CoordinationResult(
                task_id=task.task_id,
                agent="",
                status="error",
                error="No suitable agent found",
                duration_ms=(time.monotonic() - start) * 1000,
            )

        task.agent_name = best_agent.name
        task.status = "running"
        task.started_at = time.time()
        self._tasks[task.task_id] = task

        try:
            # Route through OCE's POAgent for actual execution
            try:
                from core.observer.po_agent import POAgent
                agent = POAgent()

                result = await agent.chat(
                    task.prompt,
                    history=[],
                    session_id=task.task_id,
                    max_tool_rounds=4,
                )
            except ImportError:
                # POAgent not available — return simulated response
                logger.warning("POAgent not available, using simulated response")
                result = f"[{best_agent.name}] {task.prompt}"

            task.status = "complete"
            task.result = result
            task.completed_at = time.time()

            return CoordinationResult(
                task_id=task.task_id,
                agent=best_agent.name,
                status="complete",
                result=result,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        except Exception as e:
            task.status = "error"
            task.error = str(e)
            return CoordinationResult(
                task_id=task.task_id,
                agent=best_agent.name,
                status="error",
                error=str(e),
                duration_ms=(time.monotonic() - start) * 1000,
            )

    def _select_agent(self, task: AgentTask) -> AgentSpec | None:
        """Select the best agent for a task based on capability matching."""
        # Simple keyword matching — can be replaced with LLM-based routing
        prompt_lower = task.prompt.lower()
        best_match = None
        best_score = 0

        keyword_map = {
            "analyze": ["analyst"],
            "research": ["researcher"],
            "search": ["researcher"],
            "find": ["researcher"],
            "code": ["coder"],
            "implement": ["coder"],
            "write": ["coder"],
            "debug": ["coder"],
        }

        for keyword, agent_names in keyword_map.items():
            if keyword in prompt_lower:
                for name in agent_names:
                    if name in self._agents:
                        score = prompt_lower.count(keyword)
                        if score > best_score:
                            best_score = score
                            best_match = self._agents[name]

        # Default to analyst if no match
        if best_match is None and "analyst" in self._agents:
            best_match = self._agents["analyst"]

        return best_match

    def get_task(self, task_id: str) -> AgentTask | None:
        """Get task status by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        return [
            {
                "task_id": t.task_id,
                "agent": t.agent_name,
                "status": t.status,
                "created_at": t.created_at,
            }
            for t in self._tasks.values()
        ]

    async def coordinate_concurrent(
        self,
        tasks: List[AgentTask],
    ) -> List[CoordinationResult]:
        """
        Execute multiple tasks concurrently with bounded parallelism.

        Uses asyncio.Semaphore to limit concurrent agent executions.
        """
        sem = asyncio.Semaphore(self.max_concurrent)

        async def _run(task: AgentTask) -> CoordinationResult:
            async with sem:
                return await self.coordinate(task)

        results = await asyncio.gather(
            *[_run(t) for t in tasks],
            return_exceptions=True,
        )

        # Convert exceptions to error results
        final = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final.append(CoordinationResult(
                    task_id=tasks[i].task_id,
                    agent="",
                    status="error",
                    error=str(r),
                ))
            else:
                final.append(r)

        return final

    def select_agent_for_query(self, query: str) -> str:
        """Public interface: select best agent name for a query string."""
        task = AgentTask(task_id="select", agent_name="", prompt=query)
        agent = self._select_agent(task)
        return agent.name if agent else "analyst"

    def get_stats(self) -> Dict[str, Any]:
        """Return coordination statistics."""
        tasks = list(self._tasks.values())
        return {
            "registered_agents": len(self._agents),
            "agent_names": list(self._agents.keys()),
            "total_tasks": len(tasks),
            "pending": sum(1 for t in tasks if t.status == "pending"),
            "running": sum(1 for t in tasks if t.status == "running"),
            "complete": sum(1 for t in tasks if t.status == "complete"),
            "error": sum(1 for t in tasks if t.status == "error"),
        }