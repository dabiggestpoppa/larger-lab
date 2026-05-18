"""Tests for Regional Clusters."""

import pytest
from oce.backend.multiscale.regional_clusters import RegionalCluster, ClusterRegistry


class TestRegionalCluster:
    def test_creation(self):
        c = RegionalCluster(cluster_id="c1")
        assert c.cluster_id == "c1"
        assert len(c.members) == 0

    def test_add_remove_member(self):
        c = RegionalCluster(cluster_id="c1")
        c.add_member("obs1")
        c.add_member("obs2")
        assert c.get_member_count() == 2
        c.remove_member("obs1")
        assert c.get_member_count() == 1

    def test_is_active(self):
        c = RegionalCluster(cluster_id="c1", interaction_density=0.5)
        assert c.is_active() is True
        c.interaction_density = 0.01
        assert c.is_active() is False


class TestClusterRegistry:
    def test_create_cluster(self):
        registry = ClusterRegistry()
        c = registry.create_cluster(["obs1", "obs2"])
        assert c is not None
        assert c.get_member_count() == 2

    def test_get_cluster_for_observer(self):
        registry = ClusterRegistry()
        registry.create_cluster(["obs1", "obs2"])
        retrieved = registry.get_cluster_for_observer("obs1")
        assert retrieved is not None

    def test_get_all_clusters(self):
        registry = ClusterRegistry()
        registry.create_cluster(["obs1", "obs2"])
        registry.create_cluster(["obs3", "obs4"])
        assert len(registry.get_all_clusters()) == 2

    def test_get_active_clusters(self):
        registry = ClusterRegistry()
        c1 = registry.create_cluster(["obs1", "obs2"])
        c1.interaction_density = 0.8
        c2 = registry.create_cluster(["obs3", "obs4"])
        c2.interaction_density = 0.01
        active = registry.get_active_clusters()
        assert len(active) == 1
