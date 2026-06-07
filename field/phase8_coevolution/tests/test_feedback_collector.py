"""Test for feedback_collector."""
from field.phase8_coevolution.feedback_collector import FeedbackCollectorModule


def test_feedback_collector_init():
    """Module initializes with default config."""
    mod = FeedbackCollectorModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_feedback_collector_start_stop():
    """Module start/stop toggles running state."""
    mod = FeedbackCollectorModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
