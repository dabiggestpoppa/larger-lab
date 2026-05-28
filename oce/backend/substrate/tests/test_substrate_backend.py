"""
O-6 Substrate Backend Unit Tests
=================================

Tests for all 8 core substrate modules:
1. local_runtime
2. permission_layer
3. execution_sandbox
4. filesystem_awareness
5. terminal_orchestrator
6. process_observer
7. environment_model
8. recovery_controller

Plus API contract tests for substrate_api endpoints.
"""

import asyncio
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure OCE backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def async_test(fn):
    """Decorator to mark async test functions for pytest."""
    return pytest.mark.asyncio(fn)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOCAL RUNTIME TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalRuntime:
    """Tests for local_runtime module."""

    def setup_method(self):
        """Reset singleton before each test."""
        from oce.backend.substrate import local_runtime as lr
        lr.LocalRuntime._instance = None

    def test_runtime_state_defaults(self):
        """RuntimeState should have sensible defaults."""
        from oce.backend.substrate.local_runtime import RuntimeState
        state = RuntimeState()
        assert state.cpu_percent == 0.0
        assert state.memory_percent == 0.0
        assert state.disk_percent == 0.0
        assert state.active_processes == 0
        assert state.active_sandboxes == 0
        assert state.uptime_seconds == 0
        assert state.timestamp != ""

    def test_singleton_pattern(self):
        """LocalRuntime should be a singleton."""
        from oce.backend.substrate.local_runtime import LocalRuntime, get_local_runtime
        r1 = get_local_runtime()
        r2 = get_local_runtime()
        assert r1 is r2

    def test_get_state_returns_dict(self):
        """get_state() should return a dict with expected keys."""
        from oce.backend.substrate.local_runtime import get_local_runtime
        rt = get_local_runtime()
        state = rt.get_state()
        assert isinstance(state, dict)
        assert "runtime" in state
        assert "initialized" in state

    @async_test
    async def test_initialize_idempotent(self):
        """initialize() should be idempotent."""
        from oce.backend.substrate.local_runtime import get_local_runtime
        rt = get_local_runtime()
        await rt.initialize()
        await rt.initialize()  # Should not raise
        assert rt._initialized is True

    @async_test
    async def test_execute_task_unknown_type_raises(self):
        """execute_task() should raise ValueError for unknown task types."""
        from oce.backend.substrate.local_runtime import get_local_runtime
        rt = get_local_runtime()
        with pytest.raises(ValueError):
            await rt.execute_task("unknown_type", {})

    def teardown_method(self):
        from oce.backend.substrate import local_runtime as lr
        lr.LocalRuntime._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PERMISSION LAYER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPermissionLayer:
    """Tests for permission_layer module."""

    def setup_method(self):
        from oce.backend.substrate import permission_layer as pl
        pl.PermissionLayer._instance = None

    def test_default_rules_loaded(self):
        """Permission layer should load default rules on init."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        assert len(pl.rules) > 0

    def test_check_permission_filesystem_read(self):
        """Workspace reads should be permitted."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        workspace = str(Path.cwd())
        result = pl.check_permission("filesystem", "read", workspace)
        assert result is True

    def test_check_permission_unknown_deny(self):
        """Unknown operations should be denied by default."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        result = pl.check_permission("filesystem", "delete", "/etc/passwd")
        assert result is False

    def test_validate_filesystem_path_in_workspace(self):
        """Paths within workspace should be valid."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        workspace = str(Path.cwd())
        assert pl.validate_filesystem_path(workspace) is True

    def test_validate_filesystem_path_outside_workspace(self):
        """Paths outside workspace should be invalid."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        assert pl.validate_filesystem_path("/etc/passwd") is False

    def test_validate_command_safe(self):
        """Safe commands should pass validation."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        assert pl.validate_command("git status") is True
        assert pl.validate_command("python -m pytest") is True

    def test_validate_command_dangerous(self):
        """Dangerous commands should be blocked."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        assert pl.validate_command("rm -rf /") is False
        assert pl.validate_command("sudo chmod 777 /") is False

    def test_get_rules_returns_dicts(self):
        """get_rules() should return list of dicts."""
        from oce.backend.substrate.permission_layer import get_permission_layer
        pl = get_permission_layer()
        rules = pl.get_rules()
        assert isinstance(rules, list)
        for r in rules:
            assert "scope" in r
            assert "action" in r
            assert "resource" in r
            assert "allowed" in r

    def teardown_method(self):
        from oce.backend.substrate import permission_layer as pl
        pl.PermissionLayer._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. EXECUTION SANDBOX TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionSandbox:
    """Tests for execution_sandbox module."""

    def setup_method(self):
        from oce.backend.substrate import execution_sandbox as es
        es.ExecutionSandbox._instance = None

    def test_default_sandboxes_created(self):
        """Default sandboxes should be created on init."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        assert "dev" in sb.sandboxes
        assert "orchestration" in sb.sandboxes
        assert "testing" in sb.sandboxes
        assert "replay" in sb.sandboxes

    def test_get_sandbox_by_id(self):
        """Should retrieve sandbox by ID."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        dev = sb.get_sandbox("dev")
        assert dev is not None
        assert dev.id == "dev"
        assert dev.name == "Development Sandbox"

    def test_enter_and_exit_sandbox(self):
        """Enter and exit should track active tasks."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        result = sb.enter("dev")
        assert result is True
        assert sb.sandboxes["dev"].active_tasks == 1
        sb.exit("dev")
        assert sb.sandboxes["dev"].active_tasks == 0

    def test_enter_at_capacity_fails(self):
        """Entering at-capacity sandbox should return False."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        replay = sb.sandboxes["replay"]
        replay.active_tasks = replay.max_tasks  # Fill it up
        result = sb.enter("replay")
        assert result is False

    def test_create_sandbox(self):
        """Should create a new sandbox."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox, SandboxType
        sb = get_execution_sandbox()
        new_sb = sb.create_sandbox("Custom", SandboxType.DEV, max_tasks=7)
        assert new_sb.id in sb.sandboxes
        assert new_sb.name == "Custom"
        assert new_sb.max_tasks == 7

    def test_get_status_returns_all_sandboxes(self):
        """get_status() should return all sandboxes."""
        from oce.backend.substrate.execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        status = sb.get_status()
        assert "sandboxes" in status
        assert "total_active_tasks" in status
        assert len(status["sandboxes"]) >= 4

    def teardown_method(self):
        from oce.backend.substrate import execution_sandbox as es
        es.ExecutionSandbox._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FILESYSTEM AWARENESS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilesystemAwareness:
    """Tests for filesystem_awareness module."""

    def setup_method(self):
        from oce.backend.substrate import filesystem_awareness as fa
        fa.FilesystemAwareness._instance = None

    def test_init_with_default_workspace(self):
        """Should initialize with cwd as default workspace."""
        from oce.backend.substrate.filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        assert fs.workspace_root == Path.cwd()

    def test_init_with_custom_workspace(self):
        """Should accept custom workspace root."""
        from oce.backend.substrate.filesystem_awareness import FilesystemAwareness
        fs = FilesystemAwareness(workspace_root=str(Path.cwd()))
        assert fs.workspace_root == Path.cwd()

    def test_get_workspace_topology(self):
        """get_workspace_topology() should return nodes and edges."""
        from oce.backend.substrate.filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        topo = fs.get_workspace_topology()
        assert "nodes" in topo
        assert "edges" in topo
        assert isinstance(topo["nodes"], list)
        assert isinstance(topo["edges"], list)

    @async_test
    async def test_execute_unknown_operation_raises(self):
        """execute() should raise ValueError for unknown operations."""
        from oce.backend.substrate.filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        with pytest.raises(ValueError):
            await fs.execute({"operation": "nonexistent"})

    @async_test
    async def test_list_directory(self):
        """Should list directory contents."""
        from oce.backend.substrate.filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        result = await fs._list_directory(str(Path.cwd()))
        assert "items" in result
        assert isinstance(result["items"], list)

    @async_test
    async def test_list_directory_outside_workspace(self):
        """Should reject paths outside workspace."""
        from oce.backend.substrate.filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        result = await fs._list_directory("/etc")
        assert "error" in result

    def teardown_method(self):
        from oce.backend.substrate import filesystem_awareness as fa
        fa.FilesystemAwareness._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TERMINAL ORCHESTRATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTerminalOrchestrator:
    """Tests for terminal_orchestrator module."""

    def setup_method(self):
        from oce.backend.substrate import terminal_orchestrator as to
        to.TerminalOrchestrator._instance = None

    def test_singleton(self):
        """TerminalOrchestrator should be a singleton."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        t1 = get_terminal_orchestrator()
        t2 = get_terminal_orchestrator()
        assert t1 is t2

    def test_get_active_executions_empty(self):
        """Active executions should start empty."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        result = to.get_active_executions()
        assert isinstance(result["executions"], list)
        assert len(result["executions"]) == 0

    @async_test
    async def test_execute_blocked_command(self):
        """Blocked commands should return error."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        result = await to.execute("rm -rf /")
        assert "error" in result

    @async_test
    async def test_execute_permitted_command(self):
        """Permitted commands should execute (echo is safe)."""
        from oce.backend.substrate.terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        result = await to.execute("echo hello")
        assert "status" in result
        assert result["status"] in ("completed", "timed_out")

    def teardown_method(self):
        from oce.backend.substrate import terminal_orchestrator as to
        to.TerminalOrchestrator._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PROCESS OBSERVER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcessObserver:
    """Tests for process_observer module."""

    def setup_method(self):
        from oce.backend.substrate import process_observer as po
        po.ProcessObserver._instance = None

    def test_singleton(self):
        """ProcessObserver should be a singleton."""
        from oce.backend.substrate.process_observer import get_process_observer
        p1 = get_process_observer()
        p2 = get_process_observer()
        assert p1 is p2

    def test_scan_processes_returns_list(self):
        """scan_processes() should return a list of ProcessInfo."""
        from oce.backend.substrate.process_observer import get_process_observer
        po = get_process_observer()
        procs = po.scan_processes()
        assert isinstance(procs, list)

    def test_get_active_processes_returns_dicts(self):
        """get_active_processes() should return list of dicts with expected keys."""
        from oce.backend.substrate.process_observer import get_process_observer
        po = get_process_observer()
        # Scan first to populate monitored_processes
        po.scan_processes()
        active = po.get_active_processes()
        assert isinstance(active, list)
        for p in active:
            assert "pid" in p
            assert "name" in p
            assert "status" in p
            assert "cpu" in p
            assert "memory" in p

    def test_detect_hung_processes(self):
        """detect_hung_processes() should return list of PIDs."""
        from oce.backend.substrate.process_observer import get_process_observer, ProcessInfo
        po = get_process_observer()
        # Manually add a "hung" process
        po._monitored_processes[99999] = ProcessInfo(
            pid=99999, name="test_hung", status="running",
            cpu_percent=0, memory_percent=0, runtime_seconds=9999
        )
        hung = po.detect_hung_processes()
        assert 99999 in hung

    @async_test
    async def test_execute_list_operation(self):
        """execute('list') should return processes."""
        from oce.backend.substrate.process_observer import get_process_observer
        po = get_process_observer()
        result = await po.execute({"operation": "list"})
        assert "processes" in result

    @async_test
    async def test_execute_unknown_operation(self):
        """execute() with unknown operation should return error."""
        from oce.backend.substrate.process_observer import get_process_observer
        po = get_process_observer()
        result = await po.execute({"operation": "fly"})
        assert "error" in result

    def teardown_method(self):
        from oce.backend.substrate import process_observer as po
        po.ProcessObserver._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ENVIRONMENT MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnvironmentModel:
    """Tests for environment_model module."""

    def setup_method(self):
        from oce.backend.substrate import environment_model as em
        em.EnvironmentModel._instance = None

    def test_singleton(self):
        """EnvironmentModel should be a singleton."""
        from oce.backend.substrate.environment_model import get_environment_model
        e1 = get_environment_model()
        e2 = get_environment_model()
        assert e1 is e2

    def test_get_current_environment_returns_dict(self):
        """get_current_environment() should return dict with expected keys."""
        from oce.backend.substrate.environment_model import get_environment_model
        em = get_environment_model()
        result = em.get_current_environment()
        assert isinstance(result, dict)
        assert "workspace" in result
        assert "projects" in result
        assert "system" in result
        assert "timestamp" in result

    def test_set_active_project(self):
        """set_active_project() should add to list."""
        from oce.backend.substrate.environment_model import get_environment_model
        em = get_environment_model()
        em.set_active_project("/test/project")
        assert "/test/project" in em._active_projects

    def test_set_active_project_no_duplicates(self):
        """set_active_project() should not add duplicates."""
        from oce.backend.substrate.environment_model import get_environment_model
        em = get_environment_model()
        em._active_projects = []
        em.set_active_project("/test/project")
        em.set_active_project("/test/project")
        assert em._active_projects.count("/test/project") == 1

    def test_set_active_workflow(self):
        """set_active_workflow() should add to list."""
        from oce.backend.substrate.environment_model import get_environment_model
        em = get_environment_model()
        em.set_active_workflow("wf-test")
        assert "wf-test" in em._active_workflows

    def teardown_method(self):
        from oce.backend.substrate import environment_model as em
        em.EnvironmentModel._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 8. RECOVERY CONTROLLER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecoveryController:
    """Tests for recovery_controller module."""

    def setup_method(self):
        from oce.backend.substrate import recovery_controller as rc
        rc.RecoveryController._instance = None

    def test_singleton(self):
        """RecoveryController should be a singleton."""
        from oce.backend.substrate.recovery_controller import get_recovery_controller
        r1 = get_recovery_controller()
        r2 = get_recovery_controller()
        assert r1 is r2

    def test_recovery_action_enum(self):
        """RecoveryAction enum should have expected values."""
        from oce.backend.substrate.recovery_controller import RecoveryAction
        assert RecoveryAction.TERMINATE_HUNG == "terminate_hung"
        assert RecoveryAction.RESTART_OBSERVER == "restart_observer"
        assert RecoveryAction.RESTORE_STATE == "restore_state"
        assert RecoveryAction.REDUCE_ENTROPY == "reduce_entropy"

    @async_test
    async def test_recover_terminate_hung(self):
        """recover(TERMINATE_HUNG) should return a RecoveryEvent."""
        from oce.backend.substrate.recovery_controller import (
            get_recovery_controller, RecoveryAction
        )
        rc = get_recovery_controller()
        event = await rc.recover(RecoveryAction.TERMINATE_HUNG, "all")
        assert event.action == RecoveryAction.TERMINATE_HUNG
        assert event.target == "all"
        assert event.status in ("stable", "failed")
        assert event.duration_seconds >= 0

    @async_test
    async def test_recover_restart_observer(self):
        """recover(RESTART_OBSERVER) should return a RecoveryEvent."""
        from oce.backend.substrate.recovery_controller import (
            get_recovery_controller, RecoveryAction
        )
        rc = get_recovery_controller()
        event = await rc.recover(RecoveryAction.RESTART_OBSERVER, "default")
        assert event.action == RecoveryAction.RESTART_OBSERVER
        assert event.status in ("stable", "failed")

    @async_test
    async def test_recover_restore_state(self):
        """recover(RESTORE_STATE) should return a RecoveryEvent."""
        from oce.backend.substrate.recovery_controller import (
            get_recovery_controller, RecoveryAction
        )
        rc = get_recovery_controller()
        event = await rc.recover(RecoveryAction.RESTORE_STATE, "continuity")
        assert event.action == RecoveryAction.RESTORE_STATE
        assert event.status in ("stable", "failed")

    @async_test
    async def test_recover_reduce_entropy(self):
        """recover(REDUCE_ENTROPY) should return a RecoveryEvent."""
        from oce.backend.substrate.recovery_controller import (
            get_recovery_controller, RecoveryAction
        )
        rc = get_recovery_controller()
        event = await rc.recover(RecoveryAction.REDUCE_ENTROPY, "cascade_1")
        assert event.action == RecoveryAction.REDUCE_ENTROPY
        assert event.status in ("stable", "failed")

    def test_get_recovery_history(self):
        """get_recovery_history() should return a list."""
        from oce.backend.substrate.recovery_controller import get_recovery_controller
        rc = get_recovery_controller()
        history = rc.get_recovery_history()
        assert isinstance(history, list)

    def test_get_status(self):
        """get_status() should return dict with expected keys."""
        from oce.backend.substrate.recovery_controller import get_recovery_controller
        rc = get_recovery_controller()
        status = rc.get_status()
        assert "total_events" in status
        assert "recent_events" in status
        assert "last_status" in status

    def test_recovery_event_stored(self):
        """Recovery events should be stored and retrievable."""
        from oce.backend.substrate.recovery_controller import get_recovery_controller
        rc = get_recovery_controller()
        initial_count = len(rc.events)
        # Manually add event
        from oce.backend.substrate.recovery_controller import RecoveryEvent, RecoveryAction
        rc.events.append(RecoveryEvent(
            id="test-1", action=RecoveryAction.TERMINATE_HUNG,
            target="test", status="stable", timestamp="2026-01-01T00:00:00Z"
        ))
        assert len(rc.events) == initial_count + 1

    def teardown_method(self):
        from oce.backend.substrate import recovery_controller as rc
        rc.RecoveryController._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# 9. API CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSubstrateAPI:
    """Tests for substrate_api endpoint registration and response shapes."""

    def test_register_substrate_endpoints(self):
        """register_substrate_endpoints should not raise."""
        from fastapi import FastAPI
        from oce.backend.substrate_api import register_substrate_endpoints
        app = FastAPI()
        register_substrate_endpoints(app)
        # Verify routes are registered
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/substrate/state" in routes
        assert "/api/substrate/processes" in routes
        assert "/api/substrate/filesystem" in routes
        assert "/api/substrate/sandbox" in routes
        assert "/api/substrate/machine-graph" in routes
        assert "/api/substrate/environment" in routes
        assert "/api/substrate/inspector" in routes

    def test_all_routes_registered(self):
        """All 10 substrate routes should be registered."""
        from fastapi import FastAPI
        from oce.backend.substrate_api import register_substrate_endpoints
        app = FastAPI()
        register_substrate_endpoints(app)
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        expected = [
            "/api/substrate/state",
            "/api/substrate/processes",
            "/api/substrate/filesystem",
            "/api/substrate/execute",
            "/api/substrate/terminal",
            "/api/substrate/sandbox",
            "/api/substrate/recovery",
            "/api/substrate/machine-graph",
            "/api/substrate/environment",
            "/api/substrate/inspector",
        ]
        for route in expected:
            assert route in routes, f"Missing route: {route}"

    def test_request_models(self):
        """Request models should have correct fields."""
        from oce.backend.substrate_api import ExecuteRequest, TerminalRequest, RecoveryRequest
        er = ExecuteRequest(task_type="terminal")
        assert er.task_type == "terminal"
        assert er.payload == {}
        assert er.sandbox_id is None

        tr = TerminalRequest(command="echo hello")
        assert tr.command == "echo hello"

        rr = RecoveryRequest(action="terminate_hung", target="all")
        assert rr.action == "terminate_hung"
        assert rr.target == "all"
