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


def test_scale_bridge_register_translation():
    """Register and retrieve scale translations."""
    mod = ScaleBridgeModule()
    mod.start()
    mod.register_translation("tick", "bar", "sum", field="volume")
    mod.register_translation("bar", "session", "aggregate")
    assert mod.get_translation("tick", "bar") is not None
    assert mod.get_translation("tick", "bar").strategy == "sum"
    assert mod.get_translation("bar", "session").strategy == "aggregate"
    assert mod.get_translation("tick", "daily") is None
    mod.stop()


def test_scale_bridge_translate():
    """Translate data between scales."""
    mod = ScaleBridgeModule()
    mod.start()
    mod.register_translation("tick", "bar", "sum")
    result = mod.translate("tick", "bar", [1, 2, 3, 4])
    assert result == 10
    mod.stop()
