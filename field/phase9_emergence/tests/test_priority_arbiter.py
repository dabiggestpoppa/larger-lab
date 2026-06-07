"""Test for priority_arbiter."""
from field.phase9_emergence.priority_arbiter import PriorityArbiterModule


def test_priority_arbiter_init():
    """Module initializes with default config."""
    mod = PriorityArbiterModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_priority_arbiter_start_stop():
    """Module start/stop toggles running state."""
    mod = PriorityArbiterModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
