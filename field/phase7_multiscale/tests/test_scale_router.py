"""Test for scale_router."""
from field.phase7_multiscale.scale_router import ScaleRouterModule


def test_scale_router_init():
    """Module initializes with default config."""
    mod = ScaleRouterModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_scale_router_start_stop():
    """Module start/stop toggles running state."""
    mod = ScaleRouterModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
