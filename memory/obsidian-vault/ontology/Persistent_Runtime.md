# Persistent Runtime

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B1: PersistentRuntime
=========================
Long-running runtime that survives restarts.

Maintains the always-on SRRA field heartbeat, coordinates persistent
observers, and manages dormant/active state transitions.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = REPO_ROOT / "data" / "persistent_field"
STATE_FILE = STATE_DIR / "runtime_state.json"

logger = logging.getLogger("persistent_field.runtime")


class RuntimeState(str, Enum):
    DORMANT = "dormant"
    OBSERVATIONAL = "observational"
    ACTIVE = "active"
    RECOVERY = "recovery"
    CRITICAL = "critical"


@dataclass
class RuntimeStatus:
    """Current runtime status."""
    state: str = RuntimeState.DORMANT
    uptime_seconds: float = 0.0
    last_heartbeat: str = ""
    active_observers: int = 0
    total_restarts: int = 0
    entropy_level: float = 0.0
    continuity_score: float = 1.0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "uptime_seconds": self.uptime_seconds,
            "last_heartbeat": self.last_heartbeat,
            "active_observers": self.active_observers,
            "total_restarts": self.total_restarts,
            "entropy_level": self.entropy_level,
            "continuity_score": self.continuity_score,
            "timestamp": self.timestamp,
        }


class PersistentRuntime:
    """
    Main always-on orchestration substrate.

    Survives restarts via state persistence. Coordinates persistent
    observers and manages dormant/active transitions.
    """

    _instance: PersistentRuntime | None = None
    _lock = threading.Lock()

    def __init__(self):
        self._status = RuntimeStatus()
        self._observers: dict[str, dict[str, Any]] = {}
        self._start_time = time.time()
        self._running = False
        self._load_state()

    @classmethod
    def get_instance(cls) -> PersistentRuntime:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        """Start the persistent runtime."""
        self._running = True
        self._status.state = RuntimeState.OBSERVATIONAL
        self._status.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self._save_state()
        logger.info("PersistentRuntime started")

    def stop(self) -> None:
        """Gracefully stop the persistent runtime."""
        self._running = False
        self._status.state = RuntimeState.DORMANT
        self._save_state()
        logger.info("PersistentRuntime stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current runtime status."""
        self._status.uptime_seconds = time.time() - self._start_time
        self._status.timestamp = datetime.now(timezone.utc).isoformat()
        return self._status.to_dict()

    def register_observer(self, observer_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Register a persistent observer."""
        self._observers[observer_id] = {
            "id": observer_id,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._status.active_observers = len(self._observers)
        self._save_state()

    def heartbeat(self) -> dict[str, Any]:
        """Update runtime heartbeat."""
        now = datetime.now(timezone.utc)
        self._status.last_heartbeat = now.isoformat()
        self._status.uptime_seconds = time.time() - self._start_time
        self._save_state()
        return self.get_status()

    def transition_state(self, new_state: RuntimeState) -> bool:
        """Transition to a new runtime state."""
        old_state = self._status.state
        self._status.state = new_state
        self._save_state()
        logger.info(f"Runtime state: {old_state} -> {new_state}")
        return True

    def _save_state(self) -> None:
        """Persist runtime state to disk."""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "status": self._status.to_dict(),
                "observers": self._observers,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save runtime state: {e}")

    def _load_state(self) -> None:
        """Restore runtime state from disk."""
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                status_data = data.get("status", {})
                self._status.state = status_data.get("state", RuntimeState.DORMANT)
                self._status.total_restarts = status_data.get("total_restarts", 0) + 1
                self._observers = data.get("observers", {})
                self._status.active_observers = len(self._observers)
                logger.info(f"Runtime state restored: {self._status.state}")
        except Exception as e:
            logger.error(f"Failed to load runtime state: {e}")

```

LINKS:
[[Heartbeat]]
[[O 7 Persistent Field Doc]]
[[Daily Runtime 20260531]]
[[Ontology Core Summary]]
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
[[Observer Lifecycle]]
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
