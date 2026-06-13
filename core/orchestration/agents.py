"""
Phase 1.6.2 — Agent Runtime System

Persistent cognitive workers with state tracking and capability registry.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.agents")


class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentSpec:
    """Specification for a cognitive agent."""
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    model: str = "openrouter/owl-alpha"
    max_concurrent: int = 3
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInstance:
    """A running agent instance."""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    spec: AgentSpec = field(default_factory=lambda: AgentSpec(name="", role=""))
    state: AgentState = AgentState.IDLE
    current_task: str = ""
    memory: Dict[str, Any] = field(default_factory=dict)
    recursion_depth: int = 0
    started_at: Optional[str] = None
    last_active: Optional[str] = None
    error: str = ""


class AgentRuntime:
    """
    Manages persistent cognitive workers.
    
    Agent types:
    - retriever: semantic recall
    - synthesizer: report creation
    - verifier: hallucination checking
    - topology_agent: graph updates
    - planner: execution strategy
    - reflection_agent: self-review
    - ingestion_agent: parser orchestration
    """

    def __init__(self, max_agents: int = 10):
        self._registry: Dict[str, AgentSpec] = {}
        self._instances: Dict[str, AgentInstance] = {}
        self._max_agents = max_agents
        self._register_defaults()

    def _register_defaults(self):
        """Register default agent types."""
        defaults = [
            AgentSpec(
                name="retriever",
                role="Semantic recall and retrieval",
                capabilities=["vector_search", "graph_query", "vault_search"],
            ),
            AgentSpec(
                name="synthesizer",
                role="Multi-source research synthesis and report generation",
                capabilities=["synthesize", "generate_report", "generate_pdf"],
            ),
            AgentSpec(
                name="verifier",
                role="Hallucination detection and output verification",
                capabilities=["verify_claims", "check_citations", "validate_reasoning"],
            ),
            AgentSpec(
                name="topology_agent",
                role="Knowledge graph updates and maintenance",
                capabilities=["update_graph", "detect_clusters", "find_gaps"],
            ),
            AgentSpec(
                name="planner",
                role="Task decomposition and execution planning",
                capabilities=["decompose", "sequence", "prioritize"],
            ),
            AgentSpec(
                name="reflection_agent",
                role="Self-review and correction",
                capabilities=["self_review", "detect_errors", "suggest_improvements"],
            ),
            AgentSpec(
                name="ingestion_agent",
                role="Data ingestion and parsing",
                capabilities=["openalex_search", "parse_documents", "normalize_data"],
            ),
        ]
        for spec in defaults:
            self._registry[spec.name] = spec

    def register(self, spec: AgentSpec):
        """Register a new agent type."""
        self._registry[spec.name] = spec
        logger.info(f"Agent registered: {spec.name}")

    def spawn(self, agent_name: str) -> Optional[AgentInstance]:
        """Spawn a new agent instance."""
        spec = self._registry.get(agent_name)
        if not spec:
            logger.warning(f"Agent '{agent_name}' not in registry")
            return None

        active = sum(1 for i in self._instances.values() if i.spec.name == agent_name and i.state == AgentState.RUNNING)
        if active >= spec.max_concurrent:
            logger.warning(f"Max concurrent instances reached for {agent_name}")
            return None

        instance = AgentInstance(
            spec=spec,
            state=AgentState.IDLE,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._instances[instance.instance_id] = instance
        logger.info(f"Agent spawned: {agent_name} ({instance.instance_id})")
        return instance

    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        return self._instances.get(instance_id)

    def update_state(self, instance_id: str, state: AgentState, **kwargs):
        """Update agent instance state."""
        instance = self._instances.get(instance_id)
        if instance:
            instance.state = state
            instance.last_active = datetime.now(timezone.utc).isoformat()
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents and their status."""
        result = []
        for name, spec in self._registry.items():
            instances = [i for i in self._instances.values() if i.spec.name == name]
            running = sum(1 for i in instances if i.state == AgentState.RUNNING)
            result.append({
                "name": name,
                "role": spec.role,
                "capabilities": spec.capabilities,
                "running": running,
                "total": len(instances),
            })
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        total = len(self._instances)
        by_state = {}
        for instance in self._instances.values():
            state = instance.state.value
            by_state[state] = by_state.get(state, 0) + 1
        return {
            "total_instances": total,
            "by_state": by_state,
            "registered_types": len(self._registry),
        }
