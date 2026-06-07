"""Test for bar_engine."""
from field.phase7_multiscale.bar_engine import BarEngineModule


def test_bar_engine_init():
    """Module initializes with default config."""
    mod = BarEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_bar_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = BarEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
