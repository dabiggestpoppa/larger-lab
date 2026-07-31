"""Test for self_model."""
from field.phase9_emergence.self_model import SelfModelModule


def test_self_model_init():
    """Module initializes with default config."""
    mod = SelfModelModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_self_model_start_stop():
    """Module start/stop toggles running state."""
    mod = SelfModelModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
