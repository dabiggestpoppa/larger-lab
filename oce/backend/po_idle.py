"""
PO Idle Runtime — Autonomous background tick for PO cognitive field.
===============================================================

P3.4 of PO × Open-LLM-VTuber Integration.

Runs on adaptive cadence (60s active / 300s warm / 900s cold) when PO
is not actively handling a request. Performs:
- Vault sync (re-index, prune stale entries)
- Memory distillation (compress WORK → LEARNED layer)
- Telemetry emission (events to OCE event fabric)
- Heartbeat (update last_seen in PO state)

Evolution of scripts/po_heartbeat.py — async, OCE-native, adaptive.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger("oce.po_idle")


# ─── Protocols (interfaces for dependency injection) ─────────────────────────

class POStateStoreProtocol(Protocol):
    """Minimal interface for PO state persistence (P2.10)."""

    async def get_state(self) -> Dict[str, Any]: ...
    async def update_state(self, updates: Dict[str, Any]) -> None: ...


class POSessionStoreProtocol(Protocol):
    """Minimal interface for PO session continuity (P2.6)."""

    async def get_active_sessions(self) -> List[Dict[str, Any]]: ...
    async def get_last_activity_time(self) -> float: ...


class EventFabricProtocol(Protocol):
    """Minimal interface for OCE event emission."""

    async def ingest(self, event_type: str, source: str, payload: Dict[str, Any]) -> None: ...


class StructuralMemoryProtocol(Protocol):
    """Minimal interface for memory distillation."""

    async def get_layer_count(self, layer: str) -> int: ...
    async def compress_work_to_learned(self, max_entries: int = 20) -> Dict[str, int]: ...


class VaultIndexerProtocol(Protocol):
    """Minimal interface for vault sync."""

    async def reindex(self) -> Dict[str, Any]: ...
    async def prune_stale(self, max_age_hours: int = 168) -> int: ...


# ─── Models ───────────────────────────────────────────────────────────────────

class SessionState(str, Enum):
    ACTIVE = "active"    # request in-flight or <30s since last
    WARM = "warm"        # last request <5min ago
    COLD = "cold"        # idle >5min


@dataclass
class VaultSyncReport:
    entries_indexed: int = 0
    entries_pruned: int = 0
    duration_ms: float = 0.0
    success: bool = True


@dataclass
class MemoryDistillReport:
    work_compressed: int = 0
    learned_created: int = 0
    compression_ratio: float = 0.0
    success: bool = True


@dataclass
class TelemetryReport:
    events_emitted: int = 0
    success: bool = True


@dataclass
class HeartbeatReport:
    state_updated: bool = False
    uptime_seconds: float = 0.0
    success: bool = True


@dataclass
class TickReport:
    ts: float = 0.0
    cadence: int = 300
    session_state: SessionState = SessionState.WARM
    vault_sync: Optional[VaultSyncReport] = None
    memory_distill: Optional[MemoryDistillReport] = None
    telemetry: Optional[TelemetryReport] = None
    heartbeat: Optional[HeartbeatReport] = None
    tick_number: int = 0


# ─── Mock Stores (for scaffolding before P2.6/P2.10 land) ────────────────────

class MockPOStateStore:
    """In-memory mock for POStateStore until AS builds the real one."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            "last_seen": 0.0,
            "uptime_seconds": 0.0,
            "tick_count": 0,
            "status": "idle",
        }

    async def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    async def update_state(self, updates: Dict[str, Any]) -> None:
        self._state.update(updates)


class MockPOSessionStore:
    """In-memory mock for POSessionStore until AS builds the real one."""

    def __init__(self):
        self._sessions: List[Dict[str, Any]] = []
        self._last_activity: float = 0.0

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        return list(self._sessions)

    async def get_last_activity_time(self) -> float:
        return self._last_activity

    def set_last_activity(self, t: float) -> None:
        """Test helper — set the last activity time."""
        self._last_activity = t


class MockEventFabric:
    """In-memory mock for OCE EventFabric."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    async def ingest(self, event_type: str, source: str, payload: Dict[str, Any]) -> None:
        self.events.append({
            "event_type": event_type,
            "source": source,
            "payload": payload,
            "ts": time.time(),
        })


class MockStructuralMemory:
    """In-memory mock for StructuralMemory."""

    def __init__(self, work_count: int = 0, learned_count: int = 0):
        self._work_count = work_count
        self._learned_count = learned_count

    async def get_layer_count(self, layer: str) -> int:
        if layer == "WORK":
            return self._work_count
        elif layer == "LEARNED":
            return self._learned_count
        return 0

    async def compress_work_to_learned(self, max_entries: int = 20) -> Dict[str, int]:
        compressed = min(self._work_count, max_entries)
        created = max(1, compressed // 4)  # 4:1 compression ratio
        self._work_count -= compressed
        self._learned_count += created
        return {"work_compressed": compressed, "learned_created": created}


class MockVaultIndexer:
    """In-memory mock for VaultIndexer."""

    def __init__(self, total_entries: int = 0):
        self._total = total_entries

    async def reindex(self) -> Dict[str, Any]:
        return {"entries_indexed": self._total, "duration_ms": 10.0}

    async def prune_stale(self, max_age_hours: int = 168) -> int:
        pruned = max(0, self._total // 50)  # prune ~2% as stale
        self._total -= pruned
        return pruned


# ─── Core: POIdleRuntime ─────────────────────────────────────────────────────

# Cadence thresholds (seconds)
ACTIVE_THRESHOLD = 30    # <30s since last request = active
WARM_THRESHOLD = 300     # <5min = warm, else cold

# Cadence values (seconds)
ACTIVE_CADENCE = 60
WARM_CADENCE = 300
COLD_CADENCE = 900

# Memory distillation trigger
WORK_COMPRESSION_THRESHOLD = 50
WORK_MAX_COMPRESS_PER_TICK = 20


class POIdleRuntime:
    """
    Autonomous idle runtime — PO never sleeps.

    Runs background tick on adaptive cadence:
    - Active (60s): fast vault sync while user is talking
    - Warm (300s): standard — matches existing po_heartbeat.py
    - Cold (900s): save resources, still keep state fresh

    Each tick performs:
    1. Vault sync (re-index + prune stale)
    2. Memory distillation (WORK → LEARNED if threshold met)
    3. Telemetry emission (events to OCE event fabric)
    4. Heartbeat (update PO state)
    """

    def __init__(
        self,
        state_store: Optional[POStateStoreProtocol] = None,
        session_store: Optional[POSessionStoreProtocol] = None,
        event_fabric: Optional[EventFabricProtocol] = None,
        memory: Optional[StructuralMemoryProtocol] = None,
        vault_indexer: Optional[VaultIndexerProtocol] = None,
        cadence_seconds: int = WARM_CADENCE,
    ):
        self._state_store = state_store or MockPOStateStore()
        self._session_store = session_store or MockPOSessionStore()
        self._event_fabric = event_fabric or MockEventFabric()
        self._memory = memory or MockStructuralMemory()
        self._vault_indexer = vault_indexer or MockVaultIndexer()

        self._base_cadence = cadence_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_lock = asyncio.Lock()
        self._last_request_time: float = 0.0
        self._tick_count: int = 0
        self._start_time: float = 0.0
        self._tick_reports: List[TickReport] = []

    # ─── Public API ───────────────────────────────────────────────────────

    async def start(self) -> None:
        """Begin the idle loop. Non-blocking."""
        if self._running:
            logger.warning("POIdleRuntime already running")
            return
        self._running = True
        self._start_time = time.time()
        self._task = asyncio.create_task(self._loop())
        logger.info("POIdleRuntime started")

    async def stop(self) -> None:
        """Stop the loop, run final sync, exit cleanly."""
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Final sync before exit
        await self._final_sync()
        logger.info(f"POIdleRuntime stopped after {self._tick_count} ticks")

    async def tick(self) -> TickReport:
        """Run one cycle. Returns what was done."""
        async with self._tick_lock:
            report = TickReport(
                ts=time.time(),
                cadence=self._compute_cadence(),
                session_state=self._get_session_state(),
                tick_number=self._tick_count,
            )

            # 1. Vault sync
            report.vault_sync = await self._vault_sync()

            # 2. Memory distillation
            report.memory_distill = await self._memory_distill()

            # 3. Telemetry emission
            report.telemetry = await self._emit_telemetry(report)

            # 4. Heartbeat
            report.heartbeat = await self._update_heartbeat()

            self._tick_count += 1
            self._tick_reports.append(report)

            # Keep only last 100 reports
            if len(self._tick_reports) > 100:
                self._tick_reports = self._tick_reports[-100:]

            return report

    def notify_request(self) -> None:
        """Call when PO handles a request (resets active timer)."""
        self._last_request_time = time.time()

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_tick_report(self) -> Optional[TickReport]:
        return self._tick_reports[-1] if self._tick_reports else None

    @property
    def uptime_seconds(self) -> float:
        if self._start_time == 0:
            return 0.0
        return time.time() - self._start_time

    # ─── Private ──────────────────────────────────────────────────────────

    def _get_session_state(self) -> SessionState:
        """Determine session state based on time since last request."""
        elapsed = time.time() - self._last_request_time
        if self._last_request_time == 0:
            return SessionState.COLD
        if elapsed < ACTIVE_THRESHOLD:
            return SessionState.ACTIVE
        elif elapsed < WARM_THRESHOLD:
            return SessionState.WARM
        else:
            return SessionState.COLD

    def _compute_cadence(self) -> int:
        """Compute adaptive cadence based on session state."""
        state = self._get_session_state()
        if state == SessionState.ACTIVE:
            return ACTIVE_CADENCE
        elif state == SessionState.WARM:
            return WARM_CADENCE
        else:
            return COLD_CADENCE

    async def _loop(self) -> None:
        """Main idle loop — runs ticks on adaptive cadence."""
        while self._running:
            try:
                cadence = self._compute_cadence()
                await asyncio.sleep(cadence)
                if not self._running:
                    break
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Idle tick error: {e}")
                # Back off on error — don't tight-loop
                await asyncio.sleep(60)

    async def _vault_sync(self) -> VaultSyncReport:
        """Re-index vault and prune stale entries."""
        try:
            t0 = time.time()
            index_result = await self._vault_indexer.reindex()
            entries_indexed = index_result.get("entries_indexed", 0)
            entries_pruned = await self._vault_indexer.prune_stale()
            duration_ms = (time.time() - t0) * 1000

            return VaultSyncReport(
                entries_indexed=entries_indexed,
                entries_pruned=entries_pruned,
                duration_ms=round(duration_ms, 2),
                success=True,
            )
        except Exception as e:
            logger.error(f"Vault sync error: {e}")
            return VaultSyncReport(success=False)

    async def _memory_distill(self) -> MemoryDistillReport:
        """Compress WORK layer entries into LEARNED if threshold met."""
        try:
            work_count = await self._memory.get_layer_count("WORK")
            if work_count < WORK_COMPRESSION_THRESHOLD:
                return MemoryDistillReport(success=True)

            result = await self._memory.compress_work_to_learned(
                max_entries=WORK_MAX_COMPRESS_PER_TICK
            )
            work_compressed = result.get("work_compressed", 0)
            learned_created = result.get("learned_created", 0)
            ratio = learned_created / work_compressed if work_compressed > 0 else 0.0

            return MemoryDistillReport(
                work_compressed=work_compressed,
                learned_created=learned_created,
                compression_ratio=round(ratio, 3),
                success=True,
            )
        except Exception as e:
            logger.error(f"Memory distillation error: {e}")
            return MemoryDistillReport(success=False)

    async def _emit_telemetry(self, report: TickReport) -> TelemetryReport:
        """Emit tick telemetry to OCE event fabric."""
        events_emitted = 0
        try:
            # Always emit heartbeat tick
            await self._event_fabric.ingest(
                event_type="po_idle_tick",
                source="po_idle",
                payload={
                    "cadence_seconds": report.cadence,
                    "session_state": report.session_state.value,
                    "tick_number": report.tick_number,
                    "uptime_seconds": self.uptime_seconds,
                },
            )
            events_emitted += 1

            # Emit vault sync event if it ran
            if report.vault_sync and report.vault_sync.success:
                await self._event_fabric.ingest(
                    event_type="po_vault_sync",
                    source="po_idle",
                    payload={
                        "entries_indexed": report.vault_sync.entries_indexed,
                        "entries_pruned": report.vault_sync.entries_pruned,
                        "index_duration_ms": report.vault_sync.duration_ms,
                    },
                )
                events_emitted += 1

            # Emit memory distill event if compression ran
            if report.memory_distill and report.memory_distill.work_compressed > 0:
                await self._event_fabric.ingest(
                    event_type="po_memory_distill",
                    source="po_idle",
                    payload={
                        "work_compressed": report.memory_distill.work_compressed,
                        "learned_created": report.memory_distill.learned_created,
                        "compression_ratio": report.memory_distill.compression_ratio,
                    },
                )
                events_emitted += 1

            return TelemetryReport(events_emitted=events_emitted, success=True)
        except Exception as e:
            logger.error(f"Telemetry emission error: {e}")
            return TelemetryReport(events_emitted=events_emitted, success=False)

    async def _update_heartbeat(self) -> HeartbeatReport:
        """Update PO state with heartbeat."""
        try:
            await self._state_store.update_state({
                "last_seen": time.time(),
                "uptime_seconds": self.uptime_seconds,
                "tick_count": self._tick_count,
                "status": "idle",
            })
            return HeartbeatReport(
                state_updated=True,
                uptime_seconds=self.uptime_seconds,
                success=True,
            )
        except Exception as e:
            logger.error(f"Heartbeat update error: {e}")
            return HeartbeatReport(success=False)

    async def _final_sync(self) -> None:
        """Run one final tick on shutdown to flush state."""
        try:
            await self._update_heartbeat()
            await self._state_store.update_state({"status": "stopped"})
            logger.info("Final sync complete")
        except Exception as e:
            logger.error(f"Final sync error: {e}")


# ─── Singleton ────────────────────────────────────────────────────────────────

_idle_runtime: Optional[POIdleRuntime] = None


def get_idle_runtime() -> POIdleRuntime:
    """Get or create the global POIdleRuntime singleton."""
    global _idle_runtime
    if _idle_runtime is None:
        _idle_runtime = POIdleRuntime()
    return _idle_runtime


def set_idle_runtime(runtime: POIdleRuntime) -> None:
    """Set the global POIdleRuntime (for dependency injection)."""
    global _idle_runtime
    _idle_runtime = runtime
