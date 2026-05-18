"""Tests for V3 Phase 7 — Multi-Scale Cognitive Fields"""

import pytest
from datetime import datetime

# Import all modules
from oce.backend.multiscale.local_fields import LocalObserverField, LocalFieldRegistry
from oce.backend.multiscale.regional_clusters import RegionalCluster, ClusterRegistry
from oce.backend.multiscale.global_attractor import GlobalAttractor, GlobalAttractorLayer
from oce.backend.multiscale.hierarchical_sync import SyncManager, SyncFrequency, SyncRecord
from oce.backend.multiscale.nested_repair import NestedRepairSystem, RepairRequest, RepairEscalation
from oce.backend.multiscale.scale_routing import ScaleAdaptiveRouter, ScaleLevel, RoutedMessage
from oce.backend.multiscale.entropy_containment import EntropyContainmentSystem, ContainmentBoundary


class TestLocalObserverField:
    """Tests for LocalObserverField."""
    
    def test_create_field(self):
        field = LocalObserverField(observer_id="test_observer")
        assert field.observer_id == "test_observer"
        assert field.coherence_level == 1.0
        assert field.local_operations == 0
    
    def test_update_state(self):
        field = LocalObserverField(observer_id="test_observer")
        field.update_state("key1", "value1")
        assert field.get_state("key1") == "value1"
        assert field.local_operations == 1
    
    def test_needs_sync(self):
        field = LocalObserverField(observer_id="test_observer", sync_bound=5)
        assert not field.needs_sync()
        for _ in range(5):
            field.update_state("key", "value")
        assert field.needs_sync()
    
    def test_calculate_coherence(self):
        field = LocalObserverField(observer_id="test_observer")
        coherence = field.calculate_coherence()
        assert 0.0 <= coherence <= 1.0


class TestLocalFieldRegistry:
    """Tests for LocalFieldRegistry."""
    
    def test_register_and_get(self):
        registry = LocalFieldRegistry()
        field = registry.register("observer1")
        assert field.observer_id == "observer1"
        assert registry.get("observer1") == field
    
    def test_get_needing_sync(self):
        registry = LocalFieldRegistry()
        registry.register("obs1", sync_bound=2)
        registry.register("obs2", sync_bound=10)
        registry.get("obs1").update_state("k", "v")
        registry.get("obs1").update_state("k", "v")
        needing = registry.get_needing_sync()
        assert len(needing) == 1
        assert needing[0].observer_id == "obs1"


class TestRegionalCluster:
    """Tests for RegionalCluster."""
    
    def test_create_cluster(self):
        cluster = RegionalCluster(cluster_id="cluster_1")
        assert cluster.cluster_id == "cluster_1"
        assert len(cluster.members) == 0
    
    def test_add_remove_members(self):
        cluster = RegionalCluster(cluster_id="cluster_1")
        cluster.add_member("obs1")
        cluster.add_member("obs2")
        assert cluster.get_member_count() == 2
        assert cluster.remove_member("obs1")
        assert cluster.get_member_count() == 1


class TestClusterRegistry:
    """Tests for ClusterRegistry."""
    
    def test_create_cluster(self):
        registry = ClusterRegistry()
        cluster = registry.create_cluster(["obs1", "obs2"])
        assert cluster.get_member_count() == 2
    
    def test_get_cluster_for_observer(self):
        registry = ClusterRegistry()
        cluster = registry.create_cluster(["obs1", "obs2"])
        retrieved = registry.get_cluster_for_observer("obs1")
        assert retrieved == cluster


class TestGlobalAttractor:
    """Tests for GlobalAttractor."""
    
    def test_create_attractor(self):
        attractor = GlobalAttractor()
        assert attractor.attractor_id == "global_attractor"
        assert attractor.influence_strength == 0.3
    
    def test_set_get_direction(self):
        attractor = GlobalAttractor()
        attractor.set_direction({"goal": "test"})
        assert attractor.get_direction() == {"goal": "test"}
    
    def test_calculate_influence(self):
        attractor = GlobalAttractor()
        assert attractor.calculate_influence("local") == 0.1
        assert attractor.calculate_influence("global") == 1.0


class TestGlobalAttractorLayer:
    """Tests for GlobalAttractorLayer."""
    
    def test_update_direction(self):
        layer = GlobalAttractorLayer()
        layer.update_direction({"strategy": "expand"})
        assert layer.get_current_direction() == {"strategy": "expand"}


class TestSyncManager:
    """Tests for SyncManager."""
    
    def test_should_sync(self):
        manager = SyncManager()
        assert manager.should_sync(SyncFrequency.LOCAL)
    
    def test_perform_sync(self):
        manager = SyncManager()
        record = manager.perform_sync(SyncFrequency.LOCAL, ["obs1"], {"data": "test"})
        assert isinstance(record, SyncRecord)
        assert record.scale == SyncFrequency.LOCAL


class TestNestedRepairSystem:
    """Tests for NestedRepairSystem."""
    
    def test_submit_repair(self):
        system = NestedRepairSystem()
        request = system.submit_repair("bug", 0.5, "module_x", "Test issue")
        assert request.issue_type == "bug"
        assert request.escalation_level == RepairEscalation.LOCAL
    
    def test_escalation_by_severity(self):
        system = NestedRepairSystem()
        local_req = system.submit_repair("bug", 0.2, "loc", "minor")
        regional_req = system.submit_repair("bug", 0.7, "loc", "major")
        global_req = system.submit_repair("bug", 0.95, "loc", "critical")
        assert local_req.escalation_level == RepairEscalation.LOCAL
        assert regional_req.escalation_level == RepairEscalation.REGIONAL
        assert global_req.escalation_level == RepairEscalation.GLOBAL


class TestScaleAdaptiveRouter:
    """Tests for ScaleAdaptiveRouter."""
    
    def test_classify_local(self):
        router = ScaleAdaptiveRouter()
        assert router.classify_message("local update") == ScaleLevel.LOCAL
    
    def test_classify_global(self):
        router = ScaleAdaptiveRouter()
        assert router.classify_message("global strategic update") == ScaleLevel.GLOBAL
    
    def test_route_message(self):
        router = ScaleAdaptiveRouter()
        msg = router.route("local info", "source1", local_targets=["obs1"])
        assert msg.scale_level == ScaleLevel.LOCAL
        assert msg.delivered


class TestEntropyContainment:
    """Tests for EntropyContainmentSystem."""
    
    def test_add_entropy(self):
        system = EntropyContainmentSystem()
        breached = system.add_entropy("local", 2.0)
        assert breached
    
    def test_resolve_entropy(self):
        system = EntropyContainmentSystem()
        system.add_entropy("local", 0.5)
        system.resolve_entropy("local", 0.5)
        status = system.get_containment_status()
        assert status["local"]["contained"]
    
    def test_get_stats(self):
        system = EntropyContainmentSystem()
        stats = system.stats
        assert "total_boundaries" in stats
        assert stats["total_boundaries"] == 3