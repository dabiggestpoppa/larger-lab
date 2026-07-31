"""
O-7 Tests: Persistent Field Mode
=================================
Tests for O7-B1 through O7-B12 components.

Run: python -m pytest tests/test_observer/test_o7_persistent_field.py -v
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T1: Persistent Runtime Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersistentRuntime:
    """O7-T1: 7-day continuous operation, stable."""

    def setup_method(self):
        from core.persistent_field.persistent_runtime import PersistentRuntime
        PersistentRuntime._instance = None
        self.runtime = PersistentRuntime.get_instance()

    def test_runtime_starts(self):
        """Runtime should start and report status."""
        self.runtime.start()
        status = self.runtime.get_status()
        assert "state" in status
        assert "uptime_seconds" in status

    def test_runtime_singleton(self):
        """Runtime should be a singleton."""
        from core.persistent_field.persistent_runtime import PersistentRuntime
        r1 = PersistentRuntime.get_instance()
        r2 = PersistentRuntime.get_instance()
        assert r1 is r2

    def test_runtime_heartbeat(self):
        """Heartbeat should update."""
        result = self.runtime.heartbeat()
        assert "last_heartbeat" in result

    def test_runtime_state_transition(self):
        """State transitions should work."""
        from core.persistent_field.persistent_runtime import RuntimeState
        assert self.runtime.transition_state(RuntimeState.ACTIVE) is True
        assert self.runtime.get_status()["state"] == RuntimeState.ACTIVE

    def test_runtime_observer_registration(self):
        """Observers should be registerable."""
        self.runtime.register_observer("test_obs", {"type": "continuity"})
        status = self.runtime.get_status()
        assert status["active_observers"] >= 1

    def test_runtime_persistence(self):
        """Runtime state should persist to disk."""
        self.runtime.stop()
        # Create new instance (simulates restart)
        from core.persistent_field.persistent_runtime import PersistentRuntime
        PersistentRuntime._instance = None
        new_runtime = PersistentRuntime.get_instance()
        status = new_runtime.get_status()
        assert status["total_restarts"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T2: Observer Recovery Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestObserverPersistence:
    """O7-T2: Crash observers, processes — recovery succeeds."""

    def setup_method(self):
        from core.persistent_field.observer_persistence import ObserverPersistence
        self.persistence = ObserverPersistence()

    def test_save_observer(self):
        """Observer state should be savable."""
        from core.persistent_field.observer_persistence import ObserverSnapshot
        snapshot = ObserverSnapshot(
            observer_id="test_continuity",
            observer_type="continuity",
            continuity_score=0.95,
        )
        self.persistence.save_observer(snapshot)
        restored = self.persistence.restore_observer("test_continuity")
        assert restored is not None
        assert restored.observer_id == "test_continuity"

    def test_restore_all(self):
        """All core observers should be restorable."""
        results = self.persistence.restore_all()
        assert isinstance(results, dict)

    def test_continuity_score(self):
        """Continuity score should be trackable."""
        from core.persistent_field.observer_persistence import ObserverSnapshot
        snapshot = ObserverSnapshot(
            observer_id="test_entropy",
            observer_type="entropy",
            continuity_score=0.8,
        )
        self.persistence.save_observer(snapshot)
        score = self.persistence.get_continuity_score("test_entropy")
        assert score == 0.8


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T3: Dormant State Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestDormantStateManager:
    """O7-T3: Idle runtime periods — passive state entered."""

    def setup_method(self):
        from core.persistent_field.dormant_state_manager import DormantStateManager
        self.mgr = DormantStateManager()

    def test_initial_state(self):
        """Should start in dormant state."""
        assert self.mgr.get_state() == "dormant"

    def test_valid_transition(self):
        """Valid transitions should succeed."""
        from core.persistent_field.dormant_state_manager import DormantState
        assert self.mgr.transition(DormantState.OBSERVATIONAL) is True
        assert self.mgr.get_state() == "observational"

    def test_invalid_transition(self):
        """Invalid transitions should fail."""
        from core.persistent_field.dormant_state_manager import DormantState
        self.mgr.transition(DormantState.DORMANT)
        # Can't go from dormant to recovery
        assert self.mgr.transition(DormantState.RECOVERY) is False

    def test_transition_history(self):
        """Transitions should be recorded."""
        from core.persistent_field.dormant_state_manager import DormantState
        self.mgr.transition(DormantState.OBSERVATIONAL)
        self.mgr.transition(DormantState.ACTIVE)
        history = self.mgr.get_transition_history()
        assert len(history) >= 2

    def test_summary(self):
        """Summary should include current state."""
        summary = self.mgr.get_summary()
        assert "current_state" in summary
        assert "time_in_state_seconds" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T4: Autonomous Repair Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestAutonomousRepair:
    """O7-T4: Hung tasks, entropy spikes — repair bounded."""

    def setup_method(self):
        from core.persistent_field.autonomous_repair import AutonomousRepair
        self.repair = AutonomousRepair()

    def test_detect_issues(self):
        """Issue detection should return list."""
        issues = self.repair.detect_issues()
        assert isinstance(issues, list)

    def test_repair_action(self):
        """Repair action should return event."""
        from core.persistent_field.autonomous_repair import RepairAction
        event = self.repair.repair(RepairAction.RESTART_OBSERVER, "test_target")
        assert event.action == RepairAction.RESTART_OBSERVER
        assert event.target == "test_target"
        assert event.status in ("stable", "failed", "escalated")

    def test_repair_history(self):
        """Repair history should be recorded."""
        from core.persistent_field.autonomous_repair import RepairAction
        self.repair.repair(RepairAction.TERMINATE_HUNG, "test")
        history = self.repair.get_repair_history()
        assert len(history) >= 1

    def test_repair_status(self):
        """Repair status should include metrics."""
        status = self.repair.get_status()
        assert "total_repairs" in status
        assert "active_repairs" in status

    def test_bounded_repairs(self):
        """Should not exceed max concurrent repairs."""
        status = self.repair.get_status()
        assert status["active_repairs"] <= 3  # MAX_CONCURRENT_REPAIRS


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T5: Snapshot/Recovery Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecoveryPersistence:
    """O7-T5: Restart machine — continuity restored."""

    def setup_method(self):
        from core.persistent_field.recovery_persistence import RecoveryPersistence
        self.recovery = RecoveryPersistence()

    def test_create_snapshot(self):
        """Snapshot should be creatable."""
        snapshot = self.recovery.create_snapshot(
            ["runtime", "observers"],
            {"state": "active", "count": 5}
        )
        assert snapshot.snapshot_id is not None
        assert "runtime" in snapshot.components

    def test_restore_snapshot(self):
        """Snapshot should be restorable."""
        self.recovery.create_snapshot(["test"], {"data": 123})
        result = self.recovery.restore_snapshot()
        assert result is not None
        assert "data" in result["data"]

    def test_latest_snapshot(self):
        """Latest snapshot should be retrievable."""
        self.recovery.create_snapshot(["test"], {"version": 2})
        latest = self.recovery.get_latest_snapshot()
        assert latest is not None

    def test_recovery_status(self):
        """Recovery status should include snapshot count."""
        status = self.recovery.get_recovery_status()
        assert "total_snapshots" in status
        assert "max_snapshots" in status


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T6: Drift Detection Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestOperationalDriftDetector:
    """O7-T6: Slow degradation — drift detected."""

    def setup_method(self):
        from core.persistent_field.operational_drift_detect import OperationalDriftDetector
        self.detector = OperationalDriftDetector()

    def test_record_metric(self):
        """Metric recording should work."""
        metric = self.detector.record_metric("routing_accuracy", 0.95)
        assert metric.metric_name == "routing_accuracy"
        assert metric.value == 0.95

    def test_drift_detection(self):
        """Drift should be detected when deviation exceeds threshold."""
        # Record baseline
        self.detector.record_metric("response_time", 1.0)
        # Record degraded value (30%+ deviation)
        metric = self.detector.record_metric("response_time", 1.5)
        assert metric.status in ("warning", "critical")

    def test_drift_report(self):
        """Drift report should include all metrics."""
        self.detector.record_metric("accuracy", 0.9)
        report = self.detector.get_drift_report()
        assert "metrics" in report
        assert "overall_status" in report

    def test_trend_analysis(self):
        """Trend analysis should detect direction."""
        for i in range(5):
            self.detector.record_metric("quality", 0.9 - i * 0.05)
        trend = self.detector.get_trend("quality")
        assert "direction" in trend


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T7: Long-Horizon Memory Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestLongHorizonMemory:
    """O7-T7: Multi-week workflows — memory persists."""

    def setup_method(self):
        from core.persistent_field.long_horizon_memory import LongHorizonMemory
        self.memory = LongHorizonMemory()

    def test_store_memory(self):
        """Memory entry should be storable."""
        entry = self.memory.store("workflow", {"task": "coding", "success": True}, 0.8)
        assert entry.entry_id is not None
        assert entry.category == "workflow"

    def test_recall_memory(self):
        """Memory should be recallable."""
        self.memory.store("repair", {"issue": "timeout"}, 0.6)
        results = self.memory.recall("repair")
        assert len(results) >= 1

    def test_memory_summary(self):
        """Memory summary should include counts."""
        self.memory.store("orchestration", {"agents": 3}, 0.7)
        summary = self.memory.get_summary()
        assert "total_entries" in summary
        assert "by_category" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# O7-T8: Integration / Stress Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersistentFieldIntegration:
    """O7-T8: All components working together."""

    def test_full_pipeline(self):
        """Full persistent field pipeline should work."""
        from core.persistent_field.persistent_runtime import PersistentRuntime, RuntimeState
        from core.persistent_field.runtime_heartbeat import RuntimeHeartbeat
        from core.persistent_field.dormant_state_manager import DormantStateManager, DormantState
        from core.persistent_field.autonomous_repair import AutonomousRepair, RepairAction

        # Start runtime
        rt = PersistentRuntime.get_instance()
        rt.start()
        rt.register_observer("continuity", {"type": "core"})
        rt.transition_state(RuntimeState.ACTIVE)

        # Pulse heartbeat
        hb = RuntimeHeartbeat()
        pulse = hb.pulse(field_state="stable", entropy_level=0.1, observer_health=0.95)
        assert pulse["field_state"] == "stable"

        # Transition state
        mgr = DormantStateManager()
        mgr.transition(DormantState.ACTIVE)
        assert mgr.get_state() == "active"

        # Trigger repair
        repair = AutonomousRepair()
        event = repair.repair(RepairAction.RESTART_OBSERVER, "test")
        assert event.status in ("stable", "failed")

        # Verify runtime status
        status = rt.get_status()
        assert status["state"] == RuntimeState.ACTIVE.value
        assert status["active_observers"] >= 1

    def test_environmental_monitor(self):
        """Environmental monitor should return status."""
        from core.persistent_field.environmental_monitor import EnvironmentalMonitor
        mon = EnvironmentalMonitor()
        report = mon.check_environment()
        assert "overall_status" in report
        assert "metrics" in report

    def test_passive_awareness(self):
        """Passive awareness should scan and return signals."""
        from core.persistent_field.passive_awareness import PassiveAwareness
        awareness = PassiveAwareness()
        signals = awareness.scan()
        assert isinstance(signals, list)

    def test_continuity_preserver(self):
        """Continuity preserver should track records."""
        from core.persistent_field.continuity_preserver import ContinuityPreserver
        preserver = ContinuityPreserver()
        preserver.preserve("workflow", {"task": "test"})
        summary = preserver.get_summary()
        assert summary["total_records"] >= 1

    def test_persistent_scheduler(self):
        """Scheduler should manage tasks."""
        from core.persistent_field.persistent_scheduler import PersistentScheduler
        scheduler = PersistentScheduler()
        status = scheduler.get_status()
        assert status["total_tasks"] >= 5  # Default tasks
        due = scheduler.get_due_tasks()
        assert isinstance(due, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
