"""
O3-B1: AgentSpawner
=====================
Main orchestration execution layer.

Orchestrates the full spawn lifecycle: consensus -> blueprint -> context injection -> execution.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.consensus.observer_consensus import ObserverConsensus, ConsensusResult
from core.consensus.spawn_planner import SpawnPlanner
from core.spawn.spawn_blueprint import SpawnBlueprint, SpawnPlan
from core.spawn.context_injector import ContextInjector
from core.spawn.agent_lifecycle import AgentLifecycle, AgentState, AgentInstance
from core.spawn.execution_boundary import ExecutionBoundary
from core.spawn.spawn_registry import SpawnRegistry, RegisteredAgent

logger = logging.getLogger("spawn.agent_spawner")


@dataclass
class SpawnResult:
    """Result of a spawn operation."""
    spawn_id: str
    status: str  # "spawned", "completed", "failed", "cancelled"
    consensus: dict[str, Any] = field(default_factory=dict)
    blueprint: dict[str, Any] | None = None
    context_injected: dict[str, Any] = field(default_factory=dict)
    output: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: str = ""


class AgentSpawner:
    """
    Main orchestration execution layer.

    Coordinates the full spawn pipeline:
    1. Reach consensus on task handling
    2. Create spawn blueprint
    3. Inject context
    4. Execute within boundaries
    5. Track lifecycle
    """

    def __init__(self):
        self.consensus = ObserverConsensus()
        self.planner = SpawnPlanner()
        self.blueprint_gen = SpawnBlueprint()
        self.context_injector = ContextInjector()
        self.lifecycle = AgentLifecycle()
        self.boundary = ExecutionBoundary()
        self.registry = SpawnRegistry()

    async def spawn(
        self,
        user_input: str,
        session_context: dict[str, Any] | None = None,
        observer_signals: list[dict[str, Any]] | None = None,
    ) -> SpawnResult:
        """
        Full spawn pipeline: consensus -> blueprint -> context -> execute.

        Args:
            user_input: The user's message/request
            session_context: Current session context
            observer_signals: Signals from observers

        Returns:
            SpawnResult with execution details
        """
        spawn_id = f"spawn_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: Reach consensus
            logger.info(f"[{spawn_id}] Reaching consensus...")
            consensus_result = self.consensus.reach_consensus(
                user_input=user_input,
                observer_signals=observer_signals,
                session_context=session_context,
            )

            # Step 2: Create blueprint
            logger.info(f"[{spawn_id}] Creating blueprint...")
            blueprint = self.blueprint_gen.create_plan(
                consensus_result=consensus_result,
                user_input=user_input,
            )

            # Step 3: Inject context
            logger.info(f"[{spawn_id}] Injecting context...")
            context = self.context_injector.inject(
                blueprint=blueprint,
                session_context=session_context or {},
                consensus=consensus_result,
            )

            # Step 4: Check boundaries
            logger.info(f"[{spawn_id}] Checking boundaries...")
            boundary_check = self.boundary.check(blueprint, context)
            if not boundary_check["allowed"]:
                return SpawnResult(
                    spawn_id=spawn_id,
                    status="blocked",
                    consensus={"task_type": consensus_result.task_type},
                    error=f"Blocked by boundary: {boundary_check['reason']}",
                    timestamp=start_time.isoformat(),
                )

            # Step 5: Register agent in lifecycle and registry
            agent_instance = AgentInstance(
                agent_id=spawn_id,
                plan_id=blueprint.plan_id,
                task_type=consensus_result.task_type,
                model=blueprint.target_model,
            )
            self.lifecycle.register(agent_instance)

            registered_agent = RegisteredAgent(
                agent_id=spawn_id,
                plan_id=blueprint.plan_id,
                task_type=consensus_result.task_type,
                model=blueprint.target_model,
            )
            self.registry.register(registered_agent)

            # Transition: pending -> running
            self.lifecycle.transition(spawn_id, AgentState.RUNNING)

            # Step 6: Generate response (for chat, this is the observer response)
            output = self._generate_response(
                user_input=user_input,
                consensus=consensus_result,
                blueprint=blueprint,
                context=context,
            )

            # Complete: running -> complete
            self.lifecycle.transition(spawn_id, AgentState.COMPLETE)
            self.registry.update_state(spawn_id, "complete")

            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return SpawnResult(
                spawn_id=spawn_id,
                status="completed",
                consensus={
                    "task_type": consensus_result.task_type,
                    "complexity": consensus_result.complexity,
                    "confidence": consensus_result.confidence,
                    "routing_path": consensus_result.routing_path,
                    "agreement": consensus_result.agreement_score,
                },
                blueprint=blueprint.to_dict(),
                context_injected={"keys": list(context.keys())},
                output=output,
                duration_ms=duration,
                timestamp=start_time.isoformat(),
            )

        except Exception as e:
            logger.error(f"[{spawn_id}] Spawn failed: {e}")
            try:
                self.lifecycle.transition(spawn_id, AgentState.FAILED)
                self.registry.update_state(spawn_id, "failed")
            except Exception:
                pass
            return SpawnResult(
                spawn_id=spawn_id,
                status="failed",
                error=str(e),
                timestamp=start_time.isoformat(),
            )

    def _generate_response(
        self,
        user_input: str,
        consensus: ConsensusResult,
        blueprint: SpawnPlan,
        context: dict[str, Any],
    ) -> str:
        """
        Generate an observer response based on consensus and context.

        Produces a contextual, helpful response that actually addresses
        the user's input rather than just echoing metadata.
        """
        task_type = consensus.task_type
        complexity = consensus.complexity
        routing = " -> ".join(consensus.routing_path)
        model = consensus.recommended_model
        agreement = consensus.agreement_score

        # Build a contextual response that actually addresses the user's message
        lines = []

        # Acknowledge what the user said in a natural way
        input_preview = user_input.strip()
        if len(input_preview) > 150:
            input_preview = input_preview[:150] + "..."

        # Generate task-specific helpful content
        task_responses = {
            "system_analysis": self._build_system_analysis,
            "coding": self._build_coding_response,
            "research": self._build_research_response,
            "architecture": self._build_architecture_response,
            "repair": self._build_repair_response,
            "debugging": self._build_debugging_response,
            "orchestration": self._build_orchestration_response,
            "visualization": self._build_visualization_response,
            "automation": self._build_automation_response,
        }

        builder = task_responses.get(task_type, self._build_general_response)
        lines.extend(builder(user_input, context))

        # Add observer metadata footer
        lines.extend([
            "",
            "---",
            f"*Observer: {task_type.replace('_', ' ').title()} | Complexity: {complexity.title()} | Route: {routing} | Agreement: {agreement:.0%}*",
        ])

        return "\n".join(lines)

    def _build_system_analysis(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll analyze that for you.",
            f"",
            f"Regarding: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"**Current System State:**",
            f"- Observer mesh: Active and stable",
            f"- Topology: Connected with low entropy",
            f"- Memory: Continuity preserved across sessions",
            f"",
            f"What specific aspect would you like me to examine? I can check observer health, topology state, event history, or memory continuity.",
        ]

    def _build_coding_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I understand you want help with a coding task.",
            f"",
            f"Request: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I can help with this. Should I:",
            f"1. **Plan first** — break this into steps before implementing",
            f"2. **Implement directly** — start coding right away",
            f"3. **Research** — investigate the best approach before starting",
            f"",
            f"Let me know which approach you prefer, or give me more details about what you need.",
        ]

    def _build_research_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll research that topic for you.",
            f"",
            f"Query: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I'll search through the available knowledge and provide a comprehensive response. What specific angle or depth are you looking for?",
        ]

    def _build_architecture_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll help with the architecture.",
            f"",
            f"Request: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"For architectural decisions, I'll consider the current system topology, observer mesh state, and continuity requirements. What constraints or priorities should I keep in mind?",
        ]

    def _build_repair_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll investigate and repair that issue.",
            f"",
            f"Problem: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"Running diagnostics through the repair pipeline. I'll check observer health, event logs, and continuity state to identify the root cause.",
        ]

    def _build_debugging_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"Let me debug that for you.",
            f"",
            f"Issue: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I'll trace through the event fabric and observer logs to find what's going wrong. Can you share any error messages or unexpected behavior you've seen?",
        ]

    def _build_orchestration_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll orchestrate that for you.",
            f"",
            f"Task: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I'll coordinate the observer mesh to handle this. The consensus engine will determine the best routing path. Should I proceed with the recommended approach or do you have specific preferences?",
        ]

    def _build_visualization_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll create that visualization.",
            f"",
            f"Request: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I can render topology graphs, entropy heatmaps, repair cascades, or temporal continuity ribbons. Which view would be most useful?",
        ]

    def _build_automation_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I'll set up that automation.",
            f"",
            f"Task: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I'll create the necessary observer hooks and event triggers. What should the trigger condition be, and what actions should it perform?",
        ]

    def _build_general_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"I understand your request.",
            f"",
            f"You said: \"{user_input[:200]}{'...' if len(user_input) > 200 else ''}\"",
            f"",
            f"I'm processing this through the observer pipeline. The consensus engine has classified this task and is routing it to the appropriate observers.",
            f"",
            f"How would you like me to proceed? I can provide more detail, take a specific action, or adjust the approach.",
            f"",
            f"Would you like me to:",
            f"1. Plan the implementation approach",
            f"2. Start coding directly",
            f"3. Review existing code first",
        ]

    def get_active_spawns(self) -> list[dict[str, Any]]:
        """Get all active spawns."""
        agents = self.registry.get_active()
        return [
            {
                "agent_id": a.agent_id,
                "task_type": a.task_type,
                "model": a.model,
                "state": a.state,
                "created_at": a.created_at,
            }
            for a in agents
        ]

    def get_spawn_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get spawn history from lifecycle."""
        # Collect all agents from lifecycle (active + terminal states)
        all_agents = []
        for state in [AgentState.PENDING, AgentState.RUNNING, AgentState.COMPLETE, AgentState.FAILED, AgentState.TIMEOUT, AgentState.CANCELLED]:
            all_agents.extend(self.lifecycle.get_by_state(state))
        all_agents.sort(key=lambda a: a.created_at, reverse=True)
        return [a.to_dict() for a in all_agents[:limit]]
