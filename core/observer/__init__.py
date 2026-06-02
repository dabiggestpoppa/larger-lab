"""
Primary Observer Core
=====================
O-1 Phase: Primary Observer Core components.

Components:
- PrimaryObserver: Main orchestration interface for chat
- ObserverState: Persistent observer state management
- RuntimeAwareness: Topology, observers, entropy awareness
- TaskIntentAnalyzer: Classifies task domain and complexity
- ContextDistiller: Compresses field state for responses
- ContinuityMemory: Operational continuity memory
- ChatLog: Persistent conversation log for field analysis
- ObserverSession: Session continuity management
- ObserverLifecycle: Heartbeat, healthcheck, recovery
- EventAwareness: Runtime event observation
"""

from .primary_observer import PrimaryObserver
from .observer_state import ObserverState
from .runtime_awareness import RuntimeAwareness
from .task_intent_analyzer import TaskIntentAnalyzer
from .context_distiller import ContextDistiller
from .continuity_memory import ContinuityMemory
from .chat_log import ChatLog, get_chat_log
from .observer_session import ObserverSession
from .observer_lifecycle import ObserverLifecycle
from .event_awareness import EventAwareness, EventType

__all__ = [
    "PrimaryObserver",
    "ObserverState",
    "RuntimeAwareness",
    "TaskIntentAnalyzer",
    "ContextDistiller",
    "ContinuityMemory",
    "ChatLog",
    "get_chat_log",
    "ObserverSession",
    "ObserverLifecycle",
    "EventAwareness",
    "EventType",
    "ObserverConversationRuntime",
    "CommandRouter",
    "Vault",
    "Journal",
    "ReportReturnSystem",
    "SemanticRetrieval",
    "KnowledgeGraph",
    "PatternDistillation",
    "FailureIntelligence",
    "AutonomousOrchestrator",
]

# Phase 1 + 2 + 3 components (lazy imports to avoid circular deps)
def __getattr__(name):
    if name == "ObserverConversationRuntime":
        from .observer_conversation_runtime import ObserverConversationRuntime
        return ObserverConversationRuntime
    if name == "CommandRouter":
        from .command_router import CommandRouter
        return CommandRouter
    if name == "Vault":
        from .vault import Vault
        return Vault
    if name == "Journal":
        from .journal import Journal
        return Journal
    if name == "ReportReturnSystem":
        from .report_return import ReportReturnSystem
        return ReportReturnSystem
    if name == "SemanticRetrieval":
        from .semantic_retrieval import SemanticRetrieval
        return SemanticRetrieval
    if name == "KnowledgeGraph":
        from .graph_traversal import KnowledgeGraph
        return KnowledgeGraph
    if name == "PatternDistillation":
        from .pattern_distillation import PatternDistillation
        return PatternDistillation
    if name == "FailureIntelligence":
        from .pattern_distillation import FailureIntelligence
        return FailureIntelligence
    if name == "AutonomousOrchestrator":
        from .autonomous_orchestrator import AutonomousOrchestrator
        return AutonomousOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
