"""
Tests for OCE Coevolution Protocol — Phase 8.5c
=================================================
Tests covering peer registration, topology sync, goal alignment, failure handling.
"""

import os
import sys
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)

from coevolution_protocol import (
    CoevolutionProtocol,
    TrustLevel,
    PeerStatus,
    get_coevolution_protocol,
    DB_PATH,
)


@pytest.fixture(autouse=True)
def reset_coevolution(tmp_path):
    CoevolutionProtocol._instance = None
    import coevolution_protocol as cp
    original_path = cp.DB_PATH
    temp_db = str(tmp_path / "test_coevolution.db")
    cp.DB_PATH = temp_db
    cp.DATA_DIR = tmp_path
    yield
    CoevolutionProtocol._instance = None
    cp.DB_PATH = original_path
    cp.DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


@pytest.fixture
def protocol():
    return get_coevolution_protocol()


class TestPeerRegistration:
    def test_register_peer(self, protocol):
        aid = protocol.register_peer_agent(
            agent_id="peer-1",
            label="Test Peer",
            capabilities=["observe", "report"],
            trust_level=TrustLevel.PARTICIPANT,
        )
        assert aid == "peer-1"

    def test_get_peer(self, protocol):
        protocol.register_peer_agent(agent_id="peer-2", label="Test", capabilities=["execute"])
        peer = protocol.get_peer("peer-2")
        assert peer is not None
        assert peer["agent_id"] == "peer-2"
        assert "execute" in peer["capabilities"]

    def test_get_peer_not_found(self, protocol):
        assert protocol.get_peer("nonexistent") is None

    def test_list_peers(self, protocol):
        protocol.register_peer_agent(agent_id="p1", label="Peer 1")
        protocol.register_peer_agent(agent_id="p2", label="Peer 2")
        peers = protocol.get_all_peers()
        assert len(peers) >= 2

    def test_active_peers(self, protocol):
        protocol.register_peer_agent(agent_id="active-1", label="Active")
        active = protocol.get_active_peers()
        assert len(active) >= 1

    def test_heartbeat(self, protocol):
        protocol.register_peer_agent(agent_id="hb-1", label="Heartbeat Test")
        protocol.update_peer_heartbeat("hb-1")
        peer = protocol.get_peer("hb-1")
        assert peer["status"] == PeerStatus.ACTIVE.value

    def test_peer_status_update(self, protocol):
        protocol.register_peer_agent(agent_id="status-1", label="Status Test")
        protocol.update_peer_status("status-1", PeerStatus.DEGRADED.value)
        peer = protocol.get_peer("status-1")
        assert peer["status"] == PeerStatus.DEGRADED.value


class TestTopologySync:
    def test_negotiate_topology_change(self, protocol):
        protocol.register_peer_agent(agent_id="topo-peer", label="Topo", trust_level=TrustLevel.COOPERATOR)
        result = protocol.negotiate_topology_change({"action": "add_edge", "from": "a", "to": "b"})
        assert "sync_id" in result
        assert result["peers_contacted"] >= 1

    def test_negotiate_no_peers(self, protocol):
        result = protocol.negotiate_topology_change({"action": "test"})
        assert result["peers_contacted"] == 0


class TestGoalAlignment:
    def test_align_goals(self, protocol):
        protocol.register_peer_agent(agent_id="goal-peer", label="Goal Test")
        alignment_id = protocol.align_goals("goal-peer", ["goal-1", "goal-2"])
        assert alignment_id is not None
        assert len(alignment_id) > 0


class TestPeerFailure:
    def test_handle_peer_failure(self, protocol):
        protocol.register_peer_agent(agent_id="fail-peer", label="Fail Test", capabilities=["observe", "execute"])
        result = protocol.handle_peer_failure("fail-peer")
        assert result["agent_id"] == "fail-peer"
        assert result["status"] == "failed"
        assert len(result["capabilities_lost"]) == 2

    def test_handle_failure_nonexistent(self, protocol):
        result = protocol.handle_peer_failure("nonexistent")
        assert result["status"] == "failed"
        assert len(result["capabilities_lost"]) == 0


class TestCoevolutionStatus:
    def test_status_report(self, protocol):
        protocol.register_peer_agent(agent_id="status-1", label="S1")
        protocol.register_peer_agent(agent_id="status-2", label="S2", trust_level=TrustLevel.COOPERATOR)
        status = protocol.get_coevolution_status()
        assert "total_peers" in status
        assert "active_peers" in status
        assert "trust_distribution" in status
        assert status["total_peers"] >= 2

    def test_singleton(self, protocol):
        p1 = get_coevolution_protocol()
        p2 = get_coevolution_protocol()
        assert p1 is p2
