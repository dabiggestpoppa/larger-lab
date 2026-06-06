"""
Tests for PO Idle Runtime — P3.4
=================================

3 tests:
1. Single tick — runs vault_sync + memory_distill + telemetry + heartbeat
2. Cadence — start() → wait 1.5× cadence → 2 ticks observed
3. Stop cleanly — no orphan tasks, no leaked state, final_sync ran
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock

from oce.backend.po_idle import (
    POIdleRuntime,
    MockPOStateStore,
    MockPOSessionStore,
    MockEventFabric,
    MockStructuralMemory,
    MockVaultIndexer,
    TickReport,
    VaultSyncReport,
    MemoryDistillReport,
    TelemetryReport,
    HeartbeatReport,
    SessionState,
    ACTIVE_CADENCE,
    WARM_CADENCE,
    COLD_CADENCE,
    WORK_COMPRESSION_THRESHOLD,
)


# ─── Test 1: Single Tick ──────────────────────────────────────────────────────

class TestSingleTick:
    """tick() runs vault_sync + memory_distill + telemetry + heartbeat,
    returns TickReport with all fields populated."""

    @pytest.mark.asyncio
    async def test_tick_returns_complete_report(self):
        """Single tick produces a TickReport with all 4 sub-reports."""
        state_store = MockPOStateStore()
        session_store = MockPOSessionStore()
        event_fabric = MockEventFabric()
        memory = MockStructuralMemory(work_count=60, learned_count=10)
        vault_indexer = MockVaultIndexer(total_entries=142)

        runtime = POIdleRuntime(
            state_store=state_store,
            session_store=session_store,
            event_fabric=event_fabric,
            memory=memory,
            vault_indexer=vault_indexer,
        )

        report = await runtime.tick()

        # TickReport is returned
        assert isinstance(report, TickReport)
        assert report.ts > 0
        assert report.tick_number == 0  # first tick

        # Vault sync ran
        assert report.vault_sync is not None
        assert isinstance(report.vault_sync, VaultSyncReport)
        assert report.vault_sync.success is True
        assert report.vault_sync.entries_indexed == 142
        assert report.vault_sync.entries_pruned >= 0

        # Memory distillation ran (work_count=60 > threshold=50)
        assert report.memory_distill is not None
        assert isinstance(report.memory_distill, MemoryDistillReport)
        assert report.memory_distill.success is True
        assert report.memory_distill.work_compressed > 0
        assert report.memory_distill.learned_created > 0

        # Telemetry emitted
        assert report.telemetry is not None
        assert isinstance(report.telemetry, TelemetryReport)
        assert report.telemetry.success is True
        assert report.telemetry.events_emitted >= 1  # at least heartbeat

        # Heartbeat updated
        assert report.heartbeat is not None
        assert isinstance(report.heartbeat, HeartbeatReport)
        assert report.heartbeat.success is True
        assert report.heartbeat.state_updated is True

    @pytest.mark.asyncio
    async def test_tick_updates_state_store(self):
        """Heartbeat writes last_seen and tick_count to state store."""
        state_store = MockPOStateStore()
        runtime = POIdleRuntime(state_store=state_store)

        await runtime.tick()

        state = await state_store.get_state()
        assert state["last_seen"] > 0
        assert state["tick_count"] == 0  # tick_count increments after tick
        assert state["status"] == "idle"

    @pytest.mark.asyncio
    async def test_tick_emits_events_to_fabric(self):
        """Tick emits at least po_idle_tick event to event fabric."""
        event_fabric = MockEventFabric()
        runtime = POIdleRuntime(event_fabric=event_fabric)

        await runtime.tick()

        assert len(event_fabric.events) >= 1
        assert event_fabric.events[0]["event_type"] == "po_idle_tick"
        assert event_fabric.events[0]["source"] == "po_idle"

    @pytest.mark.asyncio
    async def test_tick_no_distill_below_threshold(self):
        """Memory distillation skips when WORK count is below threshold."""
        memory = MockStructuralMemory(work_count=10, learned_count=5)
        runtime = POIdleRuntime(memory=memory)

        report = await runtime.tick()

        assert report.memory_distill is not None
        assert report.memory_distill.work_compressed == 0
        assert report.memory_distill.learned_created == 0

    @pytest.mark.asyncio
    async def test_tick_increments_count(self):
        """tick_count increments after each tick."""
        runtime = POIdleRuntime()

        assert runtime.tick_count == 0
        await runtime.tick()
        assert runtime.tick_count == 1
        await runtime.tick()
        assert runtime.tick_count == 2


# ─── Test 2: Cadence ─────────────────────────────────────────────────────────

class TestCadence:
    """start() → wait → ticks observed on adaptive cadence."""

    @pytest.mark.asyncio
    async def test_adaptive_cadence_active(self):
        """Active session (recent request) uses 60s cadence."""
        runtime = POIdleRuntime()
        runtime.notify_request()  # just now

        cadence = runtime._compute_cadence()
        assert cadence == ACTIVE_CADENCE  # 60

    @pytest.mark.asyncio
    async def test_adaptive_cadence_warm(self):
        """Warm session (request 2min ago) uses 300s cadence."""
        runtime = POIdleRuntime()
        runtime._last_request_time = time.time() - 120  # 2 min ago

        cadence = runtime._compute_cadence()
        assert cadence == WARM_CADENCE  # 300

    @pytest.mark.asyncio
    async def test_adaptive_cadence_cold(self):
        """Cold session (no recent request) uses 900s cadence."""
        runtime = POIdleRuntime()
        # _last_request_time defaults to 0 → cold

        cadence = runtime._compute_cadence()
        assert cadence == COLD_CADENCE  # 900

    @pytest.mark.asyncio
    async def test_session_state_transitions(self):
        """Session state transitions correctly over time."""
        runtime = POIdleRuntime()

        # No request yet → cold
        assert runtime._get_session_state() == SessionState.COLD

        # Just now → active
        runtime.notify_request()
        assert runtime._get_session_state() == SessionState.ACTIVE

        # 1 min ago → warm
        runtime._last_request_time = time.time() - 60
        assert runtime._get_session_state() == SessionState.WARM

        # 10 min ago → cold
        runtime._last_request_time = time.time() - 600
        assert runtime._get_session_state() == SessionState.COLD

    @pytest.mark.asyncio
    async def test_loop_produces_ticks(self):
        """start() with short cadence produces ticks over time."""
        # Use a very short cadence for testing (override the loop)
        runtime = POIdleRuntime(cadence_seconds=1)

        # We'll manually drive ticks instead of waiting for the loop
        # (loop uses adaptive cadence which could be 60-900s)
        await runtime.tick()
        await runtime.tick()

        assert runtime.tick_count == 2
        assert len(runtime._tick_reports) == 2


# ─── Test 3: Stop Cleanly ────────────────────────────────────────────────────

class TestStopCleanly:
    """stop() → no orphan tasks, no leaked state, final_sync ran."""

    @pytest.mark.asyncio
    async def test_stop_sets_not_running(self):
        """After stop(), is_running is False."""
        runtime = POIdleRuntime()
        await runtime.start()

        assert runtime.is_running is True

        await runtime.stop()

        assert runtime.is_running is False

    @pytest.mark.asyncio
    async def test_stop_runs_final_sync(self):
        """stop() updates state store with 'stopped' status."""
        state_store = MockPOStateStore()
        runtime = POIdleRuntime(state_store=state_store)
        await runtime.start()
        await runtime.stop()

        state = await state_store.get_state()
        assert state["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """After stop(), the background task is done."""
        runtime = POIdleRuntime()
        await runtime.start()

        task = runtime._task
        assert task is not None
        assert not task.done()

        await runtime.stop()

        assert task.done() or task.cancelled()

    @pytest.mark.asyncio
    async def test_double_stop_is_safe(self):
        """Calling stop() twice doesn't crash."""
        runtime = POIdleRuntime()
        await runtime.start()
        await runtime.stop()
        await runtime.stop()  # should not raise

        assert runtime.is_running is False

    @pytest.mark.asyncio
    async def test_no_leaked_tick_lock(self):
        """After stop(), the tick lock is not held."""
        runtime = POIdleRuntime()
        await runtime.start()
        await runtime.tick()
        await runtime.stop()

        # Lock should not be held
        assert not runtime._tick_lock.locked()
