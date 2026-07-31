"""Test for weekly_engine."""
from field.phase7_multiscale.weekly_engine import WeeklyEngineModule


def test_weekly_engine_init():
    """Module initializes with default config."""
    mod = WeeklyEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_weekly_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = WeeklyEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
