"""Test for session_engine."""
from field.phase7_multiscale.session_engine import SessionEngineModule


def test_session_engine_init():
    """Module initializes with default config."""
    mod = SessionEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_session_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = SessionEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
