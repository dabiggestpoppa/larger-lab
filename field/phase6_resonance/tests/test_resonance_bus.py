"""Test for resonance_bus."""
from field.phase6_resonance.resonance_bus import ResonanceBusModule


def test_resonance_bus_init():
    """Module initializes with default config."""
    mod = ResonanceBusModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_resonance_bus_start_stop():
    """Module start/stop toggles running state."""
    mod = ResonanceBusModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
