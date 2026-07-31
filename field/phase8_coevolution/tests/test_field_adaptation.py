"""Test for field_adaptation."""
from field.phase8_coevolution.field_adaptation import FieldAdaptationModule


def test_field_adaptation_init():
    """Module initializes with default config."""
    mod = FieldAdaptationModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_field_adaptation_start_stop():
    """Module start/stop toggles running state."""
    mod = FieldAdaptationModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
