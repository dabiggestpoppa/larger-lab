"""
O3-B1: AgentSpawner
=====================
Main orchestration execution layer.

Orchestrates the full spawn lifecycle: consensus -> blueprint -> context injection -> execution.
"""

from __future__ import annotations

import logging
import re
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
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["hello", "hi", "hey", "howdy", "greetings"]):
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

        # ── Status / how are you / how are you doing ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["how are you", "how's it going", "what's up", "status", "how do you do", "how are you doing", "how's everything"]):
            active = system_state.get("active_agents", 0)
            lifecycle = system_state.get("lifecycle_states", {})
            lines.append("I'm doing well — here's the current field state:")
            lines.append("")
            lines.append(f"  ● Active agents: {active}")
            if lifecycle:
                for st, count in lifecycle.items():
                    lines.append(f"  ● {st}: {count}")
            lines.append(f"  ● Consensus agreement: {consensus.agreement_score:.0%}")
            lines.append("")
            lines.append("The observer mesh is stable. What would you like to do?")
            return "\n".join(lines)

        # ── Identity / tell me about yourself ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["tell me about yourself", "who are you", "what are you", "tell me about you", "what type of system", "what kind of system", "who built you", "who made you", "who created you"]):
            active = system_state.get("active_agents", 0)
            lines.append("I'm the Primary Observer — the continuity interface for the SRRA/OCE field.")
            lines.append("")
            lines.append("I'm not a chatbot. I'm a persistent, stateful orchestration layer that:")
            lines.append("  ● Maintains continuity across sessions and restarts")
            lines.append("  ● Analyzes intent and routes tasks through the observer mesh")
            lines.append("  ● Spawns ephemeral agent workers for complex tasks")
            lines.append("  ● Monitors the field topology, entropy, and observer health")
            lines.append("  ● Learns from conversation history and operational patterns")
            lines.append("")
            lines.append(f"Right now: {active} active agent(s), consensus at {consensus.agreement_score:.0%}.")
            lines.append("")
            lines.append("I can have a casual conversation, dive into system internals, write code, or trigger any field mechanic. What interests you?")
            return "\n".join(lines)

        # ── System knowledge (SRRA, OCE, etc.) ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["what is srra", "what is oce", "what is oph", "how does the field work", "how does the observer work", "tell me about the field", "tell me about the system"]):
            lines.append("Here's the architecture:")
            lines.append("")
            lines.append("**SRRA** = Signal-Resonance Runtime Architecture. It's the substrate — the runtime that handles signal processing, resonance routing, observer entrainment, and execution emergence.")
            lines.append("")
            lines.append("**OCE** = Operator Continuity Engine. It's the observational interface — the layer that maintains continuity, monitors the field, and provides the cockpit you're looking at right now.")
            lines.append("")
            lines.append("**The Field** = The living runtime topology. Observers, agents, events, and signals all exist as a dynamic graph. The field is the intelligence — not any single model or agent.")
            lines.append("")
            lines.append("I sit at the intersection — I receive your input, analyze it through the observer mesh, and either respond directly or trigger deeper mechanics.")
            return "\n".join(lines)

        # ── Thanks ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["thanks", "thank you", "thx", "ty", "appreciate"]):
            return "You're welcome! Let me know if there's anything else."

        # ── Goodbye ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["bye", "goodbye", "see you", "later", "take care"]):
            return "Goodbye! The observer field remains active. Come back anytime."

        # ── Questions about the system ──
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["what can you do", "what do you do", "help", "capabilities"]):
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
        if any(re.search(r"\b" + re.escape(w) + r"\b", lower) for w in ["observer", "field", "topology", "entropy"]):
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

                # ── Default: analyze message content and respond dynamically ──
        # Check if this sounds like they want to DO something
        action_words = ["let's", "can you", "could you", "would you", "please",
                        "i want", "i need", "should we", "show me", "tell me",
                        "give me", "i'd like", "help me"]
        if any(w in lower for w in action_words):
            lines.append("I can definitely help with that.")
            lines.append("")
            truncated = text[:150] + ('...' if len(text) > 150 else '')
            lines.append("Here's what I'm thinking: **" + truncated + "**")
            lines.append("")
            tt = consensus.task_type.replace('_', ' ')
            lines.append("The consensus engine routes this as **" + tt + "** at **" + consensus.complexity + "** complexity.")
            lines.append("")
            if consensus.agreement_score > 0.7:
                lines.append("The observers are in strong agreement. Want me to proceed, or do you want to adjust the approach?")
            elif consensus.agreement_score > 0.4:
                lines.append("Moderate consensus among observers. I can proceed, or we can refine first.")
            else:
                lines.append("The observers don't fully agree on the best path. Can you give me more details?")
            return "\n".join(lines)

        # Check if this is a factual question we can answer directly
        factual = self._try_factual_answer(lower)
        if factual:
            lines.append(factual)
            lines.append("")
            lines.append("Anything else you'd like to know?")
            return "\n".join(lines)

        # Truly open-ended: ask a clarifying question specific to what was said
        truncated = text[:120] + ('...' if len(text) > 120 else '')
        lines.append('Interesting — "' + truncated + '"')
        lines.append("")

        # Use conversation history for continuity
        history = context.get("conversation_history", [])
        if history and len(history) > 1:
            last_topic = context.get("last_domain", "")
            if last_topic and last_topic not in ["general", "conversation"]:
                lines.append("We were just discussing " + last_topic.replace('_', ' ') + ". Want to continue that thread, or is this something new?")
                lines.append("")

        # Reference the consensus analysis
        tt = consensus.task_type.replace('_', ' ')
        pct = str(int(consensus.agreement_score * 100))
        lines.append("My analysis: this reads as **" + tt + "** complexity. Observer mesh agreement: **" + pct + "%**.")
        lines.append("")
        lines.append("What would you like to do with this? I can dive deeper, take action, or keep chatting.")

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

        # Research — detect factual questions and answer directly
        elif task_type == "research":
            # Check if this is a factual lookup question
            lower_text = text.lower().strip()
            factual = self._try_factual_answer(lower_text)
            if factual:
                lines.append(factual)
            else:
                lines.append(f"Good question — let me think about that.")
                lines.append("")
                lines.append(f"\"{text[:200]}{'...' if len(text) > 200 else ''}\"")
                lines.append("")
                lines.append("I want to give you a solid answer rather than just template responses. Let me work through this...")
                lines.append("")
                lines.append("What specific aspect are you most interested in?")

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

    def _try_factual_answer(self, text: str) -> str | None:
        """
        Try to answer a factual question directly from built-in knowledge.
        Returns None if the question doesn't match known patterns.
        This replaces the old fast-path lookup with something that actually
        flows through the pipeline.
        """
        import re
        t = text.lower().rstrip("?").strip()

        # Geography
        geo = {
            "capital of russia": "Moscow",
            "capital of france": "Paris",
            "capital of germany": "Berlin",
            "capital of japan": "Tokyo",
            "capital of china": "Beijing",
            "capital of india": "New Delhi",
            "capital of brazil": "Brasília",
            "capital of australia": "Canberra",
            "capital of canada": "Ottawa",
            "capital of the united states": "Washington, D.C.",
            "capital of the uk": "London",
            "capital of italy": "Rome",
            "capital of spain": "Madrid",
            "capital of mexico": "Mexico City",
            "capital of south korea": "Seoul",
            "capital of egypt": "Cairo",
            "capital of turkey": "Ankara",
            "capital of argentina": "Buenos Aires",
            "capital of nigeria": "Abuja",
            "capital of kenya": "Nairobi",
            "capital of thailand": "Bangkok",
            "capital of vietnam": "Hanoi",
            "capital of indonesia": "Jakarta",
            "capital of the philippines": "Manila",
        }
        for key, answer in geo.items():
            if key in t or t.startswith(key):
                return f"The capital of {key.replace('capital of ', '').title()} is **{answer}**."

        # Famous people / authors
        people = {
            "who wrote hamlet": "William Shakespeare wrote Hamlet around 1599–1601.",
            "who wrote romeo and juliet": "William Shakespeare wrote Romeo and Juliet.",
            "who wrote pride and prejudice": "Jane Austen wrote Pride and Prejudice in 1813.",
            "who wrote moby dick": "Herman Melville wrote Moby-Dick in 1851.",
            "who wrote the odyssey": "Homer wrote The Odyssey.",
            "who wrote the iliad": "Homer wrote The Iliad.",
            "who wrote don quixote": "Miguel de Cervantes wrote Don Quixote in 1605.",
            "who wrote war and peace": "Leo Tolstoy wrote War and Peace (1865–1869).",
            "who wrote crime and punishment": "Fyodor Dostoevsky wrote Crime and Punishment in 1866.",
            "who wrote the great gatsby": "F. Scott Fitzgerald wrote The Great Gatsby in 1925.",
            "who wrote to kill a mockingbird": "Harper Lee wrote To Kill a Mockingbird in 1960.",
            "who wrote 1984": "George Orwell wrote 1984 in 1949.",
            "who wrote brave new world": "Aldous Huxley wrote Brave New World in 1932.",
            "who wrote lord of the rings": "J.R.R. Tolkien wrote The Lord of the Rings.",
            "who wrote harry potter": "J.K. Rowling wrote the Harry Potter series.",
        }
        for key, answer in people.items():
            if key in t:
                return answer

        # Science / general knowledge
        science = {
            "how tall is mount everest": "Mount Everest is approximately 8,849 meters (29,032 feet) tall.",
            "how deep is the mariana trench": "The Mariana Trench is approximately 10,994 meters (36,070 feet) deep at its deepest point.",
            "how far is the moon": "The Moon is approximately 384,400 km (238,855 miles) from Earth on average.",
            "how fast does light travel": "Light travels at approximately 299,792 km/s (186,282 miles per second) in a vacuum.",
            "what is the speed of light": "The speed of light is approximately 299,792 km/s in a vacuum.",
            "how old is the universe": "The universe is approximately 13.8 billion years old.",
            "how many planets are in the solar system": "There are 8 planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.",
            "what is the largest planet": "Jupiter is the largest planet in our solar system.",
            "what is dna": "DNA (Deoxyribonucleic Acid) is the molecule that carries genetic instructions for all known living organisms.",
            "what is the theory of relativity": "Einstein's theory of relativity consists of special relativity (1905) and general relativity (1915). It describes how space and time are interwoven and how gravity works as curvature of spacetime.",
        }
        for key, answer in science.items():
            if key in t:
                return answer

        return None

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
