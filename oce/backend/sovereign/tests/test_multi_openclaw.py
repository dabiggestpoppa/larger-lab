"""Tests for Multi-OpenClaw Swarm."""

import pytest
from oce.backend.sovereign.multi_openclaw import MultiOpenClawSwarm, SwarmMember


class TestSwarmMember:
    """Tests for SwarmMember dataclass."""

    def test_member_creation(self):
        """Test SwarmMember can be created."""
        member = SwarmMember(
            member_id="member-1",
            role="coordinator",
            status="active",
            last_heartbeat=12345.0,
            coherence=0.8,
        )
        assert member.member_id == "member-1"
        assert member.role == "coordinator"
        assert member.status == "active"

    def test_member_to_dict(self):
        """Test SwarmMember serialization."""
        member = SwarmMember(
            member_id="member-1",
            role="coordinator",
            status="active",
            last_heartbeat=12345.0,
            coherence=0.8,
        )
        d = member.to_dict()
        assert d["member_id"] == "member-1"
        assert d["coherence"] == 0.8


class TestMultiOpenClawSwarm:
    """Tests for MultiOpenClawSwarm class."""

    def test_swarm_creation(self):
        """Test MultiOpenClawSwarm can be created."""
        swarm = MultiOpenClawSwarm()
        assert swarm is not None

    def test_add_member(self):
        """Test adding a member."""
        swarm = MultiOpenClawSwarm()
        member = swarm.add_member("coordinator")
        assert member.role == "coordinator"
        assert member.status == "active"

    def test_get_member(self):
        """Test getting a member."""
        swarm = MultiOpenClawSwarm()
        member = swarm.add_member("coordinator")
        retrieved = swarm.get_member(member.member_id)
        assert retrieved == member

    def test_get_nonexistent_member(self):
        """Test getting nonexistent member."""
        swarm = MultiOpenClawSwarm()
        assert swarm.get_member("nonexistent") is None

    def test_remove_member(self):
        """Test removing a member."""
        swarm = MultiOpenClawSwarm()
        member = swarm.add_member("coordinator")
        result = swarm.remove_member(member.member_id)
        assert result is True
        assert swarm.get_member(member.member_id) is None

    def test_remove_nonexistent_member(self):
        """Test removing nonexistent member."""
        swarm = MultiOpenClawSwarm()
        assert swarm.remove_member("nonexistent") is False

    def test_heartbeat(self):
        """Test updating heartbeat."""
        swarm = MultiOpenClawSwarm()
        member = swarm.add_member("coordinator")
        updated = swarm.heartbeat(member.member_id, coherence=0.9)
        assert updated.coherence == 0.9

    def test_heartbeat_nonexistent(self):
        """Test heartbeat on nonexistent member."""
        swarm = MultiOpenClawSwarm()
        assert swarm.heartbeat("nonexistent") is None

    def test_get_active_members(self):
        """Test getting active members."""
        swarm = MultiOpenClawSwarm()
        m1 = swarm.add_member("coordinator")
        m2 = swarm.add_member("researcher")
        active = swarm.get_active_members()
        assert len(active) == 2

    def test_get_members_by_role(self):
        """Test getting members by role."""
        swarm = MultiOpenClawSwarm()
        m1 = swarm.add_member("coordinator")
        m2 = swarm.add_member("researcher")
        coordinators = swarm.get_members_by_role("coordinator")
        assert len(coordinators) == 1
        assert coordinators[0].role == "coordinator"

    def test_get_coordinator(self):
        """Test getting coordinator."""
        swarm = MultiOpenClawSwarm()
        swarm.add_member("researcher")
        swarm.add_member("coordinator")
        coordinator = swarm.get_coordinator()
        assert coordinator is not None
        assert coordinator.role == "coordinator"

    def test_get_coordinator_none(self):
        """Test getting coordinator when none exists."""
        swarm = MultiOpenClawSwarm()
        swarm.add_member("researcher")
        assert swarm.get_coordinator() is None

    def test_get_stats(self):
        """Test getting swarm statistics."""
        swarm = MultiOpenClawSwarm()
        swarm.add_member("coordinator")
        swarm.add_member("researcher")
        stats = swarm.get_stats()
        assert stats["total_members"] == 2
        assert "active_members" in stats
        assert "roles" in stats