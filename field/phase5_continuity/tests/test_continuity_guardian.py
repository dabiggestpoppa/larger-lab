"""Test for continuity_guardian."""
from field.phase5_continuity.continuity_guardian import ContinuityGuardianModule


def test_continuity_guardian_init():
    """Module initializes with default config."""
    mod = ContinuityGuardianModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_continuity_guardian_start_stop():
    """Module start/stop toggles running state."""
    mod = ContinuityGuardianModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
