"""Test for long_term_memory."""
from field.phase5_continuity.long_term_memory import LongTermMemoryModule


def test_long_term_memory_init():
    """Module initializes with default config."""
    mod = LongTermMemoryModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_long_term_memory_start_stop():
    """Module start/stop toggles running state."""
    mod = LongTermMemoryModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
