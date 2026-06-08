"""
4_instrumentation.field_state_snapshot

Periodic field state capture — point-in-time snapshots of the entire field.

Stores module states, agent states, event bus depth, and health score
in a ring buffer for historical comparison and trend analysis.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.field_state_snapshot")


class SnapshotRecord(BaseModel):
    """A single field state snapshot."""
    timestamp: str
    module_count: int = 0
    active_modules: int = 0
    agent_count: int = 0
    active_agents: int = 0
    event_bus_depth: int = 0
    health_score: float = 1.0
    module_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SnapshotDiff(BaseModel):
    """Difference between two snapshots."""
    timestamp_a: str
    timestamp_b: str
    modules_added: List[str] = Field(default_factory=list)
    modules_removed: List[str] = Field(default_factory=list)
    modules_status_changed: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    health_delta: float = 0.0
    event_depth_delta: int = 0
    agent_count_delta: int = 0


class FieldStateSnapshotConfig(BaseModel):
    """Configuration for field_state_snapshot."""
    enabled: bool = True
    snapshot_interval_sec: float = 30.0
    max_snapshots: int = 2880  # 24h at 30s intervals


class FieldStateSnapshotModule:
    """Captures and stores periodic field state snapshots."""

    def __init__(self):
        self.config = FieldStateSnapshotConfig()
        self.running = False
        self._snapshots: deque = deque(maxlen=self.config.max_snapshots)
        self._lock = Lock()
        self._capture_count = 0
        self._last_capture_time: Optional[str] = None
        logger.info("FieldStateSnapshotModule initialized (max_snapshots=%d)", self.config.max_snapshots)

    def start(self) -> None:
        """Start the module."""
        self.running = True
        logger.info("FieldStateSnapshotModule started")

    def stop(self) -> None:
        """Stop the module."""
        self.running = False
        logger.info("FieldStateSnapshotModule stopped (captures=%d)", self._capture_count)

    def capture(
        self,
        module_states: Optional[Dict[str, Dict[str, Any]]] = None,
        agent_states: Optional[Dict[str, Dict[str, Any]]] = None,
        event_bus_depth: int = 0,
        health_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SnapshotRecord:
        """Capture a point-in-time snapshot of the field state.

        Args:
            module_states: Dict of module_name -> state dict
            agent_states: Dict of agent_id -> state dict
            event_bus_depth: Current event bus queue depth
            health_score: Overall field health score (0.0 to 1.0)
            metadata: Additional metadata to store

        Returns:
            SnapshotRecord with the captured state
        """
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            module_states = module_states or {}
            agent_states = agent_states or {}
            metadata = metadata or {}

            active_modules = sum(
                1 for m in module_states.values() if m.get("status") == "active"
            )
            active_agents = sum(
                1 for a in agent_states.values() if a.get("status") in ("connected", "processing")
            )

            record = SnapshotRecord(
                timestamp=now,
                module_count=len(module_states),
                active_modules=active_modules,
                agent_count=len(agent_states),
                active_agents=active_agents,
                event_bus_depth=event_bus_depth,
                health_score=health_score,
                module_states=module_states,
                agent_states=agent_states,
                metadata=metadata,
            )

            self._snapshots.append(record)
            self._capture_count += 1
            self._last_capture_time = now

            logger.debug(
                "Snapshot captured: modules=%d/%d agents=%d/%d health=%.4f",
                active_modules, len(module_states),
                active_agents, len(agent_states),
                health_score,
            )
            return record

    def get_latest(self) -> Optional[SnapshotRecord]:
        """Get the most recent snapshot.

        Returns:
            Latest SnapshotRecord or None if no snapshots exist
        """
        with self._lock:
            if self._snapshots:
                return self._snapshots[-1]
            return None

    def get_history(self, n: int = 100) -> List[SnapshotRecord]:
        """Get the last N snapshots.

        Args:
            n: Number of snapshots to retrieve

        Returns:
            List of SnapshotRecord, oldest first
        """
        with self._lock:
            snapshots = list(self._snapshots)
            return snapshots[-n:] if n < len(snapshots) else snapshots

    def compare_snapshots(
        self, snap_a: SnapshotRecord, snap_b: SnapshotRecord
    ) -> SnapshotDiff:
        """Compare two snapshots and return their differences.

        Args:
            snap_a: Earlier snapshot
            snap_b: Later snapshot

        Returns:
            SnapshotDiff with detailed differences
        """
        mods_a = set(snap_a.module_states.keys())
        mods_b = set(snap_b.module_states.keys())

        added = list(mods_b - mods_a)
        removed = list(mods_a - mods_b)

        status_changed = {}
        for mod_name in mods_a & mods_b:
            status_a = snap_a.module_states[mod_name].get("status", "unknown")
            status_b = snap_b.module_states[mod_name].get("status", "unknown")
            if status_a != status_b:
                status_changed[mod_name] = {"from": status_a, "to": status_b}

        return SnapshotDiff(
            timestamp_a=snap_a.timestamp,
            timestamp_b=snap_b.timestamp,
            modules_added=added,
            modules_removed=removed,
            modules_status_changed=status_changed,
            health_delta=round(snap_b.health_score - snap_a.health_score, 4),
            event_depth_delta=snap_b.event_bus_depth - snap_a.event_bus_depth,
            agent_count_delta=snap_b.agent_count - snap_a.agent_count,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get snapshot statistics.

        Returns:
            Dict with capture count, storage usage, time range
        """
        with self._lock:
            return {
                "total_captures": self._capture_count,
                "stored_snapshots": len(self._snapshots),
                "max_snapshots": self.config.max_snapshots,
                "last_capture": self._last_capture_time,
                "storage_utilization": len(self._snapshots) / self.config.max_snapshots,
            }
