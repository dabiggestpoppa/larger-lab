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
from core.spawn.agent_lifecycle import AgentLifecycle, AgentState
from core.spawn.execution_boundary import ExecutionBoundary
from core.spawn.spawn_registry import SpawnRegistry, SpawnRecord

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

            # Step 5: Register and start lifecycle
            record = SpawnRecord(
                spawn_id=spawn_id,
                task_type=consensus_result.task_type,
                complexity=consensus_result.complexity,
                model=blueprint.target_model,
                status="active",
                started_at=start_time.isoformat(),
            )
            self.registry.register(record)
            self.lifecycle.start(spawn_id)

            # Step 6: Generate response (for chat, this is the observer response)
            output = self._generate_response(
                user_input=user_input,
                consensus=consensus_result,
                blueprint=blueprint,
                context=context,
            )

            # Complete
            self.lifecycle.complete(spawn_id)
            self.registry.update_status(spawn_id, "completed")

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
            self.lifecycle.fail(spawn_id)
            self.registry.update_status(spawn_id, "failed")
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

        This is the core chat response generator. It uses the consensus
        result to craft a contextual response from the observer's perspective.
        """
        task_type = consensus.task_type
        complexity = consensus.complexity
        routing = " -> ".join(consensus.routing_path)
        model = consensus.recommended_model
        agreement = consensus.agreement_score

        # Build response based on task type
        response_parts = [
            f"**Observer Analysis**",
            f"",
            f"**Task Type:** {task_type.replace('_', ' ').title()}",
            f"**Complexity:** {complexity.title()}",
            f"**Routing Path:** {routing}",
            f"**Model Selected:** {model}",
            f"**Consensus Agreement:** {agreement:.0%}",
            f"",
        ]

        # Add task-specific response
        if task_type == "system_analysis":
            response_parts.extend(self._system_analysis_response(user_input, context))
        elif task_type == "coding":
            response_parts.extend(self._coding_response(user_input, context))
        elif task_type == "research":
            response_parts.extend(self._research_response(user_input, context))
        elif task_type == "architecture":
            response_parts.extend(self._architecture_response(user_input, context))
        elif task_type == "repair":
            response_parts.extend(self._repair_response(user_input, context))
        elif task_type == "debugging":
            response_parts.extend(self._debugging_response(user_input, context))
        elif task_type == "orchestration":
            response_parts.extend(self._orchestration_response(user_input, context))
        elif task_type == "visualization":
            response_parts.extend(self._visualization_response(user_input, context))
        elif task_type == "automation":
            response_parts.extend(self._automation_response(user_input, context))
        else:
            response_parts.extend(self._general_response(user_input, context))

        return "\n".join(response_parts)

    def _system_analysis_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**System Analysis:**",
            f"Analyzing your request against the current observer field state.",
            f"",
            f"**Current Field Status:**",
            f"- Active Observers: planner, execution, memory, repair",
            f"- Topology: Connected and stable",
            f"- Entropy: Within normal bounds",
            f"",
            f"Your query: \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"I'm routing this through the system analysis pipeline. What specific metrics or state would you like me to examine?",
        ]

    def _coding_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Coding Task Detected**",
            f"",
            f"I'm analyzing your implementation request. The planner will decompose this into steps, and the execution observer will handle the implementation.",
            f"",
            f"**Your request:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"Would you like me to:",
            f"1. Plan the implementation approach",
            f"2. Start coding directly",
            f"3. Review existing code first",
        ]

    def _research_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Research Mode**",
            f"",
            f"I'm activating the research pipeline. The memory observer will retrieve relevant context, and the planner will structure the investigation.",
            f"",
            f"**Query:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"What aspect would you like me to focus on?",
        ]

    def _architecture_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Architecture Design**",
            f"",
            f"Engaging the architecture design pipeline. This will involve planning, memory (for pattern retrieval), and execution observers.",
            f"",
            f"**Design Brief:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"I'll produce a structured design document. What constraints should I consider?",
        ]

    def _repair_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Repair Mode Activated**",
            f"",
            f"The repair observer is analyzing the issue. This involves diagnostics, root cause analysis, and healing procedures.",
            f"",
            f"**Issue:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"Running diagnostics now. I'll report back with findings and recommended fixes.",
        ]

    def _debugging_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Debugging Session**",
            f"",
            f"Engaging the debugging pipeline: repair observer for error detection, planner for root cause analysis, memory for historical context.",
            f"",
            f"**Debug Target:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"What specific behavior are you seeing? Any error messages?",
        ]

    def _orchestration_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Orchestration Request**",
            f"",
            f"This is a multi-agent orchestration task. I'll coordinate the observer field to handle this.",
            f"",
            f"**Task:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"**Spawn Plan:**",
            f"- Planner: Task decomposition",
            f"- Execution: Implementation",
            f"- Memory: Context continuity",
            f"- Repair: Quality assurance",
            f"",
            f"Should I proceed with the orchestration?",
        ]

    def _visualization_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Visualization Request**",
            f"",
            f"Engaging the visualization pipeline. The planner will design the view, and execution will render it.",
            f"",
            f"**Request:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"What type of visualization do you need? (chart, graph, topology map, dashboard)",
        ]

    def _automation_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Automation Task**",
            f"",
            f"Setting up the automation pipeline. The planner will design the workflow, and execution will implement it.",
            f"",
            f"**Task:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"What triggers and actions should the automation include?",
        ]

    def _general_response(self, user_input: str, context: dict) -> list[str]:
        return [
            f"**Observer Response**",
            f"",
            f"I've analyzed your message through the observer field.",
            f"",
            f"**Your message:** \"{user_input[:100]}{'...' if len(user_input) > 100 else ''}\"",
            f"",
            f"How can I help you? I can:",
            f"- Analyze system state and topology",
            f"- Help with coding and implementation",
            f"- Design architecture and plan features",
            f"- Debug and repair issues",
            f"- Coordinate multi-agent workflows",
            f"- Create visualizations and dashboards",
        ]

    def get_active_spawns(self) -> list[dict[str, Any]]:
        """Get all active spawns."""
        return self.registry.get_active()

    def get_spawn_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get spawn history."""
        return self.registry.get_history(limit)
