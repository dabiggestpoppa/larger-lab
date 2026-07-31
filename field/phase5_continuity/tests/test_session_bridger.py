"""Test for session_bridger."""
from field.phase5_continuity.session_bridger import SessionBridgerModule


def test_session_bridger_init():
    """Module initializes with default config."""
    mod = SessionBridgerModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_session_bridger_start_stop():
    """Module start/stop toggles running state."""
    mod = SessionBridgerModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
