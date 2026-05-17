"""Tests for Continuity Snapshot System."""

import pytest
import time
from oce.backend.sovereign.continuity_snapshot import (
    ContinuitySnapshot,
    ContinuitySnapshotSystem,
)


class TestContinuitySnapshot:
    """Tests for ContinuitySnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test ContinuitySnapshot can be created."""
        snapshot = ContinuitySnapshot(
            snapshot_id="snap-1",
            timestamp=time.time(),
            shell_state={"key": "value"},
            observer_states={"obs-1": {}},
            active_trajectories=["traj-1"],
            topology_state={},
            memory_anchors=["anchor-1"],
            entropy_budget=1.0,
            field_health=1.0,
        )
        assert snapshot.snapshot_id == "snap-1"
        assert snapshot.entropy_budget == 1.0
        assert snapshot.field_health == 1.0

    def test_snapshot_checksum(self):
        """Test snapshot checksum calculation."""
        snapshot = ContinuitySnapshot(
            snapshot_id="snap-1",
            timestamp=time.time(),
            shell_state={},
            observer_states={},
            active_trajectories=[],
            topology_state={},
            memory_anchors=[],
            entropy_budget=1.0,
            field_health=1.0,
        )
        assert snapshot.checksum != ""
        assert len(snapshot.checksum) == 16

    def test_snapshot_is_valid(self):
        """Test snapshot validity check."""
        snapshot = ContinuitySnapshot(
            snapshot_id="snap-1",
            timestamp=time.time(),
            shell_state={},
            observer_states={},
            active_trajectories=[],
            topology_state={},
            memory_anchors=[],
            entropy_budget=1.0,
            field_health=1.0,
        )
        assert snapshot.is_valid is True

    def test_snapshot_to_dict(self):
        """Test ContinuitySnapshot serialization."""
        snapshot = ContinuitySnapshot(
            snapshot_id="snap-1",
            timestamp=time.time(),
            shell_state={"key": "value"},
            observer_states={"obs-1": {}},
            active_trajectories=["traj-1"],
            topology_state={},
            memory_anchors=["anchor-1"],
            entropy_budget=0.8,
            field_health=0.9,
        )
        d = snapshot.to_dict()
        assert d["snapshot_id"] == "snap-1"
        assert d["observer_count"] == 1


class TestContinuitySnapshotSystem:
    """Tests for ContinuitySnapshotSystem class."""

    def test_system_creation(self):
        """Test ContinuitySnapshotSystem can be created."""
        system = ContinuitySnapshotSystem()
        assert system is not None

    def test_capture(self):
        """Test capturing a snapshot."""
        system = ContinuitySnapshotSystem()
        snapshot = system.capture(
            shell_state={"test": "value"},
            observer_states={"obs-1": {}},
            trajectories=["traj-1"],
            topology={"topo": "value"},
            memory_anchors=["anchor-1"],
        )
        assert snapshot.snapshot_id is not None
        assert snapshot.shell_state == {"test": "value"}

    def test_restore(self):
        """Test restoring from snapshot."""
        system = ContinuitySnapshotSystem()
        snapshot = system.capture(
            shell_state={"test": "value"},
            observer_states={},
            trajectories=["traj-1"],
        )
        restored = system.restore(snapshot.snapshot_id)
        assert restored is not None
        assert restored.shell_state == {"test": "value"}

    def test_restore_nonexistent(self):
        """Test restoring nonexistent snapshot."""
        system = ContinuitySnapshotSystem()
        assert system.restore("nonexistent") is None

    def test_get_latest(self):
        """Test getting latest snapshot."""
        system = ContinuitySnapshotSystem()
        system.capture(shell_state={"v1": True})
        system.capture(shell_state={"v2": True})
        latest = system.get_latest()
        assert latest is not None
        assert latest.shell_state == {"v2": True}

    def test_get_latest_empty(self):
        """Test getting latest when empty."""
        system = ContinuitySnapshotSystem()
        assert system.get_latest() is None

    def test_list_snapshots(self):
        """Test listing snapshots."""
        system = ContinuitySnapshotSystem()
        system.capture(shell_state={"v1": True})
        system.capture(shell_state={"v2": True})
        snapshots = system.list_snapshots()
        assert len(snapshots) == 2

    def test_stats(self):
        """Test getting system statistics."""
        system = ContinuitySnapshotSystem()
        system.capture(shell_state={})
        stats = system.stats
        assert stats["total_snapshots"] == 1
        assert "snapshot_dir" in stats