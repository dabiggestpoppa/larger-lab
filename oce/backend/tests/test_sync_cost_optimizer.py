"""
Tests for OCE Sync Cost Optimizer — OCE-9.5b
==============================================
10+ tests covering sync pattern analysis, optimization, batching.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_sync_cost(tmp_path):
    """Reset the SyncCostOptimizer singleton before each test."""
    from sync_cost_optimizer import SyncCostOptimizer
    import sync_cost_optimizer
    original_path = sync_cost_optimizer.DB_PATH
    test_db = str(tmp_path / "test_sync_cost.db")
    sync_cost_optimizer.DB_PATH = test_db
    SyncCostOptimizer._instance = None
    yield
    SyncCostOptimizer._instance = None
    sync_cost_optimizer.DB_PATH = original_path


class TestSyncCostOptimizerInit:
    def test_singleton_identity(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s1 = get_sync_cost_optimizer()
        s2 = get_sync_cost_optimizer()
        assert s1 is s2


class TestSyncPatternAnalysis:
    def test_analyze_empty(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        result = s.analyze_sync_patterns()
        assert result["total_syncs"] == 0
        assert result["total_cost"] == 0.0

    def test_analyze_with_data(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        s.record_sync("obs-1", "obs-2", "state_sync", 1.0)
        s.record_sync("obs-2", "obs-3", "state_sync", 1.5)
        result = s.analyze_sync_patterns()
        assert result["total_syncs"] >= 2
        assert result["total_cost"] >= 2.5

    def test_analyze_structure(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        result = s.analyze_sync_patterns()
        assert "by_type" in result
        assert "by_pair" in result
        assert "recommendations" in result


class TestSyncCostReport:
    def test_report_structure(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        report = s.get_sync_cost_report()
        assert "total_syncs" in report
        assert "total_cost" in report
        assert "avg_cost_per_sync" in report

    def test_report_with_data(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        s.record_sync("a", "b", "test", 2.0)
        report = s.get_sync_cost_report()
        assert report["total_syncs"] >= 1


class TestSyncScheduleOptimization:
    def test_optimize_returns_suggestions(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        result = s.optimize_sync_schedule()
        assert "optimizations" in result
        assert "current_patterns" in result

    def test_optimize_empty(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        result = s.optimize_sync_schedule()
        assert len(result["optimizations"]) >= 1


class TestSyncBatching:
    def test_batch_operations(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        ops = [
            {"source": "a", "target": "b", "sync_type": "test", "cost": 1.0},
            {"source": "c", "target": "d", "sync_type": "test", "cost": 2.0},
        ]
        result = s.batch_sync_operations(ops)
        assert result["batched_count"] == 2
        assert result["savings_pct"] == 50.0

    def test_batch_reduces_cost(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        ops = [{"source": "a", "target": "b", "sync_type": "test", "cost": 10.0}]
        result = s.batch_sync_operations(ops)
        assert result["total_cost"] == 5.0  # 50% reduction


class TestSyncPriority:
    def test_set_priority(self):
        from sync_cost_optimizer import get_sync_cost_optimizer
        s = get_sync_cost_optimizer()
        s.set_sync_priority("obs-1->obs-2", "critical")
        assert s._sync_priorities["obs-1->obs-2"] == "critical"
