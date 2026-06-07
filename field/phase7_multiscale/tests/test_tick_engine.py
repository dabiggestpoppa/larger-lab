"""Test for tick_engine."""
from field.phase7_multiscale.tick_engine import TickEngineModule


def test_tick_engine_init():
    """Module initializes with default config."""
    mod = TickEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_tick_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = TickEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
