"""Test for operator_profiles."""
from field.phase8_coevolution.operator_profiles import OperatorProfilesModule


def test_operator_profiles_init():
    """Module initializes with default config."""
    mod = OperatorProfilesModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_operator_profiles_start_stop():
    """Module start/stop toggles running state."""
    mod = OperatorProfilesModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
