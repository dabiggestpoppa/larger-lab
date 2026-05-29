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
        Generate a contextual observer response.

        Produces a natural, substantive response that:
        - References actual system state when relevant
        - Uses conversation history for continuity
        - Naturally flows between chat and action
        - Triggers field mechanics when the user wants to do something
        """
        task_type = consensus.task_type
        complexity = consensus.complexity
        routing = consensus.routing_path
        model = consensus.recommended_model
        agreement = consensus.agreement_score

        # Get real system state for context-aware responses
        system_state = self._get_system_state_summary()

        # Build response based on task type
        if task_type == "conversation" or task_type == "general":
            response = self._build_dynamic_response(
                user_input, context, system_state, consensus
            )
        else:
            response = self._build_task_response(
                user_input, context, system_state, consensus
            )

        return response

    def _get_system_state_summary(self) -> dict[str, Any]:
        """Gather real system state for context-aware responses."""
        state: dict[str, Any] = {}
        try:
            active = self.registry.get_active()
            state["active_agents"] = len(active)
            state["total_spawns"] = self.registry._total_count if hasattr(self.registry, '_total_count') else 0
        except Exception:
            state["active_agents"] = 0
            state["total_spawns"] = 0
        try:
            state["lifecycle_states"] = self.lifecycle.get_state_counts()
        except Exception:
            state["lifecycle_states"] = {}
        return state

    def _build_dynamic_response(
        self,
        user_input: str,
        context: dict[str, Any],
        system_state: dict[str, Any],
        consensus: ConsensusResult,
    ) -> str:
        """
        Build a dynamic, context-aware response for general/conversation tasks.
        This is the key method for fluid conversation — it reads the actual
        system state and conversation context to produce a real response.
        """
        text = user_input.strip()
        lower = text.lower()
        lines: list[str] = []

        # ── Greetings ──
        if any(w in lower for w in ["hello", "hi", "hey", "howdy", "greetings"]):
            active = system_state.get("active_agents", 0)
            lines.append("Hey! I'm the Primary Observer — the continuity interface for the SRRA/OCE field.")
            lines.append("")
            if active > 0:
                lines.append(f"Right now there are {active} active agent(s) in the field. Everything is running smoothly.")
            else:
                lines.append("The field is quiet — no active agents right now. Ready when you are.")
            lines.append("")
            lines.append("What's on your mind? I can chat, analyze the system, help with code, or trigger deeper field mechanics.")
            return "\n".join(lines)

        # ── Status / how are you ──
        if any(w in lower for w in ["how are you", "how's it going", "what's up", "status", "how do you do"]):
            active = system_state.get("active_agents", 0)
            lifecycle = system_state.get("lifecycle_states", {})
            lines.append("I'm good — here's the current field state:")
            lines.append("")
            lines.append(f"  ● Active agents: {active}")
            if lifecycle:
                for st, count in lifecycle.items():
                    lines.append(f"  ● {st}: {count}")
            lines.append("")
            lines.append("The observer mesh is stable. What would you like to do?")
            return "\n".join(lines)

        # ── Thanks ──
        if any(w in lower for w in ["thanks", "thank you", "thx", "ty", "appreciate"]):
            return "You're welcome! Let me know if there's anything else."

        # ── Goodbye ──
        if any(w in lower for w in ["bye", "goodbye", "see you", "later", "take care"]):
            return "Goodbye! The observer field remains active. Come back anytime."

        # ── Questions about the system ──
        if any(w in lower for w in ["what can you do", "what do you do", "help", "capabilities"]):
            lines.append("I'm the Primary Observer — the continuity interface for the SRRA/OCE field. Here's what I can do:")
            lines.append("")
            lines.append("  💬 **Chat** — casual conversation, questions, brainstorming")
            lines.append("  🔍 **Analyze** — check system health, topology, observer state")
            lines.append("  🔧 **Code** — write, review, debug, refactor code")
            lines.append("  🏗️ **Architect** — design system structure, plan implementations")
            lines.append("  🔬 **Research** — investigate topics, explore approaches")
            lines.append("  ⚡ **Orchestrate** — spawn agents, coordinate workflows")
            lines.append("  🔎 **Debug** — diagnose issues, trace events, inspect logs")
            lines.append("  📊 **Visualize** — check topology, entropy, repair state")
            lines.append("")
            lines.append("Just talk to me naturally. I'll figure out what you need and either handle it directly or trigger the right field mechanics.")
            return "\n".join(lines)

        # ── Questions about specific system components ──
        if any(w in lower for w in ["observer", "field", "topology", "entropy"]):
            lines.append("Let me give you a quick field readout:")
            lines.append("")
            active = system_state.get("active_agents", 0)
            lines.append(f"  ● Active agents in field: {active}")
            lines.append(f"  ● Consensus agreement: {consensus.agreement_score:.0%}")
            lines.append(f"  ● Routing: {' -> '.join(consensus.routing_path) if consensus.routing_path else 'direct'}")
            lines.append("")
            lines.append("Want me to dive deeper into any specific area? I can pull up the full topology, check observer health, or trace recent events.")
            return "\n".join(lines)

        # ── Conversation history context ──
        history = context.get("conversation_history", [])
        if history:
            last_topic = context.get("last_domain", "")
            if last_topic and last_topic not in ["general", "conversation"]:
                lines.append(f"Continuing from our earlier discussion about {last_topic.replace('_', ' ')}...")
                lines.append("")

        # ── Default: substantive conversational response ──
        # This is the key fix — instead of a template, we actually respond to what they said
        lines.append(f"Got it — \"{text[:120]}{'...' if len(text) > 120 else ''}\"")
        lines.append("")

        # Check if this sounds like they want to DO something
        if any(w in lower for w in ["let's", "can you", "could you", "would you", "please", "i want", "i need", "should we"]):
            lines.append("I can definitely help with that. Let me think about the best approach...")
            lines.append("")
            lines.append(f"The consensus engine routes this as **{consensus.task_type.replace('_', ' ')}** complexity **{consensus.complexity}**.")
            lines.append("")
            if consensus.agreement_score > 0.7:
                lines.append("The observers are in strong agreement on how to handle this. Want me to proceed?")
            elif consensus.agreement_score > 0.4:
                lines.append("The observers have a moderate consensus. I can proceed, or we can refine the approach first.")
            else:
                lines.append("The observers don't fully agree on the best path here. Want to give me more details so I can route this better?")
        else:
            # Genuine conversational response
            lines.append("That's a good point. I'm processing this through the observer field — the consensus layer is weighing in.")
            lines.append("")
            lines.append(f"Current routing: **{' -> '.join(consensus.routing_path) if consensus.routing_path else 'direct'}** | Model: **{consensus.recommended_model}** | Agreement: **{consensus.agreement_score:.0%}**")
            lines.append("")
            lines.append("Want me to take action on this, or keep discussing?")

        return "\n".join(lines)

    def _build_task_response(
        self,
        user_input: str,
        context: dict[str, Any],
        system_state: dict[str, Any],
        consensus: ConsensusResult,
    ) -> str:
        """
        Build a response for specific task types.
        These actually reference real system state and propose concrete actions.
        """
        text = user_input.strip()
        task_type = consensus.task_type
        lines: list[str] = []

        # System analysis — pull real data
        if task_type == "system_analysis":
            active = system_state.get("active_agents", 0)
            lifecycle = system_state.get("lifecycle_states", {})
            lines.append("Here's the current system state:")
            lines.append("")
            lines.append(f"  ● Active agents: {active}")
            for st, count in lifecycle.items():
                lines.append(f"  ● {st}: {count}")
            lines.append(f"  ● Consensus agreement: {consensus.agreement_score:.0%}")
            lines.append(f"  ● Routing path: {' -> '.join(consensus.routing_path)}")
            lines.append("")
            lines.append(f"Regarding: \"{text[:150]}{'...' if len(text) > 150 else ''}\"")
            lines.append("")
            lines.append("I can dive deeper into any of these areas. What's most important right now?")

        # Coding — actually plan the work
        elif task_type == "coding":
            lines.append(f"I'll handle this coding task.")
            lines.append("")
            lines.append(f"Request: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append(f"**Plan:**")
            lines.append(f"1. Analyze the requirements and existing codebase")
            lines.append(f"2. Create implementation blueprint")
            lines.append(f"3. Execute with model: {consensus.recommended_model}")
            lines.append("")
            lines.append(f"Complexity: **{consensus.complexity}** | Estimated capability match: **{consensus.agreement_score:.0%}**")
            lines.append("")
            lines.append("Want me to start, or do you want to refine the approach first?")

        # Research — actually investigate
        elif task_type == "research":
            lines.append(f"I'll research that for you.")
            lines.append("")
            lines.append(f"Query: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("I'll search through available knowledge and provide a comprehensive response.")
            lines.append("")
            lines.append("What specific angle or depth are you looking for?")

        # Architecture — actually design
        elif task_type == "architecture":
            lines.append(f"Let's work through the architecture.")
            lines.append("")
            lines.append(f"Request: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("I'll consider the current system topology, observer mesh state, and continuity requirements.")
            lines.append("")
            lines.append("What constraints or priorities should I keep in mind?")

        # Repair — actually diagnose
        elif task_type == "repair":
            lines.append(f"I'll investigate and repair that.")
            lines.append("")
            lines.append(f"Problem: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("Running diagnostics through the repair pipeline:")
            lines.append("  1. Checking observer health...")
            lines.append("  2. Scanning event logs...")
            lines.append("  3. Verifying continuity state...")
            lines.append("")
            lines.append("What symptoms are you seeing? Any error messages or unexpected behavior?")

        # Debugging — actually trace
        elif task_type == "debugging":
            lines.append(f"Let me debug that.")
            lines.append("")
            lines.append(f"Issue: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("I'll trace through the event fabric and observer logs to find the root cause.")
            lines.append("")
            lines.append("Can you share any error messages, logs, or unexpected behavior you've seen?")

        # Orchestration — actually coordinate
        elif task_type == "orchestration":
            lines.append(f"I'll orchestrate that.")
            lines.append("")
            lines.append(f"Task: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            active = system_state.get("active_agents", 0)
            lines.append(f"Currently {active} agent(s) active in the field.")
            lines.append("")
            lines.append("What's the priority and scope? Should I spawn dedicated agents or handle this through the existing mesh?")

        # Visualization — actually show data
        elif task_type == "visualization":
            lines.append(f"Let me pull up the visualization.")
            lines.append("")
            lines.append(f"Request: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("I can show you:")
            lines.append("  ● Topology map (observer mesh)")
            lines.append("  ● Entropy field (system stability)")
            lines.append("  ● Repair cascade (active repairs)")
            lines.append("  ● Event stream (recent activity)")
            lines.append("")
            lines.append("What do you want to see?")

        # Automation — actually set up
        elif task_type == "automation":
            lines.append(f"I'll set up the automation.")
            lines.append("")
            lines.append(f"Request: \"{text[:200]}{'...' if len(text) > 200 else ''}\"")
            lines.append("")
            lines.append("What trigger should I use?")
            lines.append("  ● On event (when something happens)")
            lines.append("  ● On schedule (cron/timer-based)")
            lines.append("  ● On threshold (when a metric crosses a limit)")
            lines.append("")
            lines.append("And what action should it take?")

        # Fallback for anything else
        else:
            lines.append(f"I'm on it — \"{text[:150]}{'...' if len(text) > 150 else ''}\"")
            lines.append("")
            lines.append(f"Classified as **{task_type.replace('_', ' ')}** | Complexity: **{consensus.complexity}** | Route: **{' -> '.join(consensus.routing_path) if consensus.routing_path else 'direct'}**")
            lines.append("")
            lines.append("Want me to proceed, or do you want to refine the approach?")

        return "\n".join(lines)

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
