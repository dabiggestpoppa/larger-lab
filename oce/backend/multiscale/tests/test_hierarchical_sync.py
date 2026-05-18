"""Tests for Hierarchical Sync."""

import pytest
import time
from oce.backend.multiscale.hierarchical_sync import SyncManager, SyncFrequency, SyncRecord


class TestSyncManager:
    def test_creation(self):
        sync = SyncManager()
        assert sync is not None

    def test_should_sync_initially_true(self):
        sync = SyncManager()
        # Initially last_sync is 0.0, so should_sync returns True
        assert sync.should_sync(SyncFrequency.LOCAL) is True

    def test_perform_sync(self):
        sync = SyncManager()
        record = sync.perform_sync(SyncFrequency.LOCAL, ["obs1"], {"data": "test"})
        assert record.scale == SyncFrequency.LOCAL
        assert "obs1" in record.participants

    def test_should_sync_after_perform(self):
        sync = SyncManager()
        sync.perform_sync(SyncFrequency.LOCAL, ["obs1"], {})
        # After sync, should not need sync immediately
        assert sync.should_sync(SyncFrequency.LOCAL) is False

    def test_get_sync_history(self):
        sync = SyncManager()
        sync.perform_sync(SyncFrequency.LOCAL, ["obs1"], {})
        sync.perform_sync(SyncFrequency.REGIONAL, ["obs2"], {})
        history = sync.get_sync_history()
        assert len(history) == 2

    def test_get_sync_interval(self):
        sync = SyncManager()
        interval = sync.get_sync_interval(SyncFrequency.LOCAL)
        assert interval == 0.1

    def test_set_sync_interval(self):
        sync = SyncManager()
        sync.set_sync_interval(SyncFrequency.LOCAL, 0.5)
        assert sync.get_sync_interval(SyncFrequency.LOCAL) == 0.5

    def test_get_time_since_last_sync(self):
        sync = SyncManager()
        elapsed = sync.get_time_since_last_sync(SyncFrequency.LOCAL)
        assert elapsed >= 0
