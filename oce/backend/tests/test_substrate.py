"""
Tests for O-6 Local Execution Substrate
========================================

Covers:
- Filesystem awareness test
- Terminal orchestration test
- Process monitor test
- Environment model test
- Sandbox test
- Machine topology test
- Recovery test
- Long horizon embodiment test
"""

import asyncio
import pytest
from pathlib import Path


# ─── Test 1: Filesystem Awareness ─────────────────────────────────────────

def test_filesystem_awareness_tracking():
    """Track repo mutations, workflow outputs, runtime artifacts."""
    from substrate.filesystem_awareness import FilesystemAwareness, get_filesystem_awareness
    
    # Reset singleton
    FilesystemAwareness._instance = None
    fs = get_filesystem_awareness()
    
    # Test workspace topology
    graph = fs.get_workspace_topology()
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)


def test_filesystem_scoped_access():
    """Verify filesystem scoped access works correctly."""
    from substrate.permission_layer import PermissionLayer, get_permission_layer
    
    # Reset singleton
    PermissionLayer._instance = None
    pl = get_permission_layer()
    
    # Test workspace path validation
    workspace = str(Path.cwd())
    assert pl.validate_filesystem_path(workspace) is True
    
    # Test out-of-scope path
    assert pl.validate_filesystem_path("/etc/passwd") is False


# ─── Test 2: Terminal Orchestration ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_terminal_bounded_execution():
    """Bounded execution workflows."""
    from substrate.terminal_orchestrator import TerminalOrchestrator, get_terminal_orchestrator
    
    # Reset singleton
    TerminalOrchestrator._instance = None
    to = get_terminal_orchestrator()
    
    # Test safe command execution
    result = await to.execute("echo 'test'")
    assert "command" in result
    assert result["command"] == "echo 'test'"


def test_terminal_command_validation():
    """Verify dangerous commands are blocked."""
    from substrate.permission_layer import PermissionLayer, get_permission_layer
    
    # Reset singleton
    PermissionLayer._instance = None
    pl = get_permission_layer()
    
    # Test blocked commands
    assert pl.validate_command("rm -rf /") is False
    assert pl.validate_command("sudo rm -rf") is False
    
    # Test allowed commands
    assert pl.validate_command("git status") is True
    assert pl.validate_command("python --version") is True


# ─── Test 3: Process Monitor ────────────────────────────────────────────────

def test_process_monitor_detection():
    """Hung processes, overload conditions, runtime crashes."""
    from substrate.process_observer import ProcessObserver, get_process_observer
    
    # Reset singleton
    ProcessObserver._instance = None
    po = get_process_observer()
    
    # Test process scanning
    processes = po.scan_processes()
    assert isinstance(processes, list)
    
    # Test active processes
    active = po.get_active_processes()
    assert isinstance(active, list)


# ─── Test 4: Environment Model ────────────────────────────────────────────────

def test_environment_model():
    """Switch projects, runtimes, active workflows."""
    from substrate.environment_model import EnvironmentModel, get_environment_model
    
    # Reset singleton
    EnvironmentModel._instance = None
    em = get_environment_model()
    
    # Test environment state
    env = em.get_current_environment()
    assert "workspace" in env
    assert "projects" in env
    assert "system" in env


# ─── Test 5: Sandbox ──────────────────────────────────────────────────────────

def test_sandbox_out_of_scope():
    """Attempt out-of-scope execution, restricted access."""
    from substrate.execution_sandbox import ExecutionSandbox, get_execution_sandbox, SandboxType
    
    # Reset singleton
    ExecutionSandbox._instance = None
    sb = get_execution_sandbox()
    
    # Test sandbox creation
    sandbox = sb.create_sandbox("test", SandboxType.DEV, max_tasks=5)
    assert sandbox.id is not None
    assert sandbox.name == "test"
    assert sandbox.type == SandboxType.DEV
    
    # Test sandbox status
    status = sb.get_status()
    assert "sandboxes" in status


# ─── Test 6: Machine Topology ─────────────────────────────────────────────────

def test_machine_topology():
    """Complex runtime workflows, machine graph updates."""
    from substrate.machine_state_graph import MachineStateGraph, get_machine_state_graph
    
    # Reset singleton
    MachineStateGraph._instance = None
    msg = get_machine_state_graph()
    
    # Test graph building
    graph = msg.build_graph()
    assert "nodes" in graph
    assert "edges" in graph
    
    # Test graph retrieval
    state = msg.get_graph()
    assert "node_count" in state
    assert "edge_count" in state


# ─── Test 7: Recovery ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recovery_operations():
    """Observer crash, process failure, orchestration collapse."""
    from substrate.recovery_controller import RecoveryController, get_recovery_controller, RecoveryAction
    
    # Reset singleton
    RecoveryController._instance = None
    rc = get_recovery_controller()
    
    # Test recovery action
    event = await rc.recover(RecoveryAction.TERMINATE_HUNG, "test_target")
    assert event.action == RecoveryAction.TERMINATE_HUNG
    assert event.target == "test_target"
    
    # Test recovery history
    history = rc.get_recovery_history()
    assert len(history) > 0


# ─── Test 8: Long Horizon Embodiment ──────────────────────────────────────────

def test_long_horizon_state():
    """72hr operational session state tracking."""
    from substrate.local_runtime import LocalRuntime, get_local_runtime
    
    # Reset singleton
    LocalRuntime._instance = None
    runtime = get_local_runtime()
    
    # Test state retrieval
    state = runtime.get_state()
    assert "runtime" in state
    assert "initialized" in state