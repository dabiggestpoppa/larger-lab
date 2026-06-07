"""Test for instrumentation_bus."""
from field.phase4_instrumentation.instrumentation_bus import InstrumentationBusModule


def test_instrumentation_bus_init():
    """Module initializes with default config."""
    mod = InstrumentationBusModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_instrumentation_bus_start_stop():
    """Module start/stop toggles running state."""
    mod = InstrumentationBusModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
