# Observer Lifecycle

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""
O-1-B9: ObserverLifecycle
==========================
Heartbeat, healthcheck, recovery, state persistence, restart continuity.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from core.observer.observer_state import ObserverState, get_observer_state, HealthStatus
from core.observer.event_awareness import EventAwareness, EventType


class ObserverLifecycle:
    """
    Manages the observer lifecycle: heartbeat, health checks,
    recovery, and state persistence.
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        healthcheck_interval: float = 60.0,
    ):
        self.state = get_observer_state()
        self.event_bus = EventAwareness()
        self._heartbeat_interval = heartbeat_interval
        self._healthcheck_interval = healthcheck_interval
        self._running = False
        self._heartbeat_thread: threading.Thread | None = None
        self._healthcheck_thread: threading.Thread | None = None
        self._heartbeat_count = 0
        self._last_healthcheck: str | None = None
        self._recovery_callbacks: list[Callable] = []

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def heartbeat_count(self) -> int:
        return self._heartbeat_count

    def start(self) -> None:
        """Start the observer lifecycle."""
        if self._running:
            return
        self._running = True
        self.state.set_health(HealthStatus.HEALTHY)
        self.event_bus.emit(
            EventType.OBSERVER_SPAWNED,
            source="observer_lifecycle",
            data={"status": "started"},
        )

        # Start heartbeat
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

        # Start healthcheck
        self._healthcheck_thread = threading.Thread(
            target=self._healthcheck_loop, daemon=True
        )
        self._healthcheck_thread.start()

    def stop(self) -> None:
        """Stop the observer lifecycle."""
        self._running = False
        self.state.set_health(HealthStatus.HEALTHY)
        self.event_bus.emit(
            EventType.OBSERVER_SHUTDOWN,
            source="observer_lifecycle",
            data={"status": "stopped"},
        )

    def register_recovery(self, callback: Callable) -> None:
        """Register a recovery callback."""
        self._recovery_callbacks.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Get lifecycle status."""
        return {
            "running": self._running,
            "heartbeat_count": self._heartbeat_count,
            "last_healthcheck": self._last_healthcheck,
            "health": self.state.get("observer_health"),
            "continuity_score": self.state.get("continuity_score"),
            "uptime_heartbeats": self._heartbeat_count,
        }

    def _heartbeat_loop(self) -> None:
        """Periodic heartbeat."""
        while self._running:
            try:
                self._heartbeat_count += 1
                self.state.set("last_heartbeat", datetime.now(timezone.utc).isoformat())
                time.sleep(self._heartbeat_interval)
            except Exception:
                time.sleep(1)

    def _healthcheck_loop(self) -> None:
        """Periodic health check."""
        while self._running:
            try:
                self._run_healthcheck()
                time.sleep(self._healthcheck_interval)
            except Exception:
                time.sleep(1)

    def _run_healthcheck(self) -> None:
        """Run a health check and update state."""
        self._last_healthcheck = datetime.now(timezone.utc).isoformat()

        health = self.state.get("observer_health")
        if health == HealthStatus.FAILED.value:
            self._attempt_recovery()
        elif health == HealthStatus.DEGRADED.value:
            self.event_bus.emit(
                EventType.OBSERVER_DEGRADED,
                source="observer_lifecycle",
                data={"health": health},
            )

    def _attempt_recovery(self) -> None:
        """Attempt to recover from failure."""
        self.state.set_health(HealthStatus.RECOVERING)
        self.event_bus.emit(
            EventType.OBSERVER_RECOVERED,
            source="observer_lifecycle",
            data={"action": "recovery_started"},
        )

        for cb in self._recovery_callbacks:
            try:
                cb()
            except Exception:
                pass

        self.state.set_health(HealthStatus.HEALTHY)

```

LINKS:
[[All Mermaid Graphs]]
[[Heartbeat]]
[[Master Plan Observer Core]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Action]]
[[Cal]]
[[Citation Workflow]]
[[Server]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
