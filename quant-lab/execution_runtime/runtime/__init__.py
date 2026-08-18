"""QL-EXEC-R3 — generic single-instance execution runtime package.

All dependencies injected; no strategy science, no capital routing math, no
MetaTrader5. Tests drive the engine exclusively through SimBrokerSession.
"""
from __future__ import annotations

from .adapters import (
    EVENT_KIND_ENTRY,
    EVENT_KIND_EXIT,
    PassThroughCapitalPolicyAdapter,
    ScriptedStrategyAdapter,
    TestCapitalTranslationAdapter,
    entry_event,
    exit_event,
)
from .engine import CrashPoint, GenericRuntime, SimulatedCrash
from .heartbeat import Heartbeat, TelemetrySnapshot
from .intent import (
    ExecutionIntent,
    IntentState,
    PositionState,
    execution_intent_id,
)
from .reconciliation import (
    CLEAN_STATES,
    ReconciliationResult,
    ReconciliationState,
    Reconciler,
)
from .singleton import SingletonConflict, SingletonLock
from .state import (
    RuntimeState,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    is_valid_transition,
    validate_transition,
)
from .store import RUNTIME_SCHEMA_VERSION, RuntimeStore

__all__ = [
    "CLEAN_STATES",
    "CrashPoint",
    "EVENT_KIND_ENTRY",
    "EVENT_KIND_EXIT",
    "ExecutionIntent",
    "GenericRuntime",
    "Heartbeat",
    "IntentState",
    "PassThroughCapitalPolicyAdapter",
    "PositionState",
    "ReconciliationResult",
    "ReconciliationState",
    "Reconciler",
    "RUNTIME_SCHEMA_VERSION",
    "RuntimeState",
    "RuntimeStore",
    "ScriptedStrategyAdapter",
    "SimulatedCrash",
    "SingletonConflict",
    "SingletonLock",
    "TERMINAL_STATES",
    "TelemetrySnapshot",
    "TestCapitalTranslationAdapter",
    "VALID_TRANSITIONS",
    "entry_event",
    "execution_intent_id",
    "exit_event",
    "is_valid_transition",
    "validate_transition",
]
