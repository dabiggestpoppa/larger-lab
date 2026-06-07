"""Test for trust_calibration."""
from field.phase8_coevolution.trust_calibration import TrustCalibrationModule


def test_trust_calibration_init():
    """Module initializes with default config."""
    mod = TrustCalibrationModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_trust_calibration_start_stop():
    """Module start/stop toggles running state."""
    mod = TrustCalibrationModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
