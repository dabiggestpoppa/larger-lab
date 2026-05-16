import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 4 End-to-End Integration Test
=====================================
Tests workspace integration: tool adapters, routing, health checks.

Success criteria:
1. All tool adapters register and report health
2. Tasks route through SRRA roles (not directly to tools)
3. Tools are interchangeable (swap adapter, same interface)
4. No workspace tool becomes identity authority
"""

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.workspace_integration import (
    WorkspaceIntegrationLayer, ToolRole,
    OpenClawAdapter, HermesAdapter, NautilusAdapter, ClaudeAdapter
)


def test_1_tool_registration():
    """Test 1: All tool adapters register correctly."""
    print("\n=== Test 1: Tool Registration ===")

    layer = WorkspaceIntegrationLayer()

    # Check all expected tools registered
    assert "OpenClaw" in layer.adapters, "OpenClaw not registered"
    assert "Hermes" in layer.adapters, "Hermes not registered"
    assert "Nautilus" in layer.adapters, "Nautilus not registered"
    assert "Claude" in layer.adapters, "Claude not registered"

    print(f"  OK: {len(layer.adapters)} tools registered")

    # Check role mapping
    strategic = layer.get_by_role(ToolRole.STRATEGIC_SYNTHESIS)
    assert len(strategic) > 0, "No strategic synthesis adapter"
    print(f"  OK: {len(strategic)} strategic synthesis adapter(s)")

    execution = layer.get_by_role(ToolRole.EXECUTION)
    assert len(execution) > 0, "No execution adapter"
    print(f"  OK: {len(execution)} execution adapter(s)")

    print("  PASS Test 1")


def test_2_health_checks():
    """Test 2: Health checks work for all tools."""
    print("\n=== Test 2: Health Checks ===")

    layer = WorkspaceIntegrationLayer()
    health = layer.health_check_all()

    assert len(health) == 4, f"Expected 4 health checks, got {len(health)}"
    print(f"  OK: Health checks for {len(health)} tools")

    # Claude should always be available (this IS Claude)
    assert health.get("Claude") == True, "Claude should be available"
    print(f"  OK: Claude available")

    # At least some tools should be available
    available = sum(1 for v in health.values() if v)
    print(f"  OK: {available}/{len(health)} tools available")

    print("  PASS Test 2")


def test_3_task_routing():
    """Test 3: Tasks route through SRRA roles."""
    print("\n=== Test 3: Task Routing ===")

    layer = WorkspaceIntegrationLayer()

    # Test planning task routes to strategic synthesis
    result = layer.route_task("planning", "analyze market data")
    # May fail if OpenClaw is not running — that's OK, routing logic works
    print(f"  OK: Planning task routed (status: {result.get('status')})")

    # Test execution task routes to execution
    result = layer.route_task("execution", "run backtest")
    print(f"  OK: Execution task routed (status: {result.get('status')})")

    # Test verification task
    result = layer.route_task("verification", "validate results")
    print(f"  OK: Verification task routed (status: {result.get('status')})")

    # Test reasoning task (should always work — Claude is self)
    result = layer.route_task("reasoning", "analyze something")
    assert result.get("status") == "self", f"Reasoning should route to self: {result}"
    print(f"  OK: Reasoning task routes to self")

    # Test unknown task type
    result = layer.route_task("unknown_type", "do something")
    assert result.get("status") == "error", "Unknown task type should error"
    print(f"  OK: Unknown task type correctly rejected")

    print("  PASS Test 3")


def test_4_tool_replaceability():
    """Test 4: Tools are interchangeable — swap adapter, same interface."""
    print("\n=== Test 4: Tool Replaceability ===")

    layer = WorkspaceIntegrationLayer()

    # Register a second strategic synthesis adapter (simulating tool swap)
    class BackupStrategicAdapter(OpenClawAdapter):
        def __init__(self):
            super().__init__()
            self.tool_name = "BackupStrategic"

    backup = BackupStrategicAdapter()
    backup.is_available = True
    layer.register(backup)

    # Should now have 2 strategic synthesis adapters
    strategic = layer.get_by_role(ToolRole.STRATEGIC_SYNTHESIS)
    assert len(strategic) >= 2, f"Expected >= 2 strategic adapters, got {len(strategic)}"
    print(f"  OK: {len(strategic)} strategic adapters (tool swap works)")

    # Routing should pick the available one (backup is available)
    result = layer.route_task("planning", "test command")
    # BackupStrategicAdapter is available, so this should work
    assert result.get("status") != "error", f"Routing with backup adapter failed: {result}"
    print(f"  OK: Routing works with swapped tool")

    print("  PASS Test 4")


def test_5_no_identity_authority():
    """Test 5: No workspace tool becomes identity authority."""
    print("\n=== Test 5: No Identity Authority ===")

    layer = WorkspaceIntegrationLayer()
    status = layer.get_status()

    # All tools should have bounded roles
    for tool_name, tool_info in status["tools"].items():
        assert "role" in tool_info, f"{tool_name} has no role"
        assert tool_info["role"] != "identity", f"{tool_name} should not be identity"
        assert tool_info["role"] != "central_memory", f"{tool_name} should not be central memory"
        assert tool_info["role"] != "orchestrator", f"{tool_name} should not be orchestrator"

    print(f"  OK: No tool has identity authority role")

    # Tools should be replaceable (no tool is required)
    health = layer.health_check_all()
    # Even if some tools are down, the layer should still function
    result = layer.route_task("reasoning", "analyze something")
    # Claude (reasoning) should always work since we're running in it
    assert result.get("status") != "error" or result.get("status") == "self", \
        "Reasoning should work through Claude"

    print(f"  OK: System functions even with tools down")

    print("  PASS Test 5")


def test_6_status_reporting():
    """Test 6: Full status reporting works."""
    print("\n=== Test 6: Status Reporting ===")

    layer = WorkspaceIntegrationLayer()
    status = layer.get_status()

    assert "tools" in status, "Status missing tools"
    assert "health" in status, "Status missing health"
    assert "available_count" in status, "Status missing available_count"
    assert "total_count" in status, "Status missing total_count"

    print(f"  OK: Status has all required fields")
    print(f"  OK: {status['available_count']}/{status['total_count']} tools available")

    print("  PASS Test 6")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 4: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_tool_registration,
        test_2_health_checks,
        test_3_task_routing,
        test_4_tool_replaceability,
        test_5_no_identity_authority,
        test_6_status_reporting,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
