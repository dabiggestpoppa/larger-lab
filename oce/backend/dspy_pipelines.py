"""
DSPy Pipelines for OCE
======================
DSPy-optimized pipelines for OCE operations.

Pipelines:
1. Contract Generation - Optimized prediction contract parameters
2. Event Routing - Optimal event routing through overlap topology
3. Evolution Planning - Adaptive topology mutation planning

All pipelines gracefully degrade when DSPy is not installed.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# Add parent directory to path for srrs_opc imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc import (
    CoherenceYieldAnalyzer,
    EntropyBudgetManager,
    RecoverabilityEconomics,
    AdaptiveCompressionEngine,
    SyncCostOptimizer,
    CollarTopologyEngine,
)

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None


# ─── Pipeline 1: Contract Generation ──────────────────────────────────────────

class ContractGenerationPipeline:
    """
    DSPy-optimized prediction contract generation.
    
    Uses historical mutation outcomes to optimize contract parameters
    for maximum coherence yield and minimum entropy cost.
    """
    
    def __init__(self, lm: Optional[Any] = None):
        self.lm = lm
        self._coherence_analyzer = CoherenceYieldAnalyzer()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._recoverability = RecoverabilityEconomics()
        self._compression = AdaptiveCompressionEngine()
        self._history: List[Dict[str, Any]] = []
    
    def generate_contract_params(self, mutation_type: str, target: str,
                                  historical_accuracy: float = 0.5,
                                  coherence_metrics: Optional[Dict] = None) -> Dict[str, float]:
        """
        Generate optimized contract parameters.
        
        When DSPy is available, uses learned optimization.
        When not available, uses heuristic-based estimation.
        """
        if DSPY_AVAILABLE and self.lm:
            return self._dspy_generate(mutation_type, target, historical_accuracy, coherence_metrics)
        return self._heuristic_generate(mutation_type, target, historical_accuracy, coherence_metrics)
    
    def _dspy_generate(self, mutation_type: str, target: str,
                        historical_accuracy: float,
                        coherence_metrics: Optional[Dict]) -> Dict[str, float]:
        """DSPy-optimized generation."""
        # Use DSPy signature for optimization
        from srrs_opc.dspy_contracts import DSPyContractGenerator
        generator = DSPyContractGenerator()
        if self.lm:
            dspy.configure(lm=self.lm)
        
        return generator(
            mutation_type=mutation_type,
            target=target,
            historical_accuracy=str(historical_accuracy),
            coherence_metrics=str(coherence_metrics or {})
        )
    
    def _heuristic_generate(self, mutation_type: str, target: str,
                            historical_accuracy: float,
                            coherence_metrics: Optional[Dict]) -> Dict[str, float]:
        """Heuristic-based generation (no DSPy required)."""
        # Base estimates from historical accuracy
        base_coherence_gain = historical_accuracy * 0.6
        base_entropy_cost = (1.0 - historical_accuracy) * 0.3
        
        # Adjust based on mutation type
        mutation_multipliers = {
            "weaken_edge": (0.4, 0.2),
            "strengthen_edge": (0.8, 0.4),
            "add_node": (0.6, 0.5),
            "remove_node": (0.3, 0.1),
            "restructure": (0.7, 0.6),
        }
        
        mult = mutation_multipliers.get(mutation_type, (0.5, 0.3))
        
        coherence_gain = min(1.0, base_coherence_gain * mult[0] * 1.5)
        entropy_cost = min(1.0, base_entropy_cost * mult[1] * 1.5)
        
        # Get current system state
        system_yield = self._coherence_analyzer.system_yield_score()
        compression_ratio = self._compression.compression_ratio()
        
        return {
            "expected_coherence_gain": round(coherence_gain, 4),
            "expected_entropy_cost": round(entropy_cost, 4),
            "expected_repair_burden": round(entropy_cost * 0.5, 4),
            "expected_reconstruction_viability": round(max(0.0, 1.0 - compression_ratio), 4),
            "rollback_feasibility": round(max(0.0, 1.0 - entropy_cost * 2), 4),
        }
    
    def record_outcome(self, mutation_type: str, target: str,
                       predicted: Dict[str, float], actual: Dict[str, float]):
        """Record actual outcome for future optimization."""
        self._history.append({
            "mutation_type": mutation_type,
            "target": target,
            "predicted": predicted,
            "actual": actual,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# ─── Pipeline 2: Event Routing ────────────────────────────────────────────────

class EventRoutingPipeline:
    """
    DSPy-optimized event routing through overlap topology.
    
    Determines optimal routing paths for events based on
    current observer state and entropy levels.
    """
    
    def __init__(self):
        self._topology_engine = CollarTopologyEngine()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._sync_optimizer = SyncCostOptimizer()
    
    def route_event(self, event_type: str, observer_state: Dict[str, Any],
                    entropy_level: float) -> Dict[str, Any]:
        """
        Determine optimal routing for an event.
        
        Returns routing decision with path, priority, and estimated cost.
        """
        # Get current topology state
        system_metrics = self._topology_engine.get_system_metrics()
        
        # Determine priority based on event type
        priority_map = {
            "chat.message": "normal",
            "observer.status": "low",
            "entropy.critical": "critical",
            "repair.triggered": "high",
            "contract.created": "normal",
            "topology.mutation": "high",
        }
        
        priority = priority_map.get(event_type.split(".")[0] + "." + event_type.split(".")[1], "normal")
        
        # Calculate entropy budget impact
        budget_impact = self._estimate_budget_impact(event_type, entropy_level)
        
        # Determine if sync is needed
        should_sync = self._sync_optimizer.should_sync(
            obs_a="planner",
            obs_b="execution",
            coherence_gain=1.0 - entropy_level,
            entropy_cost=entropy_level
        )
        
        return {
            "event_type": event_type,
            "priority": priority,
            "should_sync": should_sync,
            "budget_impact": budget_impact,
            "recommended_path": self._get_optimal_path(event_type, priority),
            "estimated_cost": budget_impact * 0.1,
        }
    
    def _estimate_budget_impact(self, event_type: str, entropy_level: float) -> float:
        """Estimate entropy budget impact of an event."""
        base_cost = 0.01  # Base cost per event
        entropy_multiplier = 1.0 + entropy_level
        return base_cost * entropy_multiplier
    
    def _get_optimal_path(self, event_type: str, priority: str) -> List[str]:
        """Get optimal routing path based on event type and priority."""
        if priority == "critical":
            return ["planner", "execution", "repair"]
        elif priority == "high":
            return ["planner", "execution"]
        else:
            return ["planner"]


# ─── Pipeline 3: Evolution Planning ───────────────────────────────────────────

class EvolutionPlanningPipeline:
    """
    DSPy-optimized adaptive evolution planning.
    
    Plans topology mutations based on coherence yield analysis
    and entropy budget constraints.
    """
    
    def __init__(self):
        self._coherence_analyzer = CoherenceYieldAnalyzer()
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._recoverability = RecoverabilityEconomics()
        self._compression = AdaptiveCompressionEngine()
        self._sync_optimizer = SyncCostOptimizer()
        self._topology_engine = CollarTopologyEngine()
    
    def plan_evolution(self, current_metrics: Dict[str, Any],
                       entropy_budget_remaining: float,
                       coherence_targets: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate an evolution plan based on current state and targets.
        
        Returns a prioritized list of recommended mutations.
        """
        # Get current system state
        system_yield = self._coherence_analyzer.system_yield_score()
        compression_stats = self._compression.get_stats()
        sync_stats = self._sync_optimizer.get_stats()
        
        # Identify inefficiencies
        inefficient = self._coherence_analyzer.identify_inefficient()
        
        # Generate mutation recommendations
        mutations = []
        
        # Check if compression is needed
        if compression_stats.get("avg_recoverability", 1.0) < 0.8:
            mutations.append({
                "type": "compress_state",
                "target": "memory",
                "priority": "high",
                "expected_yield_improvement": 0.15,
                "entropy_cost": 0.05,
            })
        
        # Check if sync optimization is needed
        over_syncing = self._sync_optimizer.get_over_syncing_pairs()
        if over_syncing:
            mutations.append({
                "type": "weaken_edge",
                "target": f"{over_syncing[0][0]}-{over_syncing[0][1]}",
                "priority": "medium",
                "expected_yield_improvement": 0.1,
                "entropy_cost": 0.02,
            })
        
        # Check if topology restructuring is needed
        weak_collars = self._topology_engine.identify_weak_collars()
        for collar in weak_collars[:3]:  # Top 3 weakest
            mutations.append({
                "type": "strengthen_edge",
                "target": collar.get("id", "unknown"),
                "priority": "medium",
                "expected_yield_improvement": 0.08,
                "entropy_cost": 0.03,
            })
        
        # Sort by yield improvement per entropy cost (efficiency)
        for m in mutations:
            m["efficiency"] = m["expected_yield_improvement"] / max(m["entropy_cost"], 0.001)
        
        mutations.sort(key=lambda x: x["efficiency"], reverse=True)
        
        # Filter by budget
        affordable_mutations = []
        total_cost = 0.0
        for m in mutations:
            if total_cost + m["entropy_cost"] <= entropy_budget_remaining * 0.1:  # Use max 10% of remaining
                affordable_mutations.append(m)
                total_cost += m["entropy_cost"]
        
        return {
            "current_yield": system_yield,
            "target_yield": coherence_targets.get("min_yield", 0.7),
            "entropy_budget_remaining": entropy_budget_remaining,
            "recommended_mutations": affordable_mutations,
            "total_estimated_cost": total_cost,
            "expected_yield_after": system_yield + sum(m["expected_yield_improvement"] for m in affordable_mutations),
        }


# ─── Pipeline Manager ─────────────────────────────────────────────────────────

class OCEPipelineManager:
    """
    Manages all DSPy pipelines for OCE.
    
    Provides a unified interface for contract generation,
    event routing, and evolution planning.
    """
    
    def __init__(self, lm: Optional[Any] = None):
        self.contract_pipeline = ContractGenerationPipeline(lm=lm)
        self.routing_pipeline = EventRoutingPipeline()
        self.evolution_pipeline = EvolutionPlanningPipeline()
        self._dspy_available = DSPY_AVAILABLE
    
    @property
    def dspy_available(self) -> bool:
        """Whether DSPy is available for optimization."""
        return self._dspy_available
    
    def generate_contract(self, mutation_type: str, target: str, **kwargs) -> Dict[str, float]:
        """Generate optimized contract parameters."""
        return self.contract_pipeline.generate_contract_params(mutation_type, target, **kwargs)
    
    def route_event(self, event_type: str, observer_state: Dict, entropy_level: float) -> Dict[str, Any]:
        """Route an event through optimal path."""
        return self.routing_pipeline.route_event(event_type, observer_state, entropy_level)
    
    def plan_evolution(self, current_metrics: Dict, budget: float, targets: Dict) -> Dict[str, Any]:
        """Plan adaptive evolution."""
        return self.evolution_pipeline.plan_evolution(current_metrics, budget, targets)
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline manager status."""
        return {
            "dspy_available": self._dspy_available,
            "contract_history_size": len(self.contract_pipeline._history),
            "pipelines": {
                "contract_generation": "active",
                "event_routing": "active",
                "evolution_planning": "active",
            },
        }
