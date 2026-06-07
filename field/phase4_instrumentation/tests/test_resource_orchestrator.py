"""Test for resource_orchestrator."""
from field.phase4_instrumentation.resource_orchestrator import ResourceOrchestratorModule


def test_resource_orchestrator_init():
    """Module initializes with default config."""
    mod = ResourceOrchestratorModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_resource_orchestrator_start_stop():
    """Module start/stop toggles running state."""
    mod = ResourceOrchestratorModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
