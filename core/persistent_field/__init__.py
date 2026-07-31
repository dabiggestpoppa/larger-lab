"""
O-7: Persistent Field Mode
===========================

Continuous operational continuity across extended time periods.
12 backend components for persistent observer-mediated operational intelligence.
"""

from core.persistent_field.persistent_runtime import PersistentRuntime, RuntimeState, RuntimeStatus
from core.persistent_field.observer_persistence import ObserverPersistence, ObserverSnapshot
from core.persistent_field.passive_awareness import PassiveAwareness, AwarenessSignal
from core.persistent_field.environmental_monitor import EnvironmentalMonitor, EnvironmentReading
from core.persistent_field.continuity_preserver import ContinuityPreserver, ContinuityRecord
from core.persistent_field.dormant_state_manager import DormantStateManager, DormantState
from core.persistent_field.autonomous_repair import AutonomousRepair, RepairAction, RepairStatus, RepairEvent
from core.persistent_field.runtime_heartbeat import RuntimeHeartbeat, HeartbeatSignal
from core.persistent_field.persistent_scheduler import PersistentScheduler, ScheduledTask
from core.persistent_field.recovery_persistence import RecoveryPersistence, Snapshot
from core.persistent_field.long_horizon_memory import LongHorizonMemory, MemoryEntry
from core.persistent_field.operational_drift_detect import OperationalDriftDetector, DriftMetric

__all__ = [
    "PersistentRuntime", "RuntimeState", "RuntimeStatus",
    "ObserverPersistence", "ObserverSnapshot",
    "PassiveAwareness", "AwarenessSignal",
    "EnvironmentalMonitor", "EnvironmentReading",
    "ContinuityPreserver", "ContinuityRecord",
    "DormantStateManager", "DormantState",
    "AutonomousRepair", "RepairAction", "RepairStatus", "RepairEvent",
    "RuntimeHeartbeat", "HeartbeatSignal",
    "PersistentScheduler", "ScheduledTask",
    "RecoveryPersistence", "Snapshot",
    "LongHorizonMemory", "MemoryEntry",
    "OperationalDriftDetector", "DriftMetric",
]
