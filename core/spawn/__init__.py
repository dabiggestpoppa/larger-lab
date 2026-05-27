"""
Spawn Engine + Context Inheritance
====================================
O-3 Phase: Spawn Engine components.

Components:
- AgentSpawner: Main orchestration execution layer
- SpawnBlueprint: Formal orchestration schema
- ContextInjector: Inject field continuity into spawned agents
- OpenRouterGateway: Unified cognition-provider layer
- AgentLifecycle: Manage agent states
- ExecutionBoundary: Prevent orchestration chaos
- MultiAgentCoordinator: Coordinate multiple agents
- TraceFeedback: Feed traces back to field memory
- SpawnReplay: Replay spawned agent behavior
- SpawnRegistry: Maintain active-agent awareness
"""

from .agent_spawner import AgentSpawner
from .spawn_blueprint import SpawnBlueprint, SpawnPlan
from .context_injector import ContextInjector
from .openrouter_gateway import OpenRouterGateway
from .agent_lifecycle import AgentLifecycle, AgentState
from .execution_boundary import ExecutionBoundary
from .multi_agent_coordinator import MultiAgentCoordinator
from .trace_feedback import TraceFeedback
from .spawn_replay import SpawnReplay
from .spawn_registry import SpawnRegistry, SpawnRecord, RegisteredAgent

__all__ = [
    "AgentSpawner",
    "SpawnBlueprint",
    "SpawnPlan",
    "ContextInjector",
    "OpenRouterGateway",
    "AgentLifecycle",
    "AgentState",
    "ExecutionBoundary",
    "MultiAgentCoordinator",
    "TraceFeedback",
    "SpawnReplay",
    "SpawnRegistry",
    "SpawnRecord",
    "RegisteredAgent",
]
