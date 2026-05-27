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
from core.observer import (
    PrimaryObserver, ObserverState, RuntimeAwareness,
    TaskIntentAnalyzer, ContextDistiller, ContinuityMemory,
    ObserverSession, ObserverLifecycle, EventAwareness,
)
# O-2 Consensus
from core.consensus import (
    ObserverConsensus, TaskClassifier, RoutingConsensus,
    ComplexityScorer, SpawnPlanner, ModelSelector,
    CapabilityMatcher, ConsensusMemory, ObserverSpecialization,
    ConsensusReplay,
)
# O-3 Spawn Engine
from core.spawn import (
    AgentSpawner, SpawnBlueprint,
    ContextInjector, AgentLifecycle, ExecutionBoundary,
    MultiAgentCoordinator, TraceFeedback, SpawnReplay,
    SpawnRegistry, SpawnRecord,
)
from core.spawn.agent_spawner import SpawnResult


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
            from event_fabric import get_fabric
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

    async def process_continuity_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a message through the full Observer pipeline.

        Pipeline:
        1. O-1: PrimaryObserver receives input, analyzes intent
        2. O-2: ObserverConsensus reaches consensus on routing
        3. O-3: AgentSpawner generates response via spawn pipeline
        4. Response enriched with system state
        """
        if not self._initialized:
            await self.initialize()

        await self.emit_event("chat.message.received", {"message": message})

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

            # ── Step 3: O-3 Spawn pipeline for response generation ──
            spawn_result = await self._agent_spawner.spawn(
                user_input=message,
                session_context={
                    "last_domain": orch_response.task_domain,
                    "last_complexity": orch_response.complexity,
                    **(context or {}),
                },
            )

            # ── Step 4: Gather system state for enrichment ──
            observer_health = self._primary_observer.health
            consensus_stats = self._observer_consensus.get_stats()
            spawn_snapshot = self._spawn_registry.get_field_snapshot()

            # ── Step 5: Build enriched response ──
            response_text = spawn_result.output if spawn_result.status == "completed" else orch_response.message

            result = {
                "response": response_text,
                "confidence": consensus_result.confidence,
                "observer": {
                    "task_domain": consensus_result.task_type,
                    "complexity": consensus_result.complexity,
                    "routing_path": consensus_result.routing_path,
                    "model": consensus_result.recommended_model,
                    "agreement": consensus_result.agreement_score,
                    "spawn_status": spawn_result.status,
                },
                "system": {
                    "health": observer_health.get("status", "unknown"),
                    "continuity_score": observer_health.get("continuity_score", 0),
                    "active_agents": spawn_snapshot.get("active_agents", 0),
                    "total_spawns": spawn_snapshot.get("total_agents", 0),
                },
            }

            # Record in continuity memory
            self._continuity_memory.record({
                "type": "chat_interaction",
                "domain": consensus_result.task_type,
                "complexity": consensus_result.complexity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        except Exception as e:
            logger.error(f"Observer pipeline error: {e}", exc_info=True)
            # Fallback to simple response
            result = {
                "response": f"Observer pipeline error: {str(e)}. The system is still initializing.",
                "confidence": 0.0,
                "observer": {"task_domain": "error", "complexity": "unknown"},
                "system": {"health": "degraded"},
            }

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
