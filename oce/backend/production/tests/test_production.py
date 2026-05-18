"""Tests for V3 Phase 9 — Post-Deployment / Production Readiness"""

import time
import pytest

from oce.backend.production.deployment_pipeline import DeploymentPipeline, DeploymentResult
from oce.backend.production.monitoring_dashboard import MonitoringDashboard, HealthMetric, SystemHealth
from oce.backend.production.alert_system import AlertSystem, AlertRule, Alert
from oce.backend.production.backup_recovery import BackupRecovery, BackupSnapshot, RecoveryPoint
from oce.backend.production.documentation import Documentation, DocPage, DocSection
from oce.backend.production.performance_benchmarks import PerformanceBenchmarks, BenchmarkResult, BenchmarkSuite


# ─────────────────────────────────────────────────────────
# DeploymentPipeline
# ─────────────────────────────────────────────────────────

class TestDeploymentPipeline:

    def test_create(self):
        pipeline = DeploymentPipeline()
        assert pipeline._history == []

    def test_register_handler(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: None)
        assert "build" in pipeline._stage_handlers

    def test_run_stage_no_handler(self):
        pipeline = DeploymentPipeline()
        result = pipeline.run_stage("build")
        assert not result.passed
        assert "No handler" in result.message

    def test_run_stage_success(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: None)
        result = pipeline.run_stage("build")
        assert result.passed
        assert result.stage == "build"

    def test_run_stage_failure(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        result = pipeline.run_stage("build")
        assert not result.passed
        assert "fail" in result.message

    def test_run_all_stops_on_failure(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        results = pipeline.run_all()
        assert len(results) == 1  # stops after first failure
        assert not results[0].passed

    def test_run_all_success(self):
        pipeline = DeploymentPipeline()
        for stage in DeploymentPipeline.STAGES:
            pipeline.register_stage_handler(stage, lambda: None)
        results = pipeline.run_all()
        assert len(results) == len(DeploymentPipeline.STAGES)
        assert all(r.passed for r in results)

    def test_deploy_returns_bool(self):
        pipeline = DeploymentPipeline()
        for stage in DeploymentPipeline.STAGES:
            pipeline.register_stage_handler(stage, lambda: None)
        assert pipeline.deploy() is True

    def test_get_last_result(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: None)
        pipeline.run_stage("build")
        result = pipeline.get_last_result("build")
        assert result is not None
        assert result.stage == "build"

    def test_history(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: None)
        pipeline.run_stage("build")
        assert len(pipeline.history) == 1

    def test_stats(self):
        pipeline = DeploymentPipeline()
        pipeline.register_stage_handler("build", lambda: None)
        pipeline.run_stage("build")
        stats = pipeline.stats
        assert stats["total_runs"] == 1
        assert stats["success_rate"] == 1.0


# ─────────────────────────────────────────────────────────
# MonitoringDashboard
# ─────────────────────────────────────────────────────────

class TestMonitoringDashboard:

    def test_create(self):
        dash = MonitoringDashboard()
        assert dash._metrics == []

    def test_record_metric(self):
        dash = MonitoringDashboard()
        m = dash.record_metric("coherence", 0.85)
        assert m.name == "coherence"
        assert m.value == 0.85

    def test_metric_status_healthy(self):
        m = HealthMetric(metric_id="m1", name="test", value=0.3)
        assert m.status == "healthy"
        assert m.is_healthy

    def test_metric_status_warning(self):
        m = HealthMetric(metric_id="m1", name="test", value = 0.75)
        assert m.status == "warning"
        assert not m.is_healthy

    def test_metric_status_critical(self):
        m = HealthMetric(metric_id="m1", name="test", value=0.95)
        assert m.status == "critical"

    def test_get_latest_metric(self):
        dash = MonitoringDashboard()
        dash.record_metric("coherence", 0.5)
        dash.record_metric("coherence", 0.9)
        latest = dash.get_latest_metric("coherence")
        assert latest.value == 0.9

    def test_get_metrics_by_status(self):
        dash = MonitoringDashboard()
        dash.record_metric("healthy_metric", 0.3)
        dash.record_metric("warning_metric", 0.8)
        critical = dash.get_metrics_by_status("critical")
        healthy = dash.get_metrics_by_status("healthy")
        assert len(healthy) >= 1

    def test_record_health_snapshot(self):
        dash = MonitoringDashboard()
        snap = dash.record_health_snapshot(0.8, 0.9, 0.7, 0.85)
        assert snap.overall_score == pytest.approx(0.8125, abs=0.01)

    def test_health_status_healthy(self):
        snap = SystemHealth(overall_score=0.9, field_coherence=0.9, observer_health=0.9,
                            entropy_budget=0.9, topology_stability=0.9)
        assert snap.status == "healthy"
        assert not snap.needs_attention

    def test_health_status_critical(self):
        snap = SystemHealth(overall_score=0.3, field_coherence=0.2, observer_health=0.3,
                            entropy_budget=0.4, topology_stability=0.3)
        assert snap.status == "critical"
        assert snap.needs_attention

    def test_get_current_health(self):
        dash = MonitoringDashboard()
        dash.record_health_snapshot(0.8, 0.8, 0.8, 0.8)
        health = dash.get_current_health()
        assert health is not None

    def test_health_trend(self):
        dash = MonitoringDashboard()
        dash.record_health_snapshot(0.5, 0.5, 0.5, 0.5)
        dash.record_health_snapshot(0.8, 0.8, 0.8, 0.8)
        trend = dash.get_health_trend()
        assert trend > 0

    def test_stats(self):
        dash = MonitoringDashboard()
        dash.record_metric("test", 0.5)
        dash.record_health_snapshot(0.8, 0.8, 0.8, 0.8)
        stats = dash.stats
        assert stats["total_metrics_recorded"] == 1
        assert stats["total_snapshots"] == 1


# ─────────────────────────────────────────────────────────
# AlertSystem
# ─────────────────────────────────────────────────────────

class TestAlertSystem:

    def test_create(self):
        system = AlertSystem()
        assert system._rules == {}

    def test_add_rule(self):
        system = AlertSystem()
        rule = system.add_rule("High CPU", "cpu_usage", 0.9)
        assert rule.name == "High CPU"
        assert rule.threshold == 0.9

    def test_remove_rule(self):
        system = AlertSystem()
        rule = system.add_rule("Test", "metric", 0.5)
        assert system.remove_rule(rule.rule_id)
        assert rule.rule_id not in system._rules

    def test_evaluate_no_rules(self):
        system = AlertSystem()
        alerts = system.evaluate("cpu_usage", 0.95)
        assert len(alerts) == 0

    def test_evaluate_triggers_alert(self):
        system = AlertSystem()
        system.add_rule("High CPU", "cpu_usage", 0.8, cooldown_seconds=0)
        alerts = system.evaluate("cpu_usage", 0.9)
        assert len(alerts) == 1
        assert alerts[0].severity == "warning"

    def test_evaluate_below_threshold(self):
        system = AlertSystem()
        system.add_rule("High CPU", "cpu_usage", 0.8, cooldown_seconds=0)
        alerts = system.evaluate("cpu_usage", 0.5)
        assert len(alerts) == 0

    def test_evaluate_cooldown(self):
        system = AlertSystem()
        system.add_rule("High CPU", "cpu_usage", 0.8, cooldown_seconds=60)
        alerts1 = system.evaluate("cpu_usage", 0.9)
        alerts2 = system.evaluate("cpu_usage", 0.95)
        assert len(alerts1) == 1
        assert len(alerts2) == 0  # cooldown active

    def test_acknowledge(self):
        system = AlertSystem()
        system.add_rule("Test", "metric", 0.5, cooldown_seconds=0)
        alerts = system.evaluate("metric", 0.9)
        assert system.acknowledge(alerts[0].alert_id)
        assert alerts[0].state == "acknowledged"

    def test_resolve(self):
        system = AlertSystem()
        system.add_rule("Test", "metric", 0.5, cooldown_seconds=0)
        alerts = system.evaluate("metric", 0.9)
        assert system.resolve(alerts[0].alert_id)
        assert alerts[0].state == "resolved"

    def test_get_active_alerts(self):
        system = AlertSystem()
        system.add_rule("Test", "metric", 0.5, cooldown_seconds=0)
        system.evaluate("metric", 0.9)
        active = system.get_active_alerts()
        assert len(active) == 1

    def test_alert_is_active(self):
        alert = Alert(alert_id="a1", rule_id="r1", name="Test", severity="warning")
        assert alert.is_active

    def test_alert_not_active_when_resolved(self):
        alert = Alert(alert_id="a1", rule_id="r1", name="Test", severity="warning", state="resolved")
        assert not alert.is_active

    def test_stats(self):
        system = AlertSystem()
        system.add_rule("Test", "metric", 0.5, cooldown_seconds=0)
        system.evaluate("metric", 0.9)
        stats = system.stats
        assert stats["total_rules"] == 1
        assert stats["active_alerts"] == 1


# ─────────────────────────────────────────────────────────
# BackupRecovery
# ─────────────────────────────────────────────────────────

class TestBackupRecovery:

    def test_create(self):
        br = BackupRecovery()
        assert br._snapshots == {}

    def test_create_snapshot(self):
        br = BackupRecovery()
        snap = br.create_snapshot("v1.0", {"key": "value"})
        assert snap.label == "v1.0"
        assert snap.state_data == {"key": "value"}

    def test_get_snapshot(self):
        br = BackupRecovery()
        snap = br.create_snapshot("test", {"a": 1})
        retrieved = br.get_snapshot(snap.snapshot_id)
        assert retrieved == snap

    def test_verify_snapshot_valid(self):
        br = BackupRecovery()
        snap = br.create_snapshot("test", {"key": "value"})
        assert br.verify_snapshot(snap.snapshot_id)

    def test_verify_snapshot_invalid(self):
        br = BackupRecovery()
        assert not br.verify_snapshot("nonexistent")

    def test_create_recovery_point(self):
        br = BackupRecovery()
        snap = br.create_snapshot("test", {"key": "value"})
        rp = br.create_recovery_point(snap.snapshot_id)
        assert rp is not None
        assert rp.verified

    def test_restore(self):
        br = BackupRecovery()
        snap = br.create_snapshot("test", {"key": "value"})
        rp = br.create_recovery_point(snap.snapshot_id)
        restored = br.restore(rp.recovery_id)
        assert restored == {"key": "value"}

    def test_restore_unverified_fails(self):
        br = BackupRecovery()
        snap = br.create_snapshot("test", {})
        rp = br.create_recovery_point(snap.snapshot_id)
        # Empty dict fails verification
        restored = br.restore(rp.recovery_id)
        assert restored is None

    def test_prune_snapshots(self):
        br = BackupRecovery()
        snap = br.create_snapshot("old", {"key": "value"})
        # Manually set timestamp to old
        snap.timestamp = time.time() - 100000
        removed = br.prune_snapshots(max_age_seconds=1000)
        assert removed == 1

    def test_get_latest_snapshot(self):
        br = BackupRecovery()
        import time as _time
        snap1 = br.create_snapshot("first", {"a": 1})
        snap1.timestamp = _time.time() - 10
        snap2 = br.create_snapshot("second", {"b": 2})
        latest = br.get_latest_snapshot()
        assert latest.label == "second"

    def test_stats(self):
        br = BackupRecovery()
        br.create_snapshot("test", {"key": "value"})
        stats = br.stats
        assert stats["total_snapshots"] == 1


# ─────────────────────────────────────────────────────────
# Documentation
# ─────────────────────────────────────────────────────────

class TestDocumentation:

    def test_create(self):
        doc = Documentation()
        assert doc._sections == {}

    def test_add_section(self):
        doc = Documentation()
        section = doc.add_section("API", "API documentation")
        assert section.title == "API"

    def test_add_page(self):
        doc = Documentation()
        page = doc.add_page("Overview", "System overview content")
        assert page.title == "Overview"
        assert page.word_count > 0

    def test_add_page_to_section(self):
        doc = Documentation()
        section = doc.add_section("API")
        doc.add_page("Endpoint", "Content", section_id=section.section_id)
        pages = doc.get_section_pages(section.section_id)
        assert len(pages) == 1

    def test_get_page(self):
        doc = Documentation()
        page = doc.add_page("Test", "Content")
        retrieved = doc.get_page(page.page_id)
        assert retrieved == page

    def test_search(self):
        doc = Documentation()
        doc.add_page("API Reference", "REST API endpoints for V3")
        doc.add_page("Deployment Guide", "How to deploy the system")
        results = doc.search("API")
        assert len(results) >= 1

    def test_page_word_count(self):
        page = DocPage(page_id="p1", title="Test", content="one two three four five")
        assert page.word_count == 5

    def test_page_update(self):
        page = DocPage(page_id="p1", title="Test", content="old")
        page.update("new content")
        assert page.content == "new content"

    def test_completeness_empty(self):
        doc = Documentation()
        comp = doc.get_completeness()
        assert comp["total_sections"] == 0

    def test_completeness_with_content(self):
        doc = Documentation()
        doc.add_page("Test", "some content here")
        comp = doc.get_completeness()
        assert comp["pages_with_content"] == 1
        assert comp["completeness_pct"] == 1.0

    def test_stats(self):
        doc = Documentation()
        doc.add_page("Test", "hello world")
        stats = doc.stats
        assert stats["total_pages"] == 1
        assert stats["total_words"] == 2


# ─────────────────────────────────────────────────────────
# PerformanceBenchmarks
# ─────────────────────────────────────────────────────────

class TestPerformanceBenchmarks:

    def test_create(self):
        pb = PerformanceBenchmarks()
        assert pb._results == []

    def test_set_baseline(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("latency", 100.0)
        assert pb._baselines["latency"] == 100.0

    def test_run_benchmark(self):
        pb = PerformanceBenchmarks()
        result = pb.run_benchmark("latency", 85.0, "ms")
        assert result.name == "latency"
        assert result.value == 85.0

    def test_benchmark_with_baseline(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("throughput", 100.0)
        result = pb.run_benchmark("throughput", 120.0)
        assert result.meets_baseline
        assert result.improvement_pct == 20.0

    def test_benchmark_below_baseline(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("throughput", 100.0)
        result = pb.run_benchmark("throughput", 80.0)
        assert not result.meets_baseline

    def test_get_latest_result(self):
        pb = PerformanceBenchmarks()
        pb.run_benchmark("latency", 80.0)
        pb.run_benchmark("latency", 90.0)
        latest = pb.get_latest_result("latency")
        assert latest.value == 90.0

    def test_get_results_by_name(self):
        pb = PerformanceBenchmarks()
        pb.run_benchmark("latency", 80.0)
        pb.run_benchmark("latency", 90.0)
        pb.run_benchmark("throughput", 1000.0)
        results = pb.get_results_by_name("latency")
        assert len(results) == 2

    def test_create_suite(self):
        pb = PerformanceBenchmarks()
        suite = pb.create_suite("V3 Core", "Core V3 benchmarks")
        assert suite.name == "V3 Core"

    def test_add_to_suite(self):
        pb = PerformanceBenchmarks()
        suite = pb.create_suite("Test")
        result = pb.run_benchmark("test", 1.0)
        assert pb.add_to_suite(suite.suite_id, result)

    def test_compare_to_baseline(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("latency", 100.0)
        pb.run_benchmark("latency", 80.0)
        comp = pb.compare_to_baseline("latency")
        assert comp["improvement_pct"] == -20.0

    def test_get_all_comparisons(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("a", 10.0)
        pb.set_baseline("b", 20.0)
        pb.run_benchmark("a", 8.0)
        pb.run_benchmark("b", 25.0)
        comps = pb.get_all_comparisons()
        assert len(comps) == 2

    def test_stats(self):
        pb = PerformanceBenchmarks()
        pb.set_baseline("throughput", 100.0)
        pb.run_benchmark("throughput", 110.0)
        stats = pb.stats
        assert stats["total_benchmarks"] == 1
        assert stats["meeting_baseline"] == 1
