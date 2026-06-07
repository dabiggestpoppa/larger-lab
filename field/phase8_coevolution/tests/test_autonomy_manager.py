"""Test for autonomy_manager."""
from field.phase8_coevolution.autonomy_manager import AutonomyManagerModule


def test_autonomy_manager_init():
    """Module initializes with default config."""
    mod = AutonomyManagerModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_autonomy_manager_start_stop():
    """Module start/stop toggles running state."""
    mod = AutonomyManagerModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
