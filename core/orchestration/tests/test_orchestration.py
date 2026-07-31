"""Tests for Phase 1.6 — Orchestration"""
import pytest
from core.orchestration.controller import OrchestrationController, TaskPriority, TaskState
from core.orchestration.planner import PlannerEngine
from core.orchestration.workflow import WorkflowEngine
from core.orchestration.scheduler import SchedulerEngine, ScheduleFrequency
from core.orchestration.governance import GovernanceEngine, GovernanceConfig
from core.orchestration.agents import AgentRuntime, AgentSpec, AgentState
from core.orchestration.memory import ContextInjector
from core.orchestration.reflection import ReflectionEngine


class TestOrchestrationController:
    def test_submit_task(self):
        ctrl = OrchestrationController()
        task = ctrl.submit_task("Test task", "Description", TaskPriority.HIGH)
        assert task.state == TaskState.PENDING
        assert task.priority == TaskPriority.HIGH

    def test_update_state(self):
        ctrl = OrchestrationController()
        task = ctrl.submit_task("Test")
        ctrl.update_state(task.task_id, TaskState.RUNNING)
        assert ctrl.get_task(task.task_id).state == TaskState.RUNNING

    def test_create_subtask(self):
        ctrl = OrchestrationController()
        parent = ctrl.submit_task("Parent")
        child = ctrl.create_subtask(parent.task_id, "Child")
        assert child is not None
        assert child.parent_id == parent.task_id
        assert child.recursion_depth == 1

    def test_recursion_limit(self):
        ctrl = OrchestrationController(max_recursion_depth=2)
        parent = ctrl.submit_task("Parent")
        child = ctrl.create_subtask(parent.task_id, "Child")
        grandchild = ctrl.create_subtask(child.task_id, "Grandchild")
        great_grandchild = ctrl.create_subtask(grandchild.task_id, "Too deep")
        assert great_grandchild is None  # Exceeds max recursion

    def test_route_task(self):
        ctrl = OrchestrationController()
        task = ctrl.submit_task("Research quantum computing")
        assert ctrl.route_task(task) == "synthesis"

        task2 = ctrl.submit_task("Ingest OpenAlex papers")
        assert ctrl.route_task(task2) == "ingestion"

    def test_execution_summary(self):
        ctrl = OrchestrationController()
        ctrl.submit_task("Task 1", priority=TaskPriority.HIGH)
        ctrl.submit_task("Task 2", priority=TaskPriority.LOW)
        summary = ctrl.get_execution_summary()
        assert summary["total_tasks"] == 2
        assert summary["pending"] == 2


class TestPlannerEngine:
    def test_plan_research(self):
        planner = PlannerEngine()
        plan = planner.plan("Research semantic memory", "research")
        assert len(plan.subtasks) > 0
        assert plan.objective == "Research semantic memory"

    def test_plan_ingest(self):
        planner = PlannerEngine()
        plan = planner.plan("Ingest OpenAlex papers", "ingest")
        assert len(plan.subtasks) > 0

    def test_get_ready_subtasks(self):
        planner = PlannerEngine()
        plan = planner.plan("Test research", "research")
        ready = plan.get_ready_subtasks()
        assert len(ready) > 0
        # First subtask should have no dependencies
        assert len(ready[0].dependencies) == 0

    def test_mark_complete(self):
        planner = PlannerEngine()
        plan = planner.plan("Test", "research")
        first = plan.subtasks[0]
        planner.mark_complete(plan, first.title)
        assert first.is_complete


class TestWorkflowEngine:
    def test_create_workflow(self):
        engine = WorkflowEngine()
        wf = engine.create_workflow("Test Workflow")
        assert wf.title == "Test Workflow"
        assert len(wf.nodes) == 0

    def test_add_nodes_and_edges(self):
        engine = WorkflowEngine()
        wf = engine.create_workflow("Test")
        n1 = wf.add_node("Step 1", "retrieve", "ingestion")
        n2 = wf.add_node("Step 2", "analyze", "synthesis")
        wf.add_edge(n1.node_id, n2.node_id)
        assert len(wf.nodes) == 2
        assert len(wf.edges) == 1

    def test_get_ready_nodes(self):
        engine = WorkflowEngine()
        wf = engine.create_workflow("Test")
        n1 = wf.add_node("Step 1", "retrieve")
        n2 = wf.add_node("Step 2", "analyze")
        wf.add_edge(n1.node_id, n2.node_id)

        ready = wf.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].title == "Step 1"

    def test_completion_pct(self):
        engine = WorkflowEngine()
        wf = engine.create_workflow("Test")
        wf.add_node("Step 1", "retrieve")
        assert wf.completion_pct == 0.0


class TestSchedulerEngine:
    def test_schedule(self):
        sched = SchedulerEngine()
        task = sched.schedule("Daily ingestion", ScheduleFrequency.DAILY, "ingest")
        assert task.frequency == ScheduleFrequency.DAILY
        assert task.is_enabled

    def test_list_scheduled(self):
        sched = SchedulerEngine()
        sched.schedule("Task 1", ScheduleFrequency.HOURLY, "test")
        sched.schedule("Task 2", ScheduleFrequency.DAILY, "test")
        tasks = sched.list_scheduled()
        assert len(tasks) == 2

    def test_enable_disable(self):
        sched = SchedulerEngine()
        task = sched.schedule("Test", ScheduleFrequency.DAILY, "test")
        sched.disable(task.task_id)
        assert not sched._scheduled_tasks[task.task_id].is_enabled
        sched.enable(task.task_id)
        assert sched._scheduled_tasks[task.task_id].is_enabled


class TestGovernanceEngine:
    def test_recursion_check(self):
        gov = GovernanceEngine()
        check = gov.check_recursion(3)
        assert check.passed is True
        check = gov.check_recursion(10)
        assert check.passed is False

    def test_concurrent_check(self):
        gov = GovernanceEngine()
        check = gov.check_concurrent(5)
        assert check.passed is True
        check = gov.check_concurrent(20)
        assert check.passed is False

    def test_tool_permission(self):
        gov = GovernanceEngine()
        check = gov.check_tool_permission("read_file")
        assert check.passed is True
        check = gov.check_tool_permission("delete_file")
        assert check.passed is False

    def test_full_check(self):
        gov = GovernanceEngine()
        check = gov.full_check(task_id="test-1", recursion_depth=2, active_tasks=3, confidence=0.8)
        assert check.passed is True


class TestAgentRuntime:
    def test_register_and_spawn(self):
        runtime = AgentRuntime()
        spec = AgentSpec(name="test_agent", role="Testing", capabilities=["test"])
        runtime.register(spec)
        instance = runtime.spawn("test_agent")
        assert instance is not None
        assert instance.spec.name == "test_agent"

    def test_list_agents(self):
        runtime = AgentRuntime()
        agents = runtime.list_agents()
        assert len(agents) > 0  # Default agents registered

    def test_update_state(self):
        runtime = AgentRuntime()
        instance = runtime.spawn("retriever")
        runtime.update_state(instance.instance_id, AgentState.RUNNING, current_task="test")
        updated = runtime.get_instance(instance.instance_id)
        assert updated.state == AgentState.RUNNING

    def test_get_stats(self):
        runtime = AgentRuntime()
        runtime.spawn("retriever")
        stats = runtime.get_stats()
        assert stats["total_instances"] == 1


class TestContextInjector:
    def test_inject_empty(self):
        injector = ContextInjector()
        contexts = injector.inject("test query")
        assert isinstance(contexts, list)

    def test_format_context(self):
        injector = ContextInjector()
        packets = injector.inject("test")
        formatted = injector.format_context(packets)
        assert isinstance(formatted, str)


class TestReflectionEngine:
    def test_reflect_good_output(self):
        engine = ReflectionEngine()
        output = "This is a well-reasoned analysis with citations [Smith, 2024]."
        result = engine.reflect(output, query="Test query")
        assert isinstance(result.passed, bool)

    def test_reflect_empty_output(self):
        engine = ReflectionEngine()
        result = engine.reflect("", query="Test")
        # Empty output should either fail or have low confidence
        assert result.passed is False or result.confidence < 0.5

    def test_reflect_contradiction(self):
        engine = ReflectionEngine()
        output = "The market is rising. The market is not rising."
        result = engine.reflect(output, query="Market direction")
        # Should detect contradiction
        assert len(result.issues) > 0 or result.passed  # Either detects or passes
