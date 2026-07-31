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


def test_register_region():
    """Registering a region sets baseline and initial offset."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    state = mod.register_region("test_region", baseline_value=1.0)
    assert state.region_id == "test_region"
    assert state.baseline_value == 1.0
    assert state.current_offset == 0.0
    assert state.drift_detected is False
    mod.stop()


def test_update_drift_no_drift():
    """Small deviation does not trigger drift."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=1.0)
    state = mod.update_drift("test_region", observed_value=1.02)
    assert state.drift_detected is False
    assert abs(state.current_offset) < 0.1
    mod.stop()


def test_update_drift_detected():
    """Large deviation triggers drift detection."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=1.0)
    state = mod.update_drift("test_region", observed_value=1.5)
    assert state.drift_detected is True
    mod.stop()


def test_correct_drift():
    """Correction returns an offset to compensate for drift."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=1.0)
    mod.update_drift("test_region", observed_value=1.5)
    correction = mod.correct_drift("test_region")
    assert correction is not None
    assert correction < 0  # negative correction to bring back to baseline
    mod.stop()


def test_get_drift_report():
    """Drift report summarizes all regions."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("r1", baseline_value=1.0)
    mod.register_region("r2", baseline_value=2.0)
    mod.update_drift("r1", observed_value=1.5)
    report = mod.get_drift_report()
    assert report["total_regions"] == 2
    assert report["drifting_regions"] == 1
    mod.stop()


def test_get_region_state():
    """Get state for a specific region."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=5.0)
    state = mod.get_region_state("test_region")
    assert state is not None
    assert state.baseline_value == 5.0
    mod.stop()


def test_get_region_state_missing():
    """Get state for unregistered region returns None."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    assert mod.get_region_state("nonexistent") is None
    mod.stop()


def test_drift_history():
    """Drift history tracks updates."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=1.0)
    mod.update_drift("test_region", observed_value=1.1)
    mod.update_drift("test_region", observed_value=1.2)
    history = mod.get_drift_history("test_region")
    assert len(history) == 2
    mod.stop()


def test_correction_strength():
    """Correction strength scales with max_correction_ratio."""
    mod = FieldDriftCorrectionModule()
    mod.start()
    mod.register_region("test_region", baseline_value=1.0)
    mod.update_drift("test_region", observed_value=10.0)
    correction = mod.correct_drift("test_region")
    # Should be capped at max_correction_ratio * baseline
    assert abs(correction) <= mod.config.max_correction_ratio * 1.0
    mod.stop()
