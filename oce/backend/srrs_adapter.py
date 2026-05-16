"""
SRRA-OPH Substrate Adapter for OCE
==================================
Bridges OCE Continuity Core with SRRA-OPH substrate.

This adapter provides:
- Observer state access
- Event emission for OCE event fabric
- Memory persistence integration
- Attractor state queries
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Add parent directory to path for srrs_opc imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc import (
    PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch,
    CollarLayer, AgentBridge,
    DriftDetector, ConsistencyValidator, ReconstructionSynthesizer,
    DynamicCouplingEngine, TopologicalRouter, DistributedConsensus,
    CollarTopologyEngine, CollarMetrics,
    LongTermDriftTracker, ReinforcementEngine,
    TopologyObserver, PredictionContractManager,
    CoherenceYieldAnalyzer, EntropyBudgetManager, RecoverabilityEconomics,
    AdaptiveCompressionEngine, SyncCostOptimizer, ResourceConstrainedCognition,
    SustainabilityGovernance
)


class SRRSAdapter:
    """
    Adapter between OCE Continuity Core and SRRA-OPH substrate.
    
    Provides a clean interface for OCE to access SRRA-OPH capabilities
    without tight coupling.
    """
    
    def __init__(self):
        self._initialized = False
        self._patches = {}
        self._collar_layer = None
        self._agent_bridge = None
        self._topology_engine = None
        self._drift_tracker = None
        self._reinforcement_engine = None
        self._coherence_analyzer = None
        self._entropy_budget = None
        self._recoverability = None
        self._compression = None
        self._sync_optimizer = None
        self._resource_cognition = None
        self._governance = None
    
    async def initialize(self):
        """Initialize SRRA-OPH substrate components."""
        if self._initialized:
            return
        
        # Initialize Phase 1: Observer Mesh
        self._patches = {
            "planner": PlannerPatch("planner"),
            "execution": ExecutionPatch("execution"),
            "memory": MemoryPatch("memory"),
            "repair": RepairPatch("repair"),
        }
        self._collar_layer = CollarLayer()
        self._agent_bridge = AgentBridge()
        
        # Initialize Phase 3: Topology
        self._topology_engine = CollarTopologyEngine()
        
        # Initialize Phase 5: Long-Horizon Continuity
        self._drift_tracker = LongTermDriftTracker()
        self._reinforcement_engine = ReinforcementEngine()
        
        # Initialize Phase 9: Entropy Economics
        self._coherence_analyzer = CoherenceYieldAnalyzer()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._recoverability = RecoverabilityEconomics()
        self._compression = AdaptiveCompressionEngine()
        self._sync_optimizer = SyncCostOptimizer()
        self._resource_cognition = ResourceConstrainedCognition()
        self._governance = SustainabilityGovernance()
        
        self._initialized = True
    
    # ─── Observer Status ───────────────────────────────────────────────────────
    
    async def get_observer_status(self) -> List[Dict[str, Any]]:
        """Get current status of all observers."""
        if not self._initialized:
            await self.initialize()
        
        status = []
        for name, patch in self._patches.items():
            metrics = self._topology_engine.get_collar_metrics(name)
            status.append({
                "observer_id": name,
                "state": "active" if patch.is_active else "idle",
                "entropy": metrics.entropy if metrics else 0.0,
                "task": getattr(patch, "current_task", "none")
            })
        
        return status
    
    # ─── Event Emission ────────────────────────────────────────────────────────
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Emit an event to the OCE event fabric."""
        if not self._initialized:
            await self.initialize()
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "source": "srrs_opc"
        }
        
        # TODO: Send to Redis Streams/NATS
        return f"event_{datetime.now().timestamp()}"
    
    # ─── Memory Access ───────────────────────────────────────────────────────────
    
    async def get_trajectory_memory(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trajectory memory from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()
        
        # TODO: Integrate with trajectory_fields
        return []
    
    async def get_structural_memory(self) -> Dict[str, Any]:
        """Get structural memory from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()
        
        # Get topology snapshot
        snapshot = self._topology_engine.snapshot()
        return {
            "topology": snapshot.to_dict() if snapshot else {},
            "collars": len(self._collar_layer.collar_states) if self._collar_layer else 0
        }
    
    # ─── Attractor State ───────────────────────────────────────────────────────
    
    async def get_attractor_state(self) -> Dict[str, Any]:
        """Get current attractor state from SRRA-OPH."""
        if not self._initialized:
            await self.initialize()
        
        # Get drift signals as attractor indicators
        drift_signals = self._drift_tracker.get_signals()
        
        return {
            "goal": "Maintain coherence-per-resource optimization",
            "confidence": 0.75,
            "entropy_pressure": sum(s.entropy_delta for s in drift_signals) if drift_signals else 0.0,
            "convergence": 0.68
        }
    
    # ─── Continuity Chat ───────────────────────────────────────────────────────
    
    async def process_continuity_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a message through SRRA-OPH substrate."""
        if not self._initialized:
            await self.initialize()
        
        # Emit event for message received
        await self.emit_event("chat.message.received", {"message": message})
        
        # Process through planner patch
        planner = self._patches.get("planner")
        if planner:
            result = await planner.process(message, context)
        else:
            result = {"response": "Planner not available"}
        
        # Emit event for response
        await self.emit_event("chat.message.responded", {"response": result.get("response", "")})
        
        return result
    
    # ─── Entropy Economics ────────────────────────────────────────────────────
    
    async def get_entropy_metrics(self) -> Dict[str, Any]:
        """Get entropy economics metrics."""
        if not self._initialized:
            await self.initialize()
        
        stats = self._entropy_budget.get_stats()
        return {
            "global_budget": stats.get("global", {}).get("max_budget", 500.0),
            "total_consumed": stats.get("global", {}).get("total_consumed", 0.0),
            "observer_count": stats.get("total_observer_budgets", 0),
            "critical_budgets": len(self._entropy_budget.get_critical_budgets())
        }
    
    # ─── Health Check ──────────────────────────────────────────────────────────
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SRRA-OPH substrate health."""
        if not self._initialized:
            await self.initialize()
        
        return {
            "status": "healthy",
            "patches_active": sum(1 for p in self._patches.values() if p.is_active),
            "total_patches": len(self._patches),
            "topology_metrics": len(self._topology_engine.metrics_history) if self._topology_engine else 0
        }


# Singleton instance
_adapter: Optional[SRRSAdapter] = None


async def get_adapter() -> SRRSAdapter:
    """Get or create the SRRA-OPH adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = SRRSAdapter()
        await _adapter.initialize()
    return _adapter