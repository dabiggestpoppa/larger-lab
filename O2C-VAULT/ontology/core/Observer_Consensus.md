# Observer Consensus

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B1: ObserverConsensus
========================
Coordinate distributed observer decision-making.

Aggregates signals from multiple observers to reach consensus
on task routing, complexity estimation, and execution strategy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.consensus.task_classifier import TaskClassifier, TaskType
from core.consensus.routing_consensus import RoutingConsensus
from core.consensus.complexity_scorer import ComplexityScorer
from core.consensus.capability_matcher import CapabilityMatcher
from core.consensus.consensus_memory import ConsensusMemory

logger = logging.getLogger("consensus.observer")


@dataclass
class ConsensusResult:
    """Result of observer consensus process."""
    task_type: str
    complexity: str
    confidence: float
    routing_path: list[str]
    required_capabilities: list[str]
    recommended_model: str
    spawn_required: bool
    timestamp: str
    voter_count: int
    agreement_score: float  # 0.0-1.0, how much observers agree
    metadata: dict[str, Any] = field(default_factory=dict)


class ObserverConsensus:
    """
    Coordinates distributed observer decision-making.

    Each observer votes on task classification, routing, and complexity.
    Consensus is reached through weighted voting based on observer
    specialization and historical accuracy.
    """

    def __init__(self):
        self.task_classifier = TaskClassifier()
        self.routing_consensus = RoutingConsensus()
        self.complexity_scorer = ComplexityScorer()
        self.capability_matcher = CapabilityMatcher()
        self.memory = ConsensusMemory()
        self._observer_weights: dict[str, float] = {}

    def reach_consensus(
        self,
        user_input: str,
        observer_signals: list[dict[str, Any]] | None = None,
        session_context: dict[str, Any] | None = None,
    ) -> ConsensusResult:
        """
        Reach consensus on how to handle a user request.

        Args:
            user_input: The raw user message
            observer_signals: Signals from individual observers (optional)
            session_context: Current session context (optional)

        Returns:
            ConsensusResult with agreed-upon routing and execution plan
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1: Classify task type
        classification = self.task_classifier.classify(user_input)
        task_type = classification["task_type"]
        type_confidence = classification["confidence"]

        # Step 2: Score complexity
        complexity_result = self.complexity_scorer.score(user_input, task_type)
        complexity = complexity_result["level"]

        # Step 3: Determine routing path
        routing = self.routing_consensus.determine_path(
            task_type=task_type,
            complexity=complexity,
            signals=observer_signals or [],
        )

        # Step 4: Match capabilities
        capabilities = self.capability_matcher.match(
            task_type=task_type,
            complexity=complexity,
            routing_path=routing["path"],
        )

        # Step 5: Select model
        model = self._select_model(task_type, complexity, capabilities)

        # Step 6: Determine if spawning is needed
        spawn_required = self._should_spawn(task_type, complexity, capabilities)

        # Step 7: Calculate agreement
        agreement = self._calculate_agreement(observer_signals or [])

        result = ConsensusResult(
            task_type=task_type,
            complexity=complexity,
            confidence=type_confidence,
            routing_path=routing["path"],
            required_capabilities=capabilities["required"],
            recommended_model=model,
            spawn_required=spawn_required,
            timestamp=timestamp,
            voter_count=len(observer_signals) if observer_signals else 1,
            agreement_score=agreement,
            metadata={
                "classification_details": classification,
                "routing_details": routing,
                "capability_details": capabilities,
                "complexity_details": complexity_result,
            },
        )

        # Store in consensus memory
        self.memory.record_consensus(result)

        logger.info(
            f"Consensus reached: {task_type} ({complexity}) "
            f"via {' -> '.join(routing['path'])} "
            f"[agreement: {agreement:.2f}]"
        )

        return result

    def _select_model(
        self, task_type: str, complexity: str, capabilities: dict
    ) -> str:
        """Select the best model for the task."""
        # Complex tasks get stronger models
        if complexity in ("critical", "high"):
            if task_type in ("coding", "architecture"):
                return "claude-sonnet-4"
            return "claude-sonnet-4"
        if task_type in ("research", "analysis"):
            return "claude-haiku-4"
        return "claude-haiku-4"

    def _should_spawn(
        self, task_type: str, complexity: str, capabilities: dict
    ) -> bool:
        """Determine if agent spawning is required."""
        # Never spawn for casual conversation or general chat
        if task_type in ("conversation", "general"):
            return False
        if complexity in ("critical", "high"):
            return True
        if task_type in ("orchestration", "automation"):
            return True
        if capabilities.get("requires_multi_agent", False):
            return True
        return False

    def _calculate_agreement(self, signals: list[dict]) -> float:
        """Calculate agreement score from observer signals."""
        if not signals:
            return 1.0  # No signals = perfect agreement (default)

        if len(signals) == 1:
            return 0.8  # Single observer = high but not perfect

        # Count agreement on task type
        types = [s.get("task_type", "unknown") for s in signals]
        type_counts: dict[str, int] = {}
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1

        max_agreement = max(type_counts.values())
        return max_agreement / len(signals)

    def get_consensus_history(
        self, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recent consensus history."""
        return self.memory.get_recent(limit)

    def get_stats(self) -> dict[str, Any]:
        """Get consensus statistics."""
        return {
            "total_consensus_rounds": self.memory.total_records,
            "avg_agreement": self.memory.avg_agreement,
            "task_type_distribution": self.memory.task_type_distribution,
            "model_distribution": self.memory.model_distribution,
        }

```

LINKS:
[[Architecture]]
[[Claude]]
[[Master Plan Observer Core]]
[[Observer Core Workspace State]]
[[User]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Server]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
