"""
Tests for OCE DSPy Execution Optimizer — OCE-6.4a
====================================================
Tests for the heuristic fallback pipelines (DSPy not required).
"""

import pytest


class TestExecutionOptimizerPipeline:
    """Tests for ExecutionOptimizerPipeline."""

    def test_heuristic_empty_history(self):
        from dspy_execution_optimizer import _heuristic_worker_count
        stats = {"total": 0, "by_status": {}, "avg_latency_ms": 100}
        assert _heuristic_worker_count(stats) == 2

    def test_heuristic_high_throughput(self):
        from dspy_execution_optimizer import _heuristic_worker_count
        stats = {"total": 100, "by_status": {"completed": 95, "failed": 5}, "avg_latency_ms": 30}
        workers = _heuristic_worker_count(stats)
        assert workers >= 4

    def test_heuristic_high_failure_rate(self):
        from dspy_execution_optimizer import _heuristic_worker_count
        stats = {"total": 100, "by_status": {"completed": 60, "failed": 40}, "avg_latency_ms": 200}
        workers = _heuristic_worker_count(stats)
        assert workers <= 5

    def test_pipeline_records_executions(self):
        from dspy_execution_optimizer import ExecutionOptimizerPipeline
        p = ExecutionOptimizerPipeline()
        for i in range(10):
            p.record_execution("skill_call", "completed", 50.0)
        assert len(p._history) == 10

    def test_pipeline_history_limit(self):
        from dspy_execution_optimizer import ExecutionOptimizerPipeline
        p = ExecutionOptimizerPipeline()
        for i in range(1100):
            p.record_execution("skill_call", "completed", 50.0)
        assert len(p._history) == 1000

    def test_pipeline_recommend_workers(self):
        from dspy_execution_optimizer import get_optimizer
        opt = get_optimizer()
        stats = {"total": 50, "by_status": {"completed": 45, "failed": 5}, "avg_latency_ms": 30}
        recommended = opt.recommend_workers(current_workers=2, history_stats=stats)
        assert 2 <= recommended <= 16


class TestTaskSchedulingPipeline:
    """Tests for TaskSchedulingPipeline."""

    def test_heuristic_critical_types(self):
        from dspy_execution_optimizer import _heuristic_priority
        assert _heuristic_priority("agent_delegate", 0.5) == 3
        assert _heuristic_priority("repair", 0.5) == 3

    def test_heuristic_high_types(self):
        from dspy_execution_optimizer import _heuristic_priority
        assert _heuristic_priority("skill_call", 0.3) == 2
        assert _heuristic_priority("pipeline_run", 0.3) == 2

    def test_heuristic_low_types(self):
        from dspy_execution_optimizer import _heuristic_priority
        assert _heuristic_priority("log", 0.5) == 0
        assert _heuristic_priority("cleanup", 0.5) == 0

    def test_heuristic_load_dependent(self):
        from dspy_execution_optimizer import _heuristic_priority
        # Under high load, normal tasks get deprioritized
        assert _heuristic_priority("tool_invoke", 0.9) == 0
        # Under low load, normal tasks get higher priority
        assert _heuristic_priority("tool_invoke", 0.3) == 2

    def test_pipeline_recommend_priority(self):
        from dspy_execution_optimizer import get_scheduler
        sched = get_scheduler()
        priority = sched.recommend_priority("skill_call", 0.3, 5, 0.1)
        assert 0 <= priority <= 3


class TestRetryPolicyPipeline:
    """Tests for RetryPolicyPipeline."""

    def test_heuristic_no_failures(self):
        from dspy_execution_optimizer import _heuristic_retry_policy
        policy = _heuristic_retry_policy("skill_call", [])
        assert policy["max_retries"] == 1
        assert "timeout" in policy["retry_on"]

    def test_heuristic_some_failures(self):
        from dspy_execution_optimizer import _heuristic_retry_policy
        failures = [
            {"task_type": "skill_call", "error": "timeout"},
            {"task_type": "skill_call", "error": "handler_error"},
        ]
        policy = _heuristic_retry_policy("skill_call", failures)
        assert policy["max_retries"] == 2
        assert policy["backoff_sec"] == 2.0

    def test_heuristic_many_failures(self):
        from dspy_execution_optimizer import _heuristic_retry_policy
        failures = [{"task_type": "skill_call", "error": "timeout"} for _ in range(5)]
        policy = _heuristic_retry_policy("skill_call", failures)
        assert policy["max_retries"] == 3
        assert policy["backoff_sec"] == 5.0
        assert "resource_exhausted" in policy["retry_on"]

    def test_pipeline_recommend_retry(self):
        from dspy_execution_optimizer import get_retry_advisor
        advisor = get_retry_advisor()
        failures = [{"task_type": "tool_invoke", "error": "timeout", "attempts": 2}]
        policy = advisor.recommend_retry_policy("tool_invoke", failures)
        assert "max_retries" in policy
        assert "backoff_sec" in policy
        assert "retry_on" in policy


class TestDSPyAvailability:
    """Test that the module works with or without DSPy."""

    def test_module_imports(self):
        from dspy_execution_optimizer import (
            ExecutionOptimizerPipeline,
            TaskSchedulingPipeline,
            RetryPolicyPipeline,
            get_optimizer,
            get_scheduler,
            get_retry_advisor,
            DSPY_AVAILABLE,
        )
        assert isinstance(DSPY_AVAILABLE, bool)

    def test_singleton_instances(self):
        from dspy_execution_optimizer import get_optimizer, get_scheduler, get_retry_advisor
        assert get_optimizer() is get_optimizer()
        assert get_scheduler() is get_scheduler()
        assert get_retry_advisor() is get_retry_advisor()
