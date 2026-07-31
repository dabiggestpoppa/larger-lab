"""Test for field_state_snapshot."""
from field.phase4_instrumentation.field_state_snapshot import FieldStateSnapshotModule


def test_field_state_snapshot_init():
    """Module initializes with default config."""
    mod = FieldStateSnapshotModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_field_state_snapshot_start_stop():
    """Module start/stop toggles running state."""
    mod = FieldStateSnapshotModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
