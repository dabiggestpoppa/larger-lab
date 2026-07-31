"""Test for coevolution_tracker."""
from field.phase8_coevolution.coevolution_tracker import CoevolutionTrackerModule


def test_coevolution_tracker_init():
    """Module initializes with default config."""
    mod = CoevolutionTrackerModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_coevolution_tracker_start_stop():
    """Module start/stop toggles running state."""
    mod = CoevolutionTrackerModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
