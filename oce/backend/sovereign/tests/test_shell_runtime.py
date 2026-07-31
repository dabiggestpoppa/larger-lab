"""Tests for OCE Shell Runtime."""

import pytest
import time
from oce.backend.sovereign.shell_runtime import OCEShell, ShellState


class TestShellState:
    """Tests for ShellState dataclass."""

    def test_shell_state_creation(self):
        """Test ShellState can be created with defaults."""
        state = ShellState(
            shell_id="test-shell",
            timestamp=time.time(),
            identity_hash="test-hash",
            continuity_score=1.0,
            active_trajectories=[],
            field_state={},
            system_priorities=["coherence"],
            memory_alignment=1.0,
        )
        assert state.shell_id == "test-shell"
        assert state.continuity_score == 1.0
        assert state.is_stable is True

    def test_shell_state_to_dict(self):
        """Test ShellState serialization."""
        state = ShellState(
            shell_id="test-shell",
            timestamp=time.time(),
            identity_hash="test-hash",
            continuity_score=0.8,
            active_trajectories=["traj-1"],
            field_state={"key": "value"},
            system_priorities=["coherence"],
            memory_alignment=0.9,
        )
        d = state.to_dict()
        assert d["shell_id"] == "test-shell"
        assert d["continuity_score"] == 0.8
        assert d["active_trajectories"] == ["traj-1"]


class TestOCEShell:
    """Tests for OCEShell class."""

    def test_shell_creation(self):
        """Test OCEShell can be created."""
        shell = OCEShell()
        assert shell.shell_id is not None
        assert shell.identity_hash is not None

    def test_shell_with_identity(self):
        """Test OCEShell with custom identity."""
        shell = OCEShell(identity_hash="custom-identity")
        assert shell.identity_hash == "custom-identity"

    def test_update_field_state(self):
        """Test updating field state."""
        shell = OCEShell()
        shell.update_field_state({"test": "value"})
        assert shell.state.field_state == {"test": "value"}

    def test_add_trajectory(self):
        """Test adding trajectories."""
        shell = OCEShell()
        shell.add_trajectory("traj-1")
        assert "traj-1" in shell.state.active_trajectories
        shell.add_trajectory("traj-2")
        assert "traj-2" in shell.state.active_trajectories

    def test_remove_trajectory(self):
        """Test removing trajectories."""
        shell = OCEShell()
        shell.add_trajectory("traj-1")
        shell.remove_trajectory("traj-1")
        assert "traj-1" not in shell.state.active_trajectories

    def test_set_priorities(self):
        """Test setting system priorities."""
        shell = OCEShell()
        shell.set_priorities(["efficiency", "stability"])
        assert shell.state.system_priorities == ["efficiency", "stability"]

    def test_measure_continuity(self):
        """Test measuring continuity."""
        shell = OCEShell()
        assert shell.measure_continuity() == 1.0

    def test_snapshot_and_restore(self):
        """Test snapshot and restore functionality."""
        shell = OCEShell()
        shell.add_trajectory("traj-1")
        snapshot = shell.snapshot()
        shell.remove_trajectory("traj-1")
        shell.restore(snapshot)
        assert "traj-1" in shell.state.active_trajectories

    def test_get_stats(self):
        """Test getting shell statistics."""
        shell = OCEShell()
        stats = shell.get_stats()
        assert "shell_id" in stats
        assert "continuity_score" in stats
        assert "active_trajectories" in stats