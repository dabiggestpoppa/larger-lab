"""Test for field_drift_correction."""
from field.phase9_emergence.field_drift_correction import FieldDriftCorrectionModule


def test_field_drift_correction_init():
    """Module initializes with default config."""
    mod = FieldDriftCorrectionModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_field_drift_correction_start_stop():
    """Module start/stop toggles running state."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
