# Semantic State

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #semantic

```python
"""
Semantic State Field — Core cognition substrate.

Every message produces an internal SemanticState object BEFORE response generation.
This replaces the regex-template routing with actual semantic interpretation.

Architecture:
    User Input → Semantic Interpreter → SemanticState → Response Synthesizer → Response

NOT:
    User Input → regex match → template → Response
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SemanticState:
    """
    Internal interpretation of a user message.
    This is the central cognition substrate — every response is generated
    FROM this object, not from raw text matching.
    """
    raw_input: str

    # Core interpretation
    primary_intent: str = ""          # greeting, question, request, command, ambiguity, identity_probe, etc.
    task_type: str = ""               # coding, research, architecture, conversation, etc.

    # Cognitive dimensions
    abstraction_level: float = 0.5    # 0.0=concrete, 1.0=abstract
    reasoning_depth: float = 0.5      # 0.0=shallow, 1.0=deep

    # Uncertainty
    uncertainty: float = 0.5          # 0.0=certain, 1.0=completely ambiguous
    entropy: float = 0.5              # operational entropy of this message

    # Response shaping
    emotional_vector: str = "neutral" # neutral, curious, frustrated, playful, urgent
    response_mode: str = "answer"     # answer, clarify, execute, explain, deflect, recover

    # Continuity
    requires_clarification: bool = False
    continuity_reference: Optional[str] = None  # references previous topic

    # Inferred goal
    inferred_goal: Optional[str] = None

    # Confidence in our own interpretation
    confidence: float = 0.5

    # Metadata
    word_count: int = 0
    has_question_mark: bool = False
    has_action_verb: bool = False
    is_short: bool = False

    def to_dict(self) -> dict:
        return {
            "raw_input": self.raw_input[:100],
            "primary_intent": self.primary_intent,
            "task_type": self.task_type,
            "abstraction_level": self.abstraction_level,
            "reasoning_depth": self.reasoning_depth,
            "uncertainty": self.uncertainty,
            "entropy": self.entropy,
            "emotional_vector": self.emotional_vector,
            "response_mode": self.response_mode,
            "requires_clarification": self.requires_clarification,
            "continuity_reference": self.continuity_reference,
            "inferred_goal": self.inferred_goal,
            "confidence": self.confidence,
        }

```

LINKS:
[[Architecture]]
[[Identity]]
[[Observer Core Workspace State]]
[[User]]
[[Workspace State]]
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Action]]
[[Citation Workflow]]
[[Neutral]]
[[Playful]]
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
[[Observer Consensus]]
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
[[Telegram Gateway]]
