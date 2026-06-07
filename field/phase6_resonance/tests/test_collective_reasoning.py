"""Test for collective_reasoning."""
from field.phase6_resonance.collective_reasoning import CollectiveReasoningModule


def test_collective_reasoning_init():
    """Module initializes with default config."""
    mod = CollectiveReasoningModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_collective_reasoning_start_stop():
    """Module start/stop toggles running state."""
    mod = CollectiveReasoningModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
