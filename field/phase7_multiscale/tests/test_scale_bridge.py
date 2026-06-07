"""Test for scale_bridge."""
from field.phase7_multiscale.scale_bridge import ScaleBridgeModule


def test_scale_bridge_init():
    """Module initializes with default config."""
    mod = ScaleBridgeModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_scale_bridge_start_stop():
    """Module start/stop toggles running state."""
    mod = ScaleBridgeModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
