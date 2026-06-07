"""Test for suggestion_engine."""
from field.phase8_coevolution.suggestion_engine import SuggestionEngineModule


def test_suggestion_engine_init():
    """Module initializes with default config."""
    mod = SuggestionEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_suggestion_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = SuggestionEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
