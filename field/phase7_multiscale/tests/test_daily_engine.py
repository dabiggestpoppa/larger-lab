"""Test for daily_engine."""
from field.phase7_multiscale.daily_engine import DailyEngineModule


def test_daily_engine_init():
    """Module initializes with default config."""
    mod = DailyEngineModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_daily_engine_start_stop():
    """Module start/stop toggles running state."""
    mod = DailyEngineModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
