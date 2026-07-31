"""Test for memory_consolidation."""
from field.phase5_continuity.memory_consolidation import MemoryConsolidationModule


def test_memory_consolidation_init():
    """Module initializes with default config."""
    mod = MemoryConsolidationModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_memory_consolidation_start_stop():
    """Module start/stop toggles running state."""
    mod = MemoryConsolidationModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
