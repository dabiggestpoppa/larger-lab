# Observer Persistence

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B2: ObserverPersistence
===========================
Save/restore observer state across sessions.

Ensures core observers never lose continuity by persisting their
state to disk and restoring on restart.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PERSISTENCE_DIR = REPO_ROOT / "data" / "persistent_field" / "observers"

logger = logging.getLogger("persistent_field.observer_persistence")


@dataclass
class ObserverSnapshot:
    """A snapshot of observer state."""
    observer_id: str
    observer_type: str
    continuity_score: float = 1.0
    specialization: dict[str, float] = field(default_factory=dict)
    last_task: str = ""
    total_tasks: int = 0
    success_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "observer_id": self.observer_id,
            "observer_type": self.observer_type,
            "continuity_score": self.continuity_score,
            "specialization": self.specialization,
            "last_task": self.last_task,
            "total_tasks": self.total_tasks,
            "success_count": self.success_count,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObserverSnapshot:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ObserverPersistence:
    """
    Save and restore observer state across sessions.

    Core observers: continuity, entropy, topology, repair, routing.
    """

    CORE_OBSERVERS = ["continuity", "entropy", "topology", "repair", "routing"]

    def __init__(self):
        self._lock = threading.Lock()
        self._snapshots: dict[str, ObserverSnapshot] = {}
        self._load_all()

    def save_observer(self, snapshot: ObserverSnapshot) -> None:
        """Save an observer snapshot to disk."""
        with self._lock:
            snapshot.timestamp = datetime.now(timezone.utc).isoformat()
            self._snapshots[snapshot.observer_id] = snapshot
            self._persist_snapshot(snapshot)
            logger.info(f"Observer saved: {snapshot.observer_id}")

    def restore_observer(self, observer_id: str) -> ObserverSnapshot | None:
        """Restore an observer from disk."""
        with self._lock:
            if observer_id in self._snapshots:
                return self._snapshots[observer_id]
            return self._load_snapshot(observer_id)

    def restore_all(self) -> dict[str, ObserverSnapshot]:
        """Restore all persisted observers."""
        with self._lock:
            for observer_id in self.CORE_OBSERVERS:
                if observer_id not in self._snapshots:
                    snapshot = self._load_snapshot(observer_id)
                    if snapshot:
                        self._snapshots[observer_id] = snapshot
            return dict(self._snapshots)

    def get_continuity_score(self, observer_id: str) -> float:
        """Get the continuity score for an observer."""
        snapshot = self._snapshots.get(observer_id)
        return snapshot.continuity_score if snapshot else 0.0

    def update_continuity(self, observer_id: str, delta: float) -> None:
        """Update an observer's continuity score."""
        with self._lock:
            if observer_id in self._snapshots:
                self._snapshots[observer_id].continuity_score = max(
                    0.0, min(1.0, self._snapshots[observer_id].continuity_score + delta)
                )

    def _persist_snapshot(self, snapshot: ObserverSnapshot) -> None:
        """Write snapshot to disk."""
        try:
            PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)
            file_path = PERSISTENCE_DIR / f"{snapshot.observer_id}.json"
            file_path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist observer {snapshot.observer_id}: {e}")

    def _load_snapshot(self, observer_id: str) -> ObserverSnapshot | None:
        """Load snapshot from disk."""
        try:
            file_path = PERSISTENCE_DIR / f"{observer_id}.json"
            if file_path.exists():
                data = json.loads(file_path.read_text(encoding="utf-8"))
                return ObserverSnapshot.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load observer {observer_id}: {e}")
        return None

    def _load_all(self) -> None:
        """Load all persisted observers."""
        try:
            if PERSISTENCE_DIR.exists():
                for file_path in PERSISTENCE_DIR.glob("*.json"):
                    try:
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        snapshot = ObserverSnapshot.from_dict(data)
                        self._snapshots[snapshot.observer_id] = snapshot
                    except Exception:
                        pass
        except Exception:
            pass

```

LINKS:
[[All Mermaid Graphs]]
[[Master Plan Observer Core]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Action]]
[[Citation Workflow]]
[[Cursor]]
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
