"""Test for sovereign_dashboard."""
from field.phase4_instrumentation.sovereign_dashboard import SovereignDashboardModule


def test_sovereign_dashboard_init():
    """Module initializes with default config."""
    mod = SovereignDashboardModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_sovereign_dashboard_start_stop():
    """Module start/stop toggles running state."""
    mod = SovereignDashboardModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
