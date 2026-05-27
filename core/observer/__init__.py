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
    "ObserverSession",
    "ObserverLifecycle",
    "EventAwareness",
    "EventType",
]
