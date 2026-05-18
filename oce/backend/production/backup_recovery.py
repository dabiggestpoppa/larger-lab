"""
V3 Phase 9 — Backup & Recovery
Automated backup of cognitive field state with recovery points.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BackupSnapshot:
    """A backup snapshot of system state."""
    snapshot_id: str
    label: str
    state_data: dict
    checksum: str = ""
    timestamp: float = field(default_factory=time.time)
    size_bytes: int = 0

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp


@dataclass
class RecoveryPoint:
    """A verified recovery point."""
    recovery_id: str
    snapshot_id: str
    label: str
    verified: bool = False
    created_at: float = field(default_factory=time.time)


class BackupRecovery:
    """
    Automated backup and recovery for cognitive field state.
    
    Features:
    - Create labeled snapshots of system state
    - Verify snapshot integrity
    - Create verified recovery points
    - Restore from any recovery point
    - Prune old snapshots
    """

    def __init__(self):
        self._snapshots: dict[str, BackupSnapshot] = {}
        self._recovery_points: dict[str, RecoveryPoint] = {}

    def create_snapshot(self, label: str, state_data: dict) -> BackupSnapshot:
        """Create a backup snapshot."""
        snapshot = BackupSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            label=label,
            state_data=state_data,
            size_bytes=len(str(state_data)),
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[BackupSnapshot]:
        """Get a snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify a snapshot's integrity."""
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            return False
        # Basic verification: state_data is non-empty dict
        return isinstance(snapshot.state_data, dict) and len(snapshot.state_data) > 0

    def create_recovery_point(self, snapshot_id: str, label: str = "") -> Optional[RecoveryPoint]:
        """Create a verified recovery point from a snapshot."""
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            return None

        verified = self.verify_snapshot(snapshot_id)
        rp = RecoveryPoint(
            recovery_id=f"rp_{uuid.uuid4().hex[:8]}",
            snapshot_id=snapshot_id,
            label=label or snapshot.label,
            verified=verified,
        )
        self._recovery_points[rp.recovery_id] = rp
        return rp

    def restore(self, recovery_id: str) -> Optional[dict]:
        """Restore state from a recovery point."""
        rp = self._recovery_points.get(recovery_id)
        if rp is None or not rp.verified:
            return None
        snapshot = self._snapshots.get(rp.snapshot_id)
        if snapshot is None:
            return None
        return dict(snapshot.state_data)

    def prune_snapshots(self, max_age_seconds: float = 86400) -> int:
        """Remove snapshots older than max_age_seconds. Returns count removed."""
        now = time.time()
        to_remove = [
            sid for sid, s in self._snapshots.items()
            if now - s.age_seconds > max_age_seconds
        ]
        for sid in to_remove:
            del self._snapshots[sid]
        return len(to_remove)

    def get_latest_snapshot(self) -> Optional[BackupSnapshot]:
        """Get the most recent snapshot."""
        if not self._snapshots:
            return None
        return max(self._snapshots.values(), key=lambda s: s.timestamp)

    @property
    def stats(self) -> dict:
        verified_rps = sum(1 for rp in self._recovery_points.values() if rp.verified)
        return {
            "total_snapshots": len(self._snapshots),
            "total_recovery_points": len(self._recovery_points),
            "verified_recovery_points": verified_rps,
            "total_size_bytes": sum(s.size_bytes for s in self._snapshots.values()),
        }
