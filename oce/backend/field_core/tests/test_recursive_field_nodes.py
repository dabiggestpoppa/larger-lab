"""
V3 Phase 9 — Sovereign Field Emergence
Tests for RecursiveFieldNodes module.
"""

import pytest
import time
from oce.backend.field_core.recursive_field_nodes import (
    RecursiveFieldNode,
    FieldTopology,
    FieldNodeRegistry,
)


class TestFieldTopology:
    """Tests for FieldTopology dataclass."""

    def test_topology_creation(self):
        """Test creating a field topology."""
        topo = FieldTopology(node_id="node_1")
        assert topo.node_id == "node_1"
        assert topo.parent_id is None
        assert topo.children == []
        assert topo.depth == 0
        assert topo.is_leaf is True
        assert topo.is_root is False

    def test_add_child(self):
        """Test adding a child."""
        topo = FieldTopology(node_id="parent")
        topo.add_child("child_1")
        assert "child_1" in topo.children
        assert topo.is_leaf is False

    def test_add_duplicate_child(self):
        """Test adding duplicate child doesn't duplicate."""
        topo = FieldTopology(node_id="parent")
        topo.add_child("child_1")
        topo.add_child("child_1")
        assert topo.children.count("child_1") == 1

    def test_remove_child(self):
        """Test removing a child."""
        topo = FieldTopology(node_id="parent")
        topo.add_child("child_1")
        topo.add_child("child_2")
        topo.remove_child("child_1")
        assert "child_1" not in topo.children
        assert "child_2" in topo.children

    def test_remove_nonexistent_child(self):
        """Test removing nonexistent child is safe."""
        topo = FieldTopology(node_id="parent")
        topo.remove_child("nonexistent")  # Should not raise


class TestRecursiveFieldNode:
    """Tests for RecursiveFieldNode dataclass."""

    def test_node_creation(self):
        """Test creating a field node."""
        node = RecursiveFieldNode(node_id="node_1")
        assert node.node_id == "node_1"
        assert node.coherence == 0.5
        assert node.active is True
        assert node.local_state == {}
        assert node.topology.node_id == "node_1"

    def test_node_with_topology(self):
        """Test creating node with custom topology."""
        topo = FieldTopology(node_id="node_1", depth=2)
        node = RecursiveFieldNode(node_id="node_1", topology=topo)
        assert node.topology.depth == 2

    def test_update_state(self):
        """Test updating node state."""
        node = RecursiveFieldNode(node_id="node_1")
        node.update_state("key1", "value1")
        assert node.local_state["key1"] == "value1"
        assert node.state_size == 1

    def test_get_state(self):
        """Test getting state with default."""
        node = RecursiveFieldNode(node_id="node_1")
        assert node.get_state("missing", "default") == "default"
        node.update_state("key", "value")
        assert node.get_state("key") == "value"

    def test_propagate_coherence(self):
        """Test coherence propagation."""
        node = RecursiveFieldNode(node_id="node_1", coherence=0.5)
        new_coherence = node.propagate_coherence(0.9, weight=0.3)
        # 0.7 * 0.5 + 0.3 * 0.9 = 0.35 + 0.27 = 0.62
        assert new_coherence == pytest.approx(0.62, rel=0.01)

    def test_is_healthy(self):
        """Test health check."""
        node = RecursiveFieldNode(node_id="node_1", coherence=0.3, active=True)
        assert node.is_healthy is True
        node.coherence = 0.1
        assert node.is_healthy is False
        node.active = False
        assert node.is_healthy is False


class TestFieldNodeRegistry:
    """Tests for FieldNodeRegistry."""

    def test_registry_empty(self):
        """Test empty registry."""
        registry = FieldNodeRegistry()
        assert registry.get("nonexistent") is None
        assert registry.stats["total_nodes"] == 0

    def test_register_node(self):
        """Test registering a node."""
        registry = FieldNodeRegistry()
        node = registry.register("node_1", coherence=0.8)
        assert node.node_id == "node_1"
        assert node.coherence == 0.8
        assert registry.get("node_1") is node

    def test_remove_node(self):
        """Test removing a node."""
        registry = FieldNodeRegistry()
        registry.register("node_1")
        assert registry.remove("node_1") is True
        assert registry.get("node_1") is None
        assert registry.remove("nonexistent") is False

    def test_get_active_nodes(self):
        """Test getting active nodes."""
        registry = FieldNodeRegistry()
        registry.register("node_1", active=True)
        registry.register("node_2", active=False)
        active = registry.get_active_nodes()
        assert len(active) == 1
        assert active[0].node_id == "node_1"

    def test_get_healthy_nodes(self):
        """Test getting healthy nodes."""
        registry = FieldNodeRegistry()
        registry.register("node_1", coherence=0.5, active=True)
        registry.register("node_2", coherence=0.1, active=True)
        healthy = registry.get_healthy_nodes()
        assert len(healthy) == 1
        assert healthy[0].node_id == "node_1"

    def test_propagate_all(self):
        """Test propagating coherence across nodes."""
        registry = FieldNodeRegistry()
        parent = registry.register("parent", coherence=0.9)
        child = registry.register("child", coherence=0.3)
        parent.topology.add_child("child")

        count = registry.propagate_all(weight=0.5)
        assert count == 1
        # Child coherence should be updated: 0.5 * 0.3 + 0.5 * 0.9 = 0.6
        assert child.coherence == pytest.approx(0.6, rel=0.01)

    def test_stats(self):
        """Test registry stats."""
        registry = FieldNodeRegistry()
        registry.register("node_1", coherence=0.8, active=True)
        registry.register("node_2", coherence=0.6, active=False)
        stats = registry.stats
        assert stats["total_nodes"] == 2
        assert stats["active_nodes"] == 1
        assert stats["healthy_nodes"] == 1
        assert stats["avg_coherence"] == pytest.approx(0.7, rel=0.01)