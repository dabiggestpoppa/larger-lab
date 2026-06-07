"""Test for emergent_insight_detector."""
from field.phase6_resonance.emergent_insight_detector import EmergentInsightDetectorModule


def test_emergent_insight_detector_init():
    """Module initializes with default config."""
    mod = EmergentInsightDetectorModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_emergent_insight_detector_start_stop():
    """Module start/stop toggles running state."""
    mod = EmergentInsightDetectorModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
