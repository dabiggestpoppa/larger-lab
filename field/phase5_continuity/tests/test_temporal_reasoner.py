"""Test for temporal_reasoner."""
from field.phase5_continuity.temporal_reasoner import TemporalReasonerModule


def test_temporal_reasoner_init():
    """Module initializes with default config."""
    mod = TemporalReasonerModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_temporal_reasoner_start_stop():
    """Module start/stop toggles running state."""
    mod = TemporalReasonerModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
