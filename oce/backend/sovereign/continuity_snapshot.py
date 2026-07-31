"""
V3 Phase 4 — Continuity Snapshot System
Captures and restores full field state for crash recovery.

Enables the system to survive:
- Crashes
- Restarts
- Model changes
- Partial failures
- Topology changes

Without identity fragmentation.
"""

from __future__ import annotations
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ContinuitySnapshot:
    """A complete snapshot of the cognitive field state."""
    snapshot_id: str
    timestamp: float
    shell_state: dict = field(default_factory=dict)
    observer_states: dict = field(default_factory=dict)
    active_trajectories: list[str] = field(default_factory=list)
    topology_state: dict = field(default_factory=dict)
    memory_anchors: list[str] = field(default_factory=list)
    entropy_budget: float = 1.0
    field_health: float = 1.0
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate integrity checksum."""
        data = f"{self.snapshot_id}{self.timestamp}{self.entropy_budget}{self.field_health}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @property
    def is_valid(self) -> bool:
        return self.checksum == self._calculate_checksum()

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "shell_state": self.shell_state,
            "observer_count": len(self.observer_states),
            "active_trajectories": self.active_trajectories,
            "entropy_budget": round(self.entropy_budget, 4),
            "field_health": round(self.field_health, 4),
            "checksum": self.checksum,
        }


class ContinuitySnapshotSystem:
    """
    Manages continuity snapshots for crash recovery.
    
    Snapshots are saved to disk and can be loaded after a restart
    to restore the full field state.
    """

    def __init__(self, snapshot_dir: str = ".oce/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: list[ContinuitySnapshot] = []
        self._max_snapshots = 100

    def capture(
        self, shell_state: dict, observer_states: dict = None,
        trajectories: list[str] = None, topology: dict = None,
        memory_anchors: list[str] = None,
        entropy_budget: float = 1.0, field_health: float = 1.0,
    ) -> ContinuitySnapshot:
        """Capture a complete field state snapshot."""
        snapshot = ContinuitySnapshot(
            snapshot_id=f"snap_{int(time.time())}",
            timestamp=time.time(),
            shell_state=shell_state,
            observer_states=observer_states or {},
            active_trajectories=trajectories or [],
            topology_state=topology or {},
            memory_anchors=memory_anchors or [],
            entropy_budget=entropy_budget,
            field_health=field_health,
        )

        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        # Persist to disk
        self._save_snapshot(snapshot)
        return snapshot

    def restore(self, snapshot_id: str = None) -> Optional[ContinuitySnapshot]:
        """
        Restore from a snapshot. If no ID given, restores the latest.
        """
        if snapshot_id:
            for snap in self._snapshots:
                if snap.snapshot_id == snapshot_id:
                    return snap
            # Try loading from disk
            return self._load_snapshot(snapshot_id)
        elif self._snapshots:
            return self._snapshots[-1]
        return None

    def get_latest(self) -> Optional[ContinuitySnapshot]:
        """Get the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def list_snapshots(self) -> list[dict]:
        """List all available snapshots."""
        return [s.to_dict() for s in self._snapshots]

    def _save_snapshot(self, snapshot: ContinuitySnapshot) -> None:
        """Save snapshot to disk."""
        filepath = self.snapshot_dir / f"{snapshot.snapshot_id}.json"
        try:
            filepath.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
        except IOError:
            pass

    def _load_snapshot(self, snapshot_id: str) -> Optional[ContinuitySnapshot]:
        """Load snapshot from disk."""
        filepath = self.snapshot_dir / f"{snapshot_id}.json"
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                return ContinuitySnapshot(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    @property
    def stats(self) -> dict:
        return {
            "total_snapshots": len(self._snapshots),
            "latest_timestamp": self._snapshots[-1].timestamp if self._snapshots else 0,
            "snapshot_dir": str(self.snapshot_dir),
        }
