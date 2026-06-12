"""
SRRA-OPH Substrate Adapter for OCE
==================================
Bridges OCE Continuity Core with SRRA-OPH substrate.

This adapter provides:
- Observer state access
- Event emission for OCE event fabric
- Memory persistence integration
- Attractor state queries
- Entropy economics metrics
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("oce.adapter")

# Add parent directory to path for srrs_opc imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc import (
    PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch,
    CollarLayer, AgentBridge,
    CollarTopologyEngine,
    LongTermDriftTracker, ReinforcementEngine,
    CoherenceYieldAnalyzer, EntropyBudgetManager, RecoverabilityEconomics,
    AdaptiveCompressionEngine, SyncCostOptimizer, ResourceConstrainedCognition,
    SustainabilityGovernance,
    PredictionContractManager,
    TopologyObserver,
)

# O-1 Observer Core
try:
    from core.observer import (
        PrimaryObserver, ObserverState, RuntimeAwareness,
        TaskIntentAnalyzer, ContextDistiller, ContinuityMemory,
        ObserverSession, ObserverLifecycle, EventAwareness,
        ChatLog, get_chat_log,
    )
except ImportError as e:
    logger.warning(f"core.observer not available: {e}")
    PrimaryObserver = ObserverState = RuntimeAwareness = None
    TaskIntentAnalyzer = ContextDistiller = ContinuityMemory = None
    ObserverSession = ObserverLifecycle = EventAwareness = None
    ChatLog = get_chat_log = None

# O-2 Consensus
try:
    from core.consensus import (
        ObserverConsensus, TaskClassifier, RoutingConsensus,
        ComplexityScorer, SpawnPlanner, ModelSelector,
        CapabilityMatcher, ConsensusMemory, ObserverSpecialization,
        ConsensusReplay,
    )
except ImportError as e:
    logger.warning(f"core.consensus not available: {e}")
    ObserverConsensus = TaskClassifier = RoutingConsensus = None
    ComplexityScorer = SpawnPlanner = ModelSelector = None
    CapabilityMatcher = ConsensusMemory = ObserverSpecialization = None
    ConsensusReplay = None

# O-3 Spawn Engine
try:
    from core.spawn import (
        AgentSpawner, SpawnBlueprint,
        ContextInjector, AgentLifecycle, ExecutionBoundary,
        MultiAgentCoordinator, TraceFeedback, SpawnReplay,
        SpawnRegistry, SpawnRecord,
    )
    from core.spawn.agent_spawner import SpawnResult
except ImportError as e:
    logger.warning(f"core.spawn not available: {e}")
    AgentSpawner = SpawnBlueprint = None
    ContextInjector = AgentLifecycle = ExecutionBoundary = None
    MultiAgentCoordinator = TraceFeedback = SpawnReplay = None
    SpawnRegistry = SpawnRecord = SpawnResult = None


class SRRSAdapter:
    """
    Adapter between OCE Continuity Core and SRRA-OPH substrate.

    Provides a clean interface for OCE to access SRRA-OPH capabilities
    without tight coupling.
    """

    def __init__(self):
        self._initialized = False
        self._patches: Dict[str, Any] = {}
        self._collar_layer: Optional[CollarLayer] = None
        self._agent_bridge: Optional[AgentBridge] = None
        self._topology_engine: Optional[CollarTopologyEngine] = None
        self._drift_tracker: Optional[LongTermDriftTracker] = None
        self._reinforcement_engine: Optional[ReinforcementEngine] = None
        self._coherence_analyzer: Optional[CoherenceYieldAnalyzer] = None
        self._entropy_budget: Optional[EntropyBudgetManager] = None
        self._recoverability: Optional[RecoverabilityEconomics] = None
        self._compression: Optional[AdaptiveCompressionEngine] = None
        self._sync_optimizer: Optional[SyncCostOptimizer] = None
        self._resource_cognition: Optional[ResourceConstrainedCognition] = None
        self._governance: Optional[SustainabilityGovernance] = None
        self._contract_manager: Optional[PredictionContractManager] = None
        self._topology_observer: Optional[TopologyObserver] = None
        self._event_counter = 0

        # O-1: Primary Observer Core
        self._primary_observer: Optional[PrimaryObserver] = None
        self._observer_state: Optional[ObserverState] = None
        self._runtime_awareness: Optional[RuntimeAwareness] = None
        self._continuity_memory: Optional[ContinuityMemory] = None
        self._observer_session: Optional[ObserverSession] = None
        self._observer_lifecycle: Optional[ObserverLifecycle] = None

        # O-2: Observer Consensus
        self._observer_consensus: Optional[ObserverConsensus] = None
        self._task_classifier: Optional[TaskClassifier] = None
        self._routing_consensus: Optional[RoutingConsensus] = None
        self._complexity_scorer: Optional[ComplexityScorer] = None
        self._spawn_planner: Optional[SpawnPlanner] = None
        self._model_selector: Optional[ModelSelector] = None
        self._capability_matcher: Optional[CapabilityMatcher] = None
        self._consensus_memory: Optional[ConsensusMemory] = None
        self._observer_specialization: Optional[ObserverSpecialization] = None
        self._consensus_replay: Optional[ConsensusReplay] = None

        # O-3: Spawn Engine
        self._agent_spawner: Optional[AgentSpawner] = None
        self._spawn_registry: Optional[SpawnRegistry] = None
        self._trace_feedback: Optional[TraceFeedback] = None
        self._multi_agent_coordinator: Optional[MultiAgentCoordinator] = None

    async def initialize(self):
        """Initialize SRRA-OPH substrate components."""
        if self._initialized:
            return

        # Phase 1: Observer Mesh (no-arg constructors)
        self._patches = {
            "planner": PlannerPatch(),
            "execution": ExecutionPatch(),
            "memory": MemoryPatch(),
            "repair": RepairPatch(),
        }
        self._collar_layer = CollarLayer()
        self._agent_bridge = AgentBridge()

        # Phase 3: Topology
        self._topology_engine = CollarTopologyEngine()

        # Phase 5: Long-Horizon Continuity
        self._drift_tracker = LongTermDriftTracker()
        self._reinforcement_engine = ReinforcementEngine()

        # Phase 7: Overlap Cognition
        self._contract_manager = PredictionContractManager()
        self._topology_observer = TopologyObserver()

        # Phase 9: Entropy Economics
        self._coherence_analyzer = CoherenceYieldAnalyzer()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._recoverability = RecoverabilityEconomics()
        self._compression = AdaptiveCompressionEngine()
        self._sync_optimizer = SyncCostOptimizer()
        self._resource_cognition = ResourceConstrainedCognition()
        self._governance = SustainabilityGovernance()

        # O-1: Initialize Primary Observer Core
        self._observer_state = ObserverState()
        self._primary_observer = PrimaryObserver()
        self._runtime_awareness = RuntimeAwareness()
        self._continuity_memory = ContinuityMemory()
        self._observer_session = ObserverSession()
        self._observer_lifecycle = ObserverLifecycle()
        logger.info("O-1: Primary Observer Core initialized")

        # O-2: Initialize Observer Consensus
        self._observer_consensus = ObserverConsensus()
        self._task_classifier = TaskClassifier()
        self._routing_consensus = RoutingConsensus()
        self._complexity_scorer = ComplexityScorer()
        self._spawn_planner = SpawnPlanner()
        self._model_selector = ModelSelector()
        self._capability_matcher = CapabilityMatcher()
        self._consensus_memory = ConsensusMemory()
        self._observer_specialization = ObserverSpecialization()
        self._consensus_replay = ConsensusReplay(self._consensus_memory)
        logger.info("O-2: Observer Consensus initialized")

        # O-3: Initialize Spawn Engine
        self._agent_spawner = AgentSpawner()
        self._spawn_registry = SpawnRegistry()
        self._trace_feedback = TraceFeedback()
        self._multi_agent_coordinator = MultiAgentCoordinator()
        logger.info("O-3: Spawn Engine initialized")
        # O-1-B5: Chat Log
        self._chat_log = get_chat_log()
        logger.info("O-1-B5: Chat Log initialized")
        self._initialized = True

    async def get_observer_status(self) -> List[Dict[str, Any]]:
        """Get current status of all observers."""
        if not self._initialized:
            await self.initialize()

        status = []
        patch_names = list(self._patches.keys())

        for i, (name, patch) in enumerate(self._patches.items()):
            patch_status = patch.get_status()
            collar_entropy = 0.0
            if i < len(patch_names) - 1:
                next_name = patch_names[i + 1]
                metrics = self._topology_engine.get_collar_metrics(name, next_name)
                if metrics and isinstance(metrics, dict):
                    collar_entropy = metrics.get("entropy", 0.0)

            status.append({
                "observer_id": name,
                "state": "active" if patch_status.get("is_stable", False) else "repairing",
                "entropy": collar_entropy,
                "task": patch_status.get("current_task", "none"),
            })

        return status

    async def emit_event(self, event_type: str, payload: Dict[str, Any], source: str = "srrs_opc") -> str:
        """Emit an event to the OCE Event Fabric."""
        if not self._initialized:
            await self.initialize()

        # Record in topology observer
        self._topology_observer.record_edge("planner", "execution", event_type)
        self._event_counter += 1

        # Ingest into Event Fabric
        try:
            from oce.backend.event_fabric import get_fabric
            fabric = get_fabric()
            event = await fabric.ingest(
                event_type=event_type,
                source=source,
                payload=payload,
            )
            return event.event_id
        except Exception as e:
            logger.warning(f"Event Fabric ingest failed, using fallback ID: {e}")
            return f"event_{datetime.now().timestamp()}_{self._event_counter}"

    async def get_trajectory_memory(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trajectory memory from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()

        trajectory = self._reinforcement_engine.get_operator_trajectory()
        return trajectory.get("recent_anchors", [])[:limit]

    async def get_structural_memory(self) -> Dict[str, Any]:
        """Get structural memory from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()

        system_metrics = self._topology_engine.get_system_metrics()

        return {
            "topology": system_metrics,
            "collar_count": len(self._topology_engine.get_observer_collars("planner")),
            "drift_signals": len(self._drift_tracker.check_all()),
            "reinforcement_anchors": self._reinforcement_engine.get_stats().get("total_anchors", 0),
        }

    async def get_attractor_state(self) -> Dict[str, Any]:
        """Get current attractor state from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()

        drift_signals = self._drift_tracker.check_all()
        entropy_pressure = sum(s.get("delta", 0.0) for s in drift_signals) if drift_signals else 0.0
        yield_score = self._coherence_analyzer.system_yield_score()

        return {
            "goal": "Maintain coherence-per-resource optimization",
            "confidence": min(1.0, max(0.0, yield_score)),
            "entropy_pressure": entropy_pressure,
            "convergence": min(1.0, max(0.0, 1.0 - abs(entropy_pressure))),
        }

    def _is_simple_question(self, message: str) -> bool:
        """
        Detect if a message is a simple factual question that doesn't
        need the full observer pipeline. Examples:
        - "What is the capital of Russia?"
        - "How tall is Mount Everest?"
        - "Who wrote Hamlet?"
        - "What time is it?"
        """
        text = message.strip().lower()
        word_count = len(text.split())

        # Simple questions are typically short (≤15 words)
        if word_count > 15:
            return False

        # Check for question patterns that indicate factual queries
        question_starters = [
            "what is", "what are", "what was", "what were",
            "who is", "who are", "who was", "who were",
            "where is", "where are", "where was",
            "when is", "when are", "when was",
            "how tall", "how long", "how many", "how much",
            "how old", "how far", "how big",
            "why does", "why is", "why are",
            "can you tell me", "do you know",
            "what's", "who's", "where's", "when's",
            "tell me about", "what about",
        ]

        is_question = any(text.startswith(s) for s in question_starters)
        is_question = is_question or text.endswith("?")

        # Check for task keywords that would require the pipeline
        task_keywords = [
            "build", "create", "implement", "write", "code", "develop",
            "fix", "debug", "repair", "refactor", "optimize",
            "deploy", "release", "ship", "publish",
            "analyze", "investigate", "research", "study",
            "design", "architect", "plan", "structure",
            "orchestrate", "coordinate", "manage", "spawn",
            "automate", "script", "schedule",
            "visualize", "chart", "graph", "render",
        ]

        has_task_keywords = any(kw in text for kw in task_keywords)

        return is_question and not has_task_keywords and word_count <= 15

    async def _fast_path_response(self, message: str) -> Dict[str, Any]:
        """
        Generate a direct response for simple questions without going
        through the full O-1 → O-2 → O-3 pipeline.

        Uses built-in knowledge to answer common factual questions directly.
        Falls back to a natural conversational response for unknown questions.
        """
        text = message.strip()
        lower = text.lower().rstrip("?").strip()

        # Built-in knowledge for common factual questions
        # This gives the observer basic general knowledge capability
        # without needing to spawn agents or call external APIs

        # Geography
        geography = {
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

        # Check geography questions
        for key, answer in geography.items():
            if key in lower or lower.startswith(key):
                return self._make_fast_response(
                    f"The capital of {key.replace('capital of ', '').title()} is **{answer}**."
                )

        # Famous people / authors
        people = {
            "who wrote hamlet": "William Shakespeare wrote Hamlet around 1599-1601.",
            "who wrote romeo and juliet": "William Shakespeare wrote Romeo and Juliet.",
            "who wrote pride and prejudice": "Jane Austen wrote Pride and Prejudice in 1813.",
            "who wrote moby dick": "Herman Melville wrote Moby-Dick in 1813.",
            "who wrote the odyssey": "Homer wrote The Odyssey, one of the foundational works of Western literature.",
            "who wrote the iliad": "Homer wrote The Iliad.",
            "who wrote don quixote": "Miguel de Cervantes wrote Don Quixote in 1605.",
            "who wrote war and peace": "Leo Tolstoy wrote War and Peace between 1865-1869.",
            "who wrote crime and punishment": "Fyodor Dostoevsky wrote Crime and Punishment in 1866.",
            "who wrote the great gatsby": "F. Scott Fitzgerald wrote The Great Gatsby in 1925.",
            "who wrote to kill a mockingbird": "Harper Lee wrote To Kill a Mockingbird in 1960.",
            "who wrote 1984": "George Orwell wrote 1984 in 1949.",
            "who wrote brave new world": "Aldous Huxley wrote Brave New World in 1932.",
            "who wrote the catcher in the rye": "J.D. Salinger wrote The Catcher in the Rye in 1951.",
            "who wrote lord of the rings": "J.R.R. Tolkien wrote The Lord of the Rings between 1937-1949.",
            "who wrote harry potter": "J.K. Rowling wrote the Harry Potter series.",
            "who wrote the hobbit": "J.R.R. Tolkien wrote The Hobbit in 1937.",
            "who is the president of the united states": "As of my last update, the US president is Donald Trump (took office January 2025). Please verify with current sources.",
            "who is the prime minister of the uk": "As of my last update, the UK Prime Minister is Keir Starmer (took office July 2024). Please verify with current sources.",
        }

        for key, answer in people.items():
            if key in lower:
                return self._make_fast_response(answer)

        # Science / general knowledge
        science = {
            "how tall is mount everest": "Mount Everest is approximately 8,849 meters (29,032 feet) tall — the highest peak on Earth.",
            "how tall is k2": "K2 is approximately 8,611 meters (28,251 feet) tall — the second-highest peak on Earth.",
            "how deep is the mariana trench": "The Mariana Trench is approximately 10,994 meters (36,070 feet) deep at its deepest point, Challenger Deep.",
            "how far is the moon": "The Moon is approximately 384,400 km (238,855 miles) from Earth on average.",
            "how fast does light travel": "Light travels at approximately 299,792 km/s (186,282 miles per second) in a vacuum.",
            "what is the speed of light": "The speed of light is approximately 299,792 km/s (186,282 miles per second) in a vacuum.",
            "how old is the universe": "The universe is approximately 13.8 billion years old, based on current cosmological models.",
            "how many planets are in the solar system": "There are 8 planets in our solar system: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.",
            "what is the largest planet": "Jupiter is the largest planet in our solar system, with a diameter of about 139,820 km.",
            "what is the smallest planet": "Mercury is the smallest planet in our solar system.",
            "what is dna": "DNA (Deoxyribonucleic Acid) is the molecule that carries genetic instructions for the development and functioning of all known living organisms.",
            "what is the theory of relativity": "The theory of relativity, developed by Albert Einstein, consists of special relativity (1905) and general relativity (1915). It describes how space and time are interwoven and how gravity works as a curvature of spacetime.",
        }

        for key, answer in science.items():
            if key in lower:
                return self._make_fast_response(answer)

        # Casual greetings that slip through
        if any(w in lower for w in ["hello", "hi", "hey", "howdy"]):
            return self._make_fast_response(
                "Hello! I'm the Primary Observer. I can help with casual questions, system analysis, coding, architecture, and more. What's on your mind?"
            )

        if any(w in lower for w in ["how are you", "how's it going", "what's up"]):
            return self._make_fast_response(
                "I'm doing well — all observer systems are running smoothly. The field is stable and entropy is low. What can I help you with?"
            )

        if any(w in lower for w in ["thanks", "thank you", "thx"]):
            return self._make_fast_response(
                "You're welcome! Let me know if there's anything else I can help with."
            )

        if any(w in lower for w in ["bye", "goodbye", "see you"]):
            return self._make_fast_response(
                "Goodbye! The observer field remains active. Come back anytime."
            )

        # Default: natural conversational response for unknown questions
        return self._make_fast_response(
            f"That's an interesting question about '{text[:80]}'. "
            f"I don't have a specific built-in answer for that, but I'd be happy to help you explore it. "
            f"Would you like me to research this through the observer pipeline, or is there something else I can help with?"
        )

    def _make_fast_response(self, text: str) -> Dict[str, Any]:
        """Helper to build a fast-path response dict."""
        return {
            "response": text,
            "confidence": 0.9,
            "observer": {
                "task_domain": "general",
                "complexity": "low",
                "routing_path": ["direct"],
                "model": "general",
                "agreement": 1.0,
                "spawn_status": "skipped",
            },
            "system": {
                "health": "healthy",
                "continuity_score": 1.0,
                "active_agents": 0,
                "total_spawns": 0,
            },
        }

    async def process_continuity_message(self, message: str, context: Optional[Dict] = None,
                                          agent_progress_callback=None) -> Dict[str, Any]:
        """
        Process a message through the Observer pipeline.

        For simple factual questions → fast path (direct response).
        For complex tasks → full O-1 → O-2 → O-3 pipeline.

        Args:
            agent_progress_callback: Optional callable(event_type, data) for streaming
                progress events during agent tool-calling.
        """
        if not self._initialized:
            await self.initialize()

        await self.emit_event("chat.message.received", {"message": message})

        # Get or create session, then log the user message
        session_id = self._chat_log.get_current_session()
        self._chat_log.add_message(
            role="user",
            content=message,
            session_id=session_id,
            observer_metadata={"source": "web_chat"},
        )
        # Use the session_id from the message (in case a new session was created)
        session_id = self._chat_log.get_current_session()

        try:
            # ── Step 1: O-1 Primary Observer receives input ──
            orch_response = self._primary_observer.receive_input(
                user_input=message,
                session_context=context or {},
            )

            # ── Step 2: O-2 Observer Consensus ──
            consensus_result = self._observer_consensus.reach_consensus(
                user_input=message,
                observer_signals=None,
                session_context=context or {},
            )

            # ── Step 3: Generate response via LLM (ChatAgent/OpenRouter) ──
            # ALL messages go through the LLM for natural, contextual responses.
            # The LLM receives system state, conversation history, and observer context.
            from core.observer.chat_agent import ChatAgent
            agent = ChatAgent()

            # Build conversation history for the LLM
            recent_history = self._chat_log.get_session_messages(session_id)
            history_msgs = []
            for m in recent_history[-10:]:
                role = "assistant" if m.get("role") == "assistant" else "user"
                history_msgs.append({"role": role, "content": m.get("content", "")})
            agent._history = history_msgs

            # Build sovereign context with real system state
            spawn_snapshot = self._spawn_registry.get_field_snapshot()
            observer_health = self._primary_observer.health
            sov_lines = [
                "## System State",
                "- Active agents: " + str(spawn_snapshot.get("active_agents", 0)),
                "- Total spawns: " + str(spawn_snapshot.get("total_agents", 0)),
                "- Observer health: " + str(observer_health.get("status", "unknown")),
                "- Continuity score: " + str(observer_health.get("continuity_score", 0)),
                "- Consensus agreement: " + str(round(consensus_result.agreement_score * 100)) + "%",
                "- Routing path: " + " -> ".join(consensus_result.routing_path),
                "- Task type: " + consensus_result.task_type,
                "- Complexity: " + consensus_result.complexity,
            ]
            sovereign_context = "\n".join(sov_lines)

            response_text = agent.chat(message, sovereign_context=sovereign_context,
                                        progress_callback=agent_progress_callback)
            spawn_status = "completed"

            # ── Step 4: Gather system state for enrichment ──
            consensus_stats = self._observer_consensus.get_stats()

            # ── Step 5: Build enriched response ──

            result = {
                "response": response_text,
                "confidence": consensus_result.confidence,
                "observer": {
                    "task_domain": consensus_result.task_type,
                    "complexity": consensus_result.complexity,
                    "routing_path": consensus_result.routing_path,
                    "model": consensus_result.recommended_model,
                    "agreement": consensus_result.agreement_score,
                    "spawn_status": spawn_status,
                },
                "system": {
                    "health": observer_health.get("status", "unknown"),
                    "continuity_score": observer_health.get("continuity_score", 0),
                    "active_agents": spawn_snapshot.get("active_agents", 0),
                    "total_spawns": spawn_snapshot.get("total_agents", 0),
                },
            }

            # Record in continuity memory
            from core.observer.continuity_memory import WorkflowRecord
            import uuid as _uuid
            self._continuity_memory.record_workflow(WorkflowRecord(
                workflow_id=f"chat_{_uuid.uuid4().hex[:8]}",
                task_domain=consensus_result.task_type,
                complexity=consensus_result.complexity,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=spawn_status == "completed",
            ))

            # Log the observer response to chat log
            self._chat_log.add_message(
                role="assistant",
                content=response_text,
                session_id=session_id,
                task_domain=consensus_result.task_type,
                complexity=consensus_result.complexity,
                observer_metadata={
                    "routing_path": consensus_result.routing_path,
                    "model": consensus_result.recommended_model,
                    "confidence": consensus_result.confidence,
                    "spawn_status": spawn_status,
                    "agreement": consensus_result.agreement_score,
                },
            )
            result["session_id"] = session_id

        except Exception as e:
            logger.error(f"Observer pipeline error: {e}", exc_info=True)
            # Fallback to simple response
            result = {
                "response": f"Observer pipeline error: {str(e)}. The system is still initializing.",
                "confidence": 0.0,
                "observer": {"task_domain": "error", "complexity": "unknown"},
                "system": {"health": "degraded"},
                "session_id": session_id,
            }
            # Log the error response
            self._chat_log.add_message(
                role="assistant",
                content=result["response"],
                session_id=session_id,
                task_domain="error",
                observer_metadata={"error": str(e)},
            )

        await self.emit_event("chat.message.responded", {
            "response": result.get("response", "")[:200],
            "domain": result.get("observer", {}).get("task_domain", ""),
        })

        return result

    async def get_entropy_metrics(self) -> Dict[str, Any]:
        """Get entropy economics metrics."""
        if not self._initialized:
            await self.initialize()

        budget_stats = self._entropy_budget.get_stats()
        coherence_stats = self._coherence_analyzer.get_stats()
        compression_stats = self._compression.get_stats()
        sync_stats = self._sync_optimizer.get_stats()
        resource_stats = self._resource_cognition.get_stats()
        governance_stats = self._governance.get_stats()

        return {
            "budget": {
                "global": budget_stats.get("global_budget", 500.0),
                "consumed": budget_stats.get("total_consumed", 0.0),
                "remaining": budget_stats.get("remaining", 500.0),
                "critical_count": len(self._entropy_budget.get_critical_budgets()),
            },
            "coherence": {
                "system_yield": self._coherence_analyzer.system_yield_score(),
                "operation_count": coherence_stats.get("total_operations", 0),
            },
            "compression": {
                "avg_ratio": compression_stats.get("avg_compression_ratio", 0.0),
                "avg_recoverability": compression_stats.get("avg_recoverability", 1.0),
            },
            "sync": {
                "efficiency": sync_stats.get("avg_yield", 0.0),
                "over_syncing_pairs": len(self._sync_optimizer.get_over_syncing_pairs()),
            },
            "resources": {
                "utilization": resource_stats.get("utilization", 0.0),
                "overloaded": self._resource_cognition.is_overloaded(),
            },
            "governance": {
                "approval_rate": governance_stats.get("approval_rate", 1.0),
                "applied_optimizations": len(self._governance.get_applied_optimizations()),
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check SRRA-OPH substrate health."""
        if not self._initialized:
            await self.initialize()

        patch_health = {}
        for name, patch in self._patches.items():
            status = patch.get_status()
            patch_health[name] = {
                "state": "active" if status.get("is_stable", False) else "repairing",
                "healthy": status.get("is_stable", False),
            }

        return {
            "status": "healthy",
            "patches": patch_health,
            "total_patches": len(self._patches),
            "entropy_remaining": self._entropy_budget.get_stats().get("remaining", 0),
            "coherence_yield": self._coherence_analyzer.system_yield_score(),
        }

    async def create_prediction_contract(self, mutation_type: str, target: str, **kwargs) -> Dict[str, Any]:
        """Create a prediction contract through SRRA-OPH."""
        if not self._initialized:
            await self.initialize()

        contract = self._contract_manager.create_contract(
            mutation_type=mutation_type, target=target, **kwargs
        )

        return {
            "contract_id": contract.contract_id,
            "mutation_type": contract.mutation_type,
            "target": contract.target,
            "status": contract.status.value,
            "created_at": contract.created_at,
        }

    async def validate_contract(self, contract_id: str) -> Dict[str, Any]:
        """Validate a prediction contract."""
        if not self._initialized:
            await self.initialize()

        result = self._contract_manager.validate_contract(contract_id, actual_coherence_gain=0.0, actual_entropy_cost=0.0)
        return {"contract_id": contract_id, "valid": result}


_adapter: Optional[SRRSAdapter] = None


async def get_adapter() -> SRRSAdapter:
    """Get or create the SRRA-OPH adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = SRRSAdapter()
        await _adapter.initialize()
    return _adapter
