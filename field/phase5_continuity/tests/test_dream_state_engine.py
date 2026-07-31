"""Test for dream_state_engine."""
from field.phase5_continuity.dream_state_engine import DreamStateEngineModule


def test_dream_state_engine_init():
    """Module initializes with default config."""
    mod = DreamStateEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_dream_state_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = DreamStateEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
